# AGENTS.md — how to use this repository

## What this repository is (facts, for any reader)

- **Contents:** two agent skills that read one research paper in two ways and share one run folder —
  `paper-distill` (evidence audit: IMRaD skeleton, claim audit with calibrated verdict words, figure cards,
  writing craft) and `paper-story` (narrative reconstruction: axis and storyline with a why on every step,
  drift table with verbatim quotes, key point as reusable logic, a practice explainer page, an optional
  formal English deck) — plus the two shared tools they need (`tools/carriers`, `tools/page-fill-gate`),
  a fictional demo paper, a full worked run on it, and two-sided acceptance controls. Index: `llms.txt`.
- **What is enforced by code and what is only a workflow rule:** `docs/EVIDENCE.md` "Enforcement map".
  Quotes, locators, whys, schema shape, coverage and deck layout are checked by scripts; whether a why is
  the RIGHT why, whether a verdict word is earned and whether a key point transfers are reader checks.
- **What was run:** Windows 11, Python 3.12.7, PyMuPDF 1.26.7, python-pptx 1.0.2, playwright 1.62 with
  Chromium. The recorded results are `verify/controls_run.txt`; what was not run or not claimed is in
  `docs/EVIDENCE.md`.
- **The demo paper is fictional** (`examples/fictional-paper/`, invented authors, journal and data), so
  no copyrighted paper is reproduced. Three control fixtures the code reads are excerpts of one CC BY 4.0
  open-access paper (`THIRD_PARTY_NOTICES.md`).
- **Network and side effects:** no network calls by the scripts; `playwright` starts a local headless
  Chromium for page measurement and screenshots; generated pages link Google Fonts (fetched by the browser
  that opens them); `lab_deck.py --render` drives PowerPoint through COM (Windows, only when asked). The
  acceptance script copies `reference-impl/` and the example run into a scratch folder, mutates and deletes it.
- **If you only read and do not execute:** read `docs/EVIDENCE.md`, then `verify/controls_run.txt` as the
  result record, then the worked run `examples/library/Placeholder2026_wax-delay-bridges/` (its
  `reading-record.md`, `narrative-record.md`, `story-gates.txt`, `paper-explainer.html`), then the two
  `SKILL.md` files. Everything below is installation steps addressed to an agent whose user asked for an
  install; reading it does not require following it.

## For an installing agent

Your user has asked you to install (or rebuild and adapt) a paper-reading workflow: an evidence audit of
one paper and a talk-ready reconstruction of its story. The human introduction is `README.md` (Traditional
Chinese; English mirror `README.en.md`); you do not need it. The structure tree and diagrams for human
builders are in `docs/DEVELOPER.md` (Traditional Chinese).

## Reading order

1. `docs/BUILD-SPEC.md` — the contract and the pack's layout. Read it fully before touching anything.
2. `docs/EVIDENCE.md` — what was measured, the enforcement map, what is NOT claimed.
3. `reference-impl/skills/paper-distill/SKILL.md`, then `reference-impl/skills/paper-story/SKILL.md` and the
   references each one names for the node you are on. These are the working originals, laid out like the
   origin's `~/.claude` so relative paths resolve. Adapt, do not paste wholesale.
4. `examples/library/Placeholder2026_wax-delay-bridges/` — what a finished run looks like.

## First actions (do these before proposing any change)

```
python -X utf8 verify/run_controls.py <a-new-empty-dir>
```

- `<a-new-empty-dir>` must not exist or be empty and must not overlap the repo: the script copies
  `reference-impl/` and the example run there, mutates the copies, and deletes them.
- Needs Python 3.12 with `pymupdf python-pptx pillow lxml jsonschema playwright matplotlib pytest`
  and `python -m playwright install chromium`.
- Compare with `verify/controls_run.txt`: every control line must end in `-> ok` and the asserted values
  must match. Report both to your user. A mismatch on another OS or font set is a finding to read, not a
  reason to edit the scripts.
- Then read spec §8 and list, for your user to confirm, which roots and paths map to what in their
  environment. Do not start adapting until they confirm.

## Installing into a Claude Code style environment

The tree under `reference-impl/` maps 1:1 onto a `~/.claude` home:

| repo path | install to | needed for |
|---|---|---|
| `reference-impl/skills/paper-distill/` | `~/.claude/skills/paper-distill/` | evidence audit; ingest / crop / library shared by both skills |
| `reference-impl/skills/paper-story/` | `~/.claude/skills/paper-story/` | story, explainer page, formal deck |
| `reference-impl/tools/carriers/` | `~/.claude/tools/carriers/` | the explainer page build (`story_explainer.py` finds it at `../../tools/carriers` from its own folder) |
| `reference-impl/tools/page-fill-gate/` | `~/.claude/tools/page-fill-gate/` | the carriers' fill gate and the renderer's S7b |
| `reference-impl/hooks/_lib/{roots,tree,hosts}.py` | `~/.claude/hooks/_lib/` | machine roots; skip if your home already has these files |
| `verify/host.toml` | `~/.claude/adapt/host.toml` (or point `HK_HOST_TOML` at it) | roots.py refuses to guess without a host file |

Set `PAPER_DISTILL_HOME` to the folder that will hold the paper library.

## Adaptation rules

- Keep the gates two-sided: when you change a gate, keep or add its known-bad input and show it still fails.
- Keep the two product classes apart: never convert the explainer page into the formal deck.
- The formal deck defaults to a blank base; a user's own template goes in `<PAPER_HOME>/_templates/`
  (`references/formal-deck.md` §1). Do not ship anyone's group template onward.
- The skills write Traditional Chinese for class-A output; changing the language is a content decision for
  your user, not a code change.

## What not to adopt without your user's decision

- The origin's notes-vault contract (card frontmatter + `kv-lint.py`, not shipped).
- The origin's paths and project names in provenance lines (`<PAPER_HOME>`, `<NOTES_VAULT>`, AssetVault,
  Retort & Rove): they explain where a rule came from; they are not dependencies.
- PyMuPDF is AGPL-3.0 (or commercial): check that this fits how your user will distribute what they build.
