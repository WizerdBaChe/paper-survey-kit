#!/usr/bin/env python
"""paper-story renderer — story.json -> paper-explainer.html (since 2026-10-12: ONE explainer page built by
story_explainer.py through tools/carriers html-explainer), story-gates.txt.
onepage.html / talk-deck.html are retired: still built in memory for S6, written only with --legacy-html.
Since 2026-11-03 (user ruling) the talk script (lab speaker-notes voice) is the explainer's 口述稿 section and the PPTX speaker
notes; talk-script.md is no longer written (one already in a run folder is left untouched). story@6 adds the argument-step
tiles of the story-mode one-page (S4 per-mode count, S4d), onepage.fields four|five and onepage.script.

PRODUCT CLASSES (user ruling 2026-09-03): the HTML products are the USER's practice /
learning / quick-review copies — readable, not presentable. The formal talk deck is the
lab's PPTX template edited in English (references/formal-deck.md) and is NEVER made by
converting these HTML products. `--pptx-from-story` (alias `--pptx`) builds
onepage.pptx / talk-deck.pptx in the HTML layout ONLY on the user's explicit request;
the gate file then carries an INFO row (P0) saying so.

Deliverables are WRITTEN FIRST, gates run AFTER (persist what a gate may reject). Exit 2 on FAIL.

Gates (severity by consumer — memory/gate-severity-by-consumer.md):
  S1 FAIL schema · S2 FAIL why-completeness (the user's core requirement) · S3 FAIL locators
  S4 FAIL one-page shape (3–6 existing figures, five table cells; story@6: four or five per onepage.fields, story mode 3–4 tiles
     + at most 1 side-evidence tile, every file of a tile exists, side-evidence carries necessity) / WARN cell length
  S4d WARN (story@6, story mode only; SKIP elsewhere) a results table used as a tile, or a tile with no argument step
  S5 FAIL deck shape (≥5 pages, Keypoint within the first 3 pages — round 5) / WARN highlight length
  S6 WARN terms coverage · S7 FAIL/WARN measured fit (Playwright, both HTML products, two-sided controls)
  S7b FAIL/WARN measured fill (width property 2026-09-04: ~/.claude/tools/page-fill-gate, class deck, two-sided controls)
  S8 WARN shell drift · S9 WARN talk conventions (formula, outline N vs parts vs Cover bullets)
  S4b WARN Conclusion cell carries the author's ending + a marked 深讀判定 (ruling 2026-09-03)
  S10 FAIL quotes: every drift row carries the paper's own words (schema @2) and every quote is found
      verbatim in source/paper.txt (folded); thin text layer → WARN, verify on the page image
  S11 WARN coverage: every unit in source/structure.json (probe.py) is cited by a locator or listed in
      coverage.skipped with a why · S12 WARN every probe anomaly is addressed in drift/storyline/skipped
  S13 WARN drift checklist (schema @3, co-upgrade round 1 2026-09-03): every kind of the narrative-axis.md §4 tell
      list is found in a drift row (drift[].kind) or declared none in coverage.drift_checklist — a checklist not
      declared is a checklist not walked · S4c WARN one-page figure kinds (onepage.figures[].kind): evidence and the
      paper's own schematic may stay, MOTIVATION figures are deck-only (user rulings Gb9 + OQ-1, 2026-09-03)
  S14 WARN stray-script characters (Cyrillic/Hangul/Thai/Arabic/Hebrew/Devanagari) in any text field — round 2 (run S3)
  S15 FAIL keypoint bindings (schema @4, user finding 2026-09-04): every role of the slogan is bound to the paper's referent —
      ≥ 3 bindings, each role a verbatim substring of logic.keypoint, every clause (split on ；) has a bound role, each with a
      locator; older runs WARN "undeclared". Whether the bindings are the RIGHT ones is the readback test's job (evals)
  S16 WARN keypoint shape: the slogan ≤ 90 CJK-eq; keypoint_description present, 200–700 CJK-eq, not a restatement — the
      讀書心得終極詮釋 the practice copies print (strip toggle, 解讀 page, deck Keypoint page). S4 WARNs when a @4 run still
      carries onepage.keypoint_box (the field invited a second compression; the strip prints logic.keypoint verbatim)
  Round-2 additions (2026-09-03, schema @3 optional fields): quote_source "page-image" turns a not-found quote into a
      WARN the dispatcher checks on the page image (run S2: the text layer missed a whole abstract); coverage.checklist_provenance
      "backfilled" marks a none as "no row", not a search; logic.reused_from cites the deep run whose key point a story-mode
      page reuses (run S1); Cover highlights may hold up to 6 outline parts (run Z hit the 3-item cap); qfold folds U+2212.
  Round 4 (2026-09-14, schema @5 — the advisor's emphasis: 一開始說明為什麼讀、所有方法、有沒有達到、怎麼判讀; 圖是第一優先
      而且要解釋; 論文怎麼說完一個研究故事 — and the user's finding that the notes read 生硬, facts without transitions):
  S18 WARN brief: every method answers a question and carries a locator, every verdict carries judged_by + result + locator,
      every method NAME is spoken on the front pages (opening + Keypoint / Verdict / Cover notes), a Verdict page sits among the
      first three pages. Promotion trigger: a listener asks 「所以到底有沒有做到／怎麼判讀的」 on a run S18 passed → FAIL
  S19 WARN figure reading: a figure page carries figure_read look / see / means (+ against on Results) and its notes point at
      the figure (axes, panels, 這張圖…); an Introduction / Method / Results page without a figure says why (no_figure).
      Promotion trigger: the presenter is asked 「這張圖在看什麼」 on a page S19 passed → FAIL
  S20 WARN narrative flow: every page after the Outline carries asks / bridge / takeaway, the bridge is inside the notes, the
      notes recite no highlight and carry ≥ 2 distinct connectives, the slogan is spoken at the close (round 7), story_arc has a
      spine and ≥ 4 craft steps each with why_it_works, and a Storyline page renders it. Connectives and deixis are PROXIES of
      a told story, not proof — the blind A/B read (round 4 record) is the instrument that judged the voice.
      Promotion trigger: a second run whose notes pass S20 is still called 生硬 by the user → replace the proxy, not tune it
  S18–S20 SKIP on schema < @5 runs that declare none of the fields, so accepted older runs stay quiet.
  P1 FAIL pptx text gates (only with --pptx-from-story)
Usage:
  python render_story.py --run <run_dir> [--fit-check] [--check-shell] [--presenter NAME] [--no-gates] [--pptx-from-story]
  python render_story.py --selftest [--keep DIR]
  python render_story.py --make-sample <dir> [--fit-check] [--pptx-from-story]
"""
import argparse
import base64
import datetime as dt
import hashlib
import html as H
import json
import math
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path
import sys as _hksys  # machine roots at run time (platform/codemod_roots.py, build plan H-1)
from pathlib import Path as _HKPath
_hksys.path.insert(0, str(_HKPath(__file__).resolve().parents[3] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRIPTS = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS.parent
SHELL = SKILL_DIR / "assets" / "deck-shell.html"
SHELL_SHA = SKILL_DIR / "assets" / "deck-shell.sha256"
SCHEMA = SKILL_DIR / "assets" / "story.schema.json"
SAMPLE = SKILL_DIR / "evals" / "fixtures" / "sample-story.json"
VAULT_SHELL = hkroots.path("WORK_ROOT", "AssetVault", "assets", "pattern-template", "html-css", "briefing-deck-shell", "deck-shell.html")
OUT = {"onepage_html": "onepage.html", "onepage_pptx": "onepage.pptx", "deck_html": "talk-deck.html",
       "deck_pptx": "talk-deck.pptx", "gates": "story-gates.txt"}   # talk-script.md is no longer written (2026-11-03)
TABLE_ROWS = (("Structure", "structure"), ("Features", "features"), ("Method", "method"), ("Result", "result"), ("Conclusion", "conclusion"))
MIN_SCALE, LEGIBLE_SCALE = 0.72, 0.85
VIEWPORTS = [(1707, 830), (1280, 720)]
LOCATOR_RE = re.compile(r"(p\.\s*\d+|pp\.\s*\d+|Fig\.?\s*S?\d+|Figure\s*\d+|Table\s*S?\d+|Eq\.?\s*\(?\d+|§\s*\d+|Sec\.?\s*\d+|\[inferred\]|\[assumed\])", re.I)
HIGHLIGHT_MAX, CELL_MAX, KPBOX_MAX, KP_MAX = 48, 120, 80, 90   # KP_MAX 70 → 90 on 2026-09-04: the slogan may carry its role qualifiers
DESC_MIN, DESC_MAX = 200, 700   # keypoint_description (讀書心得終極詮釋) — WARN outside; the user said ≤ 80 was far too small for the reading
# co-upgrade round 1 (2026-09-03): the drift tell list of references/narrative-axis.md §4 as an enum. Kept in sync with
# assets/story.schema.json by the selftest ("kinds-in-sync"). Blind calibration: two readers of one paper each walked
# a different subset of the list — the walk must be DECLARED (S13), not remembered.
DRIFT_KINDS = ("over-claim", "grafted-result", "no-criterion", "method-after-the-fact", "figure-unasked",
               "limitation-aside", "weaker-instrument", "discussion-new-data", "selective-condition", "abstract-mismatch")
FIG_KINDS = ("evidence", "schematic", "motivation")
# round 4 (2026-09-14, schema @5)
METHOD_KINDS = ("fabrication", "model", "simulation", "measurement", "analysis")
VERDICT_STATUS = ("achieved", "partly", "simulated-only", "not-shown")
STATUS_ZH = {"achieved": "達到（實測）", "partly": "部分達到", "simulated-only": "僅模擬／計算", "not-shown": "沒有證明"}
CLOSE_SECTIONS = ("keylogic", "storyline", "conclusion", "closing")   # round 7: where the slogan is spoken, after the paper is walked
FRONT_SECTIONS = ("keypoint", "verdict", "cover", "source", "keylogic", "methods")   # the pages spoken before the paper is walked — the advisor's 「一開始」 (source / keylogic / methods: round 5, the lab deck's front block)
FLOW_EXEMPT = ("keypoint", "cover", "source", "references")                   # the opening formula and the outline sentence are their own register
FIGURE_SECTIONS = ("introduction", "method", "methods", "results")
FIG_READ_PARTS = (("look", "看什麼："), ("see", "會看到："), ("against", "對照："), ("means", "所以："))
TAKEAWAY_MAX = 60
# a told figure points at it; a told page links its sentences. Both are proxies (S19 / S20 docstrings), not proof of voice.
FIG_DEIXIS = re.compile(r"這張|那張|圖[中上下左右裡]|左邊|右邊|上面|下面|中間|橫軸|縱軸|[xy]\s*軸|（[a-h]）|\([a-h]\)|曲線|虛線|實線|[藍紅黑橘黃][點線圈色]|點是|線是", re.I)
CONNECTIVES = re.compile(r"因為|所以|但是|但|不過|然而|於是|因此|也就是說|換句話說|接下來|問題是|為了|那麼|可是|反過來|回到|那要|那為什麼|有意思的是")


def schema_ver(story):
    m = re.search(r"@(\d+)$", str(story.get("schema", "")))
    return int(m.group(1)) if m else 1


def kp_text(story):
    """The slogan every product prints. Schema ≥ @4: logic.keypoint VERBATIM — onepage.keypoint_box is gone because it
    invited a second compression of an already-abstract sentence (user finding 2026-09-04: Bose 68 → 59 CJK-eq with the
    80 cap never reached; Zhang's box carried a duplicate 為什麼讀它). Older runs keep printing their box."""
    if schema_ver(story) >= 4:
        return story.get("logic", {}).get("keypoint", "")
    return story.get("onepage", {}).get("keypoint_box", "") or story.get("logic", {}).get("keypoint", "")


def kp_clauses(kp):
    return [c.strip() for c in re.split(r"[；;｜|]", kp or "") if c.strip()]


def role_spans(kp, bindings):
    """Non-overlapping (start, end, role) occurrences of every binding role in the slogan, longest roles first — every
    occurrence of a role is decorated (Ow's 邊界 appears twice and both are the same referent)."""
    taken, spans = [], []
    for role in sorted({b.get("role", "") for b in bindings if b.get("role")}, key=len, reverse=True):
        for m in re.finditer(re.escape(role), kp):
            a, z = m.start(), m.end()
            if any(a < t1 and z > t0 for t0, t1 in taken):
                continue
            taken.append((a, z)); spans.append((a, z, role))
    return sorted(spans)


def decorate_roles(kp, bindings):
    """Server-side decoration of the slogan: each bound role becomes a .sym span keyed kp:<role>, registered n:1 so the
    shell's page-wide decorator never touches the same word in a table cell; the hover card reads 在這篇＝referent."""
    out, last = [], 0
    for a, z, role in role_spans(kp, bindings):
        out.append(esc(kp[last:a]))
        out.append(f'<span class="sym kp-role" tabindex="0" data-key="kp:{esc(role)}" style="border-bottom:1px dotted var(--glass);font-weight:700;">{esc(role)}</span>')
        last = z
    out.append(esc(kp[last:]))
    return "".join(out)


def esc(s):
    return H.escape(str(s if s is not None else ""), quote=True)


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


class Gates:
    def __init__(self):
        self.rows = []

    def add(self, g, s, m):
        self.rows.append((g, s, m))

    @property
    def failed(self):
        return any(s == "FAIL" for _, s, _ in self.rows)

    def text(self):
        out = [f"paper-story gates — {dt.datetime.now().astimezone().isoformat(timespec='seconds')}"]
        out += [f"{g:<4}{s:<5}— {m}" for g, s, m in self.rows]
        out.append("RESULT: " + ("FAIL" if self.failed else "PASS" + (" with warnings" if any(s == "WARN" for _, s, _ in self.rows) else "")))
        return "\n".join(out)


# ---------------------------------------------------------------- gates
def s1_schema(story, G):
    try:
        import jsonschema
        errs = sorted(jsonschema.Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(story), key=lambda e: list(e.path))
        if errs:
            G.add("S1", "FAIL", f"schema: {len(errs)} violation(s) — " + "; ".join(f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message[:80]}" for e in errs[:4]))
            return False
        G.add("S1", "PASS", "story.json valid (assets/story.schema.json)")
        return True
    except ImportError:
        ok = all(k in story for k in ("axis", "storyline", "logic", "onepage", "deck", "talk", "terms"))
        G.add("S1", "PASS" if ok else "FAIL", "minimal structural check (jsonschema not installed)")
        return ok


def s2_whys(story, G):
    empty = []
    for k, v in story["axis"].items():
        w = v.get("why") or v.get("why_matters") or ""
        if not w.strip():
            empty.append(f"axis.{k}")
        elif fold(w) == fold(v.get("what", "")):
            empty.append(f"axis.{k} (restates what)")
    for i, b in enumerate(story["storyline"]):
        if not b.get("why", "").strip() or fold(b["why"]) == fold(b.get("what", "")):
            empty.append(f"storyline[{i}]")
    for i, c in enumerate(story["logic"]["chain"]):
        if not c.get("warrant", "").strip() or fold(c["warrant"]) == fold(c.get("step", "")):
            empty.append(f"chain[{i}].warrant")
        if schema_ver(story) >= 4:
            # 2026-09-04: the abstract step alone read as a telegram (「副作用 → 控制元件」); the concrete event sentence is required beside it
            itp = c.get("in_this_paper", "")
            if not itp.strip() or fold(itp) == fold(c.get("step", "")):
                empty.append(f"chain[{i}].in_this_paper")
    if empty:
        G.add("S2", "FAIL", "why missing/empty/restated: " + ", ".join(empty) + " — every step needs the reason it was taken" + (" and its concrete form in this paper" if schema_ver(story) >= 4 else ""))
    else:
        G.add("S2", "PASS", f"whys present on {len(story['axis'])} axis items, {len(story['storyline'])} beats, {len(story['logic']['chain'])} chain links" + (" (each with its in_this_paper sentence)" if schema_ver(story) >= 4 else ""))


def s3_locators(story, G):
    bad = []
    for k, v in story["axis"].items():
        if not LOCATOR_RE.search(v.get("locator", "")):
            bad.append(f"axis.{k}")
    for i, b in enumerate(story["storyline"]):
        if not LOCATOR_RE.search(b.get("locator", "")):
            bad.append(f"storyline[{i}]")
    for i, c in enumerate(story["logic"]["chain"]):
        if not LOCATOR_RE.search(c.get("backing", "")):
            bad.append(f"chain[{i}].backing")
    for i, d in enumerate(story.get("drift", [])):
        if not LOCATOR_RE.search(d.get("locator", "") + " " + d.get("where", "")):
            bad.append(f"drift[{i}]")
    if bad:
        G.add("S3", "FAIL", "no locator (p.N / Fig.N / §N / [inferred]) on: " + ", ".join(bad))
    else:
        G.add("S3", "PASS", "axis, beats, chain backing and drift rows all carry locators")


def tile_files(f):
    """Image files of one one-page figure/tile. story@6 (user ruling 2026-11-03 G1): a tile may carry several panels in files[]
    (files wins over file); older runs carry one file."""
    fs = f.get("files")
    if fs:
        return [str(x) for x in fs]
    return [f["file"]] if f.get("file") else []


def onepage_fields(op):
    """'four' | 'five' (user ruling 2026-11-03 G2: Features is optional per deck, the default stays five)."""
    return "four" if (op or {}).get("fields") == "four" else "five"


def table_rows(op):
    """The (label, key) rows the one-page table prints — four or five per onepage.fields."""
    return tuple(r for r in TABLE_ROWS if not (r[1] == "features" and onepage_fields(op) == "four"))


def story_mode_tiles(story):
    """(main tiles, side-evidence tiles) of a one-page; a tile without a step counts as main."""
    figs = story["onepage"]["figures"]
    side = [f for f in figs if f.get("step") == "side-evidence"]
    return [f for f in figs if f.get("step") != "side-evidence"], side


def tile_is_table(f):
    """A results TABLE used as a tile (user ruling 2026-11-03 G1: tables do not take a tile, their numbers go into the Result cell).
    Determinable from the caption/locator/file name: a Table token and no Fig token."""
    s = " ".join(str(f.get(k, "")) for k in ("caption", "locator"))
    names = " ".join(tile_files(f))
    has_tab = re.search(r"\b(?:table|tab\.)\s*S?\d+|表\s*\d+", s, re.I) or re.search(r"(?:^|[/\\_-])table[-_]?\d", names, re.I)
    has_fig = re.search(r"\b(?:fig|figure)s?\.?\s*S?\d+|圖\s*\d+", s, re.I)
    return bool(has_tab) and not has_fig


def s4_onepage(story, run_dir, G):
    op = story["onepage"]
    figs = op["figures"]
    mode = story.get("run", {}).get("mode", "deep")
    tiles_v6 = schema_ver(story) >= 6
    four = onepage_fields(op) == "four"
    missing = [fn for f in figs for fn in tile_files(f) if not (run_dir / fn).is_file()]
    if not all(tile_files(f) for f in figs):
        missing.append("<tile without file/files>")
    cells = {k: v for k, v in op["table"].items() if not (four and k == "features")}
    if not four and "features" not in cells:
        cells["features"] = ""
    empty = [k for k, v in cells.items() if not v.strip()]
    nonec = [f.get("caption", "")[:24] for f in figs if f.get("step") == "side-evidence" and not str(f.get("necessity", "")).strip()] if tiles_v6 else []
    if tiles_v6 and mode == "story":
        main, side = story_mode_tiles(story)
        count_ok = 3 <= len(main) <= 4 and len(side) <= 1
        count_need = f"story mode needs 3–4 tiles plus at most 1 side-evidence tile, got {len(main)} + {len(side)}"
    else:
        count_ok = 3 <= len(figs) <= 6
        count_need = f"figures={len(figs)} (need 3–6)"
    if missing or empty or nonec or not count_ok:
        G.add("S4", "FAIL", f"one-page shape: {count_need}, missing files {missing}, empty cells {empty}"
              + (f", side-evidence tiles without necessity {nonec}" if nonec else ""))
        return False
    long = [f"{k} {len(v)}" for k, v in cells.items() if len(v) > CELL_MAX]
    kb = cjk_len(kp_text(story))
    probs = []
    if four and op["table"].get("features"):
        probs.append("table.features is present but onepage.fields is four — the Features row is not printed")
    if long:
        probs.append(f"cells over {CELL_MAX} chars: {long}")
    if schema_ver(story) >= 4:
        if op.get("keypoint_box"):
            probs.append("keypoint_box is ignored on schema @4 (the strip prints logic.keypoint verbatim; the field invited a second compression — 2026-09-04): remove it")
    else:
        if kb > KPBOX_MAX:
            probs.append(f"keypoint_box {kb:.0f} > {KPBOX_MAX}")
        if re.match(r"\s*key\s*point", op.get("keypoint_box", ""), re.I):
            # round 2 (run Z): the strip printed 「KEYPOINT｜KEYPOINT｜…」 — the renderer prints the label, the field holds the sentence only
            probs.append("keypoint_box starts with the KEYPOINT label — the renderer prints the label; keep only the sentence")
    if probs:
        G.add("S4", "WARN", "one-page text: " + "; ".join(probs))
    else:
        nfiles = sum(len(tile_files(f)) for f in figs)
        what = (f"{len(figs)} tiles ({nfiles} image files)" if tiles_v6 else f"{len(figs)} figures") + " present"
        G.add("S4", "PASS", f"one-page: {what}, {'four' if four else 'five'} table cells filled, keypoint strip {kb:.0f} CJK-eq" + (" (logic.keypoint verbatim)" if schema_ver(story) >= 4 else ""))
    return True


STEP_ORDER = ("context", "series", "trend", "mechanism")
STEP_ZH = {"context": "情境", "series": "原始系列", "trend": "萃取趨勢", "mechanism": "機制", "side-evidence": "重點旁證"}


def s4d_tiles(story, G):
    """story@6 story-mode tiles (user ruling 2026-11-03 G1: figures are grouped by ARGUMENT STEP, results tables do not take a tile,
    key side-evidence stays allowed). WARN: both defects are determinable from the page's own declarations, but whether a table
    is truly 'only numbers' or a side figure truly 'necessary' stays the author's call. SKIP outside story mode and below @6, so
    accepted @5 runs and deep mode keep their gate output."""
    mode = story.get("run", {}).get("mode", "deep")
    if schema_ver(story) < 6:
        G.add("S4d", "SKIP", f"schema @{schema_ver(story)} < @6 — tile rules apply from story@6")
        return
    if mode != "story":
        G.add("S4d", "SKIP", f"mode {mode} — argument-step tiles are a story-mode rule (deep mode unchanged)")
        return
    figs = story["onepage"]["figures"]
    tabs = [f.get("caption", "")[:32] for f in figs if tile_is_table(f)]
    nostep = [f.get("caption", "")[:32] for f in figs if not f.get("step")]
    probs = []
    if tabs:
        probs.append(f"results table used as a tile: {tabs} — table numbers go into the Result cell, not a tile (user ruling 2026-11-03 G1)")
    if nostep:
        probs.append(f"tile without a step (context|series|trend|mechanism|side-evidence): {nostep}")
    if probs:
        G.add("S4d", "WARN", "; ".join(probs))
    else:
        order = " → ".join(STEP_ZH.get(f["step"], f["step"]) for f in figs)
        G.add("S4d", "PASS", f"{len(figs)} tiles each carry an argument step ({order}); no results table takes a tile")


def s15_bindings(story, G):
    """User finding 2026-09-04: the three accepted one-pages printed the abstract slogan alone, and its role nouns (形狀,
    載體, 自由度, 模型, 最低點, 操作範圍, 下游指標…) could not be resolved even after reading the paper — an unbound role
    invites a wrong reading（錯誤的詮釋比沒解釋更糟糕）. Determinable part, hence FAIL: every binding role is a verbatim
    substring of the slogan, every clause (split on ；) carries ≥ 1 bound role, ≥ 3 bindings, each with a locator.
    Whether the bindings are the RIGHT ones is the readback test's job (evals), never this gate's."""
    lg = story.get("logic", {}); kp = lg.get("keypoint", ""); b = lg.get("bindings") or []
    if schema_ver(story) < 4 and not b:
        G.add("S15", "WARN", f"bindings undeclared (schema @{schema_ver(story)}): declare logic.bindings[] (role → referent → locator) so every role noun of the slogan resolves — story@4")
        return
    probs = []
    if len(b) < 3:
        probs.append(f"only {len(b)} bindings (need ≥ 3)")
    stray = [x.get("role", "") for x in b if x.get("role", "") and x["role"] not in kp]
    if stray:
        probs.append(f"roles not found verbatim in the slogan: {stray[:5]}")
    noloc = [x.get("role", "") for x in b if not LOCATOR_RE.search(x.get("locator", ""))]
    if noloc:
        probs.append(f"bindings without a locator (p.N / Fig.N / §N / [inferred]): {noloc[:5]}")
    unbound = [c[:24] for c in kp_clauses(kp) if not any(x.get("role", "") and x["role"] in c for x in b)]
    if unbound:
        probs.append(f"slogan clauses with no bound role: {unbound}")
    if probs:
        G.add("S15", "FAIL", "; ".join(probs) + " — every role a reader cannot resolve from the slogan is a hole (logic-extraction.md Test 0b)")
    else:
        G.add("S15", "PASS", f"{len(b)} roles bound to referents, every clause of the slogan covered (hover cards on the strip)")


def s16_description(story, G):
    """The slogan is a slogan (≤ KP_MAX) and the 讀書心得終極詮釋 exists at reading length (DESC_MIN–DESC_MAX CJK-eq) and is not
    the slogan restated. WARN: the reader judges whether the paragraph is the ultimate reading; the bounds only stop the
    two failure shapes seen on 2026-09-04 (nothing beside the slogan; the slogan re-compressed into a box)."""
    lg = story.get("logic", {}); kp = lg.get("keypoint", ""); d = lg.get("keypoint_description", "")
    n, nd, probs = cjk_len(kp), cjk_len(d), []
    if n > KP_MAX:
        probs.append(f"slogan {n:.0f} CJK-eq > {KP_MAX} — a slogan, not a paragraph; the paragraph is keypoint_description")
    if schema_ver(story) < 4 and not d:
        G.add("S16", "WARN", (("; ".join(probs) + "; ") if probs else "") + f"keypoint_description undeclared (schema @{schema_ver(story)}): the practice copies print the slogan alone — author the 讀書心得終極詮釋 (story@4)")
        return
    if not d.strip():
        probs.append("keypoint_description missing")
    elif nd < DESC_MIN:
        probs.append(f"keypoint_description {nd:.0f} CJK-eq < {DESC_MIN} — too short to be a 讀書心得的終極詮釋")
    elif nd > DESC_MAX:
        probs.append(f"keypoint_description {nd:.0f} CJK-eq > {DESC_MAX} — the record §1 holds the long form")
    if d.strip() and fold(d) == fold(kp):
        probs.append("keypoint_description restates the slogan")
    if probs:
        G.add("S16", "WARN", "; ".join(probs))
    else:
        G.add("S16", "PASS", f"slogan {n:.0f} CJK-eq; description {nd:.0f} CJK-eq (the 讀書心得終極詮釋 printed under 展開解讀, on the 解讀 page and the deck's Keypoint page)")


LAYERS = ("A", "B", "C")
ASK_KINDS = ("clarify", "challenge", "extend")
CHALLENGE_PARTS = (("admit", "承認"), ("reason", "為什麼這樣選"), ("settle", "什麼證據能定案"))
BACKUP_MAX = 2
SPEAK_RATE = 250      # CJK-eq spoken per minute — an assumption until the presenter times one rehearsal (round 4, 2026-09-14)
SLOT_OVER = 1.2       # a full script longer than deck.minutes × this warns


def spoken_minutes(story):
    """Spoken-length estimate per cut from the text that is actually said (opening + page notes), not from page counts:
    the first round-4 Tran notes ran ≈ 21 min at this rate while the page rule said 11 — a told page is ≈ 2× a reported one."""
    pages = (story.get("deck") or {}).get("pages", [])
    opening = (story.get("talk") or {}).get("opening", "")
    extra = cjk_len(opening) if pages and pages[0].get("notes", "") != opening else 0

    def total(keep):
        return (extra + sum(cjk_len(p.get("notes", "")) for p in pages if keep(p))) / SPEAK_RATE
    return [(total(lambda p: True), "全講"), (total(lambda p: p.get("layer") != "C"), "刪 C"), (total(lambda p: p.get("layer") == "A"), "只留 A")]


def cut_plan(pages):
    """Page numbers per time layer and the page count after each cut (lab rule: pages ≈ minutes × 1.5)."""
    by = {L: [i for i, p in enumerate(pages, 1) if p.get("layer") == L] for L in LAYERS}
    return by, [(len(pages), "全講"), (len(pages) - len(by["C"]), "刪 C"), (len(by["A"]), "只留 A")]


def s17_layers_questions(story, G):
    """Time layers on deck pages and question kinds on if_asked (researcher.tw B-12 / B-13, user ruling R5 2026-09-14).
    WARN: an LLM writes these and the presenter reads them. The gate rules only on what it can determine — every page
    layered once any is, the Keypoint page and a Results page kept at A, every if_asked kinded once any is, every challenge
    carrying admit / reason / settle. Whether a C page is truly expendable stays the reader's call. SKIP when neither is
    declared, so older story.json files stay quiet.
    Round 4: once layers exist it also estimates the SPOKEN length (spoken_minutes, SPEAK_RATE CJK-eq per minute) and warns
    when the full script exceeds deck.minutes × SLOT_OVER — the page rule alone let a 21-minute script pass as 11. The rate is
    an assumption; recalibrate SPEAK_RATE (not the threshold) the first time a rehearsal is timed."""
    pages = (story.get("deck") or {}).get("pages", [])
    asked = (story.get("talk") or {}).get("if_asked", [])
    layered = [p for p in pages if p.get("layer")]
    kinded = [q for q in asked if q.get("kind")]
    if not layered and not kinded:
        G.add("S17", "SKIP", "no deck.pages[].layer and no talk.if_asked[].kind — undeclared (older story.json): no cut plan, no backup pages")
        return
    probs, info = [], []
    if layered:
        if len(layered) < len(pages):
            probs.append(f"{len(pages) - len(layered)} of {len(pages)} pages carry no layer — a cut plan needs every page")
        kpage = next((p for p in pages if p.get("section", "").lower() == "keypoint"), pages[0] if pages else {})
        if pages and kpage.get("layer") != "A":
            probs.append(f"Keypoint page is layer {kpage.get('layer') or '-'} — it is never cut (A)")
        if not any(p.get("layer") == "A" and p.get("section", "").lower() == "results" for p in pages):
            probs.append("no Results page is layer A — the main result must survive every cut")
        _, steps = cut_plan(pages)
        info.append("cut plan " + " → ".join(f"{label} {k} pages ≈ {k / 1.5:.0f} min" for k, label in steps))
        spoken = spoken_minutes(story)
        info.append("spoken ≈ " + " → ".join(f"{label} {m:.1f} min" for m, label in spoken) + f" at {SPEAK_RATE} CJK-eq/min (assumed)")
        slot = (story.get("deck") or {}).get("minutes")
        if slot and spoken[0][0] > slot * SLOT_OVER:
            probs.append(f"spoken text ≈ {spoken[0][0]:.1f} min at {SPEAK_RATE} CJK-eq/min exceeds the {slot}-min slot × {SLOT_OVER}"
                         f" — tighten the notes or plan the cut (刪 C ≈ {spoken[1][0]:.1f}, 只留 A ≈ {spoken[2][0]:.1f} min)")
    else:
        info.append("layers undeclared")
    if kinded:
        if len(kinded) < len(asked):
            probs.append(f"{len(asked) - len(kinded)} of {len(asked)} if_asked items carry no kind")
        challenges = [q for q in asked if q.get("kind") == "challenge"]
        for q in challenges:
            miss = [k for k, _ in CHALLENGE_PARTS if not str((q.get("challenge") or {}).get(k, "")).strip()]
            if miss:
                probs.append(f"challenge 「{q.get('q', '')[:24]}」 lacks {'/'.join(miss)} — answer = admit → why this choice → what would settle it")
        info.append(f"if_asked {len(asked)} (" + ", ".join(f"{k} {sum(1 for q in asked if q.get('kind') == k)}" for k in ASK_KINDS)
                    + f"); backup pages {min(BACKUP_MAX, len(challenges))}")
    else:
        info.append("question kinds undeclared")
    if probs:
        G.add("S17", "WARN", "; ".join(probs))
    else:
        G.add("S17", "PASS", "; ".join(info))


def s18_brief(story, G):
    """@5 brief — why read / every method / did it work / how judged, up front (advisor 2026-09-14; Pratt's three questions).
    WARN (an LLM writes it, the presenter reads it). Rules only on what it can determine: methods answer something and carry a
    locator; verdicts carry judged_by + result + locator; problem is not why_me.why_read restated (Q1 is the paper's bottleneck,
    not my reason); every method NAME occurs in the front text (talk.opening + notes of the leading FRONT_SECTIONS pages —
    Keypoint / Verdict / Cover, and since round 5 Source / KeyLogic / Methods); a Verdict page among the front pages. Whether a status is RIGHT stays paper-distill's call. SKIP without a brief."""
    b = story.get("brief")
    if not b:
        G.add("S18", "SKIP", "no brief — schema < @5 or story mode: why read / methods / verdicts are not declared up front")
        return
    probs = []
    methods, verdicts = b.get("methods", []), b.get("verdicts", [])
    for i, m in enumerate(methods):
        if not str(m.get("answers", "")).strip() or fold(m.get("answers", "")) == fold(m.get("name", "")):
            probs.append(f"methods[{i}] {m.get('name', '')!r} answers no question")
        if not LOCATOR_RE.search(m.get("locator", "")):
            probs.append(f"methods[{i}] {m.get('name', '')!r} has no locator")
    for i, v in enumerate(verdicts):
        miss = [k for k in ("judged_by", "result") if not str(v.get(k, "")).strip()]
        if miss:
            probs.append(f"verdicts[{i}] {v.get('goal', '')[:20]!r} lacks {'/'.join(miss)}")
        if not LOCATOR_RE.search(v.get("locator", "")):
            probs.append(f"verdicts[{i}] {v.get('goal', '')[:20]!r} has no locator")
    pb = fold(b.get("problem", ""))
    if pb and pb == fold((story.get("why_me") or {}).get("why_read", "")):
        probs.append("brief.problem restates why_me.why_read — Q1 is the paper's bottleneck, not my reason for reading it")
    pages = (story.get("deck") or {}).get("pages", [])
    if pages:
        n_front = next((i for i, p in enumerate(pages) if p.get("section", "").lower() not in FRONT_SECTIONS), len(pages))
        front = fold((story.get("talk") or {}).get("opening", "") + " " + " ".join(p.get("notes", "") for p in pages[:n_front]))
        unspoken = [m.get("name", "") for m in methods if fold(m.get("name", "")) not in front]
        if unspoken:
            probs.append(f"method(s) never named in the opening or the {n_front} front page(s): {unspoken[:6]} — say every method before walking the paper")
        if not any(p.get("section", "").lower() == "verdict" for p in pages[:max(3, n_front)]):
            probs.append("no Verdict page among the front pages — 有沒有達到／怎麼判讀 belongs up front")
    if probs:
        G.add("S18", "WARN", "; ".join(probs))
    else:
        G.add("S18", "PASS", f"{len(methods)} methods, all named up front; {len(verdicts)} verdicts (" +
              ", ".join(f"{STATUS_ZH[s]} {sum(1 for v in verdicts if v.get('status') == s)}" for s in VERDICT_STATUS) + ")")


def s19_figure_reading(story, G):
    """@5 figure reading (advisor 2026-09-14: 圖片跟圖表是最大優先…也要特別解釋). WARN. A figure page carries figure_read
    look / see / means, plus against on a Results page (a result is always against something); its notes point at the figure
    (FIG_DEIXIS — a proxy: the round-4 before-copy's notes named numbers but never an axis or a panel); an Introduction / Method
    / Results page without a figure says why in no_figure. SKIP on schema < @5 when no page declares either field."""
    pages = (story.get("deck") or {}).get("pages", [])
    if not pages or (schema_ver(story) < 5 and not any(p.get("figure_read") or p.get("no_figure") for p in pages)):
        G.add("S19", "SKIP", "no deck, or schema < @5 without figure_read / no_figure — figure walks undeclared")
        return
    probs, n_fig = [], 0
    for i, p in enumerate(pages, 1):
        sec, fr = p.get("section", "").lower(), p.get("figure_read") or {}
        if p.get("figure"):
            n_fig += 1
            miss = [k for k in ("look", "see", "means") if not str(fr.get(k, "")).strip()]
            if sec == "results" and not str(fr.get("against", "")).strip():
                miss.append("against")
            if miss:
                probs.append(f"p{i} figure without figure_read {'/'.join(miss)}")
            elif not FIG_DEIXIS.search(p.get("notes", "")):
                probs.append(f"p{i} notes never point at the figure (axis / panel / 這張圖…) — the walk is written but not spoken")
        elif sec in FIGURE_SECTIONS and not str(p.get("no_figure", "")).strip():
            probs.append(f"p{i} {p.get('section', '')} page has no figure and no no_figure reason — a figure is the first thing a page gets")
    if probs:
        G.add("S19", "WARN", "; ".join(probs[:8]))
    else:
        G.add("S19", "PASS", f"{n_fig} figure pages, each with look / see / means (+ against on Results) and spoken deixis")


def s20_flow(story, G):
    """@5 narrative flow (the user's 「生硬」 finding, round 4). WARN. Every page after the Outline carries asks / bridge / takeaway;
    the bridge is verbatim inside the notes; notes recite no highlight (≥ 10 CJK-eq) and carry ≥ 2 distinct connectives; takeaway
    ≤ TAKEAWAY_MAX; the slogan is SPOKEN at the close — on a logic-chain / storyline / conclusion page after the paper is walked,
    or in talk.closing (user ruling round 7, 2026-09-21, for every deck; it overturned round 5's 「Keypoint搬回前面」);
    story_arc has a spine and ≥ 4 craft steps each with a why_it_works that is not the move restated; a Storyline page exists.
    Connectives are a proxy — see the module docstring for the instrument that judged the voice."""
    pages = (story.get("deck") or {}).get("pages", [])
    tk = story.get("talk") or {}
    declared = any(p.get("asks") or p.get("bridge") or p.get("takeaway") for p in pages) or tk.get("story_arc")
    if not pages or (schema_ver(story) < 5 and not declared):
        G.add("S20", "SKIP", "no deck, or schema < @5 without asks / bridge / takeaway / story_arc — narrative flow undeclared")
        return
    probs, n = [], 0
    for i, p in enumerate(pages, 1):
        if p.get("section", "").lower() in FLOW_EXEMPT:
            continue
        n += 1
        miss = [k for k in ("asks", "bridge", "takeaway") if not str(p.get(k, "")).strip()]
        if miss:
            probs.append(f"p{i} lacks {'/'.join(miss)}")
            continue
        notes = p.get("notes", "")
        fn = fold(notes)
        if fold(p["bridge"]) not in fn:
            probs.append(f"p{i} bridge is not inside the notes")
        rec = [h for h in p.get("highlights", []) if cjk_len(h) >= 10 and fold(h) in fn]
        if rec:
            probs.append(f"p{i} notes recite a highlight ({rec[0][:18]}…) — notes add the walk and the why, the slide already shows it")
        if len(set(CONNECTIVES.findall(notes))) < 2:
            probs.append(f"p{i} notes carry < 2 distinct connectives — reads as a list of facts")
        if cjk_len(p["takeaway"]) > TAKEAWAY_MAX:
            probs.append(f"p{i} takeaway {cjk_len(p['takeaway']):.0f} CJK-eq > {TAKEAWAY_MAX}")
    # round 7 (user ruling 2026-09-21, 「全部簡報都照這個改」): the logic chain closes the talk — the slogan is spoken on a closing
    # page (logic chain / storyline / conclusion after the paper is walked) or in talk.closing; saying it up front as well is allowed
    kp = fold((story.get("logic") or {}).get("keypoint", ""))[:24]
    n_front = next((i for i, p in enumerate(pages) if p.get("section", "").lower() not in FRONT_SECTIONS), len(pages))
    cl = tk.get("closing") or {}
    close = fold(" ".join(p.get("notes", "") for p in pages[n_front:] if p.get("section", "").lower() in CLOSE_SECTIONS) + " " +
                 (" ".join(str(v) for v in cl.values()) if isinstance(cl, dict) else str(cl)))
    if kp and kp not in close:
        probs.append("the key point (slogan) is not spoken at the close — say it on the logic-chain / storyline / conclusion page after the paper is walked (user ruling round 7)")
    arc = tk.get("story_arc") or {}
    craft = arc.get("craft") or []
    if not str(arc.get("spine", "")).strip():
        probs.append("talk.story_arc.spine empty — how does this paper tell its story in one And-But-Therefore sentence?")
    if len(craft) < 4:
        probs.append(f"story_arc has {len(craft)} craft step(s) (< 4)")
    thin = [c.get("beat", "?") for c in craft if not str(c.get("why_it_works", "")).strip() or fold(c.get("why_it_works", "")) == fold(c.get("move", ""))]
    if thin:
        probs.append(f"craft step(s) {thin} lack a why_it_works")
    if arc and not any(p.get("section", "").lower() == "storyline" for p in pages):
        probs.append("story_arc is not rendered — no page with section Storyline")
    if probs:
        G.add("S20", "WARN", "; ".join(probs[:8]))
    else:
        G.add("S20", "PASS", f"{n} flow pages with asks / bridge (inside notes) / takeaway; no recited highlight; key point spoken at the close; story_arc {len(craft)} craft steps")


def s5_deck(story, run_dir, G):
    pages = story["deck"]["pages"]
    # round 5 (user ruling 2026-09-14): the lab's GaN decks put Outlines (Cover) before Key points and a source page may sit beside
    # the title — the Keypoint page stays in the first three pages, never behind the paper's content
    k = next((i for i, p in enumerate(pages) if p.get("section", "").lower() == "keypoint"), None)
    if len(pages) < 5 or k is None or k > 2:
        G.add("S5", "FAIL", f"deck shape: {len(pages)} pages, Keypoint page at {('p' + str(k + 1)) if k is not None else 'none'} (must be within the first 3 pages)")
        return False
    long = [f"p{i+1}:{cjk_len(h):.0f}" for i, p in enumerate(pages) for h in p.get("highlights", []) if cjk_len(h) > HIGHLIGHT_MAX]
    missing = [p["figure"] for p in pages if p.get("figure") and not (run_dir / p["figure"]).is_file()]
    if missing:
        G.add("S5", "FAIL", f"deck figure files missing: {missing}")
        return False
    if long:
        G.add("S5", "WARN", f"highlights over {HIGHLIGHT_MAX} CJK-eq (a slide is a 重點提醒, not an essay): {long[:8]}")
    else:
        G.add("S5", "PASS", f"deck: {len(pages)} pages, Keypoint page p{k + 1}, every highlight ≤ {HIGHLIGHT_MAX}")
    return True


def s6_terms(story, rendered_text, G):
    terms = story.get("terms", [])
    ft = fold(rendered_text)
    unused = [t["term"] for t in terms if fold(t["term"]) not in ft]
    probs = []
    if story["run"].get("mode") in ("deep", "story") and len(terms) < 12:
        probs.append(f"only {len(terms)} terms (< 12 for a full paper — every technical term on the pages needs a preview)")
    if unused:
        probs.append(f"terms never appear in the rendered pages: {unused[:8]}")
    if probs:
        G.add("S6", "WARN", "; ".join(probs) + " — promotion trigger: the user finds an unglossed term → FAIL")
    else:
        G.add("S6", "PASS", f"{len(terms)} terms, every one appears on a rendered page (hover cards active)")


def _eol_sha(p: Path) -> str:
    # Line endings are a checkout artefact: this repo pins LF, AssetVault checks out CRLF,
    # so a raw-byte hash reported drift between identical copies (fixed 2026-10-05).
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def s8_shell(G):
    recorded = SHELL_SHA.read_text(encoding="utf-8").strip() if SHELL_SHA.exists() else ""
    actual = _eol_sha(SHELL)
    if recorded and actual != recorded:
        G.add("S8", "WARN", "assets/deck-shell.html differs from the recorded sha256 (LF-normalised)")
    if VAULT_SHELL is not None and VAULT_SHELL.is_file():  # WORK_ROOT unset: same as no AssetVault copy
        if _eol_sha(VAULT_SHELL) != actual:
            G.add("S8", "WARN", "AssetVault briefing-deck-shell has changed since this copy — re-copy and re-record the sha")
        else:
            G.add("S8", "PASS", "deck-shell byte-identical to the AssetVault reference")
    else:
        G.add("S8", "SKIP", "AssetVault shell not reachable — drift not determinable")


_NUM = {"一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def outline_parts(text):
    """(N, items) from 「分為 N 個部分…：a、b、c」 — N None when the formula is absent, items [] when nothing is enumerated."""
    m = re.search(r"分為\s*([一二兩三四五六七八九十]|\d+)\s*個部分", text or "")
    n = (int(m.group(1)) if m.group(1).isdigit() else _NUM.get(m.group(1))) if m else None
    items = []
    if re.search(r"[：:]", text or ""):
        tail = re.split(r"[：:]", text, 1)[1].strip().rstrip("。.")
        for it in re.split(r"[、，,；;]", tail):
            it = re.sub(r"^(最後是|最後|以及|還有|和|與)", "", it.strip()).strip()
            if it:
                items.append(it)
    return n, items


def s9_talk(story, G, shown=None):
    """Talk conventions. Since 2026-11-03 the talk script is no longer a file of its own: it is the 口述稿 section of the
    explainer (user ruling), so the opening formula, the outline sentence and the closing synthesis are ALSO checked on the text
    that section prints (`shown`, from talk_section_text) — a script that is declared but not shown is the defect this catches."""
    t = story["talk"]
    probs = []
    op = t.get("opening", "")
    if not (("大家好" in op) and ("我是" in op) and ("題目" in op)):
        probs.append("opening lacks the lab formula（大家好／我是／題目）")
    elif shown is not None and fold(op) not in fold(shown):
        probs.append("the opening is not printed in the explainer's 口述稿 section")
    if "分為" not in t.get("outline", ""):
        probs.append("outline lacks 「分為 N 個部分」")
    else:
        if shown is not None and "分為" not in shown:
            probs.append("the outline sentence is not printed in the explainer's 口述稿 section")
        # calibration 2026-09-03 (run A): the outline said five parts, the Cover page listed three — a listener notices.
        n, items = outline_parts(t.get("outline", ""))
        if n and len(items) >= 2 and len(items) != n:
            probs.append(f"outline says {n} parts but enumerates {len(items)}")
        cover = [p for p in story.get("deck", {}).get("pages", []) if p.get("section", "").lower() == "cover"]
        if n and cover and len(cover[0].get("highlights", [])) >= 3 and len(cover[0]["highlights"]) != n:
            probs.append(f"Cover page lists {len(cover[0]['highlights'])} bullets but the outline says {n} parts (≥3 bullets on the Cover are the outline)")
    if not t.get("closing", {}).get("basis") or not t.get("closing", {}).get("help"):
        probs.append("closing lacks 研究依據／對後續的幫助")
    if probs:
        G.add("S9", "WARN", "; ".join(probs) + " (talk-conventions.md)")
    else:
        G.add("S9", "PASS", "talk carries the lab's opening formula, outline sentence and closing synthesis")


# ---------------------------------------------------------------- source-anchored gates (ruling 2026-09-03: 看錯／漏看 = 亂掰)
SEC_TOKEN = re.compile(r"§\s*([0-9]+(?:\.[0-9]+)*)|\b(?:sec\.?|section)\s*([0-9]+(?:\.[0-9]+)*)", re.I)
FIG_TOKEN = re.compile(r"\b(fig|figure|table)s?\.?\s*(\d{1,2})", re.I)
PAGE_TOKEN = re.compile(r"\bpp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.I)


def paper_text(run_dir: Path):
    p = run_dir / "source" / "paper.txt"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def page_texts(text):
    parts = re.split(r"<!--\s*p\.(\d+)\s*-->", text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def qfold(s):
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = s.replace("-\n", "").replace("‐", "-").replace("−", "-").replace("–", "-").replace("—", "-").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[\s ]+", " ", s).strip()


def quote_fields(story):
    """(path, quote, locator, quote_source) for every quote field; drift rows are listed even without one."""
    out = []
    for k, v in story.get("axis", {}).items():
        if isinstance(v, dict) and v.get("quote"):
            out.append((f"axis.{k}", v["quote"], v.get("locator", ""), v.get("quote_source", "")))
    for i, b in enumerate(story.get("storyline", [])):
        if b.get("quote"):
            out.append((f"storyline[{i}]", b["quote"], b.get("locator", ""), b.get("quote_source", "")))
    for i, d in enumerate(story.get("drift", [])):
        out.append((f"drift[{i}]", d.get("quote", ""), d.get("locator") or d.get("where", ""), d.get("quote_source", "")))
    return out


def s10_quotes(story, run_dir: Path, G):
    text = paper_text(run_dir)
    strict = schema_ver(story) >= 2
    if not text:
        G.add("S10", "WARN", "no source/paper.txt — quotes cannot be checked; every quote stays [assumed] until read on the page image")
        return
    ft = qfold(text)
    thin = [n for n, t in page_texts(text).items() if len(qfold(t)) < 200]
    fails, warns, n_ok = [], [], 0
    for path, q, loc, src in quote_fields(story):
        if not q:
            if path.startswith("drift"):
                (fails if strict else warns).append(f"{path}: no quote — a drift row without the paper's own words is an unanchored reading")
            continue
        fq = qfold(q)
        if len(fq) < 8:
            warns.append(f"{path}: quote too short to anchor ({q[:30]!r})")
            continue
        if fq in ft:
            n_ok += 1
            continue
        m = PAGE_TOKEN.search(loc or "")
        pg = int(m.group(1)) if m else None
        if src == "page-image":
            # round 2 (run S2): a text layer can miss a whole block (Zhang 2021's abstract) on a page that is otherwise dense —
            # the author declares the quote read from the page image; the dispatcher verifies it there. Absent from the page too = fabrication.
            warns.append(f"{path}: quote declared read from the page image ({loc or 'no locator'}), absent from the text layer — verify on source/pages; absent from the page too = fabrication")
        elif thin and (pg is None or pg in thin):
            warns.append(f"{path}: quote not found and the text layer is thin on page(s) {thin[:6]} — verify on the page image")
        else:
            fails.append(f"{path}: quote not found in source/paper.txt: {q[:60]!r}")
    if fails:
        G.add("S10", "FAIL", "; ".join(fails[:6]))
    elif warns:
        G.add("S10", "WARN", f"{n_ok} quotes anchored; " + "; ".join(warns[:6]))
    else:
        G.add("S10", "PASS", f"{n_ok} quotes found verbatim in source/paper.txt; every drift row anchored")


def collect_locators(story):
    strs = []
    for v in story.get("axis", {}).values():
        if isinstance(v, dict):
            strs.append(v.get("locator", ""))
    for b in story.get("storyline", []):
        strs.append(b.get("locator", ""))
    for d in story.get("drift", []):
        strs += [d.get("locator", ""), d.get("where", "")]
    for c in story.get("logic", {}).get("chain", []):
        strs.append(c.get("backing", ""))
    for f in story.get("onepage", {}).get("figures", []):
        strs += [f.get("locator", ""), f.get("caption", "")]
    for p in story.get("deck", {}).get("pages", []):
        strs += [p.get("locator", ""), p.get("title", ""), p.get("section", "")]
    for x in story.get("coverage", {}).get("skipped", []):
        strs.append(x.get("unit", ""))
    blob = " | ".join(s for s in strs if s)
    pages = set()
    for m in PAGE_TOKEN.finditer(blob):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        pages.update(range(a, b + 1))
    return blob, pages


def s11_coverage(story, run_dir: Path, G):
    sp = run_dir / "source" / "structure.json"
    if not sp.exists():
        G.add("S11", "SKIP", "no source/structure.json — run paper-distill/scripts/probe.py --run <run_dir> first")
        return None
    st = json.loads(sp.read_text(encoding="utf-8"))
    blob, pages = collect_locators(story)
    fb = qfold(blob)
    secs = {(m.group(1) or m.group(2)) for m in SEC_TOKEN.finditer(blob)}
    figs = {(("table" if m.group(1).lower().startswith("tab") else "fig"), int(m.group(2))) for m in FIG_TOKEN.finditer(blob)}
    skipped = {qfold(x.get("unit", "")) for x in story.get("coverage", {}).get("skipped", [])}
    units = st.get("units", [])
    sec_units = [u for u in units if u.get("kind") in ("section", "subsection")]
    spans = {}
    for i, u in enumerate(sec_units):
        nxt = sec_units[i + 1]["page"] if i + 1 < len(sec_units) else u["page"]
        spans[u["id"]] = (u["page"], max(u["page"], nxt))
    missing = []
    for u in units:
        uid = u.get("id", "")
        if qfold(uid) in skipped or (u.get("text") and qfold(u["text"]) in skipped):
            continue
        if u.get("kind") in ("section", "subsection"):
            num = uid[1:] if uid.startswith("§") and re.match(r"^\d", uid[1:]) else None
            if num and num in secs:
                continue
            if not num and u.get("text") and qfold(u["text"]) in fb:
                continue
            lo, hi = spans.get(uid, (u.get("page"), u.get("page")))
            if lo is not None and any(lo <= p <= hi for p in pages):
                continue
            missing.append(uid)
        else:
            m = re.match(r"(Fig|Table)\.?\s*(\d+)", uid)
            if m and (("table" if m.group(1) == "Table" else "fig"), int(m.group(2))) in figs:
                continue
            missing.append(uid)
    if missing:
        G.add("S11", "WARN", f"{len(missing)} of {len(units)} units never cited and not in coverage.skipped: {missing[:10]} — 漏看 until each is mapped or skipped with a why")
    else:
        G.add("S11", "PASS", f"every unit in structure.json ({len(units)}) is cited by a locator or explicitly skipped")
    return st


def s12_anomalies(story, st, G):
    if st is None:
        G.add("S12", "SKIP", "no structure.json")
        return
    an = st.get("anomalies", [])
    if not an:
        G.add("S12", "PASS", "probe found no structure anomalies")
        return
    strs = []
    for d in story.get("drift", []):
        strs += [d.get("where", ""), d.get("what_drifted", ""), d.get("why_it_matters", ""), d.get("locator", "")]
    for b in story.get("storyline", []):
        strs += [b.get("what", ""), b.get("locator", "")]
    for x in story.get("coverage", {}).get("skipped", []):
        strs += [x.get("unit", ""), x.get("why", "")]
    blob = qfold(" | ".join(strs))
    un = []
    for x in an:
        kind, xid = x.get("kind", ""), x.get("id", "")
        if kind == "abstract-number-not-in-body":
            nums = re.findall(r"\d+(?:\.\d+)?", x.get("detail", "").split(":")[-1])
            hit = ("摘要" in blob or "abstract" in blob) and any(re.search(r"(?<![\d.])" + re.escape(n) + r"(?![\d])", blob) for n in nums)
        elif xid.startswith("§"):
            hit = re.search(r"(?<![\d.])" + re.escape(xid[1:]) + r"(?![\d])", blob) is not None
        elif re.match(r"(Fig|Table)\.?\s*\d+", xid):
            m = re.match(r"(Fig|Table)\.?\s*(\d+)", xid)
            hit = re.search(r"\b(fig|figure|table)s?\.?\s*" + m.group(2) + r"\b", blob) is not None
        else:
            hit = qfold(xid) in blob
        if not hit:
            un.append(f"{kind} {xid}")
    if un:
        G.add("S12", "WARN", f"{len(un)} probe anomalies not addressed in drift/storyline/coverage.skipped: {un[:6]} — classify each (grafted section, uncited figure, abstract number) or say why it is nothing")
    else:
        G.add("S12", "PASS", f"all {len(an)} probe anomalies are addressed in the story")


def s4b_conclusion(story, G):
    c = story.get("onepage", {}).get("table", {}).get("conclusion", "")
    if "深讀判定" in c or "偏離：" in c:
        G.add("S4b", "PASS", "Conclusion cell keeps the author's ending and appends a marked 深讀判定")
    else:
        G.add("S4b", "WARN", "Conclusion cell has no 「深讀判定：」 marker — keep the author's ending, append the reader's verdict after the marker (ruling 2026-09-03)")


DECK_ONLY_KINDS = ("motivation",)   # OQ-1 ruling 2026-09-03: narrowed from (schematic, motivation) — see the docstring below


def s4c_figure_kinds(story, G):
    """Gb9 (user ruling 2026-09-03) as narrowed by OQ-1 (user ruling, same day): the one-page carries the paper's
    EVIDENCE figures and its OWN process/structure schematic (the picture behind the Structure / Method cells);
    MOTIVATION figures (overview, application scenarios) go to the deck only. Blind calibration: both readers kept the
    process flow and disagreed only on the six-panel motivation figure; every accepted run carried a process flow."""
    figs = story.get("onepage", {}).get("figures", [])
    if schema_ver(story) < 3 and not any(f.get("kind") for f in figs):
        G.add("S4c", "WARN", f"figure kinds undeclared (schema @{schema_ver(story)}): declare onepage.figures[].kind (evidence|schematic|motivation) — motivation figures are deck-only (ruling 2026-09-03 Gb9/OQ-1)")
        return
    non = [f"{f.get('caption', '')[:40]} ({f.get('kind')})" for f in figs if f.get("kind") in DECK_ONLY_KINDS]
    undeclared = [f.get("caption", "")[:40] for f in figs if not f.get("kind")]
    probs = ([f"deck-only figures on the one-page: {non} — move them to the deck, or keep with the reason in the record"] if non else []) + \
            ([f"kind undeclared: {undeclared}"] if undeclared else [])
    if probs:
        G.add("S4c", "WARN", "; ".join(probs) + " (ruling 2026-09-03 Gb9/OQ-1: motivation figures are deck-only; evidence and the paper's own schematic may stay)")
    else:
        n_sch = sum(1 for f in figs if f.get("kind") == "schematic")
        G.add("S4c", "PASS", f"{len(figs)} one-page figures declared: {len(figs) - n_sch} evidence, {n_sch} schematic, no motivation figure")


def s13_drift_checklist(story, G):
    """Gb8 (user ruling 2026-09-03): the §4 tell list is walked AND declared — every kind found in a drift row or marked
    none in coverage.drift_checklist. Determinable: declaration, not judgment; the judgment stays with the readers."""
    drift = story.get("drift", [])
    used = {d.get("kind") for d in drift if d.get("kind") in DRIFT_KINDS}
    decl = story.get("coverage", {}).get("drift_checklist") or {}
    if schema_ver(story) < 3 and not used and not decl:
        G.add("S13", "WARN", f"drift checklist not declared (schema @{schema_ver(story)}): no drift[].kind and no coverage.drift_checklist — walk the tell list (narrative-axis.md §4) and declare each kind found/none (story@3)")
        return
    probs = []
    unknown = sorted(k for k in decl if k not in DRIFT_KINDS)
    if unknown:
        probs.append(f"unknown kinds in drift_checklist: {unknown}")
    silent = [k for k in DRIFT_KINDS if k not in used and decl.get(k) != "none"]
    if silent:
        probs.append(f"{len(silent)} kinds neither found in a drift row nor declared none: {silent}")
    phantom = [k for k in DRIFT_KINDS if decl.get(k) == "found" and k not in used]
    if phantom:
        probs.append(f"declared found but no drift row carries the kind: {phantom}")
    contra = [k for k in DRIFT_KINDS if decl.get(k) == "none" and k in used]
    if contra:
        probs.append(f"declared none but a drift row carries the kind: {contra}")
    prov = " [backfilled: none = no row of that kind in the original reading, not a declared search]" if story.get("coverage", {}).get("checklist_provenance") == "backfilled" else ""
    if probs:
        G.add("S13", "WARN", "; ".join(probs) + " — a checklist not declared is a checklist not walked; promotion trigger: a kind declared none whose observation a second reader finds under no kind of this reading → FAIL" + prov)
    else:
        n_none = sum(1 for k in DRIFT_KINDS if decl.get(k) == "none")
        G.add("S13", "PASS", f"drift checklist walked: {len(used)} kinds found in {len(drift)} rows, {n_none} declared none, all {len(DRIFT_KINDS)} covered" + prov)


STRAY_RE = re.compile(r"[Ѐ-ԯ가-힯฀-๿؀-ۿ֐-׿ऀ-ॿ]")


def s14_stray_script(story, G):
    """Round 2 (run S3 caught 製程схема / 最ало脆弱 by hand before rendering): LLM-typed CJK sometimes carries a token from
    another script. Determinable: Cyrillic / Hangul / Thai / Arabic / Hebrew / Devanagari in any text field. Greek is
    allowed (μm, λ/4, Ω·cm are physics)."""
    hits = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
        elif isinstance(o, str):
            m = STRAY_RE.search(o)
            if m:
                hits.append(f"{path}: {m.group(0)!r} in {o[:24]!r}")
    walk(story, "story")
    if hits:
        G.add("S14", "WARN", f"{len(hits)} field(s) carry a stray-script character (Cyrillic/Hangul/Thai/Arabic/Hebrew/Devanagari; Greek is allowed for units): {hits[:5]} — retype the token")
    else:
        G.add("S14", "PASS", "no stray-script characters in any text field")


# ---------------------------------------------------------------- html
def data_uri(p: Path):
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(p.suffix.lower().lstrip("."), "image/png")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def cite(src):
    au = src.get("authors") or []
    a = (au[0] + (" et al." if len(au) > 1 else "")) if au else "（作者待填）"
    return " · ".join(b for b in [a, str(src.get("year") or ""), src.get("venue", ""), ("DOI " + src["doi"]) if src.get("doi") else src.get("url", "")] if b)


def registries(story):
    syms = {}
    for t in story.get("terms", []):
        title = t["term"] + ((" — " + t["en"]) if t.get("en") and t["en"] != t["term"] else "") + ((" ／ " + t["zh"]) if t.get("zh") and t["zh"] != t["term"] else "")
        syms[t["term"]] = {"t": title, "d": t["gloss"][:240], "s": 0}
        for a in t.get("aliases", []) or []:
            if a and a not in syms:
                syms[a] = {"t": title, "d": t["gloss"][:240], "s": 0}
    # 2026-09-04 keypoint bindings: registered n:1 (glossary-only) under kp:<role> so the shell's page-wide decorator never
    # decorates the same word in a table cell; the strip's own spans carry data-key="kp:<role>" and the hover card resolves here.
    for b in story.get("logic", {}).get("bindings", []) or []:
        if b.get("role"):
            syms["kp:" + b["role"]] = {"t": f"KEYPOINT 角色｜{b['role']}", "d": f"在這篇＝{b.get('referent', '')}（{b.get('locator', '')}）", "s": 0, "n": 1}

    def jd(x):  # every "<" -> <: paper text inside a <script> must not hold "</script" or "<!-- <script"
        return json.dumps(x, ensure_ascii=False).replace("<", "\\u003c")

    def js(obj):
        return "{\n" + ",\n".join(f"    {jd(k)}: {{t:{jd(v['t'])}, d:{jd(v['d'])}, s:0{', n:1' if v.get('n') else ''}}}" for k, v in obj.items()) + "\n  };"
    return "{\n  };", js(syms)


def splice(story, slides_html, title):
    shell = SHELL.read_text(encoding="utf-8")
    start, end = shell.index("<!-- SLIDE 1: cover"), shell.index("<!-- ==== chrome ==== -->")
    out = shell[:start] + slides_html.strip() + "\n\n" + shell[end:]
    out = re.sub(r"<title>.*?</title>", lambda m: "<title>" + esc(title) + "</title>", out, count=1, flags=re.S)
    refs_js, syms_js = registries(story)
    # function replacements: a template string would turn "\\u003c" into a bad escape and "\\n" into a newline
    out = re.sub(r"var REFS = \{.*?\n\s*\};", lambda m: "var REFS = " + refs_js, out, count=1, flags=re.S)
    out = re.sub(r"var SYMS = \{.*?\n\s*\};", lambda m: "var SYMS = " + syms_js, out, count=1, flags=re.S)
    return out.replace("<!-- FILL POINT 1 — slides.", "<!-- generated by paper-story render_story.py — FILL POINT 1 — slides.", 1)


def glossary_slide(story, no):
    rows = "".join(f"<tr><td><span class='val' style='white-space:normal'>{esc(t['term'])}</span>{(' <span class=small>' + esc(t.get('en','')) + '</span>') if t.get('en') and t['en'] != t['term'] else ''}</td><td>{esc(t['gloss'])}</td></tr>" for t in story.get("terms", []))
    return f"""
<section class="slide" id="gloss-page">
  <div class="eyebrow"><span class="no">{no:02d}</span><span>詞彙 · 頁面上出現的每個專有名詞（正文滑過虛線底可看卡片）</span></div>
  <h2>詞彙表</h2>
  <div class="twrap"><table><thead><tr><th style="width:26%">詞</th><th>說明</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>
"""


def kp_strip_html(story):
    """The one Keypoint strip on the lab one-page: the slogan (roles decorated, hover 在這篇＝…) + 為什麼讀它, and — for runs
    that carry the reading — a closed <details> 展開解讀 holding the 讀書心得終極詮釋 and the role table. Closed by default so
    the lab layout (S7 fit) is untouched; the user opens it when practising (ruling R3-1, 2026-09-04)."""
    lg, why = story["logic"], story["why_me"]
    b = lg.get("bindings") or []
    kp_html = decorate_roles(kp_text(story), b) if b else esc(kp_text(story))
    why_line = f"　·　為什麼讀它：{esc(why.get('why_read',''))}"
    if lg.get("keypoint_description"):
        # the 為什麼讀它 line IS the <summary>, so the toggle adds no height to the lab layout (S7 fit at 1707 stays PASS)
        paras = "".join(f"<p style='margin:4px 0;'>{esc(p.strip())}</p>" for p in re.split(r"\n\s*\n|\n", lg["keypoint_description"]) if p.strip())
        rows = "".join(f"<tr><td style='white-space:nowrap;'><b>{esc(x.get('role',''))}</b></td><td>{esc(x.get('referent',''))}</td><td class='small' style='white-space:nowrap;'>{esc(x.get('locator',''))}</td></tr>" for x in b)
        tail = f"""
    <details class="small kp-more" style="display:inline;"><summary style="display:inline;list-style:none;cursor:pointer;">{why_line}　<span style="color:var(--glass);font-weight:700;">▸ 展開解讀</span></summary>
      <div style="padding:4px 0 0;">{paras}
        <table style="margin-top:4px;"><thead><tr><th>slogan 裡的角色</th><th>在這篇＝</th><th>出處</th></tr></thead><tbody>{rows}</tbody></table>
        <p class="small" style="margin:2px 0 0;">完整解讀與邏輯鏈在第 2–3 頁。</p>
      </div>
    </details>"""
    else:
        tail = f'<span class="small">{why_line}</span>'
    return f"""
  <div class="thesis" style="padding:6px 12px;border-left:4px solid var(--glass);background:var(--glass-bg);">
    <span class="val" style="color:var(--glass);font-weight:700;">KEYPOINT｜</span>{kp_html}{tail}
  </div>"""


def keypoint_pages_html(story, no):
    """Two learning pages after the lab one-page (class A only; 2026-09-04): 解讀 = slogan + the 讀書心得終極詮釋 + the role
    table; 邏輯鏈 = the chain with its concrete form, warrant, qualifier and backing, then fragile + portable. Empty for runs
    that carry no description (older schema) — the strip alone then, as before."""
    lg = story["logic"]
    if not lg.get("keypoint_description"):
        return "", no
    b = lg.get("bindings") or []
    paras = "".join(f"<p class='lead'>{esc(p.strip())}</p>" for p in re.split(r"\n\s*\n|\n", lg["keypoint_description"]) if p.strip())
    brows = "".join(f"<tr><td style='white-space:nowrap;'><b>{esc(x.get('role',''))}</b></td><td>{esc(x.get('referent',''))}</td><td class='small' style='white-space:nowrap;'>{esc(x.get('locator',''))}</td></tr>" for x in b)
    crows = "".join(f"<tr><td>{i}</td><td><b>{esc(c.get('step',''))}</b></td><td>{esc(c.get('in_this_paper',''))}</td><td>{esc(c.get('warrant',''))}</td><td class='small'>{esc(c.get('qualifier',''))}</td><td class='small' style='white-space:nowrap;'>{esc(c.get('backing',''))}</td></tr>" for i, c in enumerate(lg.get("chain", []), 1))
    fr, po = lg.get("fragile", {}), lg.get("portable", {})
    pats = " · ".join(lg.get("patterns") or [])
    p1 = f"""
<section class="slide" id="kp-read">
  <div class="eyebrow"><span class="no">{no:02d}</span><span>Keypoint 解讀 · 練習・複習用 · 讀書心得的終極詮釋{(' · 邏輯型：' + esc(pats)) if pats else ''}</span></div>
  <h2>這篇是怎麼被建構的：把 slogan 的每個角色綁回論文</h2>
  <div class="thesis" style="padding:6px 12px;border-left:4px solid var(--glass);background:var(--glass-bg);"><span class="val" style="color:var(--glass);font-weight:700;">KEYPOINT｜</span>{decorate_roles(kp_text(story), b) if b else esc(kp_text(story))}</div>
  <div class="note explain" style="margin-top:6px;"><span class="tag">解讀</span>{paras}</div>
  <div class="twrap" style="margin-top:6px;"><table><thead><tr><th style="width:16%">slogan 裡的角色</th><th>在這篇＝</th><th style="width:12%">出處</th></tr></thead><tbody>{brows}</tbody></table></div>
</section>
"""
    p2 = f"""
<section class="slide" id="kp-chain">
  <div class="eyebrow"><span class="no">{no + 1:02d}</span><span>Keypoint 邏輯鏈 · 每一步的抽象形式、在這篇的具體形式、為什麼成立、到哪為止</span></div>
  <h2>邏輯鏈（含 warrant）</h2>
  <div class="twrap"><table><thead><tr><th>#</th><th style="width:16%">步驟（抽象）</th><th style="width:26%">在這篇</th><th>為什麼這一步成立</th><th style="width:14%">到哪為止</th><th style="width:9%">依據</th></tr></thead><tbody>{crows}</tbody></table></div>
  <div class="grid2" style="margin-top:6px;">
    <div class="note ask"><span class="tag">最脆弱的一環</span><p>{esc(fr.get('what',''))}</p><p class="small">為什麼脆弱：{esc(fr.get('why',''))}</p></div>
    <div class="note evidence"><span class="tag">可移植到</span><p>{esc(po.get('where',''))}</p><p class="small">為什麼可移植：{esc(po.get('why',''))}　·　何時不可移植：{esc(po.get('when_not',''))}</p></div>
  </div>
</section>
"""
    return p1 + p2, no + 2


def build_onepage_html(story, run_dir, presenter):
    src, op = story["source"], story["onepage"]
    figs = op["figures"]
    rows = math.ceil(len(figs) / 2)
    mh = {1: 42, 2: 27, 3: 18}.get(rows, 18)
    def tile_imgs(f):   # story@6: one tile = every panel of one argument step, side by side
        fs = tile_files(f)
        sub = mh if len(fs) == 1 else max(mh // 2, 12)
        return "".join(f'<img src="{data_uri(run_dir / fn)}" alt="{esc(f.get("caption",""))}" style="max-height:{sub}vh;{"max-width:48%;" if len(fs) > 1 else ""}">' for fn in fs)
    fig_html = "".join(
        f'<figure class="fig" style="padding:6px 6px 4px;">{tile_imgs(f)}'
        f'<figcaption>{esc(f.get("caption",""))}{(" · " + esc(f["locator"])) if f.get("locator") else ""}</figcaption></figure>' for f in figs)
    tbl = "".join(f"<tr><td><b>{esc(k)}</b></td><td>{esc(op['table'][kk])}</td></tr>" for k, kk in table_rows(op))
    eyebrow = " · ".join(x for x in ["paper-story · 論文一頁 · 練習・複習用（正式簡報＝實驗室範本英文版）", presenter or story["run"].get("presenter", ""), story["run"].get("created", "")[:10]] if x)
    p1 = f"""
<!-- SLIDE 1: 【論文一頁】 the lab's one-page format + ONE Keypoint strip -->
<section class="slide" id="p1">
  <div class="eyebrow"><span class="no">01</span><span>{esc(eyebrow)}</span></div>
  <h2 style="font-size:clamp(18px,1.9vw,26px);margin:0;">{esc(src.get('title',''))}</h2>
  <p class="small" style="margin:0;">{esc(cite(src))}{(' · ' + esc(', '.join(src.get('authors', [])[:4]))) if src.get('authors') else ''}</p>{kp_strip_html(story)}
  <div style="display:grid;grid-template-columns:1.35fr 1fr;gap:14px;min-height:min-content;align-items:start;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">{fig_html}</div>
    <div class="twrap"><table><tbody>{tbl}</tbody></table></div>
  </div>
  <p class="small" style="margin:0;"><b>References｜</b>{esc(cite(src))}　·　詞彙：滑過虛線底的詞看卡片，G 開全表</p>
</section>
"""
    kp_pages, next_no = keypoint_pages_html(story, 2)
    return splice(story, p1 + kp_pages + glossary_slide(story, next_no), f"【論文一頁・練習用】{src.get('title','')[:60]}")


def build_deck_html(story, run_dir, presenter):
    src, ax, why, lg, tk = story["source"], story["axis"], story["why_me"], story["logic"], story["talk"]
    parts = []
    b = lg.get("bindings") or []
    kp_html = decorate_roles(lg.get("keypoint", ""), b) if b else esc(lg.get("keypoint", ""))
    binds = ("<p class='small' style='margin:4px 0 0;'>" + "　·　".join(f"<b>{esc(x.get('role',''))}</b>＝{esc(x.get('referent',''))}" for x in b[:5]) + "</p>") if b else ""
    desc = (f"<details class='small' style='margin-top:4px;'><summary style='cursor:pointer;color:var(--glass);'>展開解讀（讀書心得的終極詮釋）</summary><p>{esc(lg['keypoint_description'])}</p></details>") if lg.get("keypoint_description") else ""
    kp_box = f'<div class="note evidence"><span class="tag">KEYPOINT｜邏輯抽取</span><p style="font-size:clamp(16px,1.5vw,20px);font-weight:700;">{kp_html}</p>{binds}{desc}</div>'
    # round 7 (user ruling 2026-09-21, every deck): the logic chain closes the talk — the slogan box sits on the Storyline page,
    # merged with the story line as on the user's final deck; a run without a rendered Storyline page keeps it on the Keypoint page
    kp_at_close = bool(tk.get("story_arc")) and any(p.get("section", "").lower() == "storyline" for p in story["deck"]["pages"])
    for i, pg in enumerate(story["deck"]["pages"], 1):
        sec = pg.get("section", "")
        hl = pg.get("highlights", [])
        notes = f'<details class="small" style="margin-top:auto;"><summary>講稿</summary><p>{esc(pg.get("notes",""))}</p></details>'
        if sec.lower() == "keypoint":
            body = f"""
  <div class="grid2">
    <div class="stack">
      <div class="note explain"><span class="tag">為什麼讀它</span><p class="lead">{esc(why.get('why_read',''))}</p></div>
      <div class="note explain"><span class="tag">對我有什麼幫助</span><p class="lead">{esc(why.get('helps',''))}</p></div>
    </div>
    <div class="stack">
      {'' if kp_at_close else kp_box}
      <div class="note ask"><span class="tag">主軸 · 切入點與為什麼</span><p><b>{esc(ax['entry_point'].get('what',''))}</b></p><p>為什麼是這個切入點：{esc(ax['entry_point'].get('why',''))}</p></div>
    </div>
  </div>"""
        elif sec.lower() == "cover":
            body = f"""
  <p class="lead">{esc(', '.join(src.get('authors', [])))}</p>
  <p class="lead">{esc(src.get('venue',''))} {esc(src.get('year') or '')}{(' · DOI ' + esc(src['doi'])) if src.get('doi') else ''}</p>
  <div class="note explain"><span class="tag">大綱</span><p class="lead">{esc(tk.get('outline',''))}</p><ul>{''.join(f'<li>{esc(h)}</li>' for h in hl)}</ul></div>"""
        elif sec.lower() == "verdict" and story.get("brief"):
            # @5 (advisor 2026-09-14): why read is page 1; this page answers the rest of 「一開始」 — the problem, every method
            # with what it answers, and each goal with how it was judged and whether it was reached
            b = story["brief"]
            mrows = "".join(f"<tr><td><b>{esc(m.get('name',''))}</b></td><td class='small'>{esc(m.get('kind',''))}</td><td>{esc(m.get('answers',''))}</td><td class='small' style='white-space:nowrap;'>{esc(m.get('locator',''))}</td></tr>" for m in b.get("methods", []))
            vrows = "".join(f"<tr><td><b>{esc(v.get('goal',''))}</b></td><td>{esc(v.get('judged_by',''))}</td><td>{esc(v.get('result',''))}</td><td><span class='val' style='white-space:normal'>{esc(STATUS_ZH.get(v.get('status',''), v.get('status','')))}</span></td></tr>" for v in b.get("verdicts", []))
            conv = f"<p class='small'>學術對話在：{esc(b['conversation'])}</p>" if b.get("conversation") else ""
            body = f"""
  <div class="grid2">
    <div class="stack">
      <div class="note explain"><span class="tag">Q1 它在解什麼問題</span><p>{esc(b.get('problem',''))}</p></div>
      <div class="note explain"><span class="tag">Q2 它怎麼做</span><p>{esc(b.get('approach',''))}</p></div>
      <div class="note ask"><span class="tag">Q3 跟別人差在哪</span><p>{esc(b.get('differs',''))}</p>{conv}</div>
    </div>
    <div class="twrap"><table><thead><tr><th>方法</th><th>類</th><th>回答什麼問題</th><th>出處</th></tr></thead><tbody>{mrows}</tbody></table></div>
  </div>
  <div class="twrap" style="margin-top:6px;"><table><thead><tr><th style="width:16%">目標</th><th>怎麼判讀</th><th>結果</th><th style="width:11%">有沒有達到</th></tr></thead><tbody>{vrows}</tbody></table></div>"""
        elif sec.lower() == "storyline" and tk.get("story_arc"):
            arc = tk["story_arc"]
            crows = "".join(f"<tr><td style='white-space:nowrap;'>{esc(c.get('beat',''))}</td><td><b>{esc(c.get('move',''))}</b></td><td>{esc(c.get('why_it_works',''))}</td><td class='small' style='white-space:nowrap;'>{esc(c.get('locator',''))}</td></tr>" for c in arc.get("craft", []))
            body = f"""
  {kp_box}
  <div class="note evidence" style="margin-top:6px;"><span class="tag">一句話的故事（And–But–Therefore）</span><p class="lead">{esc(arc.get('spine',''))}</p></div>
  <div class="twrap" style="margin-top:6px;"><table><thead><tr><th style="width:8%">拍</th><th style="width:32%">作者這一步怎麼寫</th><th>為什麼對讀者有效（可以學的寫法）</th><th style="width:12%">出處</th></tr></thead><tbody>{crows}</tbody></table></div>"""
        elif sec.lower() == "closing":
            cl = tk.get("closing", {})
            body = f"""
  <div class="stack">
    <div class="note evidence"><span class="tag">這篇幫我建立的研究依據</span><p class="lead">{esc(cl.get('basis',''))}</p></div>
    <div class="note explain"><span class="tag">對後續量測／設計的幫助</span><p class="lead">{esc(cl.get('help',''))}</p></div>
    {('<div class="note ask"><span class="tag">下一步</span><p class="lead">' + esc(cl.get('next','')) + '</p></div>') if cl.get('next') else ''}
    {('<ul class="lead">' + ''.join(f'<li>{esc(h)}</li>' for h in hl) + '</ul>') if hl else ''}
  </div>"""
        else:
            hl_html = "".join(f'<div class="note explain"><p style="font-size:clamp(15px,1.4vw,19px);font-weight:600;margin:2px 0;">{esc(h)}</p></div>' for h in hl)
            fr = pg.get("figure_read") or {}
            ta_html = (f'<div class="note evidence" style="padding:4px 10px;"><span class="tag">這頁帶走</span><p style="font-weight:700;margin:2px 0;">{esc(pg["takeaway"])}</p></div>') if pg.get("takeaway") else ""
            fr_html = ('<div class="note ask" style="padding:4px 10px;"><span class="tag">這張圖怎麼看</span>' + "".join(f"<p class='small' style='margin:1px 0;'><b>{lab}</b>{esc(fr[k])}</p>" for k, lab in FIG_READ_PARTS if fr.get(k)) + "</div>") if fr else ""
            if pg.get("figure"):
                body = f"""
  <div class="fig-main" style="min-height:min-content;">
    <figure class="fig"><img src="{data_uri(run_dir / pg['figure'])}" alt="{esc(pg.get('title',''))}" style="max-height:56vh;"><figcaption>{esc(pg.get('locator',''))}</figcaption></figure>
    <div class="stack">{ta_html}{hl_html}{fr_html}</div>
  </div>"""
            else:
                body = f'<div class="stack">{ta_html}{hl_html}</div>'
        badge = " · 練習・複習用（正式簡報＝實驗室範本英文版）" if i == 1 else ""
        ask_html = (f'<p class="small" style="margin:0;"><b>這頁回答：</b>{esc(pg["asks"])}' + (f'　·　{esc(pg["beat"])}' if pg.get("beat") else "") + "</p>") if pg.get("asks") else ""
        parts.append(f"""
<section class="slide" id="d{i}">
  <div class="eyebrow"><span class="no">{i:02d}</span><span>{esc(sec)}{badge}{(' · 層 ' + esc(pg['layer'])) if pg.get('layer') else ''}{(' · ' + esc(pg.get('locator',''))) if pg.get('locator') else ''}</span></div>
  <h2>{esc(pg.get('title',''))}</h2>{ask_html}{body}
  {notes}
</section>""")
    backup, n = backup_pages_html(story, len(story["deck"]["pages"]) + 1)
    return splice(story, "\n".join(parts) + backup + glossary_slide(story, n), f"【多頁簡報・練習用】{src.get('title','')[:60]}")


def backup_pages_html(story, start_no):
    """Practice deck only (B-13): the first BACKUP_MAX challenge questions as 備份頁 after the last page, flipped to only
    when asked. The formal lab PPTX never gets them (formal-deck.md)."""
    challenges = [q for q in (story.get("talk") or {}).get("if_asked", []) if q.get("kind") == "challenge"][:BACKUP_MAX]
    out = []
    for j, q in enumerate(challenges):
        c = q.get("challenge") or {}
        rows = "".join(f'<div class="note {cls}"><span class="tag">{label}</span><p class="lead">{esc(c.get(k, "") or "（未填）")}</p></div>'
                       for (k, label), cls in zip(CHALLENGE_PARTS, ("explain", "ask", "evidence")))
        loc = c.get("locator", "")
        out.append(f"""
<section class="slide backup" id="b{j + 1}">
  <div class="eyebrow"><span class="no">{start_no + j:02d}</span><span>備份頁 · 被問時才翻（練習版限定）{(' · ' + esc(loc)) if loc else ''}</span></div>
  <h2>被問：{esc(q.get('q', ''))}</h2>
  <div class="stack">{rows}</div>
</section>""")
    return "".join(out), start_no + len(challenges)


# ---------------------------------------------------------------- talk script (the explainer's 口述稿 section; talk-script.md since 2026-11-03 is no longer written)
def if_asked_bracket(q):
    """One if-asked memo in the lab's bracket form; a challenge-kind question prints its admit / reason / settle parts."""
    c = q.get("challenge") or {}
    if q.get("kind") == "challenge" and any(c.get(x) for x, _ in CHALLENGE_PARTS):
        return f"（{q.get('q','')} → " + "；".join(f"{lab}：{c[x]}" for x, lab in CHALLENGE_PARTS if c.get(x)) + "）"
    return f"（{q.get('q','')} → {q.get('a','')}）"


def talk_only_parts(tk):
    """ex_blocks for a run that declares `talk` but no `deck` (so talk_parts cannot run): the outline, the if-asked memos and the
    closing, i.e. what the former 上台要點 section held, so the 口述稿 section carries them (user ruling 2026-11-03: only 口述稿 stays)."""
    ex = []
    if tk.get("outline"):
        ex.append(("labelled", "分段", tk["outline"]))
    if tk.get("if_asked"):
        ex += [("head", "被問時（括號備忘）"), ("bullets", [if_asked_bracket(q) for q in tk["if_asked"]])]
    cl = tk.get("closing") or {}
    closing = [f"{lab}：{cl[k]}" for k, lab in (("basis", "這篇文獻幫我建立的研究依據"), ("help", "對後續量測／設計的幫助"), ("next", "下一步")) if cl.get(k)]
    if closing:
        ex += [("head", "結尾"), ("bullets", closing)]
    return ex


def talk_parts(story):
    """The deep-mode talk script, built ONCE from story.json. Returns (md_lines, ex_blocks): md_lines is the Markdown body the
    retired talk-script.md carried (kept for build_talk_md and its selftests); ex_blocks is the part the explainer's 口述稿
    section prints (user ruling 2026-11-03: the talk script lives inside the explainer; the preamble, brief tables and story-arc
    table already have their own explainer sections, so they are md-only). ex_blocks items:
      ("head", text) · ("labelled", label, text) · ("bullets", [text, …]) · ("steps", [(title, [(label, text), …]), …])
    — plain strings, the explainer adds the glossary markers and the bold labels."""
    src, tk, run, lg = story["source"], story["talk"], story["run"], story["logic"]
    title = src.get("title", "")
    ex = []
    body = [f"# 【口述稿】報告時我要說的話：{title}", "",
            "> 這份是報告的口述內容，照實驗室既有備註的講法（開場公式、分段句、被問時的括號備忘、結尾的研究依據與幫助）。先讀模型版，再改成自己的話（最後一節）。正式簡報（實驗室 pptx 範本改英文，明確要求時才做）的演講者備註以這份為底。", "",
            f"- Keypoint：{lg.get('keypoint','')}", ""]
    if lg.get("keypoint_description"):
        body += [f"- 解讀（讀書心得的終極詮釋）：{lg['keypoint_description']}", ""]
    if lg.get("bindings"):
        body += ["- slogan 裡的角色在這篇＝：" + "；".join(f"{x.get('role','')}＝{x.get('referent','')}（{x.get('locator','')}）" for x in lg["bindings"]), ""]
    cell = lambda s: str(s or "").replace("|", "／").replace("\n", " ")
    b = story.get("brief")
    if b:
        # @5 (advisor 2026-09-14): the four things said up front, as the presenter's crib before the opening
        body += ["## 上台前先記住：它在解什麼、用了哪些方法、有沒有做到、怎麼判讀", "",
                 f"- **Q1 它在解什麼問題：** {b.get('problem','')}", f"- **Q2 它怎麼做：** {b.get('approach','')}",
                 f"- **Q3 跟別人差在哪：** {b.get('differs','')}" + (f"（學術對話在 {b['conversation']}）" if b.get("conversation") else ""), "",
                 "| 方法 | 類 | 回答什麼問題 | 出處 |", "|---|---|---|---|"]
        body += [f"| {cell(m.get('name'))} | {cell(m.get('kind'))} | {cell(m.get('answers'))} | {cell(m.get('locator'))} |" for m in b.get("methods", [])]
        body += ["", "| 目標 | 怎麼判讀 | 結果 | 有沒有達到 |", "|---|---|---|---|"]
        body += [f"| {cell(v.get('goal'))} | {cell(v.get('judged_by'))} | {cell(v.get('result'))} | {STATUS_ZH.get(v.get('status', ''), cell(v.get('status')))} |" for v in b.get("verdicts", [])] + [""]
    body += ["## 開場", "", tk.get("opening", ""), "", "## 分段", "", tk.get("outline", ""), ""]
    ex += [("labelled", "開場", tk.get("opening", "")), ("labelled", "分段", tk.get("outline", ""))]
    pages = story["deck"]["pages"]
    if any(p.get("asks") for p in pages):
        body += ["## 問題鏈（每頁回答一個問題；照順序念一遍，就是這場報告的故事線）", ""]
        body += [f"{i}. {p['asks']}" + (f" → {p['takeaway']}" if p.get("takeaway") else "") for i, p in enumerate(pages, 1) if p.get("asks")] + [""]
        ex += [("head", "問題鏈（每頁回答一個問題；照順序念一遍，就是這場報告的故事線）"),
               ("steps", [(p["asks"], [("帶走", p["takeaway"])] if p.get("takeaway") else []) for p in pages if p.get("asks")])]
    ex_pages = []
    for i, pg in enumerate(pages, 1):
        lay = f"・{pg['layer']} 層" if pg.get("layer") else ""
        beat = f"・{pg['beat']}" if pg.get("beat") else ""
        body += [f"## {i}. {pg.get('title','')}（{pg.get('section','')}{lay}{beat}）", ""]
        parts = []
        if pg.get("asks"):
            body += [f"**這頁回答：** {pg['asks']}", ""]
            parts.append(("這頁回答", pg["asks"]))
        body += [f"**說：** {pg.get('notes','')}", ""]
        parts.append(("說", pg.get("notes", "")))
        fr = pg.get("figure_read")
        if fr:
            body += ["> **這張圖怎麼看**", ">"] + [f"> - {lab}{fr[k]}" for k, lab in FIG_READ_PARTS if fr.get(k)] + [""]
            parts.append(("這張圖怎麼看", "　".join(f"{lab}{fr[k]}" for k, lab in FIG_READ_PARTS if fr.get(k))))
        if pg.get("takeaway"):
            body += [f"**這頁帶走：** {pg['takeaway']}", ""]
            parts.append(("這頁帶走", pg["takeaway"]))
        ex_pages.append((f"{pg.get('title','')}（{pg.get('section','')}{lay}{beat}）", parts))
    ex += [("head", "逐頁怎麼講"), ("steps", ex_pages)]
    if any(p.get("layer") for p in pages):
        by, steps = cut_plan(pages)
        nums = lambda xs: "、".join(f"第 {x} 頁" for x in xs) or "（無）"
        cut = [f"先刪 C：{nums(by['C'])}", f"再壓縮 B（每頁只講第一條重點）：{nums(by['B'])}", f"A 不動：{nums(by['A'])}",
               "頁數與時間（實驗室規則：頁數 ≈ 分鐘 × 1.5）：" + "；".join(f"{label} {k} 頁 ≈ {k / 1.5:.0f} 分鐘" for k, label in steps),
               f"口述長度估計（備註字數，每分鐘 {SPEAK_RATE} 字當量；排練計時一次後校正）：" + "；".join(f"{label} ≈ {m:.1f} 分鐘" for m, label in spoken_minutes(story))]
        body += ["## 時間不夠時（刪減順序）", ""] + [f"- {x}" for x in cut] + [""]
        ex += [("head", "時間不夠時（刪減順序）"), ("bullets", cut)]
    if tk.get("if_asked"):
        asked = tk["if_asked"]
        body += ["## 被問時（括號備忘）", ""]
        ex.append(("head", "被問時（括號備忘）"))
        if any(q.get("kind") for q in asked):
            groups = (("challenge", "挑戰（先承認 → 為什麼這樣選 → 什麼證據能定案）"), ("clarify", "澄清"), ("extend", "延伸"), (None, "未分類"))
            for k, label in groups:
                grp = [q for q in asked if (q.get("kind") or None) == k]
                if not grp:
                    continue
                body += [f"### {label}", ""]
                brackets = [if_asked_bracket(q) for q in grp]
                body += brackets + [""]
                ex += [("labelled", label, ""), ("bullets", brackets)]
        else:
            brackets = [f"（{q.get('q','')} → {q.get('a','')}）" for q in asked]
            body += brackets + [""]
            ex.append(("bullets", brackets))
    arc = tk.get("story_arc")
    if arc:
        body += ["## 這篇怎麼說完一個研究故事（可以學的寫法）", "", f"**一句話：** {arc.get('spine','')}", "",
                 "| 拍 | 作者這一步怎麼寫 | 為什麼對讀者有效 | 出處 |", "|---|---|---|---|"]
        body += [f"| {cell(c.get('beat'))} | {cell(c.get('move'))} | {cell(c.get('why_it_works'))} | {cell(c.get('locator'))} |" for c in arc.get("craft", [])] + [""]
    cl = tk.get("closing", {})
    body += ["## 結尾", "", f"這篇文獻幫我建立的研究依據：{cl.get('basis','')}", "", f"對後續量測／設計的幫助：{cl.get('help','')}", ""]
    closing = [f"這篇文獻幫我建立的研究依據：{cl.get('basis','')}", f"對後續量測／設計的幫助：{cl.get('help','')}"]
    if cl.get("next"):
        body += [f"下一步：{cl['next']}", ""]
        closing.append(f"下一步：{cl['next']}")
    ex += [("head", "結尾"), ("bullets", closing)]
    body += ["## 我的版本（上台前用自己的話重寫；留下模型版做對照）", "", "> _（空白：先自己講一遍，錄下來，再寫）_", "", "相關：[[home]]", ""]
    return body, ex


def build_talk_md(story):
    """The Markdown form of the deep-mode talk script (the retired talk-script.md). No longer written to a run folder since
    2026-11-03; kept as the md rendering of talk_parts for the selftests that check the script's sections."""
    run, src = story["run"], story["source"]
    today = run.get("created", "")[:10] or dt.date.today().isoformat()
    title = src.get("title", "")
    fm = ["---", "xi: 1",
          "what: " + json.dumps(f"【口述稿】{title} — 報告時我要說的話，實驗室備註慣例 (spoken memo in the lab's speaker-notes voice, personal, to be rewritten)", ensure_ascii=False),
          "tags: [paper-story, talk-script, literature]",
          "aliases: [" + json.dumps(f"{run.get('id','')} 口述稿", ensure_ascii=False) + ", " + json.dumps(f"{title[:60]} talk script", ensure_ascii=False) + "]",
          f"date: {today}", "status: draft", "kind: literature",
          "source: " + json.dumps(f"file: {run.get('id','')}/source/paper.pdf", ensure_ascii=False),
          "verified: " + json.dumps(f"model-drafted {today}; the presenter rewrites it in their own words", ensure_ascii=False),
          "review-when: \"the presenter rewrites it, or the keypoint changes\"", "domain: []", "promoted-to: \"-\"", "---", ""]
    return "\n".join(fm + talk_parts(story)[0])


def story_script_parts(story):
    """Story-mode spoken walk (user ruling 2026-11-03 G5, the senior's pattern: source line -> purpose line -> each tile: axes ->
    what is seen -> what it means; the table is never read aloud). Same ex_blocks shape as talk_parts. Returns [] when the
    run declares neither onepage.script nor any tile notes."""
    op = story.get("onepage", {})
    sc = op.get("script") or {}
    ex = []
    if sc.get("source_line"):
        ex.append(("labelled", "出處", sc["source_line"]))
    if sc.get("purpose_line"):
        ex.append(("labelled", "目的", sc["purpose_line"]))
    tiles = []
    for k, f in enumerate(op.get("figures", [])):
        if not f.get("notes"):
            continue
        step = STEP_ZH.get(f.get("step", ""), "")
        tiles.append((f"({chr(97 + k)}) {f.get('caption', '')}" + (f"（{step}）" if step else ""), [("說", f["notes"])]))
    if tiles:
        ex += [("head", "逐格走圖：先說座標，再說看到什麼，最後說代表什麼"), ("steps", tiles)]
    return ex


def blocks_plain(ex):
    """Plain text of ex_blocks (labels included), the text S9 reads."""
    out = []
    for b in ex:
        if b[0] in ("head",):
            out.append(b[1])
        elif b[0] == "labelled":
            out.append(f"{b[1]}：{b[2]}")
        elif b[0] == "bullets":
            out += b[1]
        elif b[0] == "steps":
            for title, parts in b[1]:
                out.append(title + " " + " ".join(f"{lab}：{t}" for lab, t in parts))
    return "\n".join(out)


# ---------------------------------------------------------------- fit (S7)
def _measure(path: Path, w, h):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(path.resolve().as_uri()); pg.wait_for_timeout(700)
        rep = pg.evaluate("() => { if (window.__fitRun) window.__fitRun(); return window.__fitReport ? window.__fitReport() : null }")
        b.close()
    return rep


def s7_fit(paths, G):
    try:
        import playwright  # noqa
    except Exception as e:
        G.add("S7", "WARN", f"fit-gate instrument unavailable ({e.__class__.__name__}) — DOWNGRADE-AND-FORWARD: check both html products by eye at 1707×830 and 1280×720")
        return
    try:
        html = paths[0].read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bad = tdp / "ctrl_bad.html"
            bad.write_text(html.replace('<section class="slide" id="p1">', '<section class="slide" id="p1"><div style="height:4000px;min-height:4000px;flex:0 0 auto;"></div>', 1), encoding="utf-8")
            good = tdp / "ctrl_good.html"
            good.write_text(html.replace("<!-- ==== chrome ==== -->", '<section class="slide" id="ctrl"><div class="eyebrow"><span class="no">00</span><span>control</span></div><h2>control</h2></section>\n<!-- ==== chrome ==== -->', 1), encoding="utf-8")
            rb, rg = _measure(bad, *VIEWPORTS[0]), _measure(good, *VIEWPORTS[0])
            if not rb or not rb[0].get("overflow"):
                G.add("S7", "FAIL", "instrument fault: known-overflow control not reported"); return
            if not rg or rg[-1].get("overflow"):
                G.add("S7", "FAIL", "instrument fault: known-fitting control reported as overflow"); return
        worst = []
        for path in paths:
            for w, h in VIEWPORTS:
                rep = _measure(path, w, h)
                if rep is None:
                    G.add("S7", "FAIL", f"__fitReport() missing in {path.name} at {w}×{h}"); return
                for r in rep:
                    if r.get("overflow"):
                        worst.append(f"{path.name} page {r['i']} overflows at {w}×{h} (need {r['need']}, avail {r['avail']})")
                    elif r.get("scale", 1) < LEGIBLE_SCALE:
                        worst.append(f"{path.name} page {r['i']} scale {r['scale']:.2f} at {w}×{h}")
        overflow = [x for x in worst if "overflows" in x]
        if overflow:
            G.add("S7", "FAIL", "measured fit: " + "; ".join(overflow) + " — page content, never cut: split the page or shorten highlights")
        elif worst:
            G.add("S7", "WARN", "measured fit: " + "; ".join(worst[:6]) + f" — legible floor {LEGIBLE_SCALE}")
        else:
            G.add("S7", "PASS", f"measured fit on {len(paths)} html products at {', '.join(f'{w}×{h}' for w, h in VIEWPORTS)} (controls fired)")
    except Exception as e:
        G.add("S7", "WARN", f"fit-gate could not run ({e.__class__.__name__}: {str(e)[:100]}) — verify by eye")


def s7b_fill(paths, G):
    """S7b — width property (2026-09-04, ops/environment.md §Display): the fill-gate beside S7,
    over the same BUILT files. The shell declares data-page-class="deck", so every .slide is
    measured; downgrade-and-forward when the tool or the browser is missing."""
    import sys as _sys
    fg_dir = SKILL_DIR.parent.parent / "tools" / "page-fill-gate"
    if not (fg_dir / "fill_gate.py").exists():
        G.add("S7b", "WARN", f"fill-gate tool missing at {fg_dir} — width property UNVERIFIED, check by eye at 1707×830")
        return
    try:
        _sys.path.insert(0, str(fg_dir))
        import fill_gate as fg
        rows = fg.gate_paths([str(p) for p in paths], viewports=[VIEWPORTS[0], (1920, 950)], controls=True)
    except Exception as e:
        G.add("S7b", "WARN", f"fill-gate could not run ({e.__class__.__name__}: {str(e)[:100]}) — verify by eye at 1707×830")
        return
    # The gate's row status also carries its in-page consistency checks (2026-10-31); this gate reports
    # the WIDTH property, so it reads `width_status` and names consistency findings on their own line.
    ws = lambda r: r.get("width_status", r["status"])
    bad = [r for r in rows if ws(r) == "FAIL" and not r["control"]]
    warn = [r for r in rows if ws(r) == "WARN" and not r["control"]]
    cons = [r for r in rows if r.get("consistency_status", "PASS") != "PASS" and not r["control"]]
    if cons:
        sev = "FAIL" if any(r["consistency_status"] == "FAIL" for r in cons) else "WARN"
        G.add("S7b", sev, "in-page consistency (same-class drift / rules declared twice): " + "; ".join(
            f"{Path(r['target']).name}: {r['consistency_reasons'][0][:90]}" for r in cons[:3]))
    if bad:
        G.add("S7b", "FAIL", "measured fill: " + "; ".join(f"{Path(r['target']).name} {r['viewport']} reach {r['reach']:.0%}: {r['reasons'][0][:90]}" for r in bad[:4]))
    elif warn:
        G.add("S7b", "WARN", "measured fill: " + "; ".join(f"{Path(r['target']).name} {r['viewport']}: {r['reasons'][0][:90]}" for r in warn[:4]))
    else:
        G.add("S7b", "PASS", f"measured fill on {len(paths)} html products at 1707×830 / 1920×950 (class deck, controls fired)")


# ---------------------------------------------------------------- pptx
def _fit_pic(ph, slide, path: Path, x, y, w, h):
    from PIL import Image
    with Image.open(path) as im:
        ar = im.width / im.height
    w_ = w if w / ar <= h else h * ar
    h_ = w_ / ar
    ph.add_pic(slide, path, x + (w - w_) / 2, y + (h - h_) / 2, w=w_, h=h_)
    return h_


def build_onepage_pptx(story, run_dir, out: Path, G):
    sys.path.insert(0, str(SCRIPTS))
    import pptx_helpers as ph
    from pptx import Presentation
    from pptx.util import Inches
    src, op, why = story["source"], story["onepage"], story["why_me"]
    prs = Presentation(); W, Hh = 13.333, 7.5
    prs.slide_width, prs.slide_height = Inches(W), Inches(Hh)
    s = ph.blank(prs)
    _, tf = ph.tb(s, 0.55, 0.25, W - 1.1, 0.5)
    ph.para(tf, src.get("title", ""), size=18 if len(src.get("title", "")) > 60 else 20, bold=True, first=True, space_after=0, fit_w=W - 1.1)
    _, tf = ph.tb(s, 0.55, 0.78, W - 1.1, 0.3)
    ph.para(tf, cite(src) + (" · " + ", ".join(src.get("authors", [])[:4]) if src.get("authors") else ""), size=9.5, color=ph.MUTED, first=True, space_after=0)
    ph.add_rect(s, 0.55, 1.12, W - 1.1, 0.62, ph.GLASS_BG, line_color=ph.GLASS, rounded=True)
    _, tf = ph.tb(s, 0.67, 1.15, W - 1.34, 0.58)
    ph.para(tf, [("KEYPOINT｜", {"bold": True, "color": ph.GLASS}), (kp_text(story), {"bold": True}),
                 ("　·　為什麼讀它：" + why.get("why_read", ""), {"color": ph.MUTED, "size": 9.5})], size=11, first=True, space_after=0, fit_w=W - 1.34)
    figs = op["figures"]; rows = math.ceil(len(figs) / 2)
    gx, gy, gw, gh = 0.55, 1.9, 7.4, 5.0
    cw, chh = (gw - 0.15) / 2, (gh - 0.12 * (rows - 1)) / rows
    for i, f in enumerate(figs):
        cx, cy = gx + (i % 2) * (cw + 0.15), gy + (i // 2) * (chh + 0.12)
        fs = tile_files(f)   # story@6 tile: its panels share the tile's cell side by side
        pw = cw / len(fs)
        for j, fn in enumerate(fs):
            _fit_pic(ph, s, run_dir / fn, cx + j * pw, cy, pw - (0.05 if len(fs) > 1 else 0), chh - 0.28)
        _, tf = ph.tb(s, cx, cy + chh - 0.28, cw, 0.26)
        ph.para(tf, (f.get("caption", "") + (" · " + f["locator"] if f.get("locator") else ""))[:80], size=8, color=ph.MUTED, first=True, space_after=0, fit_w=cw)
    tx, tw = 8.15, W - 8.15 - 0.55
    rows_t = [["欄位", "內容"]] + [[k, op["table"][kk][:CELL_MAX]] for k, kk in table_rows(op)]
    ph.add_table(s, tx, gy, tw, rows_t, col_w=[1.0, 3.7], font=9, header_font=8.5, row_h=0.42)
    ph.ref_strip(s, W, Hh, cite(src))
    ph.notes(s, story["talk"].get("opening", "") + "\n\n" + story["talk"].get("closing", {}).get("basis", ""))
    s2 = ph.blank(prs)
    ph.eyebrow_title(s2, W, "詞彙", "頁面上出現的每個專有名詞")
    rows_g = [["詞", "說明"]] + [[t["term"] + (f" ({t['en']})" if t.get("en") and t["en"] != t["term"] else ""), t["gloss"][:110]] for t in story.get("terms", [])[:14]]
    ph.add_table(s2, 0.55, 1.4, W - 1.1, rows_g, col_w=[1.6, 5.0], font=9, header_font=8.5, row_h=0.34)
    ph.number_pass(prs, W, Hh); prs.save(str(out))
    ph.FORBIDDEN_TERMS = ("样例禁词",); ph.VALUES = (kp_text(story)[:30],)
    try:
        ph.run_gates(out, min_links=0); G.add("P1", "PASS", f"{out.name}: keypoint verbatim, no forbidden variant")
    except SystemExit as e:
        G.add("P1", "FAIL", f"{out.name}: {e}")


def build_deck_pptx(story, run_dir, out: Path, G):
    sys.path.insert(0, str(SCRIPTS))
    import pptx_helpers as ph
    from pptx import Presentation
    from pptx.util import Inches
    src, ax, why, lg, tk = story["source"], story["axis"], story["why_me"], story["logic"], story["talk"]
    prs = Presentation(); W, Hh = 13.333, 7.5
    prs.slide_width, prs.slide_height = Inches(W), Inches(Hh)
    for i, pg in enumerate(story["deck"]["pages"], 1):
        s = ph.blank(prs); sec = pg.get("section", ""); hl = pg.get("highlights", [])
        ph.eyebrow_title(s, W, f"{sec}" + (f" · {pg['locator']}" if pg.get("locator") else ""), pg.get("title", ""))
        if sec.lower() == "keypoint":
            _, tf = ph.tb(s, 0.55, 1.6, 6.0, 4.8)
            ph.para(tf, [("為什麼讀它　", {"bold": True, "color": ph.GLASS}), (why.get("why_read", ""), {})], size=14, first=True, space_after=10, fit_w=6.0)
            ph.para(tf, [("對我有什麼幫助　", {"bold": True, "color": ph.GLASS}), (why.get("helps", ""), {})], size=14, space_after=10, fit_w=6.0)
            ph.add_rect(s, 6.9, 1.6, W - 6.9 - 0.55, 1.9, ph.PASS_BG if hasattr(ph, "PASS_BG") else ph.GLASS_BG, line_color=ph.PASS_C, rounded=True)
            _, tf = ph.tb(s, 7.02, 1.65, W - 6.9 - 0.79, 1.8)
            ph.para(tf, [("KEYPOINT｜邏輯抽取", {"bold": True, "color": ph.PASS_C, "size": 10})], size=10, first=True, space_after=4)
            ph.para(tf, lg.get("keypoint", ""), size=15, bold=True, space_after=0, fit_w=W - 6.9 - 0.79)
            _, tf = ph.tb(s, 6.9, 3.7, W - 6.9 - 0.55, 2.6)
            ph.para(tf, [("主軸 · 切入點　", {"bold": True, "color": ph.ASK}), (ax["entry_point"].get("what", ""), {})], size=12, first=True, space_after=6, fit_w=W - 6.9 - 0.55)
            ph.para(tf, [("為什麼是這個切入點　", {"bold": True, "color": ph.ASK}), (ax["entry_point"].get("why", ""), {})], size=11.5, space_after=0, fit_w=W - 6.9 - 0.55)
        elif sec.lower() == "cover":
            _, tf = ph.tb(s, 0.55, 1.6, W - 1.1, 4.5)
            ph.para(tf, ", ".join(src.get("authors", [])), size=14, first=True, space_after=8)
            ph.para(tf, f"{src.get('venue','')} {src.get('year') or ''}" + (f" · DOI {src['doi']}" if src.get("doi") else ""), size=13, color=ph.MUTED, space_after=14)
            ph.para(tf, tk.get("outline", ""), size=14, bold=True, space_after=6)
            for h in hl:
                ph.para(tf, "• " + h, size=13, space_after=3)
        elif sec.lower() == "closing":
            cl = tk.get("closing", {})
            _, tf = ph.tb(s, 0.55, 1.6, W - 1.1, 5.0)
            ph.para(tf, [("這篇幫我建立的研究依據　", {"bold": True, "color": ph.PASS_C}), (cl.get("basis", ""), {})], size=14, first=True, space_after=12, fit_w=W - 1.1)
            ph.para(tf, [("對後續量測／設計的幫助　", {"bold": True, "color": ph.GLASS}), (cl.get("help", ""), {})], size=14, space_after=12, fit_w=W - 1.1)
            if cl.get("next"):
                ph.para(tf, [("下一步　", {"bold": True, "color": ph.ASK}), (cl["next"], {})], size=14, space_after=12, fit_w=W - 1.1)
            for h in hl:
                ph.para(tf, "• " + h, size=13, space_after=3)
        else:
            if pg.get("figure"):
                _fit_pic(ph, s, run_dir / pg["figure"], 0.55, 1.55, 6.9, 5.2)
                _, tf = ph.tb(s, 7.75, 1.7, W - 7.75 - 0.55, 5.0)
            else:
                _, tf = ph.tb(s, 0.55, 1.7, W - 1.1, 5.0)
            for j, h in enumerate(hl):
                ph.para(tf, "• " + h, size=17, bold=True, first=(j == 0), space_after=12, fit_w=(W - 7.75 - 0.55) if pg.get("figure") else (W - 1.1))
        notes = pg.get("notes", "")
        if i == len(story["deck"]["pages"]) and tk.get("if_asked"):
            notes += "\n\n" + "\n".join(f"（{q.get('q','')} → {q.get('a','')}）" for q in tk["if_asked"])
        ph.notes(s, notes)
    ph.number_pass(prs, W, Hh); prs.save(str(out))
    ph.FORBIDDEN_TERMS = ("样例禁词",); ph.VALUES = (lg.get("keypoint", "")[:30],)
    try:
        ph.run_gates(out, min_links=0); G.add("P1", "PASS", f"{out.name}: keypoint verbatim, no forbidden variant")
    except SystemExit as e:
        G.add("P1", "FAIL", f"{out.name}: {e}")


# ---------------------------------------------------------------- render / sample / selftest
def strip_tags(html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


GLOSS_RE = re.compile(r'<section class="slide" id="gloss-page">.*?</section>', re.S)


def page_text(html):
    """Visible text WITHOUT the glossary page. S6 / V8 must not count a term as 'appearing on a page' because the
    glossary lists it — round 2 desk finding U-6: with the glossary included the unused-term branch could never fire."""
    return strip_tags(GLOSS_RE.sub(" ", html))


def render(run_dir: Path, do_pptx, do_fit, check_shell, presenter, gates_on=True, legacy_html=False, explainer=True):
    story = json.loads((run_dir / "story.json").read_text(encoding="utf-8"))
    G = Gates()
    ok = s1_schema(story, G)
    rendered = ""
    written = []
    shown = None   # the 口述稿 text the explainer prints (S9 reads it); None = no explainer built
    if ok:
        # round 2 (2026-09-03) desk finding U-5: `story` mode (one page per paper) authors no deck and no talk —
        # both are optional in the schema unless mode == deep; S5 / S9 SKIP when absent, the talk script needs both.
        mode = story.get("run", {}).get("mode", "deep")
        has_deck, has_talk = "deck" in story, "talk" in story
        ok4 = s4_onepage(story, run_dir, G)
        s4d_tiles(story, G)
        if has_deck:
            ok5 = s5_deck(story, run_dir, G)
        else:
            ok5 = False
            G.add("S5", "SKIP", f"no deck in story.json — mode {mode} (one page per paper): the deck product is not authored")
        try:
            # 2026-10-12 (user ruling): class-A HTML is ONE explainer page (story_explainer.py -> tools/carriers html-explainer).
            # The two legacy pages are still built in memory — S6 reads their visible text — and written only with --legacy-html.
            html_parts = []
            if ok4:
                html_parts.append((OUT["onepage_html"], build_onepage_html(story, run_dir, presenter)))
            if ok5:
                html_parts.append((OUT["deck_html"], build_deck_html(story, run_dir, presenter)))
            if legacy_html:
                for name, h in html_parts:
                    p = run_dir / name; p.write_text(h, encoding="utf-8"); written.append(p)
            names = [p.name for p in written]
            # 2026-11-03 (user ruling): talk-script.md is no longer written — the talk script is the explainer's 口述稿 section
            # (and stays in the PPTX speaker notes). A talk-script.md already in the run folder is left untouched.
            G.add("OUT", "PASS", "wrote " + (", ".join(names) if names else "no separate file (the talk script is the explainer's 口述稿 section; talk-script.md is no longer written)"))
            rendered = "".join(page_text(h) for _, h in html_parts)
            if explainer and (ok4 or ok5):
                import story_explainer
                rc = story_explainer.build(run_dir)
                G.add("EX", "PASS" if rc == 0 else "FAIL",
                      f"{story_explainer.STEM}.html via tools/carriers {story_explainer.CARRIER}: " + ("build PASS, check ok" if rc == 0 else "build or check failed (output above)"))
                if rc == 0:
                    shown = story_explainer.talk_section_text(run_dir)
        except Exception as e:
            G.add("OUT", "FAIL", f"render error: {e.__class__.__name__}: {str(e)[:160]}")
        if gates_on:
            s2_whys(story, G); s3_locators(story, G); s6_terms(story, rendered, G)
            if has_talk:
                s9_talk(story, G, shown)
            else:
                G.add("S9", "SKIP", f"no talk in story.json — mode {mode}: talk conventions not applicable")
            s4b_conclusion(story, G); s4c_figure_kinds(story, G); s10_quotes(story, run_dir, G); st_json = s11_coverage(story, run_dir, G); s12_anomalies(story, st_json, G)
            s13_drift_checklist(story, G); s14_stray_script(story, G); s15_bindings(story, G); s16_description(story, G); s17_layers_questions(story, G)
            s18_brief(story, G); s19_figure_reading(story, G); s20_flow(story, G)
            if check_shell:
                s8_shell(G)
            if do_fit and written:
                s7_fit(written, G)
                s7b_fill(written, G)
        if do_pptx:
            G.add("P0", "INFO", "pptx built from story.json on explicit request — the HTML layout in pptx form, NOT the formal deck (lab template, English: references/formal-deck.md)")
            try:
                if ok4:
                    build_onepage_pptx(story, run_dir, run_dir / OUT["onepage_pptx"], G)
                if ok5:
                    build_deck_pptx(story, run_dir, run_dir / OUT["deck_pptx"], G)
            except Exception as e:
                G.add("P1", "FAIL", f"pptx build error: {e.__class__.__name__}: {str(e)[:160]}")
    (run_dir / OUT["gates"]).write_text(G.text() + "\n", encoding="utf-8")
    print(G.text())
    return 2 if G.failed else 0


def make_sample(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "figures").mkdir(exist_ok=True)
    from PIL import Image, ImageDraw
    for i, col in enumerate(("#3e7cab", "#c2491d", "#1a7f4e"), 1):
        im = Image.new("RGB", (900, 600), "white"); d = ImageDraw.Draw(im)
        d.rectangle([60, 40, 860, 540], outline="#1c2733", width=2)
        pts = [(60 + k * 80, 540 - int(450 * (1 - 1 / (1 + (k / 3.0) ** 2)))) for k in range(11)]
        d.line(pts, fill=col, width=5); d.text((80, 55), f"SYNTHETIC S{i}", fill="#5c6b7a")
        im.save(dest / "figures" / f"S{i}.png")
    story = json.loads(SAMPLE.read_text(encoding="utf-8"))
    (dest / "story.json").write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    src = dest / "source"; src.mkdir(exist_ok=True)
    (src / "paper.txt").write_text(
        "<!-- p.1 -->\nAbstract\nIn-situ sidewall passivation suppresses the post-stress dynamic on-resistance rise to a quarter of the untreated value. "
        "The devices are vertical trench MOSFETs on free-standing GaN; the passivation is grown in the same chamber without breaking vacuum.\n"
        "1. Introduction\nDynamic on-resistance decides the switching loss of vertical GaN devices, and trap states at the trench sidewall are the usual suspect.\n"
        "<!-- p.8 -->\n5. Discussion\nWe consider in-situ passivation a viable route towards commercial vertical GaN, although only C-V inference supports the mechanism. "
        "A direct trap spectroscopy on the passivated sidewall remains to be done; the present data cannot separate interface from bulk contributions.\n",
        encoding="utf-8")
    (src / "structure.json").write_text(json.dumps({
        "schema": "paper-distill/structure@1", "units": [
            {"id": "§1", "kind": "section", "page": 1, "text": "1. Introduction"},
            {"id": "§5", "kind": "section", "page": 8, "text": "5. Discussion"}],
        "subheadings": [], "anomalies": []}, ensure_ascii=False, indent=1), encoding="utf-8")
    return dest


def selftest(keep):
    td = keep or Path(tempfile.mkdtemp(prefix="paper-story-selftest-"))
    base = make_sample(td / "sample")
    results = []

    def case(name, mutate, gate, expect, needle=None, raw=False):
        """needle (round 4): a WARN case also asserts its own message — a gate that warns for a different reason is not the
        control firing (L-062: assert on the value the defect changes, not on the label).
        raw (2026-11-03): run the later gates even when the schema rejects the mutation — for a gate that repeats a schema rule
        (S4's side-evidence necessity) and must fire on its own."""
        d = td / name
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(base, d)
        st = json.loads((d / "story.json").read_text(encoding="utf-8")); mutate(st, d)
        (d / "story.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        G = Gates(); ok = s1_schema(st, G) or raw
        if ok:
            ok4 = s4_onepage(st, d, G)
            s4d_tiles(st, G)
            if "deck" in st:
                ok5 = s5_deck(st, d, G)
            else:
                ok5 = False; G.add("S5", "SKIP", "no deck (story mode)")
            rendered = ""
            if ok4:
                (d / OUT["onepage_html"]).write_text(build_onepage_html(st, d, "selftest"), encoding="utf-8"); rendered += page_text((d / OUT["onepage_html"]).read_text(encoding="utf-8"))
            if ok5:
                (d / OUT["deck_html"]).write_text(build_deck_html(st, d, "selftest"), encoding="utf-8"); rendered += page_text((d / OUT["deck_html"]).read_text(encoding="utf-8"))
            s2_whys(st, G); s3_locators(st, G); s6_terms(st, rendered, G)
            if "talk" in st:
                s9_talk(st, G)
            else:
                G.add("S9", "SKIP", "no talk (story mode)")
            s4b_conclusion(st, G); s4c_figure_kinds(st, G); s10_quotes(st, d, G); stj = s11_coverage(st, d, G); s12_anomalies(st, stj, G)
            s13_drift_checklist(st, G); s14_stray_script(st, G); s15_bindings(st, G); s16_description(st, G); s17_layers_questions(st, G)
            s18_brief(st, G); s19_figure_reading(st, G); s20_flow(st, G)
        got = {g: s for g, s, _ in G.rows}; msgs = {g: m for g, _, m in G.rows}
        hit = got.get(gate) == expect and (needle is None or needle in msgs.get(gate, ""))
        results.append((name, gate, expect, got.get(gate, "absent") + ("" if hit else "  [" + msgs.get(gate, "no row")[:100] + "]"), hit))
        return G

    G0 = case("good", lambda s, d: None, "S1", "PASS")
    bad = [(g, s) for g, s, _ in G0.rows if s in ("FAIL", "WARN")]
    results.append(("good-clean", "ALL", "PASS/SKIP", ",".join(f"{g}:{s}" for g, s in bad) or "clean", not bad))
    case("s1-two-figures", lambda s, d: s["onepage"]["figures"].pop(), "S1", "FAIL")
    case("s2-empty-why", lambda s, d: s["axis"]["method_choice"].update({"why": " "}), "S2", "FAIL")
    case("s2-restated-why", lambda s, d: s["storyline"][2].update({"why": s["storyline"][2]["what"]}), "S2", "FAIL")
    case("s3-no-locator", lambda s, d: s["logic"]["chain"][0].update({"backing": "somewhere"}), "S3", "FAIL")
    case("s4-missing-figure", lambda s, d: (d / "figures" / "S2.png").unlink(), "S4", "FAIL")
    case("s4-long-cell", lambda s, d: s["onepage"]["table"].update({"method": "很長的方法描述。" * 20}), "S4", "WARN")
    case("s5-keypoint-not-first", lambda s, d: s["deck"]["pages"].insert(3, s["deck"]["pages"].pop(0)), "S5", "FAIL")
    case("s5-keypoint-after-cover", lambda s, d: s["deck"]["pages"].insert(0, s["deck"]["pages"].pop(2)), "S5", "PASS")   # round 5: GaN order Outlines → Key points
    case("s5-long-highlight", lambda s, d: s["deck"]["pages"][3]["highlights"].__setitem__(0, "這是一條刻意寫得非常長的重點提醒句子，" * 4 + "用來測試閘門會不會對超過四十八個字的內容發出警告。"), "S5", "WARN")
    case("s6-few-terms", lambda s, d: s.__setitem__("terms", s["terms"][:4]), "S6", "WARN")
    case("s9-no-formula", lambda s, d: s["talk"].update({"opening": "今天報告這篇。"}), "S9", "WARN")
    case("s9-outline-count", lambda s, d: s["talk"].update({"outline": "這次的報告分為三個部分說明：甲、乙、丙、丁，最後是戊。"}), "S9", "WARN")
    case("s4b-no-marker", lambda s, d: s["onepage"]["table"].update({"conclusion": "作者的結論句而已。"}), "S4b", "WARN")
    case("s10-fake-quote", lambda s, d: s["drift"][0].update({"quote": "this sentence does not occur anywhere in the sample paper text"}), "S10", "FAIL")
    case("s10-drift-no-quote", lambda s, d: s["drift"][0].pop("quote", None), "S10", "FAIL")

    def _uncovered(s, d):
        j = json.loads((d / "source" / "structure.json").read_text(encoding="utf-8")); j["units"].append({"id": "Fig. 9", "kind": "figure", "page": 9, "text": "Fig. 9 never cited"})
        (d / "source" / "structure.json").write_text(json.dumps(j), encoding="utf-8")

    def _anomaly(s, d):
        j = json.loads((d / "source" / "structure.json").read_text(encoding="utf-8")); j["anomalies"].append({"kind": "duplicate-section-number", "id": "§3.2", "pages": [5, 7], "detail": "section number 3.2 appears 2 times"})
        (d / "source" / "structure.json").write_text(json.dumps(j), encoding="utf-8")
    case("s11-uncovered-unit", _uncovered, "S11", "WARN")
    case("s12-anomaly-unaddressed", _anomaly, "S12", "WARN")
    # co-upgrade round 1 (2026-09-03): Gb8 drift checklist, Gb9 figure kinds — positive controls on both sides
    case("s13-kind-undeclared", lambda s, d: s["coverage"]["drift_checklist"].pop("grafted-result"), "S13", "WARN")
    case("s13-found-unused", lambda s, d: s["coverage"]["drift_checklist"].update({"grafted-result": "found"}), "S13", "WARN")
    case("s13-none-but-used", lambda s, d: s["coverage"]["drift_checklist"].update({"over-claim": "none"}), "S13", "WARN")
    case("s1-kind-missing-on-v3", lambda s, d: s["drift"][0].pop("kind"), "S1", "FAIL")
    case("s4c-motivation-on-page", lambda s, d: s["onepage"]["figures"][0].update({"kind": "motivation"}), "S4c", "WARN")
    case("s4c-schematic-allowed", lambda s, d: s["onepage"]["figures"][0].update({"kind": "schematic"}), "S4c", "PASS")   # OQ-1: negative control
    case("s4c-kind-missing-on-v3", lambda s, d: s["onepage"]["figures"][1].pop("kind"), "S1", "FAIL")
    # round 2 (2026-09-03): U-5 story mode (one page per paper) authors no deck / talk; U-6 the unused-term branch of S6

    def _story_mode(s, d):
        s["run"]["mode"] = "story"; s.pop("deck"); s.pop("talk")
    case("story-mode-no-deck", _story_mode, "S5", "SKIP")
    case("s1-deep-needs-deck", lambda s, d: s.pop("deck"), "S1", "FAIL")
    case("s6-unused-term", lambda s, d: s["terms"].append({"term": "幽靈術語", "gloss": "a term that appears on no rendered page"}), "S6", "WARN")
    # round 2 field findings (2026-09-03): S2's missing-abstract text layer, S3's minus-sign variants + stray script, Z's Cover cap + label repeat
    case("s10-page-image-quote", lambda s, d: s["drift"][0].update({"quote": "this sentence is only on the page image", "quote_source": "page-image"}), "S10", "WARN")
    case("s10-minus-sign-quote", lambda s, d: s["drift"][0].update({"quote": "suppresses the post−stress dynamic on−resistance rise"}), "S10", "PASS")

    def _cover5(s, d):
        s["talk"]["outline"] = "這次的報告分為五個部分說明：背景、方法、結果、討論、結論。"
        cov = [p for p in s["deck"]["pages"] if p["section"].lower() == "cover"][0]
        cov["highlights"] = ["背景", "方法", "結果", "討論", "結論"]
    case("s9-cover-five-parts", _cover5, "S9", "PASS")
    case("s14-stray-script", lambda s, d: s["onepage"]["table"].update({"features": s["onepage"]["table"]["features"] + "製程схема"}), "S14", "WARN")

    def _v3_label_repeated(s, d):
        s["schema"] = "paper-story/story@3"; s["onepage"]["keypoint_box"] = "KEYPOINT｜" + s["logic"]["keypoint"]
    case("s4-keypoint-label-repeated", _v3_label_repeated, "S4", "WARN")
    # 2026-09-04 (user finding: the slogan alone was unreadable): schema @4 bindings + description, two-sided
    case("s4-keypoint-box-on-v4", lambda s, d: s["onepage"].update({"keypoint_box": s["logic"]["keypoint"]}), "S4", "WARN")
    case("s1-v4-needs-bindings", lambda s, d: s["logic"].pop("bindings"), "S1", "FAIL")
    case("s1-v4-needs-in-this-paper", lambda s, d: s["logic"]["chain"][0].pop("in_this_paper"), "S1", "FAIL")
    case("s2-empty-in-this-paper", lambda s, d: s["logic"]["chain"][0].update({"in_this_paper": " "}), "S2", "FAIL")
    case("s2-in-this-paper-restates", lambda s, d: s["logic"]["chain"][1].update({"in_this_paper": s["logic"]["chain"][1]["step"]}), "S2", "FAIL")
    case("s15-role-not-in-slogan", lambda s, d: s["logic"]["bindings"][0].update({"role": "不存在的角色"}), "S15", "FAIL")
    case("s15-clause-unbound", lambda s, d: s["logic"].update({"keypoint": s["logic"]["keypoint"] + "；第二個子句沒有任何角色被綁定"}), "S15", "FAIL")
    case("s15-binding-no-locator", lambda s, d: s["logic"]["bindings"][0].update({"locator": "somewhere"}), "S15", "FAIL")
    case("s1-two-bindings", lambda s, d: s["logic"].update({"bindings": s["logic"]["bindings"][:2]}), "S1", "FAIL")   # minItems 3 is the schema's
    case("s15-good-bindings", lambda s, d: None, "S15", "PASS")   # negative control
    case("s16-short-description", lambda s, d: s["logic"].update({"keypoint_description": "太短，不是讀書心得。"}), "S16", "WARN")
    case("s16-slogan-too-long", lambda s, d: s["logic"].update({"keypoint": s["logic"]["keypoint"] + "，而且這句話被硬生生拉長到超過九十個字元的上限以測試閘門會不會對過長的標語提出警告並且指出段落應該放在描述欄位"}), "S16", "WARN")
    case("s16-description-restates", lambda s, d: s["logic"].update({"keypoint_description": s["logic"]["keypoint"]}), "S16", "WARN")
    case("s16-good-description", lambda s, d: None, "S16", "PASS")   # negative control

    def _v3_undeclared(s, d):
        s["schema"] = "paper-story/story@3"; s["logic"].pop("bindings"); s["logic"].pop("keypoint_description"); s["onepage"]["keypoint_box"] = s["logic"]["keypoint"]
    case("s15-v3-undeclared", _v3_undeclared, "S15", "WARN")
    # 2026-09-14 (researcher.tw B-12 / B-13, user ruling R5): time layers + question kinds, two-sided
    case("s17-good", lambda s, d: None, "S17", "PASS")   # negative control

    def _over_slot(s, d):
        s["deck"]["minutes"] = 1
        s["deck"]["pages"][-1]["notes"] += "因為這一段刻意寫長，所以口述時間會超過一分鐘的時段。" * 12
    case("s17-spoken-over-slot", _over_slot, "S17", "WARN", "spoken")

    def _undeclared17(s, d):
        for p in s["deck"]["pages"]:
            p.pop("layer", None)
        for q in s["talk"]["if_asked"]:
            q.pop("kind", None); q.pop("challenge", None)
    case("s17-undeclared", _undeclared17, "S17", "SKIP")   # older runs stay quiet
    case("s17-keypoint-not-a", lambda s, d: s["deck"]["pages"][0].update({"layer": "C"}), "S17", "WARN")
    case("s17-partial-layers", lambda s, d: s["deck"]["pages"][2].pop("layer"), "S17", "WARN")
    case("s17-no-results-a", lambda s, d: [p.update({"layer": "B"}) for p in s["deck"]["pages"] if p["section"] == "Results"], "S17", "WARN")
    case("s17-challenge-part-missing", lambda s, d: [q["challenge"].pop("settle") for q in s["talk"]["if_asked"] if q.get("kind") == "challenge"], "S17", "WARN")
    case("s17-kind-partial", lambda s, d: s["talk"]["if_asked"][1].pop("kind"), "S17", "WARN")
    # 2026-09-14 round 4 (schema @5): brief / figure reading / narrative flow — two-sided; every WARN case asserts its own message
    pages_of = lambda s, sec: [p for p in s["deck"]["pages"] if p["section"] == sec]
    case("s18-good", lambda s, d: None, "S18", "PASS")   # negative control
    case("s1-v5-deep-needs-brief", lambda s, d: s.pop("brief"), "S1", "FAIL")
    case("s1-v5-deep-needs-story-arc", lambda s, d: s["talk"].pop("story_arc"), "S1", "FAIL")
    case("s18-method-unspoken", lambda s, d: s["brief"]["methods"][0].update({"name": "從未說出口的方法"}), "S18", "WARN", "never named")
    case("s18-verdict-no-locator", lambda s, d: s["brief"]["verdicts"][0].update({"locator": "somewhere"}), "S18", "WARN", "no locator")
    case("s18-verdict-page-late", lambda s, d: s["deck"]["pages"].insert(4, s["deck"]["pages"].pop(1)), "S18", "WARN", "no Verdict page")
    case("s18-problem-is-why-read", lambda s, d: s["brief"].update({"problem": s["why_me"]["why_read"]}), "S18", "WARN", "restates why_me")

    def _v4_no_brief(s, d):
        s["schema"] = "paper-story/story@4"; s.pop("brief")
    case("s18-v4-skip", _v4_no_brief, "S18", "SKIP")
    case("s19-good", lambda s, d: None, "S19", "PASS")   # negative control
    case("s19-results-no-against", lambda s, d: [p["figure_read"].pop("against") for p in pages_of(s, "Results")], "S19", "WARN", "against")
    case("s19-figure-no-read", lambda s, d: [p.pop("figure_read") for p in pages_of(s, "Method")], "S19", "WARN", "figure_read")
    case("s19-notes-no-deixis", lambda s, d: [p.update({"notes": p["bridge"] + "。因為製程漂移大，所以用同片對照。"}) for p in pages_of(s, "Method")], "S19", "WARN", "never point")
    case("s19-content-page-no-figure", lambda s, d: [p.pop("no_figure") for p in pages_of(s, "Introduction")], "S19", "WARN", "no_figure")

    def _v4_undeclared_flow(s, d):
        s["schema"] = "paper-story/story@4"; s.pop("brief"); s["talk"].pop("story_arc")
        for p in s["deck"]["pages"]:
            for k in ("asks", "bridge", "takeaway", "beat", "figure_read", "no_figure"):
                p.pop(k, None)
    case("s19-v4-undeclared", _v4_undeclared_flow, "S19", "SKIP")   # older accepted runs stay quiet
    case("s20-v4-undeclared", _v4_undeclared_flow, "S20", "SKIP")
    case("s20-good", lambda s, d: None, "S20", "PASS")   # negative control
    case("s20-bridge-not-in-notes", lambda s, d: pages_of(s, "Introduction")[0].update({"bridge": "一句沒有出現在講稿裡的過場"}), "S20", "WARN", "bridge")

    def _recite(s, d):
        r = pages_of(s, "Results")[0]; r["highlights"][0] = "兩組各十二顆的分布完全沒有交集"; r["notes"] += "兩組各十二顆的分布完全沒有交集。"
    case("s20-recites-highlight", _recite, "S20", "WARN", "recite")
    # round 7 flip (user ruling 2026-09-21): the slogan is spoken at the close; up front as well is allowed, up front ONLY is the defect
    def _slogan_front_only(s, d):
        kp = s["logic"]["keypoint"]
        for p in s["deck"]["pages"]:
            if p.get("section", "").lower() in CLOSE_SECTIONS:
                p["notes"] = p.get("notes", "").replace(kp, "")
        s["talk"]["closing"] = {k: str(v).replace(kp, "") for k, v in (s["talk"].get("closing") or {}).items()}
    case("s20-slogan-front-only", _slogan_front_only, "S20", "WARN", "not spoken at the close")
    def _slogan_in_closing(s, d):
        _slogan_front_only(s, d)
        s["talk"]["closing"]["basis"] = s["logic"]["keypoint"] + "。" + s["talk"]["closing"].get("basis", "")
    case("s20-slogan-in-closing-ok", _slogan_in_closing, "S20", "PASS")
    case("s20-arc-short", lambda s, d: s["talk"]["story_arc"].update({"craft": s["talk"]["story_arc"]["craft"][:2]}), "S20", "WARN", "craft")
    case("s20-no-connectives", lambda s, d: [p.update({"notes": p["bridge"] + "。作者的結論是鈍化可行。機制只有 C-V。"}) for p in pages_of(s, "Conclusion")], "S20", "WARN", "connectives")
    # 2026-11-03 story@6 (user rulings G1/G2/G5): argument-step tiles, four/five fields, the story-mode script — two-sided
    def _story6(s, d):
        s["schema"] = "paper-story/story@6"; s["run"]["mode"] = "story"; s.pop("deck"); s.pop("talk"); s.pop("brief", None)
        for f, step in zip(s["onepage"]["figures"], ("context", "series", "trend")):
            f["step"] = step; f["why"] = "這一格負責論證的一個步驟"
        shutil.copy(d / "figures" / "S2.png", d / "figures" / "S2b.png")
        f1 = s["onepage"]["figures"][1]
        f1["files"] = ["figures/S2.png", "figures/S2b.png"]; f1.pop("file")   # a two-panel tile
        f1["figure_read"] = {"look": "橫軸是應力時間", "see": "兩組分布", "against": "未處理組", "means": "鈍化組變化較小"}
        f1["notes"] = "圖二是 Ron 對應力時間，可以看到鈍化組上升較少，代表側壁鈍化有效。"
        s["onepage"]["script"] = {"source_line": "這邊是 2026 年發表的文章。", "purpose_line": "主要是探討側壁鈍化對動態導通電阻的影響。"}

    def on6(fn):
        return lambda s, d: (_story6(s, d), fn(s, d))

    def _side(s, d):
        shutil.copy(d / "figures" / "S3.png", d / "figures" / "S4.png")
        s["onepage"]["figures"].append({"file": "figures/S4.png", "caption": "Fig.6 control", "locator": "p.8", "kind": "evidence",
                                        "step": "side-evidence", "necessity": "沒有這張對照，Ron 的下降無法歸因於鈍化"})
    case("s4d-story6-good", on6(lambda s, d: None), "S4d", "PASS")   # negative control: tiles with steps, a two-panel tile
    case("s4-story6-good", on6(lambda s, d: None), "S4", "PASS", "tiles (4 image files)")
    case("s4d-table-tile", on6(lambda s, d: s["onepage"]["figures"][2].update({"caption": "Table 2 benchmark", "locator": "Table 2, p.7"})), "S4d", "WARN", "results table")
    case("s4d-no-step", on6(lambda s, d: s["onepage"]["figures"][0].pop("step")), "S4d", "WARN", "without a step")
    case("s4d-side-evidence-ok", on6(_side), "S4d", "PASS")        # key side-evidence stays allowed as a tile
    case("s4-side-evidence-ok", on6(_side), "S4", "PASS")
    case("s4d-deep-skip", lambda s, d: None, "S4d", "SKIP")         # deep mode / @5 keep their gate output
    case("s4-story6-five-main-tiles", on6(lambda s, d: s["onepage"]["figures"].extend(
        [dict(s["onepage"]["figures"][0], step="mechanism"), dict(s["onepage"]["figures"][0], step="series")])), "S4", "FAIL", "story mode needs 3–4 tiles")
    case("s4-story6-two-side-evidence", on6(lambda s, d: (_side(s, d), s["onepage"]["figures"].append(dict(s["onepage"]["figures"][-1])))), "S4", "FAIL", "at most 1")
    case("s4-deep-six-tiles-ok", lambda s, d: s["onepage"]["figures"].extend([dict(s["onepage"]["figures"][0]) for _ in range(3)]), "S4", "PASS")   # deep mode keeps 3–6
    case("s4-story6-missing-panel", on6(lambda s, d: (d / "figures" / "S2b.png").unlink()), "S4", "FAIL", "S2b.png")
    case("s1-side-evidence-needs-necessity", on6(lambda s, d: (_side(s, d), s["onepage"]["figures"][-1].pop("necessity"))), "S1", "FAIL")
    case("s4-side-evidence-necessity-direct", on6(lambda s, d: (_side(s, d), s["onepage"]["figures"][-1].pop("necessity"))), "S4", "FAIL", "necessity", raw=True)

    def _four(s, d):
        s["onepage"]["fields"] = "four"; s["onepage"]["table"].pop("features")
    case("s4-four-fields", _four, "S4", "PASS", "four table cells")
    case("s1-five-needs-features", lambda s, d: s["onepage"]["table"].pop("features"), "S1", "FAIL")
    case("s4-four-fields-features-present", lambda s, d: s["onepage"].update({"fields": "four"}), "S4", "WARN", "Features row is not printed")
    case("s1-v5-fields-bad-enum", lambda s, d: s["onepage"].update({"fields": "six"}), "S1", "FAIL")
    # the products: four/five rows, the 口述稿 section, S9 reads the section, no talk-script.md
    import contextlib
    import io
    import story_explainer as SE
    ex_ok = True
    detail = []
    for nm, want_rows in (("s4-four-fields", 4), ("good", 5)):
        c = SE.build_content(td / nm)
        tb = next(b for s_ in c["sections"] for b in s_["blocks"] if b.get("type") == "table" and b.get("caption", "").startswith("論文一頁"))
        ex_ok &= len(tb["rows"]) == want_rows
        detail.append(f"{nm}:{len(tb['rows'])}")
    results.append(("explainer-table-rows", "EX", "4 rows / 5 rows", " ".join(detail), ex_ok))
    c_deep = SE.build_content(td / "good")
    sec_deep = next((s_ for s_ in c_deep["sections"] if s_["id"] == "script"), None)
    heads = [b["text"] for b in (sec_deep or {}).get("blocks", []) if b["type"] == "para"]
    deep_ok = bool(sec_deep) and any("開場" in h for h in heads) and any("逐頁怎麼講" in h for h in heads) and any("被問時" in h for h in heads) and any("結尾" in h for h in heads)
    ids = [s_["id"] for s_ in c_deep["sections"]]
    deep_ok = deep_ok and ids.index("script") == ids.index("figures") + 1   # 口述稿 sits right after 逐圖判讀
    results.append(("explainer-script-deep", "EX", "開場/逐頁/被問時/結尾 after 逐圖判讀", "present" if deep_ok else f"MISSING {heads[:4]} {ids}", deep_ok))
    c6 = SE.build_content(td / "s4d-story6-good")
    sec6 = next((s_ for s_ in c6["sections"] if s_["id"] == "script"), None)
    fig6 = [b for s_ in c6["sections"] if s_["id"] == "figures" for b in s_["blocks"] if b["type"] == "figure"]
    story_ok = bool(sec6) and "出處" in json.dumps(sec6, ensure_ascii=False) and len(fig6) == 4   # 3 tiles, one with two panels = 4 images
    results.append(("explainer-script-story", "EX", "出處+目的+tile notes; 4 images", "present" if story_ok else f"MISSING fig={len(fig6)}", story_ok))
    SE.build(td / "good", do_build=False)
    shown = SE.talk_section_text(td / "good")
    st_good = json.loads((td / "good" / "story.json").read_text(encoding="utf-8"))
    G9a, G9b = Gates(), Gates()
    s9_talk(st_good, G9a, shown); s9_talk(st_good, G9b, "（口述稿段落缺失）")
    results.append(("s9-reads-explainer-section", "S9", "PASS on the real section, WARN on a stripped one",
                    f"{G9a.rows[0][1]} / {G9b.rows[0][1]}  [{G9b.rows[0][2][:70]}]", G9a.rows[0][1] == "PASS" and G9b.rows[0][1] == "WARN" and "not printed" in G9b.rows[0][2]))
    # user ruling 2026-11-03 「只留「口述稿」section」: no 上台要點 section, and nothing it held is lost from 口述稿
    retired = lambda c: any(s_.get("id") == "talk" or s_.get("heading") == "上台要點" for s_ in c["sections"])
    def lost_from_script(st, text):
        """What the former 上台要點 section held (outline, each if-asked question, closing parts) that `text` does not print."""
        tk_ = st["talk"]; want = [("outline", tk_.get("outline", ""))] + [("if_asked", q["q"]) for q in tk_.get("if_asked", [])] \
            + [("closing." + k, tk_.get("closing", {}).get(k, "")) for k in ("basis", "help", "next")]
        return [k for k, v in want if v and fold(v) not in fold(text)]
    inj = json.loads(json.dumps(c_deep)); inj["sections"].append({"id": "talk", "heading": "上台要點", "blocks": []})
    results.append(("no-retired-talk-section", "EX", "deep+story clean; injected 上台要點 caught",
                    f"deep={retired(c_deep)} story={retired(c6)} injected={retired(inj)}", not retired(c_deep) and not retired(c6) and retired(inj)))
    lost_real, lost_ctrl = lost_from_script(st_good, shown), lost_from_script(st_good, "")
    results.append(("script-keeps-former-talk-content", "EX", "nothing lost; empty script loses all (positive control)",
                    f"lost={lost_real} / control lost {len(lost_ctrl)}", not lost_real and len(lost_ctrl) >= 4))
    to = td / "talk-only"
    if to.exists():
        shutil.rmtree(to)
    shutil.copytree(td / "good", to)
    st_to = json.loads((to / "story.json").read_text(encoding="utf-8")); st_to.pop("deck")
    (to / "story.json").write_text(json.dumps(st_to, ensure_ascii=False), encoding="utf-8")
    SE.build(to, do_build=False)
    lost_to = lost_from_script(st_to, SE.talk_section_text(to))
    results.append(("talk-without-deck-still-printed", "EX", "outline/if-asked/closing in 口述稿 when there is no deck", f"lost={lost_to}", not lost_to))
    cr = b"\r"
    raw_ok = (td / "good" / f"{SE.STEM}.explainer.json").read_bytes()
    (td / "crlf-control.json").write_text("{\n}\n", encoding="utf-8")   # the former writer (Path.write_text): CRLF on Windows
    ctrl_cr = (td / "crlf-control.json").read_bytes().count(cr)
    results.append(("explainer-json-lf-only", "EX", "no CR byte in the built content file; the old writer's CRLF is caught (positive control, Windows)",
                    f"CR={raw_ok.count(cr)} / old-writer control CR={ctrl_cr}", cr not in raw_ok and (ctrl_cr > 0 or sys.platform != "win32")))
    # no talk-script.md is written, and one already in the folder is left byte-identical
    tw = td / "no-talk-write"
    if tw.exists():
        shutil.rmtree(tw)
    shutil.copytree(base, tw)
    (tw / "talk-script.md").write_text("OLD CONTENT\n", encoding="utf-8")
    tw2 = td / "no-talk-write2"
    if tw2.exists():
        shutil.rmtree(tw2)
    shutil.copytree(base, tw2)
    with contextlib.redirect_stdout(io.StringIO()):
        render(tw, False, False, False, "selftest", explainer=False); render(tw2, False, False, False, "selftest", explainer=False)
    keep_ok = (tw / "talk-script.md").read_text(encoding="utf-8") == "OLD CONTENT\n" and not (tw2 / "talk-script.md").exists() and not (tw2 / "talk-script-pre-story.md").exists()
    results.append(("talk-script-not-written", "OUT", "none written, old one untouched", "as expected" if keep_ok else "MISMATCH", keep_ok))
    nb = (td / "good" / OUT["deck_html"]).read_text(encoding="utf-8").count('class="slide backup"')
    nb0 = (td / "s17-undeclared" / OUT["deck_html"]).read_text(encoding="utf-8").count('class="slide backup"')
    results.append(("s17-backup-pages", "S17", "1 good / 0 undecl.", f"{nb} / {nb0}", nb == 1 and nb0 == 0))
    t_good = build_talk_md(json.loads((td / "good" / "story.json").read_text(encoding="utf-8")))
    t_old = build_talk_md(json.loads((td / "s17-undeclared" / "story.json").read_text(encoding="utf-8")))
    plan_ok = "時間不夠時" in t_good and "### 挑戰" in t_good and "時間不夠時" not in t_old and "### 挑戰" not in t_old
    results.append(("s17-cut-plan-in-script", "S17", "good has, undecl. not", "as expected" if plan_ok else "MISMATCH", plan_ok))
    v5_keys = ("## 上台前先記住", "## 問題鏈", "這張圖怎麼看", "## 這篇怎麼說完一個研究故事")
    t_v4 = build_talk_md(json.loads((td / "s20-v4-undeclared" / "story.json").read_text(encoding="utf-8")))
    sec_ok = all(k in t_good for k in v5_keys) and not any(k in t_v4 for k in v5_keys)
    results.append(("v5-script-sections", "S20", "good has, v4 not", "as expected" if sec_ok else "MISMATCH " + str([k for k in v5_keys if k not in t_good]), sec_ok))
    dh = (td / "good" / OUT["deck_html"]).read_text(encoding="utf-8"); dh4 = (td / "s20-v4-undeclared" / OUT["deck_html"]).read_text(encoding="utf-8")
    deck_ok = all(k in dh for k in ("Q1 它在解什麼問題", "一句話的故事", "這張圖怎麼看", "這頁帶走")) and "這頁帶走" not in dh4
    results.append(("v5-deck-pages", "S18", "verdict/arc/walk", "as expected" if deck_ok else "MISMATCH", deck_ok))
    sch = json.loads(SCHEMA.read_text(encoding="utf-8"))
    enum_d = tuple(k for k in sch["properties"]["drift"]["items"]["properties"]["kind"]["enum"] if k != "other")
    enum_f = tuple(sch["properties"]["onepage"]["properties"]["figures"]["items"]["properties"]["kind"]["enum"])
    insync = enum_d == DRIFT_KINDS and enum_f == FIG_KINDS
    results.append(("kinds-in-sync", "S13", "schema == code", "in sync" if insync else f"OUT OF SYNC {enum_d} {enum_f}", insync))
    G7 = Gates(); s7_fit([td / "good" / OUT["onepage_html"], td / "good" / OUT["deck_html"]], G7)
    results.append(("s7-fit-on-good", "S7", "PASS or WARN", (G7.rows[0][1] + "  [" + G7.rows[0][2][:100] + "]") if G7.rows else "absent", bool(G7.rows) and G7.rows[0][1] in ("PASS", "WARN")))
    Gd = Gates(); real = SHELL.read_bytes()
    try:
        SHELL.write_bytes(real[:-1] + (b"\n" if real[-1:] != b"\n" else b" ")); s8_shell(Gd)
        hit = bool(Gd.rows) and Gd.rows[0][1] == "WARN"
    finally:
        SHELL.write_bytes(real)
    results.append(("s8-one-byte-drift", "S8", "WARN", Gd.rows[0][1] if Gd.rows else "absent", hit))
    # embed (2026-10-27): paper text spliced into the deck must not end or swallow its <script> ("</script",
    # "<!-- <script"), and no splice may run paper text through a re.sub template ("\m" in a LaTeX title raised
    # bad escape; "\n" in a gloss became a raw newline inside a JS string).
    gloss, ttl = "line one\nline two </script> x <!-- <script> y", r"$\mu$-LED \n </title> z"
    try:
        pg = splice({"terms": [{"term": "Term", "gloss": gloss}]}, "<section>s</section>", ttl)
        syms = re.search(r"var SYMS = (\{.*?\n\s*\};)", pg, re.S).group(1)
        d = json.loads(re.search(r'd:("(?:[^"\\]|\\.)*")', syms).group(1))
        got = f"raw '<' in SYMS: {syms.count('<')}; gloss round-trips: {d == gloss}; title kept: {esc(ttl) in pg}"
        hit = syms.count("<") == 0 and d == gloss and esc(ttl) in pg
    except Exception as e:  # the old template path raised here
        got, hit = f"{type(e).__name__}: {e}"[:90], False
    results.append(("embed-hostile-text", "EMB", "escaped+intact", got, hit))
    ok = all(r[-1] for r in results)
    print("paper-story selftest — two-sided calibration")
    for n, g, e, got, h in results:
        print(f"  {'OK ' if h else 'BAD'} {n:<24} {g:<4} expected {e:<14} got {got}")
    print(("sample kept at: " + str(base)) if keep else f"temp dir: {td}")
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path); ap.add_argument("--fit-check", action="store_true")
    ap.add_argument("--pptx-from-story", "--pptx", dest="pptx", action="store_true",
                    help="EXPLICIT REQUEST ONLY: onepage.pptx / talk-deck.pptx in the HTML layout — not the formal deck (lab template, English)")
    ap.add_argument("--check-shell", action="store_true"); ap.add_argument("--no-gates", action="store_true"); ap.add_argument("--presenter", default="")
    ap.add_argument("--legacy-html", action="store_true", help="also write onepage.html / talk-deck.html (retired 2026-10-12; old runs only)")
    ap.add_argument("--no-explainer", action="store_true", help="skip the explainer page build (gates only)")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--keep", type=Path); ap.add_argument("--make-sample", type=Path)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest(a.keep)
    if a.make_sample:
        d = make_sample(a.make_sample); print(json.dumps({"sample_run": str(d)}))
        return render(d, a.pptx, a.fit_check, a.check_shell, a.presenter or "sample", legacy_html=a.legacy_html, explainer=not a.no_explainer)
    if not a.run:
        ap.error("--run <run_dir> (or --selftest / --make-sample)")
    return render(a.run, a.pptx, a.fit_check, a.check_shell, a.presenter, not a.no_gates, a.legacy_html, not a.no_explainer)


if __name__ == "__main__":
    sys.exit(main())
