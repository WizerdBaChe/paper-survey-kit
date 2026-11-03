---
xi: 1
what: paper-distill Stage 3 主張審計——主張類型、證據種類、判斷強度、原文出處與來源標記的填表規則 (claim audit table rules: claim types, evidence kinds, verdict strength, origin tags)
tags: [skill-reference, paper-distill, claim-audit, evidence]
aliases: [主張審計, claim table, 證據層次, 判斷強度, evidence level, verdict strength]
date: 2026-09-02
status: live
---

# Claim audit — is the evidence enough, not just present

Stage 3 of `paper-distill`. Output: 2–5 rows (`standard` depth ≤ 3) in
`cards.json → claims[]` and the same table in `analysis.md`. The audit is
the instrument the key point rests on: a key point that says "proves" over
a row marked *hypothetical* is a defect the renderer flags.

## Why a table and not a paragraph

A paragraph lets confidence leak in through adjectives. A table forces five
separate answers per claim — what is claimed, how far it reaches, what backs
it, what kind of backing that is, what is still missing — and only then a verdict. The table
is also the only stage output another person can re-check row by row
(source B-4: SHIP 003 Day 04, fig 7; the post's own judgment was that this
table is its most valuable artifact for exactly that reason).

## Columns

| Column | Fill rule |
|---|---|
| `id` | C1… in order of load-bearing weight (C1 = the claim the paper would be cited for) |
| `text` | the claim in ONE sentence, `[author]` wording kept close; strip promotional words and record them in `notes` ("first", "novel", "SOTA", "significantly") |
| `type` | `specific` (a concrete result: value, trend) · `testable` (a statement data could refute) · `mechanism` (why it happens) · `prediction` (what will happen / where it applies) |
| `reach[]` | which axes the claim ASSERTS, as codes from the `reach` enum in `assets/cards.schema.json` (definitions and minimum support: `~/.claude/references/writing-norms/claim-reach.md` §1). The row's `verdict` is the one its evidence earns for its WEAKEST asserted axis; an asserted axis with no locatable support is either cut from `text` (the cut wording goes to `notes`) or makes the row `withhold`, and `missing` names that axis. Optional on legacy runs; filled on every new row |
| `evidence[]` | each item = `locator` + `what` — the figure, table, equation or passage that backs the claim, and what in it does the backing. No locator → `無法定位` and the row cannot score above *withhold* |
| `kind` | the KIND of evidence behind the row (see below) |
| `missing` | the one thing that would most raise the verdict if present (a control, an independent device, a second wafer, a standard benchmark, a repeat, a temperature sweep…) |
| `verdict` | `provisional` · `leaning` · `hypothetical` · `withhold` (see below) |
| `origin` | `author` (the paper asserts it) · `verified` (I checked the figure/table and it shows this) · `inferred` (my reading beyond what the paper states) · `assumed` |
| `notes` | promotional words stripped, fairness of comparison, self-evaluation flags |

## Evidence kind (借 B-4, adapted)

Day 04 labels four evidence levels L1–L4. Read literally, its table pairs
L4 "external validation" with "withhold" — a contradiction if L1–L4 were a
ladder. The post-brief record of that post already noted the correct
reading: each row is an independent pairing ("given only this kind of
evidence, how far may I go?"). This skill keeps the four KINDS and lets the
reader choose the verdict; kind and verdict are separate columns.

| kind | What it is | In device / photonics papers |
|---|---|---|
| `E1 primary` | raw data, direct observation | measured curves on named devices; images (TEM/SEM) of the measured device |
| `E2 secondary` | aggregated statistics, systematic review, database | wafer maps, box plots over n devices, benchmark tables compiled from literature |
| `E3 inferential` | theory, derivation, mechanism model, simulation | TCAD/FDTD results, analytical fits, extracted parameters |
| `E4 external` | independent reproduction, real application, cross-context validation | another group's result cited as agreeing; deployment; a standard benchmark |

Typical verdict by kind, before adjustment: E1 alone → *provisional* (I
can say what was observed, on those devices, under those conditions); E2 →
*leaning* (likely holds / likely not, sample-limited); E3 alone →
*hypothetical* (a reasonable model, unverified); E4 present → the verdict
may rise one step; nothing locatable → *withhold*.

## Verdict strength → wording (calibration)

| verdict | May say | May not say |
|---|---|---|
| `provisional` | "shows, on N devices, under X…"; "observed" | "demonstrates generally", "proves" |
| `leaning` | "likely", "tends to", "supports" | "establishes" |
| `hypothetical` | "if the model holds, then…"; "consistent with" | "explains", "because" |
| `withhold` | "cannot yet say"; "claimed, not shown" | any positive claim |

`paper-story` quotes these verdict words in `drift` and the key point's verbs may
not exceed C1's (`../../paper-story/references/logic-extraction.md`). Ceiling
(B-7, Research Reading OS cards 02/03/05): a single paper's result is evidence
that ONE route is possible, never that it is the answer — so no row rises above
*provisional* on the paper's own evidence alone; *leaning* and above need E2/E4.
An untested premise in `core.assumptions[]` (`tested: no`) that a row rests on is
written into that row's `missing`.

## Adjustments the user's habits require

- **Self-evaluation is weaker evidence.** A baseline built by the authors,
  an ablation on their own setup, or a "conventional device" fabricated in
  the same run for comparison is one code judging itself. Note it in
  `notes` as `self-eval`; prefer a standard benchmark or an independent
  device when weighing the verdict (habit: the gate reads the emitted
  artifact, not the producer's own state).
- **Two-sided calibration.** Does the experiment include a case that
  SHOULD fail (a control that isolates the mechanism) as well as the case
  that should succeed? Positive-only evidence gets `notes: one-sided` and
  cannot reach *leaning* on a `mechanism` claim.
- **Claim calibration.** "First / novel / record / SOTA" → rewrite as
  "authors claim better than X on metric Y under Z"; record what X was
  (their own prior work? a 10-year-old reference?) — the fairness of the
  comparison goes in `notes` and feeds Stage 2's rejection table.
- **Numbers carry their provenance.** Every number copied into the audit
  is tagged: `paper-measured` / `paper-simulated` / `re-derived here` /
  `unverified`. A number the reader re-derives (e.g. an FOM from BV and
  Ron) is `re-derived`, with the formula.
- **Reach traps in device papers** (axes as in `reach[]`): an E3 simulation
  row asserting `real-device`; one champion device asserting `generality`;
  "no significant change" read as `equivalence`; a fit to a trap model
  asserting `mechanism`; a sub-component test asserting `whole-system`.
  Each caps the row at the weaker verdict and names the axis in `missing`.
- **"Published ≠ worth building judgment on."** (B-4) Peer review is a
  floor, not a verdict. Say the venue; do not let it move a row.

## What did the paper actually DO? (B-4, fig 5)

Tick four boxes: new **framework**, new **term**, concrete **use case**,
**experiment or derivation**. Only the first two ticked → no claim in the
table may exceed *hypothetical*, and the key point should say so.

## Slop diagnostics (B-4, fig 8 — generalised from "AI slop" to any paper)

Flag, with a locator, when present:

- **term substitution** — the same concept renamed to look new (check
  against the field's standard term; consult `literature-search-extract`
  or LexiconVault if unsure). The input list is every `terms[]` row with
  `role: coined` from the Stage 0b glossary pass (`reading-method.md`);
- **framework stacking** — several models invoked with no mechanism joining
  them;
- **complete narrative, no verification** — every step explained, nothing
  measured that could have failed.

None of these is a verdict by itself; each lowers what the table may say.

## Row budget

`full` depth: 2–5 claims. `standard`: ≤ 3. `triage`: C1 only, verdict may
be left `withhold` with `missing: not audited (triage)`. More rows than
this is the audit refusing to rank — the point of the table is to say which
claim carries the paper.
