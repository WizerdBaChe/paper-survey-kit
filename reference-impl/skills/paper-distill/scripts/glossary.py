#!/usr/bin/env python
"""paper-distill glossary — term-frequency CANDIDATES for the first pass, as INPUT to the reader.

Why (borrowed from IG Dc0XR8aHJwm, Day 09, 2026-09-03 — see reading-method.md B-10): the first
pass over a paper should build the paper's own glossary — 10–15 recurring terms, their
frequency, a four-way class (subject / frame / field-shared / paper-coined) and what is still
unclear — before any claim is read. Frequency and where a term first appears are
determinable from the bytes, so they are computed here; the class and the 「還不懂什麼」
column need an opinion and are filled by the reader into cards.json `terms[]`
(`role`, `unclear`, `ask_next`).

Writes <run>/source/glossary-candidates.json (or --out):
  candidates[]  term · count · score · in_title / in_abstract / in_intro · first_page · pages
  acronyms[]    ACRONYM · expansion guessed from "Long Form (ACR)" · count
  text_layer    chars, pages, language guess — 'cjk' means the ranking below is unreliable
Usage: python glossary.py --run <run_dir> [--top 40] [--out FILE] [--print] | --selftest
Exit 0 always (it is an input, not a gate); --selftest exits 1 on a failed two-sided check.

Ranking: count × (1 + 2·title + 1·abstract + 0.5·intro). Unigrams need ≥ 5 hits, n-grams
≥ 3; function words and citation noise never form a term. English text layers only —
a CJK paper is reported as such and left to the reader.
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

STOP = set("""
a an the and or but nor of in on at to for from by with without as is are was were be been being
this that these those it its their his her they them we our you your i me my he she which who whom
whose what when where why how not no yes than then there here also into onto over under between
among within upon about above below after before during while both each either neither such same
other another more most less least very much many few some any all several via per et al fig figs
figure figures table tables eq eqs equation ref refs reference references doi www http https com org
respectively however therefore thus hence moreover furthermore whereas although though because since
if unless until so too can could may might shall should will would must do does did done have has had
having use used using uses show shows shown showed see seen given give gives obtain obtained based
due able well only even still yet already again further first second third one two three four five
six seven eight nine ten et al. i.e e.g ie eg vs versus using through across along around toward
towards against out up down off new old high low large small long short good bad
""".split())
NOISE = re.compile(r"^(\d+|[a-z]|[ivx]+|\S*\d\S*)$")  # bare numbers, single letters, roman numerals, mixed digit tokens
TOKEN = re.compile(r"[A-Za-z][A-Za-z\-]*[A-Za-z]|[A-Za-z]")
ACR = re.compile(r"\(([A-Z][A-Za-z0-9\-]{1,7})\)")
PAGE = re.compile(r"<!--\s*p\.(\d+)\s*-->")
UNITS = set("nm um mm cm km MHz GHz kHz THz Hz dB mW W mA A V K ps fs ns ms s eV meV keV".split())
ROMAN = re.compile(r"^[IVX]+$")
REFS_HEAD = re.compile(r"(?im)^\s*(references(?: and links)?|bibliography|literature cited)\s*$")
INTRO_HEAD = re.compile(r"(?im)^\s*1\.?\s+introduction\b")


def fold(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "").casefold()).strip()


def prepare(text):
    """De-hyphenate line breaks (mag-\\nnetic → magnetic), unify dashes; cut the reference list when
    a References heading sits in the last 45 % of the text — journal names and author surnames
    otherwise rank as terms (Ow 2010: 'express', 'phys', 'jun')."""
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    t = t.replace("–", "-").replace("—", "-")
    # running heads / footers: a line repeated verbatim on ≥ 3 pages (Optics Express prints
    # "Received … published 1 Jun 2010" on every page — 'jun' ranked 12th on Ow 2010)
    per_page = [set(fold(ln) for ln in ptxt.splitlines() if len(ln.strip()) > 10) for _, ptxt in pages_of(t)]
    if len(per_page) >= 3:
        seen = Counter(l for s in per_page for l in s)
        rep = {l for l, c in seen.items() if c >= 3}
        if rep:
            t = "\n".join(ln for ln in t.splitlines() if fold(ln) not in rep)
    hits = list(REFS_HEAD.finditer(t))
    if not hits:
        return t
    # Optics-Express style: the list sits BEFORE the body, between "References and links" and "1. Introduction"
    first = hits[0]
    m = INTRO_HEAD.search(t, first.end())
    if m and m.start() - first.start() < 25000 and first.start() < 0.4 * len(t):
        t = t[:first.start()] + t[m.start():]
        hits = list(REFS_HEAD.finditer(t))
    if hits and hits[-1].start() > 0.55 * len(t):
        t = t[:hits[-1].start()]
    return t


def expand(acr, text):
    """Long form for 'Long Form (ACR)': the shortest suffix of the preceding words whose initials
    (hyphen parts counted separately) spell the acronym's letters; else the last len(acr) words + '?'."""
    m = re.search(r"((?:[A-Za-z][\w\-]*[\s,]+){1,8})\(" + re.escape(acr) + r"\)", text)
    if not m:
        return ""
    words = [w for w in re.split(r"[\s,]+", m.group(1).strip()) if w]
    letters = re.sub(r"[^A-Za-z]", "", acr).lower()
    flat = [p for w in words for p in w.split("-") if p]  # quasi-transverse magnetic → quasi transverse magnetic
    for seq in (words, flat):
        for k in range(1, len(seq) + 1):
            suffix = seq[-k:]
            initials = "".join(p[0].lower() for w in suffix for p in w.split("-") if p)
            if initials == letters:
                return " ".join(suffix)
    return " ".join(words[-max(1, len(letters)):]) + " ?"


def lang_guess(text):
    cjk = sum(1 for ch in text[:20000] if "一" <= ch <= "鿿")
    return "cjk" if cjk > 200 else "en"


def pages_of(text):
    """[(page_no, page_text)] from the <!-- p.N --> markers; one page when there are none."""
    parts = PAGE.split(text)
    if len(parts) < 3:
        return [(1, text)]
    out = []
    for i in range(1, len(parts) - 1, 2):
        out.append((int(parts[i]), parts[i + 1]))
    return out


def spans(text, meta_title=""):
    """title / abstract / introduction spans, best effort, on the folded text."""
    low = fold(text)
    title = fold(meta_title)
    if not title:
        head = [ln for ln in text.splitlines()[:40] if len(ln.strip()) > 20]
        title = fold(head[0]) if head else ""
    m = re.search(r"\babstract\b", low[:8000])
    a0 = m.end() if m else 0
    m2 = re.search(r"\b(1\.?\s+)?introduction\b", low[a0:])
    a1 = a0 + m2.start() if m2 else min(len(low), a0 + 3000)
    i0 = a1
    m3 = re.search(r"\n\s*(2\.?\s+[a-z]|methods?\b|experimental\b|results?\b)", low[i0 + 200:])
    i1 = i0 + 200 + m3.start() if m3 else min(len(low), i0 + 8000)
    return title, low[a0:a1], low[i0:i1]


def ngrams(tokens, n):
    for i in range(len(tokens) - n + 1):
        g = tokens[i:i + n]
        if g[0] in STOP or g[-1] in STOP or any(NOISE.match(t) for t in g):
            continue
        if n == 1 and (len(g[0]) < 3 or g[0] in STOP):
            continue
        yield " ".join(g)


def candidates(text, meta_title="", top=40):
    text = prepare(text)
    title, abstract, intro = spans(text, meta_title)
    count, first_page, pages = Counter(), {}, defaultdict(set)
    for pno, ptxt in pages_of(text):
        toks = [fold(t) for t in TOKEN.findall(ptxt)]
        toks = [t.strip("-") for t in toks]
        seen_here = set()
        for n in (1, 2, 3):
            for g in ngrams(toks, n):
                count[g] += 1
                seen_here.add(g)
        for g in seen_here:
            first_page.setdefault(g, pno)
            pages[g].add(pno)
    rows = []
    for g, c in count.items():
        n = g.count(" ") + 1
        if (n == 1 and c < 5) or (n > 1 and c < 3):
            continue
        t, a, i = int(g in title), int(g in abstract), int(g in intro)
        score = c * (1 + 2 * t + 1 * a + 0.5 * i)
        rows.append({"term": g, "n": n, "count": c, "score": round(score, 1), "in_title": bool(t),
                     "in_abstract": bool(a), "in_intro": bool(i), "first_page": first_page.get(g),
                     "pages": sorted(pages[g])[:6]})
    # a unigram that only ever occurs inside one higher-scoring n-gram is that n-gram's shadow
    by_term = {r["term"]: r for r in rows}
    shadow = set()
    for r in rows:
        if r["n"] > 1:
            for w in r["term"].split():
                u = by_term.get(w)
                if u and u["count"] <= r["count"] + 2 and u["score"] <= r["score"]:
                    shadow.add(w)
    rows = [r for r in rows if r["term"] not in shadow]
    rows.sort(key=lambda r: (-r["score"], -r["count"], r["term"]))
    acr = Counter(a for a in ACR.findall(text) if a not in UNITS and not ROMAN.match(a) and len(re.sub(r"[^A-Za-z]", "", a)) >= 2)
    acronyms = []
    for a, c in acr.most_common(30):
        total = len(re.findall(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", text))
        acronyms.append({"acronym": a, "expansion": expand(a, text), "count": total})
    return rows[:top], acronyms


def render(rows, acronyms, lang):
    out = []
    if lang == "cjk":
        out.append("text layer looks CJK — the frequency ranking below is unreliable; build the glossary by hand")
    out.append("| # | term | count | title/abs/intro | first p. | class (fill) | unclear (fill) |")
    out.append("|---|---|---|---|---|---|---|")
    for k, r in enumerate(rows, 1):
        flags = "".join(("T" if r["in_title"] else "·", "A" if r["in_abstract"] else "·", "I" if r["in_intro"] else "·"))
        out.append(f"| {k} | {r['term']} | {r['count']} | {flags} | {r['first_page']} |  |  |")
    if acronyms:
        out.append("")
        out.append("acronyms: " + "; ".join(f"{a['acronym']}={a['expansion'] or '?'} ({a['count']})" for a in acronyms[:15]))
    out.append("")
    out.append("class = subject (主角) / frame (解釋框架) / field (領域共用) / coined (本文特有 — check it against the field's standard term: claim-audit.md term substitution)")
    return "\n".join(out)


def selftest():
    """Two-sided: a recurring title term ranks in the top 5; a function word never appears; a once-only term never appears."""
    body = ("<!-- p.1 -->\nAnneal-free deuterated silane nitride waveguides\nAbstract\n"
            + "The deuterated silane process gives low loss nitride waveguides. " * 4
            + "\nReferences and links\n" + "3. K. Kim and J. Jun, Opt. Express 12, 99 (2004).\n" * 6
            + "\n1. Introduction\n" + "Deuterated silane replaces silane in the nitride deposition. " * 6
            + "The quasi-transverse magnetic (TM) mode is lossier. " * 3
            + "\n<!-- p.2 -->\n" + "The waveguide loss was measured with the ring resonator method (RRM). " * 7
            + "\n#123456 - $15.00 USD Received 15 Apr 2010; published 1 Jun 2010\n<!-- p.3 -->\n"
            + "#123456 - $15.00 USD Received 15 Apr 2010; published 1 Jun 2010\nMore body text about the waveguide.\n<!-- p.4 -->\n"
            + "#123456 - $15.00 USD Received 15 Apr 2010; published 1 Jun 2010\nMore body text about the waveguide.\n"
            + "A single-shot control appears once. The the the the the the the the the the the the.\n"
            + "The Pound-Drever-Hall (PDH) lock and the trans-\nverse electric (TE) mode were used. " * 3
            + "\nReferences\n" + "J. Jun and K. Kim, Opt. Express 18, 1234 (2010). Phys. Rev. Lett. 99, 1 (2007).\n" * 9)
    rows, acr = candidates(body, "Anneal-free deuterated silane nitride waveguides", top=40)
    terms = [r["term"] for r in rows]
    exp = {a["acronym"]: a["expansion"] for a in acr}
    fails = []
    if any(t in terms for t in ("express", "phys", "jun", "opt express", "published", "received")):
        fails.append(f"reference-list / running-footer control: noise surfaced: {[t for t in terms if t in ('express','phys','jun','opt express','published','received')]}")
    if exp.get("PDH") != "Pound-Drever-Hall":
        fails.append(f"acronym expansion control: PDH → {exp.get('PDH')!r}")
    if exp.get("TE") != "transverse electric":
        fails.append(f"de-hyphenation control: TE → {exp.get('TE')!r}")
    if exp.get("TM") != "transverse magnetic":
        fails.append(f"hyphen-prefix control: TM → {exp.get('TM')!r}")
    if "deuterated silane" not in terms[:5] or "silane" not in terms[:5]:
        fails.append("references-before-body control changed the ranking")
    if "deuterated silane" not in terms[:5]:
        fails.append(f"positive control: 'deuterated silane' not in top 5: {terms[:5]}")
    if "the" in terms:
        fails.append("negative control: function word 'the' surfaced")
    if "single-shot control" in terms or "single-shot" in terms:
        fails.append("negative control: once-only term surfaced")
    if not any(a["acronym"] == "RRM" for a in acr):
        fails.append("acronym control: RRM not found")
    print("\n".join(fails) if fails else f"selftest OK — top: {terms[:5]}; acronyms: {[a['acronym'] for a in acr]}")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.run:
        ap.error("--run is required (or --selftest)")
    src = a.run / "source"
    txt = src / "paper.txt"
    if not txt.exists():
        print(f"no text layer at {txt} — run ingest.py first", file=sys.stderr)
        return 0
    text = txt.read_text(encoding="utf-8", errors="ignore")
    meta = a.run / "_meta.json"
    title = ""
    if meta.exists():
        try:
            title = json.loads(meta.read_text(encoding="utf-8")).get("title", "") or ""
        except Exception:
            title = ""
    lang = lang_guess(text)
    rows, acronyms = candidates(text, title, a.top)
    out = a.out or (src / "glossary-candidates.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema": "paper-distill/glossary-candidates@1", "run": a.run.name,
                               "text_layer": {"chars": len(text), "pages": len(pages_of(text)), "lang": lang},
                               "candidates": rows, "acronyms": acronyms}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} candidates, {len(acronyms)} acronyms, lang={lang})", file=sys.stderr)
    if a.print:
        print(render(rows, acronyms, lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
