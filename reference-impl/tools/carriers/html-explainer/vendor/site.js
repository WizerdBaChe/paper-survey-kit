/* Research-site mechanism: registry-driven define-before-use (hover card 350 ms, click-to-jump,
   Backspace-return, G glossary overlay), 本節速查 rail, the evidence-table filter, cross-reference previews
   (hover card on id links, pinnable), resizable side columns, a nav keyword filter, a nav drawer under 920 px
   and self-test blocks (details.quiz) that open for printing.
   Adapted from a long-document reference shell (deck-shell lineage). Differences:
   - multi-page: the nav is server-rendered native links; the destination lives in the URL;
   - a registry entry `s` may be "other-page.html#id": clicking navigates there;
   - registry and preview text is inserted with textContent (never innerHTML);
   - links created here use setAttribute (gate-scanned documents must not contain href string literals);
   - previews come from <script type="application/json" id="previews"> (pages are opened from file://, no fetch).
   JS-dead degradation: without this file every page is a plain scrollable document: no handles, default widths,
   links are ordinary anchors. */
(function(){
  'use strict';
  var REFS = window.SITE_REFS || {};
  var SYMS = window.SITE_SYMS || {};
  var CUR = (location.pathname.split('/').pop() || 'index.html');
  var card = document.getElementById('refcard'), pill = document.getElementById('backpill');
  var gloss = document.getElementById('gloss'), backStack = [];
  var pins = document.getElementById('pins');
  /* a hub page (course index, launcher) carries #side but not the reader chrome (#refcard, #gloss, #backpill): the
     hover / glossary / back handlers stand down there, and the nav, layout and drawer below still run */
  var HAS_READER = !!(card && gloss && pill);
  var SEL = '.ref,.sym,a[data-pv]';
  function fail(where, e){ try { console.error(JSON.stringify({site:'research', where:where, error:String(e && e.message || e)})); } catch(_){} }

  /* ---- cross-reference previews: key "file.html#id" -> {t:title, b:body, p:page title} */
  var PV = {};
  try { var pe = document.getElementById('previews'); if (pe) PV = JSON.parse(pe.textContent) || {}; } catch (e) { fail('previews-json', e); }
  function keyOf(a){
    var h = a.getAttribute('href');
    if (!h || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(h)) return null;
    var i = h.indexOf('#'); if (i < 0) return null;
    return (i === 0 ? CUR : h.slice(0, i)) + h.slice(i);
  }
  function decorateLinks(){
    document.querySelectorAll('main a[href]').forEach(function(a){
      var k = keyOf(a);
      if (k && Object.prototype.hasOwnProperty.call(PV, k)) a.dataset.pv = k;
    });
  }

  function entryFor(k){ return REFS[k] || SYMS[k]; }
  /* SH-18 token matching, the one rule shell_match.py mirrors (decorate_cases.json binds both):
     longest key first at each position, left to right; a match touching an ASCII word character
     on either side is skipped WHOLE (no shorter key is retried there). */
  function matcher(keys){
    keys = keys.slice().sort(function(a,b){ return b.length - a.length; });
    if (!keys.length) return function(){ return []; };   /* '()' would match the empty string forever */
    var pat = keys.map(function(t){ return t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }).join('|');
    var reG = new RegExp('(' + pat + ')','g'), bound = /[A-Za-z0-9_]/;
    return function(text){
      var out = [], m;
      reG.lastIndex = 0;
      while ((m = reG.exec(text))){
        var before = text[m.index-1], after = text[m.index + m[0].length];
        if ((before && bound.test(before)) || (after && bound.test(after))) continue;
        out.push([m.index, m.index + m[0].length, m[0]]);
      }
      return out;
    };
  }
  function matchText(text, keys){ return matcher(keys)(text); }
  var SKIP_TAGS = {SCRIPT:1, STYLE:1, SVG:1, H1:1, H2:1, H3:1, H4:1, A:1, CODE:1, TITLE:1, MATH:1};
  function skipped(n){
    for (var e = n.parentNode; e && e !== document.body; e = e.parentNode){
      if (SKIP_TAGS[e.nodeName.toUpperCase()]) return true;
      if (e.classList && (e.classList.contains('ref')||e.classList.contains('sym')||e.classList.contains('nodeco'))) return true;
    }
    return false;
  }
  /* Decorate the text under `root`; returns false when the registry has no matchable key.
     A key whose entry has `b` (a block term) is matched, so it shields the shorter keys inside it,
     but gets no token and no card. */
  function decorateIn(root, refs, syms){
    var keys = [];
    Object.keys(refs).forEach(function(k){ if(!refs[k].n) keys.push(k); });
    Object.keys(syms).forEach(function(k){ if(!syms[k].n) keys.push(k); });
    if (!keys.length || !root) return false;
    var match = matcher(keys), work = [];
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: function(n){
      return skipped(n) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
    }});
    while (walker.nextNode()){
      var ms = match(walker.currentNode.nodeValue);
      if (ms.length) work.push([walker.currentNode, ms]);
    }
    work.forEach(function(w){
      var node = w[0], text = node.nodeValue, frag = document.createDocumentFragment(), last = 0, any = false;
      w[1].forEach(function(m){
        var k = m[2], e = refs[k] || syms[k];
        if (e && e.b) return;   /* block term: the text stays plain */
        frag.appendChild(document.createTextNode(text.slice(last, m[0])));
        var sp = document.createElement('span');
        sp.className = Object.prototype.hasOwnProperty.call(refs, k) ? 'ref' : 'sym';
        sp.tabIndex = 0; sp.dataset.key = k; sp.textContent = k;
        frag.appendChild(sp); last = m[1]; any = true;
      });
      if (!any) return;
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
    return true;
  }
  window.SiteShell = { matchText: matchText, decorateIn: decorateIn };   /* SH-18 test seam */
  function decorate(){
    if (!decorateIn(document.querySelector('main'), REFS, SYMS)) return;
    railFor = null; cur();   /* rebuild the rail once the tokens exist */
  }
  var hoverTimer = null, hideTimer = null, curKey = null;
  function place(anchor){
    var r = anchor.getBoundingClientRect(), cw = card.offsetWidth, ch = card.offsetHeight;
    var x = Math.min(Math.max(8, r.left), window.innerWidth - cw - 8), y = r.bottom + 8;
    if (y + ch > window.innerHeight - 8) y = r.top - ch - 8;
    card.style.left = x + 'px'; card.style.top = Math.max(8, y) + 'px';
  }
  function showCard(sp){
    var e = entryFor(sp.dataset.key); if (!e) return;
    curKey = null; card.className = ''; card.setAttribute('role', 'tooltip');
    card.textContent = '';
    var t = document.createElement('div'); t.className = 'rt'; t.textContent = e.t; card.appendChild(t);
    var d = document.createElement('div'); d.textContent = e.d; card.appendChild(d);
    if (e.o && e.o.length){ var o = document.createElement('div'); o.className = 'ro'; o.textContent = '又作：' + e.o.join('、'); card.appendChild(o); }
    if (e.s){ var j = document.createElement('div'); j.className = 'rj'; j.textContent = '點擊跳至定義處 · Backspace 返回'; card.appendChild(j); }
    card.style.display = 'block';
    place(sp);
  }
  /* title, body, 出自, 前往 + (釘選 | ×): the same layout in the hover card and in a pinned card */
  function fillPreview(box, key, e, pinned){
    box.textContent = '';
    function div(cls, txt){ var d = document.createElement('div'); d.className = cls; d.textContent = txt; box.appendChild(d); return d; }
    div('rt', e.t);
    if (e.b) div('rb', e.b);
    div('rfrom', '出自：' + e.p);
    var act = document.createElement('div'); act.className = 'cact';
    var go = document.createElement('a'); go.className = 'cgo'; go.setAttribute('href', key); go.textContent = '前往 →'; act.appendChild(go);
    var b = document.createElement('button'); b.type = 'button';
    if (pinned){ b.className = 'cx'; b.textContent = '×'; b.setAttribute('aria-label', '關閉這張釘選卡片'); }
    else { b.className = 'cpin'; b.textContent = '釘選'; }
    act.appendChild(b); box.appendChild(act);
  }
  function showPreview(a){
    var key = a.dataset.pv, e = PV[key]; if (!e) return;
    curKey = key; card.className = 'pv'; card.setAttribute('role', 'group'); card.setAttribute('aria-label', '預覽：' + e.t);
    fillPreview(card, key, e, false);
    card.style.display = 'block';
    place(a);
  }
  function showFor(sp){ if (sp.matches('a[data-pv]')) showPreview(sp); else showCard(sp); }
  function hideCard(){ card.style.display = 'none'; curKey = null; }
  function pinCurrent(){
    if (!curKey || !PV[curKey]) return;
    var key = curKey, e = PV[key];
    Array.prototype.slice.call(pins.children).forEach(function(c){ if (c.dataset.key === key) pins.removeChild(c); });
    var pc = document.createElement('div'); pc.className = 'pcard'; pc.dataset.key = key;
    pc.setAttribute('role', 'group'); pc.setAttribute('aria-label', '釘選：' + e.t);
    fillPreview(pc, key, e, true);
    pins.appendChild(pc);
    while (pins.children.length > 4) pins.removeChild(pins.firstChild);   /* the oldest drops */
    hideCard();
  }
  /* s = "#id" or "file.html#id" or "file.html". Same page: smooth jump + Backspace pill. Other page: navigate. */
  function jumpTo(s){
    if (!s) return;
    var i = s.indexOf('#'), file = i < 0 ? s : s.slice(0, i), id = i < 0 ? '' : s.slice(i + 1);
    if (file && file !== CUR){ location.href = s; return; }
    var el = id ? document.getElementById(id) : null; if (!el) return;
    backStack.push(window.scrollY); pill.style.display = 'block'; hideCard();
    el.scrollIntoView({behavior:'smooth', block:'start'});
  }
  function goBack(){ if (!backStack.length) return; var y = backStack.pop(); if (!backStack.length) pill.style.display='none'; window.scrollTo({top:y, behavior:'smooth'}); }
  /* a click on an ordinary link that stays on this page: the browser does the scrolling, we only remember where we were */
  function noteSamePage(a){
    var k = keyOf(a); if (!k) return;
    var i = k.indexOf('#'); if (k.slice(0, i) !== CUR || !document.getElementById(k.slice(i + 1))) return;
    backStack.push(window.scrollY); pill.style.display = 'block';
  }
  document.addEventListener('mouseover', function(e){
    if (!HAS_READER) return;
    if (card.contains(e.target)){ clearTimeout(hideTimer); return; }   /* the card stays while the pointer is inside it */
    var sp = e.target.closest && e.target.closest(SEL); clearTimeout(hoverTimer);
    if (sp){ clearTimeout(hideTimer); hoverTimer = setTimeout(function(){ showFor(sp); }, 350); } });
  document.addEventListener('mouseout', function(e){
    if (!HAS_READER) return;
    var sp = e.target.closest && e.target.closest(SEL), inCard = card.contains(e.target), to = e.relatedTarget;
    if (!sp && !inCard) return;
    if (to && (card.contains(to) || (sp && sp.contains(to)))) return;   /* moving between the link and its card, or inside the link */
    clearTimeout(hoverTimer); hideTimer = setTimeout(hideCard, 150); });
  document.addEventListener('focusin', function(e){ if (!HAS_READER) return; var sp = e.target.closest && e.target.closest(SEL); if (sp){ clearTimeout(hideTimer); showFor(sp); } });
  document.addEventListener('focusout', function(e){
    if (!HAS_READER) return;
    var sp = e.target.closest && e.target.closest(SEL);
    if (sp && !(e.relatedTarget && card.contains(e.relatedTarget))) hideCard(); });
  document.addEventListener('click', function(e){
    if (!HAS_READER) return;
    var t = e.target;
    var pin = t.closest && t.closest('.cpin');
    if (pin){ pinCurrent(); return; }
    if (t.closest && t.closest('#hint .hx')){ hideHint(true); return; }
    if (t.closest && t.closest('#hint .hr')){ showHint(); return; }
    var x = t.closest && t.closest('.cx');
    if (x){ var pc = x.closest('.pcard'); if (pc && pc.parentNode) pc.parentNode.removeChild(pc); return; }
    var sp = t.closest && t.closest('.ref,.sym');
    if (sp){ var en = entryFor(sp.dataset.key); if (en && en.s) jumpTo(en.s); return; }
    var row = t.closest && t.closest('.gl-row.jump');
    if (row){ gloss.classList.remove('open'); jumpTo(row.dataset.sid); return; }
    var a = t.closest && t.closest('a[href]');
    if (a && !a.closest('#side') && !a.closest('#rail') && e.button === 0 && !(e.ctrlKey || e.metaKey || e.shiftKey || e.altKey)){
      noteSamePage(a); hideCard();
    }
  });
  /* ---- the hint bar can be closed (user ruling 2026-10-04); the choice is remembered per viewer, best effort */
  var HKEY = 'research-site-hint-v1', hintEl = document.getElementById('hint');
  function hideHint(save){
    if (hintEl){ hintEl.classList.add('off'); var hb = hintEl.querySelector('.hr'); if (hb && save) hb.focus(); }
    if (save){ try { window.localStorage.setItem(HKEY, 'off'); } catch (e) { fail('hint-save', e); } }
  }
  /* closing collapses the bar to a small restore tab (user ruling 2026-10-14); it never disappears for good */
  function showHint(){
    if (hintEl) hintEl.classList.remove('off');
    try { window.localStorage.removeItem(HKEY); } catch (e) { fail('hint-save', e); }
  }
  if (hintEl && !hintEl.querySelector('.hr')){
    var hr = document.createElement('button'); hr.type = 'button'; hr.className = 'hr';
    hr.textContent = '？操作提示'; hr.setAttribute('aria-label', '展開操作提示'); hintEl.appendChild(hr);
  }
  try { if (window.localStorage.getItem(HKEY) === 'off') hideHint(false); } catch (e) { fail('hint-load', e); }
  /* ---- pinned cards push the main column (user ruling 2026-10-04): site.css widens main's right margin under html.has-pins */
  function syncPins(){ document.documentElement.classList.toggle('has-pins', !!(pins && pins.children.length)); }
  try { if (pins) new MutationObserver(syncPins).observe(pins, {childList:true}); } catch (e) { fail('pins-observe', e); }
  syncPins();
  var glossBuilt = false;
  function buildGloss(){
    if (glossBuilt) return; glossBuilt = true;
    var box = document.getElementById('glosslist'); box.textContent = '';
    function head(s){ var h = document.createElement('h3'); h.textContent = s; box.appendChild(h); }
    function row(k, e){
      var r = document.createElement('div'); r.className = 'gl-row' + (e.s ? ' jump' : ''); if (e.s) r.dataset.sid = e.s;
      var shown = e.k || k;   /* SH-14: an entry may name its display key (e.g. the English standard name) */
      var a = document.createElement('span'); a.className = 'gl-k'; a.textContent = shown;
      var b = document.createElement('span'); var bb = document.createElement('b');
      bb.textContent = e.t.replace(new RegExp('^' + shown.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + '\\s*[—·-]\\s*'), '');
      b.appendChild(bb);
      if (e.o && e.o.length) b.appendChild(document.createTextNode('（又作 ' + e.o.join('、') + '）'));
      b.appendChild(document.createTextNode('：' + e.d));
      r.appendChild(a); r.appendChild(b); box.appendChild(r);
    }
    head('本頁出現的編號（點列可跳至定義處 · Esc 關閉）');
    Object.keys(REFS).forEach(function(k){ if (!REFS[k].b) row(k, REFS[k]); });
    head('名詞與縮寫');
    /* SH-14: a synonym key (`a` = its standard key) decorates and hovers, but is listed once, under its standard entry;
       SH-18: a block term (`b`) only shields shorter keys and is never listed */
    Object.keys(SYMS).forEach(function(k){ if (!SYMS[k].a && !SYMS[k].b) row(k, SYMS[k]); });
  }
  document.addEventListener('keydown', function(e){
    if (!HAS_READER || e.altKey || e.ctrlKey || e.metaKey) return;
    var t = e.target;
    /* Enter/Space on a focused token jumps; every other key falls through (after a click the token keeps focus,
       and Backspace / G / Esc must still work from there) */
    if (t && t.closest && t.closest('.ref,.sym') && (e.key==='Enter'||e.key===' ')){ e.preventDefault(); var en = entryFor(t.dataset.key); if (en && en.s) jumpTo(en.s); return; }
    if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA')) return;   /* typing in a filter box */
    if (e.key === 'Escape'){ gloss.classList.remove('open'); hideCard(); return; }
    /* keyboard route to 釘選: the preview of the focused link is open, P pins it */
    if ((e.key === 'p' || e.key === 'P') && curKey && card.style.display === 'block'){ e.preventDefault(); pinCurrent(); return; }
    if (e.key === 'g' || e.key === 'G'){ buildGloss(); gloss.classList.toggle('open'); }
    if (e.key === 'Backspace'){ e.preventDefault(); goBack(); }
  });
  if (HAS_READER){
    gloss.addEventListener('click', function(e){ if (e.target === gloss) gloss.classList.remove('open'); });
    pill.addEventListener('click', goBack);
  }

  /* 本節速查 rail: the section in view, its decorated tokens and figures. */
  var railEl = document.getElementById('rail'), railHead = document.getElementById('railhead'),
      railBody = document.getElementById('railbody'), railFor = null;
  function rail(best){
    if (!railEl) return;
    var sec = null;
    if (best){ var target = document.getElementById(best.getAttribute('href').slice(1)); if (target) sec = target.closest('section.ch') || target; }
    if (!sec) sec = document.querySelector('section.ch');
    if (!sec || sec === railFor) return; railFor = sec;
    var h = sec.querySelector('h2');
    railHead.textContent = '';
    var rt = document.createElement('div'); rt.className = 'rt'; rt.textContent = '本節速查'; railHead.appendChild(rt);
    var rs = document.createElement('div'); rs.className = 'rs'; rs.textContent = h ? h.textContent : ''; railHead.appendChild(rs);
    railBody.textContent = '';
    var seen = {}, n = 0, hd = null;
    sec.querySelectorAll('span[data-key]').forEach(function(sp){
      var k = sp.dataset.key, e0 = entryFor(k);
      if (e0 && e0.a && entryFor(e0.a)) k = e0.a;   /* SH-14: a synonym folds into its standard entry */
      if (seen[k]) return; seen[k] = 1;
      var e = entryFor(k); if (!e) return;
      if (!hd){ hd = document.createElement('h3'); hd.textContent = '代號與名詞'; railBody.appendChild(hd); }
      var r = document.createElement('div'); r.className = 'gl-row' + (e.s ? ' jump' : ''); if (e.s) r.dataset.sid = e.s;
      var a = document.createElement('span'); a.className = 'gl-k'; a.textContent = e.k || k;
      var b = document.createElement('span'); b.textContent = e.d;
      r.appendChild(a); r.appendChild(b); railBody.appendChild(r); n++;
    });
    if (!n){ var none = document.createElement('div'); none.className = 'rs'; none.style.fontWeight = '400'; none.style.color = 'var(--muted)'; none.textContent = '本節沒有代號'; railBody.appendChild(none); }
    var figs = sec.querySelectorAll('figure.tb');
    if (figs.length){
      var fh = document.createElement('h3'); fh.textContent = '本節圖表'; railBody.appendChild(fh);
      figs.forEach(function(f, i){
        var c = f.querySelector('figcaption'); if (!f.id) f.id = sec.id + '-fig' + (i + 1);
        var a = document.createElement('a'); a.className = 'rf'; a.setAttribute('href', '#' + f.id);
        a.textContent = c ? c.textContent.slice(0, 60) + (c.textContent.length > 60 ? '…' : '') : '圖 ' + (i + 1); railBody.appendChild(a);
      });
    }
  }
  /* current-section highlight over the server-rendered sub-links of the current page */
  var links = Array.prototype.slice.call(document.querySelectorAll('#side a[data-sec]'));
  /* SH-12: input handlers (scroll, resize, pointermove) only record and schedule; the work runs at most once per
     frame, when layout is already clean, so a burst of events never forces one layout per event. */
  function perFrame(fn){
    var q = 0;
    return function(){ if (!q) q = window.requestAnimationFrame(function(){ q = 0; fn(); }); };
  }
  var scrollJobs = [];
  window.addEventListener('scroll', perFrame(function(){ scrollJobs.forEach(function(f){ f(); }); }), {passive:true});
  function cur(){
    var y = window.scrollY + 120, best = null;
    links.forEach(function(a){ var el = document.getElementById(a.getAttribute('href').slice(1)); if (el && el.getBoundingClientRect().top + window.scrollY <= y) best = a; });
    links.forEach(function(a){ a.classList.toggle('cur', a === best); });
    rail(best);
  }
  scrollJobs.push(cur);

  /* evidence table: text filter + kind/subsystem selects; the state lives in the URL query string. */
  function evidenceFilter(){
    var table = document.getElementById('evtab'); if (!table) return;
    var q = document.getElementById('evq'), kind = document.getElementById('evkind'), sub = document.getElementById('evsub'),
        count = document.getElementById('evcount');
    var rows = Array.prototype.slice.call(table.tBodies[0].rows), hay = null;
    var params = new URLSearchParams(location.search);
    q.value = params.get('q') || ''; kind.value = params.get('kind') || ''; sub.value = params.get('sub') || '';
    if (kind.value !== (params.get('kind') || '')) kind.value = '';
    if (sub.value !== (params.get('sub') || '')) sub.value = '';
    function apply(writeUrl){
      if (!hay) hay = rows.map(function(r){ return r.textContent.toLowerCase(); });
      var needle = q.value.trim().toLowerCase(), k = kind.value, s = sub.value, shown = 0;
      rows.forEach(function(r, i){
        var ok = (!needle || hay[i].indexOf(needle) >= 0) && (!k || r.dataset.kind === k) && (!s || r.dataset.sub === s);
        r.hidden = !ok; if (ok) shown++;
      });
      count.textContent = '顯示 ' + shown + ' / ' + rows.length + ' 筆';
      if (writeUrl){
        var p = new URLSearchParams();
        if (q.value.trim()) p.set('q', q.value.trim()); if (k) p.set('kind', k); if (s) p.set('sub', s);
        var qs = p.toString();
        try { history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash); }
        catch (e) { fail('evidence-filter replaceState', e); }
      }
    }
    q.addEventListener('input', function(){ apply(true); });
    kind.addEventListener('change', function(){ apply(true); });
    sub.addEventListener('change', function(){ apply(true); });
    apply(false);
    /* a filtered-out row would hide the anchor the URL points at: keep the targeted row visible */
    if (location.hash){ var t = document.getElementById(location.hash.slice(1)); if (t && t.hidden){ t.hidden = false; } }
  }

  /* The destination lives in the URL, so a reload / Back / Forward must land on the same view. The browser restores the
     window scroll but not the scroll of a nested container (the evidence tables), so a target inside one is re-aligned. */
  function restoreHash(){
    if (!location.hash) return;
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (el && el.closest && el.closest('.twrap.scroll')) el.scrollIntoView({behavior:'instant', block:'start'});
  }

  /* ---- resizable side columns (WC-P5-03 section 1)
     --nav-w / --rail-w on :root drive the layout (site.css). The user's widths go to --nav-w-set / --rail-w-set; unset
     means the CSS default. Bounds: nav 180-480, rail 200-560, main never under 480 px (the dragged side gives way).
     One localStorage key holds both widths and both collapsed flags; every access is inside try/catch and a stored value
     that does not parse or is out of bounds is ignored, so the page renders with storage absent or throwing. */
  var LKEY = 'research-site-layout-v1';
  var SPEC = {nav:{min:180, max:480}, rail:{min:200, max:560}}, MAIN_MIN = 480, STEP = 16;
  var mqNav = window.matchMedia('(min-width:921px)'), mqRail = window.matchMedia('(min-width:1500px)');
  var root = document.documentElement;
  var vw = root.clientWidth;   /* read on init and resize only (SH-12): never between a style write and the next frame */
  var L = {nav:null, rail:null, navOff:false, railOff:false};
  var HDL = {}, TGL = {};
  function numOk(v, side){ return typeof v === 'number' && isFinite(v) && v >= SPEC[side].min && v <= SPEC[side].max; }
  function loadLayout(){
    try {
      var raw = window.localStorage.getItem(LKEY); if (!raw) return;
      var o = JSON.parse(raw); if (!o || typeof o !== 'object') return;
      if (numOk(o.nav, 'nav')) L.nav = o.nav;
      if (numOk(o.rail, 'rail')) L.rail = o.rail;
      if (o.navOff === true) L.navOff = true;
      if (o.railOff === true) L.railOff = true;
    } catch (e) { fail('layout-load', e); }
  }
  function saveLayout(){
    try { window.localStorage.setItem(LKEY, JSON.stringify(L)); } catch (e) { fail('layout-save', e); }
  }
  function shownSide(side){ return side === 'nav' ? mqNav.matches : mqRail.matches; }
  function defW(side){ return side === 'nav' ? 310 : Math.min(300, Math.max(220, window.innerWidth * 0.16)); }
  function widthOf(side){
    if (!shownSide(side) || L[side + 'Off']) return 0;
    return L[side] != null ? L[side] : defW(side);
  }
  function bounds(side){
    var other = widthOf(side === 'nav' ? 'rail' : 'nav');
    return [SPEC[side].min, Math.max(SPEC[side].min, Math.min(SPEC[side].max, vw - other - MAIN_MIN))];
  }
  function clampW(side, w){ var b = bounds(side); return Math.min(b[1], Math.max(b[0], w)); }
  function applyLayout(){
    ['nav', 'rail'].forEach(function(side){
      var off = !!L[side + 'Off'], sh = shownSide(side);
      if (L[side] != null && sh && !off) root.style.setProperty('--' + side + '-w-set', Math.round(clampW(side, L[side])) + 'px');
      else root.style.removeProperty('--' + side + '-w-set');
      root.classList.toggle(side + '-off', off);
      var h = HDL[side], g = TGL[side]; if (!h || !g) return;
      /* aria-valuenow comes from the state, not from a layout read: the CSS width is exactly this value */
      var b = bounds(side), w = (sh && !off) ? Math.round(clampW(side, widthOf(side))) : 0;
      h.setAttribute('aria-valuemin', String(off ? 0 : b[0])); h.setAttribute('aria-valuemax', String(b[1])); h.setAttribute('aria-valuenow', String(w));
      g.setAttribute('aria-expanded', off ? 'false' : 'true');
      g.setAttribute('aria-label', (off ? '展開' : '收合') + (side === 'nav' ? '導覽欄' : '速查欄'));
      g.textContent = (side === 'nav') === off ? '›' : '‹';
    });
  }
  function currentWidth(side){ var el = side === 'nav' ? document.getElementById('side') : railEl; return el ? el.getBoundingClientRect().width : 0; }
  function setWidth(side, w){ L[side] = Math.round(clampW(side, w)); L[side + 'Off'] = false; applyLayout(); }
  function resetSide(side){ L[side] = null; L[side + 'Off'] = false; applyLayout(); saveLayout(); }
  function bindHandle(h, side){
    var grab = 0, want = null;
    function pos(e){ return side === 'nav' ? e.clientX : vw - e.clientX; }
    var flush = perFrame(function(){ if (want != null) { setWidth(side, want); want = null; } });
    h.addEventListener('pointerdown', function(e){
      if (e.button !== 0) return;
      e.preventDefault();
      grab = pos(e) - (L[side + 'Off'] ? 0 : currentWidth(side));
      try { h.setPointerCapture(e.pointerId); } catch (x) { fail('pointer-capture', x); }
      h.classList.add('drag');
    });
    h.addEventListener('pointermove', function(e){
      if (!h.classList.contains('drag')) return;
      want = pos(e) - grab; flush();
    });
    function end(e){
      if (!h.classList.contains('drag')) return;
      h.classList.remove('drag');
      if (want != null) { setWidth(side, want); want = null; }   /* the last position lands even if its frame has not run */
      try { h.releasePointerCapture(e.pointerId); } catch (x) { /* already released */ }
      saveLayout();
    }
    h.addEventListener('pointerup', end);
    h.addEventListener('pointercancel', end);
    h.addEventListener('dblclick', function(){ resetSide(side); });
    h.addEventListener('keydown', function(e){
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var d = 0;
      /* the arrows move the separator: for the rail, ArrowLeft makes the column wider */
      if (e.key === 'ArrowRight') d = side === 'nav' ? STEP : -STEP;
      else if (e.key === 'ArrowLeft') d = side === 'nav' ? -STEP : STEP;
      else if (e.key === 'Home'){ e.preventDefault(); resetSide(side); return; }
      else return;
      e.preventDefault();
      var base = L[side + 'Off'] ? defW(side) - d : currentWidth(side);
      setWidth(side, base + d); saveLayout();
    });
  }
  function initLayout(){
    ['nav', 'rail'].forEach(function(side){
      var h = document.createElement('div');
      h.id = 'h' + side; h.className = 'hdl hdl-' + side; h.tabIndex = 0;
      h.setAttribute('role', 'separator'); h.setAttribute('aria-orientation', 'vertical');
      h.setAttribute('aria-label', side === 'nav' ? '調整導覽欄寬度' : '調整速查欄寬度');
      h.title = '拖曳調整寬度 · 方向鍵微調 · 雙擊或 Home 還原';
      var g = document.createElement('button');
      g.type = 'button'; g.id = 't' + side; g.className = 'tgl tgl-' + side;
      g.addEventListener('click', function(){ L[side + 'Off'] = !L[side + 'Off']; applyLayout(); saveLayout(); });
      document.body.appendChild(h); document.body.appendChild(g);
      HDL[side] = h; TGL[side] = g;
      bindHandle(h, side);
    });
    loadLayout();
    applyLayout();
    window.addEventListener('resize', perFrame(function(){ vw = root.clientWidth; applyLayout(); }));
  }

  /* ---- self-test print, nav filter, narrow-window nav drawer (accepted 2026-10-18, course-notes site)
     details.quiz: every closed one opens before printing and closes again after.
     Filter: an input at the top of #side. Sections of this page (a[data-sec]) match on title + section text; links
     a builder lists hidden as a.xs (other pages' sections) match on title only and appear under their page's l1.
     Drawer (<=920 px, html.drawer): #side slides in over a scrim from a sticky #navbar that names the current
     section; Esc, the scrim or a link closes it. JS-dead: answers still print (CSS), the nav stays stacked. */
  function quizPrint(){
    var reopened = [];
    window.addEventListener('beforeprint', function(){
      document.querySelectorAll('details.quiz:not([open])').forEach(function(d){ d.open = true; reopened.push(d); });
    });
    window.addEventListener('afterprint', function(){ reopened.forEach(function(d){ d.open = false; }); reopened = []; });
  }
  var navq = null;
  function navFilter(){
    var side = document.getElementById('side'); if (!side) return;
    navq = document.createElement('input');
    navq.type = 'search'; navq.className = 'navq'; navq.id = 'navq';
    navq.placeholder = '篩選章節與小節…'; navq.setAttribute('aria-label', '篩選章節與小節');
    var count = document.createElement('div'); count.className = 'navq-n'; count.setAttribute('aria-live', 'polite'); count.hidden = true;
    var first = side.querySelector('a');
    side.insertBefore(navq, first); side.insertBefore(count, first);
    var groups = [], g = null;
    Array.prototype.forEach.call(side.querySelectorAll('a'), function(a){
      if (a.classList.contains('l1')) { g = {head:a, items:[]}; groups.push(g); }
      else if (g && (a.classList.contains('l2') || a.classList.contains('l3'))) g.items.push(a);
    });
    var hay = new Map();
    function textOf(a){
      if (hay.has(a)) return hay.get(a);
      var t = a.textContent;
      if (a.hasAttribute('data-sec')) { var s = document.getElementById(a.getAttribute('href').slice(1)); if (s) t += ' ' + s.textContent; }
      t = t.toLowerCase(); hay.set(a, t); return t;
    }
    function apply(){
      var q = navq.value.trim().toLowerCase(), hits = 0;
      groups.forEach(function(gr){
        var any = false;
        gr.items.forEach(function(a){
          var show = q ? textOf(a).indexOf(q) >= 0 : !a.classList.contains('xs');
          a.hidden = !show; if (show && q) { any = true; hits++; }
        });
        var headHit = !!q && gr.head.textContent.toLowerCase().indexOf(q) >= 0;
        if (headHit && !any) hits++;
        gr.head.hidden = !!q && !headHit && !any && gr.items.length > 0;
      });
      count.hidden = !q; count.textContent = hits ? hits + ' 個符合' : '沒有符合的章節或小節';
    }
    navq.addEventListener('input', apply);
    navq.addEventListener('keydown', function(e){ if (e.key === 'Escape' && navq.value) { e.stopPropagation(); navq.value = ''; apply(); } });
  }
  function navDrawer(){
    var side = document.getElementById('side'); if (!side) return;
    var mq = window.matchMedia('(max-width:920px)'), html = document.documentElement;
    var bar = document.createElement('button');
    bar.type = 'button'; bar.id = 'navbar';
    bar.setAttribute('aria-controls', 'side'); bar.setAttribute('aria-expanded', 'false');
    var lab = document.createElement('span'); lab.textContent = '☰ 目錄';
    var curEl = document.createElement('span'); curEl.className = 'nb-cur';
    bar.appendChild(lab); bar.appendChild(curEl);
    var scrim = document.createElement('div'); scrim.id = 'scrim';
    side.parentNode.insertBefore(bar, side.nextSibling);
    document.body.appendChild(scrim);
    html.classList.add('drawer');
    /* The filter box takes focus only when the drawer was opened from the keyboard (click detail 0). A pointer open
       must not focus it: on a phone that pops the keyboard and, with a < 16 px field, zooms the page (A4, 2026-10-18). */
    function setOpen(o, byKey){
      html.classList.toggle('nav-open', o); bar.setAttribute('aria-expanded', o ? 'true' : 'false');
      if (o && navq && byKey) navq.focus({preventScroll:true});
      else if (!o && side.contains(document.activeElement)) bar.focus({preventScroll:true});
    }
    bar.addEventListener('click', function(e){ setOpen(!html.classList.contains('nav-open'), e.detail === 0); });
    scrim.addEventListener('click', function(){ setOpen(false); });
    side.addEventListener('click', function(e){ if (mq.matches && e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && html.classList.contains('nav-open')) setOpen(false); });
    mq.addEventListener('change', function(){ if (!mq.matches) setOpen(false); });
    var page = side.querySelector('a.l1[aria-current="page"]');
    function label(){ var c = side.querySelector('a.cur'); curEl.textContent = c ? c.textContent : (page ? page.textContent : ''); }
    scrollJobs.push(label); label();
  }

  /* ---- content update stamp (SH-16, 2026-10-26, course notes): a builder writes the date a page's CONTENT last changed
     as <time datetime="YYYY-MM-DD" data-fresh="14">, never the build day, so a rebuild without a content change is
     byte-identical. Whether that date is still "new" depends on the reader's day, not the build's, so the badge is
     added here: 0 <= age < data-fresh days -> time.fresh plus a span.upd-new (label: data-fresh-label, default 已更新).
     JS-dead degradation: the date still shows, without the badge. */
  function updStamp(){
    var now = new Date(), today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    document.querySelectorAll('time[data-fresh]').forEach(function(t){
      var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(t.getAttribute('datetime') || ''); if (!m) return;
      var age = Math.round((today - Date.UTC(+m[1], +m[2] - 1, +m[3])) / 864e5);
      var win = parseInt(t.getAttribute('data-fresh'), 10);
      if (!(age >= 0 && age < win)) return;
      t.classList.add('fresh');
      var b = document.createElement('span'); b.className = 'upd-new';
      b.textContent = t.getAttribute('data-fresh-label') || '已更新';
      t.parentNode.insertBefore(b, t.nextSibling);
    });
  }

  try { cur(); decorate(); } catch (e) { fail('decorate', e); }
  try { updStamp(); } catch (e) { fail('update-stamp', e); }
  try { quizPrint(); } catch (e) { fail('quiz-print', e); }
  try { navFilter(); } catch (e) { fail('nav-filter', e); }
  try { navDrawer(); } catch (e) { fail('nav-drawer', e); }
  try { decorateLinks(); } catch (e) { fail('link-previews', e); }
  try { evidenceFilter(); } catch (e) { fail('evidence-filter', e); }
  try { restoreHash(); } catch (e) { fail('restore-hash', e); }
  try { initLayout(); } catch (e) { fail('layout', e); }
  window.addEventListener('pageshow', function(ev){ if (ev.persisted) { try { restoreHash(); } catch (e) { fail('restore-hash', e); } } });
})();
