#!/usr/bin/env python
"""paper-story shot — element screenshots of a rendered HTML product (Playwright, headless chromium).

The dispatcher's appearance instrument for a calibration (the S7 fit gate measures overflow; a human
still looks at the page). Element screenshots, so the deck shell's scroll-snap does not matter.
Usage: python -X utf8 shot.py <html> <out_dir> <prefix> <selector> [<selector>...]
  e.g. shot.py <run>/paper-explainer.html evidence/ A "#script"   (section ids: keypoint brief axis storyline figures script audit logic next)
  legacy pages (render_story.py --legacy-html only): shot.py <run>/onepage.html evidence/ A "#p1"   shot.py <run>/talk-deck.html evidence/ A "#d1"
Viewport 1707x830 (the S7 fit viewport). Writes <out_dir>/<prefix>-<selector>.png.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main(html, out_dir, prefix, selectors):
    html = Path(html).resolve()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1707, "height": 830})
        pg.goto(html.as_uri())
        pg.wait_for_load_state("networkidle")
        for sel in selectors:
            el = pg.query_selector(sel)
            if el is None:
                print(f"MISSING {sel}")
                continue
            el.scroll_into_view_if_needed()
            pg.wait_for_timeout(150)
            path = out / f"{prefix}-{sel.strip('#')}.png"
            el.screenshot(path=str(path))
            print(f"wrote {path}")
        b.close()


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
