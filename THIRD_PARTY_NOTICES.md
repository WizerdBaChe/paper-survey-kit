# Third-party notices

Checked on 2026-11-03. Everything else in this repository is the author's own work (see `LICENSE`,
`LICENSE-DOCS`); the demo paper in `examples/fictional-paper/` is fictional and written for this kit.

## Control fixtures cut from an open-access paper (CC BY 4.0)

Three acceptance controls the code reads at run time are excerpts of one open-access paper:

- `reference-impl/skills/paper-distill/evals/fixtures/caption-check_tran2018-F4.json` — the Figure 4
  caption and the surrounding text-layer lines (ingest's caption-completeness control);
- `reference-impl/skills/paper-distill/evals/fixtures/crop-gate-bad_tran2018-F6.png` — a deliberately
  bad crop of Figure 6 (crop.py's known-bad border-ink control);
- `reference-impl/skills/paper-distill/evals/units-allow.json` — two allow-list entries that name short
  journal-citation strings (such as 'Appl. Sci. 2017, 7, 732') from the reference lists of this paper and
  of a second review in the same journal (run id `Mu2020_edge-couplers-si-pic-review`). A bibliographic
  citation is a fact, not the papers' expression; no licence is claimed for these strings.

Source: Minh A. Tran, Duanni Huang, Tin Komljenovic, Jonathan Peters, Aditya Malik, John E. Bowers,
"Ultra-Low-Loss Silicon Waveguides for Heterogeneously Integrated Silicon/III-V Photonics",
*Applied Sciences* 8 (2018) 1139, doi:10.3390/app8071139. Licence: Creative Commons Attribution 4.0
International, https://creativecommons.org/licenses/by/4.0/ (the licence line printed in the paper;
recorded inside the fixture's `source.licence`).
Changes: cut to the lines and the region each control needs; the crop was deliberately cut badly.
These files are not covered by this repository's CC BY licence grant to the extent they are the
paper authors' material; they stay under the paper's own CC BY 4.0 with the credit above.

`reference-impl/skills/paper-story/evals/fixtures/sample-story.json` is a synthetic story written by
the author (presenter 「示範」, an invented GaN paper title) and is the author's own work.

## Runtime dependencies (installed by you, not shipped)

| package | used by | licence (from its installed metadata, 2026-11-03) |
|---|---|---|
| PyMuPDF 1.26 | ingest, probe, crop, units (PDF text and page images) | **GNU AGPL-3.0 or Artifex commercial licence** — read it before you distribute anything built on it |
| python-pptx 1.0 | formal deck, pptx carrier | MIT |
| Pillow 12 | crops, figure sizes | MIT-CMU |
| lxml 6 | formal deck XML | BSD-3-Clause |
| jsonschema 4 | carriers content validation | MIT |
| playwright 1.62 | page-fill gate, screenshots | Apache-2.0 |
| Chromium (downloaded by `python -m playwright install chromium`) | headless page measurement | the Chromium project's licences (mainly BSD-3-Clause; full list at `chrome://credits` in that browser) |
| matplotlib 3 | the demo paper's figures (`make_paper.py`) | matplotlib licence (PSF-based) |
| pytest 9 | paper-distill unit tests (K5b) | MIT |

This repository's MIT code imports PyMuPDF; it does not include or modify it.

## Web fonts loaded by generated pages

`reference-impl/skills/paper-story/assets/deck-shell.html` and the pages built from it link Google Fonts
(IBM Plex Mono, Noto Sans TC; SIL Open Font License 1.1). Opening such a page online requests the fonts
from fonts.googleapis.com; offline it falls back to local fonts.
