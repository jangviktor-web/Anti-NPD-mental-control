#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''把合订本 Markdown 构建成单文件 index.html（全部内容内嵌）。'''
import os
import re
import html as ihtml
import markdown

BASE = '/sandbox/workspace/npd-book'
WEB = os.path.join(BASE, 'web')
SRC = os.path.join(BASE, '反NPD精神控制的实用操作说明书.md')
OUT = os.path.join(BASE, 'index.html')

EXTRA_CSS = '''
/* ---------- 章标题、区块节奏、跳转链接（构建期追加） ---------- */
.prose.finale{margin-top:96px;border-top:3px solid var(--deep);padding-top:34px;}
.prose h1.chapter-title{
  font-family:var(--serif);font-weight:600;
  font-size:clamp(1.75rem,3.4vw,2.35rem);line-height:1.36;
  margin:0 0 22px;max-width:24em;
}
.content > .prose + .prose{margin-top:88px;}
.content > .part-divider + .prose{margin-top:32px;}
.content > .prose + .part-divider{margin-top:84px;}
.skip{position:absolute;left:-9999px;top:0;}
.skip:focus{left:14px;top:14px;z-index:120;background:var(--paper);color:var(--ink);
  padding:9px 14px;border:1px solid var(--rule);text-decoration:none;}
.prose a{overflow-wrap:break-word;}
'''

md = markdown.Markdown(extensions=['tables', 'sane_lists', 'fenced_code'])


def convert(text):
    md.reset()
    return md.convert(text)


def postprocess(h, sec_id, subs):
    # 表格横向滚动容器
    h = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap">\1</div>', h, flags=re.S)
    # 二级标题：加 id 与锚点，供目录与滚动定位
    counter = [0]

    def h2repl(m):
        counter[0] += 1
        sid = '%s-%d' % (sec_id, counter[0])
        title_html = m.group(1)
        plain = re.sub(r'<[^>]+>', '', title_html)
        subs.append((sid, plain))
        return '<h2 id="%s" data-anchor="%s">%s</h2>' % (sid, sid, title_html)

    h = re.sub(r'<h2>(.*?)</h2>', h2repl, h, flags=re.S)
    # 「本章依据」块：先取出该段，再解开只包着它的引用块
    h = re.sub(
        r'<p><strong>本章依据</strong>(.*?)</p>',
        lambda m: '<aside class="source"><strong>本章依据</strong>%s</aside>' % m.group(1),
        h, flags=re.S)
    h = re.sub(r'<blockquote>\s*(<aside class="source">.*?</aside>)\s*</blockquote>',
               r'\1', h, flags=re.S)
    # 危险等级 L1–L4 着色（仅这些标记，别处不受影响）
    h = re.sub(r'(?<![A-Za-z0-9])L([1-4])(?![0-9A-Za-z])',
               lambda m: '<span class="lv lv%s">L%s</span>' % (m.group(1), m.group(1)), h)
    return h


def build():
    raw = open(SRC, encoding='utf-8').read()
    body = raw[raw.index('\n# 第一部分'):].strip()
    blocks = re.split(r'\n(?=# )', body)

    sections = []
    nav = []
    part_i = 0

    for b in blocks:
        lines = b.split('\n')
        head = lines[0][2:].strip()
        rest = '\n'.join(lines[1:]).strip()

        if re.match(r'^第[一二三四五六七]部分', head):
            part_i += 1
            sid = 'p%d' % part_i
            m = re.match(r'(第[一二三四五六七]部分)\s*(.*)', head)
            label, title = m.group(1), m.group(2)
            intro_html = convert(rest)
            sections.append(
                '<section class="part-divider" id="%s" data-anchor="%s">'
                '<p class="part-no">%s</p><h2>%s</h2>%s</section>'
                % (sid, sid, label, ihtml.escape(title), intro_html))
            nav.append(('part', head, sid, None))

        elif re.match(r'^第\d+章', head):
            n = re.match(r'^第(\d+)章', head).group(1)
            sid = 'c%s' % n
            subs = []
            h = postprocess(convert(rest), sid, subs)
            sections.append(
                '<section class="prose" id="%s" data-anchor="%s">'
                '<h1 class="chapter-title">%s</h1>%s</section>'
                % (sid, sid, ihtml.escape(head), h))
            nav.append(('chapter', head, sid, subs))

        elif re.match(r'^附录[A-E]', head):
            letter = re.match(r'^附录([A-E])', head).group(1)
            sid = 'ap%s' % letter
            subs = []
            h = postprocess(convert(rest), sid, subs)
            sections.append(
                '<section class="prose" id="%s" data-anchor="%s">'
                '<h1 class="chapter-title">%s</h1>%s</section>'
                % (sid, sid, ihtml.escape(head), h))
            nav.append(('chapter', head, sid, subs))

        elif head.startswith('写在最后'):
            sid = 'end'
            subs = []
            h = postprocess(convert(rest), sid, subs)
            sections.append(
                '<section class="prose finale" id="%s" data-anchor="%s">'
                '<h1 class="chapter-title">%s</h1>%s</section>'
                % (sid, sid, ihtml.escape(head), h))
            nav.append(('chapter', head, sid, subs))

    # 侧栏目录
    groups = []
    for t in nav:
        if t[0] == 'part':
            groups.append({'title': t[1], 'items': []})
        else:
            if t[1].startswith('写在最后'):
                groups.append({'title': '结尾', 'items': []})
            if not groups:
                groups.append({'title': None, 'items': []})
            groups[-1]['items'].append(t)

    toc = []
    for g in groups:
        if g['title']:
            toc.append('<p class="toc-part">%s</p>' % ihtml.escape(g['title']))
        toc.append('<ol class="toc-list">')
        for kind, head, sid, subs in g['items']:
            search = head + ' ' + ' '.join(s for _, s in (subs or []))
            item = '<li data-search="%s"><a href="#%s">%s</a>' % (
                ihtml.escape(search), sid, ihtml.escape(head))
            if subs:
                item += '<ul class="sub">' + ''.join(
                    '<li><a href="#%s">%s</a></li>' % (s2, ihtml.escape(st)) for s2, st in subs) + '</ul>'
            item += '</li>'
            toc.append(item)
        toc.append('</ol>')

    hero = open(os.path.join(WEB, 'intro.html'), encoding='utf-8').read()
    css = open(os.path.join(WEB, 'style.css'), encoding='utf-8').read() + EXTRA_CSS
    js = open(os.path.join(WEB, 'app.js'), encoding='utf-8').read()
    tpl = open(os.path.join(WEB, 'template.html'), encoding='utf-8').read()

    page = (tpl
            .replace('@@CSS@@', css)
            .replace('@@JS@@', js)
            .replace('@@HERO@@', hero)
            .replace('@@TOC@@', '\n'.join(toc))
            .replace('@@CONTENT@@', '\n'.join(sections)))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(page)

    print('输出:', OUT)
    print('文件大小: %.1f KB' % (os.path.getsize(OUT) / 1024))
    print('section 数:', len(sections))
    print('目录条目数:', sum(1 for t in nav if t[0] == 'chapter'))
    print('子标题数:', sum(len(t[3] or []) for t in nav if t[0] == 'chapter'))
    print('替换字符:', page.count('\ufffd'))


if __name__ == '__main__':
    build()
