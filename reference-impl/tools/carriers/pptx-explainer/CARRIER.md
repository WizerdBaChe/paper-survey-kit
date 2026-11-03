# pptx-explainer — explainer/1 -> read-through PPTX deck

Version **1** (registry row `pptx-explainer`, `tools/carriers/registry.json`). Consumes `explainer/1`
(`tools/carriers/schema/explainer-1.schema.json`). Output suffix `.pptx`. Reading mode: read-through
(from the first slide to the last, or presented). Dispatcher: `python -X utf8 tools/carriers/build.py build --carrier pptx-explainer --content <c.json> --out <f.pptx>`.

Consumer of this file: builders and maintainers. Slide text is Traditional Chinese (the content's language);
everything in this folder is English.

## Purpose

Turn one `explainer/1` content file into a 16:9 deck, mechanically and deterministically: same content ->
same slide count and texts. The deck is a REBUILT artifact, never hand-edited (edit the content, rebuild).
The carrier decides layout only; what the deck says lives in the content file.

## Declared deck class and density

- Class: **presentation** (the stricter reading in `rules/office-deck-deliverables.md`; a deck with no declared
  class is treated as presentation).
- Density (P2): **繁複** — the text on the slide is enough to be read through; the speaker's extra material goes
  to the notes. Declared on the cover slide's notes (in Chinese, presenter-facing).

## Slide plan

| # | slide | built from | title / description |
|---|---|---|---|
| 1 | cover | `meta.title`, `subtitle`, `purpose`, `date`, `author` | title 38 pt, subtitle 20 pt, purpose 16 pt (own object), date + author 13 pt |
| 2.. | per section, one or more slides | `sections[i]` | kicker `第 i 節`; title = heading; description = `summary` (own object, first slide only); blocks top to bottom |
| .. | section continuation | the blocks that did not fit | title `<heading>（續）`, no description |
| .. | section closing box | `takeaways` | box 「本節重點」 on the section's LAST slide (own slide `（續）` when it does not fit) |
| n-2 | 詞彙 (1+ slides) | `glossary` | table: 詞彙 / English (only when any entry has `en`) / 說明; skipped when no glossary |
| n-1 | 出處 (1+ slides) | `refs` | table: 出處 / 說明 / 連結 (only when any ref has `href`; plain text, no hyperlink); skipped when no refs |
| n | colophon 「版本與來源」 | `meta.source_note`, `date`, `author` | three labelled lines |

Appendix slides carry the kicker `附錄`. Page numbers (`k / N`, slide 2 on) are stamped by a post-pass from slide order.
Core properties: `title`, `author`, `language`, and `keywords = "sections=<n>"` (independent section count the
structure gate checks the slide count against; the stamp step later fills `content_status` / `comments`).

## Block -> shape mapping

Shape names are the content key: `<section id>.<block index, 1-based>.<type>` (+ `-bg` for decoration, `.step<k>`,
`.metric<k>`, `.figcard<k>`, `.takeaways<k>`); appendix tables are `glossary.table` / `refs.table`.
Exact names `kicker`, `title`, `description`, `caption`, `page-number`, `cover-title|sub|purpose|meta` are the
vendored type audit's floor keys and must not be renamed.

| block | shape(s) | tier (pt) |
|---|---|---|
| para | one text object, body, 1.5 line spacing | body 15.5 |
| bullets | one text object, real bullet characters (`a:buChar`) with a 0.32 in hanging indent | body 15.5 |
| steps | 2-4 short steps: numbered flow boxes with arrows (flat connectors); otherwise a vertical numbered list (round badge + title + text) | box title 18 / text 15; list title 18 / text 15.5 |
| table | native pptx table (`L.table`): header row, zebra, first column bold; optional 12 pt caption above; columns weighted by natural text width | 13-15 (searched inside the tier) |
| figure | picture (aspect MEASURED with PIL), 12 pt caption under it, figure card to its right: 「圖中呈現」 `shows`, 「未畫出」 `not_drawn` | card 15, caption 12 |
| callout | filled box with a colour bar and a 19 pt bold title (default 重點 / 備註 / 注意 when `title` is absent); key = blue tint, note = grey, warn = orange tint | title 19 / body 15.5 |
| metrics | number cards, up to 4 per row: value 32 pt + unit 18 pt, label 15.5 bold, note 14 | 32 / 18 / 15.5 / 14 |
| quote | grey box with an accent bar, text, `—— source` line | 15.5 / 14 |
| takeaways | white box with an accent rule, heading 「本節重點」, bullets in up to 3 columns | 19 / 15.5 |

Inline markup is rendered from `common/inline.py` tokens only: `**bold**` -> bold run; `[[g:id]]` -> the glossary
TERM in bold; `[[r:id]]` -> `〔label〕`; `[[s:id]]` -> the target section's heading. Table cells and titles reach the
vendored helpers as `**bold**` strings produced FROM tokens (never from the raw text).

Speaker notes, every slide (P1): `圖種：<kinds>` / `這頁回答：<question>` (+ the glossary terms and refs the slide
uses). Text-only slides say why (「文字（概念說明，沒有可比較的數值或結構）」). The question is the section `summary`
(or `<heading>是什麼`).

## Overflow rule

Blocks are measured with the vendored estimators (`est_h`, `_row_h`) and stacked with a 0.22 in gap down to y = 7.0 in
(the page-number band starts there).

1. A block that does not fit the remaining height, but would fit a fresh slide, moves WHOLE to a new slide
   `<heading>（續）`.
2. A block bigger than a whole slide is split: paragraph by sentence (`。！？`), bullets / steps / metrics by item,
   table by row (header repeated; at least 2 rows per fragment). A split steps list continues numbering, vertical form.
3. A figure is elastic: it shrinks (not below 1.8 in tall) to the room left, else moves to a new slide.
4. An unsplittable block bigger than a slide (a callout of 40 lines) is placed anyway and recorded in
   `render.FINDINGS_LAST` as `overflow`; the geometry gate then fails the build — loudly, never silently.
5. Font search steps INSIDE a tier and never below its floor (body 14, table 13); a page that only fits below the
   floor is split, never shrunk (P5).

`render.FINDINGS_LAST` (also printed to stderr as `pptx-explainer WARN {...}`) holds `orphan` (estimated last line
<= 8 chars), `fit`, `title-wrap`, `overflow` findings of the last render. They are WARN output, not gates: where a line
breaks is known only to PowerPoint.

## Provenance

Upstream asset: `<projects>/AssetVault/assets/pattern-template/python/pptx-deck-builder/` (README pitfall table 1-17 +
layout layer P1-P5). `vendor/` holds BYTE-IDENTICAL copies, never edited here (`deck_layout` imports `deck_builder`
by module name; `render.py` puts `vendor/` on `sys.path` and refuses to run if either module loads from elsewhere).
Pulled 2026-10-09; the test `test_vendored_files_match_recorded_sha_and_asset` compares these shas with the files
and with the asset.

Shas are of the LF-normalised bytes (`~/.claude` pins `*.py` to LF and eol-sync rewrites working-tree endings
after a commit, which is not an edit). The CRLF copies as pulled hashed 93f812ab… / a7c97690….

| file | sha256 (LF-normalised) |
|---|---|
| vendor/deck_builder.py | 35466bfdfda64136fa8002c3bb9825df99291e5ee9aa8b7f67679880ab2a03d1 |
| vendor/deck_layout.py | 63b63311cbfa6b0ea02684f00b3e1d67d8182444932c844f873d7179037d9bba |

A vendored copy is refreshed by copying the asset again, re-recording both shas here, and bumping the version.
Rulings that gain a GENERIC form in this carrier flow back to the asset (office-deck-deliverables "Shared layout code").

## Rules of `rules/office-deck-deliverables.md`

Implemented:

- Class and density declared (above). Per-slide P1 declaration in the notes, notes walked by the text gate.
- P3 flat: rectangles get an explicit fill and `shadow.inherit = False`; connectors get an empty `a:effectLst`.
- P5 tiers as the vendored constants; title and description are separate objects; body floor 14 (table 13, caption 11,
  kicker / page number 11.5) read back from the emitted file by `type_audit`.
- Body line spacing 1.5 and 6 pt between paragraphs (vendored `block`); height estimators multiply the pitch by it.
- CJK typeface (`a:ea` / `a:cs`) and `lang` on every run (vendored `_set_font`); text box side insets zeroed.
- Orphan-wrap handling as far as an estimator can: clause-break soft breaks, box narrowing, then a WARN finding.
- Picture aspect measured, never guessed. Shape names carry the content key (review loop, `pptx-review`).
- Page numbers from a post-pass. Speaker notes are part of the gated text.

NOT implemented (by design or deferred):

- **Visual acceptance** (COM render read page by page) and **line-start check**: manual,
  `python -X utf8 ~/.claude/tools/pptx-line-start/line_start.py <deck>` and a PowerPoint COM PNG export.
  No gate here needs PowerPoint.
- **P3 colour count** (`tools/pptx-presentation-gate/presentation_gate.py`) is not run by the build; a slide with a
  warn and a key callout can carry blue and orange tints together.
- **P4 sample page first**: a process step for the author, not something a carrier can do.
- **pptx-edit-headroom**: the deck is a rebuilt artifact, not an editable one (hand edits are caught by the stamp).
- **Bottom References strip, file:// link gate, per-family term/value gates**: no literature strip (refs are inline
  `〔label〕` + the 出處 slide), no hyperlinks are emitted, no canonical-term set exists for explainer content.
- **Table cell line spacing is 1.25** (vendored `L.table`), below the 1.5 body ruling; callout / quote / card sub-lines
  use 1.15-1.25. Inherited from the asset, not re-ruled here.
- **Producer-side unread-key check**: every schema field is rendered except `meta.audience` (an author-side
  declaration; NO mechanism checks that audience-class text is free of paths / ids / gate counts — that stays a
  reader check) and `refs[].href` (shown as plain text). A new schema field is NOT rendered until this
  file's mapping and `render.py` are extended.
- `lang` is the vendored fixed `zh-TW` (+ `altLang en-US`) whatever `meta.lang` says; harmless for Latin text, wrong
  kinsoku for a non-CJK deck. `meta.lang` only reaches the core properties.

## Gates (`gates.py`, run by `build.py` after the render, before the stamp)

| gate | rules on | fails when |
|---|---|---|
| `type_audit` | vendored `deck_layout.type_audit` on the emitted file, plus an instrument check | any run below its tier floor; a text run with no explicit size; zero runs read (instrument blind) |
| `structure` | slide count against `keywords = sections=<n>`, text, notes | slides < 1 + sections; `[[` in any text frame, table cell or notes; a slide without a notes declaration (`這頁回答`); distinct `第 n 節` kickers != sections; marker missing |
| `geometry` | stored shape geometry | a shape outside the slide or in the page-number band; two content shapes (text / picture / table) overlapping. Stored boxes only: a table that auto-grows in PowerPoint is not seen |

A gate never raises: an exception becomes `(name, False, reason)`. Controls (positive = known violation must fire,
negative = clean golden sample must pass) live in `tests/test_pptx_explainer.py`: 9 pt run, leftover marker (text, table
cell, notes), missing declaration, dropped slides, overlap, off-slide, garbage file; plus a 13-slide long-content deck
that must split, repeat table headers, lose nothing, and still pass every gate.

Run: `python -X utf8 -m unittest discover -s ~/.claude/tools/carriers/pptx-explainer/tests -v`

## Known blockers and limits

- **Stamp (resolved 2026-10-09, before v1 shipped)**: python-pptx caps each core property at 255 characters, and the
  first stamp (one JSON in `comments`, 273 chars) raised `ValueError: exceeded 255 char limit`. `common/stamp.py` now
  splits the stamp: `identifier` = content_sha256, `category` = body_sha256, `comments` = the other fields — full-length
  hashes, no truncation. `test_end_to_end_build_and_stamp` runs (no skip) and `build.py selftest` passes the pptx
  hand-edit and stale controls. The body hash is stable across the core-properties save (checked inside `apply`).
- Estimated heights are deliberately tall (a calibrated bias); PowerPoint may draw a block shorter, never meant to draw it taller.
- Table row heights are stored at ~1.01 of the estimate; a boundary cell that wraps grows into reserved space.
- The vendored estimators know nothing about a hanging indent; the figure card therefore uses a label column and a text
  column instead of a hanging paragraph.

## Version and change log

Version: **1**

Change log
- v1 2026-10-09 — first build: cover, section slides with overflow continuation, takeaways box, glossary / refs /
  colophon slides, all eight block types, speaker-notes declarations, gates `type_audit` / `structure` / `geometry`,
  vendored pptx-deck-builder (shas above).

## Maintenance

Any edit to this folder: bump the registry row `version`, add a change-log line here, and
`python -X utf8 ~/.claude/tools/carriers/build.py selftest` must pass. Also re-run the unit tests above.
review-when: `rules/office-deck-deliverables.md` changes a P-rule or a type tier, or the AssetVault `pptx-deck-builder`
asset gains a measured pitfall fix (the registry row carries the same trigger).
