#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''把合订本 Markdown 构建成电子书 PDF（WeasyPrint + CSS Paged Media）。

   结构：封面 → 版权页 → 目录（带页码）→ 前言 → 正文（各部分单页 + 章章分页）→ 尾页
'''
import os
import re
import html as ihtml
import markdown
from weasyprint import HTML, CSS

BASE = '/sandbox/workspace/npd-book'
WEB = os.path.join(BASE, 'web')
NAME = '反NPD精神控制的实用操作说明书'
SRC = os.path.join(BASE, NAME + '.md')
OUT = os.path.join(BASE, NAME + '.pdf')

md = markdown.Markdown(extensions=['tables', 'sane_lists', 'fenced_code'])


def conv(text):
    md.reset()
    return md.convert(text)


def post(h, sec_id):
    """PDF 版后处理：二级标题编号、依据块、危险分级着色（表格不加滚动容器）"""
    counter = [0]

    def rep(m):
        counter[0] += 1
        return '<h2 id="%s-%d">%s</h2>' % (sec_id, counter[0], m.group(1))

    h = re.sub(r'<h2>(.*?)</h2>', rep, h, flags=re.S)
    h = re.sub(r'<p><strong>本章依据</strong>(.*?)</p>',
               lambda m: '<aside class="source"><strong>本章依据</strong>%s</aside>' % m.group(1),
               h, flags=re.S)
    h = re.sub(r'<blockquote>\s*(<aside class="source">.*?</aside>)\s*</blockquote>', r'\1', h, flags=re.S)
    h = re.sub(r'(?<![A-Za-z0-9])L([1-4])(?![0-9A-Za-z])',
               lambda m: '<span class="lv lv%s">L%s</span>' % (m.group(1), m.group(1)), h)
    return h


COVER = '''
<div class="cover">
  <p class="kicker">自助工具书 · 识别与自我保护</p>
  <h1>反NPD精神控制的<br>实用操作说明书</h1>
  <p class="sub">从“说不清、只会自责”，到看得懂套路、说得出话、走得开。</p>
  <div class="spectrum"><span class="s1"></span><span class="s2"></span><span class="s3"></span><span class="s4"></span></div>
  <div class="scale"><span>健康自恋、高自尊</span><span>人格倾向，多为难自己</span><span>人格障碍，消耗他人</span><span>安全红线</span></div>
  <div class="foot">
    <span class="rule"></span>
    <p>三条铁律：不做诊断、不贴标签；安全大于胜负；每条判断附依据。</p>
    <p>全书 20 章，31 种操控机制，91 条可照说的话术，44 则脱敏案例，14 条安全红线。</p>
    <p>2026-10 · 供个人学习、识别与自我保护使用</p>
  </div>
</div>
'''

COLOPHON = '''
<div class="colophon">
  <p>反NPD精神控制的实用操作说明书</p>
  <p>本书为自助工具书，内容整理自公开出版与发表的临床、科普与实操素材，每条判断均标注来源；书中案例均为素材中的化名或据素材情境重建的脱敏案例，不对应任何现实可指认的人。</p>
  <p>本书不构成医学诊断、心理治疗或法律意见，也不用于给他人贴标签、诊断或指控。涉及人身安全，请立即向执法与专业机构求助（号码以当地最新公示为准）。</p>
  <p>版本 2026-10 · 由 Markdown 经 HTML+CSS Paged Media 排版生成</p>
</div>
'''


def build():
    raw = open(SRC, encoding='utf-8').read()
    front = raw[:raw.index('\n# 第一部分')]
    front = front[:front.index('# 目录')]
    body = raw[raw.index('\n# 第一部分'):].strip()

    # ---- 版权页 / 前言 ----
    copyright_html = ''
    preface = []
    for s in re.split(r'\n(?=## )', front):
        if s.startswith('## 版权与免责'):
            copyright_html = conv(s.split('\n', 1)[1])
        elif re.match(r'## (写在前面|如何使用这本书|本书的依据)', s):
            preface.append(conv(s))
    copyright_page = '<div class="copyright"><h1>版权与免责提示</h1>%s</div>' % copyright_html

    # ---- 正文分块 ----
    sections, nav = [], []
    part_i = 0
    for b in re.split(r'\n(?=# )', body):
        lines = b.split('\n')
        head = lines[0][2:].strip()
        rest = '\n'.join(lines[1:]).strip()

        if re.match(r'^第[一二三四五六七]部分', head):
            part_i += 1
            sid = 'p%d' % part_i
            m = re.match(r'(第[一二三四五六七]部分)\s*(.*)', head)
            label, title = m.group(1), m.group(2)
            inner = conv(rest)
            lede = re.search(r'<p>(.*?)</p>', inner, re.S)
            sections.append(
                '<section class="part-page" id="%s"><p class="part-no">%s</p><h1>%s</h1>'
                '<p class="lede">%s</p></section>'
                % (sid, label, ihtml.escape(title), lede.group(1) if lede else ''))
            nav.append(('part', head, sid))

        elif re.match(r'^第\d+章', head):
            sid = 'c%s' % re.match(r'^第(\d+)章', head).group(1)
            sections.append('<section class="chapter" id="%s"><h1 class="chapter-title">%s</h1>%s</section>'
                            % (sid, ihtml.escape(head), post(conv(rest), sid)))
            nav.append(('chapter', head, sid))

        elif re.match(r'^附录[A-E]', head):
            sid = 'ap%s' % re.match(r'^附录([A-E])', head).group(1)
            sections.append('<section class="chapter" id="%s"><h1 class="chapter-title">%s</h1>%s</section>'
                            % (sid, ihtml.escape(head), post(conv(rest), sid)))
            nav.append(('chapter', head, sid))

        elif head.startswith('写在最后'):
            sid = 'end'
            sections.append('<section class="finale" id="%s"><h1>%s</h1>%s</section>'
                            % (sid, ihtml.escape(head), post(conv(rest), sid)))
            nav.append(('chapter', head, sid))

    # ---- 目录 ----
    rows = []
    for t in nav:
        if t[0] == 'part':
            rows.append('<div class="toc-part">%s</div>' % ihtml.escape(t[1]))
        else:
            rows.append('<div class="toc-row"><span class="tt">%s</span>'
                        '<span class="tp"><a href="#%s"></a></span></div>' % (ihtml.escape(t[1]), t[2]))

    page = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<title>%s</title>'
            '<meta name="description" content="识别与应对自恋型关系的自助工具书：20 章、31 种操控机制、91 条可照说的话术、44 则脱敏案例、14 条安全红线；不做诊断、不贴标签，每条判断附出处。">'
            '<meta name="keywords" content="NPD,自恋型人格,精神控制,煤气灯,边界,自我修复,识别应对">'
            '</head><body>%s%s<div class="toc"><h1>目录</h1>%s</div>'
            '<section class="frontmatter">%s</section>%s%s</body></html>'
            % (NAME, COVER, copyright_page, ''.join(rows), ''.join(preface),
               ''.join(sections), COLOPHON))

    open(os.path.join(BASE, '_pdf_source.html'), 'w', encoding='utf-8').write(page)
    HTML(string=page, base_url=BASE).write_pdf(
        OUT, stylesheets=[CSS(filename=os.path.join(WEB, 'print.css'))])

    print('输出:', OUT)
    print('大小: %.1f MB' % (os.path.getsize(OUT) / 1024 / 1024))
    print('章节节数:', sum(1 for t in nav if t[0] == 'chapter'))


if __name__ == '__main__':
    build()
