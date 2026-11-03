#!/usr/bin/env python
"""paper-distill units — the paper's text as ordered, verbatim source units with a replayable fix log.

Why (Retort & Rove card WC-06, user ruling 2026-09-27): Retort & Rove shows a paper verbatim, paragraph by
paragraph, and never parses a PDF itself. paper.txt is page text (paragraph breaks lost, ligatures and running
heads inside) and structure.json holds headings only, so the paragraphs come from here.

Writes <run>/source/units.json (schema paper-distill/units@1):
  units[]    every text line of the PDF lands in exactly one unit or one removed[] entry. A unit has
             raw (its lines, whitespace-collapsed, joined by one space; no space after a line-end hyphen)
             and text = raw with its fixes[] applied (ligature, dehyphenation). Kinds:
               body:     abstract, heading, paragraph, caption, reference_list (exactly one)
               non-body: title_block, figure_text, table_region, backmatter, note
  removed[]  running headers/footers (edge zone + the same digit-folded text on >= 3 pages) and page numbers
  figures[]  one per figures.json caption: its caption unit, crop file, gate verdict, crop rect, text units
  checks     coverage, replay, foreign text, paragraph proxies, reading order, headings vs structure.json,
             each with its controls (a control that misfires makes that check UNDET)

Reads source/paper.pdf, source/figures.json, source/crops.json (crop_all.py; the crop rects mark figure and
table regions) and source/structure.json (heading comparison). Headings come from probe.find_headings.

A run with source_kind text|jats (ingest.py --text / --jats) has no PDF, no page and no crop: its units are built from
source/paper.txt + source/structure.json + source/figures.json alone (section "text and JATS sources" below). A unit
there carries `line` (1-based, paper.txt) and lines [[n], ...] instead of a page and [page, block, line] refs, its id
is L<first line>, source has paper_txt_sha256 instead of pdf_sha256, and checks.structure_unresolved lists structure
units whose `line` does not hold their text (a hard failure). Paragraph breaks of a PLAIN text are a heuristic.

Usage:
  python units.py --run <run_dir> [--check] [--twice] [--clean-control <json list of clean paragraphs>]
  python units.py --accepted <PaperSurvey home> [--check] [--twice]
Exit: 0 ok; 1 a hard check failed or a control misfired (--check); 2 an input is missing.
"""
import argparse
import copy
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe  # noqa: E402  body_size, body_font, line_records, find_headings, BACKMATTER, fold
from crop import EDGE_ZONE  # noqa: E402  the running header/footer zone, shared with the crop band rule
from crop_all import TEXTLIKE, source_kind, unit_resolves  # noqa: E402  text|jats = a run with no PDF (ingest.py --text / --jats)

sys.stdout.reconfigure(encoding="utf-8")

SCHEMA = "paper-distill/units@1"
ALLOW = Path(__file__).resolve().parent.parent / "evals" / "units-allow.json"
BODY_KINDS = ("abstract", "heading", "paragraph", "caption", "reference_list")
WS = re.compile(r"\s+")
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
# U+00AD counts as a join hyphen too: a PDF may map its visible hyphen glyph to the soft hyphen (a PyMuPDF
# insert_text PDF in Arial does), so deleting every U+00AD would turn "III-V" into "IIIV". A mid-line U+00AD is
# kept and counted (checks.soft_hyphens); none of the 7 accepted papers has one (2026-09-27).
JOIN_HYPHENS = "-‐‑­"
SOFT_HYPHEN = "­"
PAGE_NUM = re.compile(r"^(\d{1,6}|\d+ of \d+|Page \d+( of \d+)?)$", re.I)  # IEEE Access pages run to 5 digits
LICENSE = re.compile(r"^(©|copyright\b)|licensee|creative commons", re.I)
START = re.compile(r"^(abstract\b|(1\.?\s+|i\.?\s+)?introduction$)")
REFS = re.compile(r"^(\d+\.?\s+)?(references|bibliography)\b")
# a sentence end: . ? ! : then closing quotes/brackets, optionally a bracketed citation ("shown.[12]", "shown. [3,4]")
TERMINAL = re.compile(r"(?:[.?!:][\"'”’)\]]*(?:\s*\[[\d,\s–-]+\])?|\[[\d,\s–-]+\]\.)[\"'”’)\]]*$")
FOREIGN = [re.compile(p, re.I) for p in (r"www\.", r"https?://", r"doi\.org", "©", r"^(received|accepted|published)\b",
                                          r"page \d+ of \d+", r"\bvolume \d+")]
URLISH = {0, 1, 2}  # FOREIGN indexes a reference list may contain
CLEAN = ["The propagation loss was measured with the cut-back method at 1550 nm.",
         "Figure 2a shows the cross section; the width is 1.8 um or lower.",
         "In conclusion, we have demonstrated low-loss waveguides on a 500 nm platform [12]."]
WORD = r"[^\W_]+"


# ---------- reading the PDF ----------

class Line:
    __slots__ = ("ref", "page", "bbox", "text", "ptext", "size", "font", "bold", "end_text", "x0", "idx")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def read_lines(doc):
    """Every text line with a non-whitespace span, in PyMuPDF order: (page, block, line) refs. Also the count of
    whitespace-only lines, which are skipped."""
    out, skipped = [], 0
    for pno, page in enumerate(doc, 1):
        for bno, b in enumerate(page.get_text("dict")["blocks"]):
            if b.get("type") != 0:
                continue
            for lno, ln in enumerate(b["lines"]):
                inked = [sp for sp in ln["spans"] if sp["text"].strip()]
                if not inked:
                    skipped += 1
                    continue
                size = max(sp["size"] for sp in inked)
                # a trailing superscript (citation "shown.12") is not the line's last word
                keep = len(ln["spans"])
                while keep > 1 and (not ln["spans"][keep - 1]["text"].strip() or ln["spans"][keep - 1]["size"] < 0.8 * size):
                    keep -= 1
                out.append(Line(ref=(pno, bno, lno), page=pno, bbox=tuple(ln["bbox"]),
                                text=WS.sub(" ", "".join(sp["text"] for sp in ln["spans"])).strip(),
                                ptext=WS.sub(" ", "".join(sp["text"] for sp in inked)).strip(),  # probe.line_records' text
                                size=round(size, 1), font=inked[0]["font"],
                                bold=bool(inked[0]["flags"] & 16) or "bold" in inked[0]["font"].lower(),
                                end_text=WS.sub(" ", "".join(sp["text"] for sp in ln["spans"][:keep])).strip(),
                                x0=min(sp["bbox"][0] for sp in inked), idx=len(out)))
    return out, skipped


def digit_fold(s):
    return re.sub(r"\d+", "#", probe.fold(s))


def section_id(h):
    """The structure.json unit id of a probe heading."""
    return f"§{h['num']}" if h["num"] else f"§{h['text'][:40]}"


def heading_guard(ln, block, accepted, bfont):
    """Why a probe.find_headings line is not taken as a heading unit here, or None. probe's list is kept as it is
    (structure.json); these are its false positives met on the 7 accepted papers (2026-09-27): a word fragment of a
    justified reference line (Jaiswal "experimental"), a formula line, a body line inside a paragraph."""
    if any(l is not ln and abs(l.bbox[1] - ln.bbox[1]) < 1.0 and l.x0 < ln.x0 for l in block):
        return "a later fragment of a justified line (another line of its block shares its baseline, further left)"
    if re.search("[=<>≤≥≈±×∗∝∑∫]", ln.text):
        return "contains a relation or operator sign (a formula line: 'PSW = …', Mu 2020 'Λ <')"
    if re.match(r"[a-z]", ln.text):
        return "starts with a lowercase letter (a continued line: Hong 2019 p.6 'eter (MFD) of …' after 'diam-')"
    k = block.index(ln)
    if k + 1 < len(block):
        nxt = block[k + 1]
        if nxt.font == bfont and ln.font != bfont and re.match(r"[a-z]", nxt.text) and abs(nxt.size - ln.size) < 0.3:
            return "a run-in label opening a paragraph (the next line goes on in the body font: 'Abstract: …', 'Keywords: …')"
    if k > 0:
        prev = block[k - 1]
        if prev.idx not in accepted and abs(prev.size - ln.size) < 0.3 and not ends_terminal(prev) \
                and not re.search(r"\(\d+\)$", prev.text):
            return "continues the previous line of its block (that line ends mid-sentence)"
    return None


def backmatter_start(ft):
    """A block's first line that opens back matter: a probe.BACKMATTER word as a short line ("References",
    "Acknowledgments") or as a run-in label ("Funding: This work…"). A body sentence that merely starts with
    such a word ("Supplementary Figure S1 shows the full spectra of …") does not."""
    if re.match(r"^\d+\.?\s+(references|bibliography|acknowledg)", ft):
        return True
    for b in probe.BACKMATTER:
        if ft == b or ft.startswith(b):
            return len(ft.split()) <= 6 or bool(re.match(re.escape(b) + r"[\w\s']{0,30}[:.]", ft))
    return False


def ends_terminal(line):
    return bool(TERMINAL.search(line.end_text))


def starts_lower(line):
    return line.text[:1].islower()


def inside(bbox, rect, share=0.9):
    """True when at least `share` of bbox's area lies inside rect."""
    x0, y0, x1, y1 = bbox
    area = max(x1 - x0, 0.01) * max(y1 - y0, 0.01)
    ix = max(0.0, min(x1, rect[2]) - max(x0, rect[0]))
    iy = max(0.0, min(y1, rect[3]) - max(y0, rect[1]))
    return ix * iy >= share * area


# ---------- raw text and the fix log ----------

def join_raw(lines):
    """raw = the lines joined by one space; after a line-end hyphen (letter/digit + hyphen) no space, hyphen kept.
    Returns raw and the offsets of those join hyphens."""
    raw, joins = "", []
    for ln in lines:
        t = ln.text
        if raw:
            if raw[-1] in JOIN_HYPHENS and len(raw) >= 2 and raw[-2].isalnum():
                joins.append(len(raw) - 1)
            else:
                raw += " "
        raw += t
    return raw, joins


def apply_fixes(raw, fixes):
    out, pos = [], 0
    for f in sorted(fixes, key=lambda f: f["at"][0]):
        a, b = f["at"]
        if a < pos or raw[a:b] != f["raw"]:
            raise ValueError(f"fix does not fit raw at {a}:{b}: {f}")
        out.append(raw[pos:a])
        out.append(f["fixed"])
        pos = b
    out.append(raw[pos:])
    return "".join(out)


def word_count(corpus, word):
    return len(re.findall(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", corpus, re.I))


def variants(w):
    v = {w, w + "s", w + "es"}
    if w.endswith("es"):
        v.add(w[:-2])
    if w.endswith("s"):
        v.add(w[:-1])
    return v


def dehyphenation_decisions(units, joins_by_unit):
    """For every join hyphen: remove it only when the joined word occurs elsewhere in this paper and the hyphenated
    word does not. The paper is its own dictionary; when unsure the hyphen stays (it is in the PDF text layer)."""
    corpus = "\n".join("".join(LIGATURES.get(c, c) for c in u["raw"]) for u in units)
    sites = []
    for u in units:
        for at in joins_by_unit.get(u["id"], []):
            left = re.search(WORD + r"$", u["raw"][:at])
            right = re.match(WORD, u["raw"][at + 1:])
            if left and right:
                sites.append((u["id"], at, "".join(LIGATURES.get(c, c) for c in left.group()),
                              "".join(LIGATURES.get(c, c) for c in right.group())))
    same_pair = Counter((l.lower(), r.lower()) for _, _, l, r in sites)
    remove = set()
    for uid, at, left, right in sites:
        joined, hyph = left + right, f"{left}-{right}"
        seen_joined = sum(word_count(corpus, v) for v in variants(joined))
        seen_hyph = word_count(corpus, hyph) - same_pair[(left.lower(), right.lower())] \
            + sum(word_count(corpus, v) for v in variants(hyph) - {hyph})
        if seen_joined > 0 and seen_hyph <= 0:
            remove.add((uid, at))
    return remove


def fixes_for(unit, remove):
    fixes = []
    for i, c in enumerate(unit["raw"]):
        if c in LIGATURES:
            fixes.append({"kind": "ligature", "at": [i, i + 1], "raw": c, "fixed": LIGATURES[c]})
        elif (unit["id"], i) in remove:
            fixes.append({"kind": "dehyphenation", "at": [i, i + 1], "raw": c, "fixed": ""})
    return fixes


# ---------- building the units ----------

def build(doc, captions=(), crops=()):
    lines, skipped = read_lines(doc)
    body = probe.body_size(doc)
    bfont = probe.body_font(doc)
    recs = probe.line_records(doc)
    if len(recs) != len(lines) or any(r["page"] != l.page or r["text"] != l.ptext for r, l in zip(recs, lines)):
        raise RuntimeError("probe.line_records and units.read_lines disagree on the line list")
    heads, _ = probe.find_headings(recs, body, bfont)
    by_block = defaultdict(list)
    for ln in lines:
        by_block[(ln.page, ln.ref[1])].append(ln)
    head_at, rejected = {}, []
    i = 0
    for h in heads:  # heads come in line order: match each to the next line with its page and text
        while i < len(lines) and not (lines[i].page == h["page"] and lines[i].ptext == h["text"]):
            i += 1
        if i == len(lines):
            raise RuntimeError(f"heading not found in the line list: p.{h['page']} {h['text']!r}")
        why = heading_guard(lines[i], by_block[(lines[i].page, lines[i].ref[1])], head_at, bfont)
        if why:
            rejected.append({"id": section_id(h), "line": list(lines[i].ref), "text": h["text"], "why": why})
        else:
            head_at[i] = h
        i += 1
    # a heading wrapped onto the next line of its block, in the heading's own (non-body) font
    head_cont = {}
    for i in list(head_at):
        bl = by_block[(lines[i].page, lines[i].ref[1])]
        k = bl.index(lines[i])
        cont = []
        while k + 1 < len(bl) and len(cont) < 2 and lines[i].font != bfont and not ends_terminal(bl[k]) \
                and bl[k + 1].font == lines[i].font and abs(bl[k + 1].size - lines[i].size) < 0.3 and bl[k + 1].idx not in head_at:
            cont.append(bl[k + 1].idx)
            k += 1
        if cont:
            head_cont[i] = cont

    label = {}           # line idx -> (class, group key)

    def block_bbox(bl):
        return (min(l.bbox[0] for l in bl), min(l.bbox[1] for l in bl), max(l.bbox[2] for l in bl), max(l.bbox[3] for l in bl))

    # 1. captions: the text block figures.json names (same page, same bbox within 1.5 pt; else same start text)
    cap_block = {}
    for ci, c in enumerate(captions):
        cands = [k for k in by_block if k[0] == c["page"]]
        hit = next((k for k in cands if all(abs(a - b) <= 1.5 for a, b in zip(block_bbox(by_block[k]), c["bbox"]))), None)
        if hit is None:
            start = probe.fold(c.get("caption", ""))[:24]
            hit = next((k for k in cands if start and probe.fold(" ".join(l.text for l in by_block[k])).startswith(start)), None)
        if hit is not None and hit not in cap_block:
            cap_block[hit] = ci
            for ln in by_block[hit]:
                label[ln.idx] = ("caption", ci)

    # 2. figure and table regions: blocks at least 90 % inside a crop rect
    for ri, r in enumerate(crops):
        rect = r.get("rect")
        if not rect:
            continue
        for k, bl in by_block.items():
            if k[0] == r["page"] and k not in cap_block and inside(block_bbox(bl), rect):
                for ln in bl:
                    label.setdefault(ln.idx, ("table_region" if r["kind"] == "table" else "figure_text", ri))

    # 3. running headers/footers and page numbers in the edge zone
    rects = {p.number + 1: p.rect for p in doc}

    def in_zone(ln):
        r = rects[ln.page]
        return ln.bbox[3] < r.y0 + EDGE_ZONE or ln.bbox[1] > r.y1 - EDGE_ZONE

    zone = [ln for ln in lines if in_zone(ln) and label.get(ln.idx, ("",))[0] != "caption"]
    pages_of = defaultdict(set)
    for ln in zone:
        pages_of[digit_fold(ln.text)].add(ln.page)
    removed = []
    for ln in zone:
        if ln.idx not in label and len(pages_of[digit_fold(ln.text)]) >= 3 and len(digit_fold(ln.text).replace("#", "").strip()) >= 3:
            label[ln.idx] = ("removed", "header_footer")
    pnum_taken = set()
    for ln in zone:
        # a page number is alone in its block, or shares it only with header/footer lines (Scientific Reports)
        mates = [l for l in by_block[(ln.page, ln.ref[1])] if l is not ln]
        if ln.idx not in label and PAGE_NUM.match(ln.text) and ln.page not in pnum_taken \
                and all(label.get(l.idx) == ("removed", "header_footer") for l in mates):
            label[ln.idx] = ("removed", "page_number")
            pnum_taken.add(ln.page)
    for ln in lines:
        if label.get(ln.idx, ("",))[0] == "removed":
            removed.append({"kind": label[ln.idx][1], "line": list(ln.ref), "raw": ln.text})

    # 4. title block, back matter, reference list, headings, notes, body
    start = next((ln.idx for ln in lines if ln.idx not in label and START.match(probe.fold(ln.text))), None)
    front, abstract_block = set(), None
    if start is None:
        # no "Abstract"/"Introduction" line (Scientific Reports): the front matter is page 1 before the first
        # substantial body-size block (that block is the abstract), plus page-1 blocks after it that are in neither
        # the body font nor the body size (affiliations, received/accepted dates, badges) and are not a numbered or
        # IMRaD heading
        for k in sorted((k for k in by_block if k[0] == 1), key=lambda k: by_block[k][0].idx):
            bl = [l for l in by_block[k] if l.idx not in label]
            if len(bl) >= 3 and sum(len(l.text) for l in bl) >= 250 and all(abs(l.size - body) <= 0.6 for l in bl):
                abstract_block = k
                break
        if abstract_block is not None:
            first = by_block[abstract_block][0].idx
            for k, bl in by_block.items():
                if k[0] != 1 or k == abstract_block:
                    continue
                rest = [l for l in bl if l.idx not in label]
                imrad = any(probe.fold(l.text) in probe.IMRAD or probe.NUM_HEAD.match(l.text) for l in rest if l.idx in head_at)
                if rest and (rest[0].idx < first or (not imrad and all(l.font != bfont and abs(l.size - body) > 0.3 for l in rest))):
                    front.update(l.idx for l in rest)
    first_of_block = {bl[0].idx for bl in (sorted((l for l in bl if l.idx not in label), key=lambda l: l.idx)
                                           for bl in by_block.values()) if bl}
    cont_of = {c: i for i, cs in head_cont.items() for c in cs}
    region = None  # None (body) | ("backmatter", idx) | ("reference_list", 0)
    license_block = None
    for ln in lines:
        if ln.idx in label:
            continue
        if (start is not None and ln.idx < start) or ln.idx in front:
            label[ln.idx] = ("title_block", (ln.page, ln.ref[1]))
            continue
        ft = probe.fold(ln.text)
        if ln.idx in head_at:
            region = None
            label[ln.idx] = ("heading", ln.idx)
            continue
        if ln.idx in cont_of and label.get(cont_of[ln.idx], ("",))[0] == "heading":
            label[ln.idx] = ("heading", cont_of[ln.idx])
            continue
        if ln.idx in first_of_block and LICENSE.search(ft):
            # a license notice ("© 2021 The Author(s)", "Licensee MDPI"): back matter for its own block only, and
            # outside the reading flow, so a paragraph that runs past it goes on (Zhang 2021 p.1 -> p.2)
            license_block = (ln.page, ln.ref[1])
        if license_block == (ln.page, ln.ref[1]):
            label[ln.idx] = ("license", license_block)
            continue
        if ln.idx in first_of_block and backmatter_start(ft):
            region = ("reference_list", 0) if REFS.match(ft) else ("backmatter", ln.idx)
        if region:
            label[ln.idx] = region
            continue
        label[ln.idx] = ("body", None)
    # notes: a block whose remaining body lines are all clearly smaller than the body font
    for k, bl in by_block.items():
        rest = [l for l in bl if label.get(l.idx, ("",))[0] == "body"]
        if rest and all(l.size < body - 0.9 for l in rest):
            for l in rest:
                label[l.idx] = ("note", k)

    # 5. paragraphs from the body lines
    body_lines = [ln for ln in lines if label[ln.idx][0] == "body"]
    body_blocks = []
    for ln in body_lines:
        if body_blocks and body_blocks[-1][0].page == ln.page and body_blocks[-1][0].ref[1] == ln.ref[1]:
            body_blocks[-1].append(ln)
        else:
            body_blocks.append([ln])

    ind = 0.5 * body  # a first-line indent: Bose 2024 indents 7.8 pt at a 9.8 pt body, Hong 2019 12 pt at 9 pt

    def left_edge(bl, ln):
        """The block's left edge from its lines on other baselines than ln (justified lines start there), or None."""
        xs = [l.x0 for l in bl if abs(l.bbox[1] - ln.bbox[1]) >= 1.0]
        return min(xs) if xs else None

    def indented(bl, k, prev_bl):
        """True/False: line k of block bl is / is not indented against its column edge; None if unknown."""
        e = left_edge(bl, bl[k])
        if e is None and k == 0 and prev_bl and prev_bl[-1].page == bl[0].page \
                and prev_bl[-1].bbox[0] < bl[0].bbox[2] and bl[0].bbox[0] < prev_bl[-1].bbox[2]:
            e = min(l.x0 for l in prev_bl)
        return None if e is None else bl[k].x0 - e >= ind

    def new_baseline(a, b):
        return b.page != a.page or b.bbox[3] > a.bbox[3] + 0.5 * body or b.bbox[3] < a.bbox[1]

    def at_break(a, b):
        """b is not directly below a: a page or column break (or a jump) separates them."""
        return not (b.page == a.page and a.bbox[0] < b.bbox[2] and b.bbox[0] < a.bbox[2] and 0 <= b.bbox[1] - a.bbox[3] < 3 * body)

    pos_in_block = {}
    for bl in body_blocks:
        for k, ln in enumerate(bl):
            pos_in_block[ln.idx] = (bl, k)
    flow = sorted(set(ln.idx for ln in lines if label[ln.idx][0] in ("body", "backmatter", "reference_list", "heading")))

    # is this an indent paper? count paragraph-start candidates (a new line after a sentence end, capitalised) that
    # are indented; a paper without first-line indents has almost none
    votes, prev, prev_bl = [], None, None
    for idx in flow:
        if label[idx][0] != "body":
            prev = None
            continue
        bl, k = pos_in_block[idx]
        ln = lines[idx]
        if prev is not None and ends_terminal(prev) and new_baseline(prev, ln) and ln.text[:1].isupper():
            v = indented(bl, k, prev_bl)
            if v is not None:
                votes.append(v)
        prev = ln
        if k == len(bl) - 1:
            prev_bl = bl
    trues = sum(1 for v in votes if v)
    indent_paper = trues >= 5 and trues >= 0.25 * len(votes)

    groups = []   # (kind, [lines])
    cur, prev_bl = None, None
    for idx in flow:
        cls = label[idx][0]
        ln = lines[idx]
        if cls != "body":
            if cur:
                groups.append(("paragraph", cur))
                cur = None
            continue
        bl, k = pos_in_block[idx]
        if cur is None:
            cur = [ln]
        elif k == 0:
            if not ends_terminal(cur[-1]) or starts_lower(ln):
                cur.append(ln)
            elif indent_paper and indented(bl, 0, prev_bl) is False and at_break(cur[-1], ln) \
                    and not ln.bold and ln.font == cur[-1].font:
                # a sentence that ends exactly at a column or page break: the paragraph goes on unindented there.
                # Directly below, a bold start or a font change, it is a new paragraph (an abstract followed by the
                # introduction, a run-in heading "Multilayer reflector design.", "Keywords:")
                cur.append(ln)
            else:
                groups.append(("paragraph", cur))
                cur = [ln]
        else:
            if ends_terminal(bl[k - 1]) and new_baseline(bl[k - 1], ln) and indented(bl, k, prev_bl):
                groups.append(("paragraph", cur))
                cur = [ln]
            else:
                cur.append(ln)
        if k == len(bl) - 1:
            prev_bl = bl
    if cur:
        groups.append(("paragraph", cur))

    # the other groups
    for cls in ("caption", "figure_text", "table_region", "title_block", "backmatter", "license", "note"):
        g = defaultdict(list)
        for ln in lines:
            if label[ln.idx][0] == cls:
                g[(cls, label[ln.idx][1])].append(ln)
        for key in sorted(g, key=lambda key: g[key][0].idx):
            groups.append(("backmatter" if cls == "license" else cls, g[key]))
    refs = [ln for ln in lines if label[ln.idx][0] == "reference_list"]
    if refs:
        groups.append(("reference_list", refs))
    hg = defaultdict(list)
    for ln in lines:
        if label[ln.idx][0] == "heading":
            hg[label[ln.idx][1]].append(ln)
    for key in hg:
        groups.append(("heading", hg[key]))

    groups.sort(key=lambda g: g[1][0].idx)
    units, joins_by_unit, used = [], {}, Counter()
    first_head = min((idx for idx in head_at if label[idx][0] == "heading"), default=None)
    abstract_lines = {l.idx for l in by_block[abstract_block]} if abstract_block else set()
    section, section_is_abstract = None, False
    for kind, gl in groups:
        base = f"p{gl[0].page}-y{int(gl[0].bbox[1])}-x{int(gl[0].bbox[0])}"
        used[base] += 1
        uid = base if used[base] == 1 else f"{base}-{used[base]}"
        if kind == "heading":
            h = head_at[gl[0].idx]
            section = section_id(h)
            section_is_abstract = probe.fold(h["text"]).startswith("abstract")
        if kind == "paragraph" and (section_is_abstract or gl[0].idx in abstract_lines
                                    or (first_head is not None and gl[0].idx < first_head and start is not None)):
            kind = "abstract"
        raw, joins = join_raw(gl)
        joins_by_unit[uid] = joins
        units.append({"id": uid, "kind": kind, "section": None if kind == "title_block" else section, "page": gl[0].page,
                      "lines": [list(l.ref) for l in gl], "raw": raw})
    remove = dehyphenation_decisions(units, joins_by_unit)
    for u in units:
        u["fixes"] = fixes_for(u, remove)
        u["text"] = apply_fixes(u["raw"], u["fixes"])
        # key order in the file: id, kind, section, page, lines, raw, text, fixes
        u_ordered = {k: u[k] for k in ("id", "kind", "section", "page", "lines", "raw", "text", "fixes")}
        u.clear()
        u.update(u_ordered)

    unit_of_line = {tuple(r): u["id"] for u in units for r in u["lines"]}
    figures = []
    for ci, c in enumerate(captions):
        cap_unit = next((unit_of_line[l.ref] for k, v in cap_block.items() if v == ci for l in by_block[k][:1]), None)
        crop = next((r for r in crops if r.get("caption_index") == ci), None)
        text_units = sorted({unit_of_line[l.ref] for l in lines if label[l.idx][0] in ("figure_text", "table_region")
                             and crop is not None and label[l.idx][1] == crops.index(crop)}, key=lambda s: s)
        figures.append({"label": c.get("label"), "kind": c.get("kind"), "num": c.get("num"), "page": c.get("page"),
                        "caption_unit": cap_unit, "caption_ok": c.get("caption_ok"),
                        "file": crop.get("file") if crop else None, "gate": crop.get("gate") if crop else None,
                        "rect": crop.get("rect") if crop else None, "text_units": text_units})
    title_heads = [{"id": section_id(h), "line": list(lines[i].ref), "text": h["text"], "why": "in the title block"}
                   for i, h in head_at.items() if label[i][0] == "title_block"]
    meta = {"body_font_size": body, "body_font": bfont, "indent_paper": indent_paper, "indent_votes": [trues, len(votes)],
            "front_matter": "abstract/introduction line" if start is not None else ("first substantial page-1 block" if abstract_block else "none"),
            "probe_headings_not_taken": rejected + title_heads, "skipped_whitespace_lines": skipped}
    return {"units": units, "removed": removed, "figures": figures}, lines, meta


# ---------- checks ----------

def coverage(result, lines):
    counts = Counter()
    for u in result["units"]:
        for r in u["lines"]:
            counts[tuple(r)] += 1
    for r in result["removed"]:
        counts[tuple(r["line"])] += 1
    refs = [l.ref for l in lines]
    known = set(refs)
    return {"unaccounted": [list(r) for r in refs if counts[r] == 0],
            "double": sorted([list(r) for r, c in counts.items() if c > 1]),
            "unknown": sorted([list(r) for r in counts if r not in known])}


def replay(result):
    bad = []
    for u in result["units"]:
        try:
            ok = apply_fixes(u["raw"], u["fixes"]) == u["text"]
        except ValueError:
            ok = False
        if not ok:
            bad.append(u["id"])
    return bad


def foreign(texts, removed):
    """(unit id, what matched) for foreign text inside body units: a removed header/footer text, or a pattern."""
    heads = sorted({digit_fold(r["raw"]) for r in removed if r["kind"] == "header_footer" and len(digit_fold(r["raw"])) >= 8})
    hits = []
    for uid, kind, text in texts:
        ft = digit_fold(text)
        for h in heads:
            if h in ft:
                hits.append({"unit": uid, "match": h})
        for i, rx in enumerate(FOREIGN):
            if kind == "reference_list" and i in URLISH:
                continue
            m = rx.search(text)
            if m:
                hits.append({"unit": uid, "match": m.group(0)})
    return hits


def proxies(result, by_ref):
    low, noend = [], []
    for u in result["units"]:
        if u["kind"] != "paragraph":
            continue
        if u["text"][:1].islower():
            low.append(u["id"])
        if not ends_terminal(by_ref[tuple(u["lines"][-1])]):
            noend.append(u["id"])
    return low, noend


def two_col_pages(lines, doc_width):
    """Pages with >= 3 column-wide lines in each half, and the side of every column-wide line. Only lines at least
    0.3 page widths wide count: an equation number at the right margin or a short last line is not a column."""
    side = {}
    per = defaultdict(lambda: [0, 0])
    for l in lines:
        w = doc_width[l.page]
        mid, tol = w / 2, 0.02 * w
        if l.bbox[2] - l.bbox[0] < 0.3 * w:
            continue
        if l.bbox[2] <= mid + tol:
            side[l.ref] = "L"
            per[l.page][0] += 1
        elif l.bbox[0] >= mid - tol:
            side[l.ref] = "R"
            per[l.page][1] += 1
    pages = {p for p, (a, b) in per.items() if a >= 3 and b >= 3}
    return pages, side


def order_violations(units, pages, side):
    bad = []
    for u in units:
        seen_r = set()
        for r in u["lines"]:
            r = tuple(r)
            if r[0] in pages and side.get(r) == "R":
                seen_r.add(r[0])
            elif r[0] in pages and side.get(r) == "L" and r[0] in seen_r:
                bad.append({"unit": u["id"], "why": "right-column line before a left-column line", "page": r[0]})
                break
    body = [u for u in units if u["kind"] in ("abstract", "heading", "paragraph")]
    for a, b in zip(body, body[1:]):
        ra, rb = tuple(a["lines"][0]), tuple(b["lines"][0])
        if ra[0] == rb[0] and ra[0] in pages and side.get(ra) == "R" and side.get(rb) == "L":
            bad.append({"unit": b["id"], "why": "starts in the left column after a unit that starts in the right column", "page": rb[0]})
    return bad


def load_allow(run_id):
    if not ALLOW.is_file():
        return []
    return json.loads(ALLOW.read_text(encoding="utf-8")).get("foreign", {}).get(run_id, [])


def foreign_checks(result, run_id):
    """(hits with their allow-list class, the body texts they were searched in)."""
    body_texts = [(u["id"], u["kind"], u["text"]) for u in result["units"] if u["kind"] in BODY_KINDS]
    hits = foreign(body_texts, result["removed"])
    allow = load_allow(run_id)
    for h in hits:
        a = next((a for a in allow if a["unit"] == h["unit"] and a["match"] == h["match"]), None)
        h["class"] = a["reason"] if a else None
    return hits, body_texts


def heading_checks(result, structure):
    """structure.json's headings, minus the ones units.py did not take (each listed with its reason), must be exactly
    the heading units, in order."""
    out = {}
    want = [u["id"] for u in structure.get("units", []) if u.get("kind") in ("section", "subsection")]
    not_taken = [x["id"] for x in result.get("source", {}).get("probe_headings_not_taken", [])]
    for sid in not_taken:
        if sid in want:
            want.remove(sid)
    got = [u["section"] for u in result["units"] if u["kind"] == "heading"]
    out["headings_match"] = want == got
    out["headings_not_taken"] = len(not_taken)
    if want != got:
        out["headings_diff"] = {"structure_only": [w for w in want if w not in got], "units_only": [g for g in got if g not in want]}
    return out


def check(result, lines, widths, structure=None, clean=None, run_id=""):
    by_ref = {l.ref: l for l in lines}
    out = {}
    cov = coverage(result, lines)
    out.update(cov)
    out["replay_mismatch"] = replay(result)
    hits, body_texts = foreign_checks(result, run_id)
    out["foreign_hits"] = hits
    out["lowercase_start"], out["no_terminal_end"] = proxies(result, by_ref)
    pages, side = two_col_pages(lines, widths)
    out["two_column_pages"] = sorted(pages)
    out["order"] = order_violations(result["units"], pages, side)
    if structure is not None:
        out.update(heading_checks(result, structure))
    cap_chars = lambda kind: sum(len(u["text"]) for u in result["units"] if u["kind"] == kind)
    out["chars"] = {k: cap_chars(k) for k in ("title_block", "note", "figure_text", "table_region", "backmatter")}
    out["figure_text_suspect"] = [u["id"] for u in result["units"] if u["kind"] in ("figure_text", "table_region")
                                  and any(len(by_ref[tuple(r)].text) >= 60 for r in u["lines"])]
    out["soft_hyphens"] = [u["id"] for u in result["units"] if SOFT_HYPHEN in u["text"]]
    controls = base_controls(result, lines, body_texts, by_ref, clean)
    if pages:
        p = min(pages)
        lft = next(l.ref for l in lines if l.page == p and side.get(l.ref) == "L")
        rgt = next(l.ref for l in lines if l.page == p and side.get(l.ref) == "R")
        fired = bool(order_violations([{"id": "x", "kind": "note", "lines": [list(rgt), list(lft)]}], pages, side))
        silent = not order_violations([{"id": "y", "kind": "note", "lines": [list(lft), list(rgt)]}], pages, side)
        controls["order"] = "ok" if fired and silent else "MISFIRE"
    else:
        controls["order"] = "n/a: no two-column page"
    out["controls"] = controls
    return out


def base_controls(result, lines, body_texts, by_ref, clean):
    """The controls every source kind shares (coverage, replay, foreign, proxies): each check must fire on a known-bad
    copy and stay silent on the known-good input."""
    controls = {}
    multi = next((u for u in result["units"] if len(u["lines"]) >= 2), None)
    if multi is None:
        controls["coverage"] = "UNDET: no unit with 2+ lines"
    else:
        bad = copy.deepcopy(result)
        victim = next(u for u in bad["units"] if u["id"] == multi["id"])
        dropped = victim["lines"].pop()
        fired = dropped in coverage(bad, lines)["unaccounted"]
        controls["coverage"] = "ok" if fired else "MISFIRE: a dropped line was not reported"
    with_fix = next((u for u in result["units"] if u["fixes"]), None)
    probe_unit = copy.deepcopy(with_fix) if with_fix else {"id": "synthetic", "raw": "ﬁ", "text": "fi",
                                                           "fixes": [{"kind": "ligature", "at": [0, 1], "raw": "ﬁ", "fixed": "fi"}]}
    good_ok = not replay({"units": [probe_unit]})
    probe_unit["fixes"] = probe_unit["fixes"][1:]
    controls["replay"] = "ok" if good_ok and replay({"units": [probe_unit]}) else "MISFIRE"
    heads = [r["raw"] for r in result["removed"] if r["kind"] == "header_footer" and len(digit_fold(r["raw"])) >= 8]
    insert = Counter(heads).most_common(1)[0][0] if heads else "see www.example.org"
    target = next((t for t in body_texts if t[1] == "paragraph"), ("synthetic", "paragraph", "A clean sentence."))
    pos_fired = bool(foreign([(target[0], "paragraph", target[2][:40] + " " + insert + " " + target[2][40:])], result["removed"]))
    clean_texts = clean if clean is not None else CLEAN
    neg_hits = foreign([(f"clean{i}", "paragraph", t) for i, t in enumerate(clean_texts)], result["removed"])
    controls["foreign"] = "ok" if pos_fired and not neg_hits else f"MISFIRE: positive fired={pos_fired}, clean hits={neg_hits[:3]}"
    controls["proxies"] = proxy_control(result, by_ref)
    return controls


def proxy_control(result, by_ref):
    """Split a paragraph that both proxies pass mid-sentence: both must fire on the parts."""
    for u in result["units"]:
        if u["kind"] != "paragraph" or u["text"][:1].islower() or not ends_terminal(by_ref[tuple(u["lines"][-1])]):
            continue
        m = re.search(r"[a-z]{3,} (?=[a-z]{3,})", u["text"][len(u["text"]) // 3:])
        if not m:
            continue
        cut = len(u["text"]) // 3 + m.end()
        a, b = u["text"][:cut].rstrip(), u["text"][cut:]
        low = b[:1].islower()
        noend = not TERMINAL.search(a)
        return "ok" if low and noend else f"MISFIRE: lowercase={low} no_end={noend}"
    return "UNDET: no well-formed paragraph to split"


def hard_failures(checks):
    fails = []
    for k in ("unaccounted", "double", "unknown", "replay_mismatch", "order", "structure_unresolved"):
        if checks.get(k):
            fails.append(f"{k}: {len(checks[k])}")
    if checks.get("headings_match") is False:
        fails.append(f"headings differ from structure.json: {checks.get('headings_diff')}")
    unclassified = [h for h in checks.get("foreign_hits", []) if not h.get("class")]
    if unclassified:
        fails.append(f"foreign_unclassified: {len(unclassified)}")
    for k, v in checks.get("controls", {}).items():
        if not (v == "ok" or v.startswith("n/a")):
            fails.append(f"control {k}: {v}")
    return fails


# ---------- text and JATS sources (no PDF) ----------
# A run made with ingest.py --text / --jats has source/paper.txt (the text itself, or JATS flattened: one line per
# paragraph) and source/structure.json (units with a 1-based `line` of paper.txt instead of a `page`). Its units are
# built from those two files only: no page, no geometry, no crop rect. Every non-blank line of paper.txt lands in
# exactly one unit or one removed[] entry (the same coverage check as a PDF), a unit's `lines` are [[n], ...] (line
# numbers of paper.txt) and its id is L<first line>. What the PDF path reads from geometry is replaced by:
#   headings    structure.json section/subsection units (a unit whose `line` does not hold its text is listed in
#               checks.structure_unresolved and fails --check)
#   captions    figures.json captions: the line they start on, extended over the lines whose joined text is the caption
#   paragraphs  JATS: one line = one paragraph (textsrc wrote it so). Plain text: HEURISTIC, a line that ends a sentence
#               and either is shorter than SHORT x the median line width or is followed by a blank line ends the paragraph
#   removed     a line that occurs >= 3 times (digits folded) with >= TEXT_HEADER_MIN letters: a running head
#   figure_text a run of >= 3 consecutive numeric fragments (axis ticks copied out of a figure), plain text only
TEXT_HEADER_MIN = 12   # letters; the PDF rule also has the edge zone, a text has no geometry, so the floor is stricter
SHORT = 0.75
NUMERIC_FRAGMENT = re.compile(r"^[\d.,;:+\-–−~×*()%/\s]{1,12}$")


def text_lines(raw_text):
    """The non-blank lines of paper.txt as Line objects (ref = (n,), n = the 1-based line number) and the blank count."""
    out, skipped = [], 0
    for n, s in enumerate(raw_text.splitlines(), 1):
        t = WS.sub(" ", s).strip()
        if not t:
            skipped += 1
            continue
        out.append(Line(ref=(n,), page=None, bbox=None, text=t, ptext=t, size=0.0, font="", bold=False, end_text=t,
                        x0=0.0, idx=len(out)))
    return out, skipped


def structure_heads(structure, by_n):
    """({line number: unit id}, [unit ids that do not resolve]) for structure.json's section/subsection units. A unit
    resolves when the line it names holds its text (or, in a plain text, is the heading textsrc reads that title from)."""
    heads, bad = {}, []
    for u in structure.get("units", []):
        if u.get("kind") not in ("section", "subsection"):
            continue
        ln = by_n.get(u.get("line"))
        if ln is not None and unit_resolves(u, ln.text):
            heads[ln.ref[0]] = u["id"]
        else:
            bad.append(u["id"])
    return heads, bad


def caption_extent(c, by_n):
    """Line numbers of a figures.json caption: from its `line` over the consecutive lines whose joined text is the
    caption (JATS: the one line). [] when its first line does not hold the caption's start."""
    n, cur, acc = c.get("line"), "", []
    target = " ".join((c.get("caption") or "").split())
    while n in by_n:
        cand = (cur + " " + by_n[n].text).strip()
        if not target.startswith(cand):
            break
        acc.append(n)
        cur = cand
        if cur == target:
            break
        n += 1
    return acc


def build_text(raw_text, structure, captions, kind):
    lines, skipped = text_lines(raw_text)
    by_n = {l.ref[0]: l for l in lines}
    heads, unresolved = structure_heads(structure, by_n)
    label = {}   # line idx -> (class, key)
    for n in heads:
        label[by_n[n].idx] = ("heading", n)
    extents = {}
    for ci, c in enumerate(captions):
        ext = caption_extent(c, by_n)
        if not ext:
            unresolved.append(f"{c.get('label')}@line{c.get('line')}")
            continue
        extents[ci] = ext
        for n in ext:
            label.setdefault(by_n[n].idx, ("caption", ci))
        if kind == "jats" and c.get("kind") == "table":    # <table-wrap> rows follow their caption, cells joined by " | "
            n = ext[-1] + 1
            while n in by_n and " | " in by_n[n].text and by_n[n].idx not in label:
                label[by_n[n].idx] = ("table_region", ci)
                n += 1
    folds = Counter(digit_fold(l.text) for l in lines)
    for ln in lines:      # running heads
        f = digit_fold(ln.text)
        if ln.idx not in label and folds[f] >= 3 and len(re.sub(r"[\W\d_]", "", f)) >= TEXT_HEADER_MIN:
            label[ln.idx] = ("removed", "header_footer")
    removed = [{"kind": "header_footer", "line": [l.ref[0]], "raw": l.text} for l in lines if label.get(l.idx, ("",))[0] == "removed"]

    start = min(heads) if heads else None   # front matter: everything before the first heading unit
    region, prev = None, None
    for ln in lines:
        if ln.idx in label:
            if label[ln.idx][0] == "heading":
                region = None
            if label[ln.idx][0] != "removed":
                prev = ln
            continue
        if start is not None and ln.ref[0] < start:
            label[ln.idx] = ("title_block", 0)
            continue
        first = kind == "jats" or prev is None or prev.ref[0] < ln.ref[0] - 1 \
            or label.get(prev.idx, ("",))[0] in ("heading", "caption", "table_region") or ends_terminal(prev)
        prev = ln
        ft = probe.fold(ln.text)
        if first and backmatter_start(ft):
            region = ("reference_list", 0) if REFS.match(ft) else ("backmatter", ln.idx)
        label[ln.idx] = region if region else ("body", None)
    if kind == "text":    # runs of numeric fragments inside the body: axis ticks copied out of a figure
        i = 0
        while i < len(lines):
            j = i
            while j < len(lines) and label[lines[j].idx][0] == "body" and NUMERIC_FRAGMENT.match(lines[j].text):
                j += 1
            if j - i >= 3:
                for k in range(i, j):
                    label[lines[k].idx] = ("figure_text", lines[i].idx)
            i = max(j, i + 1)

    body = [l for l in lines if label[l.idx][0] == "body"]
    width = statistics.median([len(l.text) for l in body]) if body else 0
    groups, cur = [], None
    for ln in lines:
        cls = label[ln.idx][0]
        if cls not in ("body", "backmatter", "reference_list", "heading"):
            continue
        if cls != "body":
            if cur:
                groups.append(("paragraph", cur))
                cur = None
            continue
        if cur is None:
            cur = [ln]
        elif kind == "jats":
            groups.append(("paragraph", cur))
            cur = [ln]
        else:
            last = cur[-1]
            blank_between = any(n not in by_n for n in range(last.ref[0] + 1, ln.ref[0]))
            if ends_terminal(last) and not starts_lower(ln) and (len(last.text) < SHORT * width or blank_between):
                groups.append(("paragraph", cur))
                cur = [ln]
            else:
                cur.append(ln)
    if cur:
        groups.append(("paragraph", cur))
    for cls in ("caption", "figure_text", "table_region", "title_block", "backmatter"):
        g = defaultdict(list)
        for ln in lines:
            if label[ln.idx][0] == cls:
                g[(cls, label[ln.idx][1])].append(ln)
        for key in sorted(g, key=lambda key: g[key][0].idx):
            groups.append((cls, g[key]))
    refs = [ln for ln in lines if label[ln.idx][0] == "reference_list"]
    if refs:
        groups.append(("reference_list", refs))
    for ln in lines:
        if label[ln.idx][0] == "heading":
            groups.append(("heading", [ln]))
    groups.sort(key=lambda g: g[1][0].idx)

    units, joins_by_unit, section = [], {}, None
    for gkind, gl in groups:
        uid = f"L{gl[0].ref[0]}"
        if gkind == "heading":
            section = heads[gl[0].ref[0]]
        if gkind == "paragraph" and section == "§0":
            gkind = "abstract"
        raw, joins = join_raw(gl)
        joins_by_unit[uid] = joins
        units.append({"id": uid, "kind": gkind, "section": None if gkind == "title_block" else section, "page": None,
                      "line": gl[0].ref[0], "lines": [[l.ref[0]] for l in gl], "raw": raw})
    remove = dehyphenation_decisions(units, joins_by_unit)
    for u in units:
        u["fixes"] = fixes_for(u, remove)
        u["text"] = apply_fixes(u["raw"], u["fixes"])
        ordered = {k: u[k] for k in ("id", "kind", "section", "page", "line", "lines", "raw", "text", "fixes")}
        u.clear()
        u.update(ordered)

    unit_of_line = {r[0]: u["id"] for u in units for r in u["lines"]}
    figures = []
    for ci, c in enumerate(captions):
        ext = extents.get(ci)
        text_units = sorted({unit_of_line[l.ref[0]] for l in lines if label[l.idx][0] == "table_region" and label[l.idx][1] == ci})
        figures.append({"label": c.get("label"), "kind": c.get("kind"), "num": c.get("num"), "page": None, "line": c.get("line"),
                        "caption_unit": unit_of_line[ext[0]] if ext else None, "caption_ok": c.get("caption_ok"),
                        "file": None, "gate": None, "rect": None, "text_units": text_units})
    meta = {"source_kind": kind,
            "paragraphs": "one paper.txt line each (JATS)" if kind == "jats"
            else f"heuristic: a sentence-ending line shorter than {SHORT} x the median width ({width}) or before a blank line",
            "front_matter": "lines before the first structure.json heading" if start is not None else "none",
            "header_footer_rule": f"line occurring >= 3 times (digits folded) with >= {TEXT_HEADER_MIN} letters",
            "skipped_blank_lines": skipped}
    return {"units": units, "removed": removed, "figures": figures}, lines, meta, unresolved


def structure_control(structure, by_n):
    """A heading unit whose line does not hold its text must be reported; one that does must not."""
    good = next((u for u in structure.get("units", []) if u.get("kind") in ("section", "subsection")
                 and not structure_heads({"units": [u]}, by_n)[1]), None)
    if good is None:
        return "n/a: no structure.json heading unit resolves to a line of paper.txt"
    bad = copy.deepcopy(good)
    bad["line"] = max(by_n) + 1000
    reported = structure_heads({"units": [bad]}, by_n)[1] == [good["id"]]
    silent = structure_heads({"units": [good]}, by_n)[1] == []
    return "ok" if reported and silent else f"MISFIRE: bad line reported={reported}, good line silent={silent}"


def check_text(result, lines, structure, unresolved, clean=None, run_id=""):
    by_ref = {l.ref: l for l in lines}
    out = {}
    out.update(coverage(result, lines))
    out["replay_mismatch"] = replay(result)
    hits, body_texts = foreign_checks(result, run_id)
    out["foreign_hits"] = hits
    out["lowercase_start"], out["no_terminal_end"] = proxies(result, by_ref)
    out["two_column_pages"] = []
    out["order"] = []
    out["structure_unresolved"] = unresolved
    if structure is not None:
        out.update(heading_checks(result, structure))
    cap_chars = lambda kind: sum(len(u["text"]) for u in result["units"] if u["kind"] == kind)
    out["chars"] = {k: cap_chars(k) for k in ("title_block", "note", "figure_text", "table_region", "backmatter")}
    out["figure_text_suspect"] = []
    out["soft_hyphens"] = [u["id"] for u in result["units"] if SOFT_HYPHEN in u["text"]]
    controls = base_controls(result, lines, body_texts, by_ref, clean)
    controls["order"] = "n/a: a text source has no page geometry"
    controls["structure"] = structure_control(structure or {}, {l.ref[0]: l for l in lines})
    out["controls"] = controls
    return out


def extract_text(paper_txt, kind, captions=(), structure=None, clean=None, run_id=""):
    data = Path(paper_txt).read_bytes()
    raw = data.decode("utf-8-sig")
    structure = structure or {}
    result, lines, meta, unresolved = build_text(raw, structure, list(captions), kind)
    head = {"schema": SCHEMA, "source": {"paper_txt_sha256": hashlib.sha256(data).hexdigest(), "lines": len(raw.splitlines()), **meta}}
    out = {**head, **result}
    out["checks"] = {"lines_total": len(lines), "lines_in_units": sum(len(u["lines"]) for u in result["units"]),
                     "lines_removed": len(result["removed"]),
                     **check_text(out, lines, structure, unresolved, clean, run_id)}
    return out


# ---------- files ----------

def serialize(result):
    return (json.dumps(result, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def extract(pdf, captions=(), crops=(), structure=None, clean=None, run_id=""):
    doc = fitz.open(str(pdf))
    result, lines, meta = build(doc, captions, crops)
    widths = {p.number + 1: p.rect.width for p in doc}
    pages = doc.page_count
    doc.close()
    head = {"schema": SCHEMA,
            "source": {"pdf_sha256": hashlib.sha256(Path(pdf).read_bytes()).hexdigest(), "pages": pages,
                       "pymupdf": fitz.VersionBind, **meta}}
    out = {**head, **result}
    out["checks"] = {"lines_total": len(lines), "lines_in_units": sum(len(u["lines"]) for u in result["units"]),
                     "lines_removed": len(result["removed"]),
                     **check(out, lines, widths, structure, clean, run_id)}
    return out


def crop_regions(crops_doc, captions):
    """crops.json results -> [{page, kind, rect, file, gate, caption_index}] (only crops with a rect)."""
    out = []
    for r in crops_doc.get("results", []):
        res = r.get("result") or {}
        ci = next((i for i, c in enumerate(captions) if c.get("label") == r.get("label") and c.get("page") == r.get("page")), None)
        # the page the crop landed on: a caption list's entry (Kumar 2022, "Figure 2:" on p.11) is cut from the page its
        # figure is on (p.13), and the rect belongs to that page. Equal to the target's page on every accepted run.
        out.append({"page": res.get("page") or r.get("page"), "kind": r.get("kind"), "rect": res.get("rect_pt"), "file": r.get("file"),
                    "gate": (res.get("gate") or {}).get("verdict") or ("ERROR" if r.get("exit") not in (0, 2, 3) else None),
                    "caption_index": ci})
    return out


def run_one_text(run, kind, want_check, twice, clean):
    src = run / "source"
    txt_p, figs_p, struct_p = src / "paper.txt", src / "figures.json", src / "structure.json"
    if not txt_p.is_file():
        return {"run": run.name, "error": "no source/paper.txt"}, 2
    if not struct_p.is_file():
        return {"run": run.name, "error": "no source/structure.json: a text/JATS run gets it from ingest.py"}, 2
    captions = json.loads(figs_p.read_text(encoding="utf-8")).get("captions", []) if figs_p.is_file() else []
    structure = json.loads(struct_p.read_text(encoding="utf-8"))
    result = extract_text(txt_p, kind, captions, structure, clean, run.name)
    data = serialize(result)
    summary = {"run": run.name, "source_kind": kind}
    if twice:
        summary["G_identical"] = serialize(extract_text(txt_p, kind, captions, structure, clean, run.name)) == data
    (src / "units.json").write_bytes(data)
    ch = result["checks"]
    kinds = Counter(u["kind"] for u in result["units"])
    summary.update({"units": len(result["units"]), "by_kind": dict(sorted(kinds.items())),
                    "fixes": dict(Counter(f["kind"] for u in result["units"] for f in u["fixes"])),
                    "removed": dict(Counter(r["kind"] for r in result["removed"])),
                    "lines": [ch["lines_total"], ch["lines_in_units"], ch["lines_removed"]],
                    "foreign": [len(ch["foreign_hits"]), sum(1 for h in ch["foreign_hits"] if not h["class"])],
                    "lowercase_start": len(ch["lowercase_start"]), "no_terminal_end": len(ch["no_terminal_end"]),
                    "headings_match": ch.get("headings_match"), "structure_unresolved": ch["structure_unresolved"],
                    "front_matter": result["source"]["front_matter"], "chars": ch["chars"], "controls": ch["controls"]})
    fails = hard_failures(ch)
    if twice and not summary["G_identical"]:
        fails.append("G: two runs differ")
    summary["hard_failures"] = fails
    return summary, (1 if (want_check and fails) else 0)


def run_one(run, want_check, twice, clean):
    kind = source_kind(run)
    if kind in TEXTLIKE:
        return run_one_text(run, kind, want_check, twice, clean)
    src = run / "source"
    pdf, figs_p, crops_p, struct_p = src / "paper.pdf", src / "figures.json", src / "crops.json", src / "structure.json"
    if not pdf.is_file():
        return {"run": run.name, "error": "no source/paper.pdf"}, 2
    if not crops_p.is_file():
        return {"run": run.name, "error": "no source/crops.json: run crop_all.py --apply first"}, 2
    captions = json.loads(figs_p.read_text(encoding="utf-8")).get("captions", []) if figs_p.is_file() else []
    crops = crop_regions(json.loads(crops_p.read_text(encoding="utf-8")), captions)
    structure = json.loads(struct_p.read_text(encoding="utf-8")) if struct_p.is_file() else None
    result = extract(pdf, captions, crops, structure, clean, run.name)
    data = serialize(result)
    summary = {"run": run.name}
    if twice:
        summary["G_identical"] = serialize(extract(pdf, captions, crops, structure, clean, run.name)) == data
    (src / "units.json").write_bytes(data)
    ch = result["checks"]
    kinds = Counter(u["kind"] for u in result["units"])
    summary.update({"units": len(result["units"]), "by_kind": dict(sorted(kinds.items())),
                    "fixes": dict(Counter(f["kind"] for u in result["units"] for f in u["fixes"])),
                    "removed": dict(Counter(r["kind"] for r in result["removed"])),
                    "lines": [ch["lines_total"], ch["lines_in_units"], ch["lines_removed"]],
                    "indent_paper": result["source"]["indent_paper"],
                    "foreign": [len(ch["foreign_hits"]), sum(1 for h in ch["foreign_hits"] if not h["class"])],
                    "lowercase_start": len(ch["lowercase_start"]), "no_terminal_end": len(ch["no_terminal_end"]),
                    "order": len(ch["order"]), "headings_match": ch.get("headings_match"),
                    "headings_not_taken": ch.get("headings_not_taken"), "front_matter": result["source"]["front_matter"],
                    "indent_votes": result["source"]["indent_votes"], "chars": ch["chars"],
                    "figure_text_suspect": len(ch["figure_text_suspect"]), "controls": ch["controls"]})
    fails = hard_failures(ch)
    if twice and not summary["G_identical"]:
        fails.append("G: two runs differ")
    summary["hard_failures"] = fails
    return summary, (1 if (want_check and fails) else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--accepted", type=Path, help="PaperSurvey home: every index.json entry with kind == accepted")
    ap.add_argument("--check", action="store_true", help="exit 1 on a hard check failure or a misfiring control")
    ap.add_argument("--twice", action="store_true", help="extract twice and compare the bytes")
    ap.add_argument("--clean-control", type=Path, help="JSON list of known-clean paragraphs for the foreign-text control")
    a = ap.parse_args(argv)
    clean = json.loads(a.clean_control.read_text(encoding="utf-8")) if a.clean_control else None
    if a.accepted:
        index = json.loads((a.accepted / "index.json").read_text(encoding="utf-8"))
        runs = [a.accepted / e["run_id"] for e in index.get("entries", []) if e.get("kind") == "accepted"]
    elif a.run:
        runs = [a.run]
    else:
        ap.error("give --run or --accepted")
    worst = 0
    for run in runs:
        summary, code = run_one(run, a.check, a.twice, clean)
        print(json.dumps(summary, ensure_ascii=False))
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    sys.exit(main())
