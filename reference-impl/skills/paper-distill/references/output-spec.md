---
xi: 1
what: paper-distill 產出契約 v1.2（拆分後，證據層）——vault 內的文獻庫與 run 資料夾、reading-record.md、cards.json、驗收 (output contract of the evidence-layer skill after the 2026-09-03 split)
tags: [skill-reference, paper-distill, output-spec, contract]
aliases: [產出規格, cards.json 契約, 文獻庫佈局, reading-record, run folder, evidence layer]
date: 2026-09-03
status: live
---

# Output contract (v1.2 — evidence layer)

After the 2026-09-03 split this skill writes the LEARNING RECORD and the EVIDENCE
CONTRACT only. Presentation products (one-page, deck, talk script, key point) are
`paper-story`'s and live beside these files in the same run folder.

## 1. Library and run folder — inside the Obsidian vault

Root: `PAPER_DISTILL_HOME`, default `<PAPER_HOME>` (vault
ruling R5). Every `.md` written here obeys the vault note contract
(`<NOTES_VAULT>\AGENTS.md` §2; `kind: literature` for run notes, `topic-map` for
the library README) and `kv-lint.py` must report 0 FAIL. Wings are never written.

```
<home>/
  index.json · README.md              library index (library.py; README = one row per PAPER + a 校準紀錄 section; topic-map note)
  KEYPOINTS.md                        論文核心邏輯快速關聯索引 (library.py; every accepted paper's slogan / reading / logic patterns, wikilinks)
  <PaperId>/                          <FirstAuthor><Year>_<short-title-slug> — ONE accepted run per paper (naming over routing, 2026-09-04;
                                      before: YYYYMMDD_<author><year>_<slug>, one folder per ingest event, calibration copies as siblings)
    <PaperId>_keypoint.md             per-paper keypoint note generated from story.json (slogan, 解讀, role table, #logic/<pattern> tags, relations)
    _meta.json                        ingest metadata (+ previous_ids after a migration)
  _calibration/<PaperId>/<label>/     comparison / calibration copies (run.id = <PaperId>__<label>; labels say what the copy IS: sonnet-B, blind-Y, from-scratch-Z, story-mode-S1)
    source/                           paper.pdf · paper.txt (<!-- p.N --> markers; .txt so the vault lint ignores it) · pages/pNNN.png · images/ · figures.json
                                      · crops.json (crop_all.py) · units.json (units.py) — §1a; Retort & Rove reads these two
    figures/                          crops (crop.py; a --caption crop is the figure only, caption excluded, since 2026-09-26); shared with paper-story
                                      F<n>/T<n>.png = crop_all.py's; _previous/<tag>/ = the files it replaced
    cards.json                        the evidence contract (assets/cards.schema.json v1.2)
    reading-record.md                 【學習紀錄】the learning document
    story.json · paper-explainer.html (its 口述稿 section is the talk script) · narrative-record.md   ← paper-story's, when it ran
                                      (older runs may still hold onepage.html · talk-deck.html (before 2026-10-12) or a talk-script.md
                                      (before 2026-11-03) — historical, no longer written)
```

`source/figures.json` → `captions[]`: `{page, kind, label, num, bbox, caption, caption_ok[, caption_fault]}`.
`caption` is the whole PDF text block that starts with the label, whitespace-normalised — never cut to a length.
`caption_ok: true` = verbatim in `paper.txt` and ends a line there; `false` names why in `caption_fault`; `null` =
the check's controls misfired and no verdict was given (`caption_check.controls` says why). Only `true` may be quoted
as verbatim. Runs ingested before 2026-09-26 have no `caption_ok`, cut every caption at 160 chars, miss captions
whose label stands alone on its first line (Tran 2018 Figure 2) and may list a body sentence ("Figure 7 shows …") as
an anchor: take their captions from `paper.txt`.

## 1a. `source/crops.json` and `source/units.json` — the verbatim layer (since 2026-09-27)

Written for Retort & Rove (user ruling 2026-09-27: paper-distill extracts, the reader only reads; card WC-06 in
`<projects>/RetortAndRove\docs\cards\`). Both are derived from `paper.pdf` + `figures.json` and are rewritten
whole by their script; nothing else writes them.

`crops.json` (`paper-distill/crops@1`, `crop_all.py --run <run> --apply`): `{schema, tag, crop_py, moved[],
results[]}`. One result per target: `{caption_index, label, kind, num, page, name, file, exit, result, error}`,
`result` = crop.py's own JSON (`rect_pt`, `gate.verdict`). Target naming: the first caption of a `(kind, num)` →
`F<num>`/`T<num>`; a later one on another page (a continued table) → `<name>_p<page>`. A gate FAIL keeps its file;
the verdict is data, never retried by hand. Other files in `figures/` (paper-story variants `F3a`, `F9F11`, `deck/`,
names like `S1`) are never touched; replaced files go to `figures/_previous/<tag>/`.

`units.json` (`paper-distill/units@1`, `units.py --run <run> [--check] [--twice]`; needs `crops.json`):

| key | content |
|---|---|
| `source` | `pdf_sha256`, `pages`, `pymupdf`, `body_font_size`, `body_font`, `indent_paper`, `indent_votes`, `front_matter`, `probe_headings_not_taken[]` (`{id, line, text, why}` — probe.py headings rejected by a guard), `skipped_whitespace_lines` |
| `units[]` | reading order. `{id, kind, section, page, lines[], raw, text, fixes[]}`. `id` = `p<page>-y<int y0>-x<int x0>` of its first line (`-2`, `-3` on a collision); `lines` = `[page, block, line]` PyMuPDF refs; `raw` = the lines whitespace-collapsed, joined by one space, no space after a line-end hyphen; `text` = `raw` with `fixes` applied |
| kinds | body: `abstract`, `heading`, `paragraph`, `caption`, `reference_list` (one unit). Non-body: `title_block`, `figure_text`, `table_region` (inside a crop rect), `backmatter` (acknowledgments, funding, licence blocks, …), `note` (all lines smaller than body − 0.9 pt: footnotes, formula fragments) |
| `fixes[]` | `{kind: ligature\|dehyphenation, at: [i, i+1], raw, fixed}` offsets into `raw`; replaying them in order must give `text` exactly (`checks.replay_mismatch`). A line-end hyphen is removed only when the paper itself writes the joined word more often than the hyphenated one |
| `removed[]` | `{kind: header_footer\|page_number, line, raw}` — running heads (80 pt edge zone + the same digit-folded text on ≥ 3 pages) and page numbers |
| `figures[]` | per figures.json caption: `{label, kind, num, page, caption_unit, caption_ok, file, gate, rect, text_units[]}` |
| `checks` | `lines_total/in_units/removed`; `unaccounted`, `double`, `unknown` (every PDF line in exactly one place); `replay_mismatch`; `foreign_hits[]` (`class` = the reason from `evals/units-allow.json`, else null); `lowercase_start`, `no_terminal_end` (paragraph proxies, advisory); `two_column_pages`, `order`; `headings_match` (vs `structure.json`, minus the not-taken); `chars`, `figure_text_suspect`, `soft_hyphens`; `controls` (each check's positive + negative control) |

`--check` exits 1 on any hard failure: a line unaccounted/double/unknown, a replay mismatch, an order violation,
headings ≠ structure.json, a foreign hit not in `evals/units-allow.json`, or a control that is neither `ok` nor
`n/a`. `--twice` builds twice and requires byte-identical output. The allow file lists hits a human read and found to
be genuine source text (a same-journal citation that matches the running head after digit folding); adding an entry
is a review act, never a way to make a run pass.

A run with `source_kind` `text` or `jats` (`ingest.py --text/--jats`, `_meta.json`) has no `paper.pdf` and no `crops.json`
(`crop_all.py` skips it with a message, so figures are listed in `figures.json`, never cropped). Its `units.json` is built
from `paper.txt` + `structure.json` + `figures.json`: `source` = `{source_kind, paper_txt_sha256, lines, paragraphs,
front_matter, header_footer_rule, skipped_blank_lines}`; a unit has `page: null`, `line` (first line of `paper.txt`) and
`lines` = `[[n], ...]`, id `L<line>`; `figures[]` have `page: null`, `line`, no crop `file`/`gate`/`rect`. JATS: one line = one
paragraph. Plain text: paragraph breaks, running heads (a line repeated ≥ 3 times with ≥ 12 letters) and figure-tick runs
(`figure_text`: ≥ 3 consecutive numeric fragments) are heuristics; tables are not separated from the body. `checks` add
`structure_unresolved` (a `structure.json` unit whose `line` does not hold its text; a hard failure) and have no two-column
check (`controls.order` = `n/a`). `verify_run.py` on such a run: V3's page half is `SKIP`, a cited `§N` must be a
`structure.json` unit id (V3 FAIL otherwise), V13 checks that the units' `line`s resolve.

Known limits (eval `evals/source-units-7papers-2026-09-27.md`): display formulas split into `note` fragments or stay
inside the paragraph; author biographies after the references stay in `reference_list`; probe.py's false headings
stay in `structure.json` (units.py only declines them).

## 2. `cards.json` — field map and who consumes it

| Block | Written at | Consumed by |
|---|---|---|
| `run`, `source`, `intake`, `paper_says` | Stage 0 | index; paper-story (source, abstract) |
| `skeleton`, `core` | Stages 1–2 | record §2–§3; paper-story Method/Intro pages |
| `claims[]` (incl. `reach[]`), `did` | Stage 3 | record §4; paper-story `drift` cites verdicts and an `over-claim` drift names the `reach` axis it crossed (axes: `~/.claude/references/writing-norms/claim-reach.md`) |
| `figures[]` | Stage 4 | record §5; paper-story figure captions |
| `craft` | Stage 5 | record §6; paper-story Method pages (design data) |
| `position` | Stage 6 | record §7; paper-story 對我有什麼幫助 |
| `terms[]` (`role`, `freq`, `unclear`, `ask_next`) | Stage 0b glossary pass, extended at any stage | record §1b + §8; `claim-audit.md` term substitution (`coined`); paper-story merges terms |
| `core.assumptions[]`, `position.lineage`, `learning` (incl. `admire`) | Stages 2 / 6 / 7 | record §3 前提盤點, §7 脈絡, §8; paper-story `drift` / `logic.fragile` cite assumptions |
| `keypoint`, `talk`, `deck_hints` | (optional, deprecated) | kept only so v1.1 runs stay valid |

## 3. `reading-record.md` — 【學習紀錄】

Traditional Chinese, terms inline `中文 (English)`; template
`assets/reading-record-template.md` (vault front matter). Order:

0. 審計摘要先行 — C1 and its verdict, what holds, what is missing, the 「先寫你的版本」
   box; a pointer to the paper-story run (key point) when it exists
1. 取用卡 · 2. 骨架卡 · 3. 核心卡 · 4. 主張審計 · 5. 圖表判讀 · 6. 寫作解剖 · 7. 定位卡
8. 學習筆記 · 9. 給 paper-story 的素材（設計資料、圖清單、可借句型）· 10. 附錄

Every stage prints its `自問` before the answer.

## 4. Acceptance for one run

Machine first: `verify_run.py <run_dir>` run by someone other than the author (V2
verbatim quotes → WARN + page-image check, V3 locator existence, V4 template + tags,
V7 deliverables), the kv-lint line. Then the human checklist (`ops/references/uat.md`
shape) with real values:

```
A. 必驗（沒過就不能交）
1. 讀 §0 審計摘要 → 能說出 C1 是哪一種證據、判定是什麼、還缺什麼。
2. 隨機挑一條主張的出處對 PDF → 該頁確有該內容。
3. 「作者說」引文對 PDF → 逐字相同。
4. §6 設計資料表 → 能照著寫出這篇 Methods 的一段。
B. 體驗（過了會更好）
5. 一週後自問三題 → 不看紀錄能回答兩題。
```

## 5. `index.json`

`{schema, home, entries[{run_id, path, title, first_author, year, venue, doi,
source_type, depth, created, revision, keypoint_title (from story.json when present),
c1_verdict, domain_profile, tags[], related[]}]}` — `library.py register` upserts and
regenerates `README.md`.
