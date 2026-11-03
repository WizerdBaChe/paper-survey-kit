"""Build the FICTIONAL demo paper `paper.pdf` (and its figure PNGs) used by this kit's examples.

Everything in it is invented: authors, journal, data, references. It exists so the kit can show a full
run without reproducing any copyrighted paper. It is written to be worth auditing: a clean story, a
deliberate abstract-vs-body mismatch, an untested condition, a borrowed baseline and a second result
with a thin sample, so the evidence audit and the drift checklist have something real to find.

  python make_paper.py            -> paper.pdf + figs/fig1..fig4.png beside this file
Needs: matplotlib, PyMuPDF (fitz). Deterministic: no randomness, fixed fonts.
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
FIGS = HERE / "figs"

TITLE = "Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics"
AUTHORS = "Ada Placeholder, Ben Fixture and Cleo Mockridge"
AFFIL = "Department of Imaginary Engineering, Example Institute (fictional)"
VENUE = "Journal of Imaginary Microfluidics 1, 101-108 (2026)  ·  FICTIONAL TEST PAPER - not a real study"

L_MM = [1, 2, 3, 4, 5]
DELAY_S = [42, 118, 236, 395, 612]          # mean delay per bridge length (n = 5 each)
DELAY_SD = [4, 11, 24, 46, 81]
CV_BRIDGE = [9.5, 9.3, 10.2, 11.6, 13.2]   # % coefficient of variation


def fig1(p: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.6), dpi=160)
    ax.set_xlim(0, 100); ax.set_ylim(0, 36); ax.axis("off")
    ax.add_patch(Rectangle((4, 14), 92, 8, color="#f2efe6", ec="#6b6b6b"))
    ax.add_patch(Rectangle((40, 14), 16, 8, color="#c9b27c", ec="#6b5a2e", hatch="///"))
    ax.add_patch(FancyBboxPatch((4, 12), 12, 12, boxstyle="round,pad=0.5", color="#9ec5e8", ec="#3a6d99"))
    ax.add_patch(FancyBboxPatch((84, 12), 12, 12, boxstyle="round,pad=0.5", color="#d9ead3", ec="#5b8a4a"))
    ax.text(10, 27, "inlet\n(reagent B)", ha="center", fontsize=8)
    ax.text(48, 27, "wax delay bridge\nlength L", ha="center", fontsize=8)
    ax.text(90, 27, "detection\nzone", ha="center", fontsize=8)
    ax.text(26, 9, "cellulose channel (w = 2 mm)", ha="center", fontsize=8)
    ax.annotate("", xy=(56, 6), xytext=(40, 6), arrowprops=dict(arrowstyle="<->"))
    ax.text(48, 1.5, "L = 1-5 mm, 120 °C for 60 s", ha="center", fontsize=8)
    fig.tight_layout(); fig.savefig(p); plt.close(fig)


def fig2(p: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=160)
    ax.errorbar(L_MM, DELAY_S, yerr=DELAY_SD, fmt="o", color="#2b5d8a", capsize=3, label="measured (n = 5)")
    xs = [1 + i * 0.05 for i in range(81)]
    ax.plot(xs, [24.6 * x ** 2 for x in xs], "--", color="#b5651d", label="fit  t = k·L², R² = 0.97")
    ax.set_xlabel("bridge length L (mm)"); ax.set_ylabel("delay time (s)")
    ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(p); plt.close(fig)


def fig3(p: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=160)
    labels = [f"{l} mm" for l in L_MM] + ["sugar barrier\n(ref. [3])"]
    vals = CV_BRIDGE + [25.0]
    cols = ["#2b5d8a"] * 5 + ["#9a9a9a"]
    ax.bar(range(6), vals, color=cols)
    ax.set_xticks(range(6), labels, fontsize=7)
    ax.set_ylabel("coefficient of variation (%)")
    ax.axhline(15, ls=":", color="#b5651d"); ax.text(5.4, 15.6, "15 %", fontsize=7, ha="right")
    fig.tight_layout(); fig.savefig(p); plt.close(fig)


def fig4(p: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.6, 3.0), dpi=160)
    ax.bar([0, 1], [0.21, 0.38], yerr=[0.04, 0.05], color=["#9a9a9a", "#2b5d8a"], capsize=4)
    ax.set_xticks([0, 1], ["simultaneous\ndelivery", "timed release\n(L = 3 mm)"], fontsize=8)
    ax.set_ylabel("colour intensity (a.u.)"); ax.set_ylim(0, 0.5)
    fig.tight_layout(); fig.savefig(p); plt.close(fig)


BODY = [
    ("Abstract", [
        "Multi-step assays on paper need reagents to arrive in sequence, yet most paper devices deliver "
        "everything at once. We print a partially fused wax bridge across a cellulose channel and show that "
        "its length sets a reproducible delay. Bridges of 1 to 5 mm delay the fluid front by 42 to 612 s, the "
        "delay follows the square of the bridge length, and the variation stays below 15 %. The approach "
        "provides delays of up to 15 minutes, is robust across ambient humidity, and doubles the signal of a "
        "two-step colour assay. Wax delay bridges need no extra material and no moving part.",
    ]),
    ("1. Introduction", [
        "Paper microfluidic devices are cheap and need no pump, which makes them attractive for testing outside "
        "a laboratory [1]. Many useful assays, however, are multi-step: a sample must meet one reagent, wait, and "
        "only then meet a second reagent. When all reagents wick at once, the steps overlap and the signal drops.",
        "Two families of timing elements exist. Dissolvable sugar barriers dissolve after a while and let the "
        "fluid pass, but their delay varies strongly from device to device [3]. Mechanical or magnetic valves "
        "give precise timing but add parts and assembly steps that undo the low cost of paper [2].",
        "We ask whether the wax printing step that already defines the channels can also define the timing. A "
        "short region where wax is only partially melted into the paper lowers the local permeability without "
        "blocking the channel. If the fluid front slows in proportion to the bridge length squared, as a "
        "Washburn-type model predicts, the delay becomes a printed dimension rather than a material property.",
    ]),
    ("2. Methods", [
        "2.1 Device fabrication. Channels 2 mm wide and 40 mm long were wax-printed on chromatography paper and "
        "heated at 150 °C for 120 s to form full barriers. Delay bridges of length L = 1, 2, 3, 4 and 5 mm were "
        "then printed across the channel and heated at 120 °C for 60 s, which melts the wax only partly into "
        "the paper (Fig. 1).",
        "2.2 Delay measurement. A 20 µL drop of dyed buffer was placed at the inlet and the front was filmed at "
        "30 frames per second. The delay time is the extra time the front needs to reach the detection zone "
        "compared with a channel without a bridge. Five devices were measured for each length at 23 °C and "
        "45 % relative humidity.",
        "2.3 Model. Treating the bridge as a porous section of lower permeability, the Washburn relation gives "
        "a delay t = k·L², where k collects viscosity, surface tension and the effective pore radius. We fit k "
        "by least squares to the five mean delays.",
        "2.4 Two-step assay. A colour assay in which reagent A must bind before reagent B arrives was run with "
        "simultaneous delivery and with reagent B behind a 3 mm bridge, three devices each. Intensity was read "
        "from photographs in the green channel.",
    ]),
    ("3. Results", [
        "3.1 Delay follows the square of the bridge length. The mean delay rose from 42 s at L = 1 mm to 612 s at "
        "L = 5 mm (Fig. 2). The quadratic model with k = 24.6 s/mm² fits the means with R² = 0.97. The spread "
        "grows with length: the standard deviation is 4 s at 1 mm and 81 s at 5 mm.",
        "3.2 The delay is reproducible. The coefficient of variation stays between 9.3 % and 13.2 % for all "
        "lengths (Fig. 3), below the 25 % reported for sugar barriers [3]. Table 1 compares the three timing "
        "approaches.",
        "Table 1. Timing elements for paper microfluidics. Wax delay bridge: delay 42-612 s, variation 9-13 %, "
        "no added material. Sugar barrier [3]: delay 60-900 s, variation about 25 %, added sugar layer. "
        "Mechanical valve [2]: delay set by the user, variation below 5 %, added parts and assembly.",
        "3.3 Timed release improves a two-step assay. With reagent B delayed by a 3 mm bridge the colour "
        "intensity was 0.38 ± 0.05 a.u., against 0.21 ± 0.04 a.u. for simultaneous delivery, an increase of "
        "1.8 times (Fig. 4).",
    ]),
    ("4. Discussion", [
        "The quadratic trend supports the picture of the bridge as a porous section of lower permeability. "
        "Longer bridges give longer delays but also a larger absolute spread, so very long delays will need a "
        "tighter control of the heating step. All measurements were made at one humidity; paper and wax both "
        "respond to moisture, and we expect the constant k to shift at other humidities. The sugar-barrier "
        "variation is taken from the literature rather than measured side by side with our devices.",
    ]),
    ("5. Conclusion", [
        "A partially fused wax bridge turns timing into a printed length. Delays of 42 to 612 s with a variation "
        "below 15 % were obtained with no added material, and a two-step assay gave 1.8 times the signal of "
        "simultaneous delivery. Wax delay bridges are a practical way to sequence reagents on paper.",
    ]),
    ("References", [
        "[1] A. Placeholder, Paper devices outside the lab, J. Imag. Microfluid. 0, 1-9 (2025). (fictional)",
        "[2] B. Fixture, Magnetic valves on paper, Imag. Lab Chip 3, 10-18 (2024). (fictional)",
        "[3] C. Mockridge, Sugar barriers for delayed wicking, Imag. Anal. Methods 7, 55-61 (2023). (fictional)",
    ]),
]
CAPTIONS = {
    "fig1": "Fig. 1. Device layout. A wax delay bridge of length L is printed across a 2 mm cellulose channel "
            "between the inlet and the detection zone and heated at 120 °C for 60 s.",
    "fig2": "Fig. 2. Delay time against bridge length. Points: mean ± standard deviation of five devices; dashed "
            "line: quadratic fit t = k·L² with k = 24.6 s/mm².",
    "fig3": "Fig. 3. Coefficient of variation of the delay for each bridge length, with the value reported for "
            "sugar barriers in ref. [3] (grey). Dotted line: 15 %.",
    "fig4": "Fig. 4. Two-step colour assay with simultaneous delivery and with reagent B behind a 3 mm bridge "
            "(mean ± standard deviation, three devices each).",
}
FIG_AFTER = {"1. Introduction": "fig1", "3.1": "fig2", "3.2": "fig3", "3.3": "fig4"}


class Writer:
    W, H, M = 595, 842, 56

    def __init__(self) -> None:
        self.doc = fitz.open()
        self.new_page()

    def new_page(self) -> None:
        self.page = self.doc.new_page(width=self.W, height=self.H)
        self.y = self.M
        n = len(self.doc)
        self.page.insert_text((self.M, self.H - 30), f"FICTIONAL TEST PAPER  ·  page {n}", fontsize=7, color=(0.45, 0.45, 0.45))

    def text(self, s: str, size: float = 10, bold: bool = False, gap: float = 6) -> None:
        font = "tibo" if bold else "tiro"
        width = self.W - 2 * self.M
        need = fitz.get_text_length(s, fontname=font, fontsize=size) / width * size * 1.35 + size * 2
        if bold:
            need += 90  # keep a heading with the start of its section
        if self.y + need > self.H - 60:
            self.new_page()
        rect = fitz.Rect(self.M, self.y, self.W - self.M, self.H - 50)
        rest = self.page.insert_textbox(rect, s, fontsize=size, fontname=font, lineheight=1.3)
        used = (rect.height - rest) if rest >= 0 else rect.height
        self.y += used + gap

    def image(self, png: Path, caption: str, width: float = 400) -> None:
        import PIL.Image
        with PIL.Image.open(png) as im:
            h = width * im.height / im.width
        if self.y + h + 50 > self.H - 60:
            self.new_page()
        x0 = (self.W - width) / 2
        self.page.insert_image(fitz.Rect(x0, self.y, x0 + width, self.y + h), filename=str(png))
        self.y += h + 8
        self.text(caption, size=8.5, gap=12)


def main() -> None:
    FIGS.mkdir(exist_ok=True)
    for name, fn in (("fig1", fig1), ("fig2", fig2), ("fig3", fig3), ("fig4", fig4)):
        fn(FIGS / f"{name}.png")
    w = Writer()
    w.text(TITLE, size=16, bold=True, gap=8)
    w.text(AUTHORS, size=10.5, gap=2)
    w.text(AFFIL, size=9, gap=2)
    w.text(VENUE, size=8.5, gap=14)
    for head, paras in BODY:
        w.text(head, size=11.5, bold=True, gap=4)
        for para in paras:
            w.text(para, size=10)
            key = next((k for k in FIG_AFTER if para.startswith(k)), None)
            if key:
                w.image(FIGS / f"{FIG_AFTER[key]}.png", CAPTIONS[FIG_AFTER[key]])
        if head in FIG_AFTER:
            w.image(FIGS / f"{FIG_AFTER[head]}.png", CAPTIONS[FIG_AFTER[head]])
    w.doc.set_metadata({"title": TITLE, "author": AUTHORS, "subject": "fictional test paper", "creator": "make_paper.py"})
    w.doc.save(HERE / "paper.pdf", deflate=True, garbage=3)
    print(f"wrote {HERE / 'paper.pdf'} ({len(w.doc)} pages) and {len(list(FIGS.glob('*.png')))} figures")


if __name__ == "__main__":
    main()
