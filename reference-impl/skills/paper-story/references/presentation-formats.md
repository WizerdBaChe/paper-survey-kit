---
xi: 1
what: paper-story 的兩種練習用簡報產物規格——一頁式＝實驗室既有格式（3–6 圖＋五格表）加一個 Keypoint；多頁式＝保留原設計、第一頁插入 Keypoint、每頁圖＋短文字重點；全詞彙 hover 預覽；html 只供練習與複習，正式簡報以實驗室 pptx 範本改英文（formal-deck.md） (the two practice presentation products: lab one-page format + Keypoint; multi-page deck with a Keypoint page and figure-plus-highlights pages; the formal deck is the lab template)
tags: [skill-reference, paper-story, presentation, onepage, deck, hover-preview]
aliases: [一頁式簡報格式, 十篇一頁, 多頁式簡報, Keypoint 頁, 圖加短文字重點, 五格表, page preview 詞彙]
date: 2026-09-03
status: live
---

# Presentation formats — what `paper-story` renders

User rulings (2026-09-03):

1. **One-page (簡報本檔)**: as many figures as the lab's reference pages (3–6)
   and the same table (Structure / Features / Method / Result / Conclusion),
   plus ONE extra element: the Keypoint. Nothing else is added.
2. **Multi-page**: keep the lab's original design (cover → outline →
   introduction → method → results → conclusion), insert a Keypoint page
   FIRST so the presenter can open with 「為什麼讀它、對我有什麼幫助」 and then
   describe; every page that used to be "figure + oral only" becomes "figure +
   short text highlights". The slide is a 重點提醒, never a thing the
   audience has to think through.
3. Every technical term (中英文都算) gets a Wikipedia page-preview style hover
   card with a short explanation.
4. (later the same day, after the first run passed every gate) The HTML
   products are the USER's practice / learning / quick-review copies — 「能看
   且方便看，但很醜不能用來展示」. The formal deck is the lab's PPTX template
   edited in English (text, pictures, minor changes), made only on explicit
   request, and never by converting the HTML (`formal-deck.md`).

## 0. Two product classes

| | class A 練習・複習稿 | class B 正式簡報 |
|---|---|---|
| files | `paper-explainer.html` (since 2026-10-12; earlier runs `onepage.html`, `talk-deck.html`, `keypoint-onepager.html` — retired, moved by `scripts/consolidate_html.py`). The talk script is a SECTION of this page (口述稿), no longer a file | `lab-deck.pptx` / `lab-onepage.pptx` (script + tile notes in the speaker notes) |
| who | the user, alone | the audience |
| language | zh-TW with inline English | slide text English; notes Chinese |
| made by | `render_story.py`, always | editing the lab template, on request |
| never | shown as the talk | rendered from class A |

**Since 2026-11-03 (user ruling) the talk script lives inside the explainer page** (new section 「口述稿」 right after
逐圖判讀; `render_story.py` no longer writes `talk-script.md`, an existing one is left untouched; S9 reads the section's
text) and the talk-deck is unnecessary: the explainer replaces onepage + talk-deck + keypoint-onepager. The MD records
(`narrative-record.md`, reading record, `<PaperId>_keypoint.md`) stay separate files. `library.py` links the page as
「說明頁」 in the README 檔案 column and the keypoint note, beside 正式pptx.

**Since 2026-10-12 (user ruling) class A's HTML is ONE explainer page** built through
`tools/carriers` (`scripts/story_explainer.py` -> `paper-explainer.explainer.json` -> `html-explainer`;
section map in `SKILL.md` Deliverables 2). Sections 1–2 below describe the retired pages; they still
govern the story.json fields those pages read (the gates S4–S7 run on them in memory), and
`--legacy-html` still writes them.

Both legacy HTML products carried a 「練習・複習用（正式簡報＝實驗室範本英文版）」 tag in
their eyebrow line so the class is visible on the page itself. Sections 1–3
below specify class A; class B is `formal-deck.md`.

## 1. `onepage.html` — 【論文一頁・練習用】 (retired 2026-10-12; `--legacy-html` only)

Layout (16:9, one screen; built on the shared `deck-shell`):

| Zone | Content | Source |
|---|---|---|
| header line | paper title · venue · year · first author et al. | `source` |
| **Keypoint strip** (the one addition) | `KEYPOINT｜` the slogan VERBATIM (`logic.keypoint`; bound roles carry a dotted underline and a hover card 在這篇＝referent), then one short clause 為什麼讀它, then a CLOSED 「展開解讀」 toggle holding `keypoint_description` + the role table (user ruling R3-1, 2026-09-04: hover + toggle keeps the lab layout; the reading is one click away) | `logic.keypoint`, `logic.bindings`, `logic.keypoint_description`, `why_me.why_read` |
| **pages 2–3 (class A only)** | 「Keypoint 解讀」: slogan + the 讀書心得終極詮釋 + role table · 「邏輯鏈」: step / 在這篇 / warrant / qualifier / backing, then fragile + portable | `logic` |
| left ~58 % | figure grid, 3–6 figures (2 columns; 2 or 3 rows), each with a 1-line caption + locator | `onepage.figures[]` (crops from the paper) |
| right ~42 % | the five-field table: Structure / Features / Method / Result / Conclusion, one short cell each (≤ 120 chars) | `onepage.table` |
| footer | References · `G` glossary hint | `source`, `terms` |

The five-field table keeps the lab's vocabulary exactly (the D1 deck's
Structure/Features/Method/Result/Conclusion rows). Its cells are `[author]`
content in the presenter's words; the Keypoint strip is the only place the
reader's own logic appears — with one ruled exception. **The Conclusion cell
keeps the author's ending (mandatory: the presenter must know how the authors
closed) and appends 「深讀判定：」 + the reader's verdict** (user ruling
2026-09-03; all three calibration runs had done it, the ruling made it the
rule). Never mixed into the author's sentence; S4b warns when the marker is
missing. Class B carries the same two parts in English: `Authors: … |
Verdict: …`. The Method cell carries the design data a reader would copy
(the numbers), not a prose flow — the flow is the Features cell's job. The
Result cell carries the flagship AND the typical value (median/mean) whenever
the paper gives both — a flagship alone is the paper's framing, not the
reader's (blind calibration 2026-09-03, run Y did it, run X did not). Page 2 of the file is the glossary (all terms,
jumpable); no 用途說明 page — the user asked for the lab format, not a guide.

**Ten-paper one-page, schema `story@6` (user ruling 2026-11-03; pattern from a labmate's ten-paper deck,
analysed in the origin's reference notes, not shipped).** One page = one paper; the page is a grid of figure TILES plus the table:

- **Tiles.** A tile is one image (`file`) or a panel set (`files[]`) with `caption`, `locator`, `step` (context · series ·
  trend · mechanism · side-evidence), `why` (what the tile adds to the argument), optional `figure_read` and `notes`
  (spoken lines for the speaker notes). Story mode takes **3–4 main tiles — one per ARGUMENT STEP of the paper, not
  one per figure of the paper** — plus **at most one side-evidence tile**; deep mode keeps 3–6 figures. A main tile
  is a figure the argument stands on; a results TABLE is not a tile (its number goes into the Result cell; S4d WARN).
- **Side-evidence rule (user's wording, 2026-11-03): 「重點旁證(非論述重點，但是成立的必要條件之一或可作為論述證據)還是可以加入圖片」.**
  A figure that is not the argument but is one necessary condition of it, or usable as evidence for it, may still be
  a tile. It is declared `step: side-evidence` and MUST carry `necessity` (which condition it establishes or which
  claim it evidences); S1 FAILs without it, S4 FAILs on a second one.
- **Table fields.** `onepage.fields` = `five` (default: Structure / Features / Method / Result / Conclusion) or `four`
  (Features dropped; ruling 2026-11-03 G2 — Features is optional). With `four`, `table.features` is not required.
  Cells are density-capped on the lab one-page: a Result cell keeps its numbers (a range counts once), whole clauses
  are dropped from the slide and moved to the speaker notes, the first clause is always kept; lab_deck gate L12 WARNs
  when a cell still exceeds the density limit.
- **Header.** Title with `(year)` only; the venue is a small badge at the top-left of the slide. The Keypoint strip is
  unchanged.
- **Script.** `onepage.script = {source_line, purpose_line}` is printed in the 口述稿 section and the notes
  (出處 / 目的); each tile's `notes` follow it.

Figures (deep mode and schema ≤ @5): 3–6 by the storyline, in beat order, each declared with `kind`
(`onepage.figures[].kind`, schema @3): `evidence` — the data a claim rests on
(plots, spectra, distributions, micrographs of the made thing, a results table),
one per claim; `schematic` — the paper's OWN process flow or device drawing, the
picture behind the Structure / Method cells (at most one or two); `motivation`
— overview or application-scenario figures, which go to the deck ONLY: the
one-page must read as evidence without the talk. Rulings 2026-09-03: Gb9
(evidence only) narrowed by OQ-1 to motivation-deck-only, because both blind
readers kept the process flow and disagreed only on the six-panel motivation
figure, and every accepted run carried a process flow. S4c warns on a
motivation figure — keep it only with the reason written in the record. Crop
with `crop.py`; a figure that must be borrowed from a cited paper is tagged
`[borrowed]` in its caption.

## 2. `talk-deck.html` — 【多頁簡報・練習用】 (retired 2026-10-12; `--legacy-html` only)

Page order = `deck.pages` order. Round 5 (user review 2026-09-14): the GaN skeleton leads — Outlines (Cover), then the
front block (Source · Keypoint · KeyLogic · Methods · Verdict), then the paper (Introduction / timeline → figures →
Fabrication → Results), Storyline, Conclusion, Future work, Search, References; the lab-deck order and its layouts are in
`formal-deck.md` §2a. The rows below describe the page kinds (numbers = the round-4 order):

| # | Page | Content | Notes (speaker) |
|---|---|---|---|
| 1 | **Keypoint** | 為什麼讀它 · 對我有什麼幫助 · KEYPOINT（the slogan, roles decorated）+ one line of 角色＝指涉 + a closed 展開解讀 holding `keypoint_description` · 主軸：切入點＋為什麼是這個切入點 | `talk.opening` + `why_me` |
| 2 (@5) | **Verdict** — the advisor's four opening questions (ruling 2026-09-14: 為什麼要讀、方法到底是什麼、有沒有達到、怎麼判讀) | Q1 它在解什麼 (`brief.problem`) · Q2 怎麼做、跟別人哪裡不同 (`brief.approach`, `brief.differs`) · methods table (`brief.methods[]`: name · kind fabrication／model／simulation／measurement／analysis · the question it answers) · verdict table 目標／怎麼判讀／結果／有沒有達到 (`brief.verdicts[]`, status achieved／partly／simulated-only／not-shown) | names EVERY method verbatim, then walks the verdict table row by row; says out loud which goals are only simulated |
| 3 | Cover / Outline | title, authors, venue, year; 「本次報告分為 N 個部分」. Its highlights are either venue/authors (≤ 2) or the N outline parts themselves (up to 6 — the only page whose highlights may exceed 3; round 2 run Z hit the cap with a five-part outline) — never a different partition (S9 warns when ≥ 3 bullets ≠ N) | `talk.outline` |
| 4… | the paper's own sections in order: Introduction → Method(s) → Results (one figure per page) → Discussion (if the paper has one) → Conclusion | each page: ONE figure (or none for pure-text pages) + ≤ 3 highlights, each ≤ 48 CJK-equivalent chars, in 重點提醒 register (a noun phrase with the number, not a sentence to think through) | `deck.pages[].notes` = what is SAID on this page |
| (optional, before last) | 沒做／沒對照到什麼 | one page of the paper's untested claims and missing controls, section `Discussion`, ≤ 3 highlights — allowed because it is the presenter's own 重點提醒, not a section the paper has (blind calibration 2026-09-03, run Y) | `drift` |
| (@5, before Conclusion) | **Storyline** — how the paper told its research story | 一句話的故事 (`talk.story_arc.spine`, And–But–Therefore) + craft table: beat · what the authors do · why it works on the reader (`story_arc.craft[]`, each with a locator); the weakest link is one of the rows | the spine, then the craft moves a reader can copy, then the weak link |
| last | 對我的幫助 | 這篇幫我建立的研究依據 · 對後續量測／設計的幫助 · 下一步 | `talk.closing`. Round 5: the lab deck has no such page — a **Future work** page (section FutureWork: the paper's own next steps beside my extensions) takes its place, and the slogan is spoken on a front page (S20) |

**Page fields since @5 (round 4, 2026-09-14)** — the notes must tell a story, not report the slide
(user finding: the round-3 notes were 「生硬」, pure data and figure reporting with no 先後連接):

- every page except Keypoint, Cover, Source and References carries `asks` (the question this page answers), `bridge`
  (its first spoken clause, verbatim inside `notes` — it picks up the previous page's hand-off
  question) and `takeaway` (≤ 60 CJK-eq, the one sentence the audience carries out; the formal
  deck prints it as the blue line under the title). `beat` names the storyline beat;
- a page with a figure carries `figure_read = {look, see, against, means}` — what the axes and
  panels are, what is visible, what it is compared with (required on Results), and so what; the
  notes POINT at the figure (這張、橫軸、左邊的 (a)…). An Introduction / Method / Results page
  without a figure states `no_figure` with a reason — figures are the first priority (advisor);
- a page's notes follow the presenter's voice (`talk-conventions.md` §8, round 7, every deck): open by
  placing the page in the structure (the bridge), mechanism in a plain image before the term, the
  obvious question answered inside, a figure walked where it could be misread, every number with its
  price, one caveat only where it changes how the number is used; they carry at least two distinct
  connectives, introduce a premise before the page that uses it, and never read a highlight aloud;
- `talk.opening` is the concrete story (why read · the problem · the move · did it work); the slogan is
  spoken AT THE CLOSE — on the Storyline page, where the talk deck also prints the slogan box beside the
  story line (round 7 user ruling 2026-09-21, reversing round 5's "up front").

Rules that make a page a 重點提醒:

- highlights are the sentence the presenter would put on the whiteboard, not
  the sentence they would say; the said sentence goes to notes;
- a Results page carries the figure's ONE number and what it shows, nothing
  about method;
- the Method pages carry the design data (the numbers a reader would copy)
  as highlights — the user's purpose is to learn to write a paper, so Methods
  pages are not skipped or compressed to one page;
- no page carries a paragraph; if a point needs a paragraph, it goes to the
  notes and the record.

Page count ≈ minutes × 1.5 (lab rule) when a slot is given. `deck.minutes` is optional since round 5
(user: 「時段沒有限制，只要完整都可以」) — without it completeness wins and S17 skips the spoken estimate.

**Time layers and backup pages — practice products only** (researcher.tw B-12 / B-13,
user ruling R5 2026-09-14). A page may declare `layer`: **A** is never cut (the Keypoint
page, the main Results page), **B** is compressed first (speak only its first
highlight), **C** is dropped first. When one storyline has to fit a shorter slot, the
cut follows the layers, not the mood of the moment; the explainer's 口述稿 section prints the cut plan
(「時間不夠時」) with page counts at minutes × 1.5. An `if_asked[]` note may declare
`kind` — `clarify` / `challenge` / `extend` — and a challenge carries
`challenge = {admit, reason, settle}`. The first two challenges become 備份頁 after the
last page of the legacy `talk-deck.html` (written only with `--legacy-html`), flipped to only when asked. The formal lab PPTX
(`formal-deck.md`) is unchanged: no layers on its pages, no backup pages.

## 3. Term previews (all products)

`terms[]` must cover every technical term that appears on any rendered page,
in the form it appears (Chinese or English), with a Wikipedia-style gloss:
one or two sentences, what it is and why it matters here. The shell decorates
every registry key found in body text (Chinese keys work; headings are not
decorated by design) and shows a 350 ms hover card; `G` opens the full
glossary. The renderer warns (S6) when a term never appears in the rendered
text or when a `full` run has fewer than 12 terms — a paper page with only a
handful of abbreviations glossed is the defect the user reported.

## 4. Gates (renderer, severity by consumer)

| Gate | Checks | Severity |
|---|---|---|
| S1 schema | `story.json` valid | FAIL |
| S2 why-completeness | every `axis.*.why*`, every `storyline[].why`, every `logic.chain[].warrant` non-empty | FAIL (the user's core requirement; determinable) |
| S3 locators | axis items, beats, drift rows, chain backing carry a locator or `[inferred]` | FAIL |
| S4 one-page shape | 3–6 figures with existing files; five table cells present | FAIL; cell > 120 chars WARN; on schema ≤ @3 keypoint_box > 80 or a box repeating the KEYPOINT label WARN; on @4 a keypoint_box still present WARN (the strip prints `logic.keypoint` verbatim — the box invited a second compression, 2026-09-04) |
| S4 (story@6) | story mode: 3–4 main tiles + ≤ 1 side-evidence tile, every file of every tile present, side-evidence carries `necessity`, `fields: four` needs no Features cell (user ruling 2026-11-03); on @5 and deep mode the old 3–6 rule stays | FAIL |
| S4d tile shape | @6 only: a results-TABLE tile (Table token without a Fig token in caption/locator, or `table` in the file name) or a tile without `step`; SKIP on @5 and deep mode (2026-11-03) | WARN |
| S15 keypoint bindings | schema @4: ≥ 3 `logic.bindings[]`, every role a verbatim substring of the slogan, every clause (split on ；) bound, each with a locator; older runs "undeclared" | FAIL (determinable; whether the bindings are the RIGHT ones is the readback test in evals) / WARN undeclared |
| S16 keypoint shape | slogan ≤ 90 CJK-eq; `keypoint_description` present, 200–700 CJK-eq, not the slogan restated | WARN (the reader judges whether it is the 讀書心得終極詮釋) |
| S17 time layers + question kinds | once any page declares `layer`, every page does; the Keypoint page and a Results page are A; once any `if_asked[]` declares `kind`, every one does; every challenge carries `admit` / `reason` / `settle`; once layered, the spoken estimate (opening + notes in CJK-eq ÷ 250 per minute — assumed until a rehearsal is timed) stays within `deck.minutes` × 1.2, printed per cut beside the page rule (round 4: the page rule passed a 21-minute script as 11); neither declared → SKIP (older runs) | WARN (an LLM writes it, the presenter reads it; whether a C page is truly expendable stays the reader's call) |
| S18 brief | schema @5: a deep run carries `brief` and `talk.story_arc` (else S1 FAIL); every method has `answers` (not its own name) and a locator; every verdict has `judged_by`, `result`, a locator; `problem` does not restate `why_me.why_read`; every method name is spoken in the opening or the front pages (Keypoint / Verdict / Cover, + Source / KeyLogic / Methods since round 5); a Verdict page sits among the front pages; older runs SKIP | WARN (an LLM writes it, the presenter reads it); promotion trigger in the `render_story.py` docstring |
| S19 figure reading | every figure page carries `figure_read` look / see / means (+ `against` on Results) and notes with spoken deixis; an Introduction / Method / Results page without a figure states `no_figure`; older runs undeclared → SKIP | WARN |
| S20 narrative flow | every page but Keypoint / Cover / Source / References carries `asks` / `bridge` / `takeaway`, the bridge verbatim inside the notes; no highlight (≥ 10 CJK-eq) recited in the notes; ≥ 2 distinct connectives per page; takeaway ≤ 60 CJK-eq; the slogan is spoken at the close — a logic-chain / storyline / conclusion page after the paper is walked, or `talk.closing` (round 7 flip, 2026-09-21; selftest `s20-slogan-front-only` / `s20-slogan-in-closing-ok`); `story_arc` has a spine, ≥ 4 craft steps each with `why_it_works`, and a Storyline page exists; older runs undeclared → SKIP | WARN (a connective count is a proxy for 先後連接, not proof — the reader pass decides) |
| S4b Conclusion cell | author's ending + 「深讀判定：」 marker present | WARN |
| S4c one-page figure kinds | every `onepage.figures[].kind` declared; `motivation` figures belong to the deck (evidence and the paper's own schematic may stay — OQ-1); schema @3, older runs report "undeclared" | WARN |
| S10 quotes | every drift row has `quote` (schema ≥ @2); every quote found verbatim in `source/paper.txt` (folded: case, dashes incl. U+2212, quotes, whitespace) | FAIL (thin text layer → WARN; `quote_source: page-image` → WARN, the dispatcher verifies on the page image) |
| S11 coverage | every `structure.json` unit cited by a locator or in `coverage.skipped` with a why | WARN → promotion trigger: a skipped unit later cited in a talk = FAIL |
| S12 anomalies | every probe anomaly addressed in drift / storyline / skipped | WARN |
| S13 drift checklist | every kind of the `narrative-axis.md` §4 tell list is found in a `drift[].kind` or declared `none` in `coverage.drift_checklist` (schema @3; older runs report "not declared"; `checklist_provenance: backfilled` runs say so) | WARN → promotion trigger: a none whose observation a second reader finds under no kind of this reading = FAIL |
| S14 stray script | no Cyrillic / Hangul / Thai / Arabic / Hebrew / Devanagari character in any text field (Greek allowed: μm, λ/4, Ω·cm) — LLM-typed CJK slips (製程схема, run S3) | WARN |
| S5 deck shape | ≥ 5 pages; a Keypoint page within the first three pages (round 5: Outlines and the source page may precede it; selftest `s5-keypoint-after-cover` PASS / `s5-keypoint-not-first` FAIL); ≤ 3 highlights per page; highlight ≤ 48 CJK-eq; SKIP when story.json has no `deck` (`story` mode) | FAIL on structure, WARN on length |
| S6 terms | every term appears in the rendered page text (glossary page excluded); `deep`/`story` run has ≥ 12 terms | WARN |
| S7 fit | Playwright at 1707×830 and 1280×720 on both HTML products; overflow FAIL, scale < 0.85 WARN; instrument missing → WARN and forward. A one-page with 5–6 figures scales to ≈ 0.80 at 1280×720 by construction (three fixed figure rows) — an expected WARN, PASS at 1707 (the user's screen at 150 %); do not drop figures to silence it. Since @4 the strip may wrap (a slogan > ~70 CJK-eq takes two lines): with SIX figures that pushed Hong 2019 to 0.83 at 1707 — take five figures and send the sixth to the deck (round 3, 2026-09-04) | FAIL / WARN |
| S8 shell drift | sha vs AssetVault | WARN |
| S9 talk conventions | opening has the lab formula; outline sentence; closing basis + help, read from the explainer page's 口述稿 section (since 2026-11-03 there is no `talk-script.md`); SKIP when story.json has no `talk` (`story` mode) | WARN |
| P0 / P1 pptx (only with `--pptx-from-story`, explicit request) | P0: this pptx is the HTML layout, not the formal deck; P1: keypoint verbatim in the built pptx, no forbidden variants | INFO / FAIL |

Deliverables are written BEFORE gates; the gate file is `story-gates.txt`.

## 5. The formal deck (class B)

Not rendered here. `formal-deck.md` holds the template inventory (4:3, Times
New Roman, English slides, Chinese notes, the two structures), the
`story.json` → slide mapping, the edit procedure and the acceptance (COM render
+ the office-deck rules). A run that only produced class A says so in its
delivery; the formal deck is a separate, explicitly requested step.
