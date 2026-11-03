#!/usr/bin/env python
"""paper-distill crop — cut the load-bearing figure out of the ingested PDF.

Three ways to name the region (first match wins):
  --caption "Fig. 3" [--page N]                              the figure above a caption anchor (a table: either side)
  --bbox x0,y0,x1,y1 --page N                                exact rectangle in PDF points
  --image p003_i01                                           an embedded raster from source/images
Output: --out figures/F1.png (relative to the run folder). Prints one JSON object.

--caption, default (ink): render the band between the nearest body-text block above the caption and the caption
top, across the caption's column (the full page width on a single-column page); the crop is the bounding box of
what is painted there, padded by --pad (4 pt) and clamped to the band. A table's band is tried on both sides of
its caption (IEEE puts the table below, Scientific Reports above) and the side whose ink is nearer the caption
wins. The caption itself is not in the crop; a thin page rule (header underline, separator) at the band's far
edge is dropped. `band.top_set_by` / `bottom_set_by` names the block that bounded the band. Measured on
rendered ink, not PDF object geometry: a PDF may place a raster twice with one copy hidden, and the hidden copy's
bbox lies outside what is painted (Tran 2018).
--caption, figures-after-captions layout (2026-11-03, Kumar 2022: the caption list on p.11, each figure on p.12-15 under a
bare "Figure N:" stub): when nothing is painted above the caption, or only text (no raster image and fewer than 3 vector
paths in the cut), or the caption is itself a bare stub, the FOLLOWING pages are searched — first for a stub of the same
label (the figure is what is painted from under it to the next caption/stub or the running footer; "Figure 1(a):" and
"1(b):" are one figure), then, on a bare caption-list page only, for the figure of the same rank among the raster images
after the list when image count and caption count agree. A stub counts as a slot only when the label's caption text was
printed on an earlier page. `band.layout = figure-after-caption`, `band.via = stub | image-order`, `page` is the FIGURE's
page. When the search finds nothing the original result stands (`band.figure_after_caption` says why). The border-ink gate
below applies unchanged. Measured: the 91 captions of the 9 accepted runs give byte-identical rect/exit/page before and after.
--caption with --above / --below / --full-width (manual): the fixed rectangle used before 2026-09-26 — the
caption's own column (--full-width: the page width) from --above (260) pt above the caption to --below (0) pt
under its bottom, caption included.

Every rendered crop then passes a border-ink gate: FAIL (exit 3, file kept) when more than 1 % of the pixels on
any 2 px border are darker than 170 — ink on the edge means the cut went through content. Its controls run first
on every call: the known-bad evals/fixtures/crop-gate-bad_tran2018-F6.png (the 2026-09-04 Tran F6, cut on the
left) must FAIL and a blank image must PASS, else the verdict is UNDET (exit 2); --selftest runs only these. The
gate cannot see a band whose top was chosen too low (a white gap inside the figure): view the crop and read
band.top_set_by.
The crop is a mechanical step; whether it is the RIGHT figure is Stage 4's judgment.
"""
import argparse
import json
import re
import shutil
import statistics
import sys
from collections import Counter, namedtuple
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BAD_CONTROL = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "crop-gate-bad_tran2018-F6.png"
INK_LEVEL = 235                     # darker than this = painted (the ink bbox)
EDGE_LEVEL, EDGE_LIMIT = 170, 1.0   # gate: > 1 % of a 2 px border darker than 170 = the cut went through content
EDGE_ZONE = 80.0                    # pt from the top/bottom page edge where running headers/footers live
LABEL = {"fig": r"fig(?:ure)?\.?", "table": r"table", "scheme": r"scheme"}
# a caption is a label followed by punctuation ("Figure 7.", "Fig. 3 |") or by a capital / bracket ("Fig. 1 Examples",
# Springer); "Figure 7 shows the schematic" is a body sentence (Tran 2018 p.8), not the caption
# "Figure 1(a): ..." captions Figure 1 (a panel suffix may follow the number; Kumar 2022, 2026-11-03)
PANEL = r"(?:\s?\([a-z]\))?"
ANY_CAPTION = re.compile(r"^\s*(?:fig(?:ure)?\.?|table|scheme)\s*s?\d+" + PANEL + r"(?:\s*[.:|]|\s+(?-i:[A-Z(\[]))", re.I)
# a STUB is a label with no caption text ("Figure 2:"): the figure's slot in a preprint that lists the captions first and
# puts the figures after them, each under its own stub (Kumar 2022 p.12-15)
STUB = re.compile(r"^\s*(fig(?:ure)?\.?|table|scheme)\s*s?(\d+)" + PANEL + r"\s*[.:|]?\s*$", re.I)
HEADING = re.compile(r"^(?:\d+(?:\.\d+)*\.?|[IVX]+\.|[A-H]\.)\s+[A-Z]")
INK_LUT = bytes(1 if v < INK_LEVEL else 0 for v in range(256))
SCALE = 2.0                         # band render scale for the ink search (144 dpi)
# gtop = glyph top of the first line (baseline - 0.8 em). The block bbox top sits a line-ascent higher, and a figure's
# axis title can reach into that strip (Zhang 2021 Fig. 2), so the band stops at the glyphs, not at the bbox.
Block = namedtuple("Block", "x0 y0 x1 y1 text size lines gtop")


def norm_label(s):
    s = s.strip().lower().replace("figure", "fig").replace("fig.", "fig")
    s = re.sub(r"\s+", " ", s)
    m = re.match(r"(fig|table|scheme)\s*s?(\d+)", s)
    return (m.group(1), int(m.group(2))) if m else None


# ---------- border-ink gate ----------

def border_ink(pix):
    """Percent of pixels darker than EDGE_LEVEL on each 2 px border of a pixmap."""
    import fitz
    if pix.alpha:
        pix = fitz.Pixmap(pix, 0)
    if pix.n != 1:
        pix = fitz.Pixmap(fitz.csGRAY, pix)
    w, h, s = pix.width, pix.height, pix.stride
    dark = pix.samples.translate(bytes(1 if v < EDGE_LEVEL else 0 for v in range(256)))
    k = min(2, w, h)
    rows = lambda rs: sum(dark[r * s:r * s + w].count(1) for r in rs) / (len(rs) * w)
    cols = lambda cs: sum(dark[c::s][:h].count(1) for c in cs) / (len(cs) * h)
    sides = {"top": rows(range(k)), "bottom": rows(range(h - k, h)),
             "left": cols(range(k)), "right": cols(range(w - k, w))}
    return {side: round(100 * v, 1) for side, v in sides.items()}


def gate_pass(pix):
    return max(border_ink(pix).values()) <= EDGE_LIMIT


def gate_controls():
    """None when both controls behave (known-bad FAILS, blank PASSES), else the reason the gate cannot be trusted."""
    import fitz
    if not BAD_CONTROL.is_file():
        return f"known-bad control missing: {BAD_CONTROL}"
    blank = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, 400, 300), False)
    blank.clear_with(255)
    if gate_pass(fitz.Pixmap(str(BAD_CONTROL))):
        return f"known-bad control PASSED (must FAIL): {BAD_CONTROL.name}"
    if not gate_pass(blank):
        return "blank control FAILED (must PASS)"
    return None


def gate(path):
    import fitz
    fault = gate_controls()
    if fault:
        return {"verdict": "UNDET", "reason": fault}
    ink = border_ink(fitz.Pixmap(str(path)))
    return {"verdict": "PASS" if max(ink.values()) <= EDGE_LIMIT else "FAIL", "border_ink_pct": ink,
            "limit": f"<= {EDGE_LIMIT} % of each 2 px border darker than {EDGE_LEVEL}", "controls": "ok"}


# ---------- caption-anchored ink crop ----------

def text_blocks(page):
    import fitz
    out = []
    for b in page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        spans = [sp for ln in b["lines"] for sp in ln["spans"]]
        text = "\n".join("".join(sp["text"] for sp in ln["spans"]) for ln in b["lines"]).strip()
        if not text:
            continue
        sizes = Counter()
        for sp in spans:
            sizes[round(sp["size"] * 2) / 2] += len(sp["text"].strip())
        # a whitespace-only line can head the block and lift its bbox (Zhang 2021 Fig. 2 caption): count inked lines
        inked = [[sp for sp in ln["spans"] if sp["text"].strip()] for ln in b["lines"]]
        inked = [ln for ln in inked if ln]
        gtop = max(b["bbox"][1], min(sp["origin"][1] - 0.8 * sp["size"] for sp in inked[0]))
        out.append(Block(*b["bbox"], text, sizes.most_common(1)[0][0], len(inked), gtop))
    return out


def edge_key(text):
    return re.sub(r"[\W\d_]+", "", text).lower()


class Doc:
    """Text blocks per page, the body font size, and the running header/footer texts of one PDF."""

    def __init__(self, doc):
        self.doc = doc
        self.blocks = [text_blocks(p) for p in doc]
        sizes = Counter()
        for bl in self.blocks:
            for b in bl:
                sizes[b.size] += len(b.text)
        self.body_size = sizes.most_common(1)[0][0] if sizes else 10.0
        # running header/footer = text in the edge zone that recurs on another page; a one-off block there may be
        # the top of a figure (an axis title at y = 60 pt), and taking it as a header would cut the figure
        seen = {}
        for page, bl in zip(doc, self.blocks):
            for b in bl:
                if self.in_edge_zone(page, b) and len(edge_key(b.text)) >= 3:
                    seen.setdefault(edge_key(b.text), set()).add(page.number)
        self.running = {k for k, pages in seen.items() if len(pages) > 1 or len(doc) == 1}

    @staticmethod
    def in_edge_zone(page, b):
        return b.y1 < page.rect.y0 + EDGE_ZONE or b.y0 > page.rect.y1 - EDGE_ZONE

    def find_caption(self, want, page_no=None):
        """(page, block) of the caption; a label + punctuation beats a label + capital (a looser Springer form)."""
        kind, num = want
        head = rf"^\s*{LABEL[kind]}\s*s?{num}{PANEL}"
        for tail in (r"\s*[.:|]", r"\s+(?-i:[A-Z(\[])"):
            rx = re.compile(head + tail, re.I)
            for page, bl in zip(self.doc, self.blocks):
                if page_no and page.number + 1 != page_no:
                    continue
                for b in bl:
                    if rx.match(b.text):
                        return page, b
        return None, None

    def body_rule(self, page, b, col_w):
        """Why b bounds a figure band (it is text of the page, not of the figure), or None."""
        if self.in_edge_zone(page, b) and edge_key(b.text) in self.running:
            return "running-header" if b.y1 < page.rect.y0 + EDGE_ZONE else "running-footer"
        if ANY_CAPTION.match(b.text):
            return "caption"
        if HEADING.match(b.text) and b.size >= 0.95 * self.body_size:
            return "heading"
        # two lines also count: a paragraph's tail carried over from another column is often < 80 chars (Jaiswal 2023 p.3)
        if b.x1 - b.x0 >= 0.7 * col_w and (len(b.text) >= 80 or b.lines >= 2) and b.size >= 0.85 * self.body_size:
            return "paragraph"
        return None

    def column(self, page, cap):
        """x-range of the caption's column: one half of a two-column page, else the full page width."""
        r, mid = page.rect, (page.rect.x0 + page.rect.x1) / 2
        tol = 0.02 * r.width
        paras = [b for b in self.blocks[page.number] if len(b.text) >= 80 and b.x1 - b.x0 >= 0.3 * r.width]
        two = any(b.x1 <= mid + tol for b in paras) and any(b.x0 >= mid - tol for b in paras)
        if two and cap.x1 <= mid + tol:
            return "left", r.x0, mid
        if two and cap.x0 >= mid - tol:
            return "right", mid, r.x1
        return "full", r.x0, r.x1

    def col_width(self, page, cap):
        """Width of a body paragraph on this page (a column on a two-column page); the caption's width if none."""
        paras = [b.x1 - b.x0 for b in self.blocks[page.number] if len(b.text) >= 200 and b.size >= 0.85 * self.body_size]
        return statistics.median(paras) if paras else cap.x1 - cap.x0


def ink_box(page, band, drop=None, clear=3.0):
    """Bounding box (pt) of what is painted in band, or None; and how many thin rules were dropped at its `drop`
    edge ("top" / "bottom" / None).

    A rule is a run of ink rows at least half the band wide, with > `clear` pt of white (or nothing) on its inner
    side, that is either a line <= 1.5 pt thick (plus at most the sparse side strokes of a frame ending there) or
    a pale strip <= 8 pt tall (no pixel darker than 200): the underline of a running header (IEEE), a dotted
    separator under a caption and the shaded header band (Scientific Reports), the bottom of the previous figure's
    frame (Light Sci Appl); measured 1-3 px thick at 144 dpi. Text does not qualify: the x-height of 5 pt type is
    already ~2.2 pt, and glyphs are darker than 200. A figure's own frame or axis box is not dropped: its sides run
    on into the content, so no white gap closes the run."""
    import fitz
    pix = page.get_pixmap(clip=band, matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csGRAY, alpha=False)
    w, h, s = pix.width, pix.height, pix.stride
    gray = pix.samples
    ink = gray.translate(INK_LUT)
    spans, count = {}, {}
    for r in range(h):
        a = ink.find(1, r * s, r * s + w)
        if a != -1:
            spans[r] = (a - r * s, ink.rfind(1, r * s, r * s + w) - r * s + 1)
            count[r] = ink.count(1, r * s, r * s + w)

    def is_rule(run):
        if max(spans[r][1] for r in run) - min(spans[r][0] for r in run) < 0.5 * w:
            return False
        if len(run) <= 8 * SCALE and min(min(gray[r * s:r * s + w]) for r in run) >= 200:
            return True
        line = [r for r in run if count[r] > 0.02 * w]
        return 0 < len(line) <= 1.5 * SCALE and max(line) - min(line) == len(line) - 1

    rows, dropped = sorted(spans), 0
    while drop and rows:
        seq = rows if drop == "top" else rows[::-1]
        n = 1
        while n < len(seq) and abs(seq[n] - seq[n - 1]) == 1:
            n += 1
        run, rest = seq[:n], seq[n:]
        if not (is_rule(run) and (not rest or abs(rest[0] - run[-1]) > clear * SCALE)):
            break
        rows, dropped = sorted(rest), dropped + 1
    if not rows:
        return None, dropped
    x0 = min(spans[r][0] for r in rows)
    x1 = max(spans[r][1] for r in rows)
    return fitz.Rect((pix.x + x0) / SCALE, (pix.y + rows[0]) / SCALE,
                     (pix.x + x1) / SCALE, (pix.y + rows[-1] + 1) / SCALE), dropped


def ink_region(d, page, cap, kind, pad):
    """The band beside the caption and the padded ink bbox inside it. Returns (rect, band_info) or (None, band_info
    with an "error")."""
    import fitz
    col, bx0, bx1 = d.column(page, cap)
    col_w = d.col_width(page, cap)
    beside = [b for b in d.blocks[page.number]
              if b is not cap and b.x1 > bx0 + 1 and b.x0 < bx1 - 1 and d.body_rule(page, b, col_w)]
    tried = []
    for side in (("below", "above") if kind == "table" else ("above",)):
        if side == "above":
            edge = max((b for b in beside if b.y1 <= cap.y0 + 0.5), key=lambda b: b.y1, default=None)
            band = fitz.Rect(bx0, (edge.y1 if edge else page.rect.y0) + 1, bx1, cap.gtop - 1)
        else:
            edge = min((b for b in beside if b.y0 >= cap.y1 - 0.5), key=lambda b: b.y0, default=None)
            band = fitz.Rect(bx0, cap.y1 + 1, bx1, (edge.gtop if edge else page.rect.y1) - 1)
        set_by = ({"rule": d.body_rule(page, edge, col_w), "y": round(edge.y1 if side == "above" else edge.gtop, 1),
                   "text": edge.text.replace("\n", " ")[:70]} if edge else {"rule": "page-edge"})
        info = {"column": col, "side": side, "x": [round(bx0, 1), round(bx1, 1)], "y": [round(band.y0, 1), round(band.y1, 1)],
                ("top_set_by" if side == "above" else "bottom_set_by"): set_by}
        # rules at the far edge are page furniture; a side holding nothing else is blank (Hong 2019 Table 1: only the
        # dotted separator lies below its caption, the table is above)
        far = "top" if side == "above" else "bottom"
        probe, dropped = ink_box(page, band, far) if band.height >= 2 else (None, 0)
        box = probe
        if kind == "table" and probe is not None:
            # a table's own top/bottom rule sits within a few pt of its rows; only a rule well clear of them is furniture
            box, dropped = ink_box(page, band, far, clear=8.0)
        if dropped:
            info["dropped_rules"] = dropped
        # the gap between the caption and the nearest ink: a table sits right against its own caption
        gap = (band.y1 - probe.y1) if probe and side == "above" else (probe.y0 - band.y0) if probe else None
        tried.append((gap, box, band, info))
    hits = [t for t in tried if t[1] is not None]
    if not hits:
        info = tried[0][3]
        return None, {**info, "error": "nothing painted between the caption and the bounding text block"}
    gap, box, band, info = min(hits, key=lambda t: t[0])
    if len(tried) > 1:
        info["caption_gap_pt"] = {t[3]["side"]: (round(t[0], 1) if t[0] is not None else "blank") for t in tried}
    return (box + (-pad, -pad, pad, pad)) & band, info


# ---------- figures-after-captions layout (preprints: the caption list first, the figures at the end) ----------

def painted_in(page, rect):
    """(raster images, vector paths) whose bbox touches rect: the evidence that a rect holds a figure and not only text."""
    n_img = sum(1 for i in page.get_image_info()
                if i["bbox"][0] <= rect.x1 and i["bbox"][2] >= rect.x0 and i["bbox"][1] <= rect.y1 and i["bbox"][3] >= rect.y0)
    n_dr = 0
    for dr in page.get_drawings():
        r = dr["rect"]
        if r.x0 <= rect.x1 and r.x1 >= rect.x0 and r.y0 <= rect.y1 and r.y1 >= rect.y0:
            n_dr += 1
    return n_img, n_dr


def has_figure_ink(page, rect):
    n_img, n_dr = painted_in(page, rect)
    return n_img >= 1 or n_dr >= 3


def stub_key(b):
    """('fig'|'table'|'scheme', n) when block b is a label with no caption text, else None."""
    m = STUB.match(re.sub(r"\s+", " ", b.text))
    return norm_label(f"{m.group(1)} {m.group(2)}") if m else None


def figure_after(d, page, cap, want, pad):
    """The figure of a caption whose figure is NOT above it, searched on the FOLLOWING pages. Returns (page, rect, info)
    or (None, None, why).

    1. by stub: the first later page holding a stub of the same label ("Figure 2:" alone in a block; "Figure 1(a):" and
       "1(b):" both belong to Figure 1). The figure is what is painted from under the first such stub down to the next
       caption/stub of ANOTHER figure or the running footer. The caption itself may be the stub (crop --page N).
    2. by order, only on a caption-list page (two or more figure captions, nothing painted): the figure with the same rank
       among the raster images of the pages after the list — and only when the image count equals the caption count,
       otherwise the order cannot be proved and nothing is returned (the caller keeps its own result)."""
    import fitz
    kind, num = want
    doc = d.doc
    first_page = page.number if stub_key(cap) == want else page.number + 1
    # a bare label is a slot for a figure BELOW it only when the label's caption text was printed on an earlier page (the
    # caption list); a label-only block in the ordinary layout is the caption of the figure ABOVE it
    listed = lambda pno: any(norm_label(b.text) == want and ANY_CAPTION.match(b.text) and not stub_key(b)
                             for q in range(pno) for b in d.blocks[q])
    for pno in range(first_page, len(doc)):
        pg = doc[pno]
        if not listed(pno):
            continue
        mine = sorted((b for b in d.blocks[pno] if stub_key(b) == want and (pno != page.number or b is cap or b.y0 >= cap.y0)),
                      key=lambda b: b.y0)
        if not mine:
            continue
        top = mine[0]
        col, bx0, bx1 = d.column(pg, top)
        bounds = [b for b in d.blocks[pno] if b.y0 >= top.y1 - 0.5 and b not in mine
                  and ((d.in_edge_zone(pg, b) and edge_key(b.text) in d.running)
                       or (ANY_CAPTION.match(b.text) and stub_key(b) != want))]
        edge = min(bounds, key=lambda b: b.y0, default=None)
        band = fitz.Rect(bx0, top.y1 + 1, bx1, (edge.gtop if edge else pg.rect.y1) - 1)
        if band.height < 2:
            continue
        box, dropped = ink_box(pg, band, "bottom")
        if box is None or not has_figure_ink(pg, box):
            return None, None, f"stub {top.text.strip()!r} on p.{pno + 1} has no figure (image or vector paths) under it"
        info = {"layout": "figure-after-caption", "via": "stub", "caption_page": page.number + 1, "figure_page": pno + 1,
                "column": col, "x": [round(bx0, 1), round(bx1, 1)], "y": [round(band.y0, 1), round(band.y1, 1)],
                "stub": top.text.strip(),
                "bottom_set_by": ({"rule": "caption-or-footer", "text": edge.text.replace("\n", " ")[:50]} if edge else {"rule": "page-edge"})}
        if dropped:
            info["dropped_rules"] = dropped
        return pg, (box + (-pad, -pad, pad, pad)) & band, info
    # 2. order among raster images, caption-list page only
    def fig_nums(pno):
        keys = [norm_label(b.text) for b in d.blocks[pno] if ANY_CAPTION.match(b.text) and not stub_key(b)]
        return [k[1] for k in keys if k and k[0] == "fig"]

    if has_figure_ink(page, page.rect):
        return None, None, "no stub of this label on a later page, and the caption page also carries painted content"
    nums, last_list = [n for i, n in enumerate(fig_nums(page.number)) if n not in fig_nums(page.number)[:i]], page.number
    while last_list + 1 < len(doc) and fig_nums(last_list + 1) and not has_figure_ink(doc[last_list + 1], doc[last_list + 1].rect):
        last_list += 1
        nums += [n for n in fig_nums(last_list) if n not in nums]
    if len(nums) < 2 or want[1] not in nums:
        return None, None, "no stub of this label on a later page, and the caption page is not a caption list"
    imgs = []
    for pno in range(last_list + 1, len(doc)):
        W, H = doc[pno].rect.width, doc[pno].rect.height
        for i in sorted(doc[pno].get_image_info(), key=lambda i: (round(i["bbox"][1]), i["bbox"][0])):
            x0, y0, x1, y1 = i["bbox"]
            if (x1 - x0) >= 0.2 * W and (y1 - y0) >= 0.05 * H:
                imgs.append((pno, fitz.Rect(i["bbox"])))
    if len(imgs) != len(nums):
        return None, None, f"order unprovable: {len(imgs)} images after the caption list, {len(nums)} figure captions in it"
    pno, r = imgs[nums.index(want[1])]
    pg = doc[pno]
    info = {"layout": "figure-after-caption", "via": "image-order", "caption_page": page.number + 1, "figure_page": pno + 1,
            "rank": nums.index(want[1]) + 1, "of": len(nums)}
    return pg, (r + (-pad, -pad, pad, pad)) & pg.rect, info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--caption", default="")
    ap.add_argument("--above", type=float, default=None, help="manual: points above the caption to include (260)")
    ap.add_argument("--below", type=float, default=None, help="manual: points below the caption bottom to include (0)")
    ap.add_argument("--pad", type=float, default=None, help="pt around the region: ink 4, manual 6")
    ap.add_argument("--full-width", action="store_true", help="manual: the full page width instead of the caption's column")
    ap.add_argument("--bbox", default="")
    ap.add_argument("--page", type=int, default=None)
    ap.add_argument("--image", default="")
    ap.add_argument("--out", default="figures/F1.png")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--selftest", action="store_true", help="run the border-ink gate's two controls and exit")
    a = ap.parse_args(argv)

    if a.selftest:
        fault = gate_controls()
        print(json.dumps({"selftest": "FAIL", "reason": fault} if fault else
                         {"selftest": "OK", "known_bad": f"{BAD_CONTROL.name} fails", "blank": "passes"}, ensure_ascii=False))
        return 2 if fault else 0
    if not a.run:
        ap.error("--run is required (or --selftest)")

    run = a.run
    out = run / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    figs = json.loads((run / "source" / "figures.json").read_text(encoding="utf-8"))

    if a.image:
        cands = [im for im in figs["images"] if Path(im["file"]).stem == a.image]
        if not cands:
            print(json.dumps({"error": f"no embedded image named {a.image}"}), file=sys.stderr)
            return 1
        src = run / cands[0]["file"]
        shutil.copy2(src, out)
        print(json.dumps({"out": str(out), "mode": "image", "source": str(src),
                          "width": cands[0]["width"], "height": cands[0]["height"],
                          "gate": "n/a (an embedded raster, not a cut)"}, ensure_ascii=False))
        return 0

    import fitz
    doc = fitz.open(str(run / "source" / "paper.pdf"))
    extra = {}

    if a.bbox:
        if a.page is None:
            print(json.dumps({"error": "--bbox needs --page"}), file=sys.stderr)
            return 1
        x0, y0, x1, y1 = (float(v) for v in a.bbox.split(","))
        page = doc[a.page - 1]
        rect = fitz.Rect(x0, y0, x1, y1) & page.rect
        mode = "bbox"
    elif a.caption:
        want = norm_label(a.caption)
        if not want:
            print(json.dumps({"error": f"cannot parse caption label {a.caption!r}"}), file=sys.stderr)
            return 1
        d = Doc(doc)
        page, cap = d.find_caption(want, a.page)
        source = "pdf-text"
        if cap is None:   # a caption the PDF text layer splits oddly may still be in ingest's looser anchor list
            hits = [c for c in figs["captions"] if norm_label(c["label"]) == want and (a.page is None or c["page"] == a.page)]
            if not hits:
                print(json.dumps({"error": f"caption {a.caption!r} not found; anchors: "
                                  f"{[c['label'] + '@p' + str(c['page']) for c in figs['captions']][:40]}"},
                                 ensure_ascii=False), file=sys.stderr)
                return 1
            page = doc[hits[0]["page"] - 1]
            bb = hits[0]["bbox"]
            cap = Block(*bb, hits[0]["caption"], d.body_size, hits[0]["caption"].count("\n") + 1, bb[1])
            source = "figures.json"
        a.page = page.number + 1
        extra["anchor"] = {"text": cap.text.replace("\n", " ")[:70], "bbox": [round(v, 1) for v in cap[:4]], "source": source}
        manual = a.above is not None or a.below is not None or a.full_width
        if manual:
            pad = 6.0 if a.pad is None else a.pad
            if a.full_width:
                x0, x1 = page.rect.x0 + pad, page.rect.x1 - pad
            else:
                x0, x1 = cap.x0 - pad, cap.x1 + pad
            rect = fitz.Rect(x0, cap.y0 - (260.0 if a.above is None else a.above),
                             x1, cap.y1 + (0.0 if a.below is None else a.below)) & page.rect
        else:
            pad = 4.0 if a.pad is None else a.pad
            rect, band = ink_region(d, page, cap, want[0], pad)
            # figures-after-captions layout: nothing painted above the caption (or only text), or the caption is a bare
            # stub whose figure lies under it -> look on the following pages; keep the original result when that finds
            # nothing (a figure with < 3 vector paths and no raster is rare, and stays as it was)
            if want[0] in ("fig", "scheme") and (rect is None or stub_key(cap) == want or not has_figure_ink(page, rect)):
                fpage, frect, finfo = figure_after(d, page, cap, want, pad)
                if fpage is not None:
                    page, rect, band = fpage, frect, {**finfo, "above_caption": band}
                    a.page = page.number + 1
                else:
                    band = {**band, "figure_after_caption": f"not used: {finfo}"}
            extra["band"] = band
            if rect is None:
                print(json.dumps({"error": band.pop("error"), "page": a.page, **extra,
                                  "hint": "pass --above/--below (manual rectangle) or --bbox"}, ensure_ascii=False),
                      file=sys.stderr)
                return 1
        mode = "caption"
        extra["method"] = "manual" if manual else "ink"
    else:
        print(json.dumps({"error": "give --caption, --bbox or --image"}), file=sys.stderr)
        return 1

    pix = page.get_pixmap(dpi=a.dpi, clip=rect, alpha=False)
    pix.save(str(out))
    verdict = gate(out)
    print(json.dumps({"out": str(out), "mode": mode, **extra, "page": a.page,
                      "rect_pt": [round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1)],
                      "width": pix.width, "height": pix.height, "gate": verdict,
                      "hint": "view the crop: text above the figure or a missing top panel is not visible to the gate; "
                              "--above/--below (manual rectangle) or --bbox for an exact cut"},
                     ensure_ascii=False))
    return {"PASS": 0, "FAIL": 3}.get(verdict["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
