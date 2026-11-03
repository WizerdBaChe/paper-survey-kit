---
xi: 1
what: paper-story 的軸向：把一篇論文的主軸與故事線重建成「每一步都帶 why」的敘事卡——標準解法評估（Heilmeier／CARS／Toulmin／C-C-C／ABT）與本 skill 採用的組合 (the why-axis for narrative reconstruction: standard frameworks evaluated and the combination adopted)
tags: [skill-reference, paper-story, narrative, why-axis, heilmeier, toulmin, cars]
aliases: [主軸與故事線, 為什麼是這個切入點, 敘事卡, why axis, Heilmeier catechism, CARS model, Toulmin warrant, storyline beats]
date: 2026-09-03
status: live
---

# The why-axis — reconstructing a paper's narrative with every step's reason

`paper-story` Stage N2. The user's ruling (2026-09-03): a logic extraction that only
says HOW and WHAT is not science reading — 科學探究最需要的是各種「為什麼」. The
first attempt phrased the 主軸 as 「能不能／是否可以」 and never said WHY the
authors chose that entry point. This file fixes the axis so that a why is a
required field, not a stylistic hope.

## 1. Which standard framework carries the "why"? (evaluated 2026-09-03)

The user asked whether a more standard solution exists for presenting the axis.
There is no single standard; four established instruments each own one kind of
why, and research-writing pedagogy combines them. Citation-level details below
are from standing knowledge (stable canon, not re-fetched this session).

| Instrument | Origin | The why it owns | Used here for |
|---|---|---|---|
| **Heilmeier Catechism** | G. H. Heilmeier, DARPA, 1975 (eight questions for judging a research proposal) | why this problem, why the current ways fall short, why the new approach should succeed, why anyone cares, how success will be checked | the AXIS card: entry point, method choice, evaluation plan, who-cares |
| **CARS — Create A Research Space** | J. Swales, *Genre Analysis*, 1990 (Move 1 territory → Move 2 niche → Move 3 occupy) | why THIS niche / entry point: which gap, why it matters now, why these authors are positioned to attack it | `axis.entry_point.why` |
| **Toulmin argument model** | S. Toulmin, *The Uses of Argument*, 1958 (claim, grounds, warrant, backing, qualifier, rebuttal) | why the evidence supports the claim — the WARRANT of each inferential step | every link of the logic chain (`logic.chain[].warrant`) |
| **Context–Content–Conclusion, one central contribution** | Mensh & Kording, *Ten simple rules for structuring papers*, PLOS Comput Biol 2017 | why a paper has ONE spine (the central contribution the title announces); results as statements each backed by a figure | the 主軸 test (one central claim) and `axis.presentation.why` |
| **ABT — And, But, Therefore** | R. Olson, *Houston, We Have a Narrative*, 2015 | narrative tension: the "But" is where the why lives | the storyline beats ①→② (the But) and ⑥ (the Therefore) |

Rejected as the spine: Sinek's Why–How–What (motivational, no evaluation
question); "5 Whys" (root-cause tool, not argument structure); IMRaD itself
(a container order, carries no why — that is exactly the gap the user named).

**Adopted axis** = Heilmeier's questions as the backbone, CARS Move 2 for the
entry point, Toulmin warrants on every chain link, the single-contribution rule
as the test that the 主軸 is one sentence and not three.

## 2. The AXIS card (`story.axis`) — five items, each with a why

| Item | What (as the paper tells it) | WHY (required) | Heilmeier question |
|---|---|---|---|
| `entry_point` 切入點 | the question / gap the paper enters through | why THIS entry point: what limits today's ways, why now, why these authors (their tools, prior work) — CARS Move 2 | Q1 what are you trying to do; Q2 how is it done today and what are the limits |
| `central_claim` 中心主張 | the one contribution the paper stands on | why it matters, to whom, what changes if true (who cares) | Q4/Q5 who cares; what difference will it make |
| `method_choice` 方法選擇 | the approach actually taken | why this method and why it should work; what alternatives were rejected and why (by the authors, or implied) — list them PER STEP of the method (e.g. mask definition / etch / removal / polish), not as one pooled list: in the 2026-09-03 calibration two independent runs of one paper each named a different step's alternative and missed the other's | Q3 what is new in the approach and why do you think it will succeed |
| `evaluation_plan` 評估計畫 | what had to be shown for the claim to hold: metrics, success criteria, controls, expected outcome | why these metrics / this criterion / these controls — what would have counted as failure | Q8 the midterm and final "exams" |
| `presentation` 呈現 | which statistics, which visualisations, in what order | why these choices fit the claim (a box plot because the claim is about spread; a cross-section SEM because the claim is a mechanism) | Mensh & Kording rule 7 |

Two more fields on `method_choice` (2026-09-03, borrowed via `paper-distill`
`reading-method.md` B-7 / B-9; optional in the schema, expected in a `deep` run):

- `necessity` — the counterfactual behind 「為什麼一定要這樣」 (Day 08's Why layer:
  換一種方式會失效嗎). For each load-bearing step: if it were swapped for the
  nearest alternative, what in the result or the argument fails? A step whose
  swap changes nothing is not load-bearing, whatever the authors say about it —
  that is a `drift` row (`method-after-the-fact` or `weaker-instrument`). Tag
  `[author]` when the paper argues it, `[inferred]` when I do.
- `dead_ends` — where the authors report getting stuck or an attempt that did
  not work (the Failure beat of the research journey, Research Reading OS card
  06: 又曾經在哪裡卡住). Usually one sentence in the Methods or Discussion
  ("initial attempts with X resulted in…"), sometimes only in the supplement.
  Write 「未述」 when the paper tells none — a journey told without a failure is
  itself a tell about the telling, worth one line in `drift` if the method's
  why is thin.

A why that only restates the what ("they chose ray tracing because they wanted to
simulate") is empty; a why names the constraint or belief that made the choice
rational ("ray tracing because the mirror is 300–600 µm, hundreds of wavelengths
across, so geometric optics is adequate and a parameter sweep of 45 points is
cheap"). Tag each why `[author]` (the paper says it), `[inferred]` (my
reconstruction) or `[assumed]`; a paper that never gives a why is recorded as
such — that is itself a finding for `drift`.

## 3. The STORYLINE (`story.storyline`) — six beats, each with a why and a locator

| # | Beat | What to write | The why of this beat |
|---|---|---|---|
| ① | 情境與痛點 | the world the paper opens in, and what hurts | why the pain matters (the stakes) |
| ② | 缺口與提問 | the gap and the question (ABT's "But") | why the gap exists — what blocks the obvious fix |
| ③ | 方法選擇 | the move the authors make | why this move follows from ② (the warrant) |
| ④ | 評估計畫 | what they set out to demonstrate and how | why these demonstrations would settle the question |
| ⑤ | 執行與呈現 | what was actually shown, told with which stats/visuals | why the telling fits the evidence (or doesn't) |
| ⑥ | 詮釋與收束 | what they say it means and how far (ABT's "Therefore") | why the qualifier is where it is |

Six beats is a floor, not a template: a paper with two results (e.g. Ow 2010's
DBR extension) gets its second result as its own ⑤ beat, labelled as a grafted
storyline if the axis card cannot absorb it.

## 4. DRIFT (`story.drift`) — where the told story leaves the axis

The user's observation: 主軸 and 故事線 are exactly what paper writing drifts from
most easily. Record every place the paper's telling departs from its own axis,
with a why-it-matters:

Each tell has a `kind` id — `drift[].kind` in story.json (schema @3), one per row:

- `over-claim` — a claim in ⑥ stronger than ④ planned to prove (the row's note names the
  `reach` axis crossed, as paper-distill's `claims[].reach[]` spells it —
  `~/.claude/references/writing-norms/claim-reach.md` §1);
- `grafted-result` — a section that belongs to a different axis (a duplicated
  section number is a tell);
- `no-criterion` — an evaluation with no criterion (a number without a threshold);
- `method-after-the-fact` — a method justified after the fact (the why appears
  only in the discussion, or the full argument sits far from the Methods);
- `figure-unasked` — a figure that answers a question the axis never asked;
- `limitation-aside` — a limitation stated as an aside inside a positive sentence
  （「…可控，主要受限於微影」）instead of as a limitation — the reader hears
  "controlled", not "limited";
- `weaker-instrument` — a claim whose evidence comes from a weaker instrument than
  the claim's wording (「selectively reflect a band」 shown by a camera RGB line
  scan, not a spectrum; a ranking whose baseline the authors computed themselves);
- `discussion-new-data` — a measurement that first appears in the Discussion (new
  data with no Results home — Bose 2024's thermal-bistability absorption fraction);
- `selective-condition` — a flagship number taken from the better of two conditions
  without saying why (TE reported, TM worse and unexplained; the best of three
  devices as the headline);
- `abstract-mismatch` — a number the abstract states that the body does not carry
  or supports only partly (Ow 2010: 「< 2 nm」 in the abstract, one sample in three
  in the body; Bose 2024: thick-film medians in the abstract only). The probe's
  `abstract-number-not-in-body` anomaly catches the absent case by machine; this
  tell also covers the partly-supported one. Added in co-upgrade round 1 when three
  real drift rows across two papers fitted no other kind;
- `other` — only with the tell named in `what_drifted`; it covers no list kind.

Walk the list item by item for every paper and DECLARE the walk: every drift row
carries its `kind`; `coverage.drift_checklist` marks each of the ten kinds `found`
(a row carries it) or `none` (looked for, not present). S13 warns for a kind
neither found nor declared. In the 2026-09-03 calibration one run found the
grafted section and missed the buried limitation, the other did the reverse; in
the blind test run X walked four kinds run Y did not, and Y two that X did not —
a checklist not declared is a checklist not walked. Promotion trigger: a kind
declared `none` whose OBSERVATION a second reader finds — and the first reading carries
it under no kind at all — is a FAIL for the first reading; the same observation filed
under a different kind (round 2: Bose Fig.1's vision cartoon as `over-claim` in one run,
`figure-unasked` in two others) is a classification disagreement, recorded, not a FAIL.
Backfilled checklists (`coverage.checklist_provenance: backfilled`, the four runs
upgraded after round 1) mean 「no row of that kind」, not a declared search — S13 says
so; the trigger applies to authored checklists. Round-2 measurement: the one from-scratch
run that declared the walk while reading (Z) found exactly the union of what two
undeclared readers (X, Y) had found.

A quote the text layer lacks (a PDF whose extracted text misses a whole block — Zhang
2021's abstract) is marked `quote_source: "page-image"` with its page locator; S10 then
warns for the dispatcher to verify it on `source/pages` instead of failing. Absent from
the page image too = fabrication.

**Anchoring and coverage (user ruling 2026-09-03: 看錯／漏看 = 亂掰).**

- Every drift row carries `quote` — the paper's own words the drift is about, verbatim,
  ≤ ~25 words, with its locator. S10 looks the quote up in `source/paper.txt`; a quote
  that is not there is a fabrication-level FAIL (a thin text layer downgrades to WARN and
  the page image decides). The axis entry point and central claim, and beats ② ⑥, carry
  a quote too when the paper states them — 「原文邏輯鏈的引用標註」 is what makes a
  reading checkable by someone who did not read the paper.
- Before writing drift, read `source/structure.json` (`paper-distill/scripts/probe.py`).
  Its `anomalies[]` are the tells a machine can determine — a duplicated section number
  (Ow 2010's two §3.2 = the grafted DBR result), a figure the body never cites, a number
  in the abstract that appears nowhere in the body. Each anomaly must land somewhere: a
  drift row, a storyline beat (⑤′ for a grafted second result the authors treat as an
  extension), or `coverage.skipped[]` with a why. S12 warns for each one left silent.
- `coverage.skipped[]`: every unit of `structure.json` (sections, subsections, figures,
  tables) that no locator cites is listed here with a why — 「這段是背景，不進故事線」 is
  a why; silence is 漏看. S11 warns for units neither cited nor skipped.

Why these three and not a self-check prompt: peer-review practice moved the same way —
reporting checklists (CONSORT/PRISMA) make authors give a page number per item, i.e. a
coverage map; Elsevier's structured-review pilot (nine fixed questions, 2022–24) raised
reviewer agreement on recommendations from 31 % to 41 % while agreement on 「是否被數據
支持」 stayed the lowest (53 %) — fixed questions improve coverage, not judgment; and
factored verification of LLM paper summaries finds 0.6–1.6 fabricated claims per summary
until each claim is checked against the source. So: coverage by checklist, fabrication by
quote lookup, judgment by a second reader (mutual detection) — three instruments, one
per failure class.

If `run.distill_run` names a `paper-distill` run, cite its claim verdicts here
(C1 verdict vs beat ⑥ wording) — that is the bridge in the direction
deep-reading → story.

## 5. Order of work

1. Read the paper backwards (conclusion → abstract → figures → introduction →
   methods → body) and write beats ⑥, ②, ① first — the ends of the story
   fix the axis; then ③④⑤.
2. Fill the AXIS card from the beats; if `central_claim.what` cannot be one
   sentence, the paper has two spines — say so in `drift`.
3. Only now go to `logic-extraction.md` (N3). Extraction before the axis is
   how the first two rounds produced summaries instead of logic.
4. **The brief (`story.brief`, schema @5, round 4 2026-09-14)** — the advisor asked that a talk
   state up front why the paper is worth reading, what ALL its methods are, whether it reached
   its goals and how that was judged. Write it from the beats and the axis, as three questions a
   reader asks before trusting a paper:
   - Q1 what problem does it solve → `brief.problem` (the paper's problem, never the presenter's
     reason — that is `why_me.why_read`, and S18 warns when the two coincide);
   - Q2 what is the approach and how does it differ → `brief.approach`, `brief.differs` (named
     against the prior work it answers) and `brief.conversation` (the locator of that exchange);
   - Q3 did it work, and how do we know → `brief.verdicts[]`: one row per goal the paper sets,
     each with `judged_by` (the instrument, statistic or comparison that rules), `result`
     (numbers with their conditions) and `status` achieved / partly / simulated-only /
     not-shown. A goal carried only by simulation or calculation is `simulated-only` even when
     the paper's abstract speaks of it as done.
   `brief.methods[]` lists EVERY method — fabrication, model, simulation, measurement, analysis —
   each with the question it answers; a method that answers nothing the verdicts need is a
   drift candidate.
5. **The story arc (`talk.story_arc`)** — after the beats, compress the telling into one
   And–But–Therefore spine and 4–6 craft steps: what the authors did at that point of the telling
   and why it works on a reader (which question it closes, which doubt it pre-empts). The weakest
   link of the telling is one of the steps. This is what the presenter learns about writing;
   the beats are what the paper says, the craft is how it gets believed.
