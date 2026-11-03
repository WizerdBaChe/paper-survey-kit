"""Tests for units.py on synthetic PDFs (stdlib unittest + PyMuPDF). Both sides of each check are asserted.

Run: python -m unittest test_units   (from scripts/)
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import units  # noqa: E402

ARIAL = Path("C:/Windows/Fonts/arial.ttf")
FILLER = [
    "Silicon photonics offers dense integration of optical",
    "components on a chip, and the loss of the waveguides",
    "sets the performance of many circuits built on it.",
]


def build_pdf(path, pages, font="ar"):
    """pages: a list of pages, each a list of (x, y, text, size) baseline-positioned lines.
    font "ar" = Arial (has the fi/fl ligature glyphs; its '-' and ' ' come back as U+00AD and U+00A0),
    "helv" = Base-14 Helvetica (WinAnsi: '-' and ' ' come back as U+002D and U+0020, like the 7 real papers)."""
    doc = fitz.open()
    for items in pages:
        page = doc.new_page(width=595, height=842)
        if font == "ar":
            page.insert_font(fontname="ar", fontfile=str(ARIAL))
        for x, y, text, size in items:
            page.insert_text((x, y), text, fontsize=size, fontname=font)
    doc.save(str(path))
    doc.close()


def para(x, y, lines, size=10, indent=0, pitch=12):
    """Lines of one paragraph from baseline y; the first line indented by `indent`. Returns (items, next y)."""
    return [(x + (indent if i == 0 else 0), y + i * pitch, t, size) for i, t in enumerate(lines)], y + len(lines) * pitch


def body(result, kinds=("abstract", "paragraph")):
    return [u for u in result["units"] if u["kind"] in kinds]


@unittest.skipUnless(ARIAL.is_file(), f"needs {ARIAL} (it has the fi/fl ligature glyphs)")
class UnitsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def pdf(self, name, pages, font="ar"):
        p = self.dir / name
        build_pdf(p, pages, font)
        return p

    def test_u01_running_header_removed_but_not_mid_page(self):
        pages = []
        for p in (1, 2, 3):
            items = [(72, 40, f"Appl. Sci. 2018, 8, 1139 {p} of 3", 8)]
            a, y = para(72, 150, FILLER, indent=10)
            items += a
            if p == 2:
                b, y = para(72, 400, ["We cite the journal header text below as part of a",
                                      f"Appl. Sci. 2018, 8, 1139 {p} of 3",
                                      "paragraph line that must stay in the body text."], indent=10)
                items += b
            pages.append(items)
        r = units.extract(self.pdf("u01.pdf", pages))
        heads = [x for x in r["removed"] if x["kind"] == "header_footer"]
        self.assertEqual(len(heads), 3)
        self.assertTrue(all(x["line"][0] == i + 1 for i, x in enumerate(heads)))
        mid = [u for u in body(r) if "Appl. Sci. 2018, 8, 1139 2 of 3" in u["text"]]
        self.assertEqual(len(mid), 1, "the mid-page copy stays in a body unit")
        self.assertIn(mid[0]["id"], [h["unit"] for h in r["checks"]["foreign_hits"]], "and the foreign-text check reports it")
        clean = [u for u in body(r) if u is not mid[0]]
        self.assertFalse({u["id"] for u in clean} & {h["unit"] for h in r["checks"]["foreign_hits"]})

    def test_u02_page_number_vs_body_number(self):
        items, y = para(72, 150, FILLER + ["7 samples were measured in total over three runs."], indent=10)
        items.append((290, 820, "7", 8))
        r = units.extract(self.pdf("u02.pdf", [items]))
        self.assertEqual([(x["kind"], x["raw"]) for x in r["removed"]], [("page_number", "7")])
        self.assertTrue(any("7 samples were measured" in u["text"] for u in body(r)))

    def test_u03_paragraph_across_pages_and_new_paragraph_after_stop(self):
        p1, _ = para(72, 700, ["The measured loss of the long spiral waveguide",
                               "decreases with the width and the measured loss"], indent=10)
        p2a, y = para(72, 100, ["Si waveguides of 3 um width show this as well.",
                                "The trend holds for every sample we measured."])
        p2b, y = para(72, y, ["A second paragraph starts after the full stop and",
                              "it has an indented first line of its own here."], indent=10)
        r = units.extract(self.pdf("u03.pdf", [FILLER_ITEMS() + p1, p2a + p2b]))  # stream order = reading order
        texts = [u["text"] for u in body(r)]
        joined = [t for t in texts if t.startswith("The measured loss")]
        self.assertEqual(len(joined), 1)
        self.assertIn("the measured loss Si waveguides of 3 um width", joined[0], "no stop at the page end: one paragraph")
        self.assertTrue(any(t.startswith("A second paragraph starts") for t in texts), "a stop + an indented capital: a new one")
        self.assertFalse(any("every sample we measured. A second" in t for t in texts))

    def test_u04_ligature_fix_replays(self):
        items, _ = para(72, 150, ["The \ufb01rst \ufb02at mirror re\ufb02ects light back into",
                                  "the cavity with a high re\ufb02ectivity of the stack."], indent=10)
        r = units.extract(self.pdf("u04.pdf", [items + FILLER_ITEMS(300)]))
        u = next(u for u in body(r) if "rst" in u["raw"])
        self.assertEqual([f["kind"] for f in u["fixes"]], ["ligature"] * 4)
        self.assertIn("first flat mirror reflects", u["text"])
        self.assertEqual(units.apply_fixes(u["raw"], u["fixes"]), u["text"])
        self.assertNotEqual(units.apply_fixes(u["raw"], u["fixes"][1:]), u["text"], "dropping one fix breaks the replay")
        self.assertEqual(r["checks"]["replay_mismatch"], [])
        bad = copy.deepcopy(r)
        next(x for x in bad["units"] if x["id"] == u["id"])["fixes"].pop()
        self.assertEqual(units.replay(bad), [u["id"]])

    def test_u05_dehyphenation_uses_the_paper_as_dictionary(self):
        a, y = para(72, 150, ["The light in the wave-", "guide is confined by the oxide cladding."], indent=10)
        b, y = para(72, y, ["A waveguide with a III-V gain section is used here."], indent=10)
        c, y = para(72, y, ["The heterogeneous III-", "V laser uses a multi-", "mode section in the cavity."], indent=10)
        r = units.extract(self.pdf("u05.pdf", [a + b + c + FILLER_ITEMS(400)], font="helv"))
        ua = next(u for u in body(r) if u["raw"].startswith("The light"))
        self.assertEqual(ua["raw"][:26], "The light in the wave-guid", "raw keeps the hyphen, joined without a space")
        self.assertIn("waveguide is confined", ua["text"])
        self.assertEqual([(f["kind"], f["raw"]) for f in ua["fixes"]], [("dehyphenation", "-")])
        uc = next(u for u in body(r) if u["raw"].startswith("The heterogeneous"))
        self.assertIn("III-V laser", uc["text"])
        self.assertIn("multi-mode section", uc["text"])
        self.assertEqual(uc["fixes"], [], "unsure joins keep the hyphen and log nothing")

    def test_u13_soft_hyphen_is_a_hyphen_not_a_deletion(self):
        # Arial via insert_text maps '-' to U+00AD: a mid-line one is kept (and counted), a line-end one is decided
        a, y = para(72, 150, ["The light in the wave-", "guide is confined by the oxide cladding."], indent=10)
        b, y = para(72, y, ["A waveguide with a III-V gain section is used here."], indent=10)
        r = units.extract(self.pdf("u13.pdf", [a + b + FILLER_ITEMS(400)]))
        ua = next(u for u in body(r) if u["raw"].startswith("The"))
        self.assertIn("waveguide", ua["text"])
        self.assertEqual([(f["kind"], f["raw"]) for f in ua["fixes"]], [("dehyphenation", "­")])
        ub = next(u for u in body(r) if u["raw"].startswith("A"))
        self.assertIn("III­V", ub["text"], "a mid-line soft hyphen is not deleted")
        self.assertEqual(ub["fixes"], [])
        self.assertEqual(r["checks"]["soft_hyphens"], [ub["id"]])

    def test_u06_two_columns_read_left_first(self):
        left1, y = para(57, 150, ["Left column first paragraph of this page begins",
                                  "here and runs on for a few lines of body text",
                                  "until it ends with a period at the column end."])
        left2, _ = para(57, y, ["Left column second paragraph has an indented",
                                "first line and continues down the left column",
                                "for three lines before it finishes cleanly."], indent=10)
        right1, y = para(310, 150, ["Right column first paragraph of this page and",
                                    "it continues with more body text on the right",
                                    "side of the page until it ends with a period."], indent=10)
        right2, _ = para(310, y, ["Right column second paragraph is indented and",
                                  "carries on down the right column for three",
                                  "lines of text before it finishes with a stop."], indent=10)
        r = units.extract(self.pdf("u06.pdf", [left1 + left2 + right1 + right2]))
        starts = [u["text"][:11] for u in body(r)]
        self.assertEqual(starts, ["Left column", "Left column", "Right colum", "Right colum"])
        self.assertIn("first paragraph", body(r)[0]["text"])
        self.assertEqual(r["checks"]["two_column_pages"], [1])
        self.assertEqual(r["checks"]["order"], [])
        self.assertEqual(r["checks"]["controls"]["order"], "ok")
        # negative side: lines written interleaved (L0 R0 L1 R1 ...) come out as one mixed block
        mixed = [item for pair in zip(left1, right1) for item in pair] + [item for pair in zip(left2, right2) for item in pair]
        m = units.extract(self.pdf("u06b.pdf", [mixed]))
        self.assertTrue(m["checks"]["order"], "an interleaved column order is reported")

    def test_u07_heading_unit_and_section(self):
        items = [(72, 90, "A Study of Low Loss Waveguides", 14)]
        a, y = para(72, 150, ["1. Introduction"])
        items += a
        b, y = para(72, y + 6, FILLER, indent=10)
        items += b
        c, y = para(72, y + 12, ["2. Methods"])
        items += c
        d, y = para(72, y + 6, ["The samples were made on a 500 nm silicon layer",
                                "and measured with the cut-back method at 1550 nm."], indent=10)
        items += d
        r = units.extract(self.pdf("u07.pdf", [items]))
        heads = [u for u in r["units"] if u["kind"] == "heading"]
        self.assertEqual([(u["text"], u["section"]) for u in heads], [("1. Introduction", "§1"), ("2. Methods", "§2")])
        after = next(u for u in body(r) if u["text"].startswith("The samples"))
        self.assertEqual(after["section"], "§2")
        self.assertEqual([u["text"] for u in r["units"] if u["kind"] == "title_block"], ["A Study of Low Loss Waveguides"])

    def test_u08_deterministic(self):
        items, _ = para(72, 150, FILLER + ["The \ufb01nal line ends here."], indent=10)
        p = self.pdf("u08.pdf", [items])
        self.assertEqual(units.serialize(units.extract(p)), units.serialize(units.extract(p)))

    def test_u09_coverage_check_both_sides(self):
        items, y = para(72, 150, FILLER, indent=10)
        more, _ = para(72, y, ["Another paragraph with a clear sentence in the middle",
                               "of it that ends with a full stop at the very end."], indent=10)
        p = self.pdf("u09.pdf", [items + more])
        r = units.extract(p)
        doc = fitz.open(str(p))
        lines, _ = units.read_lines(doc)
        doc.close()
        self.assertEqual(units.coverage(r, lines), {"unaccounted": [], "double": [], "unknown": []})
        bad = copy.deepcopy(r)
        dropped = bad["units"][0]["lines"].pop()
        self.assertEqual(units.coverage(bad, lines)["unaccounted"], [dropped])
        twice = copy.deepcopy(r)
        twice["units"][1]["lines"].append(twice["units"][0]["lines"][0])
        self.assertEqual(units.coverage(twice, lines)["double"], [twice["units"][0]["lines"][0]])
        for k in ("coverage", "replay", "foreign", "proxies"):
            self.assertEqual(r["checks"]["controls"][k], "ok", k)
        self.assertEqual(units.hard_failures(r["checks"]), [])

    def test_u10_caption_and_figure_region_leave_the_body(self):
        a, _ = para(72, 120, ["The ring spectra are measured with a tunable laser", "and they are plotted as shown in"], indent=10)
        fig = [(90, 200, "(a)", 7), (300, 200, "(b)", 7), (150, 280, "Wavelength (nm)", 7), (360, 280, "Wavelength (nm)", 7)]
        cap = [(72, 330, "Figure 1. The measured spectra of the ring resonator.", 9)]
        b, _ = para(72, 380, ["the figure above for both of the ring radii.", "The fit gives the intrinsic quality factor."])
        p = self.pdf("u10.pdf", [a + fig + cap + b + FILLER_ITEMS(500)])
        with fitz.open(str(p)) as doc:
            cb = next(bl for bl in doc[0].get_text("dict")["blocks"] if bl.get("type") == 0
                      and units.WS.sub(" ", "".join(s["text"] for s in bl["lines"][0]["spans"])).startswith("Figure 1"))
        captions = [{"page": 1, "kind": "figure", "label": "Figure 1", "num": 1, "bbox": [round(v, 1) for v in cb["bbox"]],
                     "caption": "Figure 1. The measured spectra of the ring resonator.", "caption_ok": True}]
        crops = [{"page": 1, "kind": "figure", "rect": [60, 180, 540, 300], "file": "figures/F1.png", "gate": "PASS", "caption_index": 0}]
        r = units.extract(p, captions, crops)
        kinds = [u["kind"] for u in r["units"]]
        self.assertEqual(kinds.count("caption"), 1)
        self.assertEqual(kinds.count("figure_text"), 1)
        self.assertFalse(any("Wavelength" in u["text"] or u["text"].startswith("(a)") for u in body(r)))
        cont = [u for u in body(r) if u["text"].startswith("The ring spectra")]
        self.assertEqual(len(cont), 1)
        self.assertIn("as shown in the figure above", cont[0]["text"], "a paragraph continues across the figure")
        f = r["figures"][0]
        self.assertEqual(f["caption_unit"], next(u["id"] for u in r["units"] if u["kind"] == "caption"))
        self.assertEqual(f["text_units"], [next(u["id"] for u in r["units"] if u["kind"] == "figure_text")])
        # without the crop rect nothing marks it as figure text: its small font makes it a note
        r2 = units.extract(p, captions, [])
        self.assertNotIn("figure_text", [u["kind"] for u in r2["units"]])
        self.assertTrue(any("Wavelength" in u["text"] and u["kind"] == "note" for u in r2["units"]))

    def test_u11_back_matter_and_one_reference_list(self):
        a, y = para(72, 120, FILLER, indent=10)
        s, y = para(72, y, ["Supplementary Figure S1 shows the full spectra of the rings in",
                            "more detail than the main figures can show here."], indent=10)
        ack, y = para(72, y + 12, ["Acknowledgments: We thank the cleanroom staff for help."])
        ref, y = para(72, y + 12, ["References", "1. Smith, J. Low loss waveguides. Opt. Lett. 2010, 1, 2.",
                                   "2. Doe, A. Ring resonators. Opt. Express 2012, 3, 4."])
        r = units.extract(self.pdf("u11.pdf", [a + s + ack + ref]))
        self.assertTrue(any(u["text"].startswith("Supplementary Figure S1") for u in body(r)), "a body sentence stays body")
        self.assertEqual([u["text"][:15] for u in r["units"] if u["kind"] == "backmatter"], ["Acknowledgments"])
        refs = [u for u in r["units"] if u["kind"] == "reference_list"]
        self.assertEqual(len(refs), 1)
        self.assertTrue(refs[0]["text"].startswith("References 1. Smith"))

    def test_u14_license_block_does_not_cut_a_paragraph(self):
        p1, _ = para(72, 650, ["The measured loss of the long spiral waveguide",
                               "decreases with the width and the measured loss"], indent=10)
        lic = [(300, 740, "© 2021 The Author(s)", 8)]
        p2, _ = para(72, 100, ["Si waveguides of 3 um width show this as well.",
                               "The trend holds for every sample we measured."])
        r = units.extract(self.pdf("u14.pdf", [FILLER_ITEMS() + p1 + lic, p2], font="helv"))
        joined = [u for u in body(r) if u["text"].startswith("The measured loss")]
        self.assertEqual(len(joined), 1)
        self.assertIn("the measured loss Si waveguides", joined[0]["text"])
        self.assertEqual([u["text"] for u in r["units"] if u["kind"] == "backmatter"], ["© 2021 The Author(s)"])

    def test_u15_heading_guards_both_sides(self):
        def L(text, x0, y0, font="H", size=10.0, idx=0):
            return units.Line(ref=(1, 0, idx), page=1, bbox=(x0, y0, x0 + 200, y0 + 10), text=text, ptext=text, size=size,
                              font=font, bold=False, end_text=text, x0=x0, idx=idx)
        # a run-in label: the next line goes on in the body font "R"
        a, b = L("Abstract: Integrated low loss waveguides are", 72, 100, font="B", idx=0), L("needed for long delay lines.", 72, 112, font="R", idx=1)
        self.assertIn("run-in label", units.heading_guard(a, [a, b], {}, "R"))
        # a genuine two-line heading: the next line keeps the heading font
        c, d = L("Thick nitride for nonlinear", 56, 100, font="H", idx=0), L("photonics applications", 56, 112, font="H", idx=1)
        self.assertIsNone(units.heading_guard(c, [c, d], {}, "R"))
        # a later fragment of a justified line
        e, f = L("Validation, IEEE", 40, 300, font="R", idx=0), L("experimental", 141, 300, font="R", idx=1)
        self.assertIn("fragment", units.heading_guard(f, [e, f], {}, "R"))
        self.assertIsNone(units.heading_guard(e, [e], {}, "R"))
        self.assertIn("formula", units.heading_guard(L("PSW = (Eon + Eoff).f", 88, 200), [L("PSW = (Eon + Eoff).f", 88, 200)], {}, "R"))
        g = L("eter (MFD) of 10.4 um. Neglecting", 155, 80, font="R")
        self.assertIn("lowercase", units.heading_guard(g, [g], {}, "R"))
        # a body line inside a paragraph: the line above it ends mid-sentence
        h, i = L("the switching energy is lower and", 36, 460, font="R", idx=0), L("ESW , it is found that PSGT shows", 36, 472, font="R", idx=1)
        self.assertIn("mid-sentence", units.heading_guard(i, [h, i], {}, "R"))
        j, k = L("the loss is lower than before.", 36, 460, font="R", idx=0), L("2. Methods", 36, 480, font="H", idx=1)
        self.assertIsNone(units.heading_guard(k, [j, k], {}, "R"))

    def test_u12_backmatter_start_rule(self):
        self.assertTrue(units.backmatter_start("references"))
        self.assertTrue(units.backmatter_start("funding: this work was supported by the nsf."))
        self.assertTrue(units.backmatter_start("5. references"))
        self.assertFalse(units.backmatter_start("supplementary figure s1 shows the full spectra of the rings in"))
        self.assertFalse(units.backmatter_start("the references below list the prior work"))


def FILLER_ITEMS(y=150):
    return para(72, y, FILLER, indent=10)[0]


if __name__ == "__main__":
    unittest.main()
