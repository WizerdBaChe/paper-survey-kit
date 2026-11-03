---
name: paper-distill
description: >-
  Evidence audit of one paper, preprint, patent or tech doc by IMRaD (論文深讀): claim audit
  (evidence kind E1–E4), figure cards, what it teaches about writing; writes the
  【學習紀錄】 reading-record. Trigger on 「深讀這篇」「拆這篇的 IMRAD」
  「審一下它的主張撐不撐得住」「這個數字是哪一種證據」「從這篇學怎麼寫 Methods」. NOT the
  talk, one-page or key point (→ paper-story), finding papers (→ literature-search-extract),
  own study design (→ scientific-research-guide), social posts (→ post-brief).
---

# paper-distill — 深讀：證據夠不夠，這篇教我怎麼寫

## What this is (after the 2026-09-03 split)

Two things a researcher does with a paper are different objects: judge its
EVIDENCE, and understand its CONSTRUCTION so as to present it. This skill is the
first: IMRaD as a thinking order, a claim audit whose verdict words are calibrated,
figure cards that read the plot before the prose, and a writing-craft card — recorded
as a learning document the user replays. The second is `paper-story` (主軸／故事線 with
whys, 邏輯抽取, the lab's decks). They share one run folder and one toolset and call
each other by situation (`../paper-story/references/bridge.md`); this skill never
renders slides and never writes a key point.

## Intake (one line each)

- **depth** — `full` (every stage, 2–5 claims, every cited figure) · `standard` (≤ 3
  claims, one figure) · `triage` (Stage 0 + C1: is it worth reading).
- **why this paper** — the question the user is trying to settle; feeds `intake.why_this`
  and positioning. Ask once if absent.
- **home** — `PAPER_DISTILL_HOME`, default `<PAPER_HOME>`
  (vault ruling R5). Read `<NOTES_VAULT>\AGENTS.md` once per session; never write
  into the wings; every `.md` in the run folder carries the vault card.
- Source rules: PDF path → ingest; HTML URL → WebFetch into `source/paper.txt`; a PDF URL
  is a download the user performs. Paywalled → `access: abstract`, every claim `withhold`.
- **marks** — a PDF from the Zotero library arrives with its annotations + child notes in
  `intake.marked[]`, each origin-tagged; read them after Stage 0's questions, as candidates
  — only `owner` marks are the user's own, and only once confirmed (`reading-method.md` §Stage 0).

## Pipeline

| Stage | Question it settles | Writes | Read |
|---|---|---|---|
| 0 Intake & triage | what does it CLAIM, why did I pick it; the depth ruler (relevance × method weight × evidence depth) | `source`, `intake`, `paper_says` | `reading-method.md` |
| 0b Glossary pass | which 10–15 terms does this paper run on; subject / frame / field / coined; what is unclear | `terms[]` (`role`, `freq`, `unclear`, `ask_next`) | `reading-method.md` |
| 1 Skeleton | what function does each section perform; what is misplaced | `skeleton` | `reading-method.md` |
| 2 Core | how does the study hold up; whom do they reject and is it fair | `core` | `reading-method.md` |
| 3 Claim audit | is the evidence ENOUGH, not just present | `claims[]`, `did` | `claim-audit.md` |
| 4 Figure reading | what does the figure show before the text tells me | `figures[]` + crops | `figure-reading.md` |
| 5 Writing craft | what does this paper teach about writing one | `craft` | `writing-craft.md` |
| 6 Positioning | gap; why we care; borrow / not borrow | `position` | `reading-method.md` |
| 7 Record & file | the learning record, library, vault lint | `learning`, files | `output-spec.md` |

Read backwards (conclusion → abstract → figures → introduction → methods → body). The
reading order is not a deck order; decks are `paper-story`'s.

## Commands

```powershell
cd $HOME\.claude\skills\paper-distill
python scripts\ingest.py <paper.pdf | url> [--depth full|standard|triage] [--presenter NAME] [--slug SLUG] [--first-author NAME] [--year YYYY]
python scripts\ingest.py --text <paper.txt> | --jats <paper.xml> [same options]                # no PDF: source/paper.txt + structure.json (§N units, Fig. N, Table N) + figures.json (label + caption only, NO images); _meta.json source_kind text|jats
python scripts\probe.py --run <run_dir> --print                                                # source/structure.json: sections/figures/tables to cover + determinable anomalies (duplicate section numbers, uncited figures, abstract numbers absent from the body) — Stage 1 skeleton reads it; paper-story S11/S12 gate on it. Figure axis/legend text, equation fragments and footnote marks are not read as headings (inside a figure box, or an axis-like token); a text/JATS run keeps ingest's section units
python scripts\glossary.py --run <run_dir> --print                                             # source/glossary-candidates.json: recurring terms ranked by frequency × title/abstract/intro, acronyms expanded (reference list cut) — Stage 0b picks 10–15 and classifies them; --selftest is two-sided
python scripts\crop.py --run <run_dir> --caption "Fig. 3" --out figures/F1.png                 # what is painted between the nearest body text and the caption (caption excluded; a table: the side it sits on; a preprint with its figures after the caption list: the figure on a following page, band.layout = figure-after-caption); exit 3 = border-ink gate FAIL (ink on the crop edge); view it anyway — band.top_set_by says which block set the top; --above/--below/--full-width = the pre-2026-09-26 fixed rectangle; or --bbox x0,y0,x1,y1 --page N / --image p003_i01
python scripts\crop_all.py --run <run_dir> --apply                                              # every figures.json caption through crop.py the same way: figures/F<n>|T<n>.png (+ _p<page> for a continued table), replaced files -> figures/_previous/<tag>/, verdicts -> source/crops.json; --plan (default) writes nothing; a label-only stub caption whose figure is cropped under its captioned twin, and a later panel caption of an already targeted figure, are listed under "skipped" instead of cropped again; a text/JATS run (no PDF) is skipped with a message, nothing cropped
python scripts\units.py --run <run_dir> --check --twice                                        # source/units.json: the paper as ordered verbatim units (abstract/heading/paragraph/caption/…) + replayable fix log + coverage/replay/foreign/order/heading checks with controls; a PDF run needs crops.json; a text/JATS run is built from paper.txt + structure.json alone (units carry `line`, ids L<n>, plain-text paragraph breaks are a heuristic); Retort & Rove reads it (output-spec §1a)
python scripts\verify_run.py <run_dir>          # run by a DIFFERENT session/agent than the author: verbatim quotes, locators, placeholders, tags; a text/JATS run: page-based checks SKIP with their reason, a cited §N must be a structure.json unit (V3), structure lines must hold their text (V13)
python scripts\library.py register <run_dir> [--kind calibration --label <what-it-is>];  python <NOTES_VAULT>\tools\kv-lint.py
# layout (naming over routing, user ruling 2026-09-04): <home>/<FirstAuthor><Year>_<slug>/ holds the ONE accepted run per paper
# (ingest.py names it so, no date); calibration copies live under <home>/_calibration/<PaperId>/<label>/; README / KEYPOINTS.md /
# <PaperId>_keypoint.md are regenerated from the layout by register / readme; `library.py migrate --plan p.json [--apply]` moves old folders
```

`ingest.py` writes `source/paper.txt` (page markers), `source/pages/pNNN.png`,
`source/images/`, `source/figures.json` and a prefilled `cards.json`. The Read tool
refuses some publisher PDFs; the rendered pages are the reliable path.

`crops.json` and `units.json` are the verbatim layer that Retort & Rove (`<projects>/RetortAndRove`)
reads instead of parsing the PDF itself (user ruling 2026-09-27). Changing their shape is a contract change
(`references/output-spec.md` §1a): re-run `units.py --accepted <home> --check --twice` and tell that project.

## Stage rules that are not negotiable

- **Origin tag on every sentence**: `[author]` (paper says it, locator) · `[verified]`
  (I checked the figure/table) · `[inferred]` · `[assumed]`. "SOTA / first / novel"
  becomes "authors claim better than X on Y under Z". Numbers carry
  `paper-measured / paper-simulated / re-derived / unverified`. Bibliographic facts the
  PDF omits (DOI) may be looked up but are tagged `[external]`.
- **Locator or 無法定位** on every load-bearing statement; quotes verbatim; sentence
  patterns ≤ 15 words.
- **The figure before the sentence**; self-built baselines are `self-eval`; positive-only
  experiments are `one-sided` and cap a mechanism claim at *hypothetical*.
- **What a figure SHOWS comes from the rendered figure image, never from its caption text
  alone** (user-approved 2026-11-03, G11). A figure card's gist, and every `[verified]` tag on
  a figure, needs the image Read (a `crop.py` crop, `source/pages/pNNN.png` or an image the
  user supplied); a statement taken from the caption is tagged `[author]` with the caption as
  locator, and with no image the card says "image not viewed" and claims nothing about the
  content. Origin: two readers called Liu 2023 Fig. 1(a) a "Feynman diagram" from its JATS
  caption; the rendered figure is a 3D surface-state / bulk / substrate cartoon (user
  correction, `<NOTES_VAULT>\literature\EvidenceRuns\reflux.jsonl`, event
  `20261103T033604-a87470`). A text or JATS source (`ingest.py --text/--jats`) has no
  images: ask for them before Stage 4.
- **A source with no PDF** (`ingest.py --text <file>` / `--jats <xml>`, `_meta.json`
  `source_kind` text|jats) is cited by `§N` / `§N.M` (the unit ids in `source/structure.json`,
  `§0` = the abstract), `Fig. N`, `Table N` — never `p.N`, never a section or paragraph number
  you counted yourself. paper-story's S3 locator pattern accepts `§<digits>` (checked
  2026-11-03).
- **Verdict words are calibrated** (`claim-audit.md`): provisional / leaning /
  hypothetical / withhold; `paper-story` quotes them and may not invent its own.
- **自問 before every answer** in the record; the record is a trail, not a summary.
- **Vault contract** for every `.md` written into the library; `kv-lint.py` 0 FAIL.
- **Stop rule**: when the run's question is answered, write "not needed for this run".
- **Premises are listed, not absorbed**: `core.assumptions[]` names what the paper takes as
  true without testing (`tested: no` → the dependent claim row's `missing`); the glossary's
  `coined` terms are the term-substitution input; `position.lineage` is read off the reference
  list — no author database (2026-09-03 fold of four posts, `reading-method.md` B-7…B-10).

## Deliverables (run folder)

1. `reading-record.md` — 【學習紀錄】 audit summary first (what holds, what is missing,
   C1 verdict), then sections 1–9 per `assets/reading-record-template.md`; a pointer to
   the `paper-story` run when one exists.
2. `cards.json` — the contract (`assets/cards.schema.json`); `paper-story` reads
   `claims`, `figures`, `craft`, `terms` from it.
3. Library entry (`library.py register`) + vault lint line.

## Delivery message shape

Audit summary first (C1 verdict and its evidence kind, what is missing), then the run
folder, `verify_run.py` + kv-lint lines verbatim, then the manual checklist (A 必驗,
B 體驗), open questions last. zh-TW with inline English. Offer `paper-story` when the
user is going to present the paper.

## Field test

Three real runs 2026-09-02/03 (calibration record: `evals/calibration-2026-09-03.md`);
presentation products retired from this skill on 2026-09-03 (`archive/2026-09-03-split/`).
Decision register D-1…D-29 and the know-why of this skill's shape (what was borrowed, what was
deliberately not built): `references/design-rationale.md` — read it before changing the pipeline.
Offer `skill-co-upgrade` after any run that had to bypass a rule here.
