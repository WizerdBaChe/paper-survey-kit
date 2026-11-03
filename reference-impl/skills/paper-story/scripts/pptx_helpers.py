# paper-story/scripts/pptx_helpers.py — VERBATIM copy of lines 1–344 (helper +
# gate region) of AssetVault assets/pattern-template/python/pptx-deck-builder/
# deck_builder.py, taken 2026-09-02. Do not hand-edit: re-copy from the vault
# when it changes (rules/office-deck-deliverables.md; hand-porting is the drift
# source). render_story.py imports this module (the paper-distill twin was
# archived 2026-09-19: it had no importer after the 2026-09-03 split).
#
# pptx-deck-builder — reusable python-pptx deck skeleton (AssetVault
# pattern-template/python). Helper region below is VERBATIM-derived by script
# from an earlier research-project PPTX builder (2026-08-31) —
# regenerate with the derivation script rather than hand-editing helpers.
#
# What the helpers already solve (measured pitfalls — details in README.md):
#   * local-file hyperlinks stored in PowerPoint's CANONICAL format
#     ("file:///" + raw Windows path, CJK unencoded) — Path.as_uri()'s
#     percent-encoded form fails with "cannot open the specified file"
#   * CJK runs get a real east-asian typeface (a:ea/a:cs), not the theme font
#   * textboxes drop the default 0.1in side insets (widen-the-block-first)
#   * no-orphan-wrap rule: a wrap spilling <=8 chars shrinks the font instead
#     (estimator carries a measured 1.04 safety factor for bold JhengHei)
#   * per-page References strip cites LITERATURE only, omitted when empty
#   * page numbers stamped by a post-pass from slide order — never hardcoded
#
# Verify visually via PowerPoint COM export (locale-named slide PNGs):
#   $pp = New-Object -ComObject PowerPoint.Application
#   $p = $pp.Presentations.Open($pptx, $true, $false, $false)
#   $p.SaveAs($outDir, 18); $p.Close(); $pp.Quit()
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8")

# ---- palette (carried over from the HTML deck: colors keep their semantics) ----
INK = RGBColor(0x1C, 0x27, 0x33)
MUTED = RGBColor(0x5C, 0x6B, 0x7A)
GLASS = RGBColor(0x3E, 0x7C, 0xAB)
GLASS_BG = RGBColor(0xE9, 0xF1, 0xF8)
PASS_C = RGBColor(0x1A, 0x7F, 0x4E)
FAIL_C = RGBColor(0xC2, 0x49, 0x1D)
GOLD = RGBColor(0xA3, 0x72, 0x0A)
ASK = RGBColor(0x7A, 0x4B, 0xB0)
LINE = RGBColor(0xD5, 0xDD, 0xE4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SANS = "Microsoft JhengHei"
MONO = "Consolas"

DATE = "2026-08-31"


# ---- low-level helpers ----
def _set_font(run, size, bold, color, name, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", SANS if name != MONO else MONO)


def tb(slide, x, y, w, h):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    # widen-the-block-first rule: kill the default 0.1in side insets
    tf.margin_left = tf.margin_right = Emu(0)
    return box, tf


# Wide NON-CJK glyphs are counted as full-width too (a research round: ⇒ was counted
# at Latin 0.55 width but renders full-width in JhengHei -> a fit_w-passing
# title still wrapped a 1-char orphan tail). Overestimating width is the SAFE
# direction here: worst case the shrink fires one step early.
_FULLWIDTH_EXTRA = "—－……──「」『』～⇒⇔→←↑↓↔±≥≤≠✓✗×"


def _est_w_in(segs, base_size, scale=1.0):
    """Rough rendered width (inches) of one line of runs."""
    w = 0.0
    for text, ov in segs:
        s = ov.get("size", base_size) * scale
        for ch in text:
            if ord(ch) >= 0x2E80 or ch in _FULLWIDTH_EXTRA:
                w += s / 72.0
            elif ch == " ":
                w += s * 0.30 / 72.0
            else:
                w += s * 0.55 / 72.0
    return w


def _fit_scale(segs, size, fit_w):
    """User's layout habit: a wrap that spills <=8 chars onto the next line is
    not allowed — shrink the text (the block is already widened) until the tail
    line is either gone or substantial. Returns a font scale factor."""
    scale = 1.0
    for _ in range(8):
        # 1.04 safety factor: the estimator runs ~4% narrow vs real JhengHei
        # bold metrics (measured on the P1 feature bullet, 2026-08-31)
        est = _est_w_in(segs, size, scale) * 1.04
        if est <= fit_w:
            break
        tail = est % fit_w
        tail_chars = tail / (size * scale / 72.0)
        if tail_chars > 8:
            break
        scale -= 0.04
        if size * scale < size - 2.5:
            scale = (size - 2.5) / size
            break
    return scale


def para(tf, segs, size=14, color=INK, bold=False, name=SANS, level=0,
         space_after=4, align=None, first=False, fit_w=None):
    """segs: str, or list of (text, {size,color,bold,name}) override tuples.
    fit_w: content width in inches — enables the no-orphan-wrap shrink rule."""
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.level = level
    p.space_after = Pt(space_after)
    if align:
        p.alignment = align
    if isinstance(segs, str):
        segs = [(segs, {})]
    scale = _fit_scale(segs, size, fit_w) if fit_w else 1.0
    for text, ov in segs:
        r = p.add_run()
        r.text = text
        _set_font(r, round(ov.get("size", size) * scale * 2) / 2,
                  ov.get("bold", bold), ov.get("color", color), ov.get("name", name))
    return p


def add_rect(slide, x, y, w, h, fill, line_color=None, rounded=False):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def chip(slide, x, y, text, color, w=1.7, size=10.5):
    shp = add_rect(slide, x, y, w, 0.28, WHITE, line_color=color, rounded=True)
    tf = shp.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Emu(18000)
    tf.margin_top = tf.margin_bottom = Emu(0)
    para(tf, text, size=size, color=color, bold=True, name=MONO, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    return shp


def link_button(slide, x, y, text, target: Path, w=2.6, h=0.34):
    shp = add_rect(slide, x, y, w, h, GLASS_BG, line_color=GLASS, rounded=True)
    tf = shp.text_frame
    tf.margin_top = tf.margin_bottom = Emu(9000)
    para(tf, text, size=11, color=GLASS, bold=True, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    # canonical Office storage (probed 2026-08-31 via PowerPoint COM):
    # "file:///" + RAW Windows path, backslashes and CJK unencoded.
    # Path.as_uri()'s percent-encoded form makes PowerPoint fail with
    # "cannot open the specified file".
    shp.click_action.hyperlink.address = "file:///" + str(target.resolve())
    return shp


def eyebrow_title(slide, W, eyebrow, title, title_color=INK):
    _, tf = tb(slide, 0.55, 0.28, W - 1.1, 0.32)
    para(tf, eyebrow, size=10 if W < 12 else 11, color=MUTED, name=MONO,
         first=True, space_after=0)
    _, tf = tb(slide, 0.55, 0.60, W - 1.1, 0.75)
    para(tf, title, size=20 if W < 12 else 24, color=title_color, bold=True,
         first=True, space_after=0)


def ref_strip(slide, W, H, text):
    """Bottom strip citing LITERATURE (references source) — never internal
    scripts/instruments (user ruling 2026-08-31). Omit entirely when a page
    rests on internal derivation only."""
    if not text:
        return
    _, tf = tb(slide, 0.55, H - 0.42, W - 1.9, 0.34)
    para(tf, [("References｜", {"bold": True}), (text, {})],
         size=9, color=MUTED, first=True, space_after=0, fit_w=W - 1.9)


def add_pic(slide, path: Path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)


def add_table(slide, x, y, w, rows, col_w=None, font=10.5, header_font=9.5,
              row_h=0.30):
    shp = slide.shapes.add_table(len(rows), len(rows[0]),
                                 Inches(x), Inches(y), Inches(w),
                                 Inches(row_h * len(rows)))
    tbl = shp.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(w * cw / total)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_top = cell.margin_bottom = Emu(18000)
            tf = cell.text_frame
            tf.word_wrap = True
            if isinstance(val, tuple):
                text, ov = val
            else:
                text, ov = val, {}
            para(tf, text, size=(header_font if ri == 0 else font),
                 color=ov.get("color", WHITE if ri == 0 else INK),
                 bold=ov.get("bold", ri == 0), first=True, space_after=0)
    return tbl


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def number_pass(prs, W, H):
    n = len(prs.slides._sldIdLst)
    for i, s in enumerate(prs.slides, 1):
        _, tf = tb(s, W - 1.25, H - 0.42, 0.75, 0.32)
        para(tf, f"{i} / {n}", size=10, color=MUTED, name=MONO, first=True,
             align=PP_ALIGN.RIGHT, space_after=0)


def pptx_text(path: Path) -> str:
    prs = Presentation(str(path))
    parts = []
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        parts.append(cell.text_frame.text)
        if s.has_notes_slide:
            parts.append(s.notes_slide.notes_text_frame.text)
    return "\n".join(parts)


# ==== gates over the BUILT pptx text (generic samples — replace per project) ====
# Every deck edition of one deliverable family runs the SAME gates, each with
# an injected-violation positive control EVERY build (a gate that never fires
# is not a gate). Origin: a research project's term-gate / value-gate.
FORBIDDEN_TERMS = ("样例禁词",)   # canonical-vocabulary lint: variants that must never appear
VALUES = ("127", "43.7")          # load-bearing numbers that must appear VERBATIM


def term_gate(txt, name):
    hits = sorted({t for t in FORBIDDEN_TERMS if t in txt})
    if hits:
        raise SystemExit(f"FAIL term-gate({name}): forbidden terms {hits}")


def value_gate(txt, name):
    missing = [v for v in VALUES if v not in txt]
    if missing:
        raise SystemExit(f"FAIL value-gate({name}): values missing {missing}")


_LINK_PAT = re.compile(r'Target="(file:///[^"]+)"')


def collect_file_links(path: Path):
    """Local-file hyperlink targets as PowerPoint stored them (package rels)."""
    out = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith(".rels"):
                for t in _LINK_PAT.findall(z.read(name).decode("utf-8")):
                    out.append(unquote(t[len("file:///"):]))
    return sorted(set(out))


def link_gate(path: Path, min_links=0):
    """A dead jump button renders exactly like a live one, and the text/layout
    gates are blind to it — so linked-artifact renames/moves need their own
    gate. min_links is PER EDITION (a 4:3 cut without the index page really
    does carry fewer links than the 16:9 one). Origin: a research round (2026-08-31)."""
    targets = collect_file_links(path)
    if len(targets) < min_links:
        raise SystemExit(f"FAIL link-gate({path.name}): expected >= "
                         f"{min_links} file links, found {len(targets)}")
    dead = [t for t in targets if not Path(t).exists()]
    if dead:
        raise SystemExit(f"FAIL link-gate({path.name}): unresolved {dead}")
    return targets


def run_gates(path: Path, min_links=0) -> None:
    txt = pptx_text(path)
    term_gate(txt, path.name)
    value_gate(txt, path.name)
    for gate, bad, tag in ((term_gate, txt + FORBIDDEN_TERMS[0], "term"),
                           (value_gate, "", "value")):
        try:
            gate(bad, "control")
        except SystemExit as e:
            if "(control)" not in str(e):
                raise
        else:
            raise SystemExit(f"FAIL {tag}-gate: positive control did not fire")
    targets = link_gate(path, min_links)
    if targets:  # positive control: an impossible target must be caught
        probe = targets + [str(path.parent / "__link_gate_control__.html")]
        if all(Path(t).exists() for t in probe):
            raise SystemExit("FAIL link-gate: positive control did not fire")
    print(f"gates OK ({path.name}): term clean + {len(VALUES)} values present "
          f"+ {len(targets)} file links resolve "
          "(+injected-violation controls fired)")


