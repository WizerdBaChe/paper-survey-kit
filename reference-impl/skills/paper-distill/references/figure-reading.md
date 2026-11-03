---
xi: 1
what: paper-distill Stage 4 圖表判讀——先讀圖再讀敘述、每種圖表要看的三件事（元件/光子/材料領域）、圖卡格式與取圖工具 (figure reading cards and per-chart checklists)
tags: [skill-reference, paper-distill, figure-reading, charts]
aliases: [圖表判讀, 這張圖怎麼看, figure card, chart checklist, I-V curve, spectrum, benchmark plot]
date: 2026-09-02
status: live
---

# Figure reading — the figure is the emitted artifact

Stage 4 of `paper-distill`. The narrative describes what the authors want
the figure to show; the figure shows what happened. Read the figure FIRST,
write what you see, then read the sentence that cites it and record any
gap. This is the user's gate rule (the checker reads the emitted artifact,
never the producer's own description) applied to a paper.

## How to get at the figures

- `Read` the PDF with `pages:` to SEE a page (the Read tool renders PDF
  pages; ≤ 20 pages per call; required for PDFs over 10 pages). The Read
  tool refuses some publisher PDFs as "password-protected" even though
  nothing asks for a password (both real papers on 2026-09-02; re-saving
  without encryption did NOT help — cause unknown). The reliable path is the
  rendered pages: `Read` `source/pages/pNNN.png` one by one (same pages,
  110 dpi) and take verbatim text + locators from `source/paper.txt`;
  embedded rasters (SEM images etc.) are in `source/images/`.
- `source/figures.json` (from `ingest.py`) lists caption anchors ("Fig. N",
  "Table N") with page, bbox and `caption` — the whole PDF text block,
  whitespace-normalised. Quote it as the caption only when `caption_ok` is
  `true` (found verbatim in `paper.txt`, ending a line there); runs ingested
  before 2026-09-26 cut every caption at 160 chars and have no `caption_ok`,
  so take their captions from `paper.txt`. Also embedded raster images extracted to
  `source/images/`. Use `crop.py` to cut the load-bearing figure for the
  one-pager: `--caption "Fig. 3"` renders the band between the nearest
  body text above the caption (paragraph, heading, running header, another
  caption) and the caption, across the full page width (the caption's
  column on a two-column page), and crops what is painted there — the
  caption itself is left out; a table is taken from whichever side of its
  caption it sits on. The JSON names the block that set the top
  (`band.top_set_by`) and carries a border-ink gate: exit 3 / `FAIL` means
  ink on the crop edge, i.e. the cut went through content. The gate cannot
  see a top chosen too low (a white gap inside the figure) or a stray line
  of text kept above it, so view the crop either way. `--above N` /
  `--below N` / `--full-width` switch to the old fixed rectangle (the
  caption's column, N pt above it, caption included) — until 2026-09-26
  that was the default, and it cut 7 of Tran 2018's 11 figures at an edge.
  `--bbox` crops an exact rectangle in PDF points; `--image` picks an
  extracted raster.
- Vector figures are not in `images/`; crop them from the rendered page.

## The figure card

One card per figure examined; `full` depth: every figure the audit cites;
`standard`: the ONE load-bearing figure plus any figure that contradicts
the narrative.

| Field | Fill rule |
|---|---|
| `id` / `locator` | F1…; `p.N Fig.M` (panel letter if relevant) |
| `question` | which ONE question this figure answers (one question, one view — a figure asked to answer two questions answers neither) |
| `look_for[]` | the three things to look at for this chart type (below) |
| `shows` | what it actually shows, in numbers where possible, `[verified]` |
| `supports` | which claim row (C1…) it backs, or `none` / `contradicts Cn` |
| `caveat` | axis scale, error bars, n, normalisation, missing baseline, cherry-picked device, simulation-vs-measurement mixing, resolution too low to read |
| `blind_spot` | what this view cannot show (a spectrum cannot show yield; a single I-V cannot show variation) |

## Three things to look at, by chart type

Built for the user's fields (GaN power devices, waveguides / photonic
packaging, materials); the generic and clinical sets follow.

| Chart | Look at 1 | Look at 2 | Look at 3 |
|---|---|---|---|
| Transfer / output I-V (FET, diode) | threshold or turn-on: definition used (current criterion?) and sweep direction (hysteresis) | on/off ratio and the leakage floor — is the floor the instrument's? | conditions: DC vs pulsed, temperature, gate/drain stress before this sweep |
| Breakdown (BV) curve | BV criterion (1 µA? 1 mA/mm? destructive?) | leakage before breakdown — soft or hard | how many devices; is the shown one the best |
| Ron,sp vs BV benchmark plot | which theoretical limit line, and whose formula | where THIS point sits and how Ron,sp was normalised (active area? pitch?) | are the comparison points the same voltage class and measurement method |
| Dynamic Ron / stress-recovery | stress condition (voltage, time, temperature) | time axis (log?) and where "recovery" is declared | baseline: fresh device or previously stressed |
| C-V / extraction plots | frequency and signal amplitude | depletion assumptions behind the extraction | fit range — where the line was drawn |
| TEM / SEM / cross-section | scale bar and what feature is claimed | is it the SAME device that was measured, or a witness sample | artefacts: FIB damage, contrast tricks, cropped edges |
| Transmission / reflection spectrum | resonance position and linewidth (Q) | normalisation reference (through-port? bare fibre? simulated?) | wavelength range shown vs the band the application needs |
| Mode profile / field map | what is plotted (|E|, |E|², power) and colour scale (log?) | boundaries and the domain size — is the mode confined or the box | simulated or measured; polarization |
| Coupling efficiency vs offset / wavelength | 1 dB / 3 dB tolerance window | peak value AND whether it includes propagation/facet loss | sim vs measurement — which is which, and which was fitted |
| Loss vs length (cut-back) | number of lengths and spread | intercept (coupling) vs slope (propagation) | was the fit forced through a point |
| Eye diagram / BER | data rate, PRBS length, extinction ratio | receiver / equalisation used | one channel or the worst channel |
| Box plot / wafer statistics | n and where it came from (devices, wafers, lots) | outliers removed? by what rule | median vs "best" quoted in text |
| Arrhenius / Weibull / lifetime | acceleration model and activation energy source | sample size and censoring | extrapolation distance to the claimed lifetime |
| Simulation vs measurement overlay | which one has free parameters and how many | agreement range vs the range where they diverge | was the simulation calibrated on this same data |
| Process flow / schematic | which step is the claimed novelty | what is NOT drawn (buffer, passivation, contacts) | scale honesty (schematic proportions can mislead) |
| Bar chart (any) | baseline present? fair? | error bars: SD, SE, min-max, or none | y-axis origin (truncated?) |
| Line chart (any) | log or linear; log-log hides a lot | extrapolated region drawn as if measured | markers = data, lines = fit or guide-to-eye? |
| Table | units and normalisation | missing cells (why?) | bold = best? by whose criterion |

Clinical charts (B-6, kept so the source stays honoured): scatter — slope
sign / significance / outliers; KM plot — arm outcome / significance /
median survival; ROC — hugs the diagonal? / toward upper-left? / AUC > 0.8;
forest — crosses the line? / significance / heterogeneity > 50 %.

Chart not listed: write your own three, and add the row here in the same
session (the table is meant to grow from real runs).

## Deck rule inherited from B-6

A talk needs ≥ 4 figures; when the paper has fewer usable ones, borrow
from cited references and label them `[borrowed: ref N]` — never present
a borrowed figure as the paper's.

## The reverse question (Stage 5 hands off here)

Once a figure card says what the figure shows, `writing-craft.md` asks the
reverse: what was it DESIGNED to prove, why this chart type, how are the
panels arranged, what is labelled and what is deliberately absent. Fill
`craft.figure_design[]` for the load-bearing figures right after their cards —
the craft of a figure is only visible once you know what it had to prove.

## Figure for the one-pager

Pick the ONE figure the key point rests on — the EVIDENCE figure (C1's SEM,
plot or table), not the process schematic that explains it (2026-09-03: a
run chose the Fig. 1 process cartoon for a fabrication paper; the SEM
cross-section that shows the mechanism happening is what the key point
rests on — the schematic belongs on the talk's Methods page). Crop tightly,
keep the panel labels, keep or re-type the axis labels legibly, and check
the crop's top edge for stray text from the paragraph above (the default
crop stops at the block named in `band.top_set_by`).
The one-pager's "這張圖怎麼看" block is exactly this card's `look_for` and
`shows` — write them so a listener with 15 seconds sees what you saw.
