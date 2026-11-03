#!/usr/bin/env python
"""paper-distill ingest — turn a PDF (or a URL record) into a run folder.

Emits: source/paper.txt (text with page markers — .txt, not .md, because the run folder
is a native area of the Obsidian vault whose lint treats every .md as a note needing a card),
source/pages/pNNN.png,
source/images/pNNN_iMM.png (embedded rasters), source/figures.json (caption
anchors with the full caption text, each checked verbatim + complete against
paper.txt, + image bboxes), _meta.json, and a PREFILLED cards.json skeleton.

This script never judges content (post-brief D-88 seam: no opinion here).
Title / year / DOI are GUESSES labelled guess=true in _meta.json; Stage 0
confirms them. Human notes -> stderr; one JSON object -> stdout (parse
stdout only, like skills/post-brief/pb.py kit).

A paper with NO PDF (an author-hosted text, a Europe PMC / PMC JATS file) is ingested with --text <file> or
--jats <xml>: source/paper.txt (JATS: body text with section titles, tags stripped; text: a copy), source/structure.json
(units numbered §N / §N.M, Fig. N, Table N; textsrc.py), source/figures.json (label + caption), and _meta.json with
source_kind text|jats (pdf for a PDF, url for a URL). There are no page images: what a figure SHOWS cannot be read from a
caption (SKILL.md figure cards), so such a run needs the figure image from the user before Stage 4.

Usage:
  python ingest.py <paper.pdf | https://...> [--home DIR] [--slug SLUG]
         [--first-author NAME] [--year YYYY] [--depth full|standard|triage]
         [--presenter NAME] [--dpi 110] [--no-pages] [--min-image 200]
  python ingest.py --text <paper.txt> | --jats <paper.xml> [same options]     a source without a PDF
  python ingest.py --selftest        run the caption check's two controls and the text/JATS controls, then exit
Exit: 0 ok · 1 usage/input error · 2 --selftest: a control misfired · 3 run folder already exists
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from xml.etree.ElementTree import ParseError as ET_ParseError
import sys as _hksys  # machine roots at run time (platform/codemod_roots.py, build plan H-1)
from pathlib import Path as _HKPath
_hksys.path.insert(0, str(_HKPath(__file__).resolve().parents[3] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SKILL_VERSION = "1.0"
_home = os.environ.get("PAPER_DISTILL_HOME") or hkroots.expand("${NOTES_VAULT}/literature/PaperSurvey")
DEFAULT_HOME = Path(_home) if _home else None  # None: pass --home (NOTES_VAULT unset)
# A caption is a label + number followed by punctuation ("Figure 2.", "Fig. 3 |", "Table 1 –"), by a capital or a
# bracket ("Fig. 1 Examples", Springer; "Figure 2 (a)"), or by nothing. Matched on the whitespace-normalised block:
# until 2026-09-26 it was matched on the block's first line and wanted a space after the punctuation, so a label alone
# on its line ("Figure 2.\n(a) Cross-sectional …", Tran 2018 p.3) was never an anchor. "Figure 7 shows the schematic"
# (Tran 2018 p.8) is a body sentence, not a caption — the same rule as crop.py's ANY_CAPTION.
# "Figure 1(a): Grazing incidence ..." (Kumar 2022, a preprint whose caption list sits before its figures) captions
# Figure 1: an optional panel suffix "(a)" may follow the number (2026-11-03).
CAPTION_RE = re.compile(
    r"^(Fig\.?|Figure|FIG\.?|FIGURE|Table|TABLE|Scheme|SCHEME)\s*S?(\d+)(?:\s?\([a-z]\))?"
    r"(?:\s*[.:|\-–—](?=\s|$)|\s+(?-i:[A-Z(\[])|$)", re.I)
# the caption check's controls: the 160-char F4 caption must FAIL, the PDF F4 caption must PASS (caption_controls)
CAPTION_CONTROL = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "caption-check_tran2018-F4.json"
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>,;]+")
ARXIV_RE = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5})(v\d+)?", re.I)
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
# marks already on a Zotero PDF (2026-09-14, researcher.tw review B-8 / reading-method B-11): read through the
# literature-search-extract connector, which owns the copy-then-read-only access and the origin rule
ZOTERO_CONNECTOR = Path(__file__).resolve().parents[2] / "literature-search-extract" / "connectors" / "zotero_local.py"
NOTE_CAP = 4000


def note(msg):
    print(msg, file=sys.stderr)


def slugify(text, words=4):
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", folded) if t]
    stop = {"a", "an", "the", "of", "for", "and", "on", "in", "with", "by", "to", "at", "via"}
    toks = [t for t in toks if t.lower() not in stop] or toks
    return "-".join(t.lower() for t in toks[:words]) or "paper"


def guess_title(doc):
    """Largest-font lines in the top 60% of page 1; fallback metadata; fallback first line."""
    try:
        page = doc[0]
        d = page.get_text("dict")
        lines = []
        for b in d.get("blocks", []):
            for ln in b.get("lines", []):
                txt = "".join(s.get("text", "") for s in ln.get("spans", [])).strip()
                if not txt or len(txt) < 4:
                    continue
                size = max((s.get("size", 0) for s in ln.get("spans", [])), default=0)
                y = ln.get("bbox", [0, 0, 0, 0])[1]
                lines.append((size, y, txt))
        if lines:
            ph = page.rect.height
            top = [l for l in lines if l[1] < ph * 0.6] or lines
            biggest = max(l[0] for l in top)
            cand = [l for l in top if l[0] >= biggest * 0.92]
            cand.sort(key=lambda l: l[1])
            title = " ".join(l[2] for l in cand)
            if 8 <= len(title) <= 300:
                return title, "font-size"
    except Exception as e:  # never fail ingest on a guess
        note(f"[ingest] title guess by font failed: {e}")
    meta_title = (doc.metadata or {}).get("title") or ""
    if len(meta_title.strip()) >= 8:
        return meta_title.strip(), "pdf-metadata"
    first = (doc[0].get_text("text").strip().splitlines() or [""])[0]
    return first[:200], "first-line"


def guess_ids(text_first_pages):
    doi = DOI_RE.search(text_first_pages)
    arx = ARXIV_RE.search(text_first_pages)
    years = YEAR_RE.findall(text_first_pages[:6000])
    year = None
    if years:
        # most frequent year on the first page is usually the publication year
        year = int(max(set(years), key=years.count))
    return (doi.group(0).rstrip(".)") if doi else ""), (arx.group(1) if arx else ""), year


def make_run_id(first_author, year, slug):
    """<FirstAuthor><Year>_<short-title-slug> — the folder is the PAPER's identity (user ruling 2026-09-04, naming over
    routing). Until then the id began with the ingest date (YYYYMMDD_), which told a reader nothing weeks later and let
    one paper own two dated folders; calibration copies now live under _calibration/<paper>/<label>/ (library.py)."""
    fa = re.sub(r"[^A-Za-z0-9]", "", unicodedata.normalize("NFKD", first_author or "").encode("ascii", "ignore").decode()) or "Unknown"
    return f"{fa}{year or ''}_{slug}"


def prefilled_cards(run_id, created, depth, presenter, source):
    row = {"function": "", "materials": "", "understood": ""}
    return {
        "schema": "paper-distill/cards@1",
        "run": {"id": run_id, "created": created, "revision": 1, "depth": depth,
                "presenter": presenter, "model": "", "skill_version": SKILL_VERSION},
        "source": source,
        "intake": {"why_this": "", "triage": {"abstract_problem": "", "conclusion_claim": "",
                                              "intro_contribution": "", "one_figure": "",
                                              "decision": "deep", "reason": ""},
                   "domain_profile": "", "lab_relevance": ""},
        "skeleton": {"I": dict(row), "M": dict(row), "R": dict(row), "D": dict(row),
                     "gap": {"problem": "", "prior": "", "gap": ""},
                     "method_elements": {"tools": "", "sampling": "", "procedure": "", "model": ""},
                     "anomalies": [], "what_why_leaks": []},
        "core": {"rq": "", "methods": "", "results": "", "limitations": "",
                 "contribution_claimed": "", "holds_up": "", "missing": "", "related_work": []},
        "claims": [],
        "did": {"framework": False, "term": False, "use_case": False,
                "experiment_or_derivation": False, "note": ""},
        "figures": [],
        "craft": {"argument_chain": [], "methods_writing": {"given": "", "missing_to_reproduce": "", "order": "", "design_data": ""},
                  "figure_design": [], "results_writing": "", "limitations_writing": "", "sentence_patterns": [], "my_rewrite": ""},
        "position": {"future_work": "", "limitations": "", "cross_paper": "", "gap": "",
                     "relevance": "", "borrow": "", "not_borrow": ""},
        "keypoint": {"title": "", "pillars": [{"axis": "方法", "text": "", "locator": ""}, {"axis": "證據", "text": "", "locator": ""},
                                              {"axis": "邊界", "text": "", "locator": ""}],
                     "question": "", "view": "", "basis": "", "conclusion": "",
                     "spoken": "", "holds_when": "", "overturned_by": "",
                     "evidence_kind": "none", "origin": "model", "candidates_rejected": []},
        "paper_says": {"conclusion_quote": "", "locator": ""},
        "terms": [],
        "talk": {"minutes": 0, "sections": []},
        "learning": {"hard": "", "self_check": [], "practice": "", "your_version_first": ""},
        "deck_hints": {"minutes": 0, "page_plan": [], "figures_for_deck": [], "essay_for_writing": ""},
    }


def zotero_marks(pdf: Path):
    """(marks, status). marks is None when nothing was checked (not a Zotero storage path, connector missing, read
    error) and a list — possibly empty — when the library was read. Never fails ingest; never judges a mark."""
    att = pdf.resolve().parent
    if att.parent.name.lower() != "storage" or not re.fullmatch(r"[A-Z0-9]{8}", att.name):
        return None, "not a Zotero storage path"
    if not ZOTERO_CONNECTOR.is_file():
        return None, f"connector missing: {ZOTERO_CONNECTOR}"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("zotero_local", ZOTERO_CONNECTOR)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        db = att.parent.parent / "zotero.sqlite"
        res, err = mod.read_marks(att.name, db if db.is_file() else None)
    except Exception as e:  # a schema change must not cost the ingest
        return None, f"read failed: {e.__class__.__name__}: {str(e)[:120]}"
    if err or res is None:
        return None, err or f"attachment key {att.name} not in the library"
    marks = [{"origin": m["origin"], "kind": m["kind"], "text": m["text"], "comment": m["comment"],
              "locator": m["locator"], "author": m["author"], "used_in": ""} for m in res["annotations"]]
    for n in res["notes"]:
        body = n["text"] if len(n["text"]) <= NOTE_CAP else n["text"][:NOTE_CAP] + f" …[truncated; full note {n['key']} in Zotero]"
        marks.append({"origin": "unattributed", "kind": "child-note", "text": body, "comment": n["title"],
                      "locator": "", "author": "", "used_in": ""})
    return marks, f"imported from attachment {att.name}"


def flat(s):
    return re.sub(r"\s+", " ", s).strip()


def line_index(text):
    """paper.txt for caption_fault: its non-blank lines, each whitespace-normalised, joined by one space, and the set
    of offsets in that string where a line ends."""
    parts, ends, at = [], set(), -1
    for line in text.splitlines():
        line = flat(line)
        if line:
            parts.append(line)
            at += len(line) + 1
            ends.add(at)
    return " ".join(parts), ends


def caption_fault(caption, index):
    """None when the caption is verbatim and complete against paper.txt, else why not.

    Verbatim: it occurs in paper.txt (both whitespace-normalised). Complete: an occurrence ends exactly where a line of
    paper.txt ends — a caption cut at a character count (160, before 2026-09-26) stops mid-line. Blind spots: a caption
    the PDF text layer splits into two blocks passes on its first block, and a block that runs on into body text passes
    whole; both end a line."""
    joined, ends = index
    c = flat(caption)
    at = joined.find(c)
    if at == -1:
        return "not in paper.txt"
    while at != -1:
        if at + len(c) in ends:
            return None
        at = joined.find(c, at + 1)
    return "ends mid-line in paper.txt"


def caption_controls():
    """None when the check fires as it must, else why it cannot be trusted. Negative: the Tran 2018 F4 caption as
    figures.json stored it before 2026-09-26 (cut at 160 chars) must fail AS INCOMPLETE; positive: the PDF F4 block
    must pass. Both against the fixture's paper.txt lines."""
    if not CAPTION_CONTROL.is_file():
        return f"control fixture missing: {CAPTION_CONTROL}"
    fx = json.loads(CAPTION_CONTROL.read_text(encoding="utf-8"))
    idx = line_index(fx["paper_txt"])
    neg = caption_fault(fx["truncated"], idx)
    if neg != "ends mid-line in paper.txt":
        return f"negative control gave {neg!r} (must be 'ends mid-line in paper.txt'): the 160-char F4 caption"
    pos = caption_fault(fx["full"], idx)
    if pos is not None:
        return f"positive control FAILED ({pos}; must pass): the PDF F4 caption"
    return None


def check_captions(captions, paper_txt):
    """Set caption_ok (and caption_fault) on every caption; the record for figures.json → caption_check. When a control
    misfires the verdicts are withheld (caption_ok = None), never guessed."""
    fault = caption_controls()
    rule = "verbatim in source/paper.txt and ends a line there (whitespace-normalised)"
    if fault:
        for c in captions:
            c["caption_ok"] = None
        return {"rule": rule, "controls": fault, "failed": None}
    idx = line_index(paper_txt)
    failed = []
    for c in captions:
        why = caption_fault(c["caption"], idx)
        c["caption_ok"] = why is None
        if why:
            c["caption_fault"] = why
            failed.append(f"{c['label']}@p{c['page']}" if c.get("page") else f"{c['label']}@line{c.get('line')}")
    return {"rule": rule, "controls": "ok", "failed": failed}


def ensure_home(home: Path):
    home.mkdir(parents=True, exist_ok=True)
    idx = home / "index.json"
    if not idx.exists():
        idx.write_text(json.dumps({"schema": "paper-distill/index@1", "home": str(home),
                                   "entries": []}, ensure_ascii=False, indent=1), encoding="utf-8")
    return idx


def ingest_pdf(pdf: Path, run_dir: Path, dpi: int, render_pages: bool, min_image: int):
    import fitz  # PyMuPDF

    src = run_dir / "source"
    (src / "pages").mkdir(parents=True, exist_ok=True)
    (src / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, src / "paper.pdf")
    doc = fitz.open(str(src / "paper.pdf"))
    # Publisher PDFs are often permission-encrypted (owner password only): PyMuPDF opens them, but the
    # Read tool refuses them ("PDF is password-protected") — met on the first two real papers,
    # 2026-09-02. Keep the original as paper.original.pdf and make paper.pdf an unencrypted copy so
    # the reader can SEE the pages; if that fails, the rendered pages/pNNN.png are the fallback.
    decrypted = False
    # is_encrypted turns False once MuPDF auto-authenticates with the empty user password, so look at
    # the trailer's /Encrypt entry as well (both real papers on 2026-09-02 reported is_encrypted=False
    # yet the Read tool refused them).
    try:
        has_encrypt = doc.xref_get_key(-1, "Encrypt")[0] not in ("null", "none", None)
    except Exception:
        has_encrypt = False
    if (doc.is_encrypted or has_encrypt) and not doc.needs_pass:
        try:
            shutil.move(str(src / "paper.pdf"), str(src / "paper.original.pdf"))
            doc.save(str(src / "paper.pdf"), encryption=fitz.PDF_ENCRYPT_NONE)
            doc.close()
            doc = fitz.open(str(src / "paper.pdf"))
            decrypted = not doc.is_encrypted
            note("[ingest] PDF carried an /Encrypt entry: wrote an unencrypted copy as source/paper.pdf "
                 "(original kept as paper.original.pdf). The Read tool may STILL refuse it (2026-09-02: it did) — "
                 "the reliable path is source/pages/pNNN.png")
        except Exception as e:
            note(f"[ingest] could not strip PDF encryption ({e}); the Read tool may refuse the PDF — use source/pages/pNNN.png")
            if not (src / "paper.pdf").exists() and (src / "paper.original.pdf").exists():
                shutil.copy2(src / "paper.original.pdf", src / "paper.pdf")
            doc = fitz.open(str(src / "paper.pdf"))

    md_parts, captions, images = [], [], []
    total_chars = 0
    for pno in range(doc.page_count):
        page = doc[pno]
        n = pno + 1
        text = page.get_text("text")
        total_chars += len(text.strip())
        md_parts.append(f"<!-- p.{n} -->\n{text.strip()}\n")
        # caption anchors: a text block that starts with Fig./Table + number; the caption is the whole block
        # (until 2026-09-26 it was cut at 160 chars, which Retort & Rove showed as "…data from th")
        for blk in page.get_text("blocks"):
            # (x0, y0, x1, y1, text, block_no, block_type); type 0 = text, 1 = image
            if len(blk) < 7 or blk[6] != 0:
                continue
            btxt = flat(blk[4])
            m = CAPTION_RE.match(btxt)
            if m:
                kind = "table" if m.group(1).lower().startswith("tab") else "figure"
                captions.append({"page": n, "kind": kind, "label": f"{m.group(1)} {m.group(2)}",
                                 "num": int(m.group(2)), "bbox": [round(v, 1) for v in blk[:4]],
                                 "caption": btxt})
        # embedded raster images
        for i, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
            except Exception:
                continue
            w, h = info.get("width", 0), info.get("height", 0)
            if w < min_image or h < min_image:
                continue
            ext = info.get("ext", "png")
            name = f"p{n:03d}_i{i:02d}.{ext}"
            (src / "images" / name).write_bytes(info["image"])
            rects = page.get_image_rects(xref)
            images.append({"page": n, "file": f"source/images/{name}", "width": w, "height": h,
                           "bbox": [round(v, 1) for v in rects[0]] if rects else None})
        if render_pages:
            pix = page.get_pixmap(dpi=dpi)
            pix.save(str(src / "pages" / f"p{n:03d}.png"))

    paper_txt = "\n".join(md_parts)
    (src / "paper.txt").write_text(paper_txt, encoding="utf-8")
    cap_check = check_captions(captions, paper_txt)
    (src / "figures.json").write_text(json.dumps(
        {"pages": doc.page_count, "page_size_pt": [round(doc[0].rect.width, 1), round(doc[0].rect.height, 1)],
         "dpi": dpi if render_pages else None, "caption_check": cap_check, "captions": captions, "images": images},
        ensure_ascii=False, indent=1), encoding="utf-8")
    if cap_check["controls"] != "ok":
        note(f"[ingest] caption check NOT RUN — its control misfired: {cap_check['controls']}. "
             "figures.json captions carry caption_ok=null; do not quote them as verbatim.")
    elif cap_check["failed"]:
        note(f"[ingest] {len(cap_check['failed'])} caption(s) not verbatim/complete against paper.txt: "
             f"{cap_check['failed']} (figures.json caption_ok=false, caption_fault says why)")

    first_text = "\n".join(doc[i].get_text("text") for i in range(min(2, doc.page_count)))
    title, how = guess_title(doc)
    doi, arxiv, year = guess_ids(first_text)
    meta_author = ((doc.metadata or {}).get("author") or "").split(",")[0].split(";")[0].strip()
    stats = {"pages": doc.page_count, "chars": total_chars, "images": len(images),
             "captions": len(captions), "captions_unverified": sum(c["caption_ok"] is not True for c in captions),
             "ocr_needed": doc.page_count > 0 and total_chars / doc.page_count < 200,
             "encrypted_original": (src / "paper.original.pdf").exists(), "decrypted_copy": decrypted}
    doc.close()
    return {"title": title, "title_how": how, "doi": doi, "arxiv": arxiv, "year": year,
            "author_meta": meta_author}, stats


def _textsrc():
    """textsrc.py beside this file; python -I does not put the script's folder on sys.path."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import textsrc
    return textsrc


def parse_textlike(kind, path):
    """{text, units, captions, meta, guess} for a --text / --jats source. Raises ValueError / ET.ParseError on a file
    that is not what its flag says."""
    ts = _textsrc()
    data = path.read_bytes()
    if kind == "jats":
        parsed = ts.parse_jats(data)
        m = parsed["meta"]
        guess = {"title": m.get("title", ""), "title_how": "jats article-title", "doi": m.get("doi", ""), "arxiv": "",
                 "year": m.get("year"), "author_meta": m.get("first_author_surname", "")}
    else:
        # CRLF / CR sources are normalised here: structure.json line numbers are counted on this
        # text, and paper.txt is written with LF, so both sides count the same lines.
        raw = data.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        if not raw.strip():
            raise ValueError("empty text file")
        parsed = ts.parse_text(raw, CAPTION_RE)
        head = parsed["text"][:6000]
        doi, arxiv, year = guess_ids(head)
        guess = {"title": ts.guess_title_text(raw), "title_how": "longest-early-line", "doi": doi, "arxiv": arxiv,
                 "year": year, "author_meta": ""}
    parsed["guess"] = guess
    return parsed


def write_textlike(kind, parsed, run_dir):
    """source/paper.txt, figures.json, structure.json for a text / JATS run. Returns (guess, stats)."""
    ts = _textsrc()
    src = run_dir / "source"
    src.mkdir(parents=True, exist_ok=True)
    text, caps = parsed["text"], parsed["captions"]
    with open(src / "paper.txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    cap_check = check_captions(caps, text)
    cap_check["extent"] = "exact (<caption> element)" if kind == "jats" else "heuristic (label line to the first short sentence end)"
    (src / "figures.json").write_text(json.dumps(
        {"pages": None, "page_size_pt": None, "dpi": None, "source_kind": kind, "caption_check": cap_check,
         "captions": caps, "images": []}, ensure_ascii=False, indent=1), encoding="utf-8")
    if cap_check["controls"] != "ok":
        note(f"[ingest] caption check NOT RUN — its control misfired: {cap_check['controls']}.")
    structure = {"schema": "paper-distill/structure@1", "source_kind": kind, "body_font_size": None,
                 "units": parsed["units"] + ts.figure_units(caps), "subheadings": [], "anomalies": [],
                 "abstract": {"chars": 0, "numbers_checked": 0}, "figure_refs": {},
                 "locator_forms": ["§N / §N.M (unit id)", "Fig. N", "Table N"],
                 "note": "written by ingest; probe.py --run adds the anomalies and keeps these section units"}
    (src / "structure.json").write_text(json.dumps(structure, ensure_ascii=False, indent=1), encoding="utf-8")
    stats = {"pages": None, "chars": len(text), "lines": text.count("\n"), "images": 0,
             "captions": len(caps), "captions_unverified": sum(c["caption_ok"] is not True for c in caps),
             "sections": sum(1 for u in parsed["units"]), "ocr_needed": False}
    return parsed["guess"], stats


# two tiny control sources for --selftest: the JATS one must yield §0 + §1 + §1.1 + §2 and Fig. 1; the text one must yield
# its numbered headings and Fig. 1; a text with no heading at all must yield NO section unit (negative)
_JATS_CONTROL = ('<article><front><article-meta><title-group><article-title>Control paper</article-title></title-group>'
                 '<abstract><title>Abstract</title><p>We measure x.</p></abstract></article-meta></front><body>'
                 '<sec><title>Introduction</title><p>Text<sup><xref ref-type="bibr" rid="r1">1</xref></sup>.</p></sec>'
                 '<sec><title>Results</title><sec><title>First result</title><p>See Fig. 1.</p>'
                 '<fig id="f1"><label>Fig. 1</label><caption><title>A cartoon.</title><p>(a) the surface.</p></caption></fig>'
                 '</sec></sec><sec sec-type="ack"><title>Acknowledgements</title><p>Thanks.</p></sec></body></article>')
_TEXT_CONTROL = ("Control paper\nABSTRACT\nWe measure x in a long enough line to set the median width of this text.\n"
                 "1. Introduction\nBody line one of the control text is long enough to set the median width here.\n"
                 "Body line two of the control text is long enough to set the median width here, too.\n"
                 "2. Results and discussion\nFig. 1. A cartoon of the sample.\n"
                 "Body line three of the control text is long enough to set the median width here, too.\nReferences\n")


def textsrc_controls():
    """None when the text/JATS parsers behave on their control sources, else why they cannot be trusted."""
    ts = _textsrc()
    try:
        j = ts.parse_jats(_JATS_CONTROL.encode("utf-8"))
    except Exception as e:  # a parser that cannot read its own control
        return f"JATS control did not parse: {e.__class__.__name__}: {e}"
    ids = [u["id"] for u in j["units"]]
    if ids != ["§0", "§1", "§2", "§2.1"]:
        return f"JATS control units {ids} (expected ['§0','§1','§2','§2.1']; Acknowledgements must not be a unit)"
    if [c["label"] for c in j["captions"]] != ["Fig. 1"] or "[1]" not in j["text"]:
        return f"JATS control captions {[c['label'] for c in j['captions']]} / citation marker missing"
    t = ts.parse_text(_TEXT_CONTROL, CAPTION_RE)
    ids = [u["id"] for u in t["units"]]
    if ids != ["§0", "§1", "§2"] or [c["label"] for c in t["captions"]] != ["Fig. 1"]:
        return f"text control units {ids} / captions {[c['label'] for c in t['captions']]} (expected §0 §1 §2, Fig. 1)"
    flat_text = ts.parse_text("just one paragraph of prose\nand a second line of it\n", CAPTION_RE)
    if flat_text["units"]:
        return f"negative control: a text with no heading gave units {[u['id'] for u in flat_text['units']]}"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="PDF path or URL")
    ap.add_argument("--text", type=Path, help="a plain-text paper instead of a PDF (source_kind text)")
    ap.add_argument("--jats", type=Path, help="a JATS XML paper (Europe PMC / PMC) instead of a PDF (source_kind jats)")
    ap.add_argument("--home", type=Path, default=DEFAULT_HOME)
    ap.add_argument("--slug", default="")
    ap.add_argument("--first-author", default="")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--depth", choices=["full", "standard", "triage"], default="full")
    ap.add_argument("--presenter", default="")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--no-pages", action="store_true")
    ap.add_argument("--min-image", type=int, default=200)
    ap.add_argument("--selftest", action="store_true",
                    help="run the caption check's two controls and the text/JATS controls, then exit")
    a = ap.parse_args(argv)

    if a.selftest:
        fault = caption_controls() or textsrc_controls()
        print(json.dumps({"selftest": "FAIL", "reason": fault} if fault else
                         {"selftest": "OK", "negative": "160-char F4 caption -> ends mid-line",
                          "positive": "PDF F4 caption -> pass", "fixture": CAPTION_CONTROL.name,
                          "text_jats": "JATS + text control sources give the expected units; a heading-less text gives none"},
                         ensure_ascii=False))
        return 2 if fault else 0
    if sum(bool(x) for x in (a.input, a.text, a.jats)) != 1:
        ap.error("give exactly one of: input (PDF path or URL), --text, --jats (or --selftest)")

    home = a.home
    if home is None:
        ap.error("--home is required: set PAPER_DISTILL_HOME, or NOTES_VAULT in adapt/host.toml")
    ensure_home(home)
    created = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    if a.text or a.jats:
        a.input = str(a.text or a.jats)
    is_url = a.input.lower().startswith(("http://", "https://"))

    source_kind = "url" if is_url else "text" if a.text else "jats" if a.jats else "pdf"
    if source_kind in ("text", "jats"):
        path = a.text or a.jats
        if not path.is_file():
            note(f"[ingest] not a file: {path}")
            return 1
        try:
            parsed = parse_textlike(source_kind, path)
        except (ValueError, ET_ParseError) as e:
            note(f"[ingest] cannot read {path.name} as {source_kind}: {e}")
            return 1
        gm = parsed["guess"]
        year = a.year or gm["year"]
        first_author = a.first_author or parsed["meta"].get("first_author_surname", "")
        slug = a.slug or slugify(gm["title"])
        run_id = make_run_id(first_author, year, slug)
        run_dir = home / run_id
        if run_dir.exists():
            note(f"[ingest] run folder exists: {run_dir} — pass --slug to make a new one")
            return 3
        run_dir.mkdir(parents=True)
        (run_dir / "figures").mkdir()
        guess, stats = write_textlike(source_kind, parsed, run_dir)
        meta_in = parsed["meta"]
        source = {"type": "paper", "title": guess["title"], "authors": meta_in.get("authors", []),
                  "venue": meta_in.get("venue", ""), "year": year, "doi": guess["doi"], "url": "", "access": "full",
                  "file": "source/paper.txt", "pages": None, "lang": "", "abstract": meta_in.get("abstract", "")}
        nxt = [f"Stage 0: this is a {source_kind.upper()} source — no PDF, no page images. Read source/paper.txt "
               "(Abstract → Conclusion → Introduction); confirm the guessed title/year/DOI and fill authors/venue in "
               "cards.json → source.",
               "Locators are §N / §N.M (source/structure.json units), Fig. N, Table N — never p.N and never a section or "
               "paragraph number you counted yourself.",
               "Figures: there are NO figure images. A statement about what a figure SHOWS needs the rendered image "
               "(SKILL.md figure cards): ask the user for the figure file, or record the figure as caption-only and make "
               "no claim about its content. figures.json holds label + caption only.",
               "Run probe.py --run <run_dir> --print (units to cover + determinable anomalies).",
               "Then stages 1–7 per SKILL.md; decks and the key point are paper-story's, not this skill's."]
        if source_kind == "text":
            nxt.insert(0, "Plain text: caption extents and heading detection are heuristics (figures.json "
                          "caption_check.extent = heuristic); check each unit against paper.txt before relying on it.")
        if stats["captions_unverified"]:
            nxt.insert(0, f"figures.json: {stats['captions_unverified']} caption(s) without caption_ok=true — take those "
                          "from source/paper.txt.")
    elif is_url:
        title_guess = a.slug or slugify(a.input.rstrip("/").split("/")[-1] or "url")
        run_id = make_run_id(a.first_author, a.year, a.slug or title_guess)
        run_dir = home / run_id
        if run_dir.exists():
            note(f"[ingest] run folder exists: {run_dir} — pass --slug to make a new one")
            return 3
        (run_dir / "source").mkdir(parents=True)
        (run_dir / "figures").mkdir()
        (run_dir / "source" / "source.url.txt").write_text(a.input + "\n", encoding="utf-8")
        guess = {"title": "", "title_how": "none", "doi": "", "arxiv": "", "year": a.year, "author_meta": ""}
        stats = {"pages": None, "chars": 0, "images": 0, "captions": 0, "ocr_needed": False}
        source = {"type": "paper", "title": a.slug or title_guess, "authors": [], "venue": "",
                  "year": a.year, "doi": "", "url": a.input, "access": "partial",
                  "file": "", "pages": None, "lang": "", "abstract": ""}
        nxt = ["URL recorded only. Fetch the page text with WebFetch (HTML pages such as arXiv /html or a "
               "publisher full-text page) and save it as source/paper.txt with <!-- p.N --> markers per section; "
               "a PDF link is a file download — hand it to the user to download (state filename, source, size) "
               "and re-run ingest on the file.",
               "Stage 0: confirm title/authors/venue/year/DOI in cards.json → source; set access honestly."]
    else:
        pdf = Path(a.input)
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            note(f"[ingest] not a PDF file: {pdf}")
            return 1
        # peek for the id before creating the folder
        import fitz
        with fitz.open(str(pdf)) as d0:
            t0, _ = guess_title(d0)
            ftxt = "\n".join(d0[i].get_text("text") for i in range(min(2, d0.page_count)))
        _, _, y0 = guess_ids(ftxt)
        year = a.year or y0
        slug = a.slug or slugify(t0)
        run_id = make_run_id(a.first_author, year, slug)
        run_dir = home / run_id
        if run_dir.exists():
            note(f"[ingest] run folder exists: {run_dir} — pass --slug to make a new one")
            return 3
        run_dir.mkdir(parents=True)
        (run_dir / "figures").mkdir()
        guess, stats = ingest_pdf(pdf, run_dir, a.dpi, not a.no_pages, a.min_image)
        source = {"type": "paper", "title": guess["title"], "authors": [], "venue": "",
                  "year": year, "doi": guess["doi"], "url": "", "access": "full",
                  "file": "source/paper.pdf", "pages": stats["pages"], "lang": "", "abstract": ""}
        nxt = ["Stage 0 (3 min): Read the PDF (Read tool, pages=) — Abstract → Conclusion → Introduction; "
               "confirm the guessed title/year/DOI, fill authors/venue/abstract in cards.json → source.",
               "Figures: source/figures.json lists caption anchors; view source/pages/pNNN.png; crop with crop.py.",
               "Run probe.py --run <run_dir> --print (source/structure.json: units to cover + anomalies to classify).",
               "Then stages 1–7 per SKILL.md (reading-record.md from assets/reading-record-template.md); "
               "decks and the key point are paper-story's (render_story.py), not this skill's."]
        if stats["captions_unverified"]:
            nxt.insert(0, f"figures.json: {stats['captions_unverified']} caption(s) without caption_ok=true — "
                          "not proven verbatim/complete; take those from source/paper.txt or the page image.")
        if stats["ocr_needed"]:
            nxt.insert(0, "Text layer is thin (< 200 chars/page): likely scanned. OCR first (e.g. markitdown-gui) "
                          "and re-ingest, or read the page renders directly and mark access=partial.")
    marks, marks_status = ((None, "url input") if is_url else (None, f"{source_kind} source, not a PDF")
                           if source_kind != "pdf" else zotero_marks(Path(a.input)))
    if marks:
        origins = {}
        for m in marks:
            origins[m["origin"]] = origins.get(m["origin"], 0) + 1
        nxt.insert(1, f"Marks: cards.json → intake.marked holds {len(marks)} Zotero mark(s) ("
                      + ", ".join(f"{k} {v}" for k, v in sorted(origins.items())) + "). Read them AFTER Stage 0's six "
                      "questions; only owner marks are the user's, once confirmed (reading-method.md §Stage 0).")

    cards = prefilled_cards(run_id, created, a.depth, a.presenter, source)
    if marks is not None:
        cards["intake"]["marked"] = marks
    (run_dir / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = {"run_id": run_id, "created": created, "depth": a.depth, "presenter": a.presenter,
            "input": a.input, "input_kind": source_kind, "source_kind": source_kind,
            "guess": {k: {"value": v, "guess": True} for k, v in guess.items()},
            "stats": stats, "status": "ingested", "skill_version": SKILL_VERSION,
            "home": str(home), "zotero_marks": {"status": marks_status,
                                                "count": None if marks is None else len(marks)}}
    (run_dir / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    note(f"[ingest] run folder: {run_dir}")
    note(f"[ingest] title guess ({guess['title_how']}): {guess['title'][:120]}")
    if stats["pages"]:
        note(f"[ingest] pages={stats['pages']} chars={stats['chars']} images={stats['images']} captions={stats['captions']}")
    out = {"run_dir": str(run_dir), "run_id": run_id, "input_kind": meta["input_kind"],
           "files": {"paper_txt": str(run_dir / "source" / "paper.txt"),
                     "pages_dir": str(run_dir / "source" / "pages"),
                     "images_dir": str(run_dir / "source" / "images"),
                     "figures_json": str(run_dir / "source" / "figures.json"),
                     "cards_json": str(run_dir / "cards.json"),
                     "meta_json": str(run_dir / "_meta.json")},
           "guess": guess, "stats": stats, "next": nxt}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
