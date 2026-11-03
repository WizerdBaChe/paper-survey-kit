---
xi: 1
what: paper-story 與 paper-distill 的橋接——不綁定、共用工具與 run 資料夾、依情況互相呼叫（比照 scientific-research-guide ↔ literature-search-extract） (how the two paper skills relate: shared tooling and run folder, situational calls, no binding)
tags: [skill-reference, paper-story, paper-distill, bridge, routing]
aliases: [兩個論文 skill 的橋接, paper-story 與 paper-distill 關係, 深讀與敘事的分工, bridge between paper skills]
date: 2026-09-03
status: live
---

# Bridge — two skills, one run folder, calls by situation

User ruling (2026-09-03): IMRaD deep reading is a complete methodology with its
own product; the presentation task has a different output shape; make each
complete on its own, then bridge them the way `scientific-research-guide` and
`literature-search-extract` are related — not bound, called together when the
situation asks.

| | `paper-distill` 深讀 | `paper-story` 敘事與簡報 |
|---|---|---|
| object | evidence: skeleton, claims with verdicts, figure cards, writing craft | narrative: axis with whys, storyline beats, logic extraction, presentation |
| product | `reading-record.md`【學習紀錄】+ `cards.json` | `narrative-record.md`【敘事紀錄】+ `story.json` + `paper-explainer.html` (練習・複習用; its 口述稿 section is the talk script — no separate `talk-script.md` since 2026-11-03) + on explicit request `lab-deck.pptx` (the lab template, English) |
| question it answers | does the evidence hold, and what does this paper teach about writing | how was this research constructed, why, and how do I present it |
| trigger words | 深讀、拆 IMRAD、審主張、證據夠不夠、學寫法 | 要報、簡報、一頁式、多頁、主軸、故事線、key point、為什麼讀它 |

## Shared, by design

- **Run folder**: both write into the same `<home>/<PaperId>/` under the vault
  library (`<PAPER_HOME>\`; `PaperId` =
  `<FirstAuthor><Year>_<short-title-slug>`, one accepted run per paper since 2026-09-04;
  calibration copies under `_calibration/<PaperId>/<label>/`). `story.json` and
  `cards.json` sit side by side; `story.json` names `run.distill_run`, and the
  library index entry carries both `distill_run` and `story_run` (written by
  `library.py register`, never into `cards.json` — the story side is not
  authorized to edit the distill products; a story run in a copied folder
  registers under its own id).
- **Tooling**: `ingest.py`, `probe.py` (structure units + anomalies → `source/structure.json`, read by the story's S11/S12 and the distill skeleton), `crop.py`, `library.py` live in `paper-distill/scripts`
  and are called by path from `paper-story`. If `paper-distill` is absent, the
  story skill stops and says so — it does not carry a second copy (one parser,
  one ingest). The deck shell and pptx helpers are verbatim copies in both
  skills with recorded sha (drift gate on both sides).
- **Terms**: `paper-story` merges `cards.terms[]` when present and extends it to
  full coverage; the story side owns the hover-preview requirement.

## Calls by situation

- Story first, no deep read: the user only wants the talk. `paper-story` reads
  the paper itself for the six beats; `drift` then says 「未經深讀審計」 next to
  any claim it leans on, and the record offers `paper-distill` for the audit.
- Deep read exists: `paper-story` cites claim verdicts in `drift` (beat ⑥ wording
  vs C1 verdict), reuses figure cards for captions, reuses `craft.methods_writing.
  design_data` for the Method pages' highlights.
- Deep read first, then a talk: `paper-distill`'s close-out offers
  `paper-story` (「要做簡報 → paper-story」); it never renders slides itself.
- Contested claim during story work (「這個數字撐得住嗎」): call `paper-distill`
  for that claim's audit row rather than guessing in the story.

## What never crosses

- Verdict words (provisional / leaning / …) are `paper-distill`'s; the story
  side quotes them, never invents them.
- The key point is `paper-story`'s (logic extraction); the deep-read record
  points to it and does not carry its own.
