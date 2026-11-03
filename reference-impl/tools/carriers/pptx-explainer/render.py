"""pptx-explainer carrier: explainer/1 content -> 16:9 read-through deck (PPTX).

Entry point (called by tools/carriers/build.py):
    render(content: dict, content_dir: Path, out_path: Path) -> None

Layout and CJK/lang handling come from the VENDORED helpers (vendor/deck_builder.py, vendor/deck_layout.py,
byte-identical copies of the AssetVault pptx-deck-builder asset; see CARRIER.md). Inline markup is tokenised
by common/inline.py only; this file renders tokens and never re-parses a raw string.

Layout is deterministic: same content -> same slide count, same texts. Blocks are measured with the vendored
height estimators, stacked top to bottom, and a block that does not fit the remaining height starts a new
slide titled "<heading>（續）". A block larger than a whole slide is split (paragraph by sentence, bullets /
steps / table / metrics by item) or, when it cannot be split, placed anyway and reported in FINDINGS_LAST.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VENDOR = HERE / "vendor"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from common import inline  # noqa: E402


def load_vendor():
    """Import the vendored helpers from vendor/ (deck_layout imports deck_builder by module name)."""
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    out = sys.stdout
    if not hasattr(out, "reconfigure"):          # deck_builder calls sys.stdout.reconfigure() at import
        try:
            out.reconfigure = lambda **kw: None
        except Exception:
            pass
    import deck_builder as hb
    import deck_layout as lay
    for m in (hb, lay):
        if Path(m.__file__).resolve().parent != VENDOR:
            raise RuntimeError(f"{m.__name__} was loaded from {m.__file__}, not from {VENDOR}; "
                               "another deck_builder/deck_layout is shadowing the vendored copy")
    return hb, lay


H, L = load_vendor()

from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_CONNECTOR  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402
from PIL import Image  # noqa: E402

GAP = 0.22                     # vertical gap between blocks (in)
BOTTOM = L.BOT                # lowest y any content may reach (the page-number band starts at L.BOT)
IND = 0.32                     # bullet hanging indent (in)
EPS = 0.01
WARN_BG = RGBColor(0xFB, 0xEC, 0xE5)
NOTE_BAR = RGBColor(0x8A, 0x97, 0xA5)

FINDINGS_LAST: list = []       # layout findings of the last render (fit / orphan / title-wrap / overflow)
DECL_LAST: list = []           # per-page P1 declarations of the last render

KIND_ZH = {"para": "文字", "bullets": "文字", "callout": "文字", "quote": "文字", "takeaways": "文字",
           "steps": "流程圖", "table": "表", "figure": "圖", "metrics": "數字卡"}
CALLOUT = {  # kind -> (default title, fill, bar colour, title colour)
    "key": ("重點", H.GLASS_BG, L.ACCENT, L.ACCENT),
    "note": ("備註", L.SOFT, NOTE_BAR, L.INK),
    "warn": ("注意", WARN_BG, L.WARN, L.WARN),
}


# ------------------------------------------------------------------ inline tokens -> segments
class Ctx:
    def __init__(self, content):
        self.glossary = {g["id"]: g for g in content.get("glossary", [])}
        self.refs = {r["id"]: r for r in content.get("refs", [])}
        self.secs = {s["id"]: s for s in content["sections"]}

    def rich(self, text):
        """-> (segs, glossary ids used, ref ids used). segs = [(text, {"bold": True}?)]."""
        segs, gids, rids = [], [], []
        for kind, val in inline.tokens(text):
            if kind == "text":
                segs.append((val, {}))
            elif kind == "bold":
                segs.append((val, {"bold": True}))
            elif kind == "gloss":
                segs.append((self.glossary[val]["term"], {"bold": True}))
                gids.append(val)
            elif kind == "ref":
                segs.append(("〔" + self.refs[val]["label"] + "〕", {}))
                rids.append(val)
            else:  # sec
                segs.append((inline.plain(self.secs[val]["heading"],
                                          {k: g["term"] for k, g in self.glossary.items()},
                                          {k: r["label"] for k, r in self.refs.items()}), {}))
        return segs, gids, rids

    def plain(self, text):
        return seg_text(self.rich(text)[0])

    def md(self, text):
        """Markdown-ish string (**bold**) for the vendored helpers that take str (table cells, titles)."""
        segs, g, r = self.rich(text)
        return segs_md(segs), g, r


def seg_text(segs):
    return "".join(t for t, _ in segs)


def segs_md(segs):
    return "".join(f"**{t}**" if ov.get("bold") else t for t, ov in segs)


def sentences(segs):
    out, cur = [], []
    for text, ov in segs:
        buf = ""
        for ch in text:
            buf += ch
            if ch in "。！？":
                cur.append((buf, ov))
                out.append(cur)
                cur, buf = [], ""
        if buf:
            cur.append((buf, ov))
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------ small drawing helpers
class Unit:
    """One placeable piece: height h (in), draw(slide, y), plus the glossary/ref ids it shows."""

    def __init__(self, kind, h, draw, gids=(), rids=()):
        self.kind, self.h, self.draw, self.gids, self.rids = kind, h, draw, list(gids), list(rids)


def _bullets(shape, ind=IND):
    emu = int(ind * 914400)
    for p in shape.text_frame.paragraphs:
        ppr = p._p.get_or_add_pPr()
        ppr.set("marL", str(emu))
        ppr.set("indent", str(-emu))
        ppr.append(ppr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
        ppr.append(ppr.makeelement(qn("a:buChar"), {"char": "•"}))


def _last_shape(s):
    return list(s.shapes)[-1]


def _panel(s, x, y, w, h, fill, bar=None, line=None, name="panel"):
    r = H.add_rect(s, x, y, w, h, fill, line_color=line)
    r.name = name + "-bg"
    if bar is not None:
        b = H.add_rect(s, x, y, 0.09, h, bar)
        b.name = name + "-bar-bg"


def _head_y(kicker, desc_md):
    """Content top y that L.head() will return (pure arithmetic copy; render asserts they agree)."""
    y = 0.34 + (0.32 if kicker else 0)
    y += 0.62 + 0.08
    if desc_md:
        y += max(0.42, L.est_h([desc_md], L.DESC_PT, L.CW, ls=1.3))
    return y + 0.28


# ------------------------------------------------------------------ block nodes (tokenised once)
def prepare(b, c, tag):
    t = b["type"]
    if t == "para":
        segs, g, r = c.rich(b["text"])
        return {"k": "para", "tag": tag, "segs": segs, "g": g, "r": r}
    if t == "bullets":
        items = [c.rich(x) for x in b["items"]]
        return {"k": "bullets", "tag": tag, "items": items}
    if t == "steps":
        items = [(c.rich(x["title"]), c.rich(x["text"]) if x.get("text") else None) for x in b["items"]]
        return {"k": "steps", "tag": tag, "items": items, "start": 1}
    if t == "table":
        allg, allr = [], []
        header = []
        for col in b["columns"]:
            m, g, r = c.md(col); header.append(m); allg += g; allr += r
        rows = []
        for row in b["rows"]:
            out = []
            for cell in row:
                m, g, r = c.md(cell); out.append(m); allg += g; allr += r
            rows.append(out)
        cap = None
        if b.get("caption"):
            cap, g, r = c.md(b["caption"]); allg += g; allr += r
        return {"k": "table", "tag": tag, "caption": cap, "header": header, "rows": rows, "g": allg, "r": allr,
                "col_w": _col_weights(header, rows)}
    if t == "figure":
        cap, g1, r1 = c.rich(b["caption"])
        shows, g2, r2 = c.rich(b["shows"])
        nd = c.rich(b["not_drawn"]) if b.get("not_drawn") else None
        return {"k": "figure", "tag": tag, "src": b["src"], "caption": segs_md(cap), "shows": shows,
                "not_drawn": nd[0] if nd else None,
                "g": g1 + g2 + (nd[1] if nd else []), "r": r1 + r2 + (nd[2] if nd else [])}
    if t == "callout":
        segs, g, r = c.rich(b["text"])
        title = c.rich(b["title"]) if b.get("title") else None
        return {"k": "callout", "tag": tag, "kind": b["kind"], "title": title[0] if title else None, "segs": segs,
                "g": g + (title[1] if title else []), "r": r + (title[2] if title else [])}
    if t == "metrics":
        items, allg, allr = [], [], []
        for it in b["items"]:
            row = {}
            for key in ("label", "value", "unit", "note"):
                if it.get(key):
                    segs, g, r = c.rich(it[key]); row[key] = segs; allg += g; allr += r
            items.append(row)
        return {"k": "metrics", "tag": tag, "items": items, "g": allg, "r": allr}
    if t == "quote":
        segs, g, r = c.rich(b["text"])
        src = c.rich(b["source"]) if b.get("source") else None
        return {"k": "quote", "tag": tag, "segs": segs, "source": src[0] if src else None,
                "g": g + (src[1] if src else []), "r": r + (src[2] if src else [])}
    raise ValueError(f"unknown block type {t!r}")


def _col_weights(header, rows):
    ws = []
    for ci in range(len(header)):
        cells = [header[ci]] + [r[ci] for r in rows]
        # natural one-line width of the widest cell (14 pt), clamped so one long column cannot starve the others
        w = max(H._est_w_in([(L.plain(x), {})], L.TABLE_PT) for x in cells)
        ws.append(min(6.0, max(0.9, w)) + 0.3)
    return ws


# ------------------------------------------------------------------ makers: node + avail -> Unit
def make_para(n, avail):
    paras = [{"segs": n["segs"], "space_after": 0}]
    h = L.est_h(paras, L.BODY_PT, L.CW) + 0.02

    def draw(s, y):
        L.block(s, L.MX, y, L.CW, h, paras, name=n["tag"] + ".para")
    return Unit("para", h, draw, n.get("g", []), n.get("r", []))


def split_para(n, avail):
    sents = sentences(n["segs"])
    if len(sents) < 2:
        return None
    for k in range(len(sents) - 1, 0, -1):
        pre = [x for s_ in sents[:k] for x in s_]
        if L.est_h([{"segs": pre, "space_after": 0}], L.BODY_PT, L.CW) + 0.02 <= avail:
            rest = [x for s_ in sents[k:] for x in s_]
            return (make_para(dict(n, segs=pre), avail), dict(n, segs=rest))
    return None


def _bullet_paras(items):
    return [{"segs": it[0], "space_after": 6 if i < len(items) - 1 else 0} for i, it in enumerate(items)]


def make_bullets(n, avail):
    paras = _bullet_paras(n["items"])
    w = L.CW - IND
    h = L.est_h(paras, L.BODY_PT, w) + 0.02
    gids = [x for it in n["items"] for x in it[1]]
    rids = [x for it in n["items"] for x in it[2]]

    def draw(s, y):
        L.block(s, L.MX + IND, y, w, h, paras, name=n["tag"] + ".bullets")
        shp = _last_shape(s)
        shp.left = Emu(shp.left - Inches(IND))
        shp.width = Emu(shp.width + Inches(IND))
        _bullets(shp)
    return Unit("bullets", h, draw, gids, rids)


def split_bullets(n, avail):
    items = n["items"]
    for k in range(len(items) - 1, 0, -1):
        u = make_bullets(dict(n, items=items[:k]), avail)
        if u.h <= avail + EPS:
            return u, dict(n, items=items[k:])
    return None


def _steps_horizontal(n):
    items = n["items"]
    if not (2 <= len(items) <= 4):
        return False
    return all(len(seg_text(t[0])) + (len(seg_text(x[0])) if x else 0) <= 70 for t, x in items)


def make_steps(n, avail):
    items = n["items"]
    gids = [x for t, x_ in items for part in (t, x_) if part for x in part[1]]
    rids = [x for t, x_ in items for part in (t, x_) if part for x in part[2]]
    tag = n["tag"]
    if not n.get("vertical") and _steps_horizontal(n):
        cnt, gap = len(items), 0.45
        bw = (L.CW - gap * (cnt - 1)) / cnt
        inner = bw - 0.28
        allp = []
        for i, (t, x) in enumerate(items, 1):
            ps = [{"segs": [(f"{i}　", {})] + t[0], "size": 18, "bold": True, "color": L.ACCENT, "ls": 1.15,
                   "space_after": 4 if x else 0}]
            if x:
                ps.append({"segs": x[0], "ls": 1.25, "space_after": 0})
            allp.append(ps)
        bh = max(L.est_h(ps, 15, inner) for ps in allp) + 0.28 + 0.04

        def draw(s, y):
            for i, ps in enumerate(allp):
                x = L.MX + i * (bw + gap)
                r = H.add_rect(s, x, y, bw, bh, H.GLASS_BG, line_color=H.LINE)
                r.name = f"{tag}.step{i + 1}-bg"
                L.block(s, x + 0.14, y + 0.14, inner, bh - 0.28, ps, size=15, floor=14, name=f"{tag}.step{i + 1}")
                if i < cnt - 1:
                    cn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x + bw + 0.05), Inches(y + bh / 2),
                                                Inches(x + bw + gap - 0.05), Inches(y + bh / 2))
                    cn.name = f"{tag}.arrow{i + 1}"
                    cn.line.color.rgb = H.MUTED
                    cn.line.width = Pt(1.75)
                    ln = cn.line._get_or_add_ln()
                    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
                    sp = cn._element.spPr
                    sp.append(sp.makeelement(qn("a:effectLst"), {}))   # P3: no inherited theme effect
        return Unit("steps", bh, draw, gids, rids)
    # vertical numbered list
    tw = L.CW - 0.75
    rows = []
    for i, (t, x) in enumerate(items, n["start"]):
        ps = [{"segs": t[0], "size": 18, "bold": True, "color": L.ACCENT, "ls": 1.15, "space_after": 3 if x else 0}]
        if x:
            ps.append({"segs": x[0], "space_after": 0})
        rows.append((i, ps, max(0.5, L.est_h(ps, L.BODY_PT, tw)) + 0.04))
    rg = 0.12
    h = sum(r[2] for r in rows) + rg * (len(rows) - 1)

    def draw(s, y):
        yy = y
        for num, ps, rh in rows:
            bd = H.add_rect(s, L.MX, yy + 0.03, 0.46, 0.46, H.GLASS, rounded=True)
            bd.name = f"{tag}.step{num}-badge"
            tf = bd.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            H.para(tf, str(num), size=18, color=H.WHITE, bold=True, first=True, align=PP_ALIGN.CENTER, space_after=0)
            L.block(s, L.MX + 0.75, yy, tw, rh, ps, name=f"{tag}.step{num}")
            yy += rh + rg
    return Unit("steps", h, draw, gids, rids)


def split_steps(n, avail):
    """A split list is always drawn in the vertical form (numbering continues on the next slide)."""
    items = n["items"]
    for k in range(len(items) - 1, 0, -1):
        u = make_steps(dict(n, items=items[:k], vertical=True), avail)
        if u.h <= avail + EPS:
            return u, dict(n, items=items[k:], start=n["start"] + k, vertical=True)
    return None


def table_size(header, rows, col_w, max_h):
    tot = sum(col_w)
    cw = [L.CW * c / tot for c in col_w]
    allrows = [header] + rows
    sz = L.TABLE_CEIL
    while sz > L.TABLE_FLOOR and max_h is not None and sum(L._row_h(r, sz, cw) for r in allrows) > max_h:
        sz -= 0.5
    return sz, sum(L._row_h(r, sz, cw) for r in allrows)


def make_table(n, avail):
    cap_h = 0.38 if n["caption"] else 0.0
    max_h = max(avail - cap_h, 0.5)
    sz, budget = table_size(n["header"], n["rows"], n["col_w"], max_h)
    h = cap_h + budget

    def draw(s, y):
        yy = y
        if n["caption"]:
            L.caption(s, L.MX, yy, L.CW, n["caption"], h=0.34)
            yy += cap_h
        L.table(s, L.MX, yy, L.CW, n["header"], n["rows"], col_w=n["col_w"], max_h=max_h, name=n["tag"] + ".table")
    return Unit("table", h, draw, n["g"], n["r"])


def split_table(n, avail):
    rows = n["rows"]
    cap_h = 0.38 if n["caption"] else 0.0
    for k in range(len(rows) - 1, 0, -1):
        _, budget = table_size(n["header"], rows[:k], n["col_w"], avail - cap_h)
        if cap_h + budget <= avail + EPS and (k >= 2 or len(rows) == 2):
            return make_table(dict(n, rows=rows[:k]), avail), dict(n, rows=rows[k:], caption=None)
    return None


def make_figure(n, avail, content_dir):
    path = Path(content_dir) / n["src"]
    with Image.open(path) as im:
        ar = im.height / im.width                      # measured, never guessed
    pw, gap, cap_h = 0.56 * L.CW, 0.4, 0.55
    card_w = L.CW - pw - gap
    max_ph = min(avail - cap_h - 0.06, 4.3)
    ph = max(max_ph, 1.8)
    fw, fh = (pw, pw * ar) if pw * ar <= ph else (ph / ar, ph)
    # figure card: a label column and a text column per line, so the estimator sees the real text width
    lab_w, rg = 1.2, 0.12
    tw = card_w - lab_w
    crow = [("圖中呈現", n["shows"])] + ([("未畫出", n["not_drawn"])] if n["not_drawn"] else [])
    cparas = [[{"segs": segs, "size": 15, "space_after": 0}] for _, segs in crow]
    chs = [L.est_h(p, 15, tw) + 0.02 for p in cparas]
    card_h = sum(chs) + rg * (len(chs) - 1)
    h = max(fh + 0.06 + cap_h, card_h)

    def draw(s, y):
        pic = H.add_pic(s, path, L.MX, y, w=fw)
        pic.name = n["tag"] + ".figure"
        L.caption(s, L.MX, y + fh + 0.06, fw, n["caption"], h=cap_h)
        cx, yy = L.MX + pw + gap, y
        for i, ((label, _), p, ch) in enumerate(zip(crow, cparas, chs)):
            L.block(s, cx, yy, lab_w, min(0.5, ch), [{"segs": [(label, {"bold": True, "color": L.MUTED})], "size": 15,
                                              "space_after": 0}], size=15, floor=14, name=f"{n['tag']}.figcard-label{i + 1}")
            L.block(s, cx + lab_w, yy, tw, ch, p, size=15, floor=14, name=f"{n['tag']}.figcard{i + 1}")
            yy += ch + rg
    return Unit("figure", h, draw, n["g"], n["r"])


def make_callout(n, avail):
    dtitle, fill, bar, tcol = CALLOUT[n["kind"]]
    title = n["title"] if n["title"] else [(dtitle, {})]
    paras = [{"segs": title, "size": L.SUB_PT, "bold": True, "color": tcol, "ls": 1.15, "space_after": 4},
             {"segs": n["segs"], "space_after": 0}]
    tw = L.CW - 0.52
    th = L.est_h(paras, L.BODY_PT, tw) + 0.02
    h = th + 0.26

    def draw(s, y):
        _panel(s, L.MX, y, L.CW, h, fill, bar=bar, name=n["tag"] + ".callout")
        L.block(s, L.MX + 0.32, y + 0.14, tw, th, paras, name=n["tag"] + ".callout")
    return Unit("callout", h, draw, n["g"], n["r"])


def _metric_paras(it):
    vs = [(seg_text(it["value"]), {"size": 32, "bold": True, "color": L.ACCENT})] if it.get("value") else []
    if it.get("unit"):
        vs.append(("　" + seg_text(it["unit"]), {"size": 18, "bold": False, "color": L.MUTED}))
    paras = [{"segs": vs, "size": 32, "ls": 1.0, "space_after": 2}]
    if it.get("label"):
        paras.append({"segs": it["label"], "size": 15.5, "bold": True, "ls": 1.15, "space_after": 2})
    if it.get("note"):
        paras.append({"segs": it["note"], "size": 14, "color": L.MUTED, "ls": 1.25, "space_after": 0})
    paras[-1]["space_after"] = 0
    return paras


def make_metrics(n, avail):
    items = n["items"]
    ncol = n.get("ncol") or min(len(items), 4)      # a split keeps the column count of the whole block
    gap = 0.3
    cw = (L.CW - gap * (ncol - 1)) / ncol
    iw = cw - 0.36
    rows = [items[i:i + ncol] for i in range(0, len(items), ncol)]
    rhs = [max(L.est_h(_metric_paras(it), 15.5, iw) for it in row) + 0.02 + 0.28 for row in rows]
    rg = 0.2
    h = sum(rhs) + rg * (len(rows) - 1)

    def draw(s, y):
        yy = y
        for row, rh in zip(rows, rhs):
            for i, it in enumerate(row):
                x = L.MX + i * (cw + gap)
                nm = f"{n['tag']}.metric{i + 1}"
                _panel(s, x, yy, cw, rh, L.SOFT, line=H.LINE, name=nm)
                L.block(s, x + 0.18, yy + 0.14, iw, rh - 0.28, _metric_paras(it), size=15.5, floor=14, name=nm)
            yy += rh + rg
    return Unit("metrics", h, draw, n["g"], n["r"])


def split_metrics(n, avail):
    items = n["items"]
    ncol = n.get("ncol") or min(len(items), 4)
    for k in range((len(items) - 1) // ncol * ncol, 0, -ncol):          # whole rows only
        u = make_metrics(dict(n, items=items[:k], ncol=ncol), avail)
        if u.h <= avail + EPS:
            return u, dict(n, items=items[k:], ncol=ncol)
    return None


def make_quote(n, avail):
    paras = [{"segs": n["segs"], "space_after": 6 if n["source"] else 0}]
    if n["source"]:
        paras.append({"segs": [("—— ", {})] + n["source"], "size": 14, "color": L.MUTED, "ls": 1.25, "space_after": 0})
    tw = L.CW - 0.6
    th = L.est_h(paras, L.BODY_PT, tw) + 0.02
    h = th + 0.26

    def draw(s, y):
        _panel(s, L.MX, y, L.CW, h, L.SOFT, bar=L.ACCENT, name=n["tag"] + ".quote")
        L.block(s, L.MX + 0.35, y + 0.14, tw, th, paras, name=n["tag"] + ".quote")
    return Unit("quote", h, draw, n["g"], n["r"])


def make_takeaways(n, avail):
    items = n["items"]
    ncol = min(len(items), 3)
    gap = 0.35
    iw = L.CW - 0.5
    colw = (iw - gap * (ncol - 1)) / ncol
    cols = [items[i::ncol] for i in range(ncol)]
    colparas = [_bullet_paras(col) for col in cols]
    head = [{"segs": [("本節重點", {})], "size": L.SUB_PT, "bold": True, "color": L.ACCENT, "ls": 1.15,
             "space_after": 0}]
    hh = L.est_h(head, L.SUB_PT, iw) + 0.02
    ch = max(L.est_h(p, L.BODY_PT, colw - IND) for p in colparas) + 0.02
    h = 0.12 + hh + 0.04 + ch + 0.10
    gids = [x for it in items for x in it[1]]
    rids = [x for it in items for x in it[2]]

    def draw(s, y):
        r = H.add_rect(s, L.MX, y, L.CW, h, H.WHITE, line_color=H.LINE)
        r.name = n["tag"] + ".takeaways-bg"
        t = H.add_rect(s, L.MX, y, L.CW, 0.05, L.ACCENT)
        t.name = n["tag"] + ".takeaways-rule-bg"
        L.block(s, L.MX + 0.25, y + 0.12, iw, hh, head, name=n["tag"] + ".takeaways-head")
        for i, ps in enumerate(colparas):
            x = L.MX + 0.25 + i * (colw + gap)
            L.block(s, x + IND, y + 0.12 + hh + 0.04, colw - IND, ch, ps, name=f"{n['tag']}.takeaways{i + 1}")
            shp = _last_shape(s)
            shp.left = Emu(shp.left - Inches(IND))
            shp.width = Emu(shp.width + Inches(IND))
            _bullets(shp)
    return Unit("takeaways", h, draw, gids, rids)


MAKERS = {"para": make_para, "bullets": make_bullets, "steps": make_steps, "table": make_table,
          "callout": make_callout, "metrics": make_metrics, "quote": make_quote, "takeaways": make_takeaways}
SPLITTERS = {"para": split_para, "bullets": split_bullets, "steps": split_steps, "table": split_table,
             "metrics": split_metrics}


def make(n, avail, content_dir):
    if n["k"] == "figure":
        return make_figure(n, avail, content_dir)
    return MAKERS[n["k"]](n, avail)


# ------------------------------------------------------------------ pagination
class Page:
    def __init__(self):
        self.units = []
        self.end = None          # y below the last unit


def paginate(nodes, top_first, top_cont, content_dir, title):
    """Stack units top to bottom; a unit that does not fit starts a new page. -> list[Page]."""
    pages = [Page()]
    queue = list(nodes)
    cont_avail = BOTTOM - top_cont
    while queue:
        n = queue.pop(0)
        pg = pages[-1]
        top = top_first if len(pages) == 1 else top_cont
        y = (pg.end + GAP) if pg.units else top
        avail = BOTTOM - y
        u = make(n, avail, content_dir)
        if u.h <= avail + EPS:
            pg.units.append(u)
            pg.end = y + u.h
            continue
        sp = SPLITTERS.get(n["k"])
        if pg.units:
            if make(n, cont_avail, content_dir).h <= cont_avail + EPS:     # whole block fits a fresh slide
                pages.append(Page())
                queue.insert(0, n)
                continue
            cut = sp(n, avail) if sp else None
            if cut:                                                         # bigger than any slide: fill this one
                pg.units.append(cut[0])
                pg.end = y + cut[0].h
                queue.insert(0, cut[1])
            else:
                pages.append(Page())
                queue.insert(0, n)
            continue
        cut = sp(n, avail) if sp else None
        if cut:
            pg.units.append(cut[0])
            pg.end = y + cut[0].h
            queue.insert(0, cut[1])
            continue
        L.FINDINGS.append({"gate": "overflow", "shape": n["tag"], "need_in": round(u.h, 2), "box_in": round(avail, 2),
                           "text": title[:30]})
        pg.units.append(u)                                                  # unsplittable and too big: placed, reported
        pg.end = y + u.h
    return pages


def _kinds_zh(units):
    ks = []
    for u in units:
        z = KIND_ZH[u.kind]
        if z not in ks:
            ks.append(z)
    if ks == ["文字"]:
        return "文字（概念說明，沒有可比較的數值或結構）"
    return "、".join(ks)


def _page_notes(c, units, question, extra=None):
    gids, rids = [], []
    for u in units:
        gids += [g for g in u.gids if g not in gids]
        rids += [r for r in u.rids if r not in rids]
    lines = [f"圖種：{_kinds_zh(units)}", f"這頁回答：{question}"]
    if extra:
        lines.append(extra)
    if gids:
        lines.append("本頁詞彙：" + "；".join(f"{c.glossary[g]['term']}＝{c.plain(c.glossary[g]['gloss'])}" for g in gids))
    if rids:
        lines.append("本頁出處：" + "；".join(
            f"〔{c.refs[r]['label']}〕" + (c.plain(c.refs[r]["detail"]) if c.refs[r].get("detail") else "") for r in rids))
    return "\n".join(lines)


def build_pages(prs, c, content_dir, nodes, heading_md, kicker, summary_md, question, takeaway_node=None):
    """Paginate nodes into slides titled heading / heading（續）. Returns the number of slides added."""
    desc = summary_md or None
    top_first, top_cont = _head_y(kicker, desc), _head_y(kicker, None)
    queue = list(nodes) + ([takeaway_node] if takeaway_node else [])
    pages = paginate(queue, top_first, top_cont, content_dir, heading_md)
    for i, pg in enumerate(pages):
        title = heading_md if i == 0 else heading_md + "（續）"
        if H._est_w_in([(L.plain(title), {})], L.TITLE_PT) * 1.04 > L.CW:
            L.FINDINGS.append({"gate": "title-wrap", "shape": "title", "text": L.plain(title)[:30]})
        s = L.blank(prs)
        y0 = L.head(s, kicker, title, desc if i == 0 else None)
        want = top_first if i == 0 else top_cont
        if abs(y0 - want) > 0.005:
            raise RuntimeError(f"head() returned y={y0:.3f}, layout planned {want:.3f}")
        y = y0
        for u in pg.units:
            u.draw(s, y)
            y += u.h + GAP
        q = question if i == 0 else f"{L.plain(heading_md)}（續）：{question}"
        L.declare(s, prs, _kinds_zh(pg.units), q)
        L.notes(s, _page_notes(c, pg.units, q))
    return len(pages)


def build_cover(prs, c, meta):
    s = L.blank(prs)
    L.rule(s, L.MX, 1.95, 1.2, t=0.06).name = "cover-rule-bg"
    y = 2.2
    title, g, r = c.md(meta["title"])
    th = L.est_h([{"segs": L.H_md(title), "size": 38, "bold": True, "ls": 1.1, "space_after": 0}], 38, L.CW) + 0.02
    L.block(s, L.MX, y, L.CW, th, [{"segs": L.H_md(title), "size": 38, "bold": True, "ls": 1.1, "space_after": 0}],
            size=38, floor=34, name="cover-title")
    y += th + 0.15
    gids, rids = list(g), list(r)
    if meta.get("subtitle"):
        sub, g, r = c.md(meta["subtitle"])
        ps = [{"segs": L.H_md(sub), "size": 20, "ls": 1.25, "space_after": 0}]
        sh = L.est_h(ps, 20, L.CW) + 0.02
        L.block(s, L.MX, y, L.CW, sh, ps, size=20, floor=18, name="cover-sub", color=L.MUTED)
        y += sh + 0.3
        gids += g; rids += r
    if meta.get("purpose"):
        pur, g, r = c.md(meta["purpose"])
        ps = [{"segs": L.H_md(pur), "size": L.DESC_PT, "ls": 1.3, "space_after": 0}]
        ph = L.est_h(ps, L.DESC_PT, L.CW * 0.8) + 0.02
        L.block(s, L.MX, y, L.CW * 0.8, ph, ps, size=L.DESC_PT, floor=14, name="cover-purpose")
        y += ph + 0.3
        gids += g; rids += r
    bits = [meta["date"]] + ([c.plain(meta["author"])] if meta.get("author") else [])
    my = max(6.1, y + 0.1)
    L.block(s, L.MX, my, L.CW, 0.45, [{"segs": [("　".join(bits), {})], "size": 13, "ls": 1.25, "space_after": 0}],
            size=13, floor=12, name="cover-meta", color=L.MUTED)
    q = "這份簡報在講什麼、看完之後能做什麼"
    L.declare(s, prs, "文字（封面）", q)
    L.notes(s, f"圖種：文字（封面，沒有可比較的數值或結構）\n這頁回答：{q}\n"
               "版式宣告：展示用簡報；密度：繁複（內容可直接照頁閱讀，講者補充放在備註）。")
    return 1


def render(content, content_dir, out_path):
    L.FINDINGS.clear()
    L.DECL.clear()
    meta = content["meta"]
    c = Ctx(content)
    prs = L.new_prs()
    n_slides = build_cover(prs, c, meta)
    sections = content["sections"]
    for si, sec in enumerate(sections, 1):
        nodes = [prepare(b, c, f"{sec['id']}.{bi}") for bi, b in enumerate(sec["blocks"], 1)]
        tk = None
        if sec.get("takeaways"):
            tk = {"k": "takeaways", "tag": sec["id"], "items": [c.rich(t) for t in sec["takeaways"]]}
        heading_md = c.md(sec["heading"])[0]
        summary_md = c.md(sec["summary"])[0] if sec.get("summary") else None
        q = c.plain(sec["summary"]) if sec.get("summary") else f"{c.plain(sec['heading'])}是什麼"
        n_slides += build_pages(prs, c, content_dir, nodes, heading_md, f"第 {si} 節", summary_md, q, tk)
    if content.get("glossary"):
        has_en = any(g.get("en") for g in content["glossary"])
        header = ["詞彙"] + (["English"] if has_en else []) + ["說明"]
        rows = [[c.md(g["term"])[0]] + ([g.get("en", "")] if has_en else []) + [c.md(g["gloss"])[0]]
                for g in content["glossary"]]
        node = {"k": "table", "tag": "glossary", "caption": None, "header": header, "rows": rows, "g": [], "r": [],
                "col_w": _col_weights(header, rows)}
        n_slides += build_pages(prs, c, content_dir, [node], "詞彙", "附錄", "簡報中以粗體標示的名詞，在這裡逐一說明。",
                                "文中的名詞各是什麼意思")
    if content.get("refs"):
        has_href = any(r.get("href") for r in content["refs"])
        header = ["出處", "說明"] + (["連結"] if has_href else [])
        rows = [[c.md(r["label"])[0], c.md(r["detail"])[0] if r.get("detail") else ""] +
                ([r.get("href", "")] if has_href else []) for r in content["refs"]]
        node = {"k": "table", "tag": "refs", "caption": None, "header": header, "rows": rows, "g": [], "r": [],
                "col_w": _col_weights(header, rows)}
        n_slides += build_pages(prs, c, content_dir, [node], "出處", "附錄", "文中以〔　〕標示的出處，依序列在這裡。",
                                "內容依據哪些出處")
    colo = []
    if meta.get("source_note"):
        segs, g, r = c.rich(meta["source_note"])
        colo.append({"k": "para", "tag": "colophon.1", "segs": [("內容來源　", {"bold": True})] + segs, "g": g, "r": r})
    colo.append({"k": "para", "tag": "colophon.2", "segs": [("製作日期　", {"bold": True}), (meta["date"], {})]})
    if meta.get("author"):
        segs, g, r = c.rich(meta["author"])
        colo.append({"k": "para", "tag": "colophon.3", "segs": [("作者　　　", {"bold": True})] + segs, "g": g, "r": r})
    n_slides += build_pages(prs, c, content_dir, colo, "版本與來源", "附錄", None, "這份簡報從哪裡來、是誰做的")
    L.number_pass(prs)
    cp = prs.core_properties
    cp.title = c.plain(meta["title"])
    cp.author = c.plain(meta["author"]) if meta.get("author") else ""
    cp.language = meta["lang"]
    cp.keywords = f"sections={len(sections)}"        # independent section count for the structure gate
    prs.save(str(out_path))
    FINDINGS_LAST[:] = list(L.FINDINGS)
    DECL_LAST[:] = list(L.DECL)
    for f in FINDINGS_LAST:
        print(f"pptx-explainer WARN {f}", file=sys.stderr)
