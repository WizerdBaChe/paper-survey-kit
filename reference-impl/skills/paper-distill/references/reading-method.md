---
xi: 1
what: paper-distill 的閱讀協定——Stage 0–6 每張卡片要問的問題、要寫什麼、常見失敗；閱讀順序與簡報順序脫鉤 (the reading protocol behind the pipeline cards)
tags: [skill-reference, paper-distill, reading-method, imrad]
aliases: [讀論文方法, IMRAD 拆解, 結構檢查表, 三分鐘判斷, reading protocol, structure card]
date: 2026-09-02
status: live
---

# Reading method — the questions behind each card

Read this when running Stage 0–6 of `paper-distill`. Each stage is a CARD: a
fixed set of questions, an answer slot, and the failure mode the questions
exist to prevent. The questions are the transferable part — the user wants
to internalize them, so `reading-record.md` prints the question next to every
answer (`自問` lines), never the answer alone.

**Reading order ≠ deck order.** The pipeline reads backwards and by function
(Conclusion → Abstract → Figures → Introduction → Methods → body last); the
multi-page talk is a product organised AFTER reading, in the paper's own
section order (user ruling 2026-09-02, `deck-formats.md`). Nothing here
constrains how the deck is ordered, and the deck never dictates how to read.

## Provenance (borrow ledger)

The method is assembled from six public posts the user collected in
`<media>/分析` (post-brief records, 2026-09-02) plus the user's own reasoning
habits. Each borrowed part is named so a future reader can see what was
taken and what was changed:

| B-n | Source | Taken | Changed |
|---|---|---|---|
| B-1 | IG DahnbFTHP74 (2026-07-08) "NotebookLM 像研究者一樣讀" | IMRaD is a THINKING ORDER (question → design → findings → meaning), not a format; Method = tools/sampling/procedure/model; Results=What vs Discussion=Why; "why is this paragraph here?" probe; significance ≠ full claim; own-version-first ordering | Method's four elements re-mapped for device/photonics papers (§Stage 1) |
| B-2 | IG DclLP5SHNJ9 SHIP 003 Day 05 (2026-08-28) | Function-first identification; structure checklist (section × must accomplish × materials placed × my understanding); failure modes (nouns only / results only / method mistaken for conclusion) | The post's own "五步/four rows" label mismatch dropped; table kept at four rows |
| B-3 | IG DcvzXtiEdIe "四種模板" (2026-09-01) | Template 1 (3-minute triage), Template 2 (RQ/Methods/Results/Limitations → contribution), Template 3 (write FROM the paper — now Stage 5 craft), Template 4 (gap from Future Work + Limitations + cross-paper inconsistency), persistence (tagged/linked/versioned/searchable) | Template 2 asks only whether evidence exists — Stage 3 adds sufficiency; Template 3 promoted from a deck hint to a full stage after the user's OQ-3 ruling (learn to write) |
| B-4 | IG DciJ5PqHGTZ SHIP 003 Day 04 (2026-08-27) | Claim → evidence → level → what's missing → judgment table; four claim types; "what did the paper actually do"; slop diagnostics | Evidence KIND read as a matrix, not a ladder; verdict strength decoupled from evidence kind (`claim-audit.md`) |
| B-5 | IG DcAwx8FnDeF ATOMIC WRITING (2026-08-14) | Atomic essay: one idea, five sentences, ≤250 chars; structure before content; "can't write short = haven't thought it through"; write MY view; daily input / weekly rewrite = internalization | The essay is the reasoning trail behind the key point, not its slide form (`keypoint-rules.md`) |
| B-6 | IG Dbvd1RpkxDh PGY 職前加油站 (2026-08-07) | Read backwards (Conclusion → Abstract → Figures; body last); slides ≈ minutes × 1.5; ≥4 figures; ≥30 pt / ≤6 lines; per-chart "three things to look at" | Section weights REPLACED by the user's ruling (Methods and figure evidence up); chart checklists rebuilt for the user's fields (`figure-reading.md`); impression-management framing not adopted |
| B-7 | IG DcmugEmlLuv "Research Reading OS" (2026-08-29; post-brief 2026-09-03) | Read for the ARGUMENT, not the method; a paper = evidence of one possibility (verdict ceiling); Problem → **Assumption** → Storyline → Method; the research journey has a **Failure** beat (where they got stuck); 欣賞作者＋保留懷疑; read people not only papers (author lineage) | Assumptions → Stage 2 `core.assumptions[]` (evidence layer, this skill); Failure → `paper-story` `axis.method_choice.dead_ends`; 欣賞 → `learning.admire`; author lineage → Stage 6 `position.lineage` from the reference list only — NO author database (revisit when the ten-paper deck needs grouping or the library passes ~20 entries); the persuasion frame (Idea → Story → Evidence → Reader) is already Stage 5 `argument_chain` + the storyline — not duplicated |
| B-8 | IG Dc0UmGqE9UF SHIP 003 Day 07 (2026-09-03) | Read many fast before reading one deep; the depth table (relevance to my research × method weight × evidence depth → 精讀 / 掃讀); 推敲 (reproduce the method) before 琢磨 (one problem, many tools); a three-paper comparison card | The three axes become the Stage 0 q5 ruler (`intake.triage.depth_ruler`) with the post's two endpoint rows kept and the mixed cases ruled here (§Stage 0); 推敲 already = Stage 5 `methods_writing.missing_to_reproduce`; 琢磨 / research identity / 問題導向 vs 工具導向 are the user's OWN study → `scientific-research-guide`, not adopted here; the comparison card = `triage` depth ×3 + `library.py find` |
| B-9 | IG Dcw-nw0Grl1 SHIP 003 Day 08 (2026-09-02) | Three purposeful re-reads What → How → Why, each with a changed question; every layer leaves a text evidence AND an own judgment; the Why layer's counterfactual 「換一種方式會失效嗎」; the loop 選擇段落 → What → How → Why → 回到文本修正 | Mapped onto the existing stages as a REPLAY schedule (§Three purposeful re-reads), not as new cards — the stages already are the changed questions and the origin tags + 自問 lines already are the two per-layer deposits; the counterfactual → `paper-story` `axis.method_choice.necessity`; 回到文本修正 = `verify_run.py` by another session + drift vs C1 (exists) |
| B-10 | IG Dc0XR8aHJwm SHIP 003 Day 09 (2026-09-03) | First pass = the paper's own glossary: 10–15 recurring terms from title / abstract / intro, PDF-search frequency, four classes (主角 / 解釋框架 / 領域共用 / 本文特有), what is still unclear, what the second pass must ask | Frequency and first-appearance are bytes → `scripts/glossary.py` (Stage 0b); the class and the unclear column need an opinion → `terms[].role / unclear / ask_next`; the `coined` class is the input list for `claim-audit.md` term-substitution slop; highlight-in-PDF not adopted (the run folder's text layer + locators replace it) |
| B-11 | researcher.tw 資源庫 borrow review (the origin's borrow review, B-8 there) | A reference manager's PDF annotations are a reading input worth importing, not re-making | Imported, not authored here: `zotero_local.py --annotations` at ingest → `intake.marked[]`. B-10's "highlight-in-PDF not adopted" still stands for THIS skill's own reading; what is new is reading marks that already exist. Each mark carries an origin (owner / named / tool / external / unattributed) because the user expects an AI-assisted library to pre-annotate papers (ruling R4, 2026-09-14) — tool attention must never pass for the user's |
| B-12 | IG DcoRWkeDbKW 「學術表達的七層結構」 (2026-08-29; post-brief 2026-09-17) | The story line as ONE object with a question and a warrant on every link — 現象 → 缺口 → 假說 → 方法 → 結果 → 詮釋 → 貢獻; 「避免跳層」 as the one checkable rule (adjacent links with no sayable warrant) | Only the missing third link was adopted here: `craft.argument_chain[]` gains an optional `hypothesis` step and a `gap to next: unstated` note (`writing-craft.md`). The rest was already held — the seven questions ARE this skill's stages, and `paper-story`'s `storyline[].why` + `logic.chain[].warrant` already carry the reading-side story line (round 5's `brief` is its deliberate compression; not re-expanded). The post's vocabulary is econometrics (識別策略／識別假設／穩健性檢驗) and is NOT imported — the engineering equivalents are named in `scientific-research-guide` §6.8. The **production** direction (writing one's OWN paper so it is 通順 and 自洽) is the user's own study by the B-8 ruling → folded into `scientific-research-guide` §6.8 + `deliverables.md` T6c, not here (user reframe 2026-09-17: the core object is the story line, used in two directions) |

Habit sources (user's own): `~/.claude/CLAUDE.md` engineering-judgement block,
`memory/problem-first-ruling-decomposition.md`, `ops/30-judgment.md` R2, the
DIT project README (learning = denoised, decision-skeleton view).

## Two rules that run through every stage

1. **Origin tag on every written sentence.** `[author]` = the paper says it
   (quote or close paraphrase with a locator); `[verified]` = I checked it
   against a figure/table/equation in the paper; `[inferred]` = my reasoning
   from the paper's material; `[assumed]` = neither — flagged for the user.
   Author claims are never silently re-worded into facts; a "SOTA" becomes
   "authors claim better than X on Y under Z".
2. **Locator or "無法定位".** Every load-bearing statement points to
   `p.N`, `Fig.N`, `Table N`, `Eq.N`, or `§N`. If it cannot be located, say
   so in place — never drop it quietly. Quotes are verbatim (PaperLens BR-1);
   paraphrase is labelled paraphrase.

## Stage map

| Stage | Card | Output block | Detail |
|---|---|---|---|
| 0 | 取用卡 intake & triage | `source`, `intake`, `paper_says` | below |
| 0b | 詞彙表 glossary pass (first pass) | `terms[]` (`role`, `freq`, `unclear`, `ask_next`) | below |
| 1 | 骨架卡 skeleton | `skeleton` | below |
| 2 | 核心卡 core | `core` | below |
| 3 | 主張審計 claim audit | `claims[]`, `did` | `claim-audit.md` |
| 4 | 圖表判讀 figure cards | `figures[]` | `figure-reading.md` |
| 5 | 寫作解剖 writing craft | `craft` | `writing-craft.md` |
| 6 | 定位卡 positioning | `position` | below |
| 7 | Key point | `keypoint` | `keypoint-rules.md` |
| 8 | 口述稿・渲染・歸檔 | `talk`, `learning`, `deck_hints` + files | `output-spec.md` |

## Stage 0 — Intake & triage card (取用卡)

Questions, in this order (B-3 Template 1, then B-6's presenter twist):

1. What problem does the Abstract say it solves? (one line)
2. What does the Conclusion claim? (one line — this is the claim the rest of
   the reading will TEST, not a summary to accept)
3. What contribution does the Introduction announce, and why does it matter
   to the authors?
4. Flip through the figures once. Which ONE figure would the authors point
   at if allowed only one? Note its number.
5. Decision: `deep` / `skim` / `archive`, and why — for a presentation run
   the decision is given (`full` or `standard` depth), so write the reason
   the paper was picked instead (`why_this`). The "why" is not free text: score
   the three axes of the depth ruler (B-8, Day 07 card 7) as `intake.triage.depth_ruler`
   and let them carry the decision —

   | axis | high | low |
   |---|---|---|
   | `relevance` — to MY research question | core problem, touches a named project | peripheral, background only |
   | `method_weight` — how much the method decides the result | complex, or a design choice the result hinges on | standard flow, little influence on the result |
   | `evidence_depth` — how much the evidence can bear | enough devices / wafers / runs, rigorous analysis, direct | few samples, thin analysis, indirect |

   The post gives only the two endpoint rows (all high → 精讀; all low → 掃讀).
   Mixed cases, ruled here: `relevance` low → `skim` whatever the others say
   (attention follows the question, not the paper's quality); `relevance` high
   with `evidence_depth` low → still `deep`, but the audit's verdicts will cap
   what may be borrowed — say so in `reason`; `relevance` high with
   `method_weight` low → `deep` at `standard` depth (the Methods pages have
   little to teach). Write the three scores even when the decision was given.
6. Lab relevance in one line: which of our projects/questions does it touch
   (use `scientific-research-guide` domain profiles when the field matches;
   name the profile from `domains/_routing.md`).

Write also: source type (paper / preprint / patent / techdoc / popsci /
other), access tag (`full` / `partial` / `abstract`), metadata (title,
authors, venue, year, DOI/URL), language, and the verbatim abstract.

**Marks already on the PDF (B-11).** A PDF ingested from the Zotero library
arrives with its annotations and child notes in `intake.marked[]`, each with an
`origin`. Read them AFTER the six questions, never before — a highlight says
what someone noticed; the questions ask what the paper claims. Then:

- `owner` (made in Zotero, no author name) is presumed the user's own attention:
  a highlighted figure is a candidate for q4, a comment a candidate for
  `why_this`. Confirm with the user; do not assume.
- `named`, `tool`, `external` are someone else's attention — another reader, an
  AI pre-annotator, whatever wrote into the PDF file. They say where to look;
  they never stand in for the user's pick and never count as evidence.
- A tool that writes into Zotero WITHOUT a name cannot be told from the user: its
  marks arrive as `owner`. When the user says a tool marked this PDF, read every
  `owner` mark as tool attention for this run and say so in the record; a tool
  that signs its marks goes into `annotation_tool_authors`
  (`literature-search-extract/connectors/registry.json`) so the next ingest tags
  them `tool`.
- `unattributed` child notes are context; quote one as the user's own only when
  the user says it is.
- A mark's text becomes a quote only once it is found verbatim in
  `source/paper.txt`; its `locator` is the PDF's page LABEL, not the index.
- Fill `used_in` on every mark (the field it seeded, or `unused: <why>`), so a
  later reader can tell imported attention from this reading's own.

`intake.marked` absent means nothing was imported; `[]` means the library was
checked and the PDF is unmarked — neither is a finding about the paper.

Failure mode prevented: spending an hour on a paper before knowing what it
claims; reading the body as a tour instead of as a test. Time box: 3 minutes
of reading before anything is written.

## Stage 0b — Glossary pass (詞彙表): the first pass builds the paper's vocabulary

B-10 (Day 09): the first pass is not for understanding; it is for finding the
paper's recurring terms so the second pass does not enter the text empty-handed.
A term that keeps coming back is either the paper's subject or the word it is
building its narrative on.

1. Run `python scripts\glossary.py --run <run_dir> --print` — counts every
   recurring 1–3-gram in `source/paper.txt`, weights title / abstract / intro
   hits, lists acronyms with their expansions. Bytes only; the ranking is an
   input, not a verdict (a CJK text layer is reported as unreliable).
2. Keep 10–15 terms (the post's number; more is a summary of the paper, fewer
   misses its frame). For each, fill in `cards.terms[]`:
   - `role` — `subject` 主角 (what is studied) · `frame` 解釋框架 (what explains
     the subject) · `field` 領域共用 (the field's shared vocabulary) · `coined`
     本文特有 (a term this paper introduces or redefines);
   - `freq` — the count from the script; `gloss` — one or two sentences, Wikipedia-
     preview register (paper-story renders the hover from this);
   - `unclear` — what I do not yet understand about it; `ask_next` — the question
     the second pass (Stage 1–3) must answer about it.
3. Every `coined` term goes to `claim-audit.md` slop diagnostics as the input list
   for term substitution: is it a new concept, or the field's concept under a new
   name? A paper whose only novelty is its coined terms is caught at Stage 3
   (`did`: framework / term only).

Failure mode prevented: the first read stalling on unknown words and turning into
a tour; the glossary that never gets written because "I'll do it at the end".
Not adopted from the post: highlighting in the PDF — the run folder's text layer
plus locators is the durable form of the same act.

## Stage 1 — Skeleton card (骨架卡): IMRaD as functions

IMRaD is the order a study THINKS in: ask → design → find → mean. The four
parts have different functions and cannot substitute for each other. Read a
section by asking which function it performs before reading its details.

| Section | What it must accomplish | What materials the author placed | What I understand now |
|---|---|---|---|
| Introduction | establish the problem: **problem / prior work / gap** (all three must be visible) | … | … |
| Methods | make the study repeatable: **tools · sampling · procedure · model** | … | … |
| Results | report findings — WHAT, objective, no interpretation | … | … |
| Discussion | interpret — WHY, meaning, limits, connection | … | … |

Method's four elements for device / photonics / materials papers:

| Generic (B-1) | Device / photonics reading |
|---|---|
| tools | structure & fabrication (epi, process, geometry), instruments |
| sampling | which devices/wafers/how many; test-structure vs product; selection criteria |
| procedure | measurement conditions (DC/pulsed, temperature, bias sequence, calibration, de-embedding) |
| model | simulation setup (solver, mesh, boundary, calibrated to what), analytical model, extraction method |

Two probes: **anomaly** — "why is this paragraph HERE?" (a method-like passage
in the Introduction, results in the Discussion, a limitation buried in the
Methods: name each and what its placement tells you — usually where the
argument is weakest); **What/Why separation** — list any Results sentence
that interprets and any Discussion sentence that introduces new data.

Non-IMRaD sources map onto the same four functions:

| Source | I | M | R | D |
|---|---|---|---|---|
| patent | background + problem | embodiments / how implemented | claims (what is protected) | advantages, alternatives, scope |
| tech document / datasheet | application context | conditions & test method | spec tables, curves | notes, derating, limits |
| popular-science article | hook / question | (usually absent — flag) | the claim | implication / hedge |
| short conference paper (2–4 pages) | one paragraph | often merged with results — split them yourself | figures carry everything | one paragraph or none — flag |

Failure modes prevented (B-2): recording nouns only; copying results only;
mistaking the method for the conclusion.

## Stage 2 — Core card (核心卡): how does the study hold up?

Four corners converge on the claimed contribution (B-3 Template 2): **RQ**,
**Methods**, **Results**, **Limitations**, then **Contribution (claimed)**
`[author]`. Then two answers in your own words: **how does this study hold
up?** and **what is missing?** — write the question the audit must settle,
not the verdict.

Related work as a rejection table (user habit: rejected options matter more
than the chosen one): `prior method | what the authors say is insufficient
about it | is that fair? [inferred]`. A paper that beats a strawman is
caught here.

**Assumptions (前提盤點, B-7 card 07 — Problem → Assumption → Storyline → Method).**
List the premises the paper accepts as true without testing them:
`core.assumptions[] = {premise, where, tested, if_false, origin}`. `where` is a
locator when the paper states the premise (usually one clause in the
Introduction or Methods: "assuming geometric optics holds", "the process is
uniform across the wafer") and `implicit` when it never does; `tested` is
`yes / partly / no / unknown`; `if_false` names which claim rows or chain steps
fall with it. Two to five rows. This is the cheapest lever the audit has: a
claim can be perfectly supported by its figures and still rest on a premise
nobody checked — Stage 3 then records that row's `missing` as the untested
premise, and `paper-story` cites the row in `drift` (a why resting on an
`[assumed]` premise) and in `logic.fragile`. Written in the user's own
premise discipline (P-env / P-intent / P-validity, `ops/05-authority.md` §4.0):
a premise the reader cannot verify is marked, never silently accepted.

## Stage 3 — Claim audit → `claim-audit.md`

## Stage 4 — Figure reading → `figure-reading.md`

## Stage 5 — Writing craft → `writing-craft.md`

## Stage 6 — Positioning card (定位卡)

Three gap sources (B-3 Template 4): **Future Work**, **Limitations** (from
Stage 2), **cross-paper inconsistency** (consult the library index; cite the
run id). Then: which important questions remain unanswered? which methods or
angles could go further? how could OUR research fill it?

Relevance block — this is where "so what for us" lives (NOT in the key
point, `keypoint-rules.md`):

- `relevance` — why our lab should care, one sentence, naming the project
  or standing question it touches.
- `borrow` — what is worth taking (a method, a test structure, a figure
  style, a benchmark table, a definition, a sentence pattern from Stage 5).
- `not_borrow` — what looks attractive but should not be taken, and why.

Lineage (`position.lineage`, B-7 cards 08–09 — read people, not only papers):
three one-liners taken from the reference list, not from a search —
`group_prior_work` (the authors' own earlier papers this one stands on; Ow 2010's
Ref 15–19 are its toolchain, and the entry-point why already used them),
`who_else` (the other groups the Introduction positions against), `community`
(which conference / journal community this belongs to). The library index then
answers "what else did this group do" by grep. Not built: an author database or
a network view — the post's Author Network is a cross-paper object with no owner
yet; revisit when the ten-paper deck needs its papers grouped, or when the
library passes ~20 entries and grep stops being enough.

Stop rule (user: 不要為了做而做): if the run's question is already answered,
do not mine the extension sections for completeness; write "not needed for
this run" and move on.

## Three purposeful re-reads — What / How / Why as a replay schedule (B-9)

Day 08's rule: 精讀不是反覆看，而是每次重讀都換問題; each layer leaves one text
evidence and one own judgment. The stages above already ARE the changed
questions, and the origin tags + 自問 lines already are the two deposits — so
the three layers are not new cards; they are the order in which the user
REPLAYS a run (first read, a week later, before the talk):

| Layer | Question | Stages that hold it | The deposit it must leave |
|---|---|---|---|
| **What** 頁面上有什麼 | what is on the page — problem, claim, evidence, elements, vocabulary | 0 intake · 0b glossary · 1 skeleton · 4 figures (`shows`) | `[author]` lines with locators; the glossary |
| **How** 作者如何把問題做出來 | can I re-walk the reasoning: question → method → procedure → result | 2 core · 3 claim audit · 5 craft (`argument_chain`, `methods_writing`) · `paper-story` beats ③④⑤ | `[verified]` lines; the audit table; the design-data table |
| **Why** 為什麼一定要這樣 | why this entry point / method / evaluation; 換一種方式會失效嗎; 破綻; 改良 | `paper-story` axis whys + `necessity` + `dead_ends` · N3 logic (`fragile`, `portable`) · 6 positioning · `core.assumptions` | `[inferred]` lines; the key point; `borrow / not_borrow` |

Replay rule: a re-read that keeps the previous layer's question is a repeat
(the post's 看三遍 loop) — the self-check questions in §8 are written one per
layer for that reason. The post's closing loop (選擇段落 → What → How → Why →
回到文本修正) is what `verify_run.py` by another session + `paper-story`'s
drift-vs-C1 check already do; nothing added.

## Significance ≠ licence to claim (B-1, fig 8)

A significant result still needs: sample size (how many devices / wafers /
runs), uncontrolled variables (temperature, process drift, measurement
sequence), and the range the result generalises to. A device paper's version
of `p < 0.05` is "the best device" — ask whether the figure shows one device
or a distribution. If the authors don't hedge, hedge for them and say so.

## Practice loop (B-1, B-5)

The tool builds a practice field; it does not think for the user. Every
`reading-record.md` therefore carries the `自問` line before each answer, a
"your version first" box at Stage 7 (the user writes their key point BEFORE
opening the model's), and three self-check questions the user should be able
to answer from memory a week later.
