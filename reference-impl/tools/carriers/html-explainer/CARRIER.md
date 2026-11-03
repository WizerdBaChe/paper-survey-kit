# html-explainer — carrier card

Version: **9** (registry row `html-explainer` in `tools/carriers/registry.json`; the two must agree)
Consumes: `explainer/1` (`tools/carriers/schema/explainer-1.schema.json`). Produces: one self-contained `.html` file.
Page class: `document-long` (declared on `<html data-page-class>`), reading mode `look-up`.

## What it is for

The look-up / skim form of an explanatory deliverable: a long page with a left section nav, a right
"本節速查" rail, hover cards for glossary terms and references, and a glossary and a references section at
the end. It is the web twin of `pptx-explainer`; both read the same `explainer/1` content file. The output
is a generated artifact: never hand-edit it, change the content file and rebuild (the generator stamp
catches a hand edit).

Not for: node views (dashboards, launchers), figure-led showcase pages, or decks (those are other page
classes with other carriers).

## Block / field -> element mapping

| content (explainer/1) | element in the page |
|---|---|
| `meta.title` / `subtitle` | `<title>`, `#side h1` + `.sub`, `h1.title` + `p.lead` |
| `meta.date` | `.eyebrow` and the colophon |
| `meta.purpose` | `.box.def` with tag 閱讀目的 under the title block |
| `meta.author`, `meta.source_note` | colophon `footer.buildinfo` (日期 / 作者 / source note) |
| `meta.lang`, `meta.audience` | `<html lang>`, `<html data-audience>` |
| section | `main > section.ch#<id>[data-kind=content]` with `h2`; one `#side a.l1[data-sec]` link |
| section `summary` | `.chsub` under the h2 and the first line of that section's rail entry |
| section `takeaways` | rail entry list 本節重點 (added by the carrier script, see below) |
| `para` | `<p>` |
| `bullets` | `<ul><li>` |
| `steps` | `<ol class="steps">`, one `li` per step: `span.st-t` title + `span.st-d` text, counter-numbered |
| `table` | `div.twrap > table` with `<caption>`, `<th scope=col>`, rows |
| `figure` | `figure.tb#<sid>-figN` with `<img>` (base64 data URI), `<figcaption>` = caption, then `div.fnotes` with 「圖中呈現：{shows}」 and (if present) 「未畫出：{not_drawn}」 |
| `callout` key / note / warn | `div.box.def` / `.src` / `.warn` with `data-kind`; tag = `title` or 重點 / 備註 / 注意 |
| `metrics` | `div.metrics > div.metric` (value in `.val`, `.mu` unit, `.ml` label, `.mn` note) |
| `quote` | `blockquote.quote > p` + `footer` (source) |
| `**bold**` | `<b>` |
| `[[g:id]]` | `span.sym[tabindex=0][data-key]` showing the term; card from `SITE_SYMS` |
| `[[r:id]]` | `span.ref[tabindex=0][data-key]` showing the label; card from `SITE_REFS` |
| `[[s:id]]` | `<a href="#id">` with the section heading as text |
| `glossary` | `SITE_SYMS` (key = term, `n:true` so only explicit markers decorate, `s` = `#g_<id>`) + section `x_glossary` (h2 詞彙, `dl.gl`, `dt#g_<id>`) |
| `refs` | `SITE_REFS` (key = label, `n:true`, `s` = `#r_<id>`) + section `x_refs` (h2 出處, `ol.refs`, `li#r_<id>`, `href` as a plain link) |

Generated ids use `_` (`x_glossary`, `g_*`, `r_*`) which a content id (`[a-z0-9-]`) can never contain.
Two glossary terms or labels that are equal get `（<id>）` appended to the later key so registry keys stay unique.
All text goes through `html.escape`; JSON inside `<script>` additionally escapes `<`.

## Rules it implements

- **Reading shell**: the accepted `research-site-shell` DOM contract, unmodified vendored CSS/JS (below).
  Behaviours inherited: drag-resizable and collapsible `#side` / `#rail` (widths in localStorage), hover cards
  (350 ms), click-to-jump + Backspace return, G glossary overlay, pinnable cards, a hint bar whose × collapses it to a restore tab, JS-dead
  degradation to a plain scrollable document. The rail exists from 1500 px up (shell media query).
- **deliverable-doc-refs.md**: define-before-use (every coded term is a `[[g:]]` marker with a card and a
  glossary row), no left-anchored cap (fluid main, no max-width), `prose-doc-layer.css` loaded LAST,
  `data-page-class` declared, no new type tier (carrier CSS reuses the layer's four tiers).
- **Single file / offline**: CSS, JS and figures inlined; the shell's Google Fonts `<link>` is NOT carried
  over (it is an external load). Font stacks fall back to local CJK faces (Noto Sans/Serif TC if installed,
  else Microsoft JhengHei / PingFang TC).
- **Deterministic**: no clock, no randomness; vendored text is read with CRLF normalised to LF; output is
  written LF-only. Same content + same figure bytes -> byte-identical file.
- **Rail extension** (carrier-owned script at the end of the page, `RAIL_JS` in `render.py`): the shell's
  rail lists tokens and figures only; this script puts the section's summary and takeaways (from
  `script#rail-data`, textContent only) above them and re-applies after every rail rebuild. If it fails it
  logs a structured console error and the shell's rail still works.

## Gates (`gates.py`)

| gate | what it rules on | notes |
|---|---|---|
| `fill_gate` | `tools/page-fill-gate/fill_gate.py --json` on the built file, 3 viewports | no target row may FAIL and the class must be declared; FAIL, no JSON or exit 2 (instrument absent) -> False (UNDET is never a pass); a width WARN still blocks; a consistency-only WARN passes with its reasons carried into the detail (v9, user ruling 2026-11-02). The tool runs its own known-bad / known-good controls on every call |
| `main_fill` | `<main>` itself, at the registry's reference viewports (read from `page_classes.json`) | main width >= 85 % (the `document-long` `min_fill`) of the width left beside the fixed nav and rail; no Playwright / Chromium -> False (UNDET). Carrier-owned addition: `fill_gate`'s reach counts the rail (from 1500 px) and the hint bar's text span (below that) as content, both at the right edge, so a capped `<main>` still reads reach ~100 % (measured 2026-10-09, `max-width:640px` on main: fill_gate PASS, main_fill 57 % / 49 % / 66 %). `fill_gate` still catches painted blocks capped inside the column (a width WARN -> False here) |
| `structure` | the file against itself | `data-page-class` + `lang`; exactly one `<main>`; content sections == `<main data-sections>` list, each with h2 text; at most one glossary and one refs section; no `[[` anywhere; no resource loading from outside (`src`/`srcset`/`data`/`poster` not `data:`, `<link href>`, CSS `@import` / `url()` not `data:`); unique ids; every `#anchor` link resolves; shell contract ids present; every hover token has a registry entry and every entry's `s` target exists |

`structure` limit: `build.py` gives gates only the output path, so it cannot compare the page with the
content file; it proves internal consistency (the section list travels inside the file), not fidelity to the
content. External `<a href>` links (refs with `href`) are navigation, not loads, and are allowed.

Build-wide checks (content validation, generator stamp) belong to `build.py`, not to this folder.

## Upstream provenance

Reading shell: AssetVault asset `research-site-shell` (`assets/pattern-template/html-css/research-site-shell`,
promoted 2026-10-18 under D-40 from the candidate of class `reading-shell:document-long`, accepted by the user
2026-10-04; behaviour contract `CONTRACT.md` SH-1..SH-13), origin repo `<share>/_packs/Claude系統工程演進研究_20261003` (at `<share>/` until 2026-10-21).
Prose layer: AssetVault asset `prose-doc-layer`.

`vendor/` holds byte-identical copies of three files (never edit them). They are DECLARED in
`asset-choices.json` (mode sync) and kept by AssetVault `tools/consumers.py`: `consumers.py check <this folder>`
says whether they match the asset, `consumers.py sync <this folder> --pull` re-vendors. No hash is copied
here: `tests/test_html_explainer.py` compares each vendor file (LF-normalised) with the asset file at the
`base` commit that `consumers.py` recorded in `asset-choices.json`, so a re-vendor needs no hand edit.

Shell storage keys `research-site-layout-v1` / `research-site-hint-v1` are shared by every `file://` page
built on this shell: a width chosen on one such page applies to the others.

## Tests

`python -X utf8 -m unittest discover -s ~/.claude/tools/carriers/html-explainer/tests -v`
(golden sample: determinism, every block type in the DOM, section / nav / rail / glossary / refs counts,
vendor integrity, escaping; negative controls: page class removed, leftover `[[g:x]]`, external image,
deleted section -> `structure` False; left-anchored 560 px painted blocks -> `fill_gate` False; 640 px
capped `<main>` -> `main_fill` False). The width tests drive headless Chromium and take about 50 s.

## Change log

- v1 (2026-10-09): first build — shell vendored from research-site-shell@810a93e, explainer/1 mapping, rail summary/takeaways extension, gates `fill_gate` + `main_fill` + `structure`, tests with negative controls.
- v2 (2026-10-14): re-vendored `site.css` / `site.js` from the candidate after the hint-bar revision (user ruling 2026-10-14): × collapses the bar to a `#hint .hr` restore tab instead of hiding it for good; the × label reads 收合這條提示 (`render.py`). The vendor files on disk are now LF, so both hash columns agree.
- v3 (2026-10-14): re-vendored `site.css` after the candidate was re-shelved from origin `69c7995` (adds the origin's unused-here `.edition-banner` rule); no change to any explainer page's look.
- v4 (2026-10-18): vendor taken from the promoted AssetVault asset `research-site-shell` (D-40) and declared in `asset-choices.json`; `site.js` +97/−5 (collapsible nav groups, hint bar, layout memory as in the SHARE origin), `site.css` +30; the stale CRLF hash of `prose-doc-layer.css` replaced by the bytes on disk; the vendor test compares with the asset instead of the shelf candidate.
- v5 (2026-10-18): re-vendored \site.css\ / \site.js\ from esearch-site-shell\ 394ce4b (SH-12 per-frame input work and \content-visibility:auto\ on chapters, SH-13 no filter autofocus on a pointer drawer open); the card header version, stale at 1, now follows the registry.
- v6 (2026-10-26): re-vendored `site.css` / `site.js` from `research-site-shell` 63078f7 (SH-14 synonym keys folded under their standard entry, long glossary keys wrap in their column, SH-15 no decoration inside `<math>`, SH-16 content-date stamp badge). The copy had stood vault-ahead since 2026-10-20 and the vendor test was failing on it; found through the system-hmi `assetvault.template-consumers` alarm (alarm-visibility round, ruling Q3).
- v7 (2026-10-26): re-vendored `site.js` from `research-site-shell` 13cd418 (SH-18: token matching specified once and exposed as `window.SiteShell.matchText` / `decorateIn`; block keys `b` match but show no card; no change for this carrier's `n:true` registries). The asset's Python twin `shell_match.py` is not vendored: this carrier decorates explicit markers only.
- v8 (2026-10-31): re-vendored `site.css` from `research-site-shell` ee7e506 (SH-19 card pager, SH-20 chapter-link block styles). An explainer page is one page with no pager or chapter links, so no output changes its look; `site_links.py` is not vendored for the same reason.
- v9 (2026-11-02): `fill_gate` blocks on a FAIL row or a width WARN (left-anchored blocks, control e unchanged); a consistency-only WARN goes into the gate detail (user ruling, decision sheet feedback-review B2). Since 2026-10-31 the fill gate's same-class / duplicate-rule checks emitted WARNs on the vendored `site.css`, and this carrier treated every WARN as a failure, so no explainer page could be stamped. The CSS duplicates are fixed upstream in `research-site-shell`, not in this vendor copy.
- v10 (2026-11-02): re-vendored `site.css` from `research-site-shell` c4d2efa (the card, list-link and hint-button looks each declared once; every computed style on the asset demos unchanged). The `span.val` line-height WARN was a fill-gate false positive (each span inherits its parent's unitless line-height, 1.3 in a metric, 1.8 in the meta line), fixed in `page-fill-gate` 68ca7f14/28ef0de7, not here. The vendor test now compares each file with the asset at the `base` that `consumers.py` records in `asset-choices.json`; the hand-copied sha256 table is gone (fb:38c88250).

## Maintenance

Any edit to this folder (render, gates, vendor, this card) bumps `version` in `tools/carriers/registry.json`,
adds a Change log line above, and must end with `python -X utf8 ~/.claude/tools/carriers/build.py selftest`
passing (it rebuilds the golden sample through this carrier and runs the hand-edit and stale-content controls).
Re-vendoring: `python -X utf8 <projects>/AssetVault/tools/consumers.py sync <this folder> --pull`, update the
hash table, rerun the tests.
Review when: `consumers.py check` reports this folder vault-ahead (a newer `research-site-shell` or
`prose-doc-layer`), or the `document-long` row of
`tools/page-fill-gate/page_classes.json` changes (same trigger as the registry row's `review_when`).
