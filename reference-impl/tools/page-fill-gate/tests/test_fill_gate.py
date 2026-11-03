"""Two-sided calibration of page-fill-gate: one known-good and one known-bad page per class.

    python tools/page-fill-gate/tests/test_fill_gate.py

Every class row in page_classes.json must have BOTH a passing and a failing
fixture here — a class with only one side is not calibrated (a reject-everything
gate scores 100 % on a one-sided check). Adding a class row without adding its
pair fails this test on purpose.
"""
import json
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fill_gate  # noqa: E402

REG = fill_gate.load_registry()

BASE = """<!doctype html><html lang="zh-Hant"{attr}><head><meta charset="utf-8"><title>{title}</title>
<style>body{{margin:0;font-family:system-ui,sans-serif;line-height:1.6}} *{{box-sizing:border-box}}
p{{margin:8px 0}} .box{{border-left:4px solid #888;background:#f4f4f4;padding:10px 16px}}
table{{width:100%;border-collapse:collapse}} td{{border:1px solid #ccc;padding:4px}}
{css}</style></head><body>{body}</body></html>"""

TEXT = "<p>" + "本段是量測用的內文，長度足以在任何欄寬下換行。" * 6 + "</p>"

CASES = {
    # name: (class attr, css, body, expected status)
    "document-short centred 900": ("document-short",
        ".wrap{max-width:900px;margin:0 auto;padding:40px 20px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div>{TEXT}</main>", "PASS"),
    "document-short left-anchored 900": ("document-short",
        ".wrap{max-width:900px;margin:0;padding:40px 20px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div>{TEXT}</main>", "FAIL"),
    # Fixed corner panel (fb:bfa19018, 2026-10-12): the panel's text children used to count as
    # content, so the right void read as the panel inset (~40px) and a centred page FAILED. The
    # asserted value is the void symmetry; the twin keeps a left cap failing with the panel present.
    "document-short centred + fixed corner panel": ("document-short",
        ".wrap{max-width:900px;margin:0 auto;padding:40px 20px} .panel{position:fixed;right:24px;bottom:24px;background:#fff;border:1px solid #999;padding:12px;display:grid;gap:8px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div></main><aside class='panel'><div>字體 襯線 無襯線</div><div>樣板比較面板，不是內容</div></aside>", "PASS"),
    "document-short left-anchored + fixed corner panel": ("document-short",
        ".wrap{max-width:900px;margin:0;padding:40px 20px} .panel{position:fixed;right:24px;bottom:24px;background:#fff;border:1px solid #999;padding:12px;display:grid;gap:8px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div></main><aside class='panel'><div>字體 襯線 無襯線</div><div>樣板比較面板，不是內容</div></aside>", "FAIL"),
    # ...but a fixed box that COVERS the viewport is the page itself (an `inset:0` app shell), not
    # an overlay: its content must still be measured (n > 0), or the page reads WARN "no block".
    "tool full-viewport fixed shell": ("tool",
        ".app{position:fixed;inset:0;display:grid;grid-template-columns:clamp(220px,20vw,320px) minmax(0,1fr);overflow:hidden} .app>*{padding:16px;border:1px solid #ccc}",
        f"<div class='app'><aside>面板</aside><main>{TEXT}</main></div>", "PASS"),
    "document-long fluid + sidebar": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px clamp(20px,4vw,64px)}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}<table><tr><td>a</td><td>b</td></tr></table>{TEXT}</main>", "PASS"),
    "document-long capped 1060 left": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 72px;max-width:1060px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}<div class='box' style='max-width:36em'>note</div>{TEXT}</main>", "FAIL"),
    # Several rails, either side (2026-10-31, PersonalSite article grid: toc rail | prose | gutter).
    # Before, only the FIRST [data-rail] counted and only as a RIGHT edge, so marking the left rail
    # made the gate read its right border as the page's right edge and fail a centred page.
    # Asserted value: void symmetry. Twins: unmarked gutter (intent unknowable -> FAIL) and a
    # marked left rail beside left-anchored prose (the mark must not excuse a real left cap).
    "document-short left rail + centred prose, rail and gutter marked": ("document-short",
        ".g{display:grid;grid-template-columns:minmax(200px,1fr) minmax(0,680px) minmax(0,1fr);gap:52px;max-width:1240px;margin:0 auto;padding:40px 20px} .rail p{margin:0;font-size:14px}",
        f"<main class='g'><aside class='rail' data-rail><p>目錄一</p><p>目錄二</p></aside><article><h1>標題</h1>{TEXT}{TEXT}</article><div data-rail></div></main>", "PASS"),
    "document-short left rail + centred prose, gutter unmarked": ("document-short",
        ".g{display:grid;grid-template-columns:minmax(200px,1fr) minmax(0,680px) minmax(0,1fr);gap:52px;max-width:1240px;margin:0 auto;padding:40px 20px} .rail p{margin:0;font-size:14px}",
        f"<main class='g'><aside class='rail' data-rail><p>目錄一</p><p>目錄二</p></aside><article><h1>標題</h1>{TEXT}{TEXT}</article><div></div></main>", "FAIL"),
    "document-short marked left rail + left-anchored prose": ("document-short",
        ".g{display:grid;grid-template-columns:220px minmax(0,680px);gap:52px;padding:40px 20px} .rail p{margin:0;font-size:14px}",
        f"<main class='g'><aside class='rail' data-rail><p>目錄一</p><p>目錄二</p></aside><article><h1>標題</h1>{TEXT}{TEXT}</article></main>", "FAIL"),
    # Clipped overflow (2026-10-13): reach cannot see a display formula scrolling inside its own box.
    # Same page, same numbers: one line (FAIL, the tail is hidden) vs two rows (PASS).
    "document-long formula wider than its box": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 48px} math[display=block]{display:block;overflow-x:auto}",
        f"<nav id='side'>TOC</nav><main><h1 id='q'>標題</h1>{TEXT}<math display='block'><mrow>{'<mn>0.123456</mn><mo>+</mo>' * 40}<mn>1</mn></mrow></math></main>", "FAIL"),
    "document-long formula broken into rows": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 48px} math[display=block]{display:block;overflow-x:auto}",
        f"<nav id='side'>TOC</nav><main><h1 id='q'>標題</h1>{TEXT}<math display='block'><mtable><mtr><mtd><mrow>{'<mn>0.123456</mn><mo>+</mo>' * 10}</mrow></mtd></mtr><mtr><mtd><mrow>{'<mn>0.123456</mn><mo>+</mo>' * 10}<mn>1</mn></mrow></mtd></mtr></mtable></math></main>", "PASS"),
    "document-long fluid main + rail": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;margin-right:320px;padding:36px 48px} #rail{position:fixed;right:0;top:0;bottom:0;width:320px;background:#f8f8f8;border-left:1px solid #ccc;padding:16px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}{TEXT}</main><aside id='rail' data-rail><p>本節速查</p></aside>", "PASS"),
    "deck slides fill": ("deck",
        "html{scroll-snap-type:y proximity} .slide{min-height:100vh;padding:24px 72px} .thesis{background:#eef;border:1px solid #99c;padding:12px} .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}",
        f"<section class='slide'><h1>結論</h1><div class='thesis'>一句話主張</div>{TEXT}</section><section class='slide'><div class='grid2'><div class='box'>a</div><div class='box'>b</div></div></section>", "PASS"),
    "deck thesis capped 56em left": ("deck",
        "html{scroll-snap-type:y proximity} .slide{min-height:100vh;padding:24px 72px} .thesis{background:#eef;border:1px solid #99c;padding:12px;max-width:40em;font-size:20px}",
        f"<section class='slide'><h1>結論</h1><div class='thesis'>一句話主張，這個框被上限卡在 40em 而且靠左，右邊空一大塊。</div>{TEXT}</section><section class='slide'><h2>二</h2>{TEXT}</section>", "WARN"),
    "tool proportional shell": ("tool",
        ".app{display:grid;grid-template-columns:clamp(220px,20vw,320px) minmax(0,1fr);height:100vh;overflow:hidden} .app>*{padding:16px;border:1px solid #ccc}",
        f"<div class='app'><aside>面板</aside><main>{TEXT}</main></div>", "PASS"),
    "tool centred 1240 cap": ("tool",
        ".container{max-width:1240px;margin:0 auto;padding:16px} .panes{display:grid;grid-template-columns:1fr 1fr;gap:16px}",
        f"<div class='container'><h1>工具</h1><div class='panes'><div class='box'>{TEXT}</div><div class='box'>{TEXT}</div></div></div>", "FAIL"),
    # The overshoot bug also MASKED defects: a box parked past the right edge inflated maxR, so a
    # left-capped page read reach >= 100 % and PASSED. The asserted value is reach (about 0.5 here).
    "tool left-capped + box parked off-canvas right": ("tool",
        ".container{max-width:900px;margin:0;padding:16px} .parked{position:absolute;left:150vw;top:0;width:300px;background:#eee;padding:8px}",
        f"<div class='container'><h1>工具</h1>{TEXT}</div><div class='parked'>停在畫面外</div>", "FAIL"),
    "diagram centred svg": ("diagram",
        "main{max-width:1240px;margin:0 auto;padding:16px} svg{width:100%;height:auto;display:block;border:1px solid #ccc}",
        "<main><h1>圖</h1><svg viewBox='0 0 1280 720'><rect x='10' y='10' width='1260' height='700' fill='#eef' stroke='#336'/></svg></main>", "PASS"),
    "diagram left-anchored svg": ("diagram",
        "main{max-width:1240px;margin:0;padding:16px} svg{width:100%;height:auto;display:block;border:1px solid #ccc}",
        "<main><h1>圖</h1><svg viewBox='0 0 1280 720'><rect x='10' y='10' width='1260' height='700' fill='#eef' stroke='#336'/></svg></main>", "FAIL"),
    "dashboard auto-fit cards": ("dashboard",
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:16px}",
        "<div class='cards'>" + "".join(f"<div class='box'>card {i}</div>" for i in range(8)) + "</div>", "PASS"),
    "dashboard capped left": ("dashboard",
        ".cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:16px;max-width:900px}",
        "<div class='cards'>" + "".join(f"<div class='box'>card {i}</div>" for i in range(8)) + "</div>", "FAIL"),
    # showcase (2026-10-02): full-bleed bands are backdrops. The bad case is the one the
    # backdrop option exists for -- measured without it, the bands read reach 100 % and PASS.
    "showcase bands + centred grid + bleed": ("showcase",
        "body{overflow-x:hidden} .band{padding:40px 0} .b1{background:#1e6fb8} .b2{background:#eef5fb} "
        ".wrap{width:min(1200px,84vw);margin:0 auto;display:grid;grid-template-columns:2fr 3fr;gap:32px;align-items:center} "
        ".bleed{display:block;width:calc(100% + (100vw - min(1200px,84vw)) / 2);height:auto}",
        "<section class='band b1'><div class='wrap'><div><h1>一句主張。</h1><p>一行說明。</p></div>"
        "<svg class='bleed' viewBox='0 0 800 400'><rect width='800' height='400' fill='#9cc'/></svg></div></section>"
        f"<section class='band b2'><div class='wrap'><svg viewBox='0 0 600 300'><rect width='600' height='300' fill='#cde'/></svg><div><h2>第二個主張。</h2>{TEXT}</div></div></section>", "PASS"),
    "showcase bands + left-capped column": ("showcase",
        ".band{padding:40px 0} .b1{background:#1e6fb8} .b2{background:#eef5fb} "
        ".wrap{max-width:800px;margin:0;padding:0 16px;display:grid;grid-template-columns:2fr 3fr;gap:32px}",
        "<section class='band b1'><div class='wrap'><div><h1>一句主張。</h1><p>一行說明。</p></div>"
        "<svg viewBox='0 0 800 400'><rect width='800' height='400' fill='#9cc'/></svg></div></section>"
        f"<section class='band b2'><div class='wrap'><svg viewBox='0 0 600 300'><rect width='600' height='300' fill='#cde'/></svg><div><h2>第二個主張。</h2>{TEXT}</div></div></section>", "FAIL"),
    # dialog (fb:86425480, 2026-10-13): a centred login card has no fill floor, only symmetry.
    "dialog centred card": ("dialog",
        "body{min-height:100vh;display:grid;place-items:center} .card{width:360px;border:1px solid #999;background:#fff;padding:24px}",
        "<div class='card'><h1>解鎖</h1><p>輸入密碼後繼續。</p></div>", "PASS"),
    "dialog card pinned left": ("dialog",
        "body{min-height:100vh;display:grid;align-items:center;justify-items:start;padding-left:24px} .card{width:360px;border:1px solid #999;background:#fff;padding:24px}",
        "<div class='card'><h1>解鎖</h1><p>輸入密碼後繼續。</p></div>", "FAIL"),
    # nav marked as content (fb:ee9813a8, 2026-10-12): header site name left + header nav right +
    # a right TOC in a centred grid. Unmarked, both navs are chrome and the name pins only the left
    # (FAIL, also the old build's reading of the MARKED page); marked, the voids are symmetric.
    "document-short header+TOC navs marked content": ("document-short",
        "header{display:flex;justify-content:space-between;padding:12px 16px} .g{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:3fr 1fr;gap:24px}",
        f"<header><div>站名</div><nav data-fill-content>文章 關於 聯絡</nav></header><div class='g'><article>{TEXT}</article><nav data-fill-content>目錄 一 二 三</nav></div>", "PASS"),
    "document-short header+TOC navs unmarked": ("document-short",
        "header{display:flex;justify-content:space-between;padding:12px 16px} .g{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:3fr 1fr;gap:24px}",
        f"<header><div>站名</div><nav>文章 關於 聯絡</nav></header><div class='g'><article>{TEXT}</article><nav>目錄 一 二 三</nav></div>", "FAIL"),
    "undeclared left cap -> inferred, WARN only": (None,
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 72px;max-width:1060px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}{TEXT}</main>", "WARN"),
    # The OTHER direction of the same rule, added 2026-09-08. A page with no
    # declared class that measures fine is still measured against a GUESS, so
    # its PASS is an artifact of the inference and must not be reported as
    # evidence. Before this, an undeclared page could print "0 FAIL / 0 WARN"
    # and that number would be carried forward
    # (outputs/diagram-authoring/mfp-audit-f5-owner-view.html, measured).
    "undeclared but well laid out -> STILL WARN, not PASS": (None,
        "main{padding:16px} .box{width:100%}",
        f"<main><div class='box'><h1>標題</h1>{TEXT}{TEXT}</div></main>", "WARN"),
}

# ---------------------------------------------------------------------------
# PAGED decks (L-125, 2026-10-11): a deck that shows one slide at a time hides
# the others (display:none / visibility:hidden / [hidden] / a hidden ancestor).
# Before the fix every hidden slide measured n=0 and the verdict was WARN "no
# painted/text block found" -- the gate could not tell a good paged deck from a
# bad one. The asserted VALUES that differ between the correct and the defective
# build are per-slide `n` (0 -> >0) and `reach` (0 % -> measured), not the label
# alone (rules/verification-ladder.md, control clause).
# ---------------------------------------------------------------------------
SLIDE = f"<h1>結論</h1>{TEXT}"          # full-width text: spans 100 % of the slide's content box
PAGED_CSS = ".slide{min-height:100vh;padding:24px 72px} .thesis{background:#eef;border:1px solid #99c;padding:12px;width:40%}"
PAGED = {
    # name: (css, body, per-slide expectation)  -- every one declares class=deck
    "paged good (display:none)": (
        PAGED_CSS + " .slide{display:none} .slide.active{display:block}",
        f"<section class='slide active'>{SLIDE}</section><section class='slide'>{SLIDE}</section><section class='slide'>{SLIDE}</section>", "PASS"),
    "paged good (visibility:hidden, stacked)": (
        PAGED_CSS + " .deck{position:relative;min-height:100vh} .slide{position:absolute;inset:0;visibility:hidden} .slide.active{visibility:visible}",
        f"<div class='deck'><section class='slide active'>{SLIDE}</section><section class='slide'>{SLIDE}</section><section class='slide'>{SLIDE}</section></div>", "PASS"),
    "paged good ([hidden] attribute)": (
        PAGED_CSS,
        f"<section class='slide'>{SLIDE}</section><section class='slide' hidden>{SLIDE}</section><section class='slide' hidden>{SLIDE}</section>", "PASS"),
    "paged good (hidden ancestor)": (
        PAGED_CSS + " .page{display:none} .page.on{display:block}",
        f"<div class='page on'><section class='slide'>{SLIDE}</section></div><div class='page'><section class='slide'>{SLIDE}</section></div><div class='page'><section class='slide'>{SLIDE}</section></div>", "PASS"),
    # the known-bad twin: slide 2 is hidden AND holds one left-anchored 40 % block
    "paged BAD (hidden slide 2 lone 40% block)": (
        PAGED_CSS + " .slide{display:none} .slide.active{display:block}",
        f"<section class='slide active'>{SLIDE}</section><section class='slide'><div class='thesis'>被卡在 40% 寬而且靠左的主張框，右邊空一大塊。</div></section><section class='slide'>{SLIDE}</section>", "FAIL"),
}

# ---------------------------------------------------------------------------
# OVERSHOOT (fill/reach > 100 %, the `tool` row of the same feedback entry): a
# fraction of the AREA cannot exceed 1. It did because the ruler counted boxes
# that are not inside the area -- clipped by an overflow ancestor, laid out past
# the area edge, or parked off-canvas -- at their full extent. Each page below is
# well laid out; the asserted value is the fraction itself.
# ---------------------------------------------------------------------------
OVERSHOOT = {
    "overshoot: off-canvas drawer (minL < area)": ("tool",
        ".app{display:grid;grid-template-columns:minmax(0,1fr);height:100vh;overflow:hidden;position:relative} .app>main{padding:16px;border:1px solid #ccc} .drawer{position:absolute;left:0;top:0;bottom:0;width:300px;background:#eee;transform:translateX(-100%)}",
        f"<div class='app'><aside class='drawer'>抽屜</aside><main>{TEXT}</main></div>"),
    "overshoot: wide table in overflow:auto panel": ("tool",
        ".app{display:grid;grid-template-columns:240px minmax(0,1fr);height:100vh;overflow:hidden} .app>*{padding:16px;border:1px solid #ccc} .sc{overflow:auto}",
        f"<div class='app'><aside>面板</aside><main><div class='sc'><table style='width:3000px'><tr><td>a</td><td>b</td></tr></table></div>{TEXT}</main></div>"),
    "overshoot: carousel track off-screen": ("tool",
        ".app{height:100vh;overflow:hidden;position:relative} .track{display:flex;width:300vw} .pane{width:100vw;padding:16px;border:1px solid #ccc}",
        f"<div class='app'><div class='track'><div class='pane'>{TEXT}</div><div class='pane'>{TEXT}</div><div class='pane'>{TEXT}</div></div></div>"),
    "overshoot: rail translated off-screen": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 48px} #rail{position:fixed;right:0;top:0;bottom:0;width:320px;background:#f8f8f8;border-left:1px solid #ccc;transform:translateX(100%)}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}</main><aside id='rail' data-rail><p>本節速查</p></aside>"),
    "overshoot: paged slide bleeding past its padding": ("deck",
        ".slide{display:none;min-height:100vh;padding:24px 72px} .slide.active{display:block} .bleed{margin:0 -72px;width:calc(100% + 144px);background:#cde;padding:12px}",
        f"<section class='slide active'><div class='bleed'>滿版出血框</div>{TEXT}</section><section class='slide'><div class='bleed'>滿版出血框</div>{TEXT}</section>"),
}


# INFERENCE of an undeclared paged deck whose slide 1 is hidden (fb:1bffdc71, 2026-10-10): the old
# build read slides[0]'s zero height and fell through to document-short. Asserted value: the class.
INFER = {
    "undeclared paged deck, slide 1 hidden": (
        ".slide{min-height:100vh;padding:24px 72px;display:none} .slide.active{display:block}",
        f"<section class='slide'>{SLIDE}</section><section class='slide active'>{SLIDE}</section><section class='slide'>{SLIDE}</section>",
        "deck"),
}


# ---------------------------------------------------------------------------
# IN-PAGE CONSISTENCY (2026-10-31): C2 same-class siblings render alike, S3 rules declared twice under
# different selectors. Every pair is known-true / known-false, and each context filter has a case that the
# filter is the ONLY thing keeping silent (the same page with the filter off reports it; test below).
# The asserted values are the drifting px values and the pair names, never the status label alone.
# ---------------------------------------------------------------------------
WRAP = ".wrap{max-width:900px;margin:0 auto;padding:40px 20px}"
CARD5 = "display:block;border:1px solid #999;border-radius:6px;background:#fafafa;overflow:hidden"


def _sib(r, sel):
    return next((f for f in (r["sibling_drift"] or {}).get("findings", []) if f["sel"] == sel), None)


def _vals(f, prop):
    return {v["v"]: v["n"] for d in (f or {}).get("drift", []) if d["prop"] == prop for v in d["values"]}


def _pairs(r):
    return [(p["a"], p["b"], p["kind"]) for g in (r["duplicate_rules"] or {}).get("groups", []) for p in g["pairs"]]


CONSIST = {
    # name: (css, body, want_status, check(row) -> list of problems)
    "C2 same class, two sizes -> WARN naming 20px and 30px": (
        WRAP + " .t{font-size:20px} .feature .t{font-size:30px}",
        f"<main class='wrap'><h2 class='t'>一</h2><h2 class='t'>二</h2><div class='feature'><h2 class='t'>三</h2></div>{TEXT}</main>", "WARN",
        lambda r: ([] if _vals(_sib(r, "h2.t"), "font-size") == {"20px": 2, "30px": 1} else [f"h2.t font-size {_vals(_sib(r, 'h2.t'), 'font-size')}"])
        + ([] if (r.get("width_status"), r.get("consistency_status")) == ("PASS", "WARN")
           else [f"width_status/consistency_status {r.get('width_status')}/{r.get('consistency_status')}, want PASS/WARN"])),
    "C2 same class, same size -> silent": (
        WRAP + " .t{font-size:20px}",
        f"<main class='wrap'><h2 class='t'>一</h2><h2 class='t'>二</h2><h2 class='t'>三</h2>{TEXT}</main>", "PASS",
        lambda r: [] if not (r["sibling_drift"] or {}).get("findings") else ["unexpected sibling finding"]),
    "C2 different classes, different sizes -> silent": (
        WRAP + " .a{font-size:20px} .b{font-size:30px}",
        f"<main class='wrap'><h2 class='a'>一</h2><h2 class='b'>二</h2>{TEXT}</main>", "PASS",
        lambda r: [] if not (r["sibling_drift"] or {}).get("findings") else ["unexpected sibling finding"]),
    "C2 svg text sized per node -> counted apart, silent": (
        WRAP,
        "<main class='wrap'><svg viewBox='0 0 300 60' width='600'><text class='n' x='5' y='20' font-size='10'>甲</text>"
        f"<text class='n' x='5' y='50' font-size='14'>乙</text></svg>{TEXT}</main>", "PASS",
        lambda r: [] if (r["sibling_drift"]["svg_skipped"] >= 2 and not r["sibling_drift"]["findings"]) else [f"svg_skipped={r['sibling_drift']['svg_skipped']}"]),
    "C2 one em declaration meeting two parents -> silent": (
        WRAP + " .p1{font-size:16px} .p2{font-size:24px} .val{font-size:.9em}",
        f"<main class='wrap'><p class='p1'><span class='val'>甲</span></p><p class='p2'><span class='val'>乙</span></p>{TEXT}</main>", "PASS",
        lambda r: [] if (r["sibling_drift"]["relative_equal"] >= 1 and not r["sibling_drift"]["findings"]) else [f"relative_equal={r['sibling_drift']['relative_equal']}"]),
    "C2 weight only inherited from two parents -> silent": (
        WRAP + " .p1{font-weight:400} .p2{font-weight:700}",
        f"<main class='wrap'><p class='p1'><span class='k'>甲</span></p><p class='p2'><span class='k'>乙</span></p>{TEXT}</main>", "PASS",
        lambda r: [] if (r["sibling_drift"]["inherited_only"] >= 1 and not r["sibling_drift"]["findings"]) else [f"inherited_only={r['sibling_drift']['inherited_only']}"]),
    # A navigation list bolds the current page by `aria-current`: a declared state, not a fork (seen on every
    # research-site-shell page, 2026-10-31). The state splits the group; members of one state still compare.
    "C2 current item marked by aria-current is its own state -> silent": (
        WRAP + " .l1{font-weight:500} .l1[aria-current]{font-weight:700}",
        f"<main class='wrap'><nav><a class='l1' href='#a'>甲</a> <a class='l1' href='#b' aria-current='page'>乙</a> "
        f"<a class='l1' href='#c'>丙</a></nav>{TEXT}</main>", "PASS",
        lambda r: [] if (not r["sibling_drift"]["findings"] and r["sibling_drift"]["state_split"] == 1
                         and {"sel": "a.l1", "n": 2} in [{"sel": g["sel"], "n": g["n"]} for g in r["sibling_drift"]["groups"]])
        else [f"findings {[f['sel'] for f in r['sibling_drift']['findings']]} state_split {r['sibling_drift'].get('state_split')} "
              f"groups {[(g['sel'], g['n']) for g in r['sibling_drift']['groups']]}"]),
    "C2 aria-current=\"false\" is no state: groups with plain items -> WARN naming 500 and 700": (
        WRAP + " .l1{font-weight:500} .l1[aria-current]{font-weight:700}",
        f"<main class='wrap'><nav><a class='l1' href='#a'>甲</a> <a class='l1' href='#b' aria-current='false'>乙</a> "
        f"<a class='l1' href='#c' aria-current=' False '>丙</a></nav>{TEXT}</main>", "WARN",
        lambda r: [] if _vals(_sib(r, "a.l1"), "font-weight") == {"500": 1, "700": 2}
        else [f"a.l1 font-weight {_vals(_sib(r, 'a.l1'), 'font-weight')}"]),
    "C2 two items in the same aria state still compare -> WARN naming 500 and 700": (
        WRAP + " .l1{font-weight:500} .hot .l1{font-weight:700}",
        f"<main class='wrap'><nav><a class='l1' href='#a' aria-current='page'>甲</a> <span class='hot'><a class='l1' href='#b' "
        f"aria-current='page'>乙</a></span></nav>{TEXT}</main>", "WARN",
        lambda r: [] if _vals(_sib(r, "a.l1[aria-current]"), "font-weight") == {"500": 1, "700": 1}
        else [f"a.l1[aria-current] font-weight {_vals(_sib(r, 'a.l1[aria-current]'), 'font-weight')}"]),
    # review 2026-10-31: keyed by value, "page" and "true" fell into two groups of one and a drift between them hid
    "C2 aria-current=\"page\" and =\"true\" are one state and compare -> WARN naming 16px and 20px": (
        WRAP + " .l1{font-size:16px} .l1[aria-current=true]{font-size:20px}",
        f"<main class='wrap'><nav><a class='l1' href='#a' aria-current='page'>甲</a> <a class='l1' href='#b' "
        f"aria-current='true'>乙</a></nav>{TEXT}</main>", "WARN",
        lambda r: [] if _vals(_sib(r, "a.l1[aria-current]"), "font-size") == {"16px": 1, "20px": 1}
        else [f"a.l1[aria-current] font-size {_vals(_sib(r, 'a.l1[aria-current]'), 'font-size')}"]),
    "S3 a card declared twice under two names -> WARN naming both": (
        WRAP + f" .card-a{{{CARD5}}} .card-b{{{CARD5};padding:8px}}",
        f"<main class='wrap'><div class='card-a'>甲</div><div class='card-b'>乙</div>{TEXT}</main>", "WARN",
        lambda r: [] if any({a, b} == {".card-a", ".card-b"} and k == "copy" for a, b, k in _pairs(r)) else [f"pairs {_pairs(r)}"]),
    "S3 two classes sharing only three declarations -> silent": (
        WRAP + " .chip{display:inline-block;padding:2px 10px;font-size:13px;border:1px solid #999} .tag{display:inline-block;padding:2px 10px;font-size:13px;background:#eee}",
        f"<main class='wrap'><span class='chip'>甲</span> <span class='tag'>乙</span>{TEXT}</main>", "PASS",
        lambda r: [] if not _pairs(r) else [f"pairs {_pairs(r)}"]),
    "S3 same class styled in two contexts -> WARN as same-target": (
        WRAP + " .a .lede{font-size:19px;color:#333;margin-top:16px} .b .lede{font-size:19px;color:#333;margin-top:16px}",
        f"<main class='wrap'><div class='a'><p class='lede'>甲</p></div><div class='b'><p class='lede'>乙</p></div>{TEXT}</main>", "WARN",
        lambda r: [] if any({a, b} == {".a .lede", ".b .lede"} and k == "same-target" for a, b, k in _pairs(r)) else [f"pairs {_pairs(r)}"]),
    "S3 hover and focus of one component -> silent (state variants)": (
        WRAP + f" .btn:hover{{{CARD5}}} .btn:focus{{{CARD5}}}",
        f"<main class='wrap'><a class='btn' href='#'>甲</a>{TEXT}</main>", "PASS",
        lambda r: [] if not _pairs(r) else [f"pairs {_pairs(r)}"]),
    "S3 a contextual override of the same component -> silent": (
        WRAP + f" .btn{{{CARD5}}} .bar .btn{{{CARD5}}}",
        f"<main class='wrap'><div class='bar'><a class='btn' href='#'>甲</a></div>{TEXT}</main>", "PASS",
        lambda r: [] if not _pairs(r) else [f"pairs {_pairs(r)}"]),
    "S3 the same selector again inside @media -> silent": (
        WRAP + f" .x{{{CARD5}}} @media (max-width:600px){{.x{{{CARD5}}}}}",
        f"<main class='wrap'><div class='x'>甲</div>{TEXT}</main>", "PASS",
        lambda r: [] if not _pairs(r) else [f"pairs {_pairs(r)}"]),
    # Chromium serialises `border: none` as FOUR longhands (width, style, color, image): uncollapsed, two reset
    # rules sharing it plus `font` and `cursor` read as six shared declarations and WARN; collapsed it is three.
    "S3 `border: none` serialised as four longhands counts once -> silent": (
        WRAP + " .r1{border:none;font:inherit;cursor:pointer;color:red} .r2{border:none;font:inherit;cursor:pointer;color:blue}",
        f"<main class='wrap'><button class='r1'>甲</button><button class='r2'>乙</button>{TEXT}</main>", "PASS",
        lambda r: [] if not _pairs(r) else [f"pairs {_pairs(r)}"]),
}


def check_consist_row(name, want, r):
    """One CONSIST case: the status AND the asserted values (the per-case check reads the finding values)."""
    probs = CONSIST[name][3](r)
    ok = r["status"] == want and not probs
    print(f"{'ok  ' if ok else 'MISS'} {name:62s} want {want:4s} got {r['status']:4s}")
    bad = [] if r["status"] == want else [f"{name}: want {want}, got {r['status']} — " + "; ".join(r["reasons"])]
    return bad + [f"{name}: {p}" for p in probs]


def check_consist_controls(rows):
    """The three every-run consistency controls, on VALUES. Prints the actual lines the report quotes."""
    bad = []
    for r in rows:
        if r["control"] not in ("consistency-bad", "consistency-good", "consistency-clean"):
            continue
        probs = fill_gate.consistency_control_problems(r["control"], r)
        h2 = _sib(r, "h2.section-title")
        print(f"control {r['control']:17s} {r['status']:4s} h2.section-title font-size={_vals(h2, 'font-size') or 'none'} "
              f"forks={len(r['duplicate_rules']['groups'])} thumb-fork={any('.proj-thumb' in a + b for a, b, _ in _pairs(r))} "
              f"standfirst-fork={any('.page-head .standfirst' in a + b for a, b, _ in _pairs(r))}")
        bad += [f"control {r['control']}: {p}" for p in probs]
    return bad


def check_filters_are_load_bearing():
    """Each C2 context filter is the ONLY thing keeping its page silent: with the filters off the same pages
    report. Without this a filter could be dead code (or the whole drift test could be vacuous)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []
    cases = {n: v for n, v in CONSIST.items() if n.startswith("C2 svg") or n.startswith("C2 one em") or n.startswith("C2 weight only")}
    out = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            for name, (css, body, _, _) in cases.items():
                pg = b.new_page(viewport={"width": 1707, "height": 830})
                pg.set_content(BASE.format(attr=' data-page-class="document-short"', title=name, css=css, body=body))
                on = fill_gate.check_consistency(pg, REG, False, suppress=True)["siblings"]["total"]
                off = fill_gate.check_consistency(pg, REG, False, suppress=False)["siblings"]["total"]
                print(f"ok   filter {name[:55]:55s} findings on={on} off={off}" if (on == 0 and off >= 1) else f"MISS filter {name[:55]} on={on} off={off}")
                if not (on == 0 and off >= 1):
                    out.append(f"filter case {name!r}: on={on} off={off} (want 0 with the filter, >= 1 without)")
                pg.close()
        finally:
            b.close()
    return out


def check_promotion():
    """sibling_fail_selectors turns a drift into FAIL for that selector only (empty by default = WARN-only)."""
    css, body, _, _ = CONSIST["C2 same class, two sizes -> WARN naming 20px and 30px"]
    out = []
    with tempfile.TemporaryDirectory() as td:
        p = write_page(td, "promotion", "document-short", css, body)
        for lst, want in (([], "WARN"), (["h2.t"], "FAIL"), (["h3."], "WARN")):
            reg = json.loads(json.dumps(REG)); reg["sibling_fail_selectors"] = lst
            rows = [r for r in fill_gate.gate_paths([p], viewports=[(1707, 830)], controls=False, reg=reg)]
            got = rows[0]["status"]
            print(f"{'ok  ' if got == want else 'MISS'} promotion sibling_fail_selectors={lst} want {want} got {got}")
            if got != want:
                out.append(f"promotion {lst}: want {want}, got {got}")
    if REG.get("sibling_fail_selectors"):
        out.append("sibling_fail_selectors must ship empty (WARN-only by default)")
    return out


def check_forks_pure():
    """S3 as a pure function over rule dumps, no browser: known-true, known-false, and the filters."""
    d5 = ["display: block", "border: 1px solid #999", "border-radius: 6px", "background: #fafafa", "overflow: hidden"]
    R = lambda sel, decl: {"sel": sel, "decl": decl}
    F = fill_gate.find_forks
    out = []

    def expect(name, got, want):
        ok = got == want
        print(f"{'ok  ' if ok else 'MISS'} forks: {name:60s} want {want} got {got}")
        if not ok:
            out.append(f"forks: {name}: want {want}, got {got}")

    n = lambda rules, *a: len(F(rules, 5, 0.8, 2, 0.6, *a)["groups"])
    expect("copy under a new name", n([R(".a", d5), R(".b", d5 + ["padding: 8px"])]), 1)
    expect("four of five shared is below K=5", n([R(".a", d5), R(".b", d5[:4] + ["color: red"])]), 0)
    expect("5 of 8 shared is below R=0.8", n([R(".a", d5 + ["x: 1", "y: 2", "z: 3"]), R(".b", d5 + ["p: 1", "q: 2", "r: 3"])]), 0)
    expect("a selector list sharing a selector (same rule split)", n([R(".a, .b", d5), R(".b", d5)]), 0)
    expect("hover vs focus of one component", n([R(".btn:hover", d5), R(".btn:focus", d5)]), 0)
    expect("contextual override `.bar .btn` of `.btn`", n([R(".btn", d5), R(".bar .btn", d5)]), 0)
    t3 = ["font-size: 19px", "color: #333", "margin-top: 16px"]
    expect("same class in two contexts, 3 of 3", n([R(".p .standfirst", t3), R(".q .standfirst", t3)]), 1)
    expect("same class in two contexts, 2 of 3", n([R(".p .byline", t3), R(".q .byline", t3[:2] + ["margin-top: 12px"])]), 1)
    expect("same class in two contexts, 1 of 3", n([R(".p .byline", t3), R(".q .byline", t3[:1] + ["a: 1", "b: 2"])]), 0)
    expect("shared STATE class is not a shared name", n([R(".tab.is-active", t3), R(".chip.is-active", t3)]), 0)
    expect("tag-only target is not a name (`.p h2` vs `.q h2`)", n([R(".p h2", t3), R(".q h2", t3)]), 0)
    # the collapse: a `font: inherit` serialised as nine longhands is one declaration, not nine
    nine = ["font-family: inherit", "font-feature-settings: inherit", "font-kerning: inherit", "font-optical-sizing: inherit",
            "font-size: inherit", "font-stretch: inherit", "font-style: inherit", "font-variant: inherit", "font-weight: inherit", "line-height: inherit"]
    expect("font longhands collapse to one unit", len(fill_gate.collapse_decls(nine)), 1)
    expect("two resets sharing `font: inherit` + 2 more", n([R(".r1", nine + ["border: 0", "cursor: pointer"]), R(".r2", nine + ["border: 0", "cursor: pointer", "color: red"])]), 0)
    expect("a lone font-size is not collapsed", len(fill_gate.collapse_decls(["font-size: 12px", "color: red"])), 2)
    return out


def check_unread_sheets():
    """A stylesheet the browser did not expose: fetched locally when it is a local file / loopback URL,
    named when still unread; a non-local unread sheet (blocked by the gate itself) adds no line."""
    out = []
    with tempfile.TemporaryDirectory() as td:
        css = pathlib.Path(td) / "a.css"; css.write_text(".k{color:red}", encoding="utf-8")
        got = fill_gate.fetchable_sheet(css.resolve().as_uri())
        if got != ".k{color:red}":
            out.append(f"fetchable_sheet(file) -> {got!r}")
    if fill_gate.fetchable_sheet("https://example.com/a.css") is not None:
        out.append("fetchable_sheet fetched a non-local URL")
    st, lines = fill_gate.consistency_verdict({"duplicate_rules": {"groups": [], "unread": [{"href": "https://fonts.googleapis.com/x", "why": "SecurityError"}]}}, REG)
    if (st, lines) != ("PASS", []):
        out.append(f"non-local unread sheet must be silent, got {(st, lines)}")
    st, lines = fill_gate.consistency_verdict({"duplicate_rules": {"groups": [], "unread": [{"href": "file:///x/a.css", "why": "SecurityError"}]}}, REG)
    if st != "PASS" or len(lines) != 1:
        out.append(f"a local unread sheet must be NAMED without raising the status, got {(st, lines)}")
    print("ok   unread sheets: local fetched, non-local silent, local-unread named" if not out else "MISS unread sheets")
    return out


def _serve_loopback():
    """A loopback server: /ok.css 200, /redir.css 302 to a NON-local URL (never contacted), /big.css 3000 bytes."""
    import http.server
    import threading

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/redir.css", "/redir-local.css"):
                to = "https://example.com/x.css" if self.path == "/redir.css" else f"http://127.0.0.1:{self.server.server_address[1]}/ok.css"
                self.send_response(302); self.send_header("Location", to); self.end_headers(); return
            body = b".k{color:red}" if self.path == "/ok.css" else b"/*" + b"x" * 3000 + b"*/"
            self.send_response(200); self.send_header("Content-Type", "text/css"); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def check_fetch_is_contained():
    """fetchable_sheet stays on loopback: no redirect followed, no proxy used, reads capped (file and http)."""
    import os
    out = []
    srv = _serve_loopback()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    saved = {k: os.environ.get(k) for k in ("http_proxy", "HTTP_PROXY", "no_proxy", "NO_PROXY")}
    try:
        # a system proxy must not be consulted for a loopback fetch: point one at a dead port BEFORE the first
        # fetch (urllib.request.urlopen caches the opener it builds on first use)
        for k in ("http_proxy", "HTTP_PROXY"):
            os.environ[k] = "http://127.0.0.1:9"
        for k in ("no_proxy", "NO_PROXY"):
            os.environ[k] = ""
        got = fill_gate.fetchable_sheet(base + "/ok.css")
        if got != ".k{color:red}":
            out.append(f"loopback sheet not fetched (through a proxy?): {got!r}")
        if fill_gate.fetchable_sheet(base + "/redir.css") is not None:
            out.append("a loopback 302 to a non-local URL was followed (must end as unread)")
        if fill_gate.fetchable_sheet(base + "/redir-local.css") is not None:
            out.append("a loopback 302 to another loopback URL was followed (no redirect is followed at all)")
        if fill_gate.fetchable_sheet(base + "/big.css", max_bytes=1000) is not None:
            out.append("an http sheet over the read cap was returned (want unread)")
        if fill_gate.fetchable_sheet(base + "/big.css", max_bytes=5000) is None:
            out.append("an http sheet under the cap was refused")
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "big.css"; f.write_text("/*" + "x" * 3000 + "*/", encoding="utf-8")
            if fill_gate.fetchable_sheet(f.resolve().as_uri(), max_bytes=1000) is not None:
                out.append("a file sheet over the read cap was returned (want unread)")
            if fill_gate.fetchable_sheet(f.resolve().as_uri(), max_bytes=5000) is None:
                out.append("a file sheet under the cap was refused")
    finally:
        srv.shutdown(); srv.server_close()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print("ok   fetch contained: no redirect, no proxy, capped reads" if not out else "MISS fetch containment")
    return out


def check_import_is_unread():
    """A fetched local sheet that @imports another is NOT fully read (replaceSync ignores @import): the target is named unread."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return []
    out = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "a.css").write_text('/* @import "ghost.css"; */\n@import url("b.css");\n.k{color:red}\n', encoding="utf-8")
        (d / "b.css").write_text(".j{color:blue}", encoding="utf-8")
        page = d / "p.html"
        page.write_text(BASE.format(attr=' data-page-class="document-short"', title="imp", css="", body="<main>x</main>")
                        .replace("</head>", '<link rel="stylesheet" href="a.css"></head>'), encoding="utf-8")
        rows = fill_gate.gate_paths([str(page)], viewports=[(1707, 830)], controls=False)
        un = [u["href"] for u in (rows[0]["duplicate_rules"] or {}).get("unread", [])]
        want = (d / "b.css").resolve().as_uri()
        if un != [want]:
            out.append(f"@import target must be the only unread sheet (comment-out import ignored): want {[want]}, got {un}")
        if not any("b.css" in r for r in rows[0]["reasons"]):
            out.append(f"the unread @import target must be named in the reasons, got {rows[0]['reasons']}")
    print("ok   @import in a fetched sheet is named unread" if not out else "MISS @import unread")
    return out


def check_unitless_line_height_inherits():
    """Two-sided (rung 0): span.val inheriting different unitless line-heights from its parents (html-explainer
    metric 1.3 vs meta line 1.8) is not a drift; one member DECLARING another line-height still is. Asserted
    value: whether span.val's line-height is named (old build: named in both pages)."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return []
    css = ".mv{font-size:20px;line-height:1.3}.meta{font-size:14px;line-height:1.8}.val{font-size:.93em}"
    body = ('<main><div class="mv"><span class="val">12</span></div><div class="mv"><span class="val">3</span></div>'
            '<p class="meta">date <span class="val"{x}>2026-11-02</span></p></main>')
    # known-true near miss (review of 68ca7f14): a px parent hands 24px down to one member, the other DECLARES the
    # parent's ratio (1.5) and renders 18px at the same font-size: a drift that a ratio match alone would hide
    css_px = ".p{font-size:16px;line-height:24px}.val{font-size:12px}"
    body_px = '<main><p class="p"><span class="val">a</span></p><p class="p"><span class="val" style="line-height:1.5">b</span></p></main>'
    got = {}
    with tempfile.TemporaryDirectory() as td:
        for name, c, bd in (("inherited", css, body.replace("{x}", "")),
                            ("declared", css, body.replace("{x}", ' style="line-height:2.4"')),
                            ("px-parent-equal-ratio", css_px, body_px)):
            page = pathlib.Path(td) / f"{name}.html"
            page.write_text(BASE.format(attr=' data-page-class="document-short"', title=name, css=c, body=bd),
                            encoding="utf-8")
            sib = fill_gate.gate_paths([str(page)], viewports=[(1707, 830)], controls=False)[0]["sibling_drift"]
            got[name] = any(f["sel"] == "span.val" and any(d["prop"] == "line-height" for d in f["drift"])
                            for f in (sib or {}).get("findings", []))
    out = [] if got == {"inherited": False, "declared": True, "px-parent-equal-ratio": True} else \
        [f"unitless line-height: want span.val named only when declared, got {got}"]
    print(("ok   " if not out else "MISS ") + f"unitless line-height inherited vs declared {got}")
    return out


def check_consistency_error_keeps_width_verdict():
    """An exception in the consistency stage must not replace the width verdict: a known-bad width fixture stays
    FAIL (exit 1) and the row says the consistency stage did not compute. Monkeypatched on the module."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return []
    out = []
    real = fill_gate.check_consistency
    fill_gate.check_consistency = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected"))
    try:
        bad = str(fill_gate.FIXTURES / "known-bad-left-cap.html")
        good = str(fill_gate.FIXTURES / "known-good-fill.html")
        rows = fill_gate.gate_paths([bad, good], viewports=[(1707, 830)], controls=False)
        if rows[0]["status"] != "FAIL":
            out.append(f"width FAIL lost: got {rows[0]['status']} {rows[0]['reasons']}")
        if not any(r == "consistency not computed: injected" for r in rows[0]["reasons"]):
            out.append(f"missing the reason 'consistency not computed: injected' in {rows[0]['reasons']}")
        if any("could not measure" in r for r in rows[0]["reasons"]):
            out.append("the width row was replaced by a 'could not measure' row")
        # a check that did not run is never a PASS (review 2026-10-31): width stays PASS, consistency reads WARN
        g = rows[1]
        if (g["width_status"], g["consistency_status"], g["status"]) != ("PASS", "WARN", "WARN") \
                or g.get("consistency_error") is None \
                or "consistency not computed: injected" not in g["consistency_reasons"]:
            out.append(f"good width page: want width PASS / consistency WARN / status WARN with the reason, got "
                       f"{g['width_status']} {g['consistency_status']} {g['status']} {g['consistency_reasons']}")
        code = fill_gate.main([bad, "--no-controls", "--viewport", "1707x830"])
        if code != 1:
            out.append(f"exit code with a width FAIL and a consistency error: want 1, got {code}")
        # the control gate must still stop on it: a consistency control that did not measure is an instrument fault
        try:
            fill_gate.gate_paths([], viewports=[(1707, 830)], controls=True)
            out.append("controls passed although the consistency stage raised")
        except RuntimeError:
            pass
    finally:
        fill_gate.check_consistency = real
    print("ok   consistency exception keeps the width FAIL, exit 1" if not out else "MISS consistency-exception isolation")
    return out


def check_width_status_paths():
    """`width_status` is the width-only verdict on every path a caller can meet (render_story S7b reads it):
    a consistency-only finding leaves it PASS, the unknown-class early return still carries it, and the
    S7b consumer reports width and consistency on separate lines. Asserted on the field values."""
    bad = []
    v = fill_gate.verdict({"cls": "zz-unknown", "declared": "zz-unknown"}, REG)
    if not (v.get("width_status") == "WARN" and v.get("consistency_status") == "PASS"
            and any("not in page_classes.json" in x for x in v["reasons"])):
        bad.append(f"unknown class: {v}")
    # S7b consumer on stub rows: no browser, the row dicts are what gate_paths returns
    sys.path.insert(0, str(HERE.parents[2] / "skills" / "paper-story" / "scripts"))
    try:
        import render_story as rs
    except Exception as exc:  # the skill is optional on another host
        print(f"skip S7b consumer test ({exc.__class__.__name__})")
        return bad
    def row(t, ws, cs, ctl=None):
        return {"target": t, "control": ctl, "viewport": "1707x830", "status": "FAIL" if "FAIL" in (ws, cs) else
                ("WARN" if "WARN" in (ws, cs) else "PASS"), "width_status": ws, "consistency_status": cs,
                "consistency_reasons": [] if cs == "PASS" else ["duplicate rules: .a and .b share 5"],
                "reach": 0.9, "reasons": ["reach 61% < 85%"] if ws != "PASS" else []}
    cases = {
        "consistency WARN only": ([row("a.html", "PASS", "WARN")], [("S7b", "WARN", "in-page consistency"), ("S7b", "PASS", "measured fill")]),
        "width FAIL only": ([row("b.html", "FAIL", "PASS")], [("S7b", "FAIL", "measured fill")]),
        "promoted consistency FAIL": ([row("c.html", "PASS", "FAIL")], [("S7b", "FAIL", "in-page consistency"), ("S7b", "PASS", "measured fill")]),
        "control rows ignored": ([row("d.html", "FAIL", "FAIL", ctl="known-bad")], [("S7b", "PASS", "measured fill")]),
        "row without new keys falls back to status": ([{"target": "e.html", "control": None, "viewport": "1707x830", "status": "FAIL",
                                                        "reach": 0.5, "reasons": ["reach 50%"]}], [("S7b", "FAIL", "measured fill")]),
    }
    real = fill_gate.gate_paths
    try:
        for name, (rows, want) in cases.items():
            fill_gate.gate_paths = lambda *a, _r=rows, **k: _r
            G = rs.Gates()
            rs.s7b_fill([pathlib.Path("x.html")], G)
            got = [(g, s, m.split(":")[0].split(" on ")[0]) for g, s, m in G.rows]
            ok = len(got) == len(want) and all(g == wg and s == ws and m.startswith(wm) for (g, s, m), (wg, ws, wm) in zip(got, want))
            print(f"{'ok  ' if ok else 'MISS'} S7b {name}: {[(g, s, m) for g, s, m in got]}")
            if not ok:
                bad.append(f"S7b {name}: want {want} got {got}")
    finally:
        fill_gate.gate_paths = real
    return bad


def check_promoted_first():
    """A promoted finding is listed first however many other groups there are (JS 40-cut and verdict 6-line cut),
    and an empty prefix is refused by the loader and ignored by the verdict."""
    out = []
    f = lambda sel, n: {"sel": sel, "n": n, "drift": [{"prop": "font-size", "values": [{"v": "20px", "n": 1, "ex": ""}, {"v": "30px", "n": 1, "ex": ""}]}]}
    reg = {"sibling_fail_selectors": ["h2.zz"]}
    cons = {"siblings": {"findings": [f(f"p.c{i}", 9) for i in range(8)] + [f("h2.zz", 2)]}}
    st, lines = fill_gate.consistency_verdict(cons, reg)
    if st != "FAIL" or "h2.zz" not in lines[0] or "[promoted to FAIL]" not in lines[0]:
        out.append(f"promoted finding must be line 1 of a FAIL, got {st} {lines[:2]}")
    st, _ = fill_gate.consistency_verdict(cons, {"sibling_fail_selectors": [""]})
    if st != "WARN":
        out.append(f"an empty prefix must not promote anything, got {st}")
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "reg.json"
        p.write_text(json.dumps({**REG, "sibling_fail_selectors": [""]}), encoding="utf-8")
        try:
            fill_gate.load_registry(p)
            out.append("load_registry accepted an empty-string prefix")
        except RuntimeError:
            pass
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return out
    groups = "".join(f"<p class='c{i}' style='font-size:20px'>a</p><p class='c{i}' style='font-size:30px'>b</p><p class='c{i}' style='font-size:20px'>c</p>" for i in range(45))
    groups += "<h2 class='zz' style='font-size:20px'>a</h2><h2 class='zz' style='font-size:30px'>b</h2>"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1707, "height": 830})
            pg.set_content(BASE.format(attr="", title="cut", css="", body=groups))
            for prefixes, want_first in (([], "p.c"), (["h2.zz"], "h2.zz")):
                got = fill_gate.check_consistency(pg, {**REG, "sibling_fail_selectors": prefixes}, False)["siblings"]
                first = got["findings"][0]["sel"]
                print(f"{'ok  ' if first.startswith(want_first) else 'MISS'} promote={prefixes} total={got['total']} kept={len(got['findings'])} first={first}")
                if not first.startswith(want_first) or got["total"] != 46 or len(got["findings"]) != 40:
                    out.append(f"promote={prefixes}: want first {want_first!r}, total 46, 40 kept; got {first!r}, {got['total']}, {len(got['findings'])}")
                if prefixes == [] and any(x["sel"] == "h2.zz" for x in got["findings"]):
                    out.append("control broken: h2.zz survived the 40 cut without promotion, the cut is not exercised")
        finally:
            b.close()
    return out


def check_bounds_and_counts():
    """N3: S3 cost is bounded and says what it did not compare. N4: the C2 set-aside counts print beside findings."""
    out = []
    d5 = ["display: block", "border: 1px solid #999", "border-radius: 6px", "background: #fafafa", "overflow: hidden"]
    R = lambda sel: {"sel": sel, "decl": d5}
    base = fill_gate.find_forks([R(".a"), R(".b")], 5, 0.8)
    capped = fill_gate.find_forks([R(".a"), R(".b")], 5, 0.8, posting_cap=1)
    short = fill_gate.find_forks([R(".a"), R(".b")], 5, 0.8, max_rules=1)
    if (len(base["groups"]), base["not_checked"]) != (1, {"rules": 0, "common_decls": 0}):
        out.append(f"uncapped baseline wrong: {base['groups']!r} {base['not_checked']}")
    if (len(capped["groups"]), capped["not_checked"]["common_decls"]) != (0, 5):
        out.append(f"posting cap must drop the 5 shared declarations and report them, got {len(capped['groups'])} {capped['not_checked']}")
    if (len(short["groups"]), short["not_checked"]["rules"]) != (0, 1):
        out.append(f"rule cap must leave 1 rule uncompared and report it, got {len(short['groups'])} {short['not_checked']}")
    # a real pile: 400 rules sharing one boilerplate declaration must not cost 80k pairs
    pile = fill_gate.find_forks([{"sel": f".r{i}", "decl": ["margin: 0"] + [f"p{i}: 1", f"q{i}: 2", f"r{i}: 3", f"s{i}: 4", f"t{i}: 5"]} for i in range(400)], 5, 0.8)
    if pile["pairs"] != 0 or pile["not_checked"]["common_decls"] != 1:
        out.append(f"boilerplate pile: want 0 pairs and 1 skipped declaration, got {pile['pairs']} {pile['not_checked']}")
    st, lines = fill_gate.consistency_verdict({"duplicate_rules": {"groups": [], "not_checked": {"rules": 7, "common_decls": 2}}}, REG)
    if st != "PASS" or len(lines) != 1 or "7 style rule(s)" not in lines[0] or "2 declaration(s)" not in lines[0]:
        out.append(f"the not-compared line must name both counts without changing the status, got {(st, lines)}")
    # N4
    sib = {"groups_compared": 12, "svg_skipped": 3, "relative_equal": 4, "inherited_only": 5,
           "findings": [{"sel": "h2.t", "n": 3, "drift": [{"prop": "font-size", "values": [{"v": "20px", "n": 2, "ex": ""}, {"v": "30px", "n": 1, "ex": ""}]}]}]}
    st, lines = fill_gate.consistency_verdict({"siblings": sib}, REG)
    last = lines[-1] if lines else ""
    if not all(x in last for x in ("12 group(s)", "3 svg", "4 relative-equal", "5 inherited-only")):
        out.append(f"set-aside counts missing from the reason line: {last!r}")
    st, lines = fill_gate.consistency_verdict({"siblings": {**sib, "findings": []}}, REG)
    if (st, lines) != ("PASS", []):
        out.append(f"a page with no finding must stay silent, got {(st, lines)}")
    print("ok   S3 bounded and reports not-checked; C2 set-aside counts printed" if not out else "MISS bounds/counts")
    return out


def check_controls_must_measure():
    """A consistency control that never measured (None -> {}) satisfies every absence assertion; the ran-check
    must refuse it. Mutants: no result at all, zero rules, an unread sheet, the h2 group missing or at n=3."""
    out = []
    ok_row = {"sibling_drift": {"groups_compared": 2, "findings": [], "groups": [{"sel": "h2.section-title", "n": 4}]},
              "duplicate_rules": {"rules": 120, "unread": [], "groups": []}}
    mut = lambda **kw: {**ok_row, **kw}
    cases = {
        "good: measured, no drift": (ok_row, True),
        "no result at all": ({"sibling_drift": None, "duplicate_rules": None}, False),
        "zero rules parsed": (mut(duplicate_rules={"rules": 0, "unread": [], "groups": []}), False),
        "an unread sheet": (mut(duplicate_rules={"rules": 120, "unread": [{"href": "file:///x.css"}], "groups": []}), False),
        "no group compared": (mut(sibling_drift={"groups_compared": 0, "findings": [], "groups": []}), False),
        "h2.section-title group absent": (mut(sibling_drift={"groups_compared": 2, "findings": [], "groups": []}), False),
        "h2.section-title group at n=3": (mut(sibling_drift={"groups_compared": 2, "findings": [], "groups": [{"sel": "h2.section-title", "n": 3}]}), False),
    }
    for name, (row, want_ok) in cases.items():
        got_ok = fill_gate.consistency_control_problems("consistency-good", row) == []
        if got_ok != want_ok:
            out.append(f"consistency-good ran-check: {name}: want accepted={want_ok}, got {got_ok}")
    if fill_gate.consistency_control_problems("consistency-clean", {"sibling_drift": None, "duplicate_rules": None}) == []:
        out.append("consistency-clean accepted a row that never measured")
    print("ok   controls must have measured (7 good/mutant rows)" if not out else "MISS controls-must-measure")
    return out


def check_loopback():
    """Pure check of the route filter: loopback continues, everything else aborts (fb:072d2f5d)."""
    want = {"http://localhost:4321/a.css": True, "http://127.0.0.1:8000/": True, "http://[::1]:3000/x": True,
            "http://site.localhost/": True, "https://example.com/a.js": False, "http://localhost.evil.com/": False,
            "http://10.0.0.5/": False}
    return [f"loopback: {u} -> {fill_gate.is_local(u)}, want {w}" for u, w in want.items() if fill_gate.is_local(u) != w]


def write_page(td, name, cls, css, body):
    p = pathlib.Path(td) / (re.sub(r"[^A-Za-z0-9._-]+", "_", name.replace("%", "pct")) + ".html")
    attr = f' data-page-class="{cls}"' if cls else ""
    p.write_text(BASE.format(attr=attr, title=name, css=css, body=body), encoding="utf-8")
    return str(p)


def run_cases(td):
    """Write every fixture, run the gate once. Returns (rows, expect) -- raises RuntimeError if the instrument is absent."""
    paths, expect = [], {}
    for name, (cls, css, body, want) in CASES.items():
        p = write_page(td, name, cls, css, body); paths.append(p); expect[p] = ("case", name, want)
    for name, (css, body, want) in PAGED.items():
        p = write_page(td, name, "deck", css, body); paths.append(p); expect[p] = ("paged", name, want)
    for name, (cls, css, body) in OVERSHOOT.items():
        p = write_page(td, name, cls, css, body); paths.append(p); expect[p] = ("overshoot", name, None)
    for name, (css, body, want) in INFER.items():
        p = write_page(td, name, None, css, body); paths.append(p); expect[p] = ("infer", name, want)
    for name, (css, body, want, _) in CONSIST.items():
        p = write_page(td, "consist " + name, "document-short", css, body); paths.append(p); expect[p] = ("consist", name, want)
    return fill_gate.gate_paths(paths, viewports=[(1707, 830)], controls=True), expect


def check_paged(name, want, r):
    """Per-slide assertions for one paged-deck row; returns a list of failure strings (empty = ok)."""
    bad, areas = [], r["areas"]
    if len(areas) != 3:
        return [f"{name}: expected 3 measured slides, got {len(areas)}"]
    if want == "PASS":
        for a in areas:
            if a["n"] == 0 or a["reach"] < 0.85:
                bad.append(f"{name}: slide {a['index']} n={a['n']} reach={a['reach']:.0%} (a shown slide would fill >= 85 %)")
        if r["status"] != "PASS":
            bad.append(f"{name}: want PASS on every slide, got {r['status']} — " + "; ".join(r["reasons"]))
    else:
        s2 = areas[1]
        if r["status"] != "FAIL":
            bad.append(f"{name}: want FAIL, got {r['status']} — " + "; ".join(r["reasons"]))
        if s2["n"] == 0 or s2["findings_total"] < 1:
            bad.append(f"{name}: slide 2 n={s2['n']} findings={s2['findings_total']} (want the lone block measured AND reported as a finding)")
        if not any(w.startswith("slide 2:") and "left-anchored" in w for w in r["reasons"]):
            bad.append(f"{name}: no 'slide 2: ... left-anchored' reason in {r['reasons']}")
        for a in (areas[0], areas[2]):
            if a["reach"] < 0.85:
                bad.append(f"{name}: slide {a['index']} should still fill, reach={a['reach']:.0%}")
    return bad


def check_overshoot(name, r):
    bad = []
    for a in r["areas"] or [{"index": None, "reach": r["reach"], "fill": r["fill"]}]:
        for k in ("reach", "fill"):
            if not (0 <= a[k] <= 1.0):
                bad.append(f"{name}: {k}={a[k]} outside [0, 1] (slide {a['index']})")
    return bad


def main() -> int:
    failures = []
    # registry shape: every class has a mode and at least one threshold
    for name, row in REG["classes"].items():
        if row.get("mode") not in ("centered", "fill", "centered-or-fill") or not (row.get("min_fill") or row.get("symmetry_px")):
            failures.append(f"registry row {name!r} lacks mode/threshold")
    covered = {c[0] for c in CASES.values() if c[0]}
    for name in REG["classes"]:
        sides = {CASES[k][3] for k in CASES if CASES[k][0] == name}
        if name not in covered or not ({"PASS"} & sides) or not ({"FAIL", "WARN"} & sides):
            failures.append(f"class {name!r} has no two-sided fixture pair in this test")
    with tempfile.TemporaryDirectory() as td:
        try:
            rows, expect = run_cases(td)
        except RuntimeError as exc:
            print(f"SKIP: {exc}"); return 2
        for r in rows:
            if r["control"]:
                print(f"control {r['control']:17s} {r['status']}"); continue
            kind, name, want = expect[r["target"]]
            if kind == "consist":
                failures += check_consist_row(name, want, r)
            elif kind == "case":
                ok = r["status"] == want
                if want == "PASS" and r["reasons"]:   # the width fixtures must stay free of consistency noise
                    failures.append(f"{name}: a PASS width case carries reasons {r['reasons']}")
                print(f"{'ok  ' if ok else 'MISS'} {name:42s} want {want:4s} got {r['status']:4s} reach={r['reach']:.0%} voidL/R={r['left_void']}/{r['right_void']} class={('inferred:' if r['inferred'] else '')+str(r['class'])}")
                if not ok:
                    failures.append(f"{name}: want {want}, got {r['status']} — " + "; ".join(r["reasons"]))
            elif kind == "paged":
                bad = check_paged(name, want, r)
                per = " ".join(f"s{a['index']}:n={a['n']}/{a['reach']:.0%}" for a in r["areas"])
                print(f"{'ok  ' if not bad else 'MISS'} {name:42s} want {want:4s} got {r['status']:4s} {per}")
                failures += bad
            elif kind == "infer":
                ok = r["class"] == want and r["inferred"]
                print(f"{'ok  ' if ok else 'MISS'} {name:42s} want class {want} got {r['class']} (inferred={r['inferred']})")
                if not ok:
                    failures.append(f"{name}: inferred class {r['class']}, want {want}")
            else:
                bad = check_overshoot(name, r)
                per = " ".join(f"{('s'+str(a['index'])+':') if a.get('index') else ''}reach={a['reach']:.3f},fill={a['fill']:.3f}" for a in (r["areas"] or [r]))
                print(f"{'ok  ' if not bad else 'MISS'} {name:50s} {per}")
                failures += bad
        failures += check_consist_controls(rows)
        failures += check_restore()
        failures += check_loopback()
    failures += check_forks_pure()
    failures += check_unread_sheets()
    failures += check_fetch_is_contained()
    failures += check_import_is_unread()
    failures += check_bounds_and_counts()
    failures += check_controls_must_measure()
    failures += check_filters_are_load_bearing()
    failures += check_promotion()
    failures += check_promoted_first()
    failures += check_consistency_error_keeps_width_verdict()
    failures += check_unitless_line_height_inherits()
    failures += check_width_status_paths()
    print("\n".join(failures) if failures else "test_fill_gate: PASS (all classes two-sided, controls fired)")
    return 1 if failures else 0


def check_restore():
    """The slide shown for measurement is put back EXACTLY: the DOM before == the DOM after."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []
    page_html = BASE.format(attr=' data-page-class="deck"', title="restore", css=PAGED_CSS + " .slide{display:none} .slide.active{display:block} .page{display:none}",
        body=f"<section class='slide active'>{SLIDE}</section>"
             f"<section class='slide' style='display:none;color:red'>{SLIDE}</section>"
             f"<section class='slide' style='visibility:hidden' hidden>{SLIDE}</section>"
             f"<div class='page' hidden><section class='slide'>{SLIDE}</section></div>")
    opts = {"asym": 0.15, "scope": ".slide", "maxScopes": 8, "backdrop": False}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1707, "height": 830})
            pg.set_content(page_html)
            before = pg.evaluate("() => document.documentElement.outerHTML")
            meas = pg.evaluate(fill_gate.MEASURE_JS, opts)
            after = pg.evaluate("() => document.documentElement.outerHTML")
        finally:
            b.close()
    out = []
    if before != after:
        out.append("restore: DOM changed by the measurement\n  before: " + before[-420:] + "\n  after:  " + after[-420:])
    if [s["n"] > 0 for s in meas["scopes"]] != [True, True, True, True]:
        out.append(f"restore fixture: every slide should have been measured, got n={[s['n'] for s in meas['scopes']]}")
    return out


# ---- pytest entry points (python -X utf8 -m pytest tools/page-fill-gate/tests -q) ----
try:
    import pytest
except ImportError:  # the script runner above needs no pytest
    pytest = None

if pytest is not None:
    @pytest.fixture(scope="module")
    def gated(tmp_path_factory):
        td = tmp_path_factory.mktemp("fillgate")
        try:
            rows, expect = run_cases(str(td))
        except RuntimeError as exc:
            pytest.skip(f"instrument unavailable: {exc}")
        return {expect[r["target"]][1]: (expect[r["target"]], r) for r in rows if not r["control"]}

    def test_registry_rows_have_mode_and_threshold():
        for name, row in REG["classes"].items():
            assert row.get("mode") in ("centered", "fill", "centered-or-fill") and (row.get("min_fill") or row.get("symmetry_px")), name

    def test_every_class_has_a_two_sided_pair():
        covered = {c[0] for c in CASES.values() if c[0]}
        for name in REG["classes"]:
            sides = {CASES[k][3] for k in CASES if CASES[k][0] == name}
            assert name in covered and "PASS" in sides and sides & {"FAIL", "WARN"}, name

    @pytest.mark.parametrize("name", list(CASES))
    def test_case_verdict(gated, name):
        (_, _, want), r = gated[name]
        assert r["status"] == want, "; ".join(r["reasons"])

    @pytest.mark.parametrize("name", list(PAGED))
    def test_paged_deck(gated, name):
        (_, _, want), r = gated[name]
        assert check_paged(name, want, r) == []

    @pytest.mark.parametrize("name", list(OVERSHOOT))
    def test_fractions_stay_within_one(gated, name):
        _, r = gated[name]
        assert check_overshoot(name, r) == []

    def test_forced_visible_slide_is_restored_exactly():
        pytest.importorskip("playwright")
        assert check_restore() == []

    @pytest.mark.parametrize("name", list(CONSIST))
    def test_consistency_case(gated, name):
        (_, _, want), r = gated[name]
        assert check_consist_row(name, want, r) == []

    def test_width_pass_cases_carry_no_consistency_noise(gated):
        for name in CASES:
            (_, _, want), r = gated[name]
            if want == "PASS":
                assert r["reasons"] == [], name

    def test_consistency_controls_read_the_right_values():
        pytest.importorskip("playwright")
        try:
            rows = fill_gate.gate_paths([], viewports=[(1707, 830)], controls=True)
        except RuntimeError as exc:
            pytest.skip(f"instrument unavailable: {exc}")
        got = {r["control"]: r for r in rows if r["control"] in fill_gate.CONSISTENCY_CONTROLS.values()}
        assert set(got) == {"consistency-bad", "consistency-good", "consistency-clean"}
        for label, r in got.items():
            assert fill_gate.consistency_control_problems(label, r) == [], label
        assert _vals(_sib(got["consistency-bad"], "h2.section-title"), "font-size") == {"22px": 2, "32px": 2}

    def test_forks_pure_function():
        assert check_forks_pure() == []

    def test_unread_sheets_are_fetched_or_named():
        assert check_unread_sheets() == []

    def test_sheet_fetch_stays_on_loopback_and_capped():
        assert check_fetch_is_contained() == []

    def test_import_in_a_fetched_sheet_is_named_unread():
        pytest.importorskip("playwright")
        assert check_import_is_unread() == []

    def test_width_status_is_width_only_on_every_path_and_s7b_reads_it():
        assert check_width_status_paths() == []

    def test_consistency_controls_refuse_a_row_that_never_measured():
        assert check_controls_must_measure() == []

    def test_s3_is_bounded_and_c2_set_aside_counts_print():
        assert check_bounds_and_counts() == []

    def test_promoted_finding_survives_the_cuts_and_empty_prefix_is_refused():
        pytest.importorskip("playwright")
        assert check_promoted_first() == []

    def test_consistency_exception_keeps_the_width_fail_and_exit_1():
        pytest.importorskip("playwright")
        assert check_consistency_error_keeps_width_verdict() == []

    def test_each_c2_filter_is_load_bearing():
        pytest.importorskip("playwright")
        assert check_filters_are_load_bearing() == []

    def test_sibling_promotion_is_per_selector_and_off_by_default():
        pytest.importorskip("playwright")
        assert check_promotion() == []


if __name__ == "__main__":
    sys.exit(main())
