#!/usr/bin/env python
"""page-fill-gate — does a human-facing HTML page USE the width it is given?

    python fill_gate.py <file.html|url> [...] [--viewport 1707x830 ...] [--class X]
                        [--json] [--no-controls] [--quiet]

Property under test (user ruling 2026-09-04, `ops/environment.md` § Display):
a page read on this machine must not leave an asymmetric void on the right.
The named defect is the LEFT-ANCHORED CAP — a page container (or a painted,
row-alone block) capped in width and hugging the left edge, which is how one
shell's `max-width:1060px` became 13 deliverables with 31–40 % of the screen
unused. Symmetric voids (a centred reading column) are a different, allowed
shape; how much fill a page owes depends on its CLASS.

Classes are DATA in `page_classes.json` (one row = one class + its rule); a new
kind of page is a new row plus a fixture, never a code branch. The page declares
its class with `<html data-page-class="…">`. An undeclared page is INFERRED
from structure and its verdict is CAPPED AT WARN in both directions, because a
gate may only rule on what it can determine (global CLAUDE.md gate rule). The
cap used to apply to FAIL only, which meant an undeclared page could report a
clean PASS — a PASS that is an artifact of the guessed ruler, not a measurement
of the page, and one that gets carried forward as evidence. Corrected
2026-09-08 on a measured case:
`outputs/diagram-authoring/mfp-audit-f5-owner-view.html` reads reach 74 % with
symmetric voids, which PASSES as the inferred `document-short` and FAILS as
`document-long` — the class an audit page with diagrams plausibly is. The
promotion trigger that turns an inferred class into a declared one is written in
the registry's `unknown_policy`.

Severity (memory `gate-severity-by-consumer`): the container-level verdict is
determinable → FAIL; a per-block finding (a narrower painted box alone in its
row) is a judgment the reader makes → WARN with the selector printed, promoted
to FAIL per selector via `block_fail_selectors` once a human has reported it.

Controls run on EVERY invocation unless `--no-controls`: a known-bad fixture
(left-anchored 800px cap) must FAIL and two known-good fixtures must PASS (a
fluid fill, and a centred column under a fixed corner panel whose text must not
count as content) — a reject-everything gate scores 100 % on a one-sided
calibration.

Exit codes: 0 = no FAIL (WARNs allowed) · 1 = at least one FAIL · 2 = the
instrument is unavailable (Playwright/Chromium missing) — downgrade-and-forward,
the caller must print the warning and not claim the property.

Scopes and fractions (L-125, 2026-10-11): a PAGED deck hides all but one slide, so
each scope is forced visible for its own measurement (`[hidden]`, display:none,
visibility:hidden, hidden wrapper) and restored exactly; row["areas"] lists the
per-slide n/reach/fill/findings. A box counts only for the part of it that is
visible inside the area (overflow clips, off-canvas, slide-padding bleed, rail),
so reach/fill stay within 0..1 — an overshoot used to mask left-capped pages.

In-page consistency (user rulings 2026-10-31, PersonalSite; proposal «shared-layer bypass», hole 3). The
property under test is now TWO things: the page uses its width (above) AND the page does not contradict
itself. On the PersonalSite home, four sibling `h2.section-title` rendered 22/22/32/32 px because a
contextual rule enlarged only two, and two style rules were forked under new class names (`.proj-thumb`
copied `.story-thumb`, `.page-head .standfirst/.byline` copied `.prose` ones); a width gate passed all of it.
Two checks, both WARN-only (a WARN keeps exit 0), both read the page's OWN computed styles / CSSOM:
  C2  visible elements sharing (tag, class list, declared aria state) must render alike in font-size / weight / family /
      line-height / letter-spacing. DETERMINABLE: that they differ (a measured fact). NOT determinable: whether
      the author meant them to (an A/B panel, a utility class). So WARN, and a selector is promoted to FAIL
      only through the data list `sibling_fail_selectors` (empty by default), like `block_fail_selectors`.
      Three context effects are not a drift of the class and are counted apart, never dropped silently:
      <svg> descendants (user units, per-node by design), one relative declaration (0.9em, unitless
      line-height) meeting different parents, and a property every element merely inherits.
  S3  two style rules under DIFFERENT selectors that declare (nearly) the same declarations (csscss's "X and Y
      share N rules", reimplemented over the CSSOM; csscss is archived and Ruby). DETERMINABLE: the shared
      declarations. NOT determinable: that it is a copy rather than two components sharing a design token or a
      reset, so WARN only, never FAIL. Two evidence channels: `copy` (>= 5 shared declarations covering >= 0.8 of
      the shorter rule) and `same-target` (the same class styled in two contexts: >= 2 shared, >= 0.6). A pair
      sharing a selector, a state/media variant of one component (`.btn:hover` vs `.btn:focus`) and a contextual
      override (`.bar .btn` vs `.btn`) are not reported. A shorthand the browser serialises as N longhands counts
      once. One fork is one line however many of its sub-rules (hover, img) were copied. S3 runs once per file
      (the CSSOM does not depend on the viewport); C2 at every viewport. A stylesheet the browser will not
      expose (a linked file:// sheet) is fetched locally when it is a local file / loopback URL and otherwise
      listed as unread in `--json`; it never reads as "no duplicates".
  Calibration (2026-10-31; thresholds live in page_classes.json, the table in README «In-page consistency»):
  33 human-facing pages in 24 distinct CSS families (15 `~/.claude/outputs` deliverables, 8 launcher views,
  10 PersonalSite `dist` pages). C2: 17 findings on 10 pages before the three context filters, 3 on 3 pages
  after (1 real, 1 ambiguous, 1 intentional A/B). S3 at K=5 R=0.8: 24 groups, 8 distinct forks, 6 judged
  real, 2 noise (generic resets, shared "muted small text"); K=4 R=0.6 gives 5.4 groups per family, K=3 19.6.
  Controls on EVERY run: the real PersonalSite CSS before the fix (`known-bad-consistency-prefix.html`: must
  WARN with h2.section-title font-size 22px AND 32px, the `.proj-thumb`/`.story-thumb` fork and the
  `.page-head .standfirst`/`.prose .standfirst` fork named) and after (`known-good-consistency-postfix.html`:
  neither the h2 drift nor those two forks), plus a clean page that must give no finding at all. They are
  asserted on those VALUES, not on the status label. Known residue: the thumb fork passes at exactly
  min_shared=5 (K=6 loses it); the width MEASURE_JS is untouched, so width output is unchanged.

Library use: `from fill_gate import gate_paths; rows = gate_paths([...])`; each row also carries
`sibling_drift` (C2 block) and `duplicate_rules` (S3 block, None at the viewports where it is not computed).

review-when: the screen or scaling in `ops/environment.md` changes (edit
`reference_viewports`); Playwright's page.evaluate semantics change; a class
row is added (add its fixture to tests/ the same commit).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
# which hosts are "this machine" is hooks/_lib/hosts.py (one copy, shared with the browser-pane
# scope guard; AP-74). No fallback: a gate that cannot load it stops rather than guess.
sys.path.insert(0, str(HERE.parents[1] / "hooks" / "_lib"))
from hosts import LOCAL_HOSTS, is_local_host  # noqa: E402
REGISTRY_PATH = HERE / "page_classes.json"
FORK_MAX_RULES = 5000           # S3 compares at most this many style rules (the rest are reported as not checked)
FORK_POSTING_CAP = 150          # a declaration used by more rules than this is boilerplate and is left out of S3
SHEET_MAX_BYTES = 2_000_000     # a stylesheet larger than this stays unread (file: and loopback http alike)
FIXTURES = HERE / "fixtures"
# fixture file -> control label; a "known-bad*" label must FAIL, every other label must PASS
CONTROLS = {"known-bad-left-cap.html": "known-bad", "known-good-fill.html": "known-good",
            "known-good-fixed-panel.html": "known-good-fixed-panel",
            "known-bad-formula-overflow.html": "known-bad-formula-overflow"}
# The in-page consistency pair (2026-10-31): the REAL PersonalSite CSS before / after the shared-layer fix.
# Width-wise both are clean; the bad one must WARN with the 22/32 px drift and the thumb fork NAMED, the
# good one must PASS with neither. Asserted on those values, not on the label (consistency_control_problems).
CONSISTENCY_CONTROLS = {"known-bad-consistency-prefix.html": "consistency-bad",
                        "known-good-consistency-postfix.html": "consistency-good",
                        "known-good-consistency-clean.html": "consistency-clean"}
ALL_CONTROLS = {**CONTROLS, **CONSISTENCY_CONTROLS}


def control_want(label: str) -> tuple:
    """The statuses a control may produce. A known-bad width control FAILs; the consistency-bad one WARNs
    (WARN-only checks); the real post-fix page PASSes or WARNs because the fix removed the NAMED defects, not
    every duplicate in that author's CSS (its values are asserted instead); everything else PASSes."""
    if label.startswith("known-bad"):
        return ("FAIL",)
    return {"consistency-bad": ("WARN",), "consistency-good": ("PASS", "WARN")}.get(label, ("PASS",))


def consistency_control_problems(label: str, row: dict) -> list[str]:
    """Value-level assertions for the consistency controls. Empty list = the control behaved.
    FIRST that both checks actually MEASURED: an absence assertion ("no thumb fork", "no finding") is also
    satisfied by a check that never ran (None -> {}), so a control that passes on absence alone proves nothing."""
    sd, dr = row.get("sibling_drift"), row.get("duplicate_rules")
    ran = []
    if not sd or not sd.get("groups_compared"):
        ran.append("C2 compared no same-class group")
    if not dr or not dr.get("rules"):
        ran.append("S3 parsed no style rule")
    elif dr.get("unread"):
        ran.append("S3 left stylesheet(s) unread: " + ", ".join(str(u.get("href")) for u in dr["unread"][:3]))
    if ran:
        return ["the check did not measure (" + "; ".join(ran) + ")"]
    sib = sd.get("findings") or []
    groups = dr.get("groups") or []
    h2 = next((f for f in sib if f["sel"] == "h2.section-title"), None)
    h2_group = next((g for g in sd.get("groups") or [] if g["sel"] == "h2.section-title"), None)
    if label in ("consistency-bad", "consistency-good") and not (h2_group and h2_group["n"] == 4):
        return [f"the h2.section-title group must be compared with 4 elements; got {h2_group}"]
    sizes = sorted({v["v"] for d in (h2 or {}).get("drift", []) if d["prop"] == "font-size" for v in d["values"]})
    pairs = [(p["a"], p["b"]) for g in groups for p in g["pairs"]]
    thumb = any({".proj-thumb", ".story-thumb"} <= {a.split(":")[0].split(" ")[0], b.split(":")[0].split(" ")[0]} for a, b in pairs)
    stand = any({".prose .standfirst", ".page-head .standfirst"} == {a, b} for a, b in pairs)
    got = f"h2.section-title font-size values {sizes}, thumb fork {thumb}, standfirst fork {stand}"
    if label == "consistency-bad":
        return [] if (sizes == ["22px", "32px"] and thumb and stand) else [f"want 22px+32px, thumb fork, standfirst fork; got {got}"]
    if label == "consistency-clean":
        return [] if (not sib and not groups) else [f"want no finding at all; got {len(sib)} sibling group(s), {len(groups)} fork(s)"]
    return [] if (h2 is None and not thumb and not stand) else [f"want none of them; got {got}"]

MEASURE_JS = r"""(opts) => {
  const W = innerWidth, H = innerHeight, cs = el => getComputedStyle(el);
  const html = document.documentElement;
  const declared = html.getAttribute('data-page-class');
  // ---- chrome: fixed/sticky, near full-height, hugging an edge, not a rail ----
  let areaL = 0, areaR = W; const chrome = [];
  for (const el of document.querySelectorAll('body *')) {
    const s = cs(el); if (s.position !== 'fixed' && s.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    if (r.height < H * 0.8 || r.width < 40 || r.width > W * 0.5) continue;
    if (el.matches('[data-rail], #rail')) continue;
    if (r.left <= 1) { areaL = Math.max(areaL, r.right); chrome.push({side: 'left', w: Math.round(r.width), id: el.id || el.tagName}); }
    else if (r.right >= W - 1) { areaR = Math.min(areaR, r.left); chrome.push({side: 'right', w: Math.round(r.width), id: el.id || el.tagName}); }
  }
  // Every marked rail counts (before 2026-10-31 only the FIRST one did, and only as a right edge:
  // a left toc rail + centred prose + marked right gutter could not be described; PersonalSite).
  const railRects = Array.from(document.querySelectorAll('[data-rail], #rail')).map(e => e.getBoundingClientRect());
  const painted = s => (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent')
                       || parseFloat(s.borderLeftWidth) > 0 || parseFloat(s.borderRightWidth) > 0;
  const ownText = el => Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
  // tagName of an inline <svg> in an HTML document is lower-case 'svg' (SVG namespace), so the
  // test upper-cases it — before 2026-10-02 an unbordered inline SVG never counted as content.
  const media = el => /^(IMG|SVG|CANVAS|VIDEO|TABLE|PRE|FIGURE|IFRAME)$/.test(el.tagName.toUpperCase());
  // A <nav> is page chrome unless the page marks it content: a centred prose grid whose header nav
  // and right TOC were both skipped read left-anchored, its site name pinning the left void and
  // nothing the right (fb:ee9813a8, 2026-10-12). Opt-in, so no unmarked page changes verdict.
  const navChrome = el => { const nv = el.closest('nav'); return !!nv && !nv.closest('[data-fill-content]'); };
  const skip = el => el.closest('script,style,#side,[hidden],[data-fill-ignore]') || navChrome(el) || cs(el).position === 'fixed';
  // A fixed box floats OVER the page, and so does everything inside it: before 2026-10-12 only the
  // fixed box itself was skipped, so the text of a fixed corner panel counted as content and shrank
  // the right void (note.html, void L/R 234/33 instead of 234/234; fb:bfa19018). Two fixed ancestors
  // stay content-bearing: a marked rail (the registry says it counts as content) and a surface that
  // covers the viewport (a `position:fixed; inset:0` app or deck shell IS the page, not an overlay).
  // The walk stops at the measured root, so a fixed slide measured as its own scope keeps its content.
  const floatsOver = p => cs(p).position === 'fixed' && !p.matches('[data-rail], #rail')
                          && !((r => r.width >= W * 0.9 && r.height >= H * 0.9)(p.getBoundingClientRect()));
  // A marked rail counts as content, but only the part of it that lies inside the page area: a rail
  // translated off-canvas, or one wider than the area, used to push reach past 100 %. A rail whose
  // centre is right of the area's centre extends the right edge; one left of it, the left edge.
  const railsIn = railRects.filter(r => r.width > 0 && r.left < areaR && r.right > areaL);
  const areaMid = (areaL + areaR) / 2;
  const rightRails = railsIn.filter(r => (r.left + r.right) / 2 >= areaMid);
  const leftRails = railsIn.filter(r => (r.left + r.right) / 2 < areaMid);
  const railEdge = rightRails.length ? Math.min(Math.max(...rightRails.map(r => r.right)), areaR) : null;
  const railEdgeL = leftRails.length ? Math.max(Math.min(...leftRails.map(r => r.left)), areaL) : null;
  // ---- one measurement over one area (the page, or one slide) ----
  const measure = (root, L, R, limitTop) => {
    let minL = Infinity, maxR = -Infinity, n = 0; const blocks = [];
    // A box only counts for the part of it that can be SEEN inside the area [L, R]: its rect, cut by
    // the padding box of every overflow-clipping ancestor between it and the area. Counting the raw
    // rect let a wide table in a scroller, a carousel track, an off-canvas drawer or a bleed into the
    // slide padding push maxR past R (or minL below L), so fill/reach exceeded 100 % (L-125).
    const spans = new Map();
    const inRoot = p => p && p !== root && root.contains(p);
    const floated = new Map();  // ancestor -> lies in (or is) a floating fixed box below root; cached per ancestor
    const inFloat = p => {
      if (!p || p === root || p === html) return false;
      if (floated.has(p)) return floated.get(p);
      const v = floatsOver(p) || inFloat(p.parentElement); floated.set(p, v); return v;
    };
    const holder = el => {   // the ancestor whose overflow clips el: parent, or the containing block of an absolute box
      if (cs(el).position !== 'absolute') return el.parentElement;
      for (let p = el.parentElement; p; p = p.parentElement) { const ps = cs(p); if (ps.position !== 'static' || ps.transform !== 'none') return p; }
      return null;
    };
    const spanFor = el => {  // horizontal span in which the CHILDREN of `el` are visible
      if (spans.has(el)) return spans.get(el);
      const h = holder(el), up = inRoot(h) ? spanFor(h) : [L, R];
      const s = cs(el); let sp = up;
      if (s.overflowX !== 'visible') { const q = el.getBoundingClientRect(); sp = [Math.max(up[0], q.left + parseFloat(s.borderLeftWidth)), Math.min(up[1], q.right - parseFloat(s.borderRightWidth))]; }
      spans.set(el, sp); return sp;
    };
    for (const el of root.querySelectorAll('*')) {
      if (skip(el) || inFloat(el.parentElement)) continue;
      const s = cs(el); if (s.display === 'inline' || s.display === 'none' || s.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect(); if (r.width < 24 || r.height < 8) continue;
      if (limitTop != null && r.top > limitTop) continue;
      const isPainted = painted(s), isText = ownText(el), isMedia = media(el);
      if (!(isPainted || isText || isMedia)) continue;           // pure wrappers do not count
      // A full-bleed painted band with no text of its own is a backdrop, not content: in a class
      // that declares `backdrop_bands` it would otherwise report reach 100 % and hide a capped,
      // left-hugging content column inside it. Its children are still measured.
      if (opts.backdrop && isPainted && !isText && !isMedia && r.width >= (R - L) * 0.98) continue;
      const h = holder(el), sp = inRoot(h) ? spanFor(h) : [L, R];
      const vl = Math.max(r.left, sp[0]), vr = Math.min(r.right, sp[1]);
      if (vr - vl < 24) continue;                                // clipped away / off-canvas / outside the area
      minL = Math.min(minL, vl); maxR = Math.max(maxR, vr); n++;
      // Block findings are about WIDE TEXT CONTAINERS capped by their own CSS. Media, controls,
      // chips/badges (intrinsic sizes) and children of grid / row-flex parents (the PARENT
      // allocates their width) are never findings — that is the proportional-vs-pixel rule.
      if (isPainted && r.height >= 24 && r.width >= 300 && !isMedia && !el.closest('figure')
          && /^(DIV|P|SECTION|ARTICLE|ASIDE|BLOCKQUOTE|DL|UL|OL|H[1-6])$/.test(el.tagName)
          && !/inline/.test(s.display)) {
        const ps = el.parentElement ? cs(el.parentElement) : null;
        const allocated = ps && (ps.display.includes('grid') || (ps.display.includes('flex') && !ps.flexDirection.startsWith('column')));
        if (!allocated) blocks.push({el, r, s});
      }
    }
    if (railEdge != null && limitTop != null) { maxR = Math.max(maxR, railEdge); }
    if (railEdgeL != null && limitTop != null) { minL = Math.min(minL, railEdgeL); }
    const areaW = R - L;
    const leftVoid = n ? Math.max(0, minL - L) : areaW, rightVoid = n ? Math.max(0, R - maxR) : areaW;
    // per-block: painted, alone in its row, narrower than 85 % of its parent, left-anchored
    const findings = [];
    for (const b of blocks) {
      const p = b.el.parentElement; if (!p) continue;
      const pr = p.getBoundingClientRect(); const ps = cs(p);
      const pl = pr.left + parseFloat(ps.paddingLeft), prr = pr.right - parseFloat(ps.paddingRight);
      const pw = prr - pl; if (pw < 200) continue;
      if (b.r.width >= pw * 0.85) continue;
      const alone = !Array.from(p.children).some(sib => sib !== b.el && (() => { const q = sib.getBoundingClientRect();
        return q.width >= 24 && q.top < b.r.bottom && q.bottom > b.r.top && (q.left >= b.r.right - 1 || q.right <= b.r.left + 1); })());
      if (!alone) continue;
      const lv = b.r.left - pl, rv = prr - b.r.right;
      if (rv - lv > pw * opts.asym) {
        const tag = b.el.tagName.toLowerCase() + (b.el.id ? '#' + b.el.id : '') + (b.el.className && typeof b.el.className === 'string' ? '.' + b.el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
        findings.push({sel: tag, w: Math.round(b.r.width), parent_w: Math.round(pw), right_void: Math.round(rv)});
      }
    }
    return {areaL: Math.round(L), areaR: Math.round(R), areaW: Math.round(areaW), n,
            minL: n ? Math.round(minL) : null, maxR: n ? Math.round(maxR) : null,
            leftVoid: Math.round(leftVoid), rightVoid: Math.round(rightVoid),
            fill: n ? +((maxR - minL) / areaW).toFixed(3) : 0, reach: n ? +((maxR - L) / areaW).toFixed(3) : 0,
            findings: findings.slice(0, 6), findings_total: findings.length};
  };
  // ---- inference (only consulted when undeclared) ----
  const infer = () => {
    const slides = document.querySelectorAll('.slide');
    // the first SHOWN slide: a paged deck whose slide 1 is hidden has a zero-height slides[0] (fb:1bffdc71)
    const shown = Array.from(slides).find(s => s.getBoundingClientRect().height > 0);
    if (slides.length >= 2 && (cs(html).scrollSnapType !== 'none' || (shown && shown.getBoundingClientRect().height >= H * 0.9))) return 'deck';
    if (chrome.some(c => c.side === 'left') && document.querySelector('main')) return 'document-long';
    let svgA = 0; for (const s of document.querySelectorAll('svg')) { const r = s.getBoundingClientRect(); if (r.top < H) svgA += Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, 0)) * r.width; }
    if (svgA >= 0.4 * W * H) return 'diagram';
    const shellLike = el => { if (!el) return false; const s = cs(el); return (s.display === 'grid' || s.display === 'flex') && el.getBoundingClientRect().height >= H * 0.9 && /hidden|auto|clip/.test(s.overflowY + s.overflow); };
    if (shellLike(document.body) || shellLike(document.body.firstElementChild) || document.querySelector('.app-shell, #app > .app, [data-page-class="tool"]')) return 'tool';
    for (const g of document.querySelectorAll('*')) { const s = cs(g); if (s.display === 'grid' && g.children.length >= 6 && s.gridTemplateColumns.split(' ').length >= 3 && g.getBoundingClientRect().top < H) return 'dashboard'; }
    return 'document-short';
  };
  const cls = declared || infer();
  const out = {declared, inferred: declared ? null : cls, cls, W, H, chrome, rail: railsIn.length > 0, rails: railsIn.length};
  // ---- paged decks (L-125): a scope is measured the way it looks WHEN SHOWN ----
  // A deck that shows one slide at a time hides the others (display:none, visibility:hidden, [hidden],
  // or a hidden wrapper); a hidden box has no layout, so measure() found nothing and the slide read WARN.
  // The scope is forced visible for the length of its own measurement and put back byte-for-byte
  // (the `style` and `hidden` attributes of every element touched). Position / transform tricks are
  // NOT neutralised: a slide parked off-screen by translate keeps a consistent box (its content and
  // its area move together), and one hidden by scale(0) or a zero height is out of this vocabulary.
  const showScope = (sc, shownDisplay) => {
    const chain = []; for (let e = sc; e && e !== html; e = e.parentElement) chain.push({e, style: e.getAttribute('style'), hidden: e.getAttribute('hidden'), touched: false});
    for (const c of chain.slice().reverse()) {   // outermost first, so a child is judged after its wrapper opens
      if (c.e.hasAttribute('hidden')) { c.e.removeAttribute('hidden'); c.touched = true; }
      if (cs(c.e).display === 'none') { c.e.style.setProperty('display', c.e === sc ? shownDisplay : 'block', 'important'); c.touched = true; }
    }
    if (cs(sc).visibility === 'hidden') { sc.style.setProperty('visibility', 'visible', 'important'); chain[0].touched = true; }
    return {forced: chain.some(c => c.touched), undo: () => { for (const c of chain) if (c.touched) {
      c.e.getAttribute('style');   // flush Chromium's lazily-synced style attribute: removeAttribute on an unsynced one leaves a ghost style=""
      if (c.style === null) c.e.removeAttribute('style'); else c.e.setAttribute('style', c.style);
      if (c.hidden === null) c.e.removeAttribute('hidden'); else c.e.setAttribute('hidden', c.hidden); } }};
  };
  if (opts.scope) {
    const all = Array.from(document.querySelectorAll(opts.scope));
    const scopes = all.slice(0, opts.maxScopes || 8);
    // a forced slide takes the display type its VISIBLE sibling uses (flex / grid / block), not a guess
    const peer = all.find(x => cs(x).display !== 'none' && !x.closest('[hidden]'));
    const shownDisplay = peer && !/^(inline|none|contents)/.test(cs(peer).display) ? cs(peer).display : 'block';
    out.scopes = scopes.map((sc, i) => {
      const f = showScope(sc, shownDisplay);
      try { const r = sc.getBoundingClientRect(), s = cs(sc);
        const m = measure(sc, r.left + parseFloat(s.paddingLeft), r.right - parseFloat(s.paddingRight), null); m.index = i + 1; m.id = sc.id || null; m.forced = f.forced; return m;
      } finally { f.undo(); } });
    if (!scopes.length) out.page = measure(document.body, areaL, areaR, H * 3);
  } else {
    out.page = measure(document.body, areaL, areaR, H * 3);
    if (railEdge != null) out.page.maxR = Math.max(out.page.maxR || 0, Math.round(railEdge)), out.page.rightVoid = Math.max(0, Math.round(areaR - out.page.maxR)), out.page.reach = +(((out.page.maxR) - areaL) / (areaR - areaL)).toFixed(3);
    if (railEdgeL != null) {
      out.page.minL = Math.min(out.page.minL ?? Infinity, Math.round(railEdgeL));
      out.page.leftVoid = Math.max(0, Math.round(out.page.minL - areaL));
      if (out.page.maxR != null) out.page.fill = +((out.page.maxR - out.page.minL) / (areaR - areaL)).toFixed(3);
    }
  }
  // ---- clipped overflow (2026-10-13): a display formula wider than its own box ----
  // Reach measures the page edge, so a calculation line scrolling inside `math{overflow-x:auto}`
  // (the answer at its tail out of sight) read PASS. Whole document, not the first 3 screens:
  // a hidden formula anywhere is the same defect. scrollWidth counts the overflow whether the box
  // scrolls, clips or spills; a box with no layout (hidden slide, inline math) has clientWidth 0.
  if (opts.overflowSel) {
    const heads = Array.from(document.querySelectorAll('h1,h2,h3,h4'));
    const items = [];
    for (const el of document.querySelectorAll(opts.overflowSel)) {
      if (el.closest('[hidden],script,style')) continue;
      const cw = el.clientWidth, sw = el.scrollWidth; if (cw < 24) continue;
      if (sw - cw <= opts.overflowTol) continue;
      const hd = heads.filter(h => h.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING).pop();
      items.push({sel: el.tagName.toLowerCase(), sw, cw, hidden: sw - cw, near: hd ? (hd.id || hd.textContent.trim().slice(0, 16)) : null,
                  text: (el.textContent || '').replace(/\s+/g, '').slice(0, 40)});
    }
    out.overflow = {total: items.length, items: items.slice(0, 8)};
  }
  return out;
}"""


# ---------------------------------------------------------------------------------------------
# In-page consistency (user rulings 2026-10-31, PersonalSite): the width check above cannot see
# that four sibling section headings render 22/22/32/32 px or that a thumbnail card was copied
# under a new class name. Two checks, both WARN-only unless a selector is promoted by data:
#   C2  elements sharing (tag, class list, aria state) render alike (font-size/weight/family/line-height/spacing)
#   S3  two style rules under DIFFERENT selectors declare (nearly) the same declarations
# They read the page's own computed styles / CSSOM, so they rule on what they can determine:
# a drift between same-class elements is a measured fact; whether it was MEANT is a judgment, hence
# WARN. A stylesheet the browser refuses to expose is counted apart (`unread`), never skipped into
# a clean result. The width MEASURE_JS above is untouched, so width output is unchanged.
# ---------------------------------------------------------------------------------------------
CONSISTENCY_JS = r"""(opts) => {
  const cs = el => getComputedStyle(el);
  const out = {siblings: null, sheets: null};
  // ---- C2: same (tag, class list, aria state) -> same type style ----
  if (opts.siblings) {
    const props = opts.props, groups = new Map();
    let unseen = 0, inspected = 0, inSvg = 0, stateSplit = 0;
    for (const el of document.body.querySelectorAll('*')) {
      if (!el.classList || !el.classList.length) continue;
      if (el.closest('script,style,template,noscript,[hidden]')) continue;
      // Inside an <svg> a computed font-size is in user units of the viewBox, so equal drawn size is not equal
      // value, and a diagram generator sets it per node by design: not comparable, counted apart.
      if (opts.suppress !== false && el.closest('svg')) { inSvg++; continue; }
      const s = cs(el);
      if (s.display === 'none' || s.visibility === 'hidden' || !el.getClientRects().length) { unseen++; continue; }
      inspected++;
      // A declared ARIA state (the current page in a nav, a selected tab) is a meaning the reader is told
      // about, not a fork: it splits the group, and members of one state still compare with each other.
      // '', 'false' and 'undefined' (the ARIA default token) mean "no state" and group with plain elements.
      // The key carries the attribute NAME only: aria-current="page" and ="true" are one state and compare.
      const state = ['aria-current', 'aria-selected', 'aria-pressed', 'aria-expanded', 'aria-checked']
        .map(a => [a, (el.getAttribute(a) || '').trim().toLowerCase()])
        .filter(([, v]) => v && v !== 'false' && v !== 'undefined')
        .map(([a]) => '[' + a + ']').join('');
      if (state) stateSplit++;
      const key = el.tagName.toLowerCase() + '.' + Array.from(el.classList).sort().join('.') + state;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(el);
    }
    // A value can differ because the DECLARATION differs (22px vs 32px) or because one relative declaration
    // (0.9em, line-height 1.35) meets different parents. `rel` is the value in its relative reading: font-size
    // against the parent's, line-height and letter-spacing against the element's own font-size. A property
    // drifts only when neither the absolute nor the relative reading is equal across the group.
    const px = v => { const m = /^(-?[\d.]+)px$/.exec(v); return m ? parseFloat(m[1]) : null; };
    const rel = (el, p, v) => {
      const own = px(cs(el).fontSize), n = px(v);
      if (n == null) return v;                                   // normal / keyword: same string = same value
      if (p === 'font-size') { const par = el.parentElement ? px(cs(el.parentElement).fontSize) : null; return par ? (n / par).toFixed(3) : v; }
      if (p === 'line-height' || p === 'letter-spacing') return own ? (n / own).toFixed(3) : v;
      return v;
    };
    const findings = [], seen = []; let compared = 0, comparedEls = 0, relative = 0, inherited = 0;
    for (const [sel, els] of groups) {
      if (els.length < 2) continue;
      compared++; comparedEls += els.length; seen.push({sel, n: els.length});
      const drift = [];
      for (const p of props) {
        const by = new Map(), rels = new Set(); let inh = 0, inhNum = 0;
        for (const el of els) {
          const v = cs(el).getPropertyValue(p);
          rels.add(rel(el, p, v));
          const par = el.parentElement, pv = par ? cs(par).getPropertyValue(p) : null;
          if (par && pv === v) inh++;
          // A unitless line-height inherits as the NUMBER, so a child with its own font-size computes another px
          // value from the same number (1.3 x 18.6px vs the parent's 1.3 x 20px): both ratios to the own font-size
          // agree. Counted separately: the group is inherited only when EVERY member matches by one reading, so a
          // member that declares a number equal to a px/em parent's ratio beside one that inherits the px still drifts.
          if (par && p === 'line-height' && px(v) != null && px(pv) != null) {
            const a = px(pv) / px(cs(par).fontSize), b = px(v) / px(cs(el).fontSize);
            if (Math.abs(a - b) < 0.0005) inhNum++;
          }
          if (!by.has(v)) by.set(v, {v, n: 0, ex: ''});
          const e = by.get(v); e.n++;
          if (!e.ex) e.ex = el.id ? '#' + el.id : (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 16);
        }
        if (by.size < 2) continue;
        // both are context effects, not a drift of the class: one relative declaration meeting different
        // parents, or every element simply taking the value its parent has. Counted apart, never dropped silently.
        if (opts.suppress !== false && rels.size < 2) { relative++; continue; }
        if (opts.suppress !== false && (inh === els.length || inhNum === els.length)) { inherited++; continue; }
        drift.push({prop: p, values: Array.from(by.values()).sort((a, b) => b.n - a.n)});
      }
      if (drift.length) findings.push({sel, n: els.length, drift});
    }
    // A promoted selector (data: sibling_fail_selectors) sorts first so the 40-entry cut can never drop the
    // finding that decides a FAIL; the rest sort by group size.
    const promo = f => (opts.promote || []).some(p => p && f.sel.startsWith(p)) ? 1 : 0;
    findings.sort((a, b) => promo(b) - promo(a) || b.n - a.n);
    seen.sort((a, b) => b.n - a.n);
    out.siblings = {groups_compared: compared, elements_compared: comparedEls, elements_inspected: inspected,
                    unseen, svg_skipped: inSvg, relative_equal: relative, inherited_only: inherited, state_split: stateSplit, total: findings.length,
                    findings: findings.slice(0, 40), groups: seen.slice(0, 200)};
  }
  // ---- S3: read every style rule the browser exposes ----
  if (opts.rules) {
    const rules = [], unread = []; let sheets = 0;
    // declarations come from style.cssText (Chromium serialises shorthands collapsed, so `border:` is one
    // declaration, not a dozen longhands); split on top-level ';' only
    const decls = txt => { const r = []; let d = 0, q = null, cur = '';
      for (const ch of txt) { if (q) { if (ch === q) q = null; cur += ch; continue; }
        if (ch === '"' || ch === "'") { q = ch; cur += ch; continue; }
        if (ch === '(') d++; if (ch === ')') d--;
        if (ch === ';' && d === 0) { if (cur.trim()) r.push(cur.trim()); cur = ''; } else cur += ch; }
      if (cur.trim()) r.push(cur.trim());
      return r.map(x => { const i = x.indexOf(':'); return x.slice(0, i).trim() + ': ' + x.slice(i + 1).trim().replace(/\s+/g, ' '); }); };
    const label = r => '@' + r.constructor.name.replace(/^CSS|Rule$/g, '').toLowerCase() + (r.conditionText ? ' ' + r.conditionText : (r.name ? ' ' + r.name : ''));
    const walk = (list, ctx, sheet) => { for (const r of list) {
      if (r.type === 1) rules.push({sel: r.selectorText, ctx, sheet, decl: decls(r.style.cssText)});
      if (r.styleSheet) { try { walk(r.styleSheet.cssRules, ctx, sheet); } catch (e) { unread.push({href: r.styleSheet.href, why: e.name}); } }
      if (r.cssRules && r.cssRules.length) walk(r.cssRules, r.type === 1 ? ctx : (ctx + ' ' + label(r)).trim(), sheet);
    } };
    const all = Array.from(document.styleSheets).concat(Array.from(document.adoptedStyleSheets || []));
    all.forEach((sh, i) => { sheets++;
      let list; try { list = sh.cssRules; } catch (e) { unread.push({href: sh.href, why: e.name}); return; }
      walk(list, '', sh.href || 'inline#' + i); });
    for (const x of (opts.extraSheets || [])) {
      try { const sh = new CSSStyleSheet(); sh.replaceSync(x.text); walk(sh.cssRules, '', x.href); } catch (e) { unread.push({href: x.href, why: 'parse ' + e.name}); } }
    out.sheets = {total: sheets, unread: opts.extraSheets ? unread.filter(u => !opts.extraSheets.some(x => x.href === u.href)) : unread, rules};
  }
  return out;
}"""


def split_selectors(sel: str) -> list[str]:
    """Split a selector list on top-level commas (not inside () or [])."""
    parts, depth, cur = [], 0, ""
    for ch in sel:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def selector_tokens(sel: str) -> frozenset:
    """The names a selector mentions (classes, ids, tags), with pseudo-classes, pseudo-elements,
    attribute selectors and combinators dropped: `.story-thumb:hover img` -> {.story-thumb, img}."""
    s = re.sub(r"\[[^\]]*\]", "", sel)
    s = re.sub(r"::?[\w-]+(\([^)]*\))?", "", s)
    return frozenset(re.findall(r"[.#]?[A-Za-z_][\w-]*", s))


_FAMILY_PREFIX = ("margin-", "padding-", "background-", "transition-", "animation-", "outline-", "list-style-",
                  "mask-", "text-decoration-", "grid-template-", "scroll-margin-", "scroll-padding-")
_FAMILY_MIN = {"font": 5}   # `font: inherit` serialises as ~9 longhands; elsewhere two members already mean a shorthand


def decl_family(prop: str) -> str | None:
    """The shorthand a longhand belongs to (`border-top-color` -> border), so a shorthand the browser
    serialises as N longhands counts once. Without this `font: inherit` alone reads as 9 shared declarations."""
    if prop.startswith("border-"):
        return "border-radius" if prop.endswith("-radius") else (None if prop.startswith(("border-collapse", "border-spacing")) else "border")
    if prop.startswith("font-") or prop == "line-height":
        return "font"
    if prop in ("row-gap", "column-gap"):
        return "gap"
    if prop in ("flex-grow", "flex-shrink", "flex-basis"):
        return "flex"
    if prop in ("overflow-x", "overflow-y"):
        return "overflow"
    for pre in _FAMILY_PREFIX:
        if prop.startswith(pre):
            return pre.rstrip("-")
    return None


def collapse_decls(decls: list[str]) -> frozenset:
    """Declaration units of one rule: longhands of one shorthand family merge into a single unit."""
    fam: dict[str, list[str]] = {}
    units = set()
    for d in decls:
        prop = d.split(":", 1)[0].strip()
        f = decl_family(prop)
        if f is None:
            units.add(d)
        else:
            fam.setdefault(f, []).append(d)
    for f, members in fam.items():
        if len(members) >= _FAMILY_MIN.get(f, 2):
            units.add(f + "{" + "; ".join(sorted(members)) + "}")
        else:
            units.update(members)
    return frozenset(units)


def selector_targets(sel: str) -> frozenset:
    """The final compound of a selector as a set of classes / ids (what it styles, not where):
    `.prose .standfirst:hover` -> {{.standfirst}}. Returned as a set of such sets so a selector list can
    be compared target by target; a tag-only target (`p`, `img`) is dropped, it names no component, and
    `.tab.is-active` vs `.btn.is-active` are different targets (a shared state class is not a shared name)."""
    s = re.sub(r"\[[^\]]*\]", "", sel)
    last = re.split(r"\s*[>+~]\s*|\s+", s.strip())[-1]
    last = re.sub(r"::?[\w-]+(\([^)]*\))?", "", last)
    names = frozenset(re.findall(r"[.#][A-Za-z_][\w-]*", last))
    return frozenset([names]) if names else frozenset()


def find_forks(rules: list[dict], min_shared: int, min_ratio: float,
               same_target_min_shared: int | None = None, same_target_min_ratio: float | None = None,
               max_rules: int = FORK_MAX_RULES, posting_cap: int = FORK_POSTING_CAP) -> dict:
    """S3, pure function over the CSSOM dump. Two style rules whose selector lists share no selector and
    whose names differ are a PAIR when they share identical declarations on one of two evidence channels:
      copy         >= min_shared declarations covering >= min_ratio of the shorter rule
                   (`.proj-thumb` vs `.story-thumb`: one component declared twice under two names);
      same-target  the same class styled in two contexts (`.prose .standfirst` vs `.page-head .standfirst`)
                   needs far less (same_target_min_shared / _ratio): sharing the target name is itself
                   most of the evidence, and a 3-declaration fork is invisible to the copy channel.
    Pairs are grouped by WHAT DIFFERS between the two selectors, so one fork is one entry however many of
    its sub-rules (hover, img) were copied. A pair whose selectors name the same things (`.btn:hover` vs
    `.btn:focus`) is a state variant of one component and a pair where one selector's names contain the
    other's is a contextual override; neither is reported.
    Cost is bounded (the pair count of one declaration grows with the square of its posting list): rules
    beyond `max_rules` are not compared and a declaration used by more than `posting_cap` rules (`margin: 0`
    style boilerplate, which evidences nothing about a copy) is left out of the shared count. Both are
    returned under `not_checked` so the verdict names what was not compared."""
    st_k = min_shared if same_target_min_shared is None else same_target_min_shared
    st_r = min_ratio if same_target_min_ratio is None else same_target_min_ratio
    floor = min(min_shared, st_k)
    prep = []
    over = max(0, len(rules) - max_rules)
    for r in rules[:max_rules]:
        sels = split_selectors(r["sel"])
        decl = collapse_decls(r["decl"])
        if len(decl) >= floor and sels:
            prep.append((r, set(sels), decl, [selector_tokens(x) for x in sels],
                         frozenset().union(*[selector_targets(x) for x in sels])))
    index: dict[str, list[int]] = {}
    for i, (_, _, decl, _, _) in enumerate(prep):
        for d in decl:
            index.setdefault(d, []).append(i)
    shared: dict[tuple[int, int], int] = {}
    common = 0
    for members in index.values():
        if len(members) > posting_cap:
            common += 1
            continue
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                key = (members[a], members[b])
                shared[key] = shared.get(key, 0) + 1
    groups: dict[tuple, dict] = {}
    n_pairs = 0
    for (i, j), n in shared.items():
        ri, si, di, ti, gi = prep[i]
        rj, sj, dj, tj, gj = prep[j]
        ratio = n / min(len(di), len(dj))
        if si & sj:
            continue
        copy = n >= min_shared and ratio >= min_ratio
        same = bool(gi & gj) and n >= st_k and ratio >= st_r
        if not (copy or same):
            continue
        # which names differ: tokens present in one selector list and not the other
        left = frozenset().union(*ti) - frozenset().union(*tj)
        right = frozenset().union(*tj) - frozenset().union(*ti)
        if not left or not right:
            continue    # both empty: same component in another state / media context; one empty: a contextual override of the other
        a, b = sorted([tuple(sorted(left)), tuple(sorted(right))])
        g = groups.setdefault((a, b), {"a": list(a), "b": list(b), "pairs": []})
        first, second = (ri, rj) if tuple(sorted(left)) == a else (rj, ri)
        g["pairs"].append({"a": first["sel"], "b": second["sel"], "shared": n, "of": min(len(di), len(dj)),
                           "kind": "copy" if copy else "same-target", "decl": sorted(di & dj)})
        n_pairs += 1
    out = []
    for g in groups.values():
        g["pairs"].sort(key=lambda p: (-p["shared"], p["a"]))
        g["best"] = g["pairs"][0]
        out.append(g)
    out.sort(key=lambda g: (-g["best"]["shared"], g["a"]))
    return {"rules": len(rules), "pairs": n_pairs, "groups": out,
            "not_checked": {"rules": over, "common_decls": common}}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A loopback sheet that answers 3xx is not followed: the target may be anywhere (HTTPError -> unread)."""
    def redirect_request(self, *args, **kwargs):
        return None


# no ProxyHandler entries (system / environment proxies would route a loopback request through a third host)
_LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def fetchable_sheet(href: str, max_bytes: int = SHEET_MAX_BYTES) -> str | None:
    """Text of a stylesheet the browser would not expose to script (file:// pages cannot read a linked
    file:// sheet). Local files and loopback URLs only; everything else stays unread, never fetched.
    No redirect is followed and no proxy is used, and at most `max_bytes` are read: a larger sheet is
    None (unread), never a truncated one parsed as if complete."""
    try:
        sp = urllib.parse.urlsplit(href)
        if sp.scheme == "file":
            with open(urllib.request.url2pathname(sp.path), "rb") as fh:
                raw = fh.read(max_bytes + 1)
        elif sp.scheme in ("http", "https") and is_local(href):
            with _LOCAL_OPENER.open(href, timeout=10) as resp:
                if not is_local(resp.geturl()):
                    return None
                raw = resp.read(max_bytes + 1)
        else:
            return None
        if len(raw) > max_bytes:
            return None
        return raw.decode("utf-8", "replace")
    except Exception:
        return None


_IMPORT_RE = re.compile(r"""@import\s+(?:url\(\s*)?["']?([^"')\s;]+)""", re.I)


def sheet_imports(text: str, base: str) -> list[str]:
    """Targets of the `@import` rules in a stylesheet text, resolved against the sheet's own URL.
    `CSSStyleSheet.replaceSync` ignores @import, so these are not in the CSSOM dump and must be named unread."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return [urllib.parse.urljoin(base, m.group(1)) for m in _IMPORT_RE.finditer(text)]


def check_consistency(page, reg: dict, with_rules: bool, keep_rules: bool = False, suppress: bool = True) -> dict:
    """Run C2 (and S3 when `with_rules`) on a loaded page. Returns the raw findings, no verdict.
    `keep_rules` attaches the CSSOM dump (calibration re-tunes K/R offline from it); `suppress=False`
    switches the three C2 context filters off (calibration measures what they remove)."""
    cfg_c2 = reg.get("defect_sibling_style_drift", {})
    cfg_s3 = reg.get("defect_duplicate_rules", {})
    opts = {"siblings": True, "props": cfg_c2.get("props", ["font-size"]), "rules": bool(with_rules and cfg_s3),
            "suppress": suppress, "promote": [p for p in reg.get("sibling_fail_selectors", []) if p]}
    raw = page.evaluate(CONSISTENCY_JS, opts)
    res = {"siblings": raw["siblings"], "duplicate_rules": None}
    if opts["rules"]:
        sh = raw["sheets"]
        unread = sh["unread"]
        if unread:                                    # a sheet script cannot read: fetch it locally and parse it
            extra, still, imports = [], [], []
            for u in unread:
                text = fetchable_sheet(u["href"]) if u.get("href") else None
                (extra if text is not None else still).append({"href": u["href"], "text": text} if text is not None else u)
                if text is not None:
                    imports += [{"href": t, "why": "@import in " + u["href"]} for t in sheet_imports(text, u["href"])]
            if extra:
                sh = page.evaluate(CONSISTENCY_JS, {**opts, "siblings": False, "extraSheets": extra})["sheets"]
                seen_h = {u.get("href") for u in still}
                sh["unread"] = still + [i for i in imports if not (i["href"] in seen_h or seen_h.add(i["href"]))]
        forks = find_forks(sh["rules"], cfg_s3.get("min_shared", 5), cfg_s3.get("min_ratio", 0.8),
                           cfg_s3.get("same_target_min_shared"), cfg_s3.get("same_target_min_ratio"))
        res["duplicate_rules"] = {"sheets": sh["total"], "unread": sh["unread"], **forks}
        if keep_rules:
            res["duplicate_rules"]["_rules"] = sh["rules"]
    return res


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> dict:
    reg = json.loads(path.read_text(encoding="utf-8"))
    # a prefix is matched with startswith: "" matches every selector and would promote every WARN to FAIL
    bad = [p for p in reg.get("sibling_fail_selectors", []) if not isinstance(p, str) or not p.strip()]
    if bad:
        raise RuntimeError(f"{path.name}: sibling_fail_selectors holds an empty or non-string prefix {bad!r}"
                           " (it would promote every same-class drift to FAIL)")
    return reg


# AP-74 not-same-as: hooks/browser_pane_scope_guard.py::is_local — this takes a URL, that one a host; both delegate to hooks/_lib/hosts.py
def is_local(url: str) -> bool:
    """A loopback URL: a built site served by `astro preview` / `python -m http.server` with
    root-absolute asset paths (fb:072d2f5d). Every other network request stays aborted."""
    return is_local_host(urllib.parse.urlsplit(url).hostname or "")


def route_local_only(route) -> None:
    if is_local(route.request.url):
        route.continue_()
    else:
        route.abort()


def to_url(target: str) -> str:
    if "://" in target:
        return target
    return pathlib.Path(target).resolve().as_uri()


def verdict(meas: dict, reg: dict, forced_class: str | None = None) -> dict:
    """Pure function: measurement + registry -> {status, class, reasons...}. No browser here."""
    classes = reg["classes"]
    cls = forced_class or meas["cls"]
    inferred = (forced_class is None and meas["declared"] is None)
    rule = classes.get(cls)
    asym = reg["defect_left_anchored_cap"]["asymmetry_frac"]
    reasons, status = [], "PASS"
    if rule is None:
        return {"status": "WARN", "width_status": "WARN", "cls": cls, "inferred": inferred,
                "reasons": [f"class '{cls}' is not in page_classes.json — add a row; measured only"],
                "consistency_status": "PASS", "consistency_reasons": []}
    areas = meas.get("scopes") or [meas["page"]]
    worst = None
    for a in areas:
        st, why = "PASS", []
        if a["n"] == 0:
            st, why = "WARN", ["no painted/text block found in the measured area"]
        else:
            left_anchored = (a["rightVoid"] - a["leftVoid"]) > asym * a["areaW"]
            mode = rule["mode"]
            if mode == "centered":
                sym_ok = abs(a["leftVoid"] - a["rightVoid"]) <= rule.get("symmetry_px", 8) + 2
                if not sym_ok:
                    st = "FAIL"; why.append(f"not centred: left void {a['leftVoid']}px vs right void {a['rightVoid']}px")
                if a["fill"] < rule.get("min_fill", 0):
                    st = "FAIL"; why.append(f"fill {a['fill']:.0%} < {rule['min_fill']:.0%}")
            elif mode == "fill":
                if a["reach"] < rule["min_fill"]:
                    st = "FAIL"; why.append(f"reach {a['reach']:.0%} < {rule['min_fill']:.0%} (right void {a['rightVoid']}px of {a['areaW']}px)")
            elif mode == "centered-or-fill":
                sym_ok = abs(a["leftVoid"] - a["rightVoid"]) <= rule.get("symmetry_px", 8) + 2
                if not (sym_ok or a["reach"] >= 0.85):
                    st = "FAIL"; why.append(f"neither centred (voids {a['leftVoid']}/{a['rightVoid']}px) nor filled (reach {a['reach']:.0%})")
                if a["fill"] < rule.get("min_fill", 0):
                    st = "FAIL"; why.append(f"fill {a['fill']:.0%} < {rule['min_fill']:.0%}")
            if left_anchored and st != "FAIL":
                st = "FAIL"; why.append(f"left-anchored cap: right void {a['rightVoid']}px exceeds left void {a['leftVoid']}px by > {asym:.0%} of {a['areaW']}px")
            if a["findings_total"]:
                promoted = [f for f in a["findings"] if any(f["sel"].startswith(s) for s in reg.get("block_fail_selectors", []))]
                if promoted:
                    st = "FAIL"; why.append("promoted block(s): " + ", ".join(f["sel"] for f in promoted))
                elif st == "PASS":
                    st = "WARN"
                why.append(f"{a['findings_total']} narrower left-anchored painted block(s) alone in row: "
                           + ", ".join(f"{f['sel']} {f['w']}/{f['parent_w']}px" for f in a["findings"][:3]))
        if a.get("index"):
            why = [f"slide {a['index']}: {w}" for w in why]
        rank = {"PASS": 0, "WARN": 1, "FAIL": 2}
        if worst is None or rank[st] > rank[worst[0]]:
            worst = (st, why)
        reasons += why
    status = worst[0] if worst else "WARN"
    ov = meas.get("overflow") or {}
    if ov.get("total"):
        sev = reg.get("defect_clipped_overflow", {}).get("severity", "FAIL")
        if sev == "FAIL" or status == "PASS":
            status = sev
        reasons.append(f"{ov['total']} display formula(s) wider than their box (content hidden behind a scroll): "
                       + "; ".join(f"#{i['near'] or '?'} {i['sw']}/{i['cw']}px '{i['text'][:24]}'" for i in ov["items"][:4]))
    if inferred:
        # An inferred class caps the verdict at WARN in BOTH directions, fixed
        # 2026-09-08. The downgrade used to apply only to FAIL, so a page whose
        # class nobody declared could report a clean PASS -- and that PASS is an
        # artifact of the guess, not a measurement of the page. Measured case:
        # `outputs/diagram-authoring/mfp-audit-f5-owner-view.html` reads
        # reach 74% with symmetric 436/436 voids, which PASSES as the inferred
        # `document-short` and FAILS as `document-long`, the class an audit page
        # with diagrams plausibly is. The run printed "0 FAIL / 0 WARN" and that
        # number would have been carried forward as evidence. A gate may only
        # rule on what it can DETERMINE -- in the permissive direction too.
        was, status = status, "WARN"
        note = (f"class INFERRED as '{cls}' (no data-page-class) — verdict capped at "
                f"WARN, so this row is NOT evidence the page is well laid out; "
                f"it measured {was} against a GUESSED ruler. Repair: declare "
                f"`<html data-page-class=\"…\">` and re-run. ")
        reasons.insert(0, note + reg["unknown_policy"]["promotion_trigger"])
    # In-page consistency: class-independent facts about the page's own styles, so the inferred-class cap
    # above does not touch them. WARN lifts a PASS; only a selector listed in `sibling_fail_selectors` FAILs.
    width_status = status  # callers that report the width property alone (render_story S7b) read this
    c_status, c_reasons = consistency_verdict(meas.get("consistency"), reg)
    if c_reasons:
        reasons += c_reasons
        if c_status == "FAIL":
            status = "FAIL"
        elif c_status == "WARN" and status == "PASS":
            status = "WARN"
    return {"status": status, "width_status": width_status, "cls": cls, "inferred": inferred, "reasons": reasons,
            "consistency_status": c_status if c_reasons else "PASS", "consistency_reasons": c_reasons}


def _fmt_vals(drift: dict) -> str:
    return " / ".join(f"{v['v']} x{v['n']}" + (f" [{v['ex']}]" if v.get("ex") else "") for v in drift["values"][:4])


def consistency_verdict(cons: dict | None, reg: dict) -> tuple[str, list[str]]:
    """Pure: C2 / S3 findings -> (status, reason lines). PASS with no lines when there is nothing to say."""
    if not cons:
        return "PASS", []
    lines, status = [], "PASS"
    sib = cons.get("siblings") or {}
    finds = sib.get("findings") or []
    prefixes = [s for s in reg.get("sibling_fail_selectors", []) if isinstance(s, str) and s.strip()]
    promoted = [f for f in finds if any(f["sel"].startswith(s) for s in prefixes)]
    if promoted:
        status = "FAIL"
        # promoted findings first: the 6-line cut must never hide the selector that decides a FAIL
        finds = promoted + [f for f in finds if f not in promoted]
    for f in finds[:6]:
        lines.append(f"same-class siblings render differently: {f['sel']} ({f['n']} elements) "
                     + "; ".join(f"{d['prop']} {_fmt_vals(d)}" for d in f["drift"])
                     + (" [promoted to FAIL]" if f in promoted else ""))
    if len(finds) > 6:
        lines.append(f"... and {len(finds) - 6} more same-class groups with differing type style")
    dup = cons.get("duplicate_rules") or {}
    groups = dup.get("groups") or []
    for g in groups[:6]:
        b = g["best"]
        more = f" (+{len(g['pairs']) - 1} related rule pair(s) in the same fork)" if len(g["pairs"]) > 1 else ""
        kind = "the same name styled in two contexts" if b.get("kind") == "same-target" else "a component declared twice"
        lines.append(f"duplicate rules: {b['a']} and {b['b']} share {b['shared']} declarations (of {b['of']} in the shorter rule; {kind}){more}")
    if len(groups) > 6:
        lines.append(f"... and {len(groups) - 6} more duplicated-rule forks")
    nc = dup.get("not_checked") or {}
    if nc.get("rules") or nc.get("common_decls"):
        lines.append("rule duplication partly checked, not compared: "
                     + ", ".join(x for x in (f"{nc['rules']} style rule(s) beyond the {FORK_MAX_RULES}-rule cap" if nc.get("rules") else "",
                                              f"{nc['common_decls']} declaration(s) used by more than {FORK_POSTING_CAP} rules" if nc.get("common_decls") else "") if x))
    local = [u for u in (dup.get("unread") or []) if not u.get("href") or is_local(u["href"]) or u["href"].startswith("file:")]
    if local:
        lines.append("rule duplication not checked for " + ", ".join(u.get("href") or "(inline)" for u in local[:3])
                     + " (the browser did not expose that stylesheet)")
    if status != "FAIL" and (finds or groups):
        status = "WARN"
    # what the C2 context filters set aside, printed beside the findings so a reader sees what was NOT ruled on
    # (a drift set on a shared wrapper hides behind `inherited_only`). Only with another consistency line: a page
    # with nothing to say keeps its output unchanged; the counts are always in --json.
    skipped = [(sib.get(k) or 0, label) for k, label in (("svg_skipped", "svg element(s)"), ("relative_equal", "relative-equal property(ies)"),
                                                           ("inherited_only", "inherited-only property(ies)"),
                                                           ("state_split", "element(s) grouped apart by an aria state"))]
    if lines and sib and any(n for n, _ in skipped):
        lines.append(f"same-class check compared {sib.get('groups_compared', 0)} group(s); set aside, not ruled on: "
                     + ", ".join(f"{n} {label}" for n, label in skipped if n))
    return status, lines


def gate_paths(targets, viewports=None, forced_class=None, reg=None, controls=True, advisory=None):
    """Measure every target at every viewport. Returns rows; raises RuntimeError(2) when the instrument is missing."""
    reg = reg or load_registry()
    gating = [tuple(v) for v in reg["reference_viewports"]["gating"]]
    adv = [tuple(v) for v in reg["reference_viewports"]["advisory"]]
    viewports = viewports or (gating + adv)
    advisory = set(advisory or adv) - set(gating)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # downgrade-and-forward: the caller prints, never claims
        raise RuntimeError(f"instrument unavailable: {exc}") from exc
    rows = []
    work = list(targets)
    if controls:
        work = [str(FIXTURES / f) for f in ALL_CONTROLS] + work
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:
            raise RuntimeError(f"instrument unavailable: {exc}") from exc
        for t in work:
            is_ctl = controls and t.startswith(str(FIXTURES))
            vps = [gating[0]] if is_ctl else viewports
            for (w, h) in vps:
                page = browser.new_page(viewport={"width": w, "height": h})
                page.route("http://**", route_local_only); page.route("https://**", route_local_only)
                try:
                    page.goto(to_url(t), wait_until="load", timeout=60000)
                    page.wait_for_timeout(300)
                    cls_hint = forced_class
                    probe = page.evaluate("() => document.documentElement.getAttribute('data-page-class')")
                    cls_for_scope = cls_hint or probe
                    rule = reg["classes"].get(cls_for_scope or "", {})
                    opts = {"asym": reg["defect_left_anchored_cap"]["asymmetry_frac"],
                            "scope": rule.get("scope"), "maxScopes": rule.get("max_scopes", 8),
                            "backdrop": bool(rule.get("backdrop_bands")),
                            "overflowSel": ", ".join(reg.get("defect_clipped_overflow", {}).get("selectors", [])),
                            "overflowTol": reg.get("defect_clipped_overflow", {}).get("tolerance_px", 2)}
                    meas = page.evaluate(MEASURE_JS, opts)
                    if not cls_for_scope and reg["classes"].get(meas["cls"], {}).get("scope"):
                        opts["scope"] = reg["classes"][meas["cls"]]["scope"]; meas = page.evaluate(MEASURE_JS, opts)
                    # in-page consistency: C2 at every viewport (media queries can change it), S3 once per file —
                    # the CSSOM does not depend on the viewport, so repeating it only repeats the lines
                    # Its own try: an exception here must never replace a width verdict (a width FAIL turned into a
                    # WARN "could not measure" with exit 0). The width status stays; the reason names what is missing.
                    try:
                        meas["consistency"] = check_consistency(page, reg, with_rules=((w, h) == vps[0]))
                        cons_err = None
                    except Exception as exc2:
                        meas["consistency"] = {}
                        cons_err = f"consistency not computed: {exc2}"
                    v = verdict(meas, reg, forced_class)
                    if cons_err:
                        # a check that did not run is never a PASS: WARN, and the reason travels with the field
                        v["reasons"].append(cons_err)
                        v["consistency_reasons"].append(cons_err)
                        if v["consistency_status"] == "PASS":
                            v["consistency_status"] = "WARN"
                        if v["status"] == "PASS":
                            v["status"] = "WARN"
                    if (w, h) in advisory and v["status"] == "FAIL":
                        v["status"] = "WARN"; v["reasons"].insert(0, "advisory viewport — FAIL downgraded")
                        for k in ("width_status", "consistency_status"):
                            if v[k] == "FAIL":
                                v[k] = "WARN"
                                if k == "consistency_status":
                                    v["consistency_reasons"].insert(0, "advisory viewport — FAIL downgraded")
                    a = (meas.get("scopes") or [meas["page"]])
                    summary = a[0] if len(a) == 1 else min(a, key=lambda x: x["reach"])
                    cons = meas["consistency"]
                    dup = cons.get("duplicate_rules")
                    rows.append({"target": t, "control": ALL_CONTROLS[pathlib.Path(t).name] if is_ctl else None,
                                 "viewport": f"{w}x{h}", "class": v["cls"], "inferred": v["inferred"],
                                 "status": v["status"], "width_status": v["width_status"],
                                 "consistency_status": v["consistency_status"], "consistency_reasons": v["consistency_reasons"],
                                 "reach": summary["reach"], "fill": summary["fill"],
                                 "left_void": summary["leftVoid"], "right_void": summary["rightVoid"],
                                 "areas": [{k: x.get(k) for k in ("index", "id", "n", "reach", "fill", "findings_total", "forced")} for x in (meas.get("scopes") or [])],
                                 "overflow": (meas.get("overflow") or {}).get("items", []),
                                 # in-page consistency findings under their own keys (None = not computed at this viewport)
                                 "sibling_drift": cons.get("siblings"),
                                 "duplicate_rules": None if dup is None else {
                                     **{k: dup[k] for k in ("sheets", "unread", "rules", "pairs", "not_checked")},
                                     "groups": [{**g, "pairs": g["pairs"][:5]} for g in dup["groups"]]},
                                 "consistency_error": cons_err,
                                 "chrome": meas["chrome"], "reasons": v["reasons"]})
                except Exception as exc:
                    rows.append({"target": t, "control": None, "viewport": f"{w}x{h}", "class": "?", "inferred": True,
                                 "status": "WARN", "width_status": "WARN", "consistency_status": "PASS", "consistency_reasons": [],
                                 "reach": 0, "fill": 0, "left_void": 0, "right_void": 0, "chrome": [], "areas": [],
                                 "sibling_drift": None, "duplicate_rules": None,
                                 "reasons": [f"could not measure: {exc}"]})
                finally:
                    page.close()
        browser.close()
    if controls:
        for name, label in ALL_CONTROLS.items():
            got = [r for r in rows if r["target"] == str(FIXTURES / name)]
            want = control_want(label)
            if not got or got[0]["status"] not in want:
                raise RuntimeError(f"fill-gate calibration: {label} control did NOT {'pass' if 'PASS' in want else 'fire'}"
                                   f" (want {'/'.join(want)}, got {got[0]['status'] if got else 'no row'}) — instrument fault, no verdict is valid")
            if label in CONSISTENCY_CONTROLS.values():
                bad = consistency_control_problems(label, got[0])
                if bad:
                    raise RuntimeError(f"fill-gate calibration: {label} control read the wrong VALUES ({bad[0]})"
                                       " — instrument fault, no verdict is valid")
    return rows


def fmt(r: dict) -> str:
    if r["control"]:
        who = "control " + r["control"]
    elif "://" in r["target"]:
        who = r["target"]
    else:
        p = pathlib.Path(r["target"])
        who = p.name if p.name.lower() not in ("index.html", "index.htm") else f"{p.parent.name}/{p.name}"
    cls = ("inferred:" if r["inferred"] else "") + str(r["class"])
    line = f"fill-gate: {r['status']:4s} {r['viewport']:9s} class={cls:24s} reach={r['reach']:.0%} fill={r['fill']:.0%} void L/R={r['left_void']}/{r['right_void']}px  {who}"
    if r["reasons"]:
        line += "\n" + "\n".join("           - " + x for x in r["reasons"])
    return line


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--viewport", action="append", help="WxH; repeatable; default = registry gating + advisory")
    ap.add_argument("--class", dest="cls", help="force a class (overrides the page's declaration)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-controls", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="only non-PASS lines")
    a = ap.parse_args(argv)
    vps = [tuple(int(x) for x in v.lower().split("x")) for v in a.viewport] if a.viewport else None
    try:
        rows = gate_paths(a.targets, viewports=vps, forced_class=a.cls, controls=not a.no_controls)
    except RuntimeError as exc:
        print(f"fill-gate: SKIP — {exc}. Downgrade-and-forward: the width property is UNVERIFIED for these files.", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            if a.quiet and r["status"] == "PASS" and not r["control"]:
                continue
            print(fmt(r))
        n_fail = sum(1 for r in rows if r["status"] == "FAIL" and not r["control"])
        n_warn = sum(1 for r in rows if r["status"] == "WARN" and not r["control"])
        ctl = ("controls fired (known-bad + known-bad-formula-overflow FAIL, known-good + known-good-fixed-panel PASS, "
               "consistency-bad WARN with the 22/32 px drift + thumb and standfirst forks named, consistency-good neither of them, "
               "consistency-clean PASS with no finding)"
               if not a.no_controls else "controls SKIPPED")
        print(f"fill-gate: {'FAIL' if n_fail else 'PASS'} — {n_fail} FAIL / {n_warn} WARN over {len([r for r in rows if not r['control']])} file×viewport rows; {ctl}")
    return 1 if any(r["status"] == "FAIL" and not r["control"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
