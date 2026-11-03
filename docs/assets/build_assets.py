"""Regenerate every README image from shipped pages (no hand-made picture).

Usage (from the repo root):  python -X utf8 docs/assets/build_assets.py

Inputs (all shipped): docs/assets/src/pipeline.html, docs/assets/src/hero.html, docs/assets/src/social.html,
examples/library/<run>/paper-explainer.html, examples/library/<run>/source/pages/p001.png.
Outputs: docs/assets/pipeline.zh-TW.png, hero.png, explainer-*.png, social-card.png.
Needs playwright + chromium. The explainer links Google Fonts, so a run without network falls back to
system fonts and the shots differ in type only.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "docs" / "assets"
SRC = ASSETS / "src"
RUN = REPO / "examples" / "library" / "Placeholder2026_wax-delay-bridges"
EXPLAINER = RUN / "paper-explainer.html"

# (output name, how to find the place: None = first screen, "#id" = a section, "text:..." = the block whose
# caption starts with that text, e.g. the drift table inside the audit section)
EXPLAINER_SHOTS = [
    ("explainer-top.png", None),
    ("explainer-drift.png", "text:敘事偏離"),
    ("explainer-logic.png", "#logic"),
]
FIND_BLOCK = """t => { const els = [...document.querySelectorAll('caption, figcaption, .cap, div, p')]
  .filter(e => e.children.length === 0 && e.textContent.trim().startsWith(t));
  if (!els.length) return false; const box = els[0].closest('table, figure, section, div') || els[0];
  window.scrollTo(0, box.getBoundingClientRect().top + window.scrollY - 24); return true; }"""


def edge_check(page, src: Path) -> None:
    """The pipeline diagram measures its own edges (window.__edgeCheck). Two-sided: the known-bad load
    (#control-short, one endpoint 4 px short of its border) must report a problem, the real load none."""
    page.goto(src.as_uri() + "#control-short")
    bad = page.evaluate("window.__edgeCheck")
    page.goto(src.as_uri())
    good = page.evaluate("window.__edgeCheck")
    print(f"edge check: known-bad {len(bad['problems'])} problem(s) {bad['problems'][:1]} vs real {len(good['problems'])} "
          f"over {good['edges']} edges")
    if not bad["problems"]:
        sys.exit("edge check control did not fire: the check cannot be trusted")
    if good["problems"]:
        sys.exit("edge check failed: " + "; ".join(good["problems"]))


def shot_page(page, src: Path, out: Path, w: int, h: int) -> None:
    page.set_viewport_size({"width": w, "height": h})
    page.goto(src.as_uri())
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
    print(f"wrote {out.relative_to(REPO).as_posix()} ({w}x{h})")


def section_ids(page) -> list[str]:
    return page.eval_on_selector_all("section[id], [data-section][id]", "els => els.map(e => e.id)")


def main() -> int:
    if not EXPLAINER.exists():
        sys.exit(f"missing {EXPLAINER.relative_to(REPO)}: build the example run first")
    work = SRC / "_shots"
    work.mkdir(exist_ok=True)
    shutil.copyfile(RUN / "source" / "pages" / "p001.png", work / "paper-p001.png")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        edge_check(page, SRC / "pipeline.html")
        shot_page(page, SRC / "pipeline.html", ASSETS / "pipeline.zh-TW.png", 1600, 840)

        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(EXPLAINER.as_uri())
        page.wait_for_load_state("networkidle")
        # dismiss the operating-hint toast the way a reader would (its close button)
        close = page.locator("#hint button, #hint [aria-label], #hint .x").first
        if close.count():
            close.click()
        ids = section_ids(page)
        for name, where in EXPLAINER_SHOTS:
            if where is None:
                page.evaluate("window.scrollTo(0, 0)")
            elif where.startswith("#"):
                if where[1:] not in ids:
                    sys.exit(f"no section {where} in the explainer; ids: {ids}")
                page.evaluate("id => document.getElementById(id).scrollIntoView({block: 'start'})", where[1:])
            else:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # sections render on scroll
                page.wait_for_timeout(500)
                if not page.evaluate(FIND_BLOCK, where[5:]):
                    sys.exit(f"no block starting with '{where[5:]}' in the explainer")
            page.wait_for_timeout(600)
            page.screenshot(path=str(ASSETS / name))
            print(f"wrote docs/assets/{name} (1440x900, {where or 'first screen'})")
        for name in ("explainer-top.png", "explainer-drift.png"):
            shutil.copyfile(ASSETS / name, work / name)

        shot_page(page, SRC / "hero.html", ASSETS / "hero.png", 1600, 800)
        shot_page(page, SRC / "social.html", ASSETS / "social-card.png", 1280, 640)
        browser.close()
    shutil.rmtree(work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
