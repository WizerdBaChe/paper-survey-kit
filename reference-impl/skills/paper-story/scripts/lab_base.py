"""The one way to open the lab base deck for ANY builder.

User ruling 2026-11-16: the lab template and the base deck are one thing — the stripped
title-only bases in <NOTES_VAULT>/literature/PaperSurvey/_templates/ (base_single-paper.pptx for a
multi-page deck, base_ten-papers.pptx for the one-page survey). Every builder that starts from one
(paper-story lab_deck.py, project weekly/progress decks) opens it through open_lab_base(), so the
base's leftover cover picture can never ride along.

Cover-picture property (formal-deck.md R7-12, widened 2026-11-16): the top-right picture of
base_single-paper.pptx is the journal logo of the paper the template was cut from. It belongs to
that paper only. A deck about a paper keeps ONLY that paper's own design in the frame (its journal
logo via `logo=`); a deck about no paper (progress report, proposal) keeps the corner empty.
"It is only a small corner logo" is the usual excuse: the audience reads it as the deck's source.

Usage from a project builder:
    sys.path.insert(0, r"~/.claude/skills/paper-story/scripts")
    from lab_base import open_lab_base
    prs, frame = open_lab_base("deck")            # progress deck: corner left empty
    prs, frame = open_lab_base("deck", logo=png)  # paper deck: this paper's logo in the frame
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402

TEMPLATES = hkroots.path("NOTES_VAULT", "literature", "PaperSurvey", "_templates")
BASES = {"deck": "base_single-paper.pptx", "onepage": "base_ten-papers.pptx"}
# how many template cover pictures each base carries (verified 2026-11-16 over both files)
COVER_PICTURES = {"deck": 1, "onepage": 0}


def _is_cover_picture(sh) -> bool:
    return sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.left / 914400 > 7.0 and sh.top / 914400 < 1.0


def strip_cover_picture(slide, logo: Path | None = None, fit=None):
    """Remove the base's top-right cover picture; with `logo`, place it in the freed frame.

    `fit(slide, path, x, y, w, h)` places the logo (lab_deck passes its fit_pic); without it the logo is
    scaled to fit and centred. Returns (number removed, frame in inches or None)."""
    hits = [sh for sh in slide.shapes if _is_cover_picture(sh)]
    frame = None
    for sh in hits:
        frame = tuple(v / 914400 for v in (sh.left, sh.top, sh.width, sh.height))
        sh._element.getparent().remove(sh._element)
    if logo and frame:
        x, y, w, h = frame
        if fit is not None:
            pic = fit(slide, logo, x, y, w, h)
        else:
            from PIL import Image  # noqa: PLC0415
            iw, ih = Image.open(logo).size
            s = min(w / iw, h / ih)
            pw, ph = iw * s, ih * s
            pic = slide.shapes.add_picture(str(logo), Emu(int((x + (w - pw) / 2) * 914400)),
                                           Emu(int((y + (h - ph) / 2) * 914400)),
                                           Emu(int(pw * 914400)), Emu(int(ph * 914400)))
        pic.name = "Source logo"
    return len(hits), frame


def open_lab_base(kind: str = "deck", out: Path | None = None, logo: Path | None = None):
    """Open the lab base deck for `kind` with its cover picture already handled. With `out`, copy the base
    there first (lab_deck's flow). Asserts the base still carries the expected number of cover
    pictures, so a re-cut template is noticed instead of silently keeping a stray logo."""
    if TEMPLATES is None:
        raise SystemExit("lab_base: NOTES_VAULT unset in adapt/host.toml; the bases live in literature/PaperSurvey/_templates")
    base = TEMPLATES / BASES[kind]
    if not base.is_file():
        raise SystemExit(f"lab_base: base missing: {base}")
    src = base
    if out is not None:
        shutil.copy(base, out)
        src = out
    prs = Presentation(str(src))
    n, frame = strip_cover_picture(prs.slides[0], logo)
    if n != COVER_PICTURES[kind]:
        raise SystemExit(f"lab_base: {base.name} carried {n} cover picture(s), expected {COVER_PICTURES[kind]}; "
                         "the template changed — re-verify COVER_PICTURES")
    return prs, frame


if __name__ == "__main__":  # self-check: both bases open clean, a picture-free result, positive control
    for k in BASES:
        p, _ = open_lab_base(k)
        left = [sh for sh in p.slides[0].shapes if _is_cover_picture(sh)]
        assert not left, f"{k}: cover picture survived"
        print(f"{k}: ok, cover pictures left = 0")
    raw = Presentation(str(TEMPLATES / BASES["deck"]))
    assert any(_is_cover_picture(sh) for sh in raw.slides[0].shapes), "control: raw deck base must carry the picture"
    print("control: raw deck base carries the picture (detector fires)")
