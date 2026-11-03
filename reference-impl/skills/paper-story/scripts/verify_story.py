#!/usr/bin/env python
"""paper-story verify_story — the dispatcher's instrument for a finished story run (never the author).

Rules only on what it can DETERMINE; judgment items are listed as TODO.
  V1  FAIL  story.json validates against assets/story.schema.json
  V2  FAIL  why-completeness: every axis why, storyline why, chain warrant non-empty and not a
            restatement (a why identical to its what, after folding, is empty)
  V3  WARN  locator existence: page numbers within range; cited Fig/Table has a caption anchor
  V4  FAIL  narrative-record.md exists, vault front matter present, no `{{` placeholders
  V5  WARN  keypoint abstraction: no digits, no unit tokens (nm µm dB % V A kV mA), ≤ 90 CJK-eq (70 → 90 on 2026-09-04:
            the slogan carries its role qualifiers, Test 0c)
  V6  WARN  deck highlights: each ≤ 48 CJK-eq; onepage table cells ≤ 120 chars; keypoint_box ≤ 80 (schema ≤ @3 only)
  V7  FAIL  deliverables present: paper-explainer.html (legacy runs: onepage.html, talk-deck.html when story.json has a deck) + story-gates.txt with RESULT: PASS; when
            story.json has deck + talk, the explainer's 口述稿 section (content file + printed heading; since 2026-11-03 there is no
            talk-script.md — a legacy run keeps requiring it); WARN when the retired 「上台要點」 section is still in the page
            (`story` mode = one page per paper authors neither)
  V8  WARN  terms: ≥ 12 for mode deep/story; every term appears in the rendered page text (glossary page excluded)
  V9  INFO  why-density in narrative-record.md (count of 為什麼/因為/warrant) — reported, not judged
  V10 INFO  generated pptx present (onepage.pptx / talk-deck.pptx): explicit-request copies in the
            HTML layout — NOT the formal deck (the lab template edited in English, lab-deck.pptx)
  V11 FAIL  quotes (renderer S10 re-run by the verifier): every drift row carries the paper's own words
            (schema @2) and every quote is found verbatim in source/paper.txt; thin text layer → WARN
  V12 WARN  coverage (S11): every unit in source/structure.json is cited or listed in coverage.skipped
  V13 WARN  anomalies (S12): every probe anomaly is addressed in drift / storyline / coverage.skipped
  V14 WARN  Conclusion cell (S4b): the author's ending + a marked 深讀判定 (ruling 2026-09-03)
  V15 WARN  drift checklist (S13): every kind of the narrative-axis.md §4 tell list found in a drift row or declared
            none in coverage.drift_checklist (schema @3; older runs: undeclared)
  V16 WARN  one-page figure kinds (S4c): every onepage figure declared; motivation figures go to the deck (OQ-1)
  V17 WARN  stray-script characters (S14) in any text field — Cyrillic/Hangul/Thai/Arabic/Hebrew/Devanagari; Greek allowed
  V18 WARN  axis.method_choice.necessity / dead_ends (D-31): [author] in necessity needs a locator; a told
            dead end carries a 「…」 fragment found in paper.txt; 「未述」 = declared absent (PASS);
            INFO when absent on a deep run, SKIP on story mode
  V19 FAIL  keypoint bindings (S15, schema @4, 2026-09-04): ≥ 3 bindings, each role verbatim in the slogan, every clause
            bound, each with a locator; older runs WARN undeclared
  V20 WARN  keypoint shape (S16): slogan ≤ 90 CJK-eq; keypoint_description present, 200–700 CJK-eq, not a restatement
  V21 WARN  brief (S18, schema @5, 2026-09-14): every method answers a question and is named up front; verdicts carry judged_by
  V22 WARN  figure reading (S19): figure pages carry look / see / means (+ against on Results) and spoken deixis
  V23 WARN  narrative flow (S20): asks / bridge in notes / takeaway; no recited highlight; key point spoken at the close (round 7); story_arc
Usage: python verify_story.py <run_dir> [--json]      exit 0 clean/WARN · 2 any FAIL
       python verify_story.py --selftest              V7 positive and negative controls
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA = SKILL_DIR / "assets" / "story.schema.json"
LOC_P = re.compile(r"\bp\.\s*(\d+)")
LOC_FIG = re.compile(r"\b(Fig\.?|Figure|Table)\s*S?(\d+)", re.I)
UNIT_RE = re.compile(r"\d|\b(nm|µm|μm|um|dB|kV|mA|mW|GHz|MHz)\b|%")
FM_KEYS = ("xi:", "what:", "tags:", "aliases:", "date:", "status:", "kind: literature", "source:", "verified:", "review-when:", "domain:", "promoted-to:")
GLOSS_RE = re.compile(r'<section class="slide" id="gloss-page">.*?</section>', re.S)


def fold(s):
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return re.sub(r"[^0-9a-z⺀-鿿㐀-䶿]+", "", s)


def cjk_len(s):
    n = 0.0
    for ch in unicodedata.normalize("NFKC", s or ""):
        if ord(ch) >= 0x2E80:
            n += 1
        elif ch.isalnum():
            n += 0.5
    return n


def strip_tags(html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def v7_deliverables(run, story):
    """V7: (status, message). The class-A HTML is paper-explainer.html (tools/carriers, since 2026-10-12); a run rendered before that
    keeps onepage/talk-deck.html and, for deck + talk, the then-current talk-script.md. Since 2026-11-03 (user ruling) the talk
    script is the explainer's 口述稿 section and talk-script.md is no longer written, so a deck + talk run is checked on the section
    (the content file's section `script` holds blocks and the built page prints the heading), not on a file; an old talk-script.md
    is neither required nor judged. A stale 「上台要點」 section (retired the same day) is a WARN: the page needs a rebuild."""
    run = Path(run)
    explainer = run / "paper-explainer.html"
    legacy = not explainer.exists() and (run / "onepage.html").exists()
    html_need = (["onepage.html"] + (["talk-deck.html"] if "deck" in story else [])) if legacy else ["paper-explainer.html"]
    deep_talk = "deck" in story and "talk" in story
    need = html_need + ["story-gates.txt"] + (["talk-script.md"] if (legacy and deep_talk) else [])
    miss = [n for n in need if not (run / n).exists()]
    res = (run / "story-gates.txt").read_text(encoding="utf-8") if (run / "story-gates.txt").exists() else ""
    probs, warns = [], []
    if miss:
        probs.append(f"missing {miss}")
    if "RESULT: PASS" not in res:
        probs.append("gates not PASS")
    script_note = ""
    cf = run / "paper-explainer.explainer.json"
    if not legacy and explainer.exists() and deep_talk:
        sec = None
        try:
            c = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else None
        except ValueError:
            c = None
        if c is None:
            probs.append("paper-explainer.explainer.json missing or unreadable — cannot see the 口述稿 section")
        else:
            sec = next((s for s in c.get("sections", []) if s.get("id") == "script" and s.get("heading") == "口述稿"), None)
            if not sec or not sec.get("blocks"):
                probs.append("the explainer has no 口述稿 section with content (deck + talk run)")
            elif "口述稿" not in strip_tags(explainer.read_text(encoding="utf-8")):
                probs.append("paper-explainer.html does not print the 口述稿 heading (stale build)")
            else:
                script_note = "; explainer 口述稿 section present"
            if any(s.get("id") == "talk" or s.get("heading") == "上台要點" for s in c.get("sections", [])):
                warns.append("the explainer still carries the retired 「上台要點」 section — rebuild with render_story.py")
    if probs:
        return "FAIL", "; ".join(probs)
    msg = "story-gates.txt RESULT is PASS" + script_note
    if warns:
        return "WARN", msg + "; " + "; ".join(warns)
    return "PASS", msg


def selftest():
    """Two-sided controls for V7: the positive controls (defects that MUST fire) and the negative controls (good inputs that MUST pass)."""
    import tempfile
    deep = {"deck": {}, "talk": {}}
    good_cf = {"sections": [{"id": "script", "heading": "口述稿", "blocks": [{"type": "para", "text": "**開場**：x"}]}]}

    def mk(root, name, *, cf=good_cf, html="<html><h2>口述稿</h2></html>", gates="RESULT: PASS", extra=()):
        d = Path(root) / name
        d.mkdir()
        (d / "story-gates.txt").write_text(gates, encoding="utf-8")
        if html is not None:
            (d / "paper-explainer.html").write_text(html, encoding="utf-8")
        if cf is not None:
            (d / "paper-explainer.explainer.json").write_text(json.dumps(cf, ensure_ascii=False), encoding="utf-8")
        for n in extra:
            (d / n).write_text("x", encoding="utf-8")
        return d

    rows = []
    with tempfile.TemporaryDirectory() as td:
        stale = {"sections": good_cf["sections"] + [{"id": "talk", "heading": "上台要點", "blocks": [{"type": "para", "text": "x"}]}]}
        cases = [   # (name, run dir, story, expected status, fragment of the message)
            ("good: section present, no talk-script.md (NEGATIVE control, must PASS)", mk(td, "a"), deep, "PASS", "口述稿 section present"),
            ("good: old talk-script.md lying around is ignored", mk(td, "b", extra=("talk-script.md",)), deep, "PASS", "口述稿 section present"),
            ("good: story mode needs no script section", mk(td, "c", cf={"sections": []}), {}, "PASS", "RESULT is PASS"),
            ("bad: no 口述稿 section (POSITIVE control, must FAIL)", mk(td, "d", cf={"sections": [{"id": "talk", "heading": "上台要點", "blocks": [{"type": "para", "text": "x"}]}]}), deep, "FAIL", "no 口述稿 section"),
            ("bad: content file missing", mk(td, "e", cf=None), deep, "FAIL", "explainer.json missing"),
            ("bad: html lacks the heading (stale build)", mk(td, "f", html="<html><h2>x</h2></html>"), deep, "FAIL", "stale build"),
            ("bad: gates not PASS", mk(td, "g", gates="RESULT: FAIL"), deep, "FAIL", "gates not PASS"),
            ("warn: retired 上台要點 still in the page", mk(td, "h", cf=stale), deep, "WARN", "上台要點"),
        ]
        legacy = Path(td) / "L"
        legacy.mkdir()
        for n in ("onepage.html", "talk-deck.html", "story-gates.txt"):
            (legacy / n).write_text("RESULT: PASS" if n.endswith(".txt") else "<html></html>", encoding="utf-8")
        cases.append(("legacy run without talk-script.md still FAILS (historical contract)", legacy, deep, "FAIL", "talk-script.md"))
        for name, d, st, want, frag in cases:
            got, msg = v7_deliverables(d, st)
            rows.append((name, got == want and frag in msg, f"want {want}, got {got}: {msg[:90]}"))
    for name, ok, detail in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {name} — {detail}")
    good = all(ok for _, ok, _ in rows)
    print("SELFTEST: " + ("PASS" if good else "FAIL"))
    return 0 if good else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__); return 1
    if argv[0] == "--selftest":
        return selftest()
    run = Path(argv[0]); as_json = "--json" in argv
    rows = []
    add = lambda v, s, m: rows.append({"check": v, "status": s, "msg": m})
    sp = run / "story.json"
    if not sp.exists():
        add("V1", "FAIL", "story.json missing")
        print("\n".join(f"{r['check']} {r['status']} — {r['msg']}" for r in rows)); return 2
    story = json.loads(sp.read_text(encoding="utf-8"))

    try:
        import jsonschema
        errs = list(jsonschema.Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(story))
        add("V1", "FAIL" if errs else "PASS", (f"{len(errs)} violation(s): " + "; ".join(f"{'/'.join(str(p) for p in e.path)}: {e.message[:80]}" for e in errs[:4])) if errs else "story.json valid")
    except ImportError:
        add("V1", "WARN", "jsonschema not installed")

    # V2 whys
    empty = []
    ax = story.get("axis", {})
    for k, v in ax.items():
        w = v.get("why") or v.get("why_matters") or ""
        if not w.strip():
            empty.append(f"axis.{k}")
        elif fold(w) == fold(v.get("what", "")):
            empty.append(f"axis.{k} (why restates what)")
    for i, b in enumerate(story.get("storyline", [])):
        if not b.get("why", "").strip() or fold(b["why"]) == fold(b.get("what", "")):
            empty.append(f"storyline[{i}]")
    for i, c in enumerate(story.get("logic", {}).get("chain", [])):
        if not c.get("warrant", "").strip() or fold(c["warrant"]) == fold(c.get("step", "")):
            empty.append(f"chain[{i}].warrant")
    add("V2", "FAIL" if empty else "PASS", ("whys missing or empty: " + ", ".join(empty)) if empty else "every axis item, beat and chain link carries a why that is not a restatement")

    # V3 locators
    anchors, pages = set(), 0
    fj = run / "source" / "figures.json"
    if fj.exists():
        d = json.loads(fj.read_text(encoding="utf-8")); pages = d.get("pages", 0)
        anchors = {(c["kind"], c["num"]) for c in d.get("captions", [])}
    bad_p, bad_f = set(), set()
    def scan(s, where):
        for m in LOC_P.finditer(s or ""):
            if pages and int(m.group(1)) > pages:
                bad_p.add(f"p.{m.group(1)}@{where}")
        for m in LOC_FIG.finditer(s or ""):
            kind = "table" if m.group(1).lower().startswith("tab") else "figure"
            if anchors and (kind, int(m.group(2))) not in anchors:
                bad_f.add(f"{m.group(1)} {m.group(2)}")
    for k, v in ax.items():
        scan(v.get("locator", ""), f"axis.{k}")
    for i, b in enumerate(story.get("storyline", [])):
        scan(b.get("locator", ""), f"storyline[{i}]")
    for i, c in enumerate(story.get("logic", {}).get("chain", [])):
        scan(c.get("backing", ""), f"chain[{i}]")
    for i, f in enumerate(story.get("onepage", {}).get("figures", [])):
        scan(f.get("locator", ""), f"onepage.figures[{i}]")
    if not pages and not anchors:
        add("V3", "SKIP", "no source/figures.json — locator existence not determinable")
    elif bad_p:
        add("V3", "FAIL", f"page locators beyond {pages} pages: {sorted(bad_p)[:6]}")
    elif bad_f:
        add("V3", "WARN", f"figure/table locators without caption anchor: {sorted(bad_f)} — check by eye")
    else:
        add("V3", "PASS", f"page locators ≤ {pages}; cited figures/tables anchored")

    # V4 record
    rr = run / "narrative-record.md"
    if not rr.exists():
        add("V4", "FAIL", "narrative-record.md missing"); why_density = 0
    else:
        t = rr.read_text(encoding="utf-8"); head = t[:1500]
        miss = [k for k in FM_KEYS if k not in head]; left = len(re.findall(r"\{\{", t))
        probs = ([f"front matter missing {miss}"] if miss else []) + ([f"{left} leftover placeholder(s)"] if left else [])
        add("V4", "FAIL" if probs else "PASS", "; ".join(probs) if probs else "front matter complete, no placeholders")
        why_density = len(re.findall(r"為什麼|因為|warrant", t))

    # V5 keypoint abstraction
    kp = story.get("logic", {}).get("keypoint", "")
    probs = []
    if UNIT_RE.search(kp):
        probs.append("keypoint contains digits or units — not abstract")
    if cjk_len(kp) > 90:
        probs.append(f"keypoint {cjk_len(kp):.0f} CJK-eq > 90")
    add("V5", "WARN" if probs else "PASS", "; ".join(probs) if probs else "keypoint is abstract (no digits/units) and ≤ 90")

    # V6 lengths
    probs = []
    for i, pg in enumerate(story.get("deck", {}).get("pages", [])):
        for h in pg.get("highlights", []):
            if cjk_len(h) > 48:
                probs.append(f"page {i+1} highlight {cjk_len(h):.0f} > 48")
    for k, v in story.get("onepage", {}).get("table", {}).items():
        if len(v) > 120:
            probs.append(f"table.{k} {len(v)} chars > 120")
    sv = int((re.search(r"@(\d+)$", str(story.get("schema", ""))) or re.match(r"(1)", "1")).group(1))
    if sv < 4 and cjk_len(story.get("onepage", {}).get("keypoint_box", "")) > 80:
        probs.append("keypoint_box > 80")
    add("V6", "WARN" if probs else "PASS", "; ".join(probs[:6]) if probs else "highlights, table cells and keypoint box within budget")

    # V7 deliverables
    add("V7", *v7_deliverables(run, story))

    # V8 terms
    terms = story.get("terms", [])
    html_text = ""
    for n in ("onepage.html", "talk-deck.html", "paper-explainer.html"):
        p = run / n
        if p.exists():
            h = re.sub(r'<section[^>]*id="x_glossary".*?</section>', " ", p.read_text(encoding="utf-8"), flags=re.S)
            html_text += strip_tags(GLOSS_RE.sub(" ", h))   # glossary page / section excluded (U-6)
    ft = fold(html_text)
    unused = [t["term"] for t in terms if html_text and fold(t["term"]) not in ft]
    probs = []
    if story.get("run", {}).get("mode") in ("deep", "story") and len(terms) < 12:
        probs.append(f"only {len(terms)} terms (< 12)")
    if unused:
        probs.append(f"terms never rendered: {unused[:8]}")
    add("V8", "WARN" if probs else "PASS", "; ".join(probs) if probs else f"{len(terms)} terms, all appear in the rendered pages")
    add("V9", "INFO", f"why-density in narrative-record.md: {why_density} occurrences of 為什麼/因為/warrant")
    gen = [n for n in ("onepage.pptx", "talk-deck.pptx") if (run / n).exists()]
    if gen:
        add("V10", "INFO", f"generated pptx present {gen}: story.json→pptx copies in the HTML layout (explicit request only) — the formal deck is lab-deck.pptx from the lab template, English; not these")
    # V11–V14: the source-anchored gates, re-run here so the verifier does not trust the author's gate file
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    import render_story as R
    G = R.Gates()
    R.s10_quotes(story, run, G); stj = R.s11_coverage(story, run, G); R.s12_anomalies(story, stj, G); R.s4b_conclusion(story, G)
    R.s13_drift_checklist(story, G); R.s4c_figure_kinds(story, G); R.s14_stray_script(story, G)
    G2 = R.Gates(); R.s15_bindings(story, G2); R.s16_description(story, G2)
    R.s18_brief(story, G2); R.s19_figure_reading(story, G2); R.s20_flow(story, G2)
    for g, s, m in G.rows + G2.rows:
        add({"S10": "V11", "S11": "V12", "S12": "V13", "S4b": "V14", "S13": "V15", "S4c": "V16", "S14": "V17", "S15": "V19", "S16": "V20",
             "S18": "V21", "S19": "V22", "S20": "V23"}[g], "INFO" if s == "SKIP" else s, m)
    # V18 necessity / dead_ends (D-31, 2026-09-03; measurement plan in paper-distill/evals/measurement-plan-new-fields-2026-09-03.md)
    mc = (story.get("axis") or {}).get("method_choice") or {}
    nec, de = mc.get("necessity"), mc.get("dead_ends")
    txt_p = run / "source" / "paper.txt"
    ptxt = fold(txt_p.read_text(encoding="utf-8", errors="ignore")) if txt_p.exists() else ""
    if nec is None and de is None:
        add("V18", "INFO" if story.get("run", {}).get("mode") == "deep" else "SKIP",
            "necessity / dead_ends not filled" + (" — expected on deep runs after 2026-09-03 (D-31)" if story.get("run", {}).get("mode") == "deep" else ""))
    else:
        probs = []
        if nec is not None:
            if "[author]" in nec and not (LOC_P.search(nec) or LOC_FIG.search(nec) or "§" in nec):
                probs.append("necessity carries [author] but no locator")
            if not nec.strip():
                probs.append("necessity empty")
        if de is not None:
            d = de.strip()
            if d and not re.match(r"^(未述|none|not told)", d):
                quotes = re.findall(r"[「“\"]([^」”\"]{6,})[」”\"]", d)
                if not quotes:
                    probs.append("dead_ends tells a failure but carries no quoted fragment 「…」 to look up")
                elif ptxt and not any(fold(q) in ptxt for q in quotes):
                    probs.append(f"dead_ends quote not found in the text layer: {quotes[0][:40]!r} — check the page image")
        add("V18", "WARN" if probs else "PASS", "; ".join(probs) if probs else
            ("necessity present" if nec else "") + ("; " if nec and de is not None else "") + (("dead_ends: 未述 (declared absent)" if de is not None and re.match(r"^(未述|none|not told)", de.strip()) else "dead_ends quoted and found") if de is not None else ""))

    rows.append({"check": "TODO", "status": "HUMAN", "msg": "is the entry-point why the real one? does the keypoint read as reusable logic AND can every role be placed from the slogan alone (Test 0c)? does keypoint_description read as the 讀書心得終極詮釋 without the paper? are highlights 重點提醒 not essays? does the talk sound like the lab?"})
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['check']:<4} {r['status']:<5} — {r['msg']}")
        print("VERIFY: " + ("FAIL" if any(r["status"] == "FAIL" for r in rows) else "PASS"))
    return 2 if any(r["status"] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
