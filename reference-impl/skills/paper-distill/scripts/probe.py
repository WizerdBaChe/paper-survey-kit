#!/usr/bin/env python
"""paper-distill probe — structure facts and anomalies of an ingested paper, as INPUT to the reader.

Why (user ruling 2026-09-03): 看錯 and 漏看 are the same severity as 亂掰. A reader cannot be
trusted to notice a duplicated section number or an uncited figure by attention alone; the
tells that are determinable from the bytes are extracted here and handed to the reading as a
list the reader must classify (paper-story S11/S12, paper-distill Stage 1 skeleton).

Writes <run>/source/structure.json:
  units[]      what a reading must cover or explicitly skip: sections (headings found by font
               size, numbered or not), figures and tables (from figures.json captions)
  subheadings  bold same-size headings — informational, not coverage units
  anomalies[]  duplicate section number / duplicate heading text; figure or table never
               referenced in the body; body reference to a figure with no caption; a number in
               the abstract that appears nowhere in the body
  abstract     the span used for the number check
Heading noise (G7, 2026-11-03: 45 "units" on a preprint, 22 of them figure axis / legend text, equation fragments and
footnote marks read as headings): a font-based heading candidate is dropped when its line lies inside a figure's bounding
box (image rects and vector-drawing clusters, `figure_boxes`) or is an axis/legend-like token (`axis_like`: units, panel
letters, bare numbers, symbols, "Label (unit)", equation fragments, footnote marks). A numbered or IMRaD heading is
never dropped by these two rules. `--selftest` runs a known-noise and a known-heading control through `axis_like`.

A run with source_kind text|jats (ingest.py --text / --jats) has no PDF: probe keeps the section units ingest wrote into
structure.json (their ids are the locators §N) and recomputes the figure units and the determinable anomalies from
figures.json and paper.txt.
Usage: python probe.py --run <run_dir> [--print]        exit 0 always (it is an input, not a gate)
       python probe.py --selftest                       exit 2 when a control misfires
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HEAD_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.+)$")
SKIP = re.compile(r"^(fig\.?|figure|table|eq\.?|equation|scheme)\b|^(?:[A-Za-z]\s){3,}[A-Za-z]$|^\W*$|^\d+$", re.I)
REF_RE = re.compile(r"\b(Fig|Figure|Table|Tab)s?\.?\s*(\d{1,2})", re.I)
NUM_UNIT = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(%|dB\s*m[-−]?1|dB/m|dB|nm|µm|μm|um|mm|cm|MHz|GHz|kHz|Hz|THz|°C|K\b|million|mW|W\b|mA|A\b|V\b|ps|fs|ns|µs|ms|s\b|×|x)", re.I)


def fold(s):
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return re.sub(r"\s+", " ", s).strip()


def body_size(doc):
    c = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln.get("spans", []):
                    t = sp["text"].strip()
                    if t:
                        c[round(sp["size"], 1)] += len(t)
    return c.most_common(1)[0][0] if c else 10.0


def body_font(doc):
    """The most common font resource name — Nature-style subsection headings differ only by font, not by flag."""
    c = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln.get("spans", []):
                    t = sp["text"].strip()
                    if t:
                        c[sp["font"]] += len(t)
    return c.most_common(1)[0][0] if c else ""


FIG_PAD = 6.0          # pt: a line this close to a figure's drawing cluster / image is inside the figure
FIG_MIN_AREA = 2500.0  # pt^2: smaller clusters are rules, bullets or underlines, not figures
FIG_MAX_SHARE = 0.6    # of the page: a box this big is a page background or a scan, never one figure
MATH_ALNUM = re.compile("[\U0001D400-\U0001D7FF]")


def figure_boxes(page):
    """Rects (pt) of what is painted as a figure on a page: embedded raster images and vector-drawing clusters
    (PyMuPDF `cluster_drawings`), each padded by FIG_PAD. Page-sized boxes and tiny clusters are ignored."""
    import fitz  # PyMuPDF
    page_area = page.rect.width * page.rect.height
    rects = []
    try:
        rects += [fitz.Rect(i["bbox"]) for i in page.get_image_info()]
        rects += list(page.cluster_drawings())
    except Exception:       # a page whose drawings cannot be read has no figure boxes; the token rule still applies
        return []
    keep = [r + (-FIG_PAD, -FIG_PAD, FIG_PAD, FIG_PAD) for r in rects
            if FIG_MIN_AREA <= r.width * r.height <= FIG_MAX_SHARE * page_area]
    return keep


def in_boxes(bbox, boxes):
    """True when the line's centre lies inside one of the boxes."""
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return any(b.x0 <= cx <= b.x1 and b.y0 <= cy <= b.y1 for b in boxes)


def axis_like(t):
    """Why a short line is figure/equation furniture and not a heading (a reason string), else None. Applied only to
    font-based heading candidates — never to a numbered or IMRaD heading."""
    s = t.strip()
    if not s:
        return "empty"
    if MATH_ALNUM.search(s):
        return "math-fragment"
    if s[0] in "*†‡":
        return "footnote-mark"
    if s[0] in ")]}−-+±=":
        return "fragment"
    if re.search(r"\(\d+\)$", s):
        return "equation-number"
    if s.count("(") != s.count(")") or s.count("[") != s.count("]"):
        return "unbalanced-bracket"
    if len(s.split()) <= 4 and re.search(r"\(\s*[^()\s][^()]{0,13}\)\s*$", s):
        return "label-unit"          # "Intensity (a.u.)", "Temperature (K)", "H (Tesla)"
    if s.isascii() and not re.search(r"[A-Za-z]{4,}", s):
        return "no-word"             # "5 nm", "(a)", "Bi2Se3", "MR %", "K"
    return None


def line_records(doc):
    """Every text line with its max span size, bold flag, page, bbox, and whether it lies inside a figure's box."""
    out = []
    for pno, page in enumerate(doc, 1):
        boxes = figure_boxes(page)
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                spans = [sp for sp in ln.get("spans", []) if sp["text"].strip()]
                if not spans:
                    continue
                text = re.sub(r"\s+", " ", "".join(sp["text"] for sp in spans)).strip()
                size = max(sp["size"] for sp in spans)
                bold = all(("bold" in sp["font"].lower()) or sp["font"].endswith(".B") or (sp["flags"] & 16) for sp in spans)
                italic = all((sp["flags"] & 2) or ("italic" in sp["font"].lower()) for sp in spans)
                bbox = [min(sp["bbox"][0] for sp in spans), min(sp["bbox"][1] for sp in spans),
                        max(sp["bbox"][2] for sp in spans), max(sp["bbox"][3] for sp in spans)]
                out.append({"page": pno, "text": text, "size": round(size, 1), "bold": bold, "italic": italic, "font": spans[0]["font"],
                            "bbox": [round(v, 1) for v in bbox], "in_fig": in_boxes(bbox, boxes)})
    return out


IMRAD = {"abstract", "introduction", "background", "related work", "theory", "methods", "method", "materials and methods",
         "experimental", "experimental section", "experiments", "experiment", "results", "results and discussion",
         "results and discussions", "discussion", "discussions", "conclusion", "conclusions", "summary", "outlook",
         "summary and outlook", "appendix"}
BACKMATTER = ("references", "bibliography", "acknowledg", "funding", "author contribution", "competing interest",
              "conflict of interest", "conflicts of interest", "data availability", "supplementary", "disclosures",
              "declaration", "ethics", "orcid", "publisher's note", "additional information", "author information")
NUM_HEAD = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{1,110})$")


def find_headings(lines, body, bfont="", skip_title=True):
    """Headings = the coverage units. Numbering is the signal for numbered ones (Ow 2010's italic '3.2'
    subsections carry no bold flag); IMRaD words, large or bold lines, and — Nature style — short lines in
    a font resource other than the body's, for unnumbered ones. The title block (before
    Abstract/Introduction) is not a unit. The back matter suppresses only font-based candidates: Optics
    Express prints the reference list BEFORE the body, so a numbered or IMRaD heading ends the block."""
    heads = []
    running = Counter(fold(l["text"]) for l in lines)  # running heads repeat on many pages
    in_refs, seen_start = False, not skip_title
    for l in lines:
        t = l["text"]
        ft = fold(t)
        if len(t) < 3 or len(t) > 120 or SKIP.match(t) or running[ft] > 3:
            continue
        if not seen_start:
            if ft.startswith("abstract") or re.match(r"^(1\.?\s+|i\.?\s+)?introduction$", ft):
                seen_start = True
            else:
                continue
        if any(ft == b or ft.startswith(b) for b in BACKMATTER) or re.match(r"^\d+\.?\s+(references|bibliography|acknowledg)", ft):
            in_refs = True
            continue
        words = len(t.split())
        big = l["size"] >= body + 1.0
        m = NUM_HEAD.match(t)
        rest = m.group(2) if m else ""
        numbered_ok = bool(m) and words <= 10 and not t.endswith((".", ",", ";", ":", "-")) and re.search(r"[A-Za-z]{4,}", rest) \
            and not re.search(r"[,;:()]|\.\s", rest) and ("." in m.group(1) or re.match(r"^\d+\.\s", t))  # "3.2 Title" or "1. Title"; never "36 Hz integral…"
        imrad = ft.rstrip(":") in IMRAD and (big or l["bold"] or words <= 3)   # "Introduction:" (Kumar 2022, 2026-11-03)
        if numbered_ok or imrad:
            in_refs = False  # a body heading after a reference block (Optics Express layout)
        if numbered_ok:
            heads.append({"page": l["page"], "text": t, "num": m.group(1), "size": l["size"],
                          "kind": "section" if "." not in m.group(1) else "subsection"})
            continue
        if imrad:
            heads.append({"page": l["page"], "text": t, "num": None, "size": l["size"], "kind": "section"})
            continue
        if l.get("in_fig") or axis_like(t):   # figure axis / legend text, equation fragment, footnote mark (G7)
            continue
        if in_refs and not big:
            continue
        if big and words <= 12 and not t.endswith((".", ",", ";")):
            heads.append({"page": l["page"], "text": t, "num": None, "size": l["size"], "kind": "section"})
        elif l["bold"] and 2 <= words <= 12 and not t.endswith((".", ",", ";")) and (not t.endswith(":") or words <= 5) \
                and l["size"] >= body - 0.3:   # a short bold line ending in ":" is a heading ("Experimental details:"), a long one a run-in label
            heads.append({"page": l["page"], "text": t, "num": None, "size": l["size"], "kind": "subsection"})
        elif bfont and l.get("font") and l["font"] != bfont and not l.get("italic") and 2 <= words <= 12 \
                and abs(l["size"] - body) <= 1.0 and t[0].isupper() and not t.endswith((".", ",", ";", ":", "-")) \
                and not re.search(r"\d{2,}", t) and not (words <= 3 and re.search(r"[/=±×]", t)):  # "R / μm", "Loss / dB" are table axis labels, "Thin nitride loss/Q and …" is a heading
            heads.append({"page": l["page"], "text": t, "num": None, "size": l["size"], "kind": "subsection"})
    if not heads and skip_title:
        return find_headings(lines, body, bfont, skip_title=False)
    return heads, []


def abstract_span(text):
    m = re.search(r"(?im)^\s*abstract\b[:.]?\s*$", text)
    start = m.end() if m else None
    if start is None:
        m2 = re.search(r"(?i)\babstract\b", text[:6000])
        start = m2.end() if m2 else 0
    m3 = re.search(r"(?im)^\s*(1\.?\s+)?introduction\b", text[start:])
    end = start + m3.start() if m3 else min(len(text), start + 3000)
    return start, end


NOISE = ["5 nm", "(a)", "Bi2Se3", "MR %", "Intensity (a.u.)", "Raman shift (cm", "-1)", "Temperature (K)", "H (Tesla)",
         "\U0001D43B) − \U0001D6F9(", "\U0001D43B)] (2)", "*Corresponding Author", "K"]
HEADINGS = ["Sample preparation", "Hall measurements", "Topological surface states", "Annealing temperature series",
            "Results", "Magnetotransport of thin films"]


def noise_controls():
    """None when axis_like fires on every known noise token (positive) and on none of the real headings (negative)."""
    missed = [t for t in NOISE if not axis_like(t)]
    if missed:
        return f"positive control: axis_like did not fire on {missed}"
    wrong = [t for t in HEADINGS if axis_like(t)]
    if wrong:
        return f"negative control: axis_like fired on real headings {wrong}"
    lines = [{"page": 1, "text": t, "size": 12.0, "bold": True, "italic": False, "font": "F-bold", "in_fig": False} for t in HEADINGS[:1]]
    inside = [{"page": 1, "text": "Annealing temperature series", "size": 12.0, "bold": True, "italic": False,
               "font": "F-bold", "in_fig": True}]
    kept, _ = find_headings([{"page": 1, "text": "Abstract", "size": 12.0, "bold": True, "italic": False, "font": "F-bold"}]
                            + lines, 10.0, "F-body")
    dropped, _ = find_headings([{"page": 1, "text": "Abstract", "size": 12.0, "bold": True, "italic": False, "font": "F-bold"}]
                               + inside, 10.0, "F-body")
    if not any(h["text"] == HEADINGS[0] for h in kept):
        return "negative control: a bold heading outside any figure was not kept by find_headings"
    if any(h["text"] == "Annealing temperature series" for h in dropped):
        return "positive control: a heading-shaped line inside a figure box was kept by find_headings"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="run the heading-noise controls and exit")
    a = ap.parse_args(argv)
    if a.selftest:
        fault = noise_controls()
        print(json.dumps({"selftest": "FAIL", "reason": fault} if fault else
                         {"selftest": "OK", "positive": "axis/legend/equation/footnote tokens are dropped",
                          "negative": "real headings are kept"}, ensure_ascii=False))
        return 2 if fault else 0
    if not a.run:
        ap.error("--run is required (or --selftest)")
    src = a.run / "source"
    pdf, txt_p, fig_p = src / "paper.pdf", src / "paper.txt", src / "figures.json"
    text = txt_p.read_text(encoding="utf-8", errors="ignore") if txt_p.exists() else ""
    figs = json.loads(fig_p.read_text(encoding="utf-8")) if fig_p.exists() else {"captions": []}
    anomalies, units, subs, heads = [], [], [], []
    old_structure = json.loads((src / "structure.json").read_text(encoding="utf-8")) if (src / "structure.json").exists() else {}
    source_kind = old_structure.get("source_kind", "pdf")

    if pdf.exists():
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf))
        body = body_size(doc)
        bfont = body_font(doc)
        lines = line_records(doc)
        heads, subs = find_headings(lines, body, bfont)
        doc.close()
    else:
        body = None
        if source_kind in ("text", "jats"):   # no PDF: ingest wrote the section units (ids are the locators)
            heads = [{"page": None, "line": u.get("line"), "text": u["text"], "num": u["id"].lstrip("§"), "kind": u["kind"]}
                     for u in old_structure.get("units", []) if u.get("kind") in ("section", "subsection")]

    # sections → units; duplicates → anomalies
    for h in heads:
        sid = f"§{h['num']}" if h["num"] else f"§{h['text'][:40]}"
        u = {"id": sid, "kind": h.get("kind", "section"), "page": h["page"], "text": h["text"]}
        if h.get("line"):
            u["line"] = h["line"]
        units.append(u)
    where = lambda hs: [h["page"] if h["page"] is not None else f"line {h.get('line')}" for h in hs]
    nums = Counter(h["num"] for h in heads if h["num"])
    for n, c in nums.items():
        if c > 1:
            pages = where([h for h in heads if h["num"] == n])
            anomalies.append({"kind": "duplicate-section-number", "id": f"§{n}", "pages": pages,
                              "detail": f"section number {n} appears {c} times (pages {pages}) — a grafted or renumbered section; classify it (storyline ⑤′ or drift)"})
    texts = Counter(fold(h["text"]) for h in heads)
    for t, c in texts.items():
        if c > 1:
            pages = where([h for h in heads if fold(h["text"]) == t])
            anomalies.append({"kind": "duplicate-heading-text", "id": t[:40], "pages": pages,
                              "detail": f"heading '{t[:60]}' appears {c} times (pages {pages})"})

    # figures / tables → units; reference counts → anomalies
    caps = figs.get("captions", [])
    labels = {}
    for c in caps:
        lab = c.get("label", "")
        m = re.match(r"(Fig|Figure|Table)\.?\s*(\d+)", lab, re.I)
        if not m:
            continue
        kind = "table" if m.group(1).lower().startswith("tab") else "figure"
        key = f"Table {int(m.group(2))}" if kind == "table" else f"Fig. {int(m.group(2))}"
        if key not in labels:
            labels[key] = {"id": key, "kind": kind, "page": c.get("page"), "text": (c.get("caption") or "")[:80]}
            if c.get("page") is None and c.get("line"):
                labels[key]["line"] = c["line"]      # a text / JATS source has a line, not a page
    units.extend(labels.values())
    # a caption line is one whose start matches a known caption from figures.json — NOT any line that
    # happens to begin with "Fig. 4a." after a line break (Ow 2010 p.6: that is a body reference). Fold first, then cut:
    # figures.json captions are whitespace-normalised since 2026-09-26, and a line with "Figure 1.  Schematic" (two
    # spaces, Hong 2019) no longer matches when the 28 chars are cut before the fold.
    cap_starts = {fold(c.get("caption"))[:28] for c in caps if c.get("caption")}
    body_lines = [ln for ln in text.splitlines() if fold(ln)[:28] not in cap_starts]
    body_text = "\n".join(body_lines)
    refs = Counter()
    for m in REF_RE.finditer(body_text):
        refs[(f"Table {int(m.group(2))}" if m.group(1).lower().startswith("tab") else f"Fig. {int(m.group(2))}")] += 1
    for key, u in labels.items():
        if refs.get(key, 0) == 0:
            anomalies.append({"kind": "unreferenced-figure", "id": key, "pages": [u["page"]] if u["page"] is not None else [],
                              "detail": f"{key} ({'p.' + str(u['page']) if u['page'] is not None else 'caption'}) is never referenced in the body text — decorative, or a result the text does not discuss"})
    maxfig = max([int(k.split()[1]) for k in labels if k.startswith("Fig")] or [0])
    for key, c in refs.items():
        if key not in labels and c >= 2 and key.startswith("Fig") and int(key.split()[1]) <= maxfig + 1:
            anomalies.append({"kind": "reference-without-caption", "id": key, "pages": [],
                              "detail": f"the body refers to {key} {c}× but no caption was detected — check figures.json / the page images"})

    # abstract numbers → anomalies
    s, e = abstract_span(text)
    abstract = text[s:e]
    after = text[e:]
    missing = []
    for m in NUM_UNIT.finditer(abstract):
        num = m.group(1)
        if len(num) <= 1:
            continue
        if not re.search(r"(?<![\d.])" + re.escape(num) + r"(?![\d])", after):
            missing.append(f"{num} {m.group(2)}")
    if missing:
        anomalies.append({"kind": "abstract-number-not-in-body", "id": "abstract", "pages": [1] if source_kind == "pdf" else [],
                          "detail": f"numbers stated in the abstract that never appear in the body: {sorted(set(missing))} — over-claim, rounding, or a text-layer gap; check the page image"})

    out = {"schema": "paper-distill/structure@1", "body_font_size": body, "units": units, "subheadings": subs,
           "anomalies": anomalies, "abstract": {"chars": len(abstract), "numbers_checked": len(list(NUM_UNIT.finditer(abstract)))},
           "figure_refs": refs}
    if source_kind != "pdf":
        out["source_kind"] = source_kind
        out["locator_forms"] = old_structure.get("locator_forms", [])
    (src / "structure.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {"units": len(units), "sections": sum(1 for u in units if u["kind"] == "section"), "figures": len(labels),
               "subheadings": len(subs), "anomalies": [f"{x['kind']}:{x['id']}" for x in anomalies], "wrote": str(src / "structure.json")}
    print(json.dumps(summary, ensure_ascii=False))
    if a.print:
        for u in units:
            at = f"p.{u['page']}" if u.get("page") is not None else f"line {u.get('line')}"
            print(f"  {u['kind']:<8} {u['id']:<28} {at}  {u.get('text','')[:70]}")
        for x in anomalies:
            print(f"  ! {x['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
