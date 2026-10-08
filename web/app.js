/* ============================================================
   《反NPD精神控制的实用操作说明书》· 单文件阅读页 · 交互
   动效只做一处：载入时谱系尺"量出"一次。
   其余一切动效都回应操作（滚动位置、点击、搜索）。
   ============================================================ */
(function () {
  var html = document.documentElement;
  var body = document.body;
  html.classList.add('js');

  var hero = document.querySelector('.hero');
  var rail = document.querySelector('.progress-rail .marker');
  var toTop = document.querySelector('.to-top');

  requestAnimationFrame(function () {
    if (hero) hero.classList.add('hero-ready');
  });

  /* --- 侧栏链接索引 --- */
  var links = {};
  [].forEach.call(document.querySelectorAll('.toc a[href^="#"]'), function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });
  var anchors = [].slice.call(document.querySelectorAll('.content [data-anchor]'));
  var activeId = null;

  function pickAnchor() {
    var y = window.scrollY + 150, best = anchors[0];
    for (var i = 0; i < anchors.length; i++) {
      if (anchors[i].getBoundingClientRect().top + window.scrollY <= y) best = anchors[i];
      else break;
    }
    return best;
  }

  function setActive(id) {
    if (id === activeId) return;
    activeId = id;
    var prev = document.querySelector('.toc a.active');
    if (prev) prev.classList.remove('active');
    if (links[id]) links[id].classList.add('active');
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var doc = document.documentElement;
      var max = doc.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      if (rail) rail.style.transform = 'translateY(' + (p * (window.innerHeight - 2)) + 'px)';
      body.classList.toggle('scrolled', window.scrollY > 600);
      var a = pickAnchor();
      if (a) setActive(a.id);
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  /* --- 回到顶部 --- */
  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* --- 移动端目录抽屉 --- */
  var toggle = document.querySelector('.toc-toggle');
  var closeBtn = document.querySelector('.toc-close');
  if (toggle) {
    toggle.addEventListener('click', function () { body.classList.toggle('toc-open'); });
  }
  if (closeBtn) {
    closeBtn.addEventListener('click', function () { body.classList.remove('toc-open'); });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') body.classList.remove('toc-open');
  });
  [].forEach.call(document.querySelectorAll('.toc a'), function (a) {
    a.addEventListener('click', function () { body.classList.remove('toc-open'); });
  });

  /* --- 目录搜索：只筛目录，不跳走 --- */
  var q = document.getElementById('q');
  var qc = document.getElementById('qcount');
  if (q) {
    var items = [].slice.call(document.querySelectorAll('.toc-list > li'));
    var parts = [].slice.call(document.querySelectorAll('.toc-part'));

    var run = function () {
      var v = (q.value || '').trim().toLowerCase();
      var shown = 0;
      items.forEach(function (li) {
        var hay = (li.getAttribute('data-search') || '').toLowerCase();
        var hit = !v || hay.indexOf(v) > -1;
        li.hidden = !hit;
        if (hit) shown++;
      });
      parts.forEach(function (p) {
        var list = p.nextElementSibling;
        var has = false;
        while (list && !(list.classList && list.classList.contains('toc-list'))) list = list.nextElementSibling;
        if (list) has = [].some.call(list.children, function (li) { return !li.hidden; });
        p.hidden = !!v && !has;
      });
      if (qc) qc.textContent = v ? shown + '/' + items.length : '';
    };

    q.addEventListener('input', run);
    q.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var first = items.filter(function (li) { return !li.hidden; })[0];
        var a = first && first.querySelector('a');
        if (a) { a.click(); }
        q.blur();
      }
    });
  }

  /* --- 快捷键：/ 聚焦搜索 --- */
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) {
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (q) { e.preventDefault(); q.focus(); }
    }
  });
})();
