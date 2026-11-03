---
what: paper-story class B — the formal talk deck built on a template-free blank base (the public kit's replacement for the origin's lab-template reference); story.json → slide mapping, the hand-tuning rules R6/R7, procedure, the lab_deck.py gates
tags: [skill-reference, paper-story, formal-deck, pptx, product-classes]
date: 2026-11-03
status: live
---

# The formal deck — what class B is made from

This file replaces the origin environment's lab-template reference in the public kit. The origin builds its
formal deck from a copy of a research group's own PPTX template; that template, the decks it was derived from
and the people who made them are not part of this kit. What is kept is everything that is NOT the template:
the two product classes, the mapping from `story.json`, the hand-tuning rules the deck owner ruled on
(R6, R7), the procedure and the gates. Section numbers follow the origin file so every `§` reference in
`SKILL.md`, `presentation-formats.md`, `talk-conventions.md` and `lab_deck.py` still resolves.

Two product classes, never converted into each other (owner ruling 2026-09-03):

| class | files | consumer | language | made by |
|---|---|---|---|---|
| A practice / review | `paper-explainer.html`, `narrative-record.md` | the presenter | the presenter's language + inline English | `render_story.py` (always) |
| B formal talk | `lab-deck.pptx` (single-paper talk), `lab-onepage.pptx` (ten-papers format) | the audience | slide text ENGLISH; speaker notes in the presenter's notes voice | `lab_deck.py`, only on explicit request |

The HTML layout is readable but not for display; the deck is never made by converting it. `--pptx-from-story`
(class A layout as pptx) exists only for an explicit request and its gate file says `P0 INFO`.

## 1. The base

**Default in this kit: `--base blank`.** `lab_deck.py` creates the base itself with python-pptx's default master:
slide size 10 × 7.5 in (4:3), layouts `Title Slide` / `Title and Content` / `Blank`, and ONE title slide holding
the three boxes the fill code looks for — the title placeholder, a `Presenter:` subtitle and a venue text box
(shape name `文字方塊 1`, kept for code compatibility). No master artwork, logo or footer band.

**Your own template (`--base template`).** Put two title-slide-only decks in `<PAPER_HOME>/_templates/`:
`base_single-paper.pptx` and `base_ten-papers.pptx`. Make each ONCE from a deck of your own by deleting every
slide but the title (`strip_to_title`) and scrubbing it (title-slide text → placeholders, notes emptied,
`docProps/app.xml` slide-title list and comment authors removed). `open_base()` stops loudly when a base is
missing or has more than one slide. The title slide must keep a text box that starts with `Presenter` and,
if you want the venue printed, a box named `文字方塊 1`. The cover's `Advisor:` line comes from `--advisor`
(empty by default in this kit: the line is dropped).

Facts the generator assumes either way: body font Times New Roman, slide text English on every slide (gate L2),
speaker notes in the presenter's spoken language, a `Thanks for listening.` slide re-created last on a blank
layout (keeping a template's own Thanks slide made python-pptx's new slide parts collide and PowerPoint refused
the file, 2026-09-04).

## 2. Mapping story.json → slides

| slide | source in `story.json` | English text rule |
|---|---|---|
| title | `source.title`, presenter, date, `en.venue`, `en.authors_line` | verbatim title |
| Key points (@5) | `en.why_read`, `en.problem`, `en.table` (five fields), `en.keypoint` | "Why this paper:" · "Problem it solves:" · the five-field table (no header row) · "Key point:" line |
| Outline | `talk.outline` part names | the paper's section names |
| section pages | `deck.pages[]` in order: `title`, `figure`, `highlights` (≤ 3) | one English bullet ≤ 12 words each; numbers verbatim from the paper |
| Results pages | one `figure` + its ONE number | picture in the figure box |
| Storyline (@5) | `en.storyline` (spine, steps[move, why]) | "In one sentence:" spine (And–But–Therefore) + numbered moves |
| Conclusion | `deck.pages[section=Conclusion]` | `cause → effect` style |
| speaker notes | `deck.pages[].notes`, `talk.if_asked` in brackets | the presenter's notes voice (`talk-conventions.md` §8) |
| Thanks | — | re-created |

### 2a. Round 5 order (2026-09-14)

Structure reference: a single-paper talk skeleton Title → Outlines → Key points → Introduction → Fabrication →
Results → Conclusion → Future work; every other page is an addition. `lab_deck.py` dispatches on
`en.pages[n].layout` (else the section): `cover` (Outlines) · `source` (About this paper: first-page image,
submission timeline, journal facts with year and route) · `keypoint` (the five fields on ONE slide when they fit)
· `keylogic` (slogan clauses over "In this paper" boxes) · `methods` · `verdict` (goal → judged by → result →
coloured status) · `timeline` · `process` (vertical step list beside the cross-section) · `storyline` (AND / BUT
/ THEREFORE + numbered moves) · `conclusion` · `futurework` · `search` (vocabulary ledger → query → backward /
forward chasing → stop) · `references`. Every diagram is native editable shapes (the presenter hand-tunes the
deck). Journal metrics carry their year AND their route; a publisher page read through web search is not JCR or
Scopus, so the delivery tells the presenter to verify them at their own library. **Round 7 (§2c) supersedes this
order for the formal deck of a review.**

### 2b. Round 6 rules — the owner's hand-tuned deck (2026-09-15; supersede §2a and §4 where they conflict)

Type and spacing
- **R6-1 One size per level, never per string length.** Title 32 on one line (shorten it; PowerPoint's own layout
  decides whether it fits). Subheading, box header, table header and row labels 20 bold. Body, bullets, table cells,
  box text 18. Diagram node text 16. Annotation or legend 14. References 12.
- **R6-2 Line spacing 1.5** in the bullet box when the page has room; single when it does not.

Figure pages
- **R6-3 Three statements per figure page, in this order:** the principle or formula → what the figure shows → the
  conclusion it supports. No "Fig. x:" prefix, no leading "→" marker, no separate takeaway line. Read without the
  speaker, the slide carries about 70 % of the point.
- **R6-4 Sub-items stay inside their statement:** (a) / (b) panels and parallel data groups go on soft line breaks
  (Shift+Enter, `<a:br/>`) in the same bullet.
- **R6-5 A semicolon may end a line;** break after it with a soft break.
- **R6-6 One structure family per page, each with its own paper figure.**
- **R6-7 Crops include the paper's label** (the "Figure x." caption line; `crop.py --caption "Figure n" --above … --below …`).
- **R6-8 Legibility beats the frame:** a figure may be enlarged over the frame so its text is readable; text boxes
  stay inside. A picture in the footer band is INFO, never a defect.

Text versus visuals
- **R6-9 Parallel items become a native table.**
- **R6-10 Visual guidance replaces text** wherever a shape, position or table already says it.
- **R6-11 No reference numbers in slide body text;** References are APA 7 from Crossref metadata, alphabetical, each
  tagged `[Ref. n]` with its number in the paper, 12 pt, over as many slides as needed.
- **R6-12 No Source strips.**

Review papers
- **R6-13 Key points of a review:** Structure = the platform and the structures derived from it; Features = the
  paper's sorting axis; Method = the per-family description template plus the shared ruler; Result = the
  comparison table's value ranges, not the flagship alone.

Revision workflow
- **R6-14 A hand-tuned deck is a baseline:** build a revision under a new name, never overwrite the presenter's deck
  (the generator stamps `core_properties.last_modified_by` and refuses an output someone else saved, unless
  `--overwrite`).

Generator status: `lab_deck.py` implements R6-1, R6-2, R6-3, R6-4/R6-5, R6-8, R6-11, R6-12 and R6-14; R6-6,
R6-7, R6-9, R6-10 and R6-13 stay authoring rules (the generator cannot see what a crop contains).

### 2c. Round 7 rules — the owner's final single-survey deck (2026-09-21; supersede §2a, §2b, §4 where they conflict)

Scope: the notes voice (`talk-conventions.md` §8), the figure–text rules R7-5, R7-6, R7-7, R7-9, R7-10, R7-11,
the title slide R7-12 and R7-2 bind every deck (class A and B, every paper type). R7-1, R7-3, R7-4 and R7-8 are
the review profile; a device / design paper keeps the §2a skeleton until its own final deck is ruled.

Page order
- **R7-1 Front block = Title → Outlines → Key points, nothing else.** The four opening questions (why read, every
  method, did it work, judged how) are answered inside the Key points rows and the notes. Then Background → How
  this review is organized → one page per family in the paper's axis order (an explainer page right after a family
  whose mechanism needs one) → the paper's comparison tables → Conclusion → Logic chain and story line → Future
  work → References → Thanks. Set `skip: true` on class-A-only pages.
- **R7-2 The logic chain closes the talk:** one page "Conclusion: Logic chain and story line" — SITUATION (green,
  numbered facts) · BUT (orange) · THEREFORE · Step 1…4 boxes in a 2 × 2 snake, 16 pt. The slogan is paraphrased as
  the steps. `render_story.py` S20 / `verify_story.py` V23 check it is spoken at the close.
- **R7-3 Conclusion = the author's own ending, then my reading:** an "Author:" line, a green "Safe to takeaway" box
  and an orange "Watch out" box.
- **R7-4 Future work = one box of extension topics** (≤ 5 bullets; the why of each in the notes).

Figure pages
- **R7-5 Titles are short nouns** ("Horizontal n: Family", "Comparison: …"), never a claim sentence.
- **R7-6 Two to four statements; the figure-reading statement is optional** (amends R6-3). Mandatory: the principle
  and the data line. A statement that only names what a panel shows moves to the notes.
- **R7-7 Native pointer shapes over a figure are welcome.**
- **R7-8 Key points of a review, Result row = the review's headline comparison:** both sides with ranges and each
  side's price. The Key points slide is dense by design: L7 exempts it.
- **R7-9 Every data line pairs the number with its price** (a number alone is half a statement).
- **R7-10 Background states the counter-case too:** why the obvious fix fails sits beside the mismatch itself.

Text
- **R7-11 An inline "→" is a causal arrow and stays;** only a LEADING "→" is the retired role marker (L11).
- **R7-12 Title slide:** publisher and journal logos when the presenter supplies them (publisher hosts are not
  agent-fetched), the venue line top right, the APA author-year line under the title.

Not generated natively yet: the R7-2 snake layout, the R7-3 boxes and R7-12 logos — hand-build them on the
generated deck until a run needs them generated.

## 3. Procedure (explicit request only — 「做正式簡報」「英文版」)

1. `python scripts/lab_deck.py --run <run_dir> --format deck` (blank base by default; `--base template` for your
   own). Never start from the HTML.
2. English slide text comes from the run's `en` block, authored by the model at N4 — never machine-translated on
   the fly. Figures from `figures/` (crop with `paper-distill/scripts/crop.py`).
3. Speaker notes: the page's spoken sentence; the `if_asked` items in brackets at the end.
4. Acceptance (a human looks at slides — no "looks fine" claim without it): `--render` exports every slide to PNG
   through PowerPoint COM (Windows + PowerPoint) and adds the L10 layout gate; without PowerPoint, open the deck by
   eye. The deck is saved BEFORE the gates run.
5. Deliver with the manual checklist; say which class was produced.

## 4. `scripts/lab_deck.py` gates

L1 slide size 10 × 7.5 · L2 no CJK on any slide · L3 Key points slide in the front block (≤ slide 4) · L4 Thanks
last · L5 (with `--render`) PowerPoint COM export · L6 storyline slide and conclusion statements · L7 WARN body run
< 14 pt, a run off the six size levels, or a slide over 650 characters (Key points and References exempt) · L8 FAIL
no References slide, WARN a leftover Source strip · L9 WARN skeleton order by fixed titles · L10 (with `--render`)
PowerPoint's own text layout: FAIL text taller than a bordered shape or a shape below the slide edge · L11 WARN
`[n]` tags, a "Fig. x:" prefix or a leading "→" · L12 (onepage) WARN a cell with more than one number.
`--selftest` builds a clean deck plus injected defects and asserts the slide or shape each defect changes; the
PowerPoint-only cases are skipped, and said so, without PowerPoint. The density ruler (650) and the glyph-width
constant `K_TIMES = 0.46` were measured on the origin's decks (2026-09-14).

## 5. Review-when

Re-read §2b / §2c when the presenter hand-tunes the next formal deck (each hand edit is a candidate rule); write
the device / design profile when the first device or design paper's final deck is ruled; re-measure L7's ruler
when your own talks get markedly denser than 650 characters per slide.

## 6. Ten-papers page (`lab-onepage.pptx`, owner ruling 2026-11-03, schema `story@6`)

Page title = `source.title (year)`; the venue is a small badge top-left (`source.venue`); pictures = the
`onepage.figures[]` tiles (3–4 main tiles, one per argument step, plus at most one `side-evidence` tile; deep mode
and schema ≤ @5 keep 3–6 figures); table = `onepage.table` in English with `onepage.fields` rows (`five` default,
`four` drops Features); Conclusion cell = `Authors: … | Verdict: …`; the Keypoint line (`logic.keypoint`,
English) under the title. Density step: every cell is cut to its numbers and first clause; the dropped clauses
and the verdict move to the speaker notes, which hold the page script (`onepage.script`) followed by each tile's
`notes`. Gate L12 WARNs when a cell is still over the limit; 120 characters per cell is the outer bound.
