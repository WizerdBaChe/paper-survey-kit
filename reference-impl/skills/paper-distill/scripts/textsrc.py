#!/usr/bin/env python
"""paper-distill textsrc — a paper that has no PDF: plain text (--text) or JATS XML (--jats) -> paper.txt + structure.

Why (G6, 2026-11-03 blind runs): with no PDF (an author-hosted text, a Europe PMC / PMC JATS file) ingest.py and
probe.py could not run, so paper-story S4/S10-S12 could not pass and the reader invented section and paragraph numbers.
This module gives such a source the same three artifacts a PDF run has: source/paper.txt, a unit list, and caption
anchors — and a LOCATOR FORM the reader may cite instead of p.N:

  §N / §N.M   a section by its number (JATS: counted in reading order, §0 = the abstract; plain text: the number the
              paper prints on the heading, else counted in reading order after the last numbered one)
  Fig. N      a figure        Table N   a table        (from <fig>/<table-wrap>, or the caption line in plain text)

paper-story's S3 pattern (render_story.LOCATOR_RE) already accepts `§\\s*\\d+` (verified 2026-11-03); `§1.1` matches on its
leading `§1`. No page exists, so a unit carries `line` (1-based line of source/paper.txt) instead of `page`.

Pure functions, stdlib only (no fitz) so a machine without PyMuPDF can still ingest a text source.
This module never judges content. Caption extents in PLAIN TEXT are a heuristic (see caption_extent); JATS captions are
exact (<caption> element).
"""
import re
import xml.etree.ElementTree as ET

# copy of probe.IMRAD / probe.BACKMATTER (probe imports fitz at module level, so it cannot be imported here)
IMRAD = {"abstract", "introduction", "background", "related work", "theory", "methods", "method", "materials and methods",
         "experimental", "experimental section", "experiments", "experiment", "results", "results and discussion",
         "results and discussions", "discussion", "discussions", "conclusion", "conclusions", "summary", "outlook",
         "summary and outlook", "appendix"}
BACKMATTER = ("references", "bibliography", "acknowledg", "funding", "author contribution", "competing interest",
              "conflict of interest", "conflicts of interest", "data availability", "code availability", "supplementary",
              "disclosures", "declaration", "ethics", "orcid", "publisher's note", "additional information",
              "author information", "peer review", "credit author", "footnotes", "associated data", "reporting summary")
# JATS section types / elements that are not body content
SKIP_SEC_TYPES = {"ack", "kwd-group", "history", "fn-group", "ref-list", "associated-data", "data-availability-statement",
                  "supplementary-materials", "supplementary-material", "notes", "author-notes"}
DROP_TEXT_TAGS = {"ref-list", "fn-group", "supplementary-material", "kwd-group", "history", "label"}
SOFT_HYPHEN = "­"


def flat(s):
    return re.sub(r"\s+", " ", s or "").strip()


def is_backmatter(title):
    ft = flat(title).casefold()
    return any(ft == b or ft.startswith(b) for b in BACKMATTER)


# ---------------------------------------------------------------- JATS

def _t(e):
    return e.tag.split("}")[-1] if isinstance(e.tag, str) else ""


def _formula(e):
    for k in e.iter():
        if _t(k) == "tex-math" and flat("".join(k.itertext())):
            return flat("".join(k.itertext()))
    return flat("".join(e.itertext()))


def inline(e):
    """Text of an element with its inline markup flattened: bibliography xrefs -> [n], superscript -> ^x, formulas -> their
    characters. Subscripts stay plain (Bi2Se3)."""
    out = [e.text or ""]
    for c in e:
        out.append(_inline_child(c))
        out.append(c.tail or "")
    return "".join(out)


def _inline_child(c):
    t = _t(c)
    if t == "xref":
        s = flat(inline(c))
        return f"[{s}]" if c.get("ref-type") == "bibr" else s
    if t == "sup":
        s = flat(inline(c))
        if any(_t(k) == "xref" and k.get("ref-type") == "bibr" for k in c) and not (c.text or "").strip():
            return s       # a citation superscript: the xref already printed [n]
        return "^" + s if len(s) <= 2 else "^(" + s + ")"
    if t in ("inline-formula", "disp-formula"):
        return _formula(c)
    if t == "break":
        return " "
    if t in ("inline-graphic", "graphic", "label"):
        return ""
    return inline(c)


def _para(e):
    return flat(inline(e))


def _caption_text(fig):
    """Label + caption of a <fig> / <table-wrap>: 'Fig. 1 <title> <paragraphs>' on ONE line."""
    label = flat("".join(fig.find("label").itertext())) if fig.find("label") is not None else ""
    cap = fig.find("caption")
    parts = []
    if cap is not None:
        for k in cap:
            s = _para(k)
            if s:
                parts.append(s)
    title = parts[0] if parts else ""
    if title and not re.search(r"[.!?:]$", title) and len(parts) > 1:
        parts[0] = title + "."
    return flat((label + " " + " ".join(parts)).strip()), label


def _table_rows(tw):
    rows = []
    for tr in tw.iter():
        if _t(tr) == "tr":
            cells = [flat(inline(c)) for c in tr if _t(c) in ("td", "th")]
            if any(cells):
                rows.append(" | ".join(cells))
    return rows


class _Out:
    def __init__(self):
        self.lines, self.units, self.captions = [], [], []

    def add(self, text=""):
        self.lines.append(text)
        return len(self.lines)       # 1-based line number of what was just added


def _label_key(label):
    m = re.match(r"(?i)(fig(?:ure)?|table|scheme)\.?\s*S?(\d+)", label or "")
    if not m:
        return None
    kind = "table" if m.group(1).lower().startswith("tab") else "figure"
    return kind, int(m.group(2))


def _walk_sec(sec, depth, counters, out, skipping):
    """Emit one <sec>. `depth` = nesting level among TITLED sections (a titleless <sec> is transparent)."""
    title_e = sec.find("title")
    title = flat("".join(title_e.itertext())) if title_e is not None else ""
    stype = (sec.get("sec-type") or "").lower()
    back = skipping or stype in SKIP_SEC_TYPES or (depth == 1 and bool(title) and is_backmatter(title))
    if title:
        if back:
            out.add(title)
        else:
            while len(counters) < depth:
                counters.append(0)
            counters[depth - 1] += 1
            del counters[depth:]
            num = ".".join(str(n) for n in counters)
            line = out.add(f"{num}. {title}" if depth == 1 else f"{num} {title}")
            out.units.append({"id": f"§{num}", "kind": "section" if depth == 1 else "subsection", "page": None,
                              "line": line, "text": title})
    for k in sec:
        t = _t(k)
        if t == "title" or t in DROP_TEXT_TAGS:
            continue
        if t == "p":
            s = _para(k)
            if s:
                out.add(s)
        elif t == "sec":
            _walk_sec(k, depth + 1 if title else depth, counters, out, back)
        elif t in ("fig", "table-wrap"):
            _block_caption(k, out)
        elif t == "disp-formula":
            lab = flat("".join(k.find("label").itertext())) if k.find("label") is not None else ""
            out.add(flat(f"{lab} {_formula(k)}"))
        elif t == "list":
            for li in k:
                s = flat(inline(li))
                if s:
                    out.add("- " + s)


def _block_caption(k, out):
    text, label = _caption_text(k)
    key = _label_key(label)
    line = out.add(text)
    if _t(k) == "table-wrap":
        for r in _table_rows(k):
            out.add(r)
    if key:
        out.captions.append({"page": None, "line": line, "kind": key[0], "label": label, "num": key[1], "bbox": None,
                             "caption": text})


def parse_jats(xml_text):
    """JATS -> {text, units, captions, meta}. Raises ValueError on a file that is not a JATS article."""
    root = ET.fromstring(xml_text)
    if _t(root) != "article":
        # PMC wraps some payloads in <pmc-articleset><article>
        art = next((e for e in root.iter() if _t(e) == "article"), None)
        if art is None:
            raise ValueError("not a JATS file: no <article> element")
        root = art
    front, body = root.find("front"), root.find("body")
    if body is None:
        raise ValueError("JATS file has no <body> (an abstract-only record?)")
    out, counters = _Out(), []
    am = front.find("article-meta") if front is not None else None
    title = flat(inline(am.find(".//article-title"))) if am is not None and am.find(".//article-title") is not None else ""
    if title:
        out.add(title)
        out.add("")
    abstract = ""
    if front is not None:
        for ab in front.iter("abstract"):
            if ab.get("abstract-type"):
                continue            # web-summary / graphical abstract: a publisher blurb, not the paper's abstract
            ps = [_para(p) for p in ab if _t(p) == "p" or _t(p) == "sec"]
            ps = [p for p in ps if p]
            if not ps:
                continue
            line = out.add("Abstract")
            for p in ps:
                out.add(p)
            out.units.append({"id": "§0", "kind": "section", "page": None, "line": line, "text": "Abstract"})
            abstract = " ".join(ps)
            out.add("")
            break
    for sec in body:
        if _t(sec) == "sec":
            _walk_sec(sec, 1, counters, out, False)
        elif _t(sec) == "p":
            s = _para(sec)
            if s:
                out.add(s)
        elif _t(sec) in ("fig", "table-wrap"):
            _block_caption(sec, out)
    meta = {"title": title, "abstract": abstract}
    if am is not None:
        meta["doi"] = next((flat("".join(a.itertext())) for a in am.iter("article-id") if a.get("pub-id-type") == "doi"), "")
        meta["venue"] = flat("".join(front.find(".//journal-title").itertext())) if front.find(".//journal-title") is not None else ""
        years = [flat("".join(y.itertext())) for y in am.iter("year")]
        meta["year"] = int(years[0]) if years and years[0].isdigit() else None
        authors = []
        for c in am.iter("contrib"):
            sn, gn = c.find(".//surname"), c.find(".//given-names")
            if sn is not None:
                authors.append(flat(f"{''.join(gn.itertext()) if gn is not None else ''} {''.join(sn.itertext())}"))
        meta["authors"] = authors
        meta["first_author_surname"] = next((flat("".join(c.find(".//surname").itertext())) for c in am.iter("contrib")
                                             if c.find(".//surname") is not None), "")
    return {"text": "\n".join(out.lines) + "\n", "units": out.units, "captions": out.captions, "meta": meta}


# ---------------------------------------------------------------- plain text

NUM_HEAD = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{1,110})$")
ABSTRACT_LINE = re.compile(r"^(?:a\s*b\s*s\s*t\s*r\s*a\s*c\s*t|abstract)\s*[:.]?$", re.I)


def heading_of(line):
    """(num or None, title) when a plain-text line is a section heading, else None. Same signal as probe.find_headings
    for numbered and IMRaD headings; font cues do not exist in text."""
    t = flat(line)
    if len(t) < 3 or len(t) > 120:
        return None
    if ABSTRACT_LINE.match(t):
        return None, "Abstract"
    m = NUM_HEAD.match(t)
    if m:
        rest = m.group(2)
        words = len(t.split())
        ok = (words <= 10 and not t.endswith((".", ",", ";", ":", "-")) and re.search(r"[A-Za-z]{4,}", rest)
              and not re.search(r"[,;:()]|\.\s", rest) and ("." in m.group(1) or re.match(r"^\d+\.\s", t)))
        if ok:
            return m.group(1), rest
    if t.casefold().rstrip(":.") in IMRAD or (is_backmatter(t) and len(t.split()) <= 4 and t[0].isupper()):
        return None, t.rstrip(":.")
    return None


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def parse_text(raw, caption_re):
    """Plain text -> {text, units, captions, meta}. text is the input unchanged (locators resolve against what the reader
    sees). Caption extents are a heuristic: from the label line to the first line that ends a sentence and is clearly
    shorter than the body's line width (cut at 12 lines; a table caption stops at its first sentence end)."""
    lines = raw.splitlines()
    nonblank = [flat(l) for l in lines if l.strip()]
    width = _median([len(l) for l in nonblank])
    units, captions, last_top, in_back, seen_abs = [], [], 0, False, False
    claimed = set()      # line indexes inside a caption: never headings
    for i, l in enumerate(lines):
        t = flat(l)
        m = caption_re.match(t) if t else None
        if m:
            kind = "table" if m.group(1).lower().startswith("tab") else "figure"
            acc, j = [t], i + 1
            tail_short = lambda s: s.rstrip().endswith(".") and len(flat(s)) < 0.7 * width
            done = tail_short(t) or (kind == "table" and t.endswith("."))
            while not done and j < len(lines) and len(acc) < 12:
                nl = flat(lines[j])
                if not nl or caption_re.match(nl) or heading_of(nl) or (len(nl) < 25 and not nl.endswith(".")):
                    break
                acc.append(nl)
                claimed.add(j)
                done = tail_short(nl) or (kind == "table" and nl.endswith("."))
                j += 1
            cap = flat(" ".join(acc))
            captions.append({"page": None, "line": i + 1, "kind": kind, "label": f"{m.group(1)} {m.group(2)}",
                             "num": int(m.group(2)), "bbox": None, "caption": cap})
            claimed.add(i)
            continue
    for i, l in enumerate(lines):
        if i in claimed:
            continue
        h = heading_of(l)
        if not h:
            continue
        num, title = h
        if not seen_abs and title == "Abstract":
            seen_abs = True
            units.append({"id": "§0", "kind": "section", "page": None, "line": i + 1, "text": "Abstract"})
            continue
        if is_backmatter(title):
            in_back = True
            continue
        if in_back and not num:
            continue
        in_back = False
        if num:
            top = int(num.split(".")[0])
            kind = "subsection" if "." in num else "section"
            last_top = max(last_top, top)
            sid = f"§{num}"
        else:
            last_top += 1
            kind, sid = "section", f"§{last_top}"
        units.append({"id": sid, "kind": kind, "page": None, "line": i + 1, "text": title})
    return {"text": raw if raw.endswith("\n") else raw + "\n", "units": units, "captions": captions, "meta": {}}


def guess_title_text(raw):
    """Longest early line that is not journal furniture. A guess (title_how: longest-early-line)."""
    lines = [flat(x) for x in raw.splitlines() if x.strip()][:15]
    stop = next((i for i, l in enumerate(lines) if re.match(r"(?i)^(a\s*r\s*t\s*i\s*c\s*l\s*e\s+i\s*n\s*f\s*o|a\s*b\s*s\s*t\s*r\s*a\s*c\s*t|abstract|keywords?)\b", l)), len(lines))
    head = lines[:stop]
    best_i = -1
    for i, l in enumerate(head):
        if re.search(r"©|available online|all rights reserved|issn|doi|^\d|www\.|http|"
                     r"\b(university|department|institute|laboratory|school|college|usa|china|taiwan)\b", l, re.I):
            continue
        if best_i < 0 or len(l) > len(head[best_i]):
            best_i = i
    if best_i < 0:
        return ""
    best = head[best_i]
    nxt = head[best_i + 1] if best_i + 1 < len(head) else ""
    if not best.endswith(".") and nxt and "," not in nxt and len(nxt) <= 80 and not re.search(r"@|\*", nxt):
        best = best + " " + nxt          # a title wrapped over two lines
    return best[:300]


def figure_units(captions):
    """One unit per distinct (kind, num): first caption wins (same rule as probe's labels)."""
    seen, out = set(), []
    for c in captions:
        key = (c["kind"], c["num"])
        if key in seen:
            continue
        seen.add(key)
        lab = f"Table {c['num']}" if c["kind"] == "table" else f"Fig. {c['num']}"
        out.append({"id": lab, "kind": c["kind"], "page": None, "line": c.get("line"), "text": c["caption"][:80]})
    return out
