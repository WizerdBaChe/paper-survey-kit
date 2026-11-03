"""html-explainer gates: gates(out_path) -> [(name, ok, detail), ...]. Never raises.

  fill_gate  runs tools/page-fill-gate/fill_gate.py on the BUILT file (its own known-bad / known-good
             controls run inside every invocation). A FAIL row, an inferred page class or an absent
             instrument (exit 2) is ok=False, because an unmeasured page is not a deliverable; so is a
             width WARN. A consistency-only WARN passes and its reasons are carried into the detail
             (user ruling 2026-11-02, sheet B2).
  main_fill  carrier-owned width check (added 2026-10-09): fill_gate's reach is satisfied by the rail / hint
             bar even when <main> is capped, so this measures <main> itself against the width left beside the
             fixed nav and rail (>= 85 %, the document-long min_fill) at the registry's reference viewports.
  structure  checks the file against itself: page class declared, one section.ch per content section
             (the ids are written into <main data-sections>, since the gate receives only the output),
             no unresolved "[[" marker left in the file, no resource that loads from outside the file,
             unique ids, every in-page link and every hover-card key resolves, and the shell's DOM
             contract (#side, #rail[data-rail], #railhead, #railbody, #hint .hx, #gloss, #refcard, #pins,
             #backpill, script#previews) is present.

Limit (said plainly): `structure` cannot compare against the content file because build.py hands gates
only the output path; it proves the file is internally consistent, not that it says what the content says.
"""
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

FILL_GATE = Path(__file__).resolve().parents[2] / "page-fill-gate" / "fill_gate.py"

_LOAD_ATTRS = ("src", "srcset", "data", "poster")
_CSS_LOAD = re.compile(r"@import|url\(\s*['\"]?(?!data:|#)", re.I)
_REGISTRY = re.compile(r"window\.SITE_REFS = (\{.*?\});\nwindow\.SITE_SYMS = (\{.*?\});</script>", re.S)
CONTRACT_IDS = ("side", "rail", "railhead", "railbody", "hint", "gloss", "glosslist", "refcard", "pins", "backpill",
                "previews", "rail-data")


def gates(out_path):
    out = []
    for name, fn in (("fill_gate", _fill_gate), ("main_fill", _main_fill), ("structure", _structure)):
        try:
            ok, detail = fn(Path(out_path))
        except Exception as e:  # a gate that cannot run is a failed gate, never a silent pass
            ok, detail = False, f"gate crashed: {type(e).__name__}: {str(e)[:200]}"
        out.append((name, bool(ok), detail))
    return out


# fill_gate marks these in consistency_reasons: a FAIL it downgraded at an advisory viewport (a
# promoted, human-reported defect), and a consistency stage that crashed (the page was not measured).
_CONS_BLOCKING = ("advisory viewport — FAIL downgraded", "consistency not computed")


def _blocks(r):
    """True when a fill_gate row is a real failure (user ruling 2026-11-02, sheet B2)."""
    if r.get("status") not in ("PASS", "WARN"):
        return True
    if r.get("width_status", r.get("status")) != "PASS":
        return True
    return any(str(x).startswith(_CONS_BLOCKING) for x in r.get("consistency_reasons") or [])


def _fill_gate(path):
    if not FILL_GATE.is_file():
        return False, f"instrument missing: {FILL_GATE} (UNDET - the page was not measured)"
    p = subprocess.run([sys.executable, "-X", "utf8", str(FILL_GATE), "--json", str(path)],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    if p.returncode == 2:
        return False, "instrument unavailable (fill_gate exit 2: Playwright/Chromium absent) - UNDET, the page was not measured"
    try:
        rows = json.loads(p.stdout)
    except Exception:
        return False, f"fill_gate printed no JSON (exit {p.returncode}): {(p.stderr or p.stdout)[:200]!r}"
    target = [r for r in rows if r.get("control") is None]
    if not target:
        return False, "fill_gate returned no row for the built file"
    # Block only on a real failure (user ruling 2026-11-02, decision sheet feedback-review B2): a FAIL
    # row, or a width WARN (left-anchored blocks: a measured defect this carrier always blocked,
    # control e). A consistency-only WARN is the gate saying it could not rule; it goes into the report.
    bad = [r for r in target if _blocks(r)]
    warned = [r for r in target if r.get("status") == "WARN" and not _blocks(r)]
    summary = ", ".join(f"{r['viewport']} reach={r['reach']:.0%}" for r in target)
    if p.returncode != 0 or bad:
        why = "; ".join(f"{r['viewport']} {r['status']}: {'; '.join(r.get('reasons', []))}" for r in bad) or f"exit {p.returncode}"
        return False, why
    declared = {r.get("class") for r in target}
    if any(r.get("inferred") for r in target):
        return False, "page class was inferred, not declared"
    note = ""
    if warned:
        note = " | WARN (reported, not blocking): " + "; ".join(
            f"{r['viewport']}: {'; '.join(r.get('reasons', []))}" for r in warned)
    return True, f"class={','.join(sorted(declared))} {summary}{note}"


_MAIN_JS = """() => {
  const vis = el => { if (!el) return null; const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return null;
    const r = el.getBoundingClientRect(); return r.width > 0 ? r : null; };
  const fixed = el => el && getComputedStyle(el).position === 'fixed';
  const side = vis(document.getElementById('side')), rail = vis(document.getElementById('rail'));
  const W = document.documentElement.clientWidth, m = document.querySelector('main').getBoundingClientRect();
  return {W: W, side: side && fixed(document.getElementById('side')) ? side.right : 0,
          rail: rail && fixed(document.getElementById('rail')) ? W - rail.left : 0, main: m.width};
}"""
MAIN_MIN_RATIO = 0.85   # same threshold as the document-long row of page_classes.json (min_fill)


def _main_fill(path):
    """The main column must take >= 85 % of the width left after the fixed nav and rail, at every reference
    viewport. Added because fill_gate cannot see a capped <main> on this shell: the rail (>= 1500 px) and the
    hint bar's text span (below that) both sit at the right edge and count as content, so reach stays ~100 %."""
    reg = json.loads((FILL_GATE.parent / "page_classes.json").read_text(encoding="utf-8"))
    views = [tuple(v) for v in reg["reference_viewports"]["gating"] + reg["reference_viewports"]["advisory"]]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        return False, f"instrument unavailable ({e}) - UNDET, main column not measured"
    rows = []
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as e:
            return False, f"instrument unavailable (chromium: {str(e)[:80]}) - UNDET, main column not measured"
        for w, h in views:
            page = browser.new_page(viewport={"width": w, "height": h})
            try:
                page.route("http://**", lambda r: r.abort())
                page.route("https://**", lambda r: r.abort())
                page.goto(path.resolve().as_uri(), wait_until="load", timeout=60000)
                page.wait_for_timeout(300)
                m = page.evaluate(_MAIN_JS)
            finally:
                page.close()
            avail = m["W"] - m["side"] - m["rail"]
            rows.append((w, h, m["main"] / avail if avail > 0 else 0.0, m["main"], avail))
        browser.close()
    bad = [r for r in rows if r[2] < MAIN_MIN_RATIO]
    desc = ", ".join(f"{w}x{h} main={mw:.0f}px of {av:.0f}px ({ra:.0%})" for w, h, ra, mw, av in rows)
    if bad:
        return False, f"main column under {MAIN_MIN_RATIO:.0%} of the width left beside nav and rail: {desc}"
    return True, desc


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_attrs, self.mains, self.ids, self.hrefs, self.loads = None, [], [], [], []
        self.sections, self.keys = [], []          # sections: dict(id, kind, h2)
        self._sec, self._h2, self._style, self.rail_attrs = None, False, False, None
        self.hx = self.panel = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_attrs = a
        if a.get("id"):
            self.ids.append(a["id"])
        cls = (a.get("class") or "").split()
        if tag == "main":
            self.mains.append(a)
        if tag == "section" and "ch" in cls:
            self._sec = {"id": a.get("id"), "kind": a.get("data-kind"), "h2": ""}
            self.sections.append(self._sec)
        if tag == "h2" and self._sec is not None:
            self._h2 = True
        if a.get("id") == "rail":
            self.rail_attrs = a
        if tag == "button" and "hx" in cls:
            self.hx = True
        if "panel" in cls:
            self.panel = True
        if tag == "a" and a.get("href") is not None:
            self.hrefs.append(a["href"])
        if tag == "span" and ("sym" in cls or "ref" in cls) and "data-key" in a:
            self.keys.append(("ref" if "ref" in cls else "sym", a["data-key"]))
        if tag == "style":
            self._style = True
        if "style" in a and a["style"] and _CSS_LOAD.search(a["style"]):
            self.loads.append(f"<{tag} style=url(...)>")
        for k in _LOAD_ATTRS:
            v = a.get(k)
            if v is not None and tag in ("img", "script", "iframe", "source", "video", "audio", "embed", "track", "object", "input") \
                    and not v.strip().lower().startswith("data:"):
                self.loads.append(f"<{tag} {k}={v[:60]!r}>")
        if tag == "link" and a.get("href") is not None and not a["href"].strip().lower().startswith("data:"):
            self.loads.append(f"<link href={a['href'][:60]!r}>")

    def handle_endtag(self, tag):
        if tag == "h2":
            self._h2 = False
        if tag == "section":
            self._sec = None
        if tag == "style":
            self._style = False

    def handle_data(self, data):
        if self._h2 and self._sec is not None:
            self._sec["h2"] += data
        if self._style and _CSS_LOAD.search(data):
            self.loads.append("<style> @import / url(non-data)")


def _structure(path):
    raw = path.read_text(encoding="utf-8")
    problems = []
    s = _Scan()
    s.feed(raw)
    s.close()

    ha = s.html_attrs or {}
    if not (ha.get("data-page-class") or "").strip():
        problems.append("<html> has no data-page-class")
    if not ha.get("lang"):
        problems.append("<html> has no lang")
    if "</head>" not in raw:
        problems.append("no </head>")
    if len(s.mains) != 1 or "</main>" not in raw:
        problems.append(f"expected exactly one <main>...</main>, found {len(s.mains)}")

    expected = []
    if len(s.mains) == 1:
        expected = [x for x in (s.mains[0].get("data-sections") or "").split(",") if x]
        if not expected:
            problems.append("<main> has no data-sections list (cannot count content sections)")
    content = [x for x in s.sections if x["kind"] == "content"]
    others = [x for x in s.sections if x["kind"] != "content"]
    if [x["id"] for x in content] != expected:
        problems.append(f"content sections {[x['id'] for x in content]} != data-sections {expected}")
    for x in s.sections:
        if not (x["h2"] or "").strip():
            problems.append(f"section {x['id']!r} has no h2 text")
    for k in ("glossary", "refs"):
        if sum(1 for x in others if x["kind"] == k) > 1:
            problems.append(f"more than one {k} section")
    stray = [x["id"] for x in others if x["kind"] not in ("glossary", "refs")]
    if stray:
        problems.append(f"section.ch with unknown data-kind: {stray}")

    # only the inline-markup grammar counts; a literal "[[" (bash, wiki links) in prose is legitimate
    left = list(re.finditer(r"\[\[[grs]:", raw))
    if left:
        i = left[0].start()
        problems.append(f"{len(left)} unresolved '[[' marker(s) left, first: {raw[i:i + 30]!r}")

    if s.loads:
        problems.append(f"{len(s.loads)} resource(s) load from outside the file: {s.loads[:3]}")

    dup = sorted({i for i in s.ids if s.ids.count(i) > 1})
    if dup:
        problems.append(f"duplicate ids {dup[:5]}")
    idset = set(s.ids)
    dangling = sorted({h for h in s.hrefs if h.startswith("#") and h[1:] not in idset})
    if dangling:
        problems.append(f"in-page links without a target: {dangling[:5]}")

    for i in CONTRACT_IDS:
        if i not in idset:
            problems.append(f"shell contract: #{i} missing")
    if s.rail_attrs is not None and "data-rail" not in s.rail_attrs:
        problems.append("shell contract: #rail has no data-rail")
    if not s.hx:
        problems.append("shell contract: '#hint .hx' close button missing")
    if not s.panel:
        problems.append("shell contract: '#gloss .panel' missing")

    m = _REGISTRY.search(raw)
    if not m:
        problems.append("window.SITE_REFS / SITE_SYMS assignments not found in the expected shape")
    else:
        try:
            reg = {"ref": json.loads(m.group(1)), "sym": json.loads(m.group(2))}
        except Exception as e:
            reg = None
            problems.append(f"SITE_REFS / SITE_SYMS are not valid JSON: {e}")
        if reg is not None:
            for kind, key in s.keys:
                if key not in reg[kind]:
                    problems.append(f"{kind} token {key!r} has no registry entry")
            for kind in ("ref", "sym"):
                for key, e in reg[kind].items():
                    if not (isinstance(e, dict) and all(f in e for f in ("t", "d", "s", "n"))):
                        problems.append(f"{kind} entry {key!r} lacks t/d/s/n")
                    elif e["s"].startswith("#") and e["s"][1:] not in idset:
                        problems.append(f"{kind} entry {key!r} jumps to missing {e['s']}")

    if problems:
        return False, "; ".join(problems[:6]) + (f" (+{len(problems) - 6} more)" if len(problems) > 6 else "")
    return True, (f"class={ha['data-page-class']}, {len(content)} content section(s) + {len(others)} appendix, "
                  f"{len(s.keys)} hover token(s) resolved, {len(s.hrefs)} link(s) checked, no external loads")
