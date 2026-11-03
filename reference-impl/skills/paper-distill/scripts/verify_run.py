#!/usr/bin/env python
"""paper-distill verify_run — the dispatcher's instrument for checking a finished run.

"Verify, don't self-verify": the session (or subagent) that wrote a run never grades it.
This script rules only on what it can DETERMINE from the run folder; everything else
(is the key point really the whole paper? is the figure the right one?) is a human or
dispatcher judgment and is listed as TODO lines, not verdicts.

Checks (severity by consumer — FAIL blocks acceptance, WARN is reported):
  V1  FAIL  cards.json validates against assets/cards.schema.json
  V2  WARN  verbatim fidelity: paper_says.conclusion_quote, source.abstract (first 120 chars)
            and every craft.sentence_patterns[].pattern occur VERBATIM in source/paper.txt
            (alnum-folded). WARN not FAIL because the TEXT LAYER can be incomplete (seen 2026-09-03:
            no abstract in an Aspose PDF's layer); the human compares the named items against the
            page image — absent there too = fabrication (PaperLens BR-1) → reject the run.
  V3  WARN  locator existence: every `p.N` ≤ page count; every `Fig.N`/`Table N` cited in
            cards.json has a caption anchor in source/figures.json (a missing anchor may be a
            caption the extractor did not parse — hence WARN, with the list)
  V4  FAIL  reading-record.md exists, has the vault front matter keys, contains no leftover
            `{{` placeholders, and carries origin tags
  V5  WARN  key point shape: title ≤ 50 CJK chars, three pillars with text + locator, spoken ≤ 40
  V6  WARN  origin-tag density in reading-record.md: at least 15 tags (`[author]`/`[verified]`/
            `[inferred]`/`[assumed]`) — a record without tags is a summary
  V7  FAIL  deliverables present: talk-script.md, keypoint-onepager.html, gates.txt with RESULT: PASS
  V8  INFO  numbers in the key point + pillars that do not occur anywhere in paper.txt (they may be
            re-derived — listed for the dispatcher to check by eye)
  V9  WARN  Stage 0b glossary (terms[] with role): 10–15 terms, each verbatim in the text layer, every
            `coined` term mentioned in the claim audit (term-substitution check); V9b INFO ask_next reuse
  V10 WARN  core.assumptions[]: where = locator | implicit; if_false names existing claim rows; a
            tested=no premise reaches the named row's `missing`; V10b INFO row count (R-2 counter)
  V11 WARN  intake.triage.depth_ruler: three axes present, consistent with decision (relevance low → skim)
  V12 WARN  position.lineage.group_prior_work and learning.admire present at full depth
            (V9–V12 SKIP when the field is absent: runs before 2026-09-03 never start warning;
            measurement plan: evals/measurement-plan-new-fields-2026-09-03.md)

A run with source_kind text|jats (ingest.py --text / --jats; _meta.json) has no PDF page: the page-based part of V3 is
SKIP with its reason, V3 judges what exists instead (every `§N` a card cites is a structure.json unit: FAIL; a `p.N`
cite cannot resolve: WARN; Fig./Table anchors as for a PDF), and
  V13 FAIL  structure.json has section units and each unit's `line` holds its text in source/paper.txt
            (only for text|jats runs; a PDF run prints no V13 row)

Usage: python verify_run.py <run_dir> [--json]
Exit 0 clean/WARN · 2 any FAIL
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crop_all import TEXTLIKE, source_kind, unit_resolves  # noqa: E402  text|jats = a run with no PDF

sys.stdout.reconfigure(encoding="utf-8")
SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA = SKILL_DIR / "assets" / "cards.schema.json"
LOC_P = re.compile(r"\bp\.\s*(\d+)")
LOC_SEC = re.compile(r"§\s*(\d+(?:\.\d+)*)")
LOC_FIG = re.compile(r"\b(Fig\.?|Figure|Table)\s*S?(\d+)", re.I)
TAG_RE = re.compile(r"\[(author|verified|inferred|assumed)\]")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")
FM_KEYS = ("xi:", "what:", "tags:", "aliases:", "date:", "status:", "kind: literature", "source:", "verified:", "review-when:", "domain:", "promoted-to:")


def fold(s):
    """Compare on letters/digits only: PDF extraction breaks words at line ends ("micro-\\nmirrors"),
    so verbatim is judged on the alphanumeric stream, casefolded (NFKC first)."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return re.sub(r"[^0-9a-z⺀-鿿㐀-䶿]+", "", s)


def walk_strings(obj, path="cards"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def v3_pdf(run, cards, pages, add):
    anchors = set()
    figs_p = run / "source" / "figures.json"
    if figs_p.exists():
        fj = json.loads(figs_p.read_text(encoding="utf-8"))
        pages = pages or fj.get("pages", 0)
        for c in fj.get("captions", []):
            anchors.add((c["kind"], c["num"]))
    missing_p, missing_f = set(), set()
    for path, s in walk_strings(cards):
        if not any(k in path for k in ("locator", "basis", "evidence", "pillars")):
            continue
        for m in LOC_P.finditer(s):
            if pages and int(m.group(1)) > pages:
                missing_p.add(f"p.{m.group(1)}@{path}")
        for m in LOC_FIG.finditer(s):
            kind = "table" if m.group(1).lower().startswith("tab") else "figure"
            if anchors and (kind, int(m.group(2))) not in anchors:
                missing_f.add(f"{m.group(1)} {m.group(2)}")
    if not pages and not anchors:
        add("V3", "SKIP", "no source/figures.json or page markers — locator existence not determinable")
    elif missing_p:
        add("V3", "FAIL", f"page locators beyond the paper's {pages} pages: {sorted(missing_p)[:8]}")
    elif missing_f:
        add("V3", "WARN", f"figure/table locators without a caption anchor in figures.json: {sorted(missing_f)} — check by eye (caption may be unparsed)")
    else:
        add("V3", "PASS", f"all page locators ≤ {pages}; all cited figures/tables have caption anchors")


def structure_units(run):
    """(units of source/structure.json or None when absent/unreadable, the lines of source/paper.txt)."""
    sp, tp = run / "source" / "structure.json", run / "source" / "paper.txt"
    try:
        units = json.loads(sp.read_text(encoding="utf-8")).get("units", []) if sp.is_file() else None
    except (OSError, ValueError):
        units = None
    return units, (tp.read_text(encoding="utf-8").splitlines() if tp.is_file() else [])


def v3_textlike(run, cards, kind):
    """V3 for a run with no PDF: [(check, status, msg)]. The page-based half is SKIP with its reason; what exists is
    judged: a cited `§N` must be a structure.json unit id (FAIL: ids are exact, so an invented number is determinable),
    a cited `p.N` cannot resolve in a source without pages (WARN: the reader may cite the publisher's pagination),
    Fig./Table anchors as for a PDF (WARN)."""
    units, _ = structure_units(run)
    ids = {u.get("id") for u in units or []}
    anchors = set()
    figs_p = run / "source" / "figures.json"
    if figs_p.exists():
        anchors = {(c["kind"], c["num"]) for c in json.loads(figs_p.read_text(encoding="utf-8")).get("captions", [])}
    bad_sec, page_cites, missing_f = set(), set(), set()
    for path, s in walk_strings(cards):
        if not any(k in path for k in ("locator", "basis", "evidence", "pillars")):
            continue
        for m in LOC_SEC.finditer(s):
            if f"§{m.group(1)}" not in ids:
                bad_sec.add(f"§{m.group(1)}@{path}")
        for m in LOC_P.finditer(s):
            page_cites.add(f"p.{m.group(1)}@{path}")
        for m in LOC_FIG.finditer(s):
            k = "table" if m.group(1).lower().startswith("tab") else "figure"
            if anchors and (k, int(m.group(2))) not in anchors:
                missing_f.add(f"{m.group(1)} {m.group(2)}")
    rows = [("V3p", "SKIP", f"source_kind {kind}: no PDF, so no page count — page locators cannot be bounded")]
    if units is None:
        rows.append(("V3", "SKIP", "no source/structure.json — § locators not determinable"))
    elif bad_sec:
        rows.append(("V3", "FAIL", f"§ locators that are not a structure.json unit id: {sorted(bad_sec)[:8]} (units: {sorted(ids)[:12]})"))
    elif page_cites:
        rows.append(("V3", "WARN", f"p.N locators in a {kind} source, which has no pages: {sorted(page_cites)[:8]} — use §N / Fig. N / Table N, or say which pagination p.N means"))
    elif missing_f:
        rows.append(("V3", "WARN", f"figure/table locators without a caption anchor in figures.json: {sorted(missing_f)} — check by eye (caption may be unparsed)"))
    else:
        rows.append(("V3", "PASS", f"all § locators are structure.json units; all cited figures/tables have caption anchors"))
    return rows


def v13_structure(run):
    """V13 (text|jats runs): structure.json has section units and each unit's `line` holds its text in paper.txt."""
    units, lines = structure_units(run)
    if units is None:
        return ("V13", "FAIL", "source/structure.json missing or unreadable — a text/JATS run has no other unit list")
    secs = [u for u in units if u.get("kind") in ("section", "subsection")]
    bad = []
    for u in units:
        if u.get("kind") not in ("section", "subsection", "figure", "table"):
            continue
        n = u.get("line")
        if not isinstance(n, int) or not 1 <= n <= len(lines) or not unit_resolves(u, lines[n - 1]):
            bad.append(f"{u.get('id')}@line{n}")
    if bad:
        return ("V13", "FAIL", f"{len(bad)} structure.json unit(s) whose `line` does not hold their text in paper.txt: {bad[:8]}")
    if not secs:
        return ("V13", "WARN", "structure.json has no section unit — no § locator can be cited (a heading-less text?)")
    return ("V13", "PASS", f"{len(secs)} section unit(s) and {len(units) - len(secs)} figure/table unit(s) resolve to lines of paper.txt")


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    run = Path(argv[0])
    as_json = "--json" in argv
    rows = []

    def add(v, s, m):
        rows.append({"check": v, "status": s, "msg": m})

    cards_p = run / "cards.json"
    if not cards_p.exists():
        add("V1", "FAIL", "cards.json missing")
        print(json.dumps(rows, ensure_ascii=False, indent=1) if as_json else "\n".join(f"{r['check']} {r['status']} — {r['msg']}" for r in rows))
        return 2
    cards = json.loads(cards_p.read_text(encoding="utf-8"))

    # V1 schema
    try:
        import jsonschema
        errs = list(jsonschema.Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(cards))
        add("V1", "FAIL" if errs else "PASS", (f"{len(errs)} schema violation(s): " + "; ".join(f"{'/'.join(str(p) for p in e.path)}: {e.message[:80]}" for e in errs[:4])) if errs else "cards.json valid")
    except ImportError:
        add("V1", "WARN", "jsonschema not installed — schema not checked")

    kind = source_kind(run)
    textlike = kind in TEXTLIKE

    # text source
    txt_p = run / "source" / "paper.txt"
    if not txt_p.exists():
        txt_p = run / "source" / "paper.md"
    text = fold(txt_p.read_text(encoding="utf-8")) if txt_p.exists() else ""
    pages = text.count("<!-- p.") if text else 0

    # V2 verbatim fidelity
    if not text:
        add("V2", "SKIP", "no source/paper.txt — verbatim fidelity not determinable")
    else:
        bad = []
        q = fold(cards.get("paper_says", {}).get("conclusion_quote", ""))
        if q and q not in text:
            bad.append("paper_says.conclusion_quote")
        ab = fold(cards.get("source", {}).get("abstract", ""))[:120]
        if ab and ab not in text:
            bad.append("source.abstract (first 120 chars)")
        for i, sp in enumerate((cards.get("craft") or {}).get("sentence_patterns") or []):
            pat = fold(sp.get("pattern", "")).strip("\"'“”‘’ ")
            if pat and pat not in text:
                bad.append(f"craft.sentence_patterns[{i}]")
        # WARN, not FAIL: the text layer itself can be incomplete (2026-09-03: an Aspose-produced PDF's
        # text layer had NO abstract at all, so a correctly transcribed abstract "failed"). Absence is
        # therefore not determinable as fabrication — downgrade and forward: the checker names the items
        # and the human compares them against source/pages/pNNN.png. Promotion trigger: a quote that is
        # absent from BOTH the text layer and the page image is fabrication → the run is rejected.
        tail = ("compare each against source/paper.txt's own lines (a " + kind + " source has no page image; absent from the source text "
                "too = fabrication → reject)") if textlike else (
            "compare each against source/pages/pNNN.png by eye (text layer may be incomplete; absent from the page too = fabrication → reject)")
        add("V2", "WARN" if bad else "PASS", ("not found verbatim in the TEXT LAYER: " + ", ".join(bad) + " — " + tail)
            if bad else "conclusion quote, abstract and sentence patterns are verbatim in the paper")

    # V3 locator existence
    if textlike:
        for v, s, m in v3_textlike(run, cards, kind):
            add(v, s, m)
        add(*v13_structure(run))
    else:
        v3_pdf(run, cards, pages, add)

    # V4 reading record
    rr = run / "reading-record.md"
    if not rr.exists():
        add("V4", "FAIL", "reading-record.md missing")
        tags = 0
    else:
        t = rr.read_text(encoding="utf-8")
        head = t[:1500]
        miss = [k for k in FM_KEYS if k not in head]
        left = len(re.findall(r"\{\{", t))
        tags = len(TAG_RE.findall(t))
        probs = []
        if miss:
            probs.append(f"front matter missing {miss}")
        if left:
            probs.append(f"{left} leftover '{{{{' placeholder(s)")
        if tags == 0:
            probs.append("no origin tags at all")
        add("V4", "FAIL" if probs else "PASS", "; ".join(probs) if probs else f"front matter complete, no placeholders, {tags} origin tags")
        add("V6", "WARN" if tags < 15 else "PASS", f"{tags} origin tags in reading-record.md" + (" (< 15 — reads like a summary)" if tags < 15 else ""))

    # V5 key point shape — length in CJK-equivalent chars: a CJK char counts 1, an ASCII letter/digit 0.5,
    # spaces and punctuation 0 (a title full of Latin tokens like "in-situ", "Ron", "C-V" is not longer to read)
    def cjk_len(s):
        n = 0.0
        for ch in unicodedata.normalize("NFKC", s or ""):
            if ord(ch) >= 0x2E80:
                n += 1
            elif ch.isalnum():
                n += 0.5
        return n
    kp = cards.get("keypoint") or {}
    ps = kp.get("pillars") or []
    if kp:   # v1.1 runs only; the key point moved to paper-story on 2026-09-03
        probs = []
        if cjk_len(kp.get("title", "")) > 50:
            probs.append(f"title {cjk_len(kp.get('title','')):.0f} CJK-equivalent chars > 50")
        if cjk_len(kp.get("spoken", "")) > 40:
            probs.append(f"spoken {cjk_len(kp.get('spoken','')):.0f} CJK-equivalent chars > 40")
        if len(ps) != 3 or any(not p.get("text") or not p.get("locator") for p in ps):
            probs.append("pillars incomplete")
        add("V5", "WARN" if probs else "PASS", "; ".join(probs) if probs else "legacy key point block well-formed (v1.1 run)")
    else:
        add("V5", "SKIP", "no keypoint block (v1.2: the key point lives in paper-story's story.json)")

    # V7 deliverables — the evidence layer's own: the record and the contract
    need = ["reading-record.md", "cards.json"]
    miss = [n for n in need if not (run / n).exists()]
    add("V7", "FAIL" if miss else "PASS", (f"missing {miss}") if miss else "reading-record.md and cards.json present")

    # V8 numbers in the key point not found in the paper (info for the dispatcher). Numbers are
    # matched against the NFKC raw text (the alnum fold used for quotes would turn 0.8 into 08).
    raw_text = unicodedata.normalize("NFKC", txt_p.read_text(encoding="utf-8")) if txt_p.exists() else ""
    if raw_text:
        kp_text = " ".join([kp.get("title", "")] + [p.get("text", "") for p in ps])
        nums = {n for n in NUM_RE.findall(unicodedata.normalize("NFKC", kp_text))}
        absent = sorted(n for n in nums if n not in raw_text)
        add("V8", "INFO", ("numbers in the key point absent from the paper text (re-derived or wrong?): " + ", ".join(absent)) if absent else "every number in the key point occurs in the paper text")

    # V9–V12: the fields folded on 2026-09-03 (D-31; measurement plan evals/measurement-plan-new-fields-2026-09-03.md).
    # Every check SKIPs when the field is absent — runs made before the fold must not start warning.
    rr_text = (run / "reading-record.md").read_text(encoding="utf-8") if (run / "reading-record.md").exists() else ""
    rr_fold = fold(rr_text)
    # V9 glossary pass (Stage 0b): terms with a role are the glossary; verbatim, 10–15, coined terms checked
    gl = [t for t in cards.get("terms") or [] if t.get("role")]
    if not gl:
        add("V9", "SKIP", "no Stage 0b glossary (no terms[].role) — pre-fold run or triage depth")
    else:
        probs = []
        if not 10 <= len(gl) <= 15:
            probs.append(f"{len(gl)} glossary terms (Day 09 rule: 10–15)")
        if text:
            absent = [t["term"] for t in gl if fold(t["term"]) not in text]
            if absent:
                probs.append(f"terms not found verbatim in the text layer: {absent[:6]} — check the page image (absent there too = fabricated term)")
        claims_notes = fold(" ".join((c.get("notes") or "") for c in cards.get("claims") or []))
        sec4 = rr_fold[rr_fold.find(fold("## 4.")):] if fold("## 4.") in rr_fold else ""
        unchecked = [t["term"] for t in gl if t.get("role") == "coined" and fold(t["term"]) not in claims_notes and fold(t["term"]) not in sec4]
        if unchecked:
            probs.append(f"coined terms never mentioned in the claim audit (term-substitution check missing): {unchecked}")
        add("V9", "WARN" if probs else "PASS", "; ".join(probs) if probs else f"{len(gl)} glossary terms, all verbatim in the paper, coined terms checked in the audit")
        asked = [t for t in gl if t.get("ask_next")]
        if asked and rr_fold:
            after = rr_fold[rr_fold.find(fold("## 2.")):] if fold("## 2.") in rr_fold else ""
            answered = [t["term"] for t in asked if fold(t["term"]) in after]
            add("V9b", "INFO", f"ask_next: {len(answered)}/{len(asked)} glossary terms with a second-pass question reappear in §2 onward (proxy for 'answered')")
    # V10 assumptions (前提盤點): locator-or-implicit, if_false names a claim row, untested premises reach that row's missing
    asm = (cards.get("core") or {}).get("assumptions")
    if asm is None:
        add("V10", "SKIP", "no core.assumptions[] — pre-fold run")
    else:
        probs = []
        claim_ids = {c.get("id") for c in cards.get("claims") or []}
        claims_by = {c.get("id"): c for c in cards.get("claims") or []}
        for i, a in enumerate(asm):
            w = a.get("where") or ""
            if not (w == "implicit" or LOC_P.search(w) or LOC_FIG.search(w) or "§" in w or "Eq" in w):
                probs.append(f"[{i}] where is neither a locator nor 'implicit': {w!r}")
            named = set(re.findall(r"\bC\d+\b", a.get("if_false") or ""))
            if not named:
                probs.append(f"[{i}] if_false names no claim row (C1…)")
            elif named - claim_ids:
                probs.append(f"[{i}] if_false names claim rows that do not exist: {sorted(named - claim_ids)}")
            if a.get("tested") == "no":
                words = [x for x in re.findall(r"[A-Za-z]{4,}|[⺀-鿿]{2,}", a.get("premise") or "")]
                hit = any(fold(x) in fold(claims_by.get(c, {}).get("missing") or "") for c in named for x in words)
                if named and not hit:
                    probs.append(f"[{i}] tested=no but none of {sorted(named)} carries the premise in `missing`")
        add("V10", "WARN" if probs else "PASS", "; ".join(probs[:6]) if probs else f"{len(asm)} assumption rows: locators/implicit, claim refs and missing-propagation consistent")
        add("V10b", "INFO", f"assumption rows = {len(asm)} (R-2 promotion counter: ≥ 2 on two consecutive real runs → make the field required)")
    # V11 depth ruler: three axes present and consistent with the decision (reading-method.md Stage 0 q5)
    tri = (cards.get("intake") or {}).get("triage") or {}
    dr = tri.get("depth_ruler")
    if not dr:
        add("V11", "SKIP", "no intake.triage.depth_ruler — pre-fold run")
    else:
        probs = [k for k in ("relevance", "method_weight", "evidence_depth") if k not in dr]
        dec = tri.get("decision")
        if dr.get("relevance") == "low" and dec == "deep":
            probs.append("relevance=low yet decision=deep (rule: relevance low → skim)")
        if dr.get("relevance") == "high" and dec == "archive":
            probs.append("relevance=high yet decision=archive")
        add("V11", "WARN" if probs else "PASS", ("; ".join(f"missing axis {p}" if p in ("relevance", "method_weight", "evidence_depth") else p for p in probs)) if probs else f"depth ruler {dr.get('relevance')}/{dr.get('method_weight')}/{dr.get('evidence_depth')} → {dec}")
    # V12 lineage + admire: presence at full depth (an audit that lists only gaps has read half the paper)
    lin = (cards.get("position") or {}).get("lineage")
    adm = (cards.get("learning") or {}).get("admire")
    if lin is None and adm is None:
        add("V12", "SKIP", "no position.lineage / learning.admire — pre-fold run")
    else:
        probs = []
        depth = (cards.get("run") or {}).get("depth")
        if depth == "full":
            if not (lin or {}).get("group_prior_work"):
                probs.append("lineage.group_prior_work empty at full depth")
            if not adm:
                probs.append("learning.admire empty at full depth")
        add("V12", "WARN" if probs else "PASS", "; ".join(probs) if probs else "lineage and admire present")

    rows.append({"check": "TODO", "status": "HUMAN", "msg": "whole-paper test (delete a section — still stands?), author test, figure choice, talk reads as speech, craft.design_data usable — dispatcher/user judgment"})
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['check']:<4} {r['status']:<5} — {r['msg']}")
        print("VERIFY: " + ("FAIL" if any(r["status"] == "FAIL" for r in rows) else "PASS"))
    return 2 if any(r["status"] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
