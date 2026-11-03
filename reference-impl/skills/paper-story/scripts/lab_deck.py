#!/usr/bin/env python
"""paper-story lab_deck — class B: the lab's PPTX template edited from story.json (references/formal-deck.md §2–§4).

  python lab_deck.py --run <run_dir> --format deck   [--out lab-deck.pptx]    single-paper talk (base: _templates/base_single-paper.pptx)
  python lab_deck.py --runs <dir1> <dir2> ... --format onepage [--out lab-onepage.pptx]   ten-papers format, one page per paper (base: _templates/base_ten-papers.pptx)
  python lab_deck.py ... --render                                           PowerPoint COM export of every slide to PNG beside the deck (acceptance)
  python lab_deck.py --selftest                                             two-sided calibration of the layout gates L7–L10 (L10 needs PowerPoint)

Never rendered from the HTML: the blank base (title slide only, PaperSurvey/_templates since 2026-09-22; before, each build
stripped a full source deck) is COPIED, new pages added on the same layouts (標題及物件), a Thanks slide re-created. Slide text ENGLISH, speaker notes Chinese (user rulings 2026-09-03).
Built 2026-09-04 for the first real talk (Tran 2018). Gates run AFTER the deck is saved; exit 2 on FAIL.

Round 4 (2026-09-14, schema @5): pages built in deck.pages ORDER and dispatched by section; Verdict page, Storyline page, takeaway
line under content titles.

Round 5 (2026-09-14, user review of the round-4 deck — 「字體偏小跟字數偏多」, sources not shown, Future work missing, Keypoint moved
to the closing): the GaN decks (deck D 0831, deck E 0907) are the STRUCTURE reference — Title → Outlines → Key points → Introduction →
Fabrication → Results → Conclusion → Future work — and everything else is an addition. Pages dispatch on `en.pages[n].layout` or the
section: cover (Outlines) · source (About this paper: first-page image, publication dates, journal facts with their route) ·
keypoint (the five fields at 22/20 pt on ONE slide, 22/18 when needed, split over two slides only when neither fits) · keylogic (the slogan as step boxes with
"in this paper" boxes — the key point is shown AND spoken up front) · methods (grouped method boxes) · verdict (goal → judged by →
result → status; rows that do not fit above the footer band drop to 14 pt, then split over pages at 16 pt) · timeline (horizontal) · process (the GaN vertical step list beside the cross-section) · storyline (AND / BUT /
THEREFORE + numbered moves) · conclusion (measured vs simulated) · futurework (the paper's next steps vs my extensions) · search
(vocabulary ledger → query → backward / forward chasing → stop) · references. Every diagram is native editable shapes (the
user hand-tunes the deck).

Round 6 (2026-09-15, the user's hand-tuned Mu 2020 deck, references/formal-deck.md §2b R6-1…R6-14): one size per level
(title 32 · head 20 B · body 18 · node 16 · note 14 · references 12); figure pages carry up to three statements (principle →
figure reading → conclusion, no takeaway line) at 1.5 line spacing while the figure keeps FIG_MIN_H; a "\n" inside a statement
is a soft break (Shift+Enter); no Source strips, so the figure takes the height down to the footer band; References at 12 pt
over as many slides as needed; an existing output last saved by anyone but this generator is never overwritten.
Gates: L1 4:3 · L2 English slides · L3 Key points slide in the front block (round 7; was: key point verbatim on the first seven
slides) · L4 Thanks last · L6 storyline slide, conclusion statements (round 7 dropped the verdict-slide check) · L7 WARN body run < 14 pt, a run off the size levels, or slide text > DENSITY_MAX
chars (References list exempt) · L8 FAIL no References slide, WARN a leftover Source strip · L9 WARN GaN skeleton order by
fixed titles · L10 (with --render) PowerPoint's own text layout: FAIL text taller than a bordered shape or a shape ending below the
slide edge, WARN taller than a borderless one, a title laid out on more than one line, or a non-picture shape reaching into
the footer band wherever it starts (2026-10-12: a row lying wholly inside the band passed); INFO a picture in
the band (R6-8) · L11 WARN reference tags [n] in slide text, or a "Fig. x:" prefix / "→" marker in a figure page's statements.

Round 7 (2026-09-21, the user's final Chinese-notes Mu 2020 deck, references/formal-deck.md §2c R7): gates recalibrated on the
user's two accepted finals (v2 0915, v3 0921), each change with its selftest positive control. L3 now checks the Key points slide
sits in the front block (≤ slide 4) and only reports where the slogan is (the logic chain moved to the Conclusion section); L6 no
longer asks for a 'Judged by' verdict slide; L7 exempts the Key points slide from DENSITY_MAX; L9 does not ask a review deck
(Horizontal / Vertical / Comparison pages) for Fabrication; L10 ignores trailing blank paragraphs (both finals FAILed on "¶ ¶" in
boxes that visibly fit); L11 flags only a LEADING "→" (an inline causal arrow is the user's own style).

Round 8 (2026-11-03, user ruling on the senior's ten-paper deck, references/formal-deck.md §6): the ten-paper page (--format onepage)
honours onepage.fields (four = no Features row), prints the venue as a small text badge top-left (the senior's journal logo; the title
keeps "(year)"), runs the G4 density step (each table cell <= 1 number, Result qualitative-first, the review verdict out of the slide —
the slide keeps "Authors: ..." — and every moved-out sentence into the speaker notes), lays a story@6 tile's panels out inside one cell,
and writes onepage.script + each tile's notes as the page's speaker notes. Gate L12 (onepage only, WARN): a cell with more than one
number, or a review verdict printed on a paper page.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR, MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from PIL import Image
import sys as _hksys  # machine roots at run time (platform/codemod_roots.py, build plan H-1)
from pathlib import Path as _HKPath
_hksys.path.insert(0, str(_HKPath(__file__).resolve().parents[3] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_story as RS  # noqa: E402  (tile / four-five-field helpers shared with the renderer — one definition)

# Blank bases (2026-09-22): title slide only, derived once from two labmate decks by strip_to_title + metadata scrub —
# no per-build stripping. Not shipped in the public kit: its default is --base blank (blank_base()).
TEMPLATES = hkroots.path("NOTES_VAULT", "literature", "PaperSurvey", "_templates")
BASES = {"deck": "base_single-paper.pptx", "onepage": "base_ten-papers.pptx"}
LAYOUT_BODY = ("標題及物件", "OBJECT", "Title and Content")
LAYOUT_BLANK = ("空白", "BLANK", "Blank")
FONT = "Times New Roman"
W, H = 10.0, 7.5
X0, CW = 0.69, 8.64            # the template's rule runs 0.69–9.33 in (measured on the round-4 render)
Y_BODY = 6.5                   # bottom of diagram / table content (the old Source strip top; kept so accepted diagram pages do not move)
CJK_RE = re.compile(r"[\u2E80-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF]")
BLUE = TAKEAWAY_RGB = RGBColor(0x1A, 0x5F, 0x9E)   # the blue the ten-papers page already uses for its Key point line
NODE = RGBColor(0x5B, 0x9B, 0xD5)                  # the GaN Fabrication pages' timeline blue
LIGHT = RGBColor(0xE9, 0xF1, 0xF9)
DARK = RGBColor(0x1F, 0x1F, 0x1F)
GRAY = RGBColor(0x50, 0x50, 0x50)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN, GREEN_FILL = RGBColor(0x1E, 0x7B, 0x3A), RGBColor(0xE8, 0xF4, 0xEA)
ORANGE, ORANGE_FILL = RGBColor(0xC0, 0x50, 0x00), RGBColor(0xFC, 0xEE, 0xE2)
STATUS_EN = {"achieved": ("Measured", GREEN), "partly": ("Partly", RGBColor(0xB0, 0x6A, 0x00)),
             "simulated-only": ("Simulated only", ORANGE), "not-shown": ("Not shown", RGBColor(0xB0, 0x20, 0x20))}
TABLE_ROWS = (("Structure", "structure"), ("Features", "features"), ("Method", "method"), ("Result", "result"), ("Conclusion", "conclusion"))
MIN_PT = 14                    # body text floor (user 2026-09-14: 字體偏小); the GaN decks set body 20, titles 36
# chars per slide outside the exempt shapes. Ruler (2026-09-14, all runs counted): labmate deck E median 137 / max 226;
# labmate deck D median 219 / max 643 (its Key points table); conference deck F median 364 / max 1220 (a multi-paper survey,
# not the structure reference). 650 = just above the structure reference's densest slide.
DENSITY_MAX = 650
# average Times glyph width in em for the layout estimates. Measured 2026-09-14 on the rendered round-5 Key points row: 64 chars
# at 16 pt span 6.27 in → 0.44 em; 0.46 keeps a margin. The old 0.5 split a table that fits one slide over two half-empty slides.
K_TIMES = 0.46
FOOTER_TOP = 6.94              # in — the template's footer band (logo strip); L10 warns for a non-picture shape reaching into it
Y_FIG = FOOTER_TOP - 0.04      # figure pages: no Source strip since round 6 (R6-12), the figure takes the height down to the band
FIG_MIN_H = 2.8                # in — a figure page keeps 1.5 line spacing (R6-2) only while its figure box stays this tall
PT_TITLE, PT_HEAD, PT_BODY, PT_NODE, PT_NOTE, PT_REF = 32, 20, 18, 16, 14, 12   # R6-1: one size per level, never per length
LEVELS = (PT_TITLE, PT_HEAD, PT_BODY, PT_NODE, PT_NOTE, PT_REF)
BUILD_STAMP = "paper-story lab_deck.py"   # core_properties.last_modified_by; PowerPoint writes the user's name there on save
CITE_RE = re.compile(r"\[\d+(?:\s*[,–-]\s*\d+)*\]")                        # R6-11: [54], [60, 64], [82–84]
FIG_PREFIX_RE = re.compile(r"^\s*Fig(?:ure)?\.?\s*\d+[a-z]?\s*[:：]", re.I)   # R6-3: no "Fig. 4:" lead-in
EXEMPT_NAMES = ("Source strip", "References list")   # L7 only; a leftover Source strip is L8's WARN
DIAGRAM_LAYOUTS = {"cover", "source", "keypoint", "keylogic", "methods", "verdict", "timeline", "process", "storyline",
                   "conclusion", "futurework", "search", "references"}
SKELETON = (("Outlines", r"^outlines?\b"), ("Key points", r"^key points?\b"), ("Fabrication", r"fabrication"),
            ("Conclusion", r"^conclusions?\b"), ("Future work", r"^future work"), ("References", r"^references?\b"))


# ---------------------------------------------------------------- pptx surgery
def find_layout(prs, names):
    for l in prs.slide_layouts:
        if l.name in names:
            return l
    return prs.slide_layouts[1]


def delete_slide(prs, idx):
    sldIdLst = prs.slides._sldIdLst
    sld = list(sldIdLst)[idx]
    prs.part.drop_rel(sld.rId)
    sldIdLst.remove(sld)


def strip_to_title(prs):
    """Keep ONLY the title slide. The template's Thanks slide is re-created at the end (thanks_slide) instead of kept:
    python-pptx names new slide parts slideN.xml by count, so a kept slide13.xml collides with the 12th new slide — the
    first build wrote a duplicate zip entry and PowerPoint refused the file (2026-09-04)."""
    for i in range(len(prs.slides) - 1, 0, -1):
        delete_slide(prs, i)


ADVISOR = ""   # cover "Advisor:" line; --advisor overrides, --advisor "" drops the line
BLANK_BASE = False   # --base blank: build on python-pptx's own default master instead of the template copies


def advisor_line():
    return [f"Advisor: {ADVISOR}"] if ADVISOR else []


def blank_base(kind, out: Path):
    """A template-free base (2026-11-03): python-pptx's default master (10 x 7.5 in, layouts 'Title Slide' /
    'Title and Content' / 'Blank') with ONE title slide carrying the three boxes the fill code looks for —
    the title placeholder, a 'Presenter' subtitle and the venue box named '文字方塊 1'. No lab master, logo or footer band."""
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = "Title"
    for sh in s.placeholders:
        if sh.placeholder_format.idx == 1:
            sh.text_frame.text = "Presenter:"
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(7.8), Inches(0.5))
    tb.name = "文字方塊 1"
    tb.text_frame.text = "Venue"
    prs.save(str(out))
    return Presentation(str(out))


def open_base(kind, out: Path):
    """Copy the blank base for `kind` to `out` and open it. The bases in TEMPLATES are already stripped (strip_to_title
    is how they were made, and how to remake them); a missing base or one with more than its title slide stops loudly.
    With --base blank (BLANK_BASE) no template is read: blank_base() makes a template-free title slide."""
    if BLANK_BASE:
        return blank_base(kind, out)
    if TEMPLATES is None:
        sys.exit("lab_deck: NOTES_VAULT unset in adapt/host.toml; the blank bases live in its literature/PaperSurvey/_templates")
    base = TEMPLATES / BASES[kind]
    if not base.is_file():
        sys.exit(f"lab_deck: blank base missing: {base} — regenerate it with strip_to_title (references/formal-deck.md §1)")
    shutil.copy(base, out)
    prs = Presentation(str(out))
    if len(prs.slides) != 1:
        sys.exit(f"lab_deck: base {base} has {len(prs.slides)} slides, expected 1 (title only) — "
                 "regenerate it with strip_to_title from the source deck (references/formal-deck.md §1)")
    return prs


def thanks_slide(prs):
    s = prs.slides.add_slide(find_layout(prs, LAYOUT_BLANK))
    textbox(s, 2.42, 3.42, 5.33, 0.84, ["Thanks for listening."], size=32, bold=False)
    return s


def set_text(tf, lines, size=20, bold_first=False, color=None, bullet_levels=None, font=FONT):
    """Replace a text frame's content with lines (list of str or (str, level)); keeps the placeholder's paragraph style."""
    tf.clear()
    first = True
    for i, ln in enumerate(lines):
        text, level = (ln if isinstance(ln, tuple) else (ln, 0))
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        _put(p, text, size - 2 * level, color=color, bold=True if (bold_first and i == 0) else None, font=font)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text or ""


def fit_pic(slide, path: Path, x, y, w, h):
    with Image.open(path) as im:
        ar = im.width / im.height
    w_ = w if w / ar <= h else h * ar
    h_ = w_ / ar
    return slide.shapes.add_picture(str(path), Inches(x + (w - w_) / 2), Inches(y + (h - h_) / 2), width=Inches(w_), height=Inches(h_))


def est_lines(text, width_in, size_pt, k=0.5):
    """Wrapped line count for Times at size_pt in width_in (k = average glyph width in em, conservative)."""
    cpl = max(8, int(width_in * 72 / (size_pt * k)))
    return max(1, -(-len(text) // cpl))


# a number never wraps away from its unit, nor a comparison sign from its number (round-5 render: "4 | dB/m multimode")
NB_UNIT = re.compile(r"(?<=\d) (?=(?:dB|[nµμpmck]?m|[kMG]?Hz|M|°)(?![A-Za-z]))|(?<=[<>≈~]) (?=[\d−-])")


def nb(text):
    return NB_UNIT.sub(" ", text) if isinstance(text, str) else text


def _put(p, text, size, color=None, bold=None, italic=None, font=FONT):
    """Runs for `text` at the end of paragraph p. A "\n" is a soft line break (<a:br/>, Shift+Enter — R6-4 / R6-5), never a new
    paragraph, so the statement keeps one bullet; the break carries the run size, or PowerPoint sizes that line from the master."""
    for k, seg in enumerate(nb(text).split("\n")):
        if k:
            p._p.add_br().get_or_add_rPr().set("sz", str(int(round(size * 100))))
        r = p.add_run(); r.text = seg
        f = r.font; f.name = font; f.size = Pt(size)
        if bold is not None:
            f.bold = bold
        if italic is not None:
            f.italic = italic
        if color is not None:
            f.color.rgb = color


def _pair(x):
    return isinstance(x, (list, tuple)) and len(x) == 2 and isinstance(x[0], str) and isinstance(x[1], dict)


def _runs(p, ln, size, color=None, bold=False, italic=False):
    """One paragraph from str | (text, kw) | [(text, kw), ...]; kw may set size / bold / color / italic. A JSON [text, {…}] pair
    counts as (text, kw), so rich lines can live in story.json (colours only from code)."""
    parts = [ln] if (_pair(ln) or not isinstance(ln, list)) else ln
    for part in parts:
        text, kw = (part[0], part[1]) if _pair(part) else (part, {})
        _put(p, text, kw.get("size", size), color=kw.get("color", color), bold=kw.get("bold", bold), italic=kw.get("italic", italic))


def textbox(slide, x, y, w, h, lines, size=12, bold=False, color=None, align=None, italic=False, name=None, anchor=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _runs(p, ln, size, color=color, bold=bold, italic=italic)
        if align is not None:
            p.alignment = align
    if name:
        tb.name = name
    return tb


def box(slide, x, y, w, h, lines, size=14, fill=None, line=None, color=DARK, bold_first=False, align=PP_ALIGN.LEFT,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.MIDDLE, name=None):
    """An editable autoshape carrying text. Every run gets an explicit colour: the theme's shape style paints text white."""
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = 0.08
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(1.5)
    shp.shadow.inherit = False
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.1); tf.margin_top = tf.margin_bottom = Inches(0.05)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        _runs(p, ln, size, color=color, bold=bold_first and i == 0)
        if i:
            p.space_before = Pt(3)
    if name:
        shp.name = name
    return shp


def arrow(slide, x1, y1, x2, y2, color=None, width=2.0, head=True):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color or BLUE
    c.line.width = Pt(width)
    if head:
        ln = c.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd")); tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
    return c


def add_table(slide, x, y, w, rows, col_w, font=10, header=False, colors=None):
    """header=True bolds row 0 instead of column 0; colors {(i, j): RGBColor} tints single cells (the verdict status).
    font may be a (label, value) pair; a cell value may be a list of segments, one paragraph each (round 5: 分段寫)."""
    fl, fv = font if isinstance(font, tuple) else (font, font)
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(0.3 * len(rows)))
    tbl = shp.table
    tbl.first_row = bool(header)   # the template style paints row 0 as a header; the Key points table has none (round 4 build)
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = ""
            tf = cell.text_frame; tf.word_wrap = True
            is_label = (i == 0) if header else (j == 0)
            for k, seg in enumerate(val if isinstance(val, list) else [str(val)]):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                if k:
                    p.space_before = Pt(4)
                tint = colors.get((i, j)) if colors else None
                _put(p, str(seg), fl if is_label else fv, color=tint, bold=is_label or tint is not None)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Inches(0.06); cell.margin_top = cell.margin_bottom = Inches(0.03)
    return shp


def label_line(slide, x, y, w, h, label, text, size=12, color=None):
    """One wrapped paragraph: a bold label run, then the text run."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = label; r.font.name = FONT; r.font.size = Pt(size); r.font.bold = True
    r2 = p.add_run(); r2.text = nb(text); r2.font.name = FONT; r2.font.size = Pt(size)
    if color:
        r.font.color.rgb = color; r2.font.color.rgb = color
    return tb


# ---------------------------------------------------------------- English text (the slide text is English; notes stay Chinese)
def en(story, key, default=""):
    """story.json may carry an `en` block with pre-translated slide text (authored by the model); fall back to default."""
    return (story.get("en") or {}).get(key, default)


def bullets_of(items, n=None):
    return [("• " + t) if isinstance(t, str) else t for t in (items[:n] if n else items)]


# ---------------------------------------------------------------- deck (single paper)
def presenter_of(story, override=None, default="Presenter"):
    """Cover presenter: an explicit --presenter wins, then story.json run.presenter, then the default.
    Until 2026-09-22 the deck format ignored --presenter and read story.json only (found in the lab share export)."""
    return override or (story.get("run") or {}).get("presenter") or default


def build_deck(run: Path, out: Path, presenter=None):
    story = json.loads((run / "story.json").read_text(encoding="utf-8"))
    E = story.get("en") or {}
    src, lg, why = story["source"], story["logic"], story["why_me"]
    prs = open_base("deck", out)
    # --- title slide
    s1 = prs.slides[0]
    for sh in s1.shapes:
        if sh.is_placeholder and sh.placeholder_format.idx == 0:
            set_text(sh.text_frame, [src["title"]], size=24, bold_first=True)
        elif sh.has_text_frame and sh.text_frame.text.startswith("Presenter"):
            set_text(sh.text_frame, [f"Presenter: {presenter_of(story, presenter)}", *advisor_line(), f"Date: {E.get('date', story['run'].get('created', '')[:10].replace('-', '.'))}"], size=16)
        elif sh.has_text_frame and sh.name.startswith("文字方塊 1"):
            set_text(sh.text_frame, [E.get("venue", src.get("venue", ""))], size=16)
            # the round-4 render ran the venue into the template's logo (top right, from ~8.5 in): stop the box short of it
            if (sh.left + sh.width) / 914400 > 8.35:
                sh.width = Inches(8.35) - sh.left
            for p in sh.text_frame.paragraphs:
                p.alignment = PP_ALIGN.RIGHT
        elif sh.has_text_frame and sh.name.startswith("文字方塊 2"):
            set_text(sh.text_frame, [E.get("authors_line") or ("; ".join(src.get("authors", [])) + f" ({src.get('year', '')})")], size=14)
    # the template's top-right logo belongs to the base deck's journal (EDS); en.cover_logo swaps in this paper's source logo
    logo = run / E["cover_logo"] if E.get("cover_logo") else None
    if logo and logo.is_file():
        for sh in list(s1.shapes):
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.left / 914400 > 7.0 and sh.top / 914400 < 1.0:
                x, y, w, h = (v / 914400 for v in (sh.left, sh.top, sh.width, sh.height))
                sh._element.getparent().remove(sh._element)
                fit_pic(s1, logo, x, y, w, h).name = "Source logo"
    extra = E.get("notes_append") or {}
    add_notes(s1, "\n".join(t for t in (story.get("talk", {}).get("opening", ""), extra.get("title", "")) if t))
    body_layout = find_layout(prs, LAYOUT_BODY)
    pages = story["deck"]["pages"]

    def deck_figure(figure):
        """Prefer the deck crop (figures/deck/<name>) over the one-page crop, whose --above margin carries body text. Since round 6
        (R6-7) the deck crop keeps the paper's "Figure x." / "Table x." label line — crop.py --caption --above --below; the
        generator cannot see what a crop contains, so this stays an authoring rule."""
        if not figure:
            return None
        alt = run / "figures" / "deck" / Path(figure).name
        return alt if alt.is_file() else ((run / figure) if (run / figure).is_file() else None)

    def new_page(title, notes="", bullets=None, size=PT_BODY, body_box=None, line_spacing=None):
        s = prs.slides.add_slide(body_layout)
        for sh in list(s.shapes):
            if sh.is_placeholder and sh.placeholder_format.idx == 0:
                # R6-1: one title size on every content slide; a title too long for one line is shortened in story.json (L10
                # warns from PowerPoint's own layout) — the round-5 ladder 36/32/28/24 by string length mixed sizes across a deck
                set_text(sh.text_frame, [title], size=PT_TITLE)
            elif sh.is_placeholder and sh.placeholder_format.idx == 1:
                if not bullets:
                    sh._element.getparent().remove(sh._element)   # an empty body placeholder shows its prompt text in edit view
                    continue
                if body_box:
                    sh.left, sh.top, sh.width, sh.height = (Inches(v) for v in body_box)
                set_text(sh.text_frame, bullets, size=size)
                if line_spacing:
                    for p in sh.text_frame.paragraphs:
                        p.line_spacing = line_spacing
        add_notes(s, notes)
        return s

    def content_page(title, statements, figure, notes):
        """Figure page (R6-3): up to three statements in the body placeholder — the principle or formula → what the figure
        shows → the conclusion it supports — at 18 pt, no takeaway line, no "Fig. x:" / "→" markers (L11 warns). A "\n" in a
        statement is a soft break (R6-4 / R6-5). Line spacing 1.5 while the figure box keeps FIG_MIN_H, else single (R6-2).
        No Source strip (R6-12): the figure takes the height down to the footer band. Without a figure the statements stand alone."""
        fp = deck_figure(figure)
        y = 1.36
        st = [t for t in statements if t][:3]

        def body_h(sp):   # the round-5 estimate (0.36 in per one-line 18 pt bullet, paragraph spacing included) scaled by spacing
            return (0.14 + sum(0.06 + 0.3 * sp * sum(est_lines(seg, CW - 0.4, PT_BODY) for seg in t.split("\n")) for t in st)) if st else 0

        sp = 1.5 if not fp or Y_FIG - (y + body_h(1.5) + 0.06) >= FIG_MIN_H else 1.0
        bh = body_h(sp)
        s = new_page(title, notes, bullets=[(t, 0) for t in st], body_box=(X0, y, CW, bh) if st else None, line_spacing=sp)
        if fp:
            top = y + bh + 0.06
            fit_pic(s, fp, X0, top, CW, Y_FIG - top)
        return s

    def keypoint_pages(title, table, notes, why=""):
        rows = []
        for label, key in TABLE_ROWS:
            v = table.get(key, "")
            rows.append([label, v if isinstance(v, list) else [x.strip() for x in re.split(r"\s*;\s*", v) if x.strip()]])
        lw_, top = 1.8, 1.5
        why_h = (0.12 + est_lines("Why this paper: " + why, CW, PT_BODY, k=K_TIMES) * PT_BODY * 1.2 / 72) if why else 0
        top += why_h
        vw, avail = CW - lw_, Y_BODY - 0.15 - top

        def row_h(segs, size):
            lh = size * 1.2 / 72
            return 0.1 + sum(est_lines(sg, vw - 0.12, size, k=K_TIMES) * lh for sg in segs) + (len(segs) - 1) * 4 / 72

        # R6-1: row labels 20 B and cells 18 on every deck (round 5 stepped 22/20 → 22/18 → 20/16 by length). 「分段寫」 stays:
        # a list value is one paragraph per segment, and a table taller than one slide splits over two
        fl, fv = PT_HEAD, PT_BODY
        hs = [row_h(sg, fv) for _, sg in rows]
        groups = [(rows, hs)] if sum(hs) <= avail else [(rows[:3], hs[:3]), (rows[3:], hs[3:])]
        for gi, (grp, gh) in enumerate(groups):
            t = title if len(groups) == 1 else f"{title} ({gi + 1}/{len(groups)})"
            s = new_page(t, notes if gi == 0 else "（五個欄位的後半：結果與結論。）")
            if why and gi == 0:   # the paper's contribution, above the table (user 2026-09-14)
                label_line(s, X0, 1.36, CW, why_h, "Why this paper: ", why, size=18)
            if len(grp) * max(gh) <= avail:
                gh = [max(gh)] * len(grp)   # equal rows when they fit: one estimate that over-counts a wrap must not make one row taller
            pad = min(0.3, max(0.0, (avail - sum(gh)) / len(grp)))   # use the slide's height, capped so rows never look stretched
            shp = add_table(s, X0, top, CW, grp, col_w=[lw_, vw], font=(fl, fv))
            for r, h_ in zip(shp.table.rows, gh):
                r.height = Inches(h_ + pad)

    def keylogic_page(title, K, notes):
        s = new_page(title, notes)
        if K.get("why"):
            label_line(s, X0, 1.36, CW, 0.7, "Why this paper: ", K["why"], size=18)
        steps = K["steps"]; n = len(steps); gap = 0.3; bw = (CW - gap * (n - 1)) / n; sz = 16; ln_h = sz * 1.2 / 72
        tall = lambda key: 0.25 + ln_h * (1 + max(est_lines(st.get(key, ""), bw - 0.2, sz, k=K_TIMES) for st in steps))
        core = K.get("core_method", "")   # one-sentence methodology replaces the per-step "In this paper" boxes (user 2026-09-14)
        top = 2.2 if K.get("why") else 1.5; th = max(1.9, tall("move")); low = top + th + 0.45
        lh = min(Y_BODY - 0.1 - low, max(1.2, tall("in_paper")))
        for k, st in enumerate(steps):
            x = X0 + k * (bw + gap)
            box(s, x, top, bw, th, [(f"Step {k + 1}", {"bold": True}), st["move"]], size=sz, fill=BLUE, color=WHITE, anchor=MSO_ANCHOR.TOP)
            if not core:
                arrow(s, x + bw / 2, top + th + 0.03, x + bw / 2, low - 0.05)
                box(s, x, low, bw, lh, [("In this paper", {"bold": True, "color": BLUE}), st["in_paper"]], size=sz, fill=LIGHT, line=BLUE, anchor=MSO_ANCHOR.TOP)
            if k < n - 1:
                arrow(s, x + bw + 0.03, top + th / 2, x + bw + gap - 0.03, top + th / 2)
        if core:
            ch = min(Y_BODY - 0.1 - low, 0.3 + est_lines("Core methodology: " + core, CW - 0.3, PT_BODY, k=K_TIMES) * PT_BODY * 1.2 / 72)
            box(s, X0, low - 0.1, CW, ch, [[("Core methodology: ", {"bold": True, "color": BLUE}), (core, {})]], size=PT_BODY, fill=LIGHT, line=BLUE)

    def methods_page(title, M, notes):
        s = new_page(title, notes)
        groups = M["groups"]; n = len(groups); gap = 0.25; gw = (CW - gap * (n - 1)) / n
        for gi, g in enumerate(groups):
            x = X0 + gi * (gw + gap)
            box(s, x, 1.45, gw, 0.62, [g["name"]], size=PT_HEAD, fill=BLUE, color=WHITE, bold_first=True, align=PP_ALIGN.CENTER)
            items = g["items"]; ih = min(1.35, (6.3 - 2.25 - 0.15 * (len(items) - 1)) / len(items)); y = 2.25
            for it in items:
                box(s, x, y, gw, ih, [(it["name"], {"bold": True}), it["answers"]], size=PT_NODE, fill=LIGHT, line=BLUE)
                y += ih + 0.15

    def verdict_page(title, V, notes):
        """Rows that do not fit above the footer band at the node level drop one level (PT_NOTE, still the MIN_PT floor); if
        they still do not fit, they split over pages at the node level, like the Key points table (2026-10-12: seven rows of
        three-line boxes ran into the footer band and off the slide, and L10 did not see it)."""
        top, gap, ws = 1.8, 0.06, any(v.get("status") for v in V)

        def fits(rows, size):
            return sum(verdict_need(rows, size, ws)) + gap * (len(rows) - 1) <= FOOTER_TOP - 0.1 - top
        if fits(V, PT_NODE) or len(V) == 1:
            return verdict_rows(title, V, notes, PT_NODE, ws)
        if fits(V, PT_NOTE):
            return verdict_rows(title, V, notes, PT_NOTE, ws)
        groups, cur = [], []
        for v in V:
            if cur and not fits(cur + [v], PT_NODE):
                groups.append(cur); cur = []
            cur.append(v)
        groups.append(cur)
        start = 1
        for gi, g in enumerate(groups):
            cont = (f"（接續上一頁的判定表，這頁是第 {start}–{start + len(g) - 1} 項：一樣逐列說明每個目標用什麼方式判定、"
                    "得到什麼結果，以及我認為它算不算達到。）")
            verdict_rows(f"{title} ({gi + 1}/{len(groups)})", g, notes if gi == 0 else cont, PT_NODE, ws)
            start += len(g)

    def verdict_cols(with_status):
        # Status 1.45 in: at the 16 pt node level "Measured" / "Simulated" broke mid-word in 1.17 in (round-6 Tran regression build)
        cols = (("Goal", 1.8), ("Judged by", 2.4), ("Result", 2.27), ("Status", 1.45)); gaps = (0.3, 0.3, 0.12)
        if not with_status:   # no status column: the deck does not rule on the authors (user 2026-09-14)
            span = CW - 0.6
            cols = (("Goal", span * 0.28), ("Judged by", span * 0.37), ("Result", span * 0.35)); gaps = (0.3, 0.3)
        return cols, gaps, with_status

    def verdict_need(V, size, ws):
        # row heights from the text they carry: R6-1 fixed the size, so the row grows instead of the text shrinking (round-6 Tran
        # build: three lines at 16 pt crossed the old fixed 0.82 in rows, L10 FAIL)
        cols, ln = verdict_cols(ws)[0], size * 1.2 / 72
        return [max(0.62, 0.14 + ln * max(est_lines(v.get(key, ""), w - 0.2, size, k=K_TIMES)
                                         for key, (_, w) in zip(("goal", "judged_by", "result"), cols))) for v in V]

    def verdict_rows(title, V, notes, size, ws):
        s = new_page(title, notes)
        cols, gaps, with_status = verdict_cols(ws)
        xs = [X0]
        for (_, w), g in zip(cols, gaps):
            xs.append(xs[-1] + w + g)
        for (lab, w), x in zip(cols, xs):
            textbox(s, x, 1.3, w, 0.46, [lab], size=PT_HEAD, bold=True, color=GRAY, align=PP_ALIGN.CENTER)
        # spare height is shared, capped at 0.2 in a row
        y, gap = 1.8, 0.06
        need = verdict_need(V, size, ws)
        spare = FOOTER_TOP - 0.1 - y - gap * (len(V) - 1) - sum(need)
        for v, rh in zip(V, [h + min(0.2, max(0.0, spare / len(V))) for h in need]):
            label, rgb = STATUS_EN.get(v.get("status", ""), (v.get("status", ""), GRAY))
            box(s, xs[0], y, cols[0][1], rh, [v.get("goal", "")], size=size, fill=LIGHT, line=BLUE, bold_first=True)
            arrow(s, xs[0] + cols[0][1] + 0.03, y + rh / 2, xs[1] - 0.03, y + rh / 2)
            box(s, xs[1], y, cols[1][1], rh, [v.get("judged_by", "")], size=size, line=BLUE)
            arrow(s, xs[1] + cols[1][1] + 0.03, y + rh / 2, xs[2] - 0.03, y + rh / 2)
            box(s, xs[2], y, cols[2][1], rh, [v.get("result", "")], size=size, line=BLUE)
            if with_status:
                box(s, xs[3], y, cols[3][1], rh, [label], size=size, fill=rgb, color=WHITE, bold_first=True, align=PP_ALIGN.CENTER)
            y += rh + gap

    def timeline_page(title, T, notes):
        s = new_page(title, notes)
        items = T["items"]; n = len(items); slot = CW / n; ly = 2.5
        arrow(s, X0, ly, X0 + CW, ly, color=NODE, width=3.0)
        for k, it in enumerate(items):
            cx = X0 + slot * (k + 0.5); col = ORANGE if it.get("this") else NODE
            textbox(s, cx - slot / 2, 1.5, slot, 0.5, [it["year"]], size=20, bold=True, color=ORANGE if it.get("this") else BLUE, align=PP_ALIGN.CENTER)
            box(s, cx - 0.15, ly - 0.15, 0.3, 0.3, [], fill=col, shape=MSO_SHAPE.OVAL)
            lines = [it["text"]] + ([(it["ref"], {"color": GRAY, "size": PT_NOTE})] if it.get("ref") else [])
            box(s, cx - slot / 2 + 0.04, 2.85, slot - 0.08, 2.0, lines, size=PT_NODE, fill=ORANGE_FILL if it.get("this") else LIGHT,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP)
        if T.get("constraint"):
            box(s, X0, 5.05, CW, 1.2, [(T.get("constraint_head", "Platform constraint"), {"bold": True, "color": ORANGE}), T["constraint"]],
                size=PT_NODE, fill=None, line=ORANGE)

    def process_page(title, Pr, figure, notes):
        s = new_page(title, notes)
        if Pr.get("subtitle"):
            textbox(s, X0, 1.36, CW, 0.5, [Pr["subtitle"]], size=20, bold=True)
        steps = Pr["steps"]; n = len(steps); top, bot = 2.0, 6.35; sh_ = (bot - top) / n; lx = X0 + 0.16
        arrow(s, lx, top + sh_ / 2, lx, bot - sh_ / 2, color=NODE, width=4.5, head=False)
        for k, st in enumerate(steps):
            cy = top + sh_ * (k + 0.5)
            box(s, lx - 0.14, cy - 0.14, 0.28, 0.28, [], fill=NODE, shape=MSO_SHAPE.OVAL)
            textbox(s, lx + 0.3, cy - sh_ / 2, 4.35, sh_, [st], size=18, anchor=MSO_ANCHOR.MIDDLE)
        fp = deck_figure(figure)
        if fp:
            fit_pic(s, fp, 5.45, 2.0, 3.88, 3.0)
        if Pr.get("caveat"):
            textbox(s, 5.45, 5.1, 3.88, 1.2, [Pr["caveat"]], size=PT_NOTE, italic=True, color=GRAY)

    def storyline_page(title, S, notes):
        s = new_page(title, notes)
        if S.get("and"):
            parts = (("AND", S["and"], BLUE), ("BUT", S["but"], ORANGE), ("THEREFORE", S["therefore"], GREEN))
            bw = (CW - 0.6) / 3
            for k, (lab, txt, col) in enumerate(parts):
                x = X0 + k * (bw + 0.3)
                box(s, x, 1.42, bw, 1.45, [(lab, {"bold": True, "color": col}), txt], size=PT_NODE, line=col, anchor=MSO_ANCHOR.TOP)
                if k < 2:
                    arrow(s, x + bw + 0.03, 2.15, x + bw + 0.27, 2.15)
        else:
            label_line(s, X0, 1.4, CW, 1.4, "In one sentence: ", S.get("spine", ""), size=PT_BODY, color=BLUE)
        textbox(s, X0, 2.95, CW, 0.46, ["How the authors tell it"], size=PT_HEAD, bold=True, color=BLUE)
        steps = S.get("steps", []); sw = (CW - 0.6) / 3; sh_ = 1.3
        for k, st in enumerate(steps):
            r, c = divmod(k, 3)
            x = X0 + c * (sw + 0.3); y = 3.45 + r * (sh_ + 0.2)
            box(s, x, y, sw, sh_, [[(f"{k + 1}  ", {"bold": True, "color": BLUE, "size": 16}), (st if isinstance(st, str) else st["move"], {})]],
                size=PT_NODE, fill=LIGHT)
            if c < 2 and k < len(steps) - 1:
                arrow(s, x + sw + 0.03, y + sh_ / 2, x + sw + 0.27, y + sh_ / 2)

    def conclusion_page(title, C, notes):
        s = new_page(title, notes)
        if C.get("claim"):
            label_line(s, X0, 1.36, CW, 0.85, "Authors conclude: ", C["claim"], size=PT_BODY)
        bw = (CW - 0.3) / 2; y0 = 2.4 if C.get("claim") else 1.5
        heads = (C.get("measured_head", "Measured"), C.get("simulated_head", "Simulated / calculated only"))
        col_h = lambda head, items: 0.2 + (est_lines(head, bw - 0.2, PT_HEAD, k=K_TIMES) * PT_HEAD + sum(
            est_lines("• " + it, bw - 0.2, PT_BODY, k=K_TIMES) * PT_BODY + 3 for it in items)) * 1.2 / 72
        bh = min(Y_BODY - 0.9 - y0, max(2.0, col_h(heads[0], C["measured"]), col_h(heads[1], C["simulated"])) + 0.15)   # boxes fit their text
        box(s, X0, y0, bw, bh, [(heads[0], {"bold": True, "size": PT_HEAD, "color": GREEN})] + bullets_of(C["measured"]),
            size=PT_BODY, fill=GREEN_FILL, line=GREEN, anchor=MSO_ANCHOR.TOP)
        box(s, X0 + bw + 0.3, y0, bw, bh, [(heads[1], {"bold": True, "size": PT_HEAD, "color": ORANGE})] + bullets_of(C["simulated"]),
            size=PT_BODY, fill=ORANGE_FILL, line=ORANGE, anchor=MSO_ANCHOR.TOP)
        if C.get("open"):
            label_line(s, X0, y0 + bh + 0.3, CW, 0.7, "Still open: ", C["open"], size=PT_BODY)

    def future_page(title, F, notes):
        s = new_page(title, notes)
        lw = 5.25; rw = CW - lw - 0.3; y0 = 1.42
        txt = lambda it: (it["text"] + "  " + it["loc"]) if isinstance(it, dict) else it
        col_h = lambda head, items, w: 0.2 + (est_lines(head, w - 0.2, 20, k=K_TIMES) * 20 + sum(
            est_lines("• " + txt(it), w - 0.2, 18, k=K_TIMES) * 18 + 3 for it in items)) * 1.2 / 72
        bh = min(4.45, max(2.0, col_h(F["paper_head"], F["paper"], lw), col_h(F["mine_head"], F["mine"], rw)) + 0.15)   # boxes fit their text
        box(s, X0, y0, lw, bh, [(F["paper_head"], {"bold": True, "size": 20, "color": BLUE})] +
            [[("• " + it["text"], {}), ("  " + it["loc"], {"color": GRAY, "size": 14})] if isinstance(it, dict) else "• " + it for it in F["paper"]],
            size=18, line=BLUE, anchor=MSO_ANCHOR.TOP)
        arrow(s, X0 + lw + 0.03, y0 + bh / 2, X0 + lw + 0.27, y0 + bh / 2, color=GREEN)
        box(s, X0 + lw + 0.3, y0, rw, bh, [(F["mine_head"], {"bold": True, "size": 20, "color": GREEN})] + bullets_of(F["mine"]),
            size=18, fill=GREEN_FILL, line=GREEN, anchor=MSO_ANCHOR.TOP)
        if F.get("followed"):
            label_line(s, X0, y0 + bh + 0.25, CW, 0.8, "Followed up by: ", F["followed"], size=PT_BODY)

    def search_page(title, Q, notes):
        s = new_page(title, notes)
        lw = 5.4; qw = CW - lw - 0.33; hd, bd = PT_NODE, PT_NODE   # a diagram of five boxes: node text, the box heads in bold
        # box heights from the text they carry (round 5: the fixed 1.8 in box let the third keyword layer cross its border)
        text_h = lambda head, lines, w: 0.2 + (est_lines(head, w - 0.2, hd, k=K_TIMES) * hd + sum(
            est_lines(t, w - 0.2, bd, k=K_TIMES) * bd + 3 for t in lines)) * 1.2 / 72
        h1 = max(text_h("1  " + Q.get("layers_head", "Three keyword layers"), [lab + ": " + val for lab, val in Q["layers"]], lw),
                 text_h("2  Query, batch n → n+1", [Q["query"]], qw)) + 0.1
        box(s, X0, 1.38, lw, h1, [("1  " + Q.get("layers_head", "Three keyword layers"), {"bold": True, "size": hd, "color": BLUE})] +
            [[(lab + ": ", {"bold": True}), (val, {})] for lab, val in Q["layers"]], size=bd, line=BLUE, anchor=MSO_ANCHOR.TOP)
        arrow(s, X0 + lw + 0.03, 1.38 + h1 / 2, X0 + lw + 0.3, 1.38 + h1 / 2)
        box(s, X0 + lw + 0.33, 1.38, qw, h1, [("2  Query, batch n → n+1", {"bold": True, "size": hd, "color": BLUE}), Q["query"]],
            size=bd, line=BLUE, anchor=MSO_ANCHOR.TOP)
        pw = 1.9; bw = (CW - pw - 0.6) / 2; y = 1.38 + h1 + 0.2; px = X0 + bw + 0.3
        h = max(text_h("3  " + Q["backward"]["head"], ["• " + t for t in Q["backward"]["items"]], bw),
                text_h("4  " + Q["forward"]["head"], ["• " + t for t in Q["forward"]["items"]], bw), 1.3) + 0.1
        box(s, X0, y, bw, h, [("3  " + Q["backward"]["head"], {"bold": True, "size": hd, "color": BLUE})] + bullets_of(Q["backward"]["items"]),
            size=bd, line=BLUE, anchor=MSO_ANCHOR.TOP)
        box(s, px, y + h / 2 - 0.55, pw, 1.1, [("This paper", {"bold": True, "size": hd}), Q.get("paper", "")], size=bd, fill=BLUE, color=WHITE, align=PP_ALIGN.CENTER)
        arrow(s, px - 0.03, y + h / 2, X0 + bw + 0.03, y + h / 2)
        arrow(s, px + pw + 0.03, y + h / 2, px + pw + 0.27, y + h / 2)
        box(s, px + pw + 0.3, y, bw, h, [("4  " + Q["forward"]["head"], {"bold": True, "size": hd, "color": BLUE})] + bullets_of(Q["forward"]["items"]),
            size=bd, line=BLUE, anchor=MSO_ANCHOR.TOP)
        ys = y + h + 0.2
        box(s, X0, ys, CW, max(0.6, min(Y_BODY - 0.08 - ys, text_h("", ["5  Screen and stop: " + Q["stop"]], CW) - 0.1)),
            [[("5  Screen and stop: ", {"bold": True, "color": BLUE}), (Q["stop"], {})]], size=bd, fill=LIGHT)

    def references_page(title, R, notes):
        """R6-11: 12 pt on every References slide, split over as many slides as the list needs (round 5 dropped to 11 pt past
        14 entries). Entries are authored APA 7 in en.references; the generator only lays them out."""
        avail, lh, gap = FOOTER_TOP - 0.1 - 1.4, PT_REF * 1.2 / 72, 3 / 72
        chunks, cur, h = [], [], 0.0
        for r in R:
            eh = est_lines(r, CW - 0.2, PT_REF) * lh + gap
            if cur and h + eh > avail:
                chunks.append(cur); cur, h = [], 0.0
            cur.append(r); h += eh
        chunks.append(cur)
        for k, chunk in enumerate(chunks):
            s = new_page(title if len(chunks) == 1 else f"{title} ({k + 1}/{len(chunks)})", notes if k == 0 else "")
            tb = textbox(s, X0, 1.4, CW, avail, chunk, size=PT_REF, name="References list")
            for p in tb.text_frame.paragraphs:
                p.space_after = Pt(3)

    # --- every page in deck.pages ORDER, dispatched by en.pages[n].layout or the section (round 5)
    kp = E.get("keypoint") or lg["keypoint"]
    v5 = bool(story.get("brief"))
    epages = E.get("pages") or {}
    for i, pg in enumerate(pages):
        sec = pg["section"].lower()
        ep = epages.get(str(i + 1)) or epages.get(pg.get("title", "")) or {}
        if ep.get("skip"):   # kept in the class A reference copies, left out of the formal deck (user 2026-09-14)
            continue
        lay = (ep.get("layout") or sec).lower().replace(" ", "").replace("_", "")
        notes, title = pg.get("notes", ""), ep.get("title") or pg.get("title", "")
        if extra.get(str(i + 1)):
            notes = notes + "\n" + extra[str(i + 1)]
        if lay == "cover":
            parts = E.get("outline_parts") or pg.get("highlights", [])
            new_page(ep.get("title") or "Outlines", notes, bullets=[(x, 0) for x in parts], size=24, body_box=(X0 + 0.3, 1.7, CW - 0.6, 4.6))
        elif lay == "source" and E.get("source_info"):
            SI = E["source_info"]
            s = new_page(ep.get("title") or SI.get("title", "About this paper"), notes)
            ip = run / SI["image"]
            if ip.is_file():
                fit_pic(s, ip, X0, 1.42, 4.15, 2.1)
            dates = SI.get("dates", [])
            if dates:
                y0, x_a, x_b = 4.0, X0 + 0.45, X0 + 3.75
                arrow(s, x_a, y0, x_b, y0, color=NODE, width=2.5, head=False)
                for k, (lab, d) in enumerate(dates):
                    cx = x_a + (x_b - x_a) * k / max(1, len(dates) - 1)
                    textbox(s, cx - 0.7, y0 - 0.55, 1.4, 0.38, [lab], size=14, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
                    box(s, cx - 0.12, y0 - 0.12, 0.24, 0.24, [], fill=NODE, shape=MSO_SHAPE.OVAL)
                    textbox(s, cx - 0.7, y0 + 0.16, 1.4, 0.38, [d], size=14, align=PP_ALIGN.CENTER)
                if SI.get("dates_note"):
                    textbox(s, X0, 4.62, 4.15, 0.4, [SI["dates_note"]], size=14, italic=True, color=GRAY, align=PP_ALIGN.CENTER)
            if SI.get("left_note"):   # [[label, value], ...]
                box(s, X0, 5.12, 4.15, 1.25, [[(lab + ": ", {"bold": True}), (val, {})] for lab, val in SI["left_note"]], size=PT_NOTE, fill=LIGHT)
            add_table(s, X0 + 4.4, 1.42, CW - 4.4, SI["rows"], col_w=[1.2, CW - 5.6], font=(PT_NODE, PT_NODE))
        elif lay == "keypoint" and v5 and E.get("table"):
            keypoint_pages(ep.get("title") or E.get("keypoint_title", "Key points"), E["table"], notes, E.get("keypoint_why", ""))
        elif lay == "keypoint":
            content_page(E.get("keypoint_title", "Why this paper · Key point"), [E.get("why_read") or why["why_read"], kp], None, notes)
        elif lay == "keylogic" and E.get("keylogic"):
            keylogic_page(title or "Key point", E["keylogic"], notes)
        elif lay == "methods" and E.get("methods_map"):
            methods_page(title or "Methods", E["methods_map"], notes)
        elif lay == "verdict" and E.get("verdicts"):
            verdict_page(title or "Did it work — and how was it judged?", E["verdicts"], notes)
        elif lay == "timeline" and (ep.get("timeline") or E.get("timeline")):
            timeline_page(title, ep.get("timeline") or E["timeline"], notes)
        elif lay == "process" and E.get("process"):
            process_page(title or "Fabrication", E["process"], pg.get("figure"), notes)
        elif lay == "storyline" and E.get("storyline"):
            storyline_page(title or "How the paper tells its story", E["storyline"], notes)
        elif lay == "conclusion" and E.get("conclusion"):
            conclusion_page(title or "Conclusion", E["conclusion"], notes)
        elif lay == "futurework" and E.get("future_work"):
            future_page(title or "Future work", E["future_work"], notes)
        elif lay == "search" and E.get("search"):
            search_page(title or "Keywords and how to find extensions", E["search"], notes)
        elif lay == "references" and E.get("references"):
            references_page(title or "References", E["references"], notes)
        else:
            # R6-3: en.pages[n].statements = [principle, figure reading, conclusion]; an older story's highlights + takeaway fill
            # the same three slots, the takeaway as the conclusion statement instead of a blue line under the title
            hl, tk = ep.get("highlights") or pg.get("highlights", []), (ep.get("takeaway", "") if v5 else "")
            content_page(title, ep.get("statements") or (hl[:3 - bool(tk)] + ([tk] if tk else [])), pg.get("figure"), notes)
    ts = thanks_slide(prs)
    add_notes(ts, "我的報告到這邊，謝謝大家。\n" + "\n".join(f"（{q.get('q','')} → {q.get('a','')}）" for q in story.get("talk", {}).get("if_asked", [])))
    prs.core_properties.last_modified_by = BUILD_STAMP   # overwrite_block reads it: PowerPoint replaces it on the presenter's save
    prs.save(str(out))
    return out


# ---------------------------------------------------------------- one page per paper (ten-papers format)
# G4 density pass (user ruling 2026-11-03: the senior's pages carry one number per cell and a qualitative Result; the review
# verdict is spoken, not printed). A "number" is a numeric token not glued to a letter (so Bi2Se3 / SiO2 are not numbers) and a
# range (180–350 °C) counts once. Only whole CLAUSES are dropped (split at ; | and sentence ends), the first clause always stays,
# and everything dropped is written into the speaker notes — the density step moves text, it does not delete it.
NUM_RE = re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?(?:\s*(?:–|-|to)\s*\d+(?:[.,]\d+)?)?")
CLAUSE_RE = re.compile(r"\s*;\s*|\s+\|\s+|(?<=[.!?])\s+")
VERDICT_RE = re.compile(r"\s*\|\s*Verdict\s*:|\s+Verdict\s*:|\s*深讀判定[：:]|\s*偏離[：:]", re.I)
CELL_LABEL = {"structure": "Structure", "features": "Features", "method": "Method", "result": "Result", "conclusion": "Conclusion"}


def count_numbers(text):
    return len(NUM_RE.findall(text or ""))


def densify_cell(text, qualitative_first=False):
    """(slide_text, dropped_clauses). At most one number stays; with qualitative_first (Result) the clauses without a number
    lead and the first numeric clause follows."""
    text = (text or "").strip()
    clauses = [c.strip() for c in CLAUSE_RE.split(text) if c.strip()]
    if len(clauses) <= 1:
        return text, []
    order = sorted(range(len(clauses)), key=lambda i: (count_numbers(clauses[i]) > 0, i)) if qualitative_first else list(range(len(clauses)))
    keep, used = [], 0
    for i in order:
        n = count_numbers(clauses[i])
        if not keep or used + n <= 1:
            keep.append(i); used += n
    if not qualitative_first:
        keep.sort()
    out = ""
    for i in keep:
        out = clauses[i] if not out else out + (" " if re.search(r"[.!?]$", out) else "; ") + clauses[i]
    return out, [clauses[i] for i in range(len(clauses)) if i not in keep]


def densify_table(t, fields="five"):
    """(cells {key: slide text}, extra_notes [Chinese note lines]) for one one-page table (English)."""
    flat = lambda v: " · ".join(v) if isinstance(v, list) else (v or "")
    cells, extra = {}, []
    for key in ("structure", "features", "method", "result", "conclusion"):
        if key == "features" and fields == "four":
            continue
        v = flat(t.get(key, ""))
        if key == "conclusion":
            parts = VERDICT_RE.split(v, maxsplit=1)
            if len(parts) == 2 and parts[0].strip():
                v = parts[0].strip()
                extra.append(f"深讀判定（不上投影片，口頭補充）：{parts[1].strip()}")
        s, dropped = densify_cell(v, qualitative_first=(key == "result"))
        cells[key] = s
        if dropped:
            extra.append(f"{CELL_LABEL[key]} 為降密度移出投影片的句子：" + "；".join(dropped))
    return cells, extra


def onepage_notes(op, extra):
    """Speaker notes of one ten-paper page (user ruling 2026-11-03 G5): onepage.script (source line, purpose line) + each tile's
    notes, then the sentences the density step moved off the slide. '' when the run declares none of it."""
    sc = op.get("script") or {}
    lines = [x for x in (sc.get("source_line"), sc.get("purpose_line")) if x]
    lines += [f"({chr(97 + k)}) {f['notes']}" for k, f in enumerate(op.get("figures", [])) if f.get("notes")]
    return "\n".join(lines + ([""] + extra if lines and extra else extra))


def tile_grid(n):
    """Panels of one tile laid out inside its cell: (columns, rows)."""
    cols = 1 if n == 1 else 2 if n <= 4 else 3
    return cols, -(-n // cols)


def build_onepage(runs, out: Path, presenter="Presenter", date=""):
    prs = open_base("onepage", out)
    s1 = prs.slides[0]
    for sh in s1.shapes:
        if sh.is_placeholder and sh.placeholder_format.idx == 0:
            set_text(sh.text_frame, ["Review of waveguide coupling papers"], size=28, bold_first=True)
        elif sh.has_text_frame and sh.text_frame.text.startswith("Presenter"):
            set_text(sh.text_frame, [f"Presenter: {presenter}", *advisor_line(), f"Date: {date}"], size=16)
    body_layout = find_layout(prs, LAYOUT_BODY)
    notes_all = []
    for run in runs:
        run = Path(run)
        story = json.loads((run / "story.json").read_text(encoding="utf-8"))
        E = story.get("en") or {}
        src, lg, op = story["source"], story["logic"], story["onepage"]
        s = prs.slides.add_slide(body_layout)
        for sh in list(s.shapes):
            if sh.is_placeholder:
                sh._element.getparent().remove(sh._element)
        # G8 (user ruling 2026-11-03): the senior's pages carry the journal logo top-left; a small text badge stands in for it, and the
        # title keeps "(year)" only. A run without a venue gets no badge and the old title line.
        venue = (E.get("venue") or src.get("venue") or "").strip()
        if venue:
            box(s, 0.3, 0.1, min(2.6, 0.4 + 0.065 * len(venue)), 0.26, [venue], size=9, fill=LIGHT, line=BLUE, color=BLUE, bold_first=True, name="Venue badge")
            textbox(s, 0.3, 0.37, 9.4, 0.5, [f"{src['title']} ({src.get('year', '')})"], size=14, bold=True, name="Page title")
        else:
            textbox(s, 0.3, 0.15, 9.4, 0.7, [f"{src['title']} ({src.get('year', '')})"], size=14, bold=True, name="Page title")
        kp_en = "Key point: " + (E.get("keypoint") or lg["keypoint"])
        textbox(s, 0.3, 0.88 if venue else 0.78, 9.4, 0.55 if venue else 0.6, [kp_en], size=9 if len(kp_en) > 220 else 10, color=RGBColor(0x1A, 0x5F, 0x9E))
        figs = op["figures"][:6]
        tiled = RS.schema_ver(story) >= 6   # story@6: a figure is a TILE (argument step) that may hold several panels
        # pictures: a 3-column strip on the upper half, table below (deck C-style density); a three-line key point
        # overlapped the strip on the first build (Tran), so the strip starts at 1.45 in. story@6 tiles: one row up to 4 tiles
        cols = len(figs) if (tiled and len(figs) <= 4) else min(3, len(figs)); rows = (len(figs) + cols - 1) // cols
        gx, gy, gw, gh = 0.3, 1.45, 9.4, 2.85 if rows > 1 else 2.5
        cw, ch = gw / cols, gh / rows
        for k, f in enumerate(figs):
            paths = []
            for fn in RS.tile_files(f):
                fp = run / "figures" / "deck" / Path(fn).name
                paths.append(fp if fp.is_file() else run / fn)
            paths = [p for p in paths if p.is_file()]
            if paths:
                gcols, grows = tile_grid(len(paths))
                px, py = gx + (k % cols) * cw + 0.05, gy + (k // cols) * ch + 0.02
                pw, ph_ = (cw - 0.1) / gcols, (ch - 0.22) / grows
                for j, fp in enumerate(paths):
                    fit_pic(s, fp, px + (j % gcols) * pw, py + (j // gcols) * ph_, pw - (0.03 if gcols > 1 else 0), ph_ - (0.03 if grows > 1 else 0))
                first = RS.tile_files(f)[0]
                textbox(s, gx + (k % cols) * cw, gy + (k // cols) * ch + ch - 0.22, cw, 0.22, [f"({chr(97 + k)}) " + (E.get("figures", {}).get(first) or f.get("locator", ""))], size=8)
        t = E.get("table") or op["table"]
        fields = RS.onepage_fields(op)
        cells, extra = densify_table(t, fields)   # G4: every ten-paper page goes through the density step
        rows_t = [[CELL_LABEL[key], cells[key]] for key in CELL_LABEL if key in cells]
        add_table(s, 0.3, gy + gh + 0.1, 9.4, rows_t, col_w=[1.2, 8.2], font=9)
        add_notes(s, onepage_notes(op, extra) or story.get("talk", {}).get("opening", "") or lg.get("keypoint_description", "")[:600])
        notes_all.append(src["title"])
    ts = thanks_slide(prs)
    add_notes(ts, "我的報告到這邊，謝謝大家。")
    prs.core_properties.last_modified_by = BUILD_STAMP
    prs.save(str(out))
    return out


# ---------------------------------------------------------------- gates + render
def _frames(sh):
    if sh.has_text_frame:
        yield sh.text_frame
    if getattr(sh, "has_table", False) and sh.has_table:
        for r in sh.table.rows:
            for c in r.cells:
                yield c.text_frame


def slide_title(slide):
    for sh in slide.shapes:
        if sh.is_placeholder and sh.placeholder_format.idx == 0:
            return sh.text_frame.text.strip()
    return ""


def deck_text(path: Path):
    prs = Presentation(str(path))   # NBSP (nb) reads back as a space, so L3 / L6 match the story's plain text
    return ["\n".join(tf.text for sh in s.shapes for tf in _frames(sh)).replace(" ", " ") for s in prs.slides]


def layout_gates(path: Path):
    """L7–L9 and L11 read the EMITTED deck only. L7 WARN (taste thresholds: the presenter decides). L8 FAIL a missing References
    slide (determinable); WARN a leftover Source strip — round 6 (R6-12) retired them, where round 5 FAILed a picture slide
    without one. L9 WARN (the skeleton is a structure reference, not a law). L11 WARN reference tags and figure-page markers
    (R6-11 / R6-3: determinable text, but a tag may be the presenter's deliberate choice)."""
    prs = Presentation(str(path))
    rows, small, offlevel, dense, strips, cites, marks, titles = [], [], [], [], [], [], [], []
    for n, s in enumerate(prs.slides, 1):
        titles.append(slide_title(s))
        if n == 1:
            continue
        outline = bool(re.match(SKELETON[0][1], titles[-1], re.I))   # the Outlines list keeps its own size class (R6-1)
        pic = any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes)
        chars = 0
        for sh in s.shapes:
            if sh.name == "Source strip":
                strips.append(n)
            if sh.name in EXEMPT_NAMES:
                continue
            body = sh.is_placeholder and sh.placeholder_format.idx == 1
            for tf in _frames(sh):
                for p in tf.paragraphs:
                    ptxt = "".join(r.text for r in p.runs)
                    m = CITE_RE.search(ptxt)
                    if m:
                        cites.append((n, m.group(0)))
                    if pic and body and (FIG_PREFIX_RE.match(ptxt) or ptxt.lstrip().startswith("→")):   # R7-11: inline → is a causal arrow
                        marks.append((n, ptxt[:24]))
                    for r in p.runs:
                        t = r.text.strip()
                        chars += len(t)
                        if t and r.font.size is not None:
                            if r.font.size.pt < MIN_PT:
                                small.append((n, r.font.size.pt, t[:20]))
                            elif r.font.size.pt not in LEVELS and not outline:
                                offlevel.append((n, r.font.size.pt, t[:20]))
        if chars > DENSITY_MAX and not re.match(SKELETON[1][1], titles[-1], re.I):   # R7-8: the Key points table is dense by design
            dense.append((n, chars))
    probs = ([f"runs < {MIN_PT} pt outside the exempt shapes: {small[:5]}"] if small else []) + \
            ([f"runs off the size levels {LEVELS} (R6-1): {offlevel[:5]}"] if offlevel else []) + \
            ([f"slides over {DENSITY_MAX} chars: {dense[:6]}"] if dense else [])
    rows.append(("L7", "WARN" if probs else "PASS", "; ".join(probs) if probs else
                 f"every body run ≥ {MIN_PT} pt and on a size level {LEVELS}; every slide ≤ {DENSITY_MAX} chars (References list exempt)"))
    has_refs = any(re.match(SKELETON[-1][1], t, re.I) for t in titles)
    if not has_refs:
        rows.append(("L8", "FAIL", "no References slide"))
    elif strips:
        rows.append(("L8", "WARN", f"Source strip shapes on slides {sorted(set(strips))} — retired by R6-12 (the References slides carry the sources)"))
    else:
        rows.append(("L8", "PASS", "References slide present; no Source strips (R6-12)"))
    found, missing = [], []
    review = any(re.match(r"^(horizontal|vertical)\b|^comparison\b", t, re.I) for t in titles)   # R7-1: a review has families, no fabrication
    for name, rx in SKELETON:
        if name == "Fabrication" and review:
            continue
        idx = next((i for i, t in enumerate(titles) if re.search(rx, t, re.I)), None)
        (missing.append(name) if idx is None else found.append((idx, name)))
    order_ok = [i for i, _ in found] == sorted(i for i, _ in found)
    p9 = ([f"missing {missing}"] if missing else []) + ([] if order_ok else [f"order differs from the GaN skeleton: {[nm for _, nm in sorted(found)]}"])
    rows.append(("L9", "WARN" if p9 else "PASS", "; ".join(p9) if p9 else
                 "GaN skeleton in order (Outlines → Key points → Fabrication → Conclusion → Future work → References; Fabrication not asked of a "
                 "review with Horizontal / Vertical / Comparison pages, R7-1; claim-titled Introduction / Results pages are not read by title)"))
    p11 = ([f"reference tags in slide text (R6-11: the figure captions carry them): {cites[:6]}"] if cites else []) + \
          ([f"'Fig. x:' prefix or '→' marker in a figure page's statements (R6-3: the order carries the role): {marks[:6]}"] if marks else [])
    rows.append(("L11", "WARN" if p11 else "PASS", "; ".join(p11) if p11 else
                 "no reference tags in slide text; figure-page statements carry no 'Fig. x:' prefix or '→' marker"))
    return rows


def gates(path: Path, keypoint_en: str, fmt: str, story=None):
    rows = []
    slides = deck_text(path)
    prs = Presentation(str(path))
    ok_size = abs(prs.slide_width / 914400 - W) < 0.05 and abs(prs.slide_height / 914400 - H) < 0.05
    rows.append(("L1", "PASS" if ok_size else "FAIL", f"slide size {prs.slide_width/914400:.2f}×{prs.slide_height/914400:.2f} in (template 4:3)"))
    cjk = [(i + 1, CJK_RE.search(t).group(0)) for i, t in enumerate(slides) if CJK_RE.search(t)]
    rows.append(("L2", "FAIL" if cjk else "PASS", ("CJK on slide text (slides must be English; notes carry the Chinese): " + str(cjk[:6])) if cjk else "every slide's text is English"))
    if fmt == "deck":
        # R7-1 / R7-2 (user final 2026-09-21): the front block is Title → Outlines → Key points; the slogan left the front (the logic
        # chain closes the talk), so L3 checks the Key points table's place, and reports where the slogan sits without ruling on it
        kpt = next((i + 1 for i, s in enumerate(prs.slides) if re.match(SKELETON[1][1], slide_title(s), re.I)), None)
        at = next((i + 1 for i, t in enumerate(slides) if keypoint_en and keypoint_en[:40] in t), None)
        where = f"; slogan verbatim on slide {at}" if at else "; slogan not verbatim on any slide (INFO — the logic-chain page paraphrases it, R7-2)"
        rows.append(("L3", "PASS" if kpt and kpt <= 4 else "FAIL",
                     (f"Key points slide at {kpt}, in the front block (R7-1)" if kpt and kpt <= 4 else
                      f"Key points slide {'at ' + str(kpt) if kpt else 'missing'} — it belongs right after Outlines (R7-1)") + where))
    else:
        rows.append(("L3", "PASS", f"{len(slides) - 2} paper pages between title and Thanks"))
    thanks = "Thanks for listening" in slides[-1]
    rows.append(("L4", "PASS" if thanks else "FAIL", "last slide is the template's Thanks slide" if thanks else "Thanks slide not last"))
    if fmt == "deck" and story is not None and story.get("brief"):
        E, alltext = story.get("en") or {}, "\n".join(slides)
        pages = story["deck"]["pages"]
        probs = []   # R7-1: no Verdict page — the advisor's four questions are answered in the Key points rows and the notes
        if (story.get("talk") or {}).get("story_arc") and not any(re.search(r"stor(y|ies)", slide_title(s), re.I) for s in prs.slides):
            probs.append("no storyline slide")
        miss = []
        for n_, ep in (E.get("pages") or {}).items():
            if ep.get("skip"):
                continue
            k = int(n_) - 1 if n_.isdigit() else -1
            lay = (ep.get("layout") or (pages[k]["section"] if 0 <= k < len(pages) else "")).lower().replace(" ", "")
            concl = (ep.get("statements") or [ep.get("takeaway", "")])[-1]   # R6-3: the conclusion statement (an older story's takeaway)
            if concl and lay not in DIAGRAM_LAYOUTS and concl.split("\n")[0][:30] not in alltext:
                miss.append(n_)
        if miss:
            probs.append(f"conclusion statement missing on en.pages {miss[:6]}")
        rows.append(("L6", "WARN" if probs else "PASS", "; ".join(probs) if probs else "storyline slide, every content-page conclusion statement on its slide"))
    if fmt == "deck":
        rows += layout_gates(path)
    if fmt == "onepage":
        rows.append(density_gate(path))
    return rows


def density_gate(path: Path):
    """L12 (user ruling 2026-11-03 G4, ten-paper pages): every table cell on a paper page carries at most one number and the review
    verdict stays in the speaker notes. WARN — the cell text is the presenter's to edit; both findings are determinable from the
    emitted table cells. A page whose Structure cell lists four thicknesses is named, not failed."""
    prs = Presentation(str(path))
    many, verdicts = [], []
    for n, s in enumerate(prs.slides, 1):
        if n == 1 or n == len(prs.slides):
            continue
        for sh in s.shapes:
            if getattr(sh, "has_table", False) and sh.has_table:
                for r in sh.table.rows:
                    label, text = r.cells[0].text_frame.text.strip(), r.cells[1].text_frame.text.replace(" ", " ")
                    if count_numbers(text) > 1:
                        many.append((n, label, count_numbers(text)))
                    if re.search(r"Verdict\s*:|深讀判定", text):
                        verdicts.append((n, label))
    probs = ([f"cells with more than one number (page, cell, count): {many[:6]}"] if many else []) + \
            ([f"review verdict printed on the slide (it belongs in the speaker notes): {verdicts[:4]}"] if verdicts else [])
    return ("L12", "WARN" if probs else "PASS", "; ".join(probs) if probs else
            "every table cell carries at most one number and no review verdict is printed on a paper page")


def com_layout(pres):
    """L10 — measured by PowerPoint's own text layout on the EMITTED deck (round 5, 2026-09-14: the Search page's third keyword
    layer crossed its box border while L1–L9 all passed — a text gate cannot see layout). Determinable → FAIL: text taller than a
    BORDERED autoshape (it visibly crosses the drawn line). Not determinable → WARN: text taller than a borderless shape (it may
    spill onto nothing), or a shape starting above the footer band and ending inside it. Title and Thanks slides are skipped.
    Round 6: a picture or group reaching into the footer band is INFO (R6-8: legibility beats the frame), any other shape there
    stays WARN; a title PowerPoint lays out on more than one line is WARN (R6-1: one title size, so the title is shortened —
    the ink test of the round-6 layout report: bound height > 1.45 lines of the title size).
    2026-10-12: the band test was "starts above the band AND ends inside it", so a 7th verdict row lying WHOLLY inside the band
    (or below the slide edge) passed while it sat on the footer logo. Any shape whose bottom passes FOOTER_TOP now counts,
    wherever it starts; a shape ending below the slide edge is FAIL (determinable: it is cut off). Slide-level footer / date /
    slide-number placeholders belong to the band and are skipped."""
    over, spill, foot, pics, wrap, off = [], [], [], [], [], []
    last = pres.Slides.Count
    slide_h = pres.PageSetup.SlideHeight / 72
    for sl in pres.Slides:
        n = sl.SlideIndex
        if n in (1, last):
            continue
        for shp in sl.Shapes:
            try:
                top, bottom = shp.Top / 72, (shp.Top + shp.Height) / 72
                if shp.Type == 14 and shp.PlaceholderFormat.Type in (13, 15, 16):   # ppPlaceholderSlideNumber / Footer / Date
                    continue
                if bottom > slide_h + 0.02:
                    off.append((n, shp.Name, round(top, 2), round(bottom, 2)))
                if bottom > FOOTER_TOP + 0.02:
                    (pics if shp.Type in (6, 13) else foot).append((n, shp.Name, round(bottom, 2)))   # msoGroup, msoPicture
                if shp.HasTable or not shp.HasTextFrame or not shp.TextFrame.HasText:
                    continue
                tf = shp.TextFrame
                if shp.Type == 14 and shp.PlaceholderFormat.Type in (1, 3):   # msoPlaceholder: ppPlaceholderTitle / CenterTitle
                    tr = tf.TextRange
                    if tr.BoundHeight > tr.Font.Size * 1.2 * 1.45:
                        wrap.append((n, tr.Text[:30]))
                # trailing blank paragraphs take height but draw nothing (2026-09-21: both user finals FAILed on "¶ ¶" after the last
                # line of a bordered box that visibly fits) — measure only up to the last visible character
                # (paragraph boundaries only: Characters(1, n).BoundHeight silenced both positive controls in the selftest)
                t2 = shp.TextFrame2.TextRange
                paras = t2.Text.split("\r")
                k = max((i for i, p_ in enumerate(paras) if p_.strip()), default=len(paras) - 1) + 1
                need = (t2.Paragraphs(1, k).BoundHeight if k < len(paras) else t2.BoundHeight) + tf.MarginTop + tf.MarginBottom
                if need > shp.Height + 3.6:   # 0.05 in tolerance
                    rec = (n, shp.Name, tf.TextRange.Text[:24], round((need - shp.Height) / 72, 2))
                    (over if shp.Type == 1 and shp.Line.Visible == -1 else spill).append(rec)   # msoAutoShape with a drawn line
            except Exception:
                continue
    info = f"; INFO pictures reaching into the footer band (R6-8 allows it): {pics[:5]}" if pics else ""
    warn = ([f"text taller than a borderless shape: {spill[:5]}"] if spill else []) + \
           ([f"titles laid out on more than one line (shorten the title, R6-1): {wrap[:5]}"] if wrap else []) + \
           ([f"non-picture shapes reaching the footer band (> {FOOTER_TOP} in): {foot[:5]}"] if foot else [])
    fails = ([f"text crosses a bordered shape (slide, name, text, overflow in): {over[:5]}"] if over else []) + \
            ([f"shapes ending below the slide edge ({slide_h:.2f} in; slide, name, top, bottom): {off[:5]}"] if off else [])
    if fails:
        return ("L10", "FAIL", "; ".join(fails) + "".join("; " + w for w in warn) + info)
    if warn:
        return ("L10", "WARN", "; ".join(warn) + info)
    return ("L10", "PASS", f"PowerPoint layout: no text taller than its shape; every title on one line; no text or shape in the footer band (> {FOOTER_TOP} in)" + info)


def _with_deck(path: Path, fn):
    """Open `path` in PowerPoint, return fn(pres); fn must return plain Python values, never COM objects.
    PowerPoint is a single-instance COM server: Dispatch ATTACHES to the user's running session. Quit() then closed the
    user's own open decks (2026-09-14: lab-deck.pptx was open for hand-tuning). Quit only an instance this call started.
    Every COM reference stays local and is dropped before/after Quit: a proxy still held by the caller keeps the quitting
    process alive, the next Dispatch attaches to it, and Open returns a disconnected object (2026-09-14: selftest crashed
    on its second L10 case with AttributeError Open.Slides, RPC_E_DISCONNECTED on Quit)."""
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    ours = app.Presentations.Count == 0
    pres = app.Presentations.Open(str(path.resolve()), WithWindow=False)
    try:
        try:
            pres.Slides.Count
        except AttributeError:
            raise RuntimeError(f"PowerPoint Open returned a disconnected object for {path} — attached to a quitting instance?")
        return fn(pres)
    finally:
        try:
            pres.Close()
        except AttributeError:
            pass
        pres = None
        if ours and app.Presentations.Count == 0:
            app.Quit()
        app = None


def render_png(path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    def work(pres):
        layout = com_layout(pres)
        for i, sl in enumerate(pres.Slides, 1):
            sl.Export(str((out_dir / f"slide-{i:02d}.png").resolve()), "PNG", 1600, 1200)
        return pres.Slides.Count, layout

    n, layout = _with_deck(path, work)
    stale = sorted(p.name for p in out_dir.glob("slide-*.png") if int(re.search(r"(\d+)", p.stem).group(1)) > n)
    return n, stale, layout


def overwrite_block(out: Path, overwrite=False):
    """Why `out` must not be written, or None. An owner file ~$<name> means the deck is open in PowerPoint: always refused (L-049).
    An existing deck whose last_modified_by is not BUILD_STAMP was saved by someone — PowerPoint writes the user's name there on
    every save — and a hand-tuned deck is a baseline (R6-14): refused unless --overwrite. Decks built before round 6 carry no
    stamp and are refused too, the safe side of an unknown."""
    if (out.parent / ("~$" + out.name)).exists():
        return f"{out.name} is open in PowerPoint (~${out.name} present) — close it or build to another --out"
    if out.exists() and not overwrite:
        try:
            by = Presentation(str(out)).core_properties.last_modified_by
        except Exception as e:
            return f"{out.name} exists and is not a readable deck ({e.__class__.__name__}) — build to another --out"
        if by != BUILD_STAMP:
            return (f"{out.name} exists and was last saved by {by!r}, not by lab_deck.py — a hand-tuned deck is a baseline (R6-14): "
                    "build to another --out, or pass --overwrite when the presenter said it may be replaced")
    return None


# ---------------------------------------------------------------- selftest (L7–L11 + the overwrite guard, two-sided)
def selftest():
    td = Path(tempfile.mkdtemp(prefix="lab-deck-selftest-"))
    png = td / "pic.png"
    Image.new("RGB", (400, 300), (200, 210, 230)).save(png)
    GOOD = [("Outlines", "text"), ("Key points", "text"), ("Structure and fabrication", "pic"), ("Loss: 16 dB/m", "pic"),
            ("Conclusion", "text"), ("Future work", "text"), ("References", "refs")]
    LONG = "A deliberately long slide title that cannot stay on one line at the title level"
    FIG_KINDS = ("pic", "marker", "leadarrow", "inlinearrow")

    def make(name, spec, stamp=True):
        out = td / f"{name}.pptx"
        prs = open_base("deck", out); lay = find_layout(prs, LAYOUT_BODY)
        for title, kind in spec:
            s = prs.slides.add_slide(lay)
            for sh in list(s.shapes):
                if sh.is_placeholder and sh.placeholder_format.idx == 0:
                    set_text(sh.text_frame, [LONG if kind == "longtitle" else title], size=PT_TITLE)
                elif sh.is_placeholder and sh.placeholder_format.idx == 1 and kind in FIG_KINDS:
                    # a figure page's statements in the body placeholder: a soft break in the clean one, markers in the defect;
                    # R7-11: an inline causal arrow is clean, a leading arrow is the retired role marker
                    sh.left, sh.top, sh.width, sh.height = Inches(X0), Inches(1.4), Inches(CW), Inches(1.0)
                    set_text(sh.text_frame, [{"marker": "Fig. 3: the loss falls → 16 dB/m", "leadarrow": "→ the loss falls to 16 dB/m",
                                              "inlinearrow": "Narrow tips merge → larger MFD → higher overlap"}.get(kind, "The principle;\nwhat the figure shows")],
                             size=PT_BODY)
                elif sh.is_placeholder:
                    sh._element.getparent().remove(sh._element)
            if kind not in FIG_KINDS:
                textbox(s, X0, 1.5, CW, 0.8, ["A short body line at eighteen points."], size=PT_BODY)
            if kind in FIG_KINDS + ("strip",):
                fit_pic(s, png, X0, 2.5, CW, 3.6)
            if kind == "strip":      # a round-5 deck: the strip R6-12 retired
                textbox(s, X0, 6.5, CW, 0.3, ["Source: test figure, 2026"], size=11, color=GRAY, name="Source strip")
            if kind == "small":
                textbox(s, X0, 3.0, CW, 0.5, ["tiny body text"], size=10)
            if kind == "offlevel":   # the round-5 Key points size, off the R6-1 levels
                textbox(s, X0, 3.0, CW, 0.5, ["a 22 pt label"], size=22)
            if kind == "dense":
                textbox(s, X0, 3.0, CW, 3.0, ["x" * 900], size=PT_NOTE)
            if kind == "cite":
                textbox(s, X0, 3.0, CW, 0.5, ["Double tip: 1.1 dB [54]"], size=PT_BODY)
            if kind == "refs":
                textbox(s, X0, 2.4, CW, 4.0, ["[Ref. 1] Author, A. (2020). Title. Journal, 1, 1."] * 16, size=PT_REF, name="References list")
            if kind == "boxover":    # L10 positive control: 30 words in a 0.5 in bordered box
                box(s, X0, 3.0, 3.0, 0.5, ["long text " * 30], size=PT_NOTE, line=BLUE, name="Overflow box")
            if kind == "boxtrail":   # L10 negative control (user finals 2026-09-21): a fitting box with two trailing blank paragraphs
                box(s, X0, 3.0, 6.0, 0.75, ["Step 3", "one line that fits", "", ""], size=PT_NODE, line=BLUE, name="Trailing box")
            if kind == "plainover":  # borderless spill
                textbox(s, X0, 3.0, 3.0, 0.4, ["long text " * 30], size=PT_NOTE, name="Spill box")
            if kind == "footer":     # a text shape in the footer band: still WARN
                box(s, X0, 6.5, 3.0, 0.8, ["x"], size=PT_NOTE, line=BLUE, name="Footer box")
            if kind == "inband":     # 2026-10-12 miss: a box lying wholly inside the band (it starts below FOOTER_TOP) — WARN
                box(s, X0, 7.0, 3.0, 0.4, ["x"], size=PT_NOTE, line=BLUE, name="Inband box")
            if kind == "offslide":   # 2026-10-12 miss: a verdict row starting in the band and ending below the slide edge — FAIL
                box(s, X0, 7.27, 3.0, 0.94, ["High-speed data"], size=PT_NODE, line=BLUE, name="Offslide box")
            if kind == "footpic":    # a picture enlarged into the band: INFO only (R6-8)
                fit_pic(s, png, X0, 5.2, 3.0, 2.2).name = "Footer picture"
        thanks_slide(prs)
        if stamp:
            prs.core_properties.last_modified_by = BUILD_STAMP
        prs.save(str(out))
        return out

    def sub(title, kind):
        return [(t, kind if t == title else k) for t, k in GOOD]

    def swap(spec, a, b):
        sp = list(spec); ia = [t for t, _ in sp].index(a); ib = [t for t, _ in sp].index(b); sp[ia], sp[ib] = sp[ib], sp[ia]
        return sp

    cases = [
        ("good", GOOD, {"L7": "PASS", "L8": "PASS", "L9": "PASS", "L11": "PASS"}, {}),
        ("small-font", sub("Key points", "small"), {"L7": "WARN"}, {"L7": "(3, 10.0"}),
        ("off-level-size", sub("Key points", "offlevel"), {"L7": "WARN"}, {"L7": "(3, 22.0"}),
        ("dense-slide", sub("Conclusion", "dense"), {"L7": "WARN"}, {"L7": "(6, 9"}),
        ("legacy-source-strip", sub("Loss: 16 dB/m", "strip"), {"L8": "WARN"}, {"L8": "[5]"}),
        ("no-references", [x for x in GOOD if x[0] != "References"], {"L8": "FAIL", "L9": "WARN"}, {"L8": "no References", "L9": "References"}),
        ("order-swapped", swap(GOOD, "Conclusion", "Structure and fabrication"), {"L9": "WARN"}, {"L9": "order"}),
        ("future-missing", [x for x in GOOD if x[0] != "Future work"], {"L9": "WARN", "L7": "PASS"}, {"L9": "Future work"}),
        ("reference-tag", sub("Conclusion", "cite"), {"L11": "WARN"}, {"L11": "(6, '[54]')"}),
        ("figure-marker", sub("Loss: 16 dB/m", "marker"), {"L11": "WARN"}, {"L11": "(5, 'Fig. 3"}),
        # round 7 (user final 2026-09-21): each change carries its positive control beside the user-final shape it now accepts
        ("leading-arrow", sub("Loss: 16 dB/m", "leadarrow"), {"L11": "WARN"}, {"L11": "(5, '→ the loss"}),
        ("inline-arrow", sub("Loss: 16 dB/m", "inlinearrow"), {"L11": "PASS"}, {}),
        ("dense-key-points", sub("Key points", "dense"), {"L7": "PASS"}, {}),
        ("review-families", [("Horizontal 1: Taper", "pic") if t == "Structure and fabrication" else (t, k) for t, k in GOOD],
         {"L9": "PASS"}, {}),
        ("fabrication-missing", [("Loss again", "pic") if t == "Structure and fabrication" else (t, k) for t, k in GOOD],
         {"L9": "WARN"}, {"L9": "Fabrication"}),
    ]
    ok_all = True
    print("lab_deck selftest — L7–L11 and the overwrite guard, two-sided calibration")
    for name, spec, expect, needle in cases:
        got = {g: (st, msg) for g, st, msg in layout_gates(make(name, spec))}
        for g, st in expect.items():
            ok = got[g][0] == st and needle.get(g, "") in got[g][1]
            ok_all &= ok
            print(f"  {'OK ' if ok else 'BAD'} {name:<20} {g:<4} expected {st:<5} got {got[g][0]:<5} {'' if ok else '— ' + got[g][1][:120]}")
    # L3 (R7-1): the Key points table in the front block — the good deck passes; moved behind the Conclusion it fails
    for name, spec, st, needle in (("key-points-front", GOOD, "PASS", "slide at 3"),
                                   ("key-points-late", swap(GOOD, "Key points", "Conclusion"), "FAIL", "at 6")):
        got = {g: (s_, m) for g, s_, m in gates(make("l3-" + name, spec), "", "deck")}["L3"]
        ok = got[0] == st and needle in got[1]
        ok_all &= ok
        print(f"  {'OK ' if ok else 'BAD'} {name:<20} L3   expected {st:<5} got {got[0]:<5} {'' if ok else '— ' + got[1][:120]}")
    # cover presenter (2026-09-22): the flag must win over story.json (the defect: it was ignored), story.json over the default
    for name, story, flag, want in (("presenter-flag-wins", {"run": {"presenter": "Story"}}, "Flag", "Flag"),
                                    ("presenter-from-story", {"run": {"presenter": "Story"}}, None, "Story"),
                                    ("presenter-default", {"run": {}}, None, "Presenter")):
        got_p = presenter_of(story, flag)
        ok = got_p == want
        ok_all &= ok
        print(f"  {'OK ' if ok else 'BAD'} {name:<20} cover expected {want:<5} got {got_p}")
    # emitted soft break (R6-4 / R6-5): one paragraph, one <a:br/> carrying the run size — read back from the saved deck
    body = next(sh for sh in Presentation(str(td / "good.pptx")).slides[3].shapes if sh.is_placeholder and sh.placeholder_format.idx == 1)
    ps = body.text_frame._txBody.findall(qn("a:p")); brs = ps[0].findall(qn("a:br")) if ps else []
    ok = len(ps) == 1 and len(brs) == 1 and brs[0].find(qn("a:rPr")) is not None and brs[0].find(qn("a:rPr")).get("sz") == "1800"
    ok_all &= ok
    print(f"  {'OK ' if ok else 'BAD'} {'soft-break emit':<20} emit expected 1 paragraph / 1 br sz 1800, got {len(ps)} / {len(brs)}")
    # verdict layout (2026-10-12): rows that do not fit above the band shrink one level, then split; every row stays above it.
    # Each oversize case first asserts its rows do NOT fit at 16 pt (the positive control: without the fix they cross the band)
    def verdict_deck(name, V):
        rd = td / f"verdict-{name}"; rd.mkdir()
        story = {"source": {"title": "T", "authors": ["A"], "year": 2026}, "logic": {"keypoint": "k"}, "why_me": {"why_read": "w"},
                 "run": {}, "en": {"verdicts": V}, "deck": {"pages": [{"section": "verdict", "title": "Did it work?"}]}}
        (rd / "story.json").write_text(json.dumps(story), encoding="utf-8")
        build_deck(rd, rd / "lab-deck.pptx")
        return rd / "lab-deck.pptx"
    vrow = lambda g, j, r: {"goal": g, "judged_by": j, "result": r, "status": "partly"}
    V_SHORT = [vrow(f"Goal {i}", "S11 with / without resistor", "< −8 dB up to 67 GHz") for i in range(6)]
    V_MID = [vrow("Extended bandwidth with 33 Ω termination", "Fitted response curve extrapolated beyond the sweep",
                  "About 246 GHz, extrapolated beyond 220 GHz")] + [vrow("High responsivity", "Photocurrent at 1550 nm", "0.56 A/W")] * 6
    V_LONG = [vrow("Extended bandwidth with 33 Ω termination and a long tail of words",
                   "Fitted response curve extrapolated beyond the 220 GHz sweep limit of the heterodyne setup",
                   "About 246 GHz, extrapolated; the measurement itself stops at 220 GHz in this work")] * 5
    room = FOOTER_TOP - 0.1 - 1.8
    for name, V, slides_want, pt_want, oversize in (("verdict-fits", V_SHORT, 1, 16.0, False), ("verdict-shrinks", V_MID, 1, 14.0, True),
                                                    ("verdict-splits", V_LONG, 2, 16.0, True)):
        est16 = sum(max(0.62, 0.14 + PT_NODE * 1.2 / 72 * max(est_lines(v[k], w, PT_NODE, k=K_TIMES)
                    for k, w in (("goal", 1.6), ("judged_by", 2.2), ("result", 2.07)))) for v in V) + 0.06 * (len(V) - 1)
        vs = [sl for sl in Presentation(str(verdict_deck(name, V))).slides if slide_title(sl).startswith("Did it work?")]
        bottom = max(((sh.top + sh.height) / 914400 for sl in vs for sh in sl.shapes), default=99)
        sizes = {r.font.size.pt for sl in vs for sh in sl.shapes if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
                 for p in sh.text_frame.paragraphs for r in p.runs if r.font.size}
        cont = [sl.notes_slide.notes_text_frame.text for sl in vs[1:]]   # a continuation page carries a full spoken sentence
        ok = ((est16 > room) == oversize and len(vs) == slides_want and sizes == {pt_want} and bottom <= FOOTER_TOP
              and all(c.startswith("（接續上一頁的判定表") and "項" in c for c in cont))
        ok_all &= ok
        print(f"  {'OK ' if ok else 'BAD'} {name:<20} vrd  expected {slides_want} slide(s) at {pt_want:g} pt above {FOOTER_TOP} in, "
              f"got {len(vs)} at {sorted(sizes)} bottom {bottom:.2f} (16-pt estimate {est16:.2f} vs room {room:.2f})")
    # ten-paper pages (2026-11-03, user rulings G2/G4/G5/G8): density step, four/five rows, venue badge, notes = script + tile notes.
    # Each check is two-sided: the dense input is trimmed (positive), the already-sparse input is left alone (negative).
    def check(name, group, want, got, ok):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"  {'OK ' if ok else 'BAD'} {name:<20} {group:<4} expected {want}, got {got}")
    dense = "Ron rose 12% vs 48%; films were stable; Dit fell 4 times"
    s_, dr_ = densify_cell(dense, qualitative_first=True)
    check("density-result", "G4", "qualitative clause first, <= 1 number, the 2-number clause moved out",
          repr(s_), s_ == "films were stable; Dit fell 4 times" and dr_ == ["Ron rose 12% vs 48%"] and count_numbers(s_) <= 1)
    sparse = "Authors: the lowest loss of 3 dB/m to date, no CMP"
    s2_, dr2_ = densify_cell(sparse, qualitative_first=False)
    check("density-sparse-kept", "G4", "a one-number cell is left untouched", repr(s2_), s2_ == sparse and dr2_ == [])
    s3_, dr3_ = densify_cell("Bi2Se3 films on SiO2 with 5, 10 and 20 nm", False)
    check("density-first-clause", "G4", "formula digits are not numbers; a lone clause is never cut", repr(s3_), s3_.startswith("Bi2Se3") and dr3_ == [] and count_numbers("Bi2Se3 films on SiO2") == 0)
    cells_, extra_ = densify_table({"structure": "s", "method": "m", "result": "r", "conclusion": "Authors: lower loss | Verdict: provisional (E1); single device"}, "four")
    check("verdict-to-notes", "G4", "slide keeps 'Authors: ...', verdict goes to the notes, no Features cell",
          f"{cells_.get('conclusion')!r} / {len(extra_)} note line(s)", cells_.get("conclusion") == "Authors: lower loss" and "features" not in cells_
          and any("provisional" in x for x in extra_))
    run = td / "ten1"; (run / "figures").mkdir(parents=True)
    for nm in ("a1", "a2", "b1", "c1", "c2", "c3"):
        Image.new("RGB", (300, 200), (180, 200, 230)).save(run / "figures" / f"{nm}.png")
    story10 = {"schema": "paper-story/story@6", "run": {"mode": "story"}, "source": {"title": "A Ten-Paper Test Title", "year": 2025, "venue": "Applied Physics Letters"},
               "logic": {"keypoint": "slogan"},
               "onepage": {"fields": "four", "script": {"source_line": "這邊是 2025 年發表的文章。", "purpose_line": "主要是探討厚度。"},
                           "table": {"structure": "s", "method": "m", "result": "r", "conclusion": "c"},
                           "figures": [{"files": ["figures/a1.png", "figures/a2.png"], "caption": "x", "locator": "Fig. 1", "step": "context", "notes": "第一格的講法。"},
                                       {"files": ["figures/b1.png"], "caption": "y", "locator": "Fig. 2", "step": "series"},
                                       {"files": ["figures/c1.png", "figures/c2.png", "figures/c3.png"], "caption": "z", "locator": "Fig. 3", "step": "trend", "notes": "第三格的講法。"}]},
               "en": {"keypoint": "Thickness sets the transport regime.",
                      "table": {"structure": "Films of several thicknesses", "method": "Sputtering; then annealing at 220 °C; XRD at 3 angles",
                                "result": "Ron rose 12% vs 48%; films were stable; Dit fell 4 times",
                                "conclusion": "Authors: lower loss | Verdict: provisional (E1); single device"}}}
    (run / "story.json").write_text(json.dumps(story10, ensure_ascii=False), encoding="utf-8")
    deck10 = build_onepage([run], td / "ten.pptx", "Tester", "2026-11-03")
    pr10 = Presentation(str(deck10)); pg = pr10.slides[1]
    tb = next(sh for sh in pg.shapes if getattr(sh, "has_table", False) and sh.has_table).table
    labels = [r.cells[0].text_frame.text for r in tb.rows]; ctext = tb.rows[len(labels) - 1].cells[1].text_frame.text
    check("four-field-rows", "G2", "4 rows, no Features", labels, labels == ["Structure", "Method", "Result", "Conclusion"])
    badge = next((sh for sh in pg.shapes if sh.name == "Venue badge"), None)
    title = next(sh for sh in pg.shapes if sh.name == "Page title").text_frame.text
    check("venue-badge", "G8", "badge shows the venue; the title carries the year only",
          f"{badge.text_frame.text if badge is not None else None!r} / {title!r}",
          badge is not None and badge.text_frame.text == "Applied Physics Letters" and "Applied Physics" not in title and title.endswith("(2025)"))
    n_pic = sum(1 for sh in pg.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
    check("tile-panels", "G1", "6 panels in 3 tiles on the page", n_pic, n_pic == 6)
    note10 = pg.notes_slide.notes_text_frame.text
    check("notes-script-tiles", "G5", "notes = source line, purpose line, tile notes, then the moved-out sentences",
          note10.splitlines()[:4], note10.splitlines()[:4] == ["這邊是 2025 年發表的文章。", "主要是探討厚度。", "(a) 第一格的講法。", "(c) 第三格的講法。"]
          and "深讀判定" in note10 and "provisional" in note10 and "Verdict" not in ctext)
    five = dict(story10, onepage=dict(story10["onepage"], fields="five")); five["en"] = dict(story10["en"], table=dict(story10["en"]["table"], features="Same-wafer comparison"))
    run5 = td / "ten5"; shutil.copytree(run, run5); (run5 / "story.json").write_text(json.dumps(five, ensure_ascii=False), encoding="utf-8")
    t5 = next(sh for sh in Presentation(str(build_onepage([run5], td / "ten5.pptx"))).slides[1].shapes if getattr(sh, "has_table", False) and sh.has_table).table
    check("five-field-default", "G2", "5 rows with Features", [r.cells[0].text_frame.text for r in t5.rows], len(t5.rows) == 5 and t5.rows[1].cells[0].text_frame.text == "Features")
    g_ok = {g: (st, m) for g, st, m in gates(deck10, "", "onepage")}["L12"]
    check("density-gate-clean", "L12", "PASS on the built page", g_ok[0], g_ok[0] == "PASS")
    bad10 = Presentation(str(deck10)); btb = next(sh for sh in bad10.slides[1].shapes if getattr(sh, "has_table", False) and sh.has_table).table
    btb.cell(2, 1).text = "Ron rose 12% vs 48% and Dit fell 4 times, Verdict: provisional"
    bad10.save(str(td / "ten-dense.pptx"))
    g_bad = {g: (st, m) for g, st, m in gates(td / "ten-dense.pptx", "", "onepage")}["L12"]
    check("density-gate-fires", "L12", "WARN naming the number count and the printed verdict",
          g_bad[0], g_bad[0] == "WARN" and "(2, 'Result', 3)" in g_bad[1] and "review verdict printed" in g_bad[1])
    # overwrite guard (R6-14): the generator's own output may be rebuilt; a deck saved by anyone else, or open, may not
    owner = make("guard-open", GOOD); (td / ("~$" + owner.name)).write_bytes(b"")
    for name, path, needle in (("guard-own-output", make("guard-own", GOOD), None),
                               ("guard-foreign-stamp", make("guard-foreign", GOOD, stamp=False), "last saved by"),
                               ("guard-open-deck", owner, "open in PowerPoint")):
        why = overwrite_block(path)
        ok = why is None if needle is None else (why is not None and needle in why)
        ok_all &= ok
        print(f"  {'OK ' if ok else 'BAD'} {name:<20} guard expected {'write' if needle is None else 'refuse':<6} got {'write' if why is None else 'refuse'} {'' if ok else '— ' + str(why)[:120]}")
    # L10 reads PowerPoint's own layout; without PowerPoint it cannot run and says so (never a silent PASS)
    com_cases = [
        ("good", GOOD, "PASS", "every title on one line"),
        ("box-overflow", sub("Conclusion", "boxover"), "FAIL", "Overflow box"),
        ("box-trailing-blank", sub("Conclusion", "boxtrail"), "PASS", "every title on one line"),
        ("borderless-spill", sub("Conclusion", "plainover"), "WARN", "Spill box"),
        ("footer-band-text", sub("Conclusion", "footer"), "WARN", "Footer box"),
        ("footer-band-inside", sub("Conclusion", "inband"), "WARN", "Inband box"),
        ("below-slide-edge", sub("Conclusion", "offslide"), "FAIL", "below the slide edge"),
        ("footer-band-picture", sub("Conclusion", "footpic"), "PASS", "INFO pictures reaching into the footer band (R6-8 allows it): [(6, 'Footer picture'"),
        ("title-wrap", sub("Future work", "longtitle"), "WARN", "(7, 'A deliberately"),
    ]
    try:
        for name, spec, st, needle in com_cases:
            g, got, msg = _with_deck(make("com-" + name, spec), com_layout)
            ok = got == st and needle in msg
            ok_all &= ok
            print(f"  {'OK ' if ok else 'BAD'} {name:<20} L10  expected {st:<5} got {got:<5} {'' if ok else '— ' + msg[:160]}")
        # the guard's premise, measured: a presenter's edit + save replaces the generator stamp. The edit is part of the control:
        # Save on an untouched presentation writes nothing (2026-09-15 probe: Saved = -1, file mtime and stamp unchanged), and
        # an unchanged file is safe to rebuild anyway
        def edit_and_save(pres):
            tr = pres.Slides(2).Shapes(1).TextFrame.TextRange
            tr.Text = tr.Text + " (hand-tuned)"
            pres.Save()

        saved = make("guard-powerpoint-saved", GOOD)
        _with_deck(saved, edit_and_save)
        why = overwrite_block(saved)
        ok = why is not None and "last saved by" in why
        ok_all &= ok
        print(f"  {'OK ' if ok else 'BAD'} {'guard-after-ppt-save':<20} guard expected refuse got {'write' if why is None else 'refuse'} {'' if ok else '— PowerPoint kept the stamp'}")
    except ImportError as e:
        print(f"  SKIP L10 / PowerPoint-save cases — PowerPoint COM unavailable ({e}); L10 and the guard premise are uncalibrated on this machine")
    print("temp dir:", td)
    print("SELFTEST", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path); ap.add_argument("--runs", type=Path, nargs="*")
    ap.add_argument("--format", choices=["deck", "onepage"])
    ap.add_argument("--out", type=Path); ap.add_argument("--render", action="store_true")
    ap.add_argument("--presenter", default=None, help="cover presenter; deck: overrides story.json run.presenter"); ap.add_argument("--date", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base", choices=["template", "blank"], default="blank", help="blank = no template: python-pptx default master")
    ap.add_argument("--advisor", default=None, help="cover Advisor line; an empty string drops it")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing output last saved by someone else (the presenter said so)")
    a = ap.parse_args(argv)
    global BLANK_BASE, ADVISOR
    BLANK_BASE = a.base == "blank"
    if a.advisor is not None:
        ADVISOR = a.advisor
    if a.selftest:
        return selftest()
    if not a.format:
        ap.error("--format required")
    story = None
    if a.format == "deck":
        if not a.run:
            ap.error("--run required for --format deck")
        out = a.out or (a.run / "lab-deck.pptx")
        stop = overwrite_block(out, a.overwrite)
        if stop:
            ap.error(stop)
        build_deck(a.run, out, a.presenter)
        story = json.loads((a.run / "story.json").read_text(encoding="utf-8"))
        kp = (story.get("en") or {}).get("keypoint") or story["logic"]["keypoint"]
    else:
        runs = a.runs or ([a.run] if a.run else [])
        if not runs:
            ap.error("--runs required for --format onepage")
        out = a.out or (Path(runs[0]) / "lab-onepage.pptx")
        stop = overwrite_block(out, a.overwrite)
        if stop:
            ap.error(stop)
        build_onepage(runs, out, a.presenter or "Presenter", a.date)
        kp = ""
    rows = gates(out, kp, a.format, story)
    if a.render:
        try:
            n, stale, layout = render_png(out, out.parent / (out.stem + "-slides"))
            rows.append(("L5", "WARN" if stale else "PASS", f"PowerPoint COM rendered {n} slides to {out.stem}-slides/ — look at them (orphan wraps, overlaps, 4:3 frame)"
                         + (f"; stale PNGs from a longer earlier build: {stale[:4]}" if stale else "")))
            if a.format == "deck":
                rows.append(layout)
        except Exception as e:
            rows.append(("L5", "WARN", f"COM render unavailable ({e.__class__.__name__}: {str(e)[:80]}) — open the deck by eye; L10 not measured"))
    for g, s, m in rows:
        print(f"{g:<4}{s:<5}— {m}")
    fail = any(s == "FAIL" for _, s, _ in rows)
    print("RESULT:", "FAIL" if fail else "PASS", "|", out)
    return 2 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
