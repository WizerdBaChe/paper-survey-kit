# BUILD SPEC — paper-survey-kit: audit a paper's evidence, rebuild its story, present it

Audience: an agent (or a builder) who will install, adapt or rebuild these two capabilities. English.
The normative sources are the two skills under `reference-impl/skills/`; this spec is their contract
summary plus everything that is about the PACK (layout, environment, acceptance, declared edits).
Where this file and a `SKILL.md` disagree, the `SKILL.md` wins and this file has a defect.

## 0. What it is, in one paragraph

Two Claude Code skills that read one research paper in two different ways and share one run folder.
`paper-distill` judges the paper's EVIDENCE: IMRaD skeleton, a claim audit whose verdict words are
calibrated (provisional / leaning / hypothetical / withhold), figure cards that read the plot before the
prose, a writing-craft card, written as `cards.json` + a learning record. `paper-story` rebuilds the
paper's CONSTRUCTION: the axis (entry point, central claim, method choice, evaluation plan, presentation)
with a why on every item, the storyline as the authors told it, a drift table of where the telling
outruns the evidence (ten tell kinds, each row with a verbatim quote), and the key point as reusable
logic (a slogan plus bindings and warrants), written as `story.json`, then rendered to a practice
explainer page and, on request, a formal English deck on a template-free blank base. Every gate is a
script; nothing is judged by taste where a determinable check exists.

## 1. Components and who calls whom

| component | path | role |
|---|---|---|
| paper-distill | `reference-impl/skills/paper-distill/` | ingest (PDF / text / JATS → `source/`), probe (structure + anomalies), glossary, crop, units, verify_run, library |
| paper-story | `reference-impl/skills/paper-story/` | render_story (gates S1–S20 + explainer), story_explainer (story.json + cards.json → `explainer/1` content), verify_story (V1–V23, run by another session), lab_deck (formal PPTX, gates L1–L12) |
| carriers | `reference-impl/tools/carriers/` | `build.py`: content file `*.explainer.json` → stamped HTML (`html-explainer`) or PPTX (`pptx-explainer`); `check` says ok / unstamped / edited / stale |
| page-fill gate | `reference-impl/tools/page-fill-gate/` | measures how much of the viewport a built page fills (class `deck` / `document-long`), two-sided fixtures |
| machine roots | `reference-impl/hooks/_lib/roots.py` (+ `tree.py`, `hosts.py`) | reads `adapt/host.toml` or `HK_HOST_TOML`; every optional root may be `none` |

Call graph: `ingest.py` → run folder → (`probe`, `glossary`, `crop`/`crop_all`, `units`) → model authors
`cards.json` → `verify_run.py` → model authors `story.json` → `render_story.py` (gates, then
`story_explainer.py` → `tools/carriers/build.py build --carrier html-explainer`) → `verify_story.py` →
optional `lab_deck.py`. The two skills share `ingest.py`, `crop.py`, `library.py`.

## 2. Reading contract (normative; source: paper-distill SKILL.md, references/*.md)

- Read backwards: conclusion → abstract → figures → introduction → methods → body.
- Origin tag on every sentence: `[author]` (locator), `[verified]` (figure or table checked),
  `[inferred]`, `[assumed]`; numbers carry paper-measured / paper-simulated / re-derived / unverified.
- What a figure SHOWS comes from the rendered image (a crop or a page image), never from its caption alone.
- A locator or 「無法定位」 on every load-bearing statement; quotes verbatim.
- Verdict words are calibrated (`references/claim-audit.md`); `paper-story` quotes them, never invents its own.
- Self-built baselines are `self-eval`; positive-only experiments are `one-sided` and cap a mechanism claim at hypothetical.
- Premises are listed (`core.assumptions[]`), not absorbed.

## 3. Story contract (normative; source: paper-story SKILL.md, references/*.md)

- A why on every step: `axis.*.why`, `storyline[].why`, `logic.chain[].warrant` non-empty (S2 FAIL);
  a why that restates the what is empty.
- The key point is abstracted logic, not a summary: a slogan (`logic.keypoint`, no material names, no
  numbers) + a narrative reading (`keypoint_description`) + `bindings[]` mapping each role to this paper (S15).
- Every drift row carries the paper's own words in `quote`; S10 finds each quote verbatim in `source/paper.txt`.
- Coverage: every section, figure and table of `source/structure.json` is cited or named in `coverage.skipped[]` with a why (S11); every probe anomaly is classified (S12); the ten-kind drift checklist is declared found / none (S13).
- Two product classes, never converted into each other: class A `paper-explainer.html` (practice,
  readable, not presentable), class B `lab-deck.pptx` / `lab-onepage.pptx` (formal, English slides,
  explicit request only; `references/formal-deck.md`).

## 4. Run folder contract

`<PAPER_DISTILL_HOME>/<FirstAuthor><Year>_<slug>/`: `source/` (paper.txt with page markers, pages/pNNN.png,
images/, figures.json, structure.json, glossary-candidates.json, crops.json, units.json), `figures/`,
`cards.json` (schema `assets/cards.schema.json` in paper-distill), `reading-record.md`, `story.json`
(schema `assets/story.schema.json` in paper-story), `narrative-record.md`, `paper-explainer.explainer.json`
→ `paper-explainer.html`, `story-gates.txt`, optional `lab-deck.pptx`. The worked example is
`examples/library/Placeholder2026_wax-delay-bridges/`.

## 5. Gate design (applies to every gate here)

- A gate rules only on what it can determine; anything else is a WARN with its reason, never a veto.
- Two-sided calibration: each gate family has a selftest with a known-good input that must pass and a
  known-bad input that must fail (`render_story.py --selftest`, `lab_deck.py --selftest`,
  `build.py selftest`, `test_fill_gate.py`, `glossary.py --selftest`, crop.py's known-bad crop, ingest's
  caption control).
- The renderer persists the deck / page BEFORE its gates run; gates read the emitted file.
- `verify_story.py` and `verify_run.py` are run by a different session than the author.

## 6. Build order that worked

ingest → probe → glossary → crop_all → units → cards.json → verify_run → story.json → render_story →
verify_story → (lab_deck). N3 (logic extraction) only after the axis exists: extraction before the axis
produced summaries twice in the origin's calibration.

## 7. Acceptance (`verify/run_controls.py`; every line prints both asserted values)

| id | what | must pass | must fail |
|---|---|---|---|
| K1 | paper-story renderer selftest | `render_story.py --selftest` → SELFTEST PASS | (its own injected defects inside) |
| K2 | formal deck selftest on the blank base | `lab_deck.py --selftest` → SELFTEST PASS | (injected layout defects inside) |
| K3 | carriers selftest | `build.py selftest` → ALL PASS (asset comparison UNDETERMINED without the upstream asset) | hand-edit / stale controls inside |
| K4 | page-fill gate | `test_fill_gate.py` → PASS | known-bad fixtures inside |
| K5 | glossary and paper-distill unit tests | `glossary.py --selftest`, `pytest test_*.py` | — |
| K6 | example run: evidence audit | `verify_run.py` on the shipped run, 0 FAIL, V2 PASS | the same run with one quote altered → V2 WARN "not found verbatim" (WARN by design: a PDF text layer can be incomplete) |
| K7 | example run: story gates | `verify_story.py` on the shipped run, 0 FAIL | one `why` emptied → FAIL; one drift quote altered → FAIL |
| K8 | fictional paper is reproducible | `make_paper.py` twice → same text layer sha256 | — |

Visual acceptance (the explainer page and the deck as a person sees them) is a human check: see
`docs/DEVELOPER.md` 人工驗收.

## 8. Adapt to your environment (re-check before trusting)

- **Roots:** `hooks/_lib/roots.py` raises when no host file exists. Either copy `verify/host.toml` to
  `<config home>/adapt/host.toml` or set `HK_HOST_TOML`. Set `PAPER_DISTILL_HOME` to your paper library.
  The origin keeps its library inside a notes vault (`<NOTES_VAULT>/literature/PaperSurvey`) with a vault
  lint (`kv-lint.py`, not shipped); paths written `<PAPER_HOME>`, `<NOTES_VAULT>`, `<projects>`, `<share>`,
  `<work>`, `<media>` in the docs are the origin's folders.
- **Vault contract:** the skills ask that every `.md` in a run carries the origin vault's card frontmatter
  and passes its lint. Without a vault, keep the frontmatter or drop the rule; nothing in the scripts needs it.
- **Formal deck:** `lab_deck.py` defaults to `--base blank` here. With your own template, put two
  title-only decks in `<PAPER_HOME>/_templates/` and pass `--base template` (`references/formal-deck.md` §1).
  `--render` needs Windows + PowerPoint (COM).
- **Not shipped, referenced by the docs:** the origin's AssetVault (upstream of the carriers' vendor files
  and of the deck shell; `render_story.py --check-shell` compares against it), Retort & Rove (a reader of
  `units.json`), the origin's `rules/*.md` and `ops/` files cited in provenance lines.
- **Language:** class-A output is Traditional Chinese with English terms inline; slide text is English.
  Change the language in the content you author; the gates measure CJK-equivalent lengths.

## 9. Declared edits relative to the origin (everything else is byte-identical)

Origin = the author's `~/.claude` at the release date. `reference-impl/` keeps the origin's layout.
Not shipped: `paper-distill/evals/*` and `paper-story/evals/*` except the four control fixtures the code
reads, `paper-distill/archive/`, `carriers/samples/built/`, `__pycache__`. The list of unshipped origin
paths is `verify/unshipped_paths.txt`.

| id | where | what changed |
|---|---|---|
| E1 | `skills/paper-story/scripts/lab_deck.py` | the cover's advisor default is empty; `--base` defaults to `blank`; the comment naming the decks the origin's blank bases were derived from, and their folder, is replaced by a neutral line; a template logo's name is generalised; the default presenter name is `Presenter` |
| E2 | `skills/paper-story/SKILL.md`, `skills/paper-distill/references/design-rationale.md`, `skills/paper-story/references/talk-conventions.md`, `skills/paper-story/references/logic-extraction.md`, `tools/page-fill-gate/README.md`, `skills/paper-story/scripts/pptx_helpers.py`, `tools/carriers/pptx-explainer/vendor/deck_builder.py` | the name of the origin's research group and its project is replaced by "the presenter's own project" / "研究專案" / "an earlier research project" (dates kept) |
| E3 | `hooks/_lib/roots.py` | an example folder in a docstring generalised |
| E4 | `tools/carriers/pptx-explainer/CARRIER.md` | the recorded sha256 of `vendor/deck_builder.py` recomputed after E2 |
| E5 | `skills/paper-story/references/logic-extraction.md`, `skills/paper-distill/references/design-rationale.md` | two portability examples no longer name the origin research project's subject or its evaluation criteria ("another substrate's micro-mirror process", "your own project's choice"); the user's field is stated generically |
| E6 | `skills/paper-story/references/talk-conventions.md`, `skills/paper-story/references/presentation-formats.md`, `skills/paper-story/assets/story.schema.json` | every example sentence quoted from a labmate's talk notes is replaced by an invented sentence in the same register (the fictional paper's domain); the patterns, counter-examples and rules are unchanged and the file says so; a reference-deck folder name, a private analysis note's path and file name, and an opaque criterion id are removed |
| E7 | `skills/paper-distill/references/reading-method.md` | two provenance rows keep their sources (a public resource site, a public post) but drop the private file paths |
| E8 | `skills/paper-story/SKILL.md` | a pointer to the unshipped template reference written without its `.md` suffix now names `formal-deck.md` §4 |
| R5 | `tools/page-fill-gate/README.md` | the origin research project's internal folder and file names (its deck build gate, its dossier and discussion-pack tests, a scratch script) → what they are, marked not shipped |
| R1 | all text files | private machine folders → `<PAPER_HOME>`, `<NOTES_VAULT>`, `~/.claude`, `<projects>/`, `<share>/`, `<work>`, `<media>/` |
| R2 | all text files | the origin's lab-template reference is not shipped; every pointer to it now names `references/formal-deck.md` |
| R3 | all text files | labmates' and a conference speaker's deck names (used as style precedents) → "labmate deck A–E" / "deck F"; a school name in two CSS/JS comments → "course notes" |
| X1 | `examples/library/index.json`, `examples/library/Placeholder2026_wax-delay-bridges/_meta.json` | the example run's absolute library folder (written by `ingest.py` / `library.py`) → `<PAPER_DISTILL_HOME>`; `library.py` resolves entries by that path, so on your machine re-register the run (`library.py register`) before using library commands on it. The run's captions were re-checked and its figures re-cropped once the control fixtures were in place (`source/figures.json` `caption_check.controls = ok`; the re-cut crops are byte-identical) |
| O1 | `skills/paper-story/references/formal-deck.md` | NEW, written for this pack: the template-free replacement of the origin's lab-template reference (same section numbers; no template facts, people or paths) |

The edits are applied by the maintainer's refresh script, which also screens every shipped text file
against a private names list with planted positives; that script and the list are not shipped.
