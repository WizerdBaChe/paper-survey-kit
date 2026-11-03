"""pptx-explainer gates: checks read back from the EMITTED .pptx (never from the build's own state).

gates(out_path) -> list[(name, ok, detail)]; it never raises. Gates:
  type_audit  vendored deck_layout.type_audit: no run below its tier floor; plus an instrument check
              (the audit must have seen runs) and a no-unsized-run check (the vendored audit skips them).
  structure   slide count >= 1 + number of sections (independent count stored in core.xml keywords),
              no "[[" in any text (shapes, table cells, speaker notes), every slide has a notes declaration.
  geometry    stored geometry: nothing outside the slide or in the page-number band, no two content shapes
              (text / picture / table) overlap. Stored boxes only: PowerPoint's own layout is not read here.

Not gates here (slow, need PowerPoint COM): line-start marks and the rendered picture. Manual check:
  python -X utf8 ~/.claude/tools/pptx-line-start/line_start.py <deck>
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
DECLARATION = "這頁回答"            # the phrase render.py writes into every slide's notes
MARKER = re.compile(r"\[\[[grs]:")  # the inline-markup grammar only; a literal "[[" in prose is legitimate
EMU = 914400
TOL = int(0.012 * EMU)              # geometry tolerance (in), well under the 0.06 in smallest deliberate gap
_RENDER = None


def _render():
    """The sibling render module (loads the vendored helpers); loaded once under a private name."""
    global _RENDER
    if _RENDER is None:
        spec = importlib.util.spec_from_file_location("pptx_explainer_render_for_gates", HERE / "render.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _RENDER = mod
    return _RENDER


def _frames(slide):
    """Every text frame / table cell on a slide: (shape name, text_frame)."""
    for shp in slide.shapes:
        if shp.has_text_frame:
            yield shp.name, shp.text_frame
        if getattr(shp, "has_table", False) and shp.has_table:
            for row in shp.table.rows:
                for cell in row.cells:
                    yield shp.name, cell.text_frame


def _type_audit(path):
    L = _render().L
    small = L.type_audit(path)
    prs = Presentation(str(path))
    n_runs, unsized, smallest = 0, [], None
    for pi, s in enumerate(prs.slides, 1):
        for nm, tf in _frames(s):
            for p in tf.paragraphs:
                for r in p.runs:
                    if not r.text.strip():
                        continue
                    n_runs += 1
                    if r.font.size is None:
                        unsized.append(f"slide {pi} {nm}: {r.text[:12]!r}")
                    else:
                        smallest = r.font.size.pt if smallest is None else min(smallest, r.font.size.pt)
    if n_runs == 0:
        return False, "instrument blind: the audit read zero text runs"
    if small:
        first = small[0]
        return False, (f"{len(small)} run(s) below their tier floor, first: slide {first['page']} "
                       f"{first['shape']} {first['pt']} pt {first['text']!r}")
    if unsized:
        return False, f"{len(unsized)} text run(s) without an explicit size (inherit 18 pt), first: {unsized[0]}"
    return True, f"{n_runs} runs read, none below its tier floor, smallest {smallest:g} pt"


def _structure(path):
    prs = Presentation(str(path))
    slides = list(prs.slides)
    kw = prs.core_properties.keywords or ""
    m = re.search(r"sections=(\d+)", kw)
    if not m:
        return False, "section-count marker missing from core properties (keywords); cannot rule on the slide count"
    n_sec = int(m.group(1))
    probs = []
    if len(slides) < 1 + n_sec:
        probs.append(f"{len(slides)} slides < 1 cover + {n_sec} sections")
    kickers = set()
    n_text = 0
    for i, s in enumerate(slides, 1):
        for nm, tf in _frames(s):
            n_text += 1
            if MARKER.search(tf.text):
                probs.append(f"slide {i} {nm}: leftover '[[' marker")
            if nm == "kicker" and re.fullmatch(r"第 \d+ 節", tf.text.strip()):
                kickers.add(tf.text.strip())
        if not s.has_notes_slide:
            probs.append(f"slide {i}: no notes slide")
            continue
        nt = s.notes_slide.notes_text_frame.text
        if MARKER.search(nt):
            probs.append(f"slide {i} notes: leftover '[[' marker")
        if DECLARATION not in nt:
            probs.append(f"slide {i}: notes carry no declaration ({DECLARATION!r})")
    if len(kickers) != n_sec:
        probs.append(f"{len(kickers)} distinct section kickers on the slides, content has {n_sec} sections")
    if probs:
        return False, f"{len(probs)} problem(s), first: {probs[0]}"
    return True, f"{len(slides)} slides for {n_sec} sections, {n_text} text frames/cells clean, notes declared on every slide"


def _content_box(shp):
    """(l, t, r, b) in EMU for a CONTENT shape (text / picture / table), None for decoration (empty rect, line)."""
    if shp.left is None or shp.width is None:
        return None
    if shp.shape_type == MSO_SHAPE_TYPE.PICTURE or getattr(shp, "has_table", False) and shp.has_table:
        pass
    elif shp.has_text_frame and shp.text_frame.text.strip():
        pass
    else:
        return None
    return shp.left, shp.top, shp.left + shp.width, shp.top + shp.height


def _geometry(path):
    prs = Presentation(str(path))
    W, Hh = prs.slide_width, prs.slide_height
    band_top = Inches(7.0) + TOL                 # page numbers sit below y = 7.0 in
    probs, n_checked = [], 0
    for i, s in enumerate(prs.slides, 1):
        boxes = []
        for shp in s.shapes:
            if shp.left is None or shp.width is None:
                continue
            l, t, r, b = shp.left, shp.top, shp.left + shp.width, shp.top + shp.height
            if l < -TOL or t < -TOL or r > W + TOL or b > Hh + TOL:
                probs.append(f"slide {i} {shp.name}: outside the slide")
            if shp.name != "page-number" and b > band_top:
                probs.append(f"slide {i} {shp.name}: reaches into the page-number band (bottom {b / EMU:.2f} in)")
            box = _content_box(shp)
            if box and shp.name != "page-number":
                boxes.append((shp.name, box))
        n_checked += len(boxes)
        for a in range(len(boxes)):
            for c in range(a + 1, len(boxes)):
                (na, (al, at, ar, ab)), (nc, (cl, ct, cr, cb)) = boxes[a], boxes[c]
                if min(ar, cr) - max(al, cl) > TOL and min(ab, cb) - max(at, ct) > TOL:
                    probs.append(f"slide {i}: {na} overlaps {nc}")
    if probs:
        return False, f"{len(probs)} problem(s), first: {probs[0]}"
    return True, f"{n_checked} content boxes checked (stored geometry): inside the slide, above the page-number band, no overlaps"


def gates(out_path):
    path = Path(out_path)
    results = []
    for name, fn in (("type_audit", _type_audit), ("structure", _structure), ("geometry", _geometry)):
        try:
            ok, detail = fn(path)
        except Exception as e:                     # a gate never raises: it fails with the reason
            ok, detail = False, f"{type(e).__name__}: {e}"
        results.append((name, bool(ok), detail))
    return results
