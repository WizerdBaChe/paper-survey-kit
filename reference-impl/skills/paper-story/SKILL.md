---
name: paper-story
description: >-
  Turn a paper into a presentation, reconstructing its narrative with a why at every
  step: 主軸, 故事線, 邏輯抽取 (the key point as reusable logic), then the
  lab's one-page and multi-page decks and a talk script. Trigger on 「這篇要報」「論文賞析簡報」「一頁式／十篇一頁」
  「多頁簡報」「主軸／故事線」「key point」「為什麼讀這篇」「正式簡報／英文版」. NOT the
  evidence audit (→ paper-distill), finding papers (→ literature-search-extract), own study
  design (→ scientific-research-guide), posts (→ post-brief).
---

# paper-story — 主軸、故事線、邏輯抽取，然後才是簡報

## What this is (and why it is a separate skill)

Reading a paper for its EVIDENCE (does the claim hold?) and reading it for its
CONSTRUCTION (how was this research built, and why that way?) produce different
objects. `paper-distill` owns the first (IMRaD skeleton, claim audit, figure cards).
This skill owns the second: the paper's 主軸 with the reason it was chosen, the
故事線 as the authors told it with a why on every beat, the 邏輯抽取 — the key point
as an abstracted, transferable logic whose every link carries a warrant — and the
presentation products the lab actually uses. The two share one run folder and one
toolset and call each other by situation (`references/bridge.md`); neither is bound
to the other.

The user's standard for this skill (2026-09-03): science reading needs the whys —
「為什麼是這個切入點」「為什麼選這個方法」「預期怎麼評估」「為什麼這樣呈現」. A card with
only how and what is rejected by the gates (S2), not by taste.

## Intake

- **mode** — `deep` (the next single-paper talk: all nodes, the multi-page deck) ·
  `story` (one page per paper for the ten-paper format: nodes N0–N3 + the one-page
  product) · `triage` (axis card only, to decide whether the paper is worth a talk).
- **presenter / minutes / project** — the deck's page count (≈ minutes × 1.5 when a slot is given; round 5: no slot → completeness wins, `deck.minutes` optional) and the
  「對我有什麼幫助」 line need them; ask once if absent. `why_me.why_read` names BOTH
  subjects with labels — 「我的專案 X 要…；這篇（Y 上的 Z）示範…」 — and the
  `keypoint_description` opens with the paper's own platform: in the round-3 readback
  (2026-09-04) a blind reader took the user's project (the presenter's own project) for the paper's
  substrate when the line listed them side by side.
- **distill run?** — if `paper-distill` already ran on this paper, name its run id in
  `run.distill_run`; the story cites its verdicts in `drift` and reuses its figure cards
  and terms. If not, the story reads the paper itself and marks unaudited claims.
- **library check (round 2, 2026-09-03)** — `library.py find <term>`: if the index already
  holds a story run for this paper, a `story`-mode page REUSES its key point and chain
  (`logic.reused_from` = that run id) and re-authors only the one-page material — the
  ten-paper page must agree with the single-paper talk. Re-deriving is for a new paper or
  for a calibration run (then the brief says so and the folders are kept apart).
- **home** — the vault library `<PAPER_HOME>` (env
  `PAPER_DISTILL_HOME`); read `<NOTES_VAULT>\AGENTS.md` once per session; every
  `.md` written there carries the vault card (`kind: literature`).

## Nodes

| Node | Nature | Question | Writes | Read |
|---|---|---|---|---|
| N0 取用 | mechanical | ingest, metadata, pages | `source` | `paper-distill/scripts/ingest.py` (shared) |
| N1 深讀 | evidence (optional, separate skill) | does it hold | `cards.json` | `paper-distill` |
| N2 敘事重建 | reconstruction with whys, anchored in the paper's words | how was it built, why that way, where does the telling drift (which of the ten tells), which units did I not use and why | `why_me`, `axis`, `storyline`, `drift` (+ `quote`, `kind`), `coverage` (`skipped`, `drift_checklist`), `brief` (Q1 problem · Q2 approach／differs · every method · Q3 verdicts, @5) | `narrative-axis.md`, `source/structure.json` |
| N3 邏輯抽取 | abstraction, then binding | what reusable logic did I learn (slogan), what each role IS in this paper (bindings, in_this_paper), how I would explain it to someone who has not read it (keypoint_description), why does each link hold, where is it fragile, where can I reuse it | `logic` | `logic-extraction.md` |
| N4 呈現 | rendering | the lab one-page + Keypoint; the multi-page deck; the talk in the lab's voice; every term glossed | `onepage`, `deck`, `talk`, `terms` → files | `presentation-formats.md`, `talk-conventions.md` |
| N5 歸檔 | mechanical | library, vault lint | index | `paper-distill/scripts/library.py` |
| N6 正式簡報 | template editing — explicit request only (「做正式簡報」「英文版」「用範本」) | what goes on the lab's slides, in English | `lab-deck.pptx` / `lab-onepage.pptx` | `formal-deck.md` |

Order inside N2: read backwards (conclusion → abstract → figures → intro → methods →
body), write beats ⑥ ② ① first, then ③ ④ ⑤, then the axis card, then drift. N3 only
after the axis exists — extraction before the axis produced summaries twice.

## Commands

```powershell
cd $HOME\.claude\skills\paper-story
python ..\paper-distill\scripts\ingest.py <paper.pdf> --slug <slug> --first-author <Name> [--year YYYY] [--presenter NAME]   # shared ingest; omit --year to let it guess
python ..\paper-distill\scripts\probe.py --run <run_dir> --print                                              # source/structure.json: units to cover + anomalies to classify (S11/S12 read it)
python ..\paper-distill\scripts\crop.py --run <run_dir> --caption "Fig. 3" --out figures/S1.png               # one crop per one-page figure (3–6) and per deck page; the figure only (caption excluded), exit 3 = ink on the crop edge
python scripts\render_story.py --run <run_dir> --check-shell --presenter NAME                                 # paper-explainer.html (練習・複習用說明頁 incl. the 口述稿 section, via story_explainer.py -> tools/carriers html-explainer) + story-gates.txt; no talk-script.md since 2026-11-03
python scripts\story_explainer.py --run <run_dir>                                                              # the explainer page alone: story.json + cards.json -> paper-explainer.explainer.json -> build + check
python scripts\verify_story.py <run_dir>                                                                      # run by someone other than the author
# formal deck (N6, explicit request only): scripts\lab_deck.py builds from the blank bases in <PAPER_HOME>\_templates\
# and is edited per references\formal-deck.md (English slide text, figures swapped, minor edits) — never --pptx-from-story for a talk
python ..\paper-distill\scripts\library.py register <run_dir>;  python <NOTES_VAULT>\tools\kv-lint.py           # also rebuilds README, KEYPOINTS.md and <PaperId>_keypoint.md (2026-09-04)
# library layout (naming over routing, 2026-09-04): <home>/<FirstAuthor><Year>_<slug>/ = the ONE accepted run per paper;
# comparison / calibration copies go to <home>/_calibration/<PaperId>/<label>/ (register --kind calibration --label <what-it-is>), never as siblings
python scripts\render_story.py --selftest                                                                    # two-sided gate calibration after editing the renderer
python scripts\consolidate_html.py --home <PaperSurvey>                                                      # dry-run: which runs hold retired onepage / talk-deck / keypoint-onepager HTML; --apply builds the explainer and MOVES them to <run>\archive\retired-html-20261103\ (never deletes, never enters junctions)
```

`story.json` (`paper-story/story@6` for new `story`-mode runs; @5 stays valid and keeps its old gate behaviour; @6 adds `onepage.fields`, `onepage.script` and figure tiles, user ruling 2026-11-03) is authored by the model from N2/N3 (Write tool; for a large nested-CJK
document a local serializer script is fine — the content is still authored field by
field, never generated from a template; helper scripts live in the session scratchpad,
only deliverables go in the run folder); the `narrative-record.md` from
`assets/narrative-record-template.md`; the renderer builds everything else. A
`talk-script.md` already in the run folder (an earlier pipeline version; none is written since 2026-11-03) is left untouched.

## Non-negotiables

- **A why on every step.** `axis.*.why`, `storyline[].why`, `logic.chain[].warrant` are
  required and non-empty (S2 FAIL). A why that restates the what is empty; a why names
  the constraint or belief that made the choice rational. Tag each `[author]` /
  `[inferred]` / `[assumed]`; a paper that gives no why is recorded as such in `drift`.
  `axis.method_choice.alternatives` names the rejected alternatives PER STEP of the
  method (mask / etch / removal / polish…), never one pooled list — two readers of one
  paper each named a different step's alternative (calibration 2026-09-03).
- **The key point is abstracted logic**, not a summary: no material names, no numbers,
  construction verbs; the tests in `logic-extraction.md` (rule-vs-event, binding,
  not-over-abstract, abstraction, why, reuse). Rule-vs-event (user, 2026-09-03): replace
  every noun by its role — a sentence that still instructs a builder is a rule; one that
  needs the paper's nouns (光罩、產物、平台) to mean anything is an event description and is
  rejected. **Two parts since 2026-09-04 (user finding: the slogan alone was unreadable):**
  `logic.keypoint` is the SLOGAN (≤ 90 CJK-eq, roles carry their qualifiers — Test 0c) and
  `logic.keypoint_description` is the 讀書心得終極詮釋 (200–700 CJK-eq, narrative, concrete
  nouns beside each abstract move); `logic.bindings[]` binds every role of the slogan to the
  paper's referent (S15 FAIL when a clause is unbound) and each `chain[].in_this_paper`
  carries the concrete event sentence (S2). The strip prints the slogan VERBATIM — no
  `keypoint_box`, no re-compression; roles hover, 「展開解讀」 unfolds the reading; the
  one-page gains 解讀 + 邏輯鏈 pages (class A only; class B keeps the slogan).
- **Locator or `[inferred]`** on every axis item, beat, drift row and chain backing.
- **The one-page (`story` mode, schema @6) is a grid of argument-step tiles** (user ruling 2026-11-03, from the
  senior's 10-in-1 deck): 3–4 main tiles, ONE PER ARGUMENT STEP (`step`: context · series · trend · mechanism), each
  with `why`, never one per figure of the paper; a results table is not a tile (S4d WARN). A key side-evidence figure
  (user's wording: 「重點旁證(非論述重點，但是成立的必要條件之一或可作為論述證據)還是可以加入圖片」) may be one extra tile,
  at most one, `step: side-evidence` with `necessity` (S1/S4 FAIL without or beyond). The table is five fields by
  default; `onepage.fields: four` drops Features (optional by ruling 2026-11-03). The lab one-page cuts each cell to its
  numbers and first clause, moves the rest and the script (出處／目的 + tile notes) to the speaker notes, and prints
  the venue as a badge (`references/presentation-formats.md` §1, `formal-deck.md` §2 ten-papers, `talk-conventions.md` §9).
- **The deep-mode one-page is the lab's format** (3–6 figures + the five-field table) plus ONE
  Keypoint strip; nothing else is added or removed (schema @5 and older behave this way in both modes). Its figures declare `kind`
  (`onepage.figures[].kind`): `evidence` figures and the paper's OWN process／structure
  `schematic` may stay; `motivation` (overview／application) figures go to the deck only
  — user rulings 2026-09-03 Gb9 + OQ-1; S4c warns. The Result cell carries the flagship
  AND the typical value when the paper gives both; the Method cell carries design data.
- **The deck keeps the lab's order** with the Keypoint page in front; every page is a
  重點提醒: ≤ 3 highlights, each ≤ 48 CJK-equivalent chars, the spoken sentence goes to
  notes. Method pages carry design data; Results pages carry one figure and its number.
  Cover bullets ≥ 3 are the outline parts themselves (S9 warns when they differ from
  「分為 N 個部分」); an optional 沒做／沒對照到什麼 page (section Discussion, from
  `drift`) may precede the closing page. Pages may declare `layer` A/B/C and if-asked
  notes `kind` (+ `challenge` = admit／reason／settle): the talk script prints the cut
  plan, the practice deck adds ≤ 2 backup pages, the lab PPTX is untouched; S17 warns.
- **Up front, figures first, told as a story** (advisor ruling relayed 2026-09-14, schema @5).
  The talk opens by saying why the paper is worth reading, what ALL its methods are, whether it
  reached its goals and how that was judged: `brief` (`narrative-axis.md` §5) feeds a Verdict
  page in the front block (round 5: Outlines → source → Key points → key-point logic → methods → verdict). Every figure is walked (`figure_read` look／see／against／
  means, notes pointing at it); a content page without a figure says why. Notes are a told
  story, not a report — each page's `bridge` picks up the last page's question, the `takeaway`
  is the one line to carry out, premises come before use, highlights are never read aloud, and
  the opening tells the concrete story while the slogan is shown and spoken UP FRONT on the
  key-point logic page (user ruling round 5, 2026-09-14, overturning round 4's slogan-at-the-closing;
  `talk-conventions.md` §7). `talk.story_arc` + a Storyline page say how the paper got its
  story believed. S18–S20 warn. **Round 7 (user final + ruling 2026-09-21) changes this for EVERY deck**: the logic chain
  closes the talk — the slogan is spoken, and in the talk deck printed, on the Storyline page after the paper is walked (S20
  flipped) — and every deck's notes follow the presenter's voice (`talk-conventions.md` §8) with the figure–text rules of
  `formal-deck.md` §2c. Page order and method pages are per paper type: the review profile (front block Title → Outlines →
  Key points, verdict inside the Key points rows) is R7-1; a device / design paper keeps the GaN skeleton until its own final
  deck is ruled.
- **Talk in the lab's voice** (`talk-conventions.md`): the opening formula, 「分為 N 個
  部分」, bracketed if-asked notes, the closing 研究依據／對後續的幫助.
- **Every technical term on any page is in `terms[]`** with a Wikipedia-preview gloss
  (Chinese or English, as it appears); the shell decorates them; S6 warns on gaps.
- **Vault contract** for every `.md` in the run folder; `kv-lint.py` 0 FAIL.
- **看錯／漏看 are the same severity as 亂掰** (user ruling 2026-09-03). Four instruments,
  all determinable: (1) every drift row — and, when they exist, the entry point, the central
  claim and beats ② ⑥ — carries the paper's own words in `quote` (≤ ~25 words); S10 finds
  each quote verbatim in `source/paper.txt` (FAIL when absent; thin text layer → WARN and
  the page image decides). (2) `source/structure.json` (`paper-distill/scripts/probe.py`)
  lists every section, subsection, figure and table; S11 warns for any unit no locator
  cites unless `coverage.skipped[]` names it with a why. (3) The probe's `anomalies[]`
  (duplicate section numbers, uncited figures, abstract numbers absent from the body) are
  INPUTS: each lands in a drift row, a storyline beat (⑤′ for a grafted second result) or
  `coverage.skipped`; S12 warns for each one left unclassified. (4) The drift tell list
  (`narrative-axis.md` §4, ten kinds) is walked AND declared: every drift row carries
  `kind`, `coverage.drift_checklist` marks each kind found／none; S13 warns for a kind
  neither found nor declared none — in the blind test two readers of one paper each
  walked a different subset; a checklist not declared is a checklist not walked (round 2:
  the one run that declared the walk while reading found the union of both). Promotion
  trigger: a `none` whose observation a second reader finds under no kind of this reading
  → FAIL; the same observation under another kind is a recorded disagreement. A quote the
  text layer lacks carries `quote_source: "page-image"` (S10 WARN, verified on the page).
  A story that passes S2 but fails S10 is not a reading.
- **The Conclusion cell keeps the author's ending and appends 「深讀判定：」 + the reader's
  verdict** (user ruling 2026-09-03: the presenter must know how the authors closed);
  S4b warns when the marker is missing. Class B: `Authors: … | Verdict: …`.
- **Two product classes, never converted into each other** (user ruling 2026-09-03).
  `paper-explainer.html` (since 2026-10-12; before it `onepage.html` / `talk-deck.html`) is the
  user's 練習・學習・快速複習 copy — readable, not presentable. The formal deck is the lab's PPTX template with its text replaced in
  ENGLISH, figures swapped and minor edits (`formal-deck.md`), built only when the user
  asks for the real talk. `--pptx-from-story` (the HTML layout as pptx) runs only on an
  explicit request and is never the talk deck.
- **Gate ids the delivery quotes** (`presentation-formats.md` §4; severity by consumer):
  S1 schema · S2 whys · S3 locators · S4 one-page shape · S4b Conclusion marker · S4c
  figure kinds · S5 deck shape · S6 terms · S7 measured fit (5–6 figures ≈ 0.80 at
  1280 × 720 is the expected WARN — never drop a figure for it) · S7b measured fill
  (width property 2026-09-04: `~/.claude/tools/page-fill-gate`, class deck — a text block
  capped narrower than its slide is the WARN to fix, never a reason to widen the shell's
  fit block) · S8 shell · S9 talk
  formula + outline N = enumerated parts = Cover bullets · S10 quotes · S11 coverage ·
  S12 anomalies · S13 drift checklist · S14 stray script · S15 keypoint bindings · S16
  keypoint shape · S17 time layers + question kinds · S18 brief · S19 figure reading · S20 narrative flow. `verify_story.py` V1–V23 runs outside the author's session; V11–V17,
  V19–V23 re-run the source-anchored, keypoint and round-4 gates.

## Deliverables (run folder, named by purpose)

Class A — for the user (練習・學習・快速複習; readable, not presentable):

1. `narrative-record.md` — 【敘事紀錄】 why-me, logic first, axis, storyline, drift,
   one-page material, deck plan, talk points, glossary, process log.
2. `paper-explainer.html` — 【論文說明頁・練習用】 since 2026-10-12 (user ruling 「html改用我們新版的說明頁
   格式」) the ONE class-A page, replacing `onepage.html` + `talk-deck.html`. A build output
   (`rules/explainer-deliverables.md`): `scripts/story_explainer.py` maps story.json + cards.json
   into `paper-explainer.explainer.json` (schema `explainer/1`, words only from the two contracts) and
   `tools/carriers/build.py` builds it with the `html-explainer` carrier and stamps it. Sections:
   Keypoint (slogan + 解讀 + bindings + why-me) → 一眼看懂 (problem/approach, five-field table,
   every method, verdicts) → 主軸 → 故事線 → 逐圖判讀 (each deck figure + look/see/against/means
   + takeaway) → 口述稿 → 深讀審計 (claims + drift) → 邏輯鏈 (warrants, fragile, portable) →
   延伸與找資料; glossary from `terms[]` (first use marked), refs from `en.references`. Since 2026-11-03
   (user ruling 「只留「口述稿」section」) 口述稿 is the page's ONLY talk section: it sits right after 逐圖判讀 and is
   built from the blocks the retired `talk-script.md` held, plus the outline, the if-asked memos and the closing (all in
   it, so the older 「上台要點」 section is gone). A `story`-mode run builds 逐圖判讀 from its tiles and prints 出處／目的 + tile
   notes there. The talk-deck is unnecessary. Never hand-edit it: change story.json and rerun. `--legacy-html`
   still writes the two retired pages; older runs are brought onto this page by `scripts/consolidate_html.py`
   (dry-run first, `--apply` moves the retired HTML to `archive/retired-html-20261103/`, never deletes).
3. (retired 2026-10-12) `onepage.html` / `talk-deck.html` — still built in memory so S6 can read
   their text; S7 / S7b measure them only under `--legacy-html` (the carrier's own gates
   `fill_gate` / `main_fill` / `structure` measure the explainer page, reported as gate `EX`).
4. (retired 2026-11-03, user ruling) `talk-script.md` — the 【口述稿】 is now the explainer page's 口述稿 section
   (in the lab's voice; ends with 結尾 in deep mode). The renderer writes no such file and leaves an existing
   one untouched; S9 reads the section. The MD records (`narrative-record.md`, reading record, `<PaperId>_keypoint.md`) stay separate files.
5. `story.json` — the contract; `story-gates.txt` — pasted into the delivery.

`story` mode (one page per paper) produces 1, 2 and 5 only: no `deck`, no `talk` in
story.json (S5 / S9 report SKIP; the record's deck and talk sections say 「story 模式不產出」). Its explainer's
口述稿 section is the one-page script (出處／目的 + tile notes); the formal `lab-onepage.pptx` carries the same
script in its speaker notes (`lab_deck.py --format onepage`, user ruling 2026-11-03).

Class B — for the real talk (explicit request 「做正式簡報」「英文版」「用範本」):

6. `lab-deck.pptx` (single-paper talk) / `lab-onepage.pptx` (ten-papers format) — the
   lab template edited: English slide text from `deck.pages` / `onepage`, figures from
   `figures/`, speaker notes (Chinese) from `deck.pages[].notes` (the same text as the explainer's 口述稿 section); since round 5 the GaN skeleton
   (Outlines → Key points → Introduction → Fabrication → Results → Conclusion → Future work) with
   additions — source page, key-point logic, methods, verdict, storyline, keyword search,
   References — as native editable diagrams, body ≥ 14 pt; since round 6 (2026-09-15) the hand-tuning rules
   R6-1…R6-14 in `references/formal-deck.md` §2b govern the finished deck: one font size per level; three-statement
   figure pages with no "Fig. x:" or "→" markers; soft line breaks for sub-items; labelled crops; figures may cross the
   frame for legibility; tables and visuals over text; APA references; no Source strips. `lab_deck.py` implements the
   determinable ones (size levels, figure-page statements with soft breaks, no strips, 12 pt References, an overwrite
   guard for hand-tuned decks; §4 round 6); gates L1–L11 (`lab_deck.py --selftest` calibrates L3, L7–L11 and the guard;
   L10 = PowerPoint's own text layout); template facts + procedure in `references/formal-deck.md` §2a / §2b / §2c / §4.
   Since round 7 (2026-09-21) the single-survey baseline is the user's final
   `Mu2020_edge-couplers-si-pic-review/0921上台版本(中文).pptx`: English slides, Chinese notes in the
   presenter's voice (`talk-conventions.md` §8), page order and figure-page rules R7-1…R7-12 (§2c). Never
   produced by converting Class A.

Only on explicit request: `onepage.pptx` / `talk-deck.pptx` via `--pptx-from-story`
(Class A layout as pptx) — not a talk deck.

## Delivery message shape

Keypoint first (the logic sentence + the entry point with its why), then 為什麼讀它／
對我有什麼幫助, then the run folder, `story-gates.txt` + kv-lint verbatim, which product
class was produced (A only, unless the user asked for the formal deck), then the manual
checklist (A 必驗 ranked by consequence, B 體驗; shape per `ops/references/uat.md`),
open questions last. zh-TW.

## Boundaries

Evidence verdicts belong to `paper-distill` (call it for a contested claim; quote its
verdict words, never invent them). Finding papers → `literature-search-extract`; the
user's own study → `scientific-research-guide`; posts → `post-brief`. Deck renderers
for other formats are not built here until a real run asks for them. The formal deck
is edited from the lab template, never rendered from the HTML.

This skill is a DOMAIN layer of the shared design knowledge in
`~/.claude/references/design-axes/` (cross-medium principles for posts, decks, films,
web pages). Read it for anything `formal-deck.md` and `presentation-formats.md` do not
settle; where they conflict, this skill's rules win and the shared layer marks the
exception (e.g. R7-5 short-noun figure titles vs the shared assertion-title rule).

## Field test

Born 2026-09-03 from the user's rejection of the first two presentation designs
(figure-and-text description; key point as summary). First real run: Ow 2010 by the
main session, the same evening — it passed every gate and the user then ruled that
its HTML is a practice copy (「能看且方便看，但很醜不能用來展示」), which produced the
two product classes above. Offer `skill-co-upgrade` after any run that had to bypass a
rule here. Round 1 (2026-09-03, `outputs/skill-reviews/paper-story-gaps-round1-2026-09-03.md`):
the two calibrations' 19 findings dispositioned — Gb8 → S13 drift checklist, Gb9 → S4c
figure kinds, schema @3, tenth tell `abstract-mismatch`; the accepted runs stay @2.
Round 4 (2026-09-14, `outputs/skill-reviews/paper-story-gaps-round4-2026-09-14.md`): the advisor's
four opening questions, figures first and notes told as a story — schema @5 (`brief`, page
`asks`／`bridge`／`takeaway`／`figure_read`, `talk.story_arc`), S18–S20 / V21–V23 / L6, re-run on
Tran 2018 (the talk paper; the round-3 run kept in `_calibration/…/before-0914`).
Round 5 (2026-09-14, `outputs/skill-reviews/paper-story-gaps-round5-2026-09-14.md`): the user's review of the round-4
lab deck — fonts too small, too much text, sources not shown, Future work missing, key point moved to the closing —
gave the GaN skeleton + additions order, native diagram pages, source / keyword-search / References pages, S5 / S18 /
S20 flips (key point up front, `deck.minutes` optional) and lab gates L7–L10; round-4 deck kept in
`_calibration/…/round4-lab-deck-0914`.
Round 6 (2026-09-15, rules in `references/formal-deck.md` §2b): the user's hand-tuned Mu 2020 deck became the
formal-deck baseline. Eight revision items, then a diff of the user's final against the delivered build and four
user additions, gave R6-1…R6-14. The user's final is kept as
`Mu2020_edge-couplers-si-pic-review/lab-deck_v2_user-final-20260915.pptx`. `lab_deck.py` implemented R6 the same day
(formal-deck.md §4, round 6: gate L11 and the overwrite guard added).
Round 7 (2026-09-21, rules in `references/formal-deck.md` §2c, notes in `talk-conventions.md` §8): the user's
`0921上台版本(中文).pptx` — English slides, Chinese notes — was ruled what a single-survey formal deck should be. Diffs v2 → v3
and 0914 build → v3 plus a read of every render gave R7-1…R7-12 and the notes voice; the gates run on both user finals as
known-TRUE inputs recalibrated L3, L6, L7, L9, L10 (a trailing-blank-paragraph false FAIL) and L11, each with a selftest
positive control. Analysis record: `Mu2020_edge-couplers-si-pic-review/formal-deck-v3-analysis-20260921.md`.
Same day, second ruling: the notes voice, the figure–text rules and the closing logic chain bind every deck (class A too:
S20 / V23 flipped to "spoken at the close", the talk deck's slogan box moved to the Storyline page); page order and
methodology are read per paper type.
