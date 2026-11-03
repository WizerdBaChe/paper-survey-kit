"""html-explainer carrier: explainer/1 content -> ONE self-contained .html file.

render(content, content_dir, out_path) -> None   (the build.py contract)

The page is the accepted reading shell (AssetVault asset research-site-shell, vendored byte-identical
under vendor/) filled according to its DOM contract: #side nav, main > section.ch > h2, #rail[data-rail]
(本節速查), #gloss overlay, #refcard hover card, #pins, #backpill, script#previews, window.SITE_REFS /
SITE_SYMS. Vendored CSS and JS are inlined, figures are embedded as data URIs: nothing loads from outside.

Determinism: no clock, no random, no dict-order dependence; the same content (and the same figure bytes)
gives a byte-identical file. Line endings of the vendored files are normalised to LF before inlining so a
CRLF/LF checkout of the tools repo does not change the output.

Inline markup is parsed ONLY by common/inline.py; this module renders its tokens.
"""
import base64
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
from common import inline  # noqa: E402

VENDOR = HERE / "vendor"
PAGE_CLASS = "document-long"

# Section ids of content are [a-z0-9-]; generated ids use '_' so they can never collide with them.
GLOSSARY_SID = "x_glossary"
REFS_SID = "x_refs"

IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
              ".webp": "image/webp", ".svg": "image/svg+xml"}
CALLOUT = {"key": ("def", "重點"), "note": ("src", "備註"), "warn": ("warn", "注意")}

# Carrier layer: only the elements the shell has no vocabulary for (steps, metrics, quote, glossary list,
# colophon labels). It adds no type tier (sizes come from the prose layer's four tiers) and no max-width.
CARRIER_CSS = """\
/* html-explainer carrier layer (not vendored) */
.pagehead{margin-bottom:8px;}
.pagehead .lead{margin:0 0 14px;color:var(--muted);}
table caption{caption-side:top;text-align:left;font-family:var(--sans);font-size:var(--pdl-meta,14px);color:var(--muted);padding:8px 10px 4px;}
ol.steps{list-style:none;counter-reset:st;padding:0;margin:14px 0;}
ol.steps > li{counter-increment:st;display:grid;grid-template-columns:2.2em 1fr;gap:0 10px;padding:10px 0;margin:0;border-bottom:1px solid var(--line);}
ol.steps > li:last-child{border-bottom:none;}
ol.steps > li::before{content:counter(st);grid-row:1 / span 2;font-family:var(--sans);font-weight:700;color:var(--glass);}
ol.steps .st-t{font-weight:700;}
ol.steps .st-d{grid-column:2;}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:14px;margin:16px 0;}
.metric{background:var(--plate);border:1px solid var(--line);padding:10px 14px;min-width:0;}
.metric .mv{font-size:var(--pdl-h3,20px);line-height:1.3;}
.metric .mu{font-family:var(--sans);font-size:var(--pdl-meta,14px);color:var(--muted);margin-left:4px;}
.metric .ml{font-family:var(--sans);font-weight:700;font-size:var(--pdl-meta,14px);}
.metric .mn{font-family:var(--sans);font-size:var(--pdl-meta,14px);color:var(--muted);}
blockquote.quote{margin:16px 0;padding:2px 0 2px 16px;border-left:2px solid var(--line);}
blockquote.quote p{margin:0 0 6px;}
blockquote.quote footer{font-family:var(--sans);font-size:var(--pdl-meta,14px);color:var(--muted);}
figure.tb figcaption{font-weight:700;color:var(--ink);}
figure.tb .fnotes{font-family:var(--sans);font-size:var(--pdl-meta,14px);color:var(--muted);padding:2px 0 4px;}
figure.tb .fnotes span{display:block;}
dl.gl{margin:12px 0;}
dl.gl dt{font-family:var(--sans);font-weight:700;margin-top:12px;scroll-margin-top:16px;}
dl.gl dt .en{font-weight:400;color:var(--muted);}
dl.gl dd{margin:2px 0 0;}
ol.refs{padding-left:1.6em;margin:12px 0;}
ol.refs li{scroll-margin-top:16px;}
ol.refs .rl{font-weight:700;}
#rail .rx .rsum{color:var(--muted);margin:0 0 6px;}
#rail .rx ul{margin:4px 0 8px;padding-left:18px;}
#rail .rx li{margin:2px 0;}
"""

# Carrier-owned rail extension: the shell's rail lists the tokens and figures of the section in view; the
# card also wants that section's summary and takeaways there. This script adds them on top of whatever the
# shell built, from script#rail-data (textContent only). Without it the shell's rail still works.
RAIL_JS = """\
(function(){
  'use strict';
  function fail(where, e){ try { console.error(JSON.stringify({site:'html-explainer', where:where, error:String(e && e.message || e)})); } catch(_){} }
  var D = {}, body = document.getElementById('railbody');
  try { D = JSON.parse(document.getElementById('rail-data').textContent) || {}; } catch (e) { fail('rail-data', e); }
  if (!body) return;
  function current(){
    var secs = document.querySelectorAll('main section.ch'), y = window.scrollY + 120, best = null;
    for (var i = 0; i < secs.length; i++){ if (secs[i].getBoundingClientRect().top + window.scrollY <= y) best = secs[i]; }
    return best || secs[0] || null;
  }
  function ensure(){
    try {
      var sec = current(); if (!sec) return;
      var have = body.querySelector('.rx');
      if (have && have.getAttribute('data-sec') === sec.id) return;
      if (have) body.removeChild(have);
      var d = D[sec.id]; if (!d || (!d.s && !(d.t && d.t.length))) return;
      var box = document.createElement('div'); box.className = 'rx'; box.setAttribute('data-sec', sec.id);
      if (d.s){ var s = document.createElement('div'); s.className = 'rsum'; s.textContent = d.s; box.appendChild(s); }
      if (d.t && d.t.length){
        var h = document.createElement('h3'); h.textContent = '本節重點'; box.appendChild(h);
        var ul = document.createElement('ul');
        d.t.forEach(function(t){ var li = document.createElement('li'); li.textContent = t; ul.appendChild(li); });
        box.appendChild(ul);
      }
      body.insertBefore(box, body.firstChild);
    } catch (e) { fail('rail-extra', e); }
  }
  try { new MutationObserver(ensure).observe(body, {childList: true}); } catch (e) { fail('rail-observe', e); }
  ensure();
})();
"""


def esc(s):
    return html.escape(s, quote=True)


def _vendor(name):
    text = (VENDOR / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
    return text if text.endswith("\n") else text + "\n"


def _json_for_script(obj):
    """JSON that is safe inside <script>: '<' and the JS line separators never appear raw."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class _Ctx:
    """Id -> display maps used by the inline renderer."""

    def __init__(self, content):
        self.glossary = {g["id"]: g for g in content.get("glossary", [])}
        self.refs = {r["id"]: r for r in content.get("refs", [])}
        self.sections = {s["id"]: s for s in content["sections"]}
        used = set()
        self.gkey, self.rkey = {}, {}
        for g in content.get("glossary", []):
            self.gkey[g["id"]] = self._unique(g["term"], g["id"], used)
        for r in content.get("refs", []):
            self.rkey[r["id"]] = self._unique(r["label"], r["id"], used)
        # plain forms for places that cannot carry markup (nav, rail, <title>, SITE_* entries)
        self.p_gloss = {i: g["term"] for i, g in self.glossary.items()}
        self.p_refs = {i: r["label"] for i, r in self.refs.items()}
        self.p_secs = {i: inline.plain(s["heading"], self.p_gloss, self.p_refs) for i, s in self.sections.items()}

    @staticmethod
    def _unique(key, ident, used):
        k = key if key not in used else f"{key}（{ident}）"
        used.add(k)
        return k

    def plain(self, text):
        return inline.plain(text, self.p_gloss, self.p_refs, self.p_secs)

    def inl(self, text):
        out = []
        for kind, val in inline.tokens(text):
            if kind == "text":
                out.append(esc(val))
            elif kind == "bold":
                out.append(f"<b>{esc(val)}</b>")
            elif kind == "gloss":
                out.append(f'<span class="sym" tabindex="0" data-key="{esc(self.gkey[val])}">{esc(self.glossary[val]["term"])}</span>')
            elif kind == "ref":
                out.append(f'<span class="ref" tabindex="0" data-key="{esc(self.rkey[val])}">{esc(self.refs[val]["label"])}</span>')
            else:  # sec
                out.append(f'<a href="#{esc(val)}">{esc(self.p_secs[val])}</a>')
        return "".join(out)


def _figure(block, content_dir, sid, n, ctx):
    path = Path(content_dir) / block["src"]
    mime = IMAGE_MIME.get(path.suffix.lower())
    if mime is None:
        raise ValueError(f"figure {block['src']}: unsupported image type {path.suffix!r}; known {sorted(IMAGE_MIME)}")
    uri = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    # The caption stays alone in <figcaption>: the shell's rail lists figures by that element's text.
    notes = [f'<span class="fshow">圖中呈現：{ctx.inl(block["shows"])}</span>']
    if block.get("not_drawn"):
        notes.append(f'<span class="fnot">未畫出：{ctx.inl(block["not_drawn"])}</span>')
    return (f'<figure class="tb" id="{sid}-fig{n}"><img src="{uri}" alt="{esc(ctx.plain(block["caption"]))}">'
            f'<figcaption>{ctx.inl(block["caption"])}</figcaption>'
            f'<div class="fnotes">{"".join(notes)}</div></figure>')


def _block(block, content_dir, sid, state, ctx):
    t = block["type"]
    if t == "para":
        return f"<p>{ctx.inl(block['text'])}</p>"
    if t == "bullets":
        return "<ul>" + "".join(f"<li>{ctx.inl(i)}</li>" for i in block["items"]) + "</ul>"
    if t == "steps":
        lis = []
        for it in block["items"]:
            d = f'<span class="st-d">{ctx.inl(it["text"])}</span>' if it.get("text") else ""
            lis.append(f'<li><span class="st-t">{ctx.inl(it["title"])}</span>{d}</li>')
        return '<ol class="steps" role="list">' + "".join(lis) + "</ol>"
    if t == "table":
        cap = f"<caption>{ctx.inl(block['caption'])}</caption>" if block.get("caption") else ""
        head = "<tr>" + "".join(f'<th scope="col">{ctx.inl(c)}</th>' for c in block["columns"]) + "</tr>"
        rows = "".join("<tr>" + "".join(f"<td>{ctx.inl(c)}</td>" for c in row) + "</tr>" for row in block["rows"])
        return f'<div class="twrap"><table>{cap}<thead>{head}</thead><tbody>{rows}</tbody></table></div>'
    if t == "figure":
        state["fig"] += 1
        return _figure(block, content_dir, sid, state["fig"], ctx)
    if t == "callout":
        cls, default = CALLOUT[block["kind"]]
        tag = ctx.inl(block["title"]) if block.get("title") else default
        return f'<div class="box {cls}" data-kind="{block["kind"]}"><span class="tag">{tag}</span>{ctx.inl(block["text"])}</div>'
    if t == "metrics":
        cells = []
        for it in block["items"]:
            unit = f'<span class="mu">{esc(it["unit"])}</span>' if it.get("unit") else ""
            note = f'<div class="mn">{ctx.inl(it["note"])}</div>' if it.get("note") else ""
            cells.append(f'<div class="metric"><div class="mv"><span class="val">{esc(it["value"])}</span>{unit}</div>'
                         f'<div class="ml">{ctx.inl(it["label"])}</div>{note}</div>')
        return '<div class="metrics">' + "".join(cells) + "</div>"
    if t == "quote":
        src = f"<footer>{ctx.inl(block['source'])}</footer>" if block.get("source") else ""
        return f'<blockquote class="quote"><p>{ctx.inl(block["text"])}</p>{src}</blockquote>'
    raise ValueError(f"unknown block type {t!r}")


def _section(sec, content_dir, ctx):
    state = {"fig": 0}
    parts = [f'<section class="ch" id="{esc(sec["id"])}" data-kind="content">', f"<h2>{ctx.inl(sec['heading'])}</h2>"]
    if sec.get("summary"):
        parts.append(f'<div class="chsub">{ctx.inl(sec["summary"])}</div>')
    parts += [_block(b, content_dir, sec["id"], state, ctx) for b in sec["blocks"]]
    parts.append("</section>")
    return "\n".join(parts)


def _glossary_section(content, ctx):
    rows = []
    for g in content["glossary"]:
        en = f' <span class="en">({esc(g["en"])})</span>' if g.get("en") else ""
        rows.append(f'<dt id="g_{esc(g["id"])}">{esc(g["term"])}{en}</dt><dd>{ctx.inl(g["gloss"])}</dd>')
    return (f'<section class="ch" id="{GLOSSARY_SID}" data-kind="glossary">\n<h2>詞彙</h2>\n'
            f'<dl class="gl">{"".join(rows)}</dl>\n</section>')


def _refs_section(content, ctx):
    lis = []
    for r in content["refs"]:
        detail = f" — {ctx.inl(r['detail'])}" if r.get("detail") else ""
        link = f' <a href="{esc(r["href"])}" rel="noopener">{esc(r["href"])}</a>' if r.get("href") else ""
        lis.append(f'<li id="r_{esc(r["id"])}"><span class="rl">{esc(r["label"])}</span>{detail}{link}</li>')
    return (f'<section class="ch" id="{REFS_SID}" data-kind="refs">\n<h2>出處</h2>\n'
            f'<ol class="refs">{"".join(lis)}</ol>\n</section>')


def render(content, content_dir, out_path):
    ctx = _Ctx(content)
    meta = content["meta"]
    secs = content["sections"]

    # registries for the shell's hover cards: n=true -> only explicit markers get a card (no text scanning)
    syms = {}
    for g in content.get("glossary", []):
        t = f'{g["term"]} — {g["en"]}' if g.get("en") else g["term"]
        syms[ctx.gkey[g["id"]]] = {"t": t, "d": ctx.plain(g["gloss"]), "s": f"#g_{g['id']}", "n": True}
    refs = {}
    for r in content.get("refs", []):
        refs[ctx.rkey[r["id"]]] = {"t": r["label"], "d": ctx.plain(r.get("detail") or r.get("href") or r["label"]),
                                   "s": f"#r_{r['id']}", "n": True}

    nav = [f'<a class="l1" href="#{esc(s["id"])}" data-sec>{esc(ctx.p_secs[s["id"]])}</a>' for s in secs]
    extra = []
    if content.get("glossary"):
        extra.append(f'<a class="l1" href="#{GLOSSARY_SID}" data-sec>詞彙</a>')
    if content.get("refs"):
        extra.append(f'<a class="l1" href="#{REFS_SID}" data-sec>出處</a>')
    if extra:
        nav.append('<div class="grp">附錄</div>')
        nav += extra

    rail = {}
    for s in secs:
        d = {}
        if s.get("summary"):
            d["s"] = ctx.plain(s["summary"])
        if s.get("takeaways"):
            d["t"] = [ctx.plain(t) for t in s["takeaways"]]
        if d:
            rail[s["id"]] = d

    head_block = ['<header class="pagehead">', f'<div class="eyebrow">{esc(meta["date"])}</div>',
                  f'<h1 class="title">{ctx.inl(meta["title"])}</h1>']
    if meta.get("subtitle"):
        head_block.append(f'<p class="lead">{ctx.inl(meta["subtitle"])}</p>')
    head_block.append("</header>")
    if meta.get("purpose"):
        head_block.append(f'<div class="box def"><span class="tag">閱讀目的</span>{ctx.inl(meta["purpose"])}</div>')

    body_secs = [_section(s, content_dir, ctx) for s in secs]
    if content.get("glossary"):
        body_secs.append(_glossary_section(content, ctx))
    if content.get("refs"):
        body_secs.append(_refs_section(content, ctx))

    colo = [f'<p>日期 <span class="val">{esc(meta["date"])}</span>']
    if meta.get("author"):
        colo[0] += f'　｜　作者 {esc(meta["author"])}'
    colo[0] += "</p>"
    if meta.get("source_note"):
        colo.append(f'<p>{ctx.inl(meta["source_note"])}</p>')

    css_site, css_prose, js_site = _vendor("site.css"), _vendor("prose-doc-layer.css"), _vendor("site.js")
    if "</style" in (css_site + css_prose + CARRIER_CSS).lower() or "</script" in (js_site + RAIL_JS).lower():
        raise ValueError("inlined asset contains a closing style/script tag; refusing to build a broken page")

    doc = f"""<!doctype html>
<html lang="{esc(meta['lang'])}" data-page-class="{PAGE_CLASS}" data-audience="{esc(meta['audience'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(ctx.plain(meta['title']))}</title>
<style>
{css_site}</style>
<style>
{CARRIER_CSS}</style>
<style>
{css_prose}</style>
</head>
<body>
<nav id="side" aria-label="章節導覽"><h1>{esc(ctx.plain(meta['title']))}</h1><div class="sub">{esc(ctx.plain(meta.get('subtitle', '')))}</div>
{chr(10).join(nav)}
</nav>
<main data-sections="{esc(','.join(s['id'] for s in secs))}">
{chr(10).join(head_block)}
{chr(10).join(body_secs)}
<footer class="buildinfo">{''.join(colo)}</footer>
</main>
<aside id="rail" data-rail aria-label="本節速查"><div id="railhead"></div><div id="railbody"></div></aside>
<div id="hint"><span>虛線詞彙與出處：滑過看說明 · 點擊跳到定義處 · ⌫ 返回 · G 詞彙表</span><button class="hx" type="button" aria-label="收合這條提示">×</button></div>
<div id="gloss" role="dialog" aria-label="詞彙表"><div class="panel"><div id="glosslist"></div></div></div>
<div id="refcard" role="tooltip"></div>
<div id="pins" aria-label="釘選的預覽卡片"></div>
<button id="backpill" type="button">↩ 返回（Backspace）</button>
<script type="application/json" id="previews">{{}}</script>
<script type="application/json" id="rail-data">{_json_for_script(rail)}</script>
<script>window.SITE_REFS = {_json_for_script(refs)};
window.SITE_SYMS = {_json_for_script(syms)};</script>
<script>
{js_site}</script>
<script>
{RAIL_JS}</script>
</body>
</html>
"""
    Path(out_path).write_text(doc, encoding="utf-8", newline="\n")
