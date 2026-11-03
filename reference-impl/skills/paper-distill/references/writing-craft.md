---
xi: 1
what: paper-distill Stage 5 寫作解剖——從一篇論文學怎麼寫論文：論證鏈、方法段怎麼給資料、圖證怎麼設計、結果與限制怎麼措辭、可借句型 (the writing-craft lens: learn to write a paper from the paper being read)
tags: [skill-reference, paper-distill, writing-craft, methods, figure-design]
aliases: [寫作解剖, 從論文學寫論文, 方法段怎麼寫, 圖證設計, argument chain, sentence patterns, craft card]
date: 2026-09-02
status: live
---

# Writing craft — read the paper as a piece of writing

Stage 5 of `paper-distill`. User ruling 2026-09-02 (OQ-3): the ultimate purpose
of PaperSurvey is that the user learns to WRITE a complete paper, so Methods
and the figure evidence (results and design data) carry MORE weight than a
journal-club reading would give them. This card records what the paper teaches
about writing, with locators, so the multi-page talk and the user's own future
manuscript can lift it.

The reading order stays decoupled from any deck order: this card is filled
after the audit and the figure cards (the craft of a figure is only visible
once you know what it had to prove).

## `craft` block — what to fill

| Field | Question | Fill rule |
|---|---|---|
| `argument_chain[]` | how does the paper move from problem to claim? | 4–7 steps: `problem → gap → hypothesis → approach → evidence → claim (→ implication)`; each step = one sentence in my words + the locator of the sentence that does that job in the paper `[author]`. `hypothesis` (why the authors EXPECTED this to work — the theory, physical model or mechanism the approach is derived from) is the step most often absent: a paper that states none is recorded as `hypothesis: none stated`, which is a finding about its argumentation, not a gap in mine. Distinct from `core.assumptions[]`, which holds what the paper takes as true WITHOUT testing. **Adjacent steps with no sayable warrant between them = a skipped link** — record it in the same row (`gap to next: unstated`) rather than inventing the bridge (B-12) |
| `methods_writing.given` | what does the Methods section actually hand the reader? | list the design data as GIVEN: geometry (with numbers), materials, process steps and their parameters, instruments, measurement conditions, simulation settings — everything a reader would need to reproduce |
| `methods_writing.missing_to_reproduce` | what would I still have to guess? | name it plainly (e.g. etch recipe, anneal profile, mesh size); this is the lesson "what NOT to leave out" |
| `methods_writing.order` | in what order do they present the method, and why does it work (or not)? | one line |
| `methods_writing.design_data` | the numbers a designer would copy | table-like line: parameter = value (unit) `[author]` with locators — this is what the lab actually reuses |
| `figure_design[]` | one row per load-bearing figure: what was it DESIGNED to prove, why this chart type, how are panels arranged, what is labelled, what is deliberately absent | the reverse of Stage 4: not "what does it show" but "how was it built to show it" |
| `results_writing` | how are numbers reported — with uncertainty? n? comparisons to what baseline? how are figures referenced in prose? | one paragraph, with an example locator |
| `limitations_writing` | how do they phrase limits and hedges — where, how long, how honest | one paragraph; note if limits are absent. Also sort what they call limits: a real boundary (constraint → which claim it bounds → what may not be concluded) vs a fixable defect dressed as a limit vs generic caution with no boundary (`~/.claude/references/writing-norms/claim-reach.md` §2) — the sort is the lesson for our own Limitations section |
| `sentence_patterns[]` | sentences worth borrowing as PATTERNS | ≤ 5 items, each ≤ 15 words verbatim in quotes + locator + "use for": the move it performs (gap statement / contribution claim / hedge / figure lead-in / comparison) |
| `my_rewrite` | practice | rewrite ONE paragraph (usually the gap statement or the main-result sentence) in my own words, planned first per `~/.claude/references/writing-norms/paragraph-plan.md` §1, then note what changed — optional at `standard` depth, expected at `full` |

## How this feeds the other outputs

- **Reading record §6** prints the card with the 自問 lines above it.
- **Deck hints** (`deck_hints.page_plan`): Methods pages carry
  `methods_writing.design_data` and the process figure; Results pages carry
  one figure each with `figure_design` beside the Stage 4 三件套. Default
  weights (user ruling): Methods 3–4 pages, figure evidence 4–6, Introduction
  1–2, Discussion 2–3, Conclusion 1, key point slide first, 對我們 last —
  in the PAPER'S OWN section order (`deck-formats.md` §3).
- **Talk script**: the 方法怎麼做 section of `talk` speaks
  `methods_writing.given` in plain words, and the 圖怎麼走 section speaks
  `figure_design` + Stage 4 `look_for`.

## Copyright and honesty

Sentence patterns are quoted short (≤ 15 words) with locators; everything
else is paraphrase marked `[author]` or my reading marked `[inferred]`. A
paper that gives no design data is recorded as such — "design data: none
given (p.N)" is a finding about the paper's writing, not a gap in mine.
