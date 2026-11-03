"""Tests for the 2026-11-03 ingest tools (card B): text/JATS sources (ingest.py + textsrc.py + probe.py), probe heading noise,
crop.py's figures-after-captions search. Each check has a positive case (the defect MUST be caught / the new path MUST fire)
and a negative case (a known-good input MUST pass unchanged).

Run: python -m unittest test_ingest_text   (from scripts/)
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crop  # noqa: E402
import ingest  # noqa: E402
import probe  # noqa: E402
import textsrc  # noqa: E402

JATS = ingest._JATS_CONTROL
TEXT = ingest._TEXT_CONTROL


def run_main(mod, argv):
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, buf.getvalue(), err.getvalue()


class TextSources(unittest.TestCase):
    def test_jats_units_in_reading_order(self):
        j = textsrc.parse_jats(JATS.encode())
        self.assertEqual([u["id"] for u in j["units"]], ["§0", "§1", "§2", "§2.1"])          # positive: §N.M numbering
        self.assertNotIn("Acknowledgements", [u["text"] for u in j["units"]])                # negative: back matter is no unit
        self.assertIn("Text[1].", j["text"])                                                 # citation superscript -> [n]
        self.assertEqual([c["label"] for c in j["captions"]], ["Fig. 1"])
        self.assertTrue(j["captions"][0]["caption"].startswith("Fig. 1 A cartoon."))

    def test_jats_rejects_non_jats(self):
        with self.assertRaises(ValueError):
            textsrc.parse_jats(b"<html><body><p>not jats</p></body></html>")                  # negative control: not an article
        with self.assertRaises(ValueError):
            textsrc.parse_jats(b"<article><front/></article>")                                # no <body>: abstract-only record

    def test_text_headings_and_captions(self):
        t = textsrc.parse_text(TEXT, ingest.CAPTION_RE)
        self.assertEqual([u["id"] for u in t["units"]], ["§0", "§1", "§2"])
        self.assertEqual([c["label"] for c in t["captions"]], ["Fig. 1"])
        self.assertEqual(textsrc.parse_text("one paragraph\nof plain prose\n", ingest.CAPTION_RE)["units"], [])   # negative

    def test_selftest_controls_fire_and_pass(self):
        self.assertIsNone(ingest.textsrc_controls())
        broken = ingest._JATS_CONTROL
        ingest._JATS_CONTROL = broken.replace("<title>Results</title>", "<title>Acknowledgements</title>")
        try:
            self.assertIn("JATS control units", ingest.textsrc_controls() or "")           # positive control: a wrong parse is reported
        finally:
            ingest._JATS_CONTROL = broken

    def test_end_to_end_jats_and_text_then_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "p.xml").write_text(JATS, encoding="utf-8")
            (tmp / "p.txt").write_text(TEXT, encoding="utf-8")
            for flag, name, kind in (("--jats", "p.xml", "jats"), ("--text", "p.txt", "text")):
                home = tmp / f"home-{kind}"
                code, out, _ = run_main(ingest, [flag, str(tmp / name), "--home", str(home), "--first-author", "Test", "--year", "2026"])
                self.assertEqual(code, 0, out)
                run = Path(json.loads(out)["run_dir"])
                meta = json.loads((run / "_meta.json").read_text(encoding="utf-8"))
                self.assertEqual(meta["source_kind"], kind)
                before = json.loads((run / "source" / "structure.json").read_text(encoding="utf-8"))
                self.assertEqual(before["source_kind"], kind)
                code, out, _ = run_main(probe, ["--run", str(run)])
                self.assertEqual(code, 0)
                after = json.loads((run / "source" / "structure.json").read_text(encoding="utf-8"))
                ids = lambda s: [u["id"] for u in s["units"]]
                self.assertEqual(ids(after), ids(before))                    # probe keeps ingest's section units (idempotent)
                self.assertIn("Fig. 1", ids(after))
                self.assertEqual(after["source_kind"], kind)
            # rung 0 example: a CRLF copy of the same text gives byte-identical paper.txt (LF) and the same
            # structure line numbers as the LF source (the CRLF bug wrote \r\r\n and doubled every line).
            (tmp / "crlf.txt").write_bytes(TEXT.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            lf_run = Path(json.loads(run_main(ingest, ["--text", str(tmp / "p.txt"), "--home", str(tmp / "h-lf"),
                                                       "--first-author", "Test", "--year", "2026"])[1])["run_dir"])
            cr_run = Path(json.loads(run_main(ingest, ["--text", str(tmp / "crlf.txt"), "--home", str(tmp / "h-cr"),
                                                       "--first-author", "Test", "--year", "2026"])[1])["run_dir"])
            lf_txt, cr_txt = ((r / "source" / "paper.txt").read_bytes() for r in (lf_run, cr_run))
            self.assertNotIn(b"\r", cr_txt)
            self.assertEqual(cr_txt, lf_txt)
            lines = lambda r: [u.get("line") for u in json.loads((r / "source" / "structure.json").read_text(encoding="utf-8"))["units"]]
            self.assertEqual(lines(cr_run), lines(lf_run))
            code, _, err = run_main(ingest, ["--text", str(tmp / "missing.txt"), "--home", str(tmp / "h2")])   # negative: no such file
            self.assertEqual(code, 1)
            code, _, err = run_main(ingest, ["--jats", str(tmp / "p.txt"), "--home", str(tmp / "h3")])        # negative: text given as JATS
            self.assertEqual(code, 1)


def synthetic_noise_pdf(path):
    """One page: body text, a real bold heading, and a vector figure whose box holds heading-shaped text and axis tokens."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 60), "Abstract", fontsize=12, fontname="hebo")
    for i in range(12):
        page.insert_text((72, 80 + i * 12), "The anneal series was measured by Hall effect and the carrier density follows the trend.", fontsize=10, fontname="helv")
    page.insert_text((72, 250), "Sample preparation", fontsize=12, fontname="hebo")              # a REAL heading, outside the figure
    page.insert_text((72, 290), "Intensity (a.u.)", fontsize=12, fontname="hebo")                  # axis-like, outside any figure box
    page.draw_rect(fitz.Rect(100, 350, 500, 600))                                                  # the figure: a frame and 4 paths
    for k in range(4):
        page.draw_line((100, 380 + 40 * k), (500, 380 + 40 * k))
    page.insert_text((200, 420), "Annealing temperature series", fontsize=12, fontname="hebo")    # heading-shaped, INSIDE the figure
    page.insert_text((300, 500), "5 nm", fontsize=12, fontname="hebo")
    doc.save(str(path))
    doc.close()


class ProbeNoise(unittest.TestCase):
    def test_noise_dropped_heading_kept_and_control_fires(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "n.pdf"
            synthetic_noise_pdf(pdf)
            doc = fitz.open(str(pdf))
            recs = probe.line_records(doc)
            body, bfont = probe.body_size(doc), probe.body_font(doc)
            doc.close()
            texts = lambda hs: {h["text"] for h in hs}
            kept, _ = probe.find_headings(recs, body, bfont)
            self.assertIn("Sample preparation", texts(kept))                                        # negative: a real heading survives
            self.assertNotIn("Annealing temperature series", texts(kept))                           # positive: figure-box rule
            self.assertNotIn("Intensity (a.u.)", texts(kept))                                       # positive: axis-token rule
            self.assertNotIn("5 nm", texts(kept))
            inside = [r for r in recs if r["text"] == "Annealing temperature series"][0]
            self.assertTrue(inside["in_fig"])
            self.assertFalse([r for r in recs if r["text"] == "Sample preparation"][0]["in_fig"])
            # the control: with both rules switched off the noise IS read as headings (the test can fail)
            saved = probe.axis_like
            probe.axis_like = lambda t: None
            try:
                raw, _ = probe.find_headings([dict(r, in_fig=False) for r in recs], body, bfont)
            finally:
                probe.axis_like = saved
            self.assertTrue({"Annealing temperature series", "Intensity (a.u.)"} <= texts(raw), texts(raw))

    def test_axis_like_controls(self):
        self.assertIsNone(probe.noise_controls())
        self.assertIsNotNone(probe.axis_like("Temperature (K)"))
        self.assertIsNone(probe.axis_like("Results and discussion"))

    def test_colon_headings(self):
        lines = [{"page": 1, "text": t, "size": 12.0, "bold": True, "italic": False, "font": "F-bold"}
                 for t in ("Abstract:", "Introduction:", "Experimental details:", "Note that this is a long label for a value:")]
        heads, _ = probe.find_headings(lines, 12.0, "F-body")
        got = {h["text"] for h in heads}
        self.assertTrue({"Abstract:", "Introduction:", "Experimental details:"} <= got)                # positive
        self.assertNotIn("Note that this is a long label for a value:", got)                           # negative: a long run-in label


def line(page, y, text, size=10, font="helv", x=72):
    page.insert_text((x, y), text, fontsize=size, fontname=font)


def footer(page, n):
    page.insert_text((250, 815), f"{n} | P a g e", fontsize=9, fontname="helv")


def draw_figure(page, x0, y0, x1, y1):
    page.draw_rect(fitz.Rect(x0, y0, x1, y1))
    for k in range(1, 5):
        page.draw_line((x0, y0 + (y1 - y0) * k / 5), (x1, y0 + (y1 - y0) * k / 5))


class CropAfterCaption(unittest.TestCase):
    def crop(self, pdf, caption, page=None):
        run = pdf.parent
        (run / "source").mkdir(exist_ok=True)
        (run / "source" / "paper.pdf").write_bytes(pdf.read_bytes())
        (run / "source" / "figures.json").write_text(json.dumps({"captions": [], "images": []}), encoding="utf-8")
        argv = ["--run", str(run), "--caption", caption, "--out", "figures/out.png"] + (["--page", str(page)] if page else [])
        code, out, err = run_main(crop, argv)
        return code, (json.loads(out.strip().splitlines()[-1]) if out.strip() else {"error": err})

    def caption_list_doc(self, path, stubs=True):
        doc = fitz.open()
        p1 = doc.new_page(width=595, height=842)
        line(p1, 80, "Figure captions:")
        line(p1, 110, "Figure 1(a): Grazing incidence diffraction of the thin films at several thicknesses.")
        line(p1, 150, "Figure 1(b): The Raman spectrum of the same films at several thicknesses.")
        line(p1, 200, "Figure 2: Variation of normalized resistivity as a function of temperature.")
        footer(p1, 1)
        p2 = doc.new_page(width=595, height=842)
        if stubs:
            line(p2, 80, "Figure 1(a):")
        draw_figure(p2, 120, 110, 480, 330)
        if stubs:
            line(p2, 360, "Figure 1(b):")
        draw_figure(p2, 120, 390, 480, 600)
        footer(p2, 2)
        p3 = doc.new_page(width=595, height=842)
        if stubs:
            line(p3, 80, "Figure 2:")
        draw_figure(p3, 120, 110, 480, 400)
        footer(p3, 3)
        doc.save(str(path))
        doc.close()

    def test_stub_layout_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "a.pdf"
            self.caption_list_doc(pdf)
            code, r = self.crop(pdf, "Fig. 2")
            self.assertEqual(code, 0, r)
            self.assertEqual((r["page"], r["band"]["layout"], r["band"]["via"]), (3, "figure-after-caption", "stub"))
            self.assertLess(abs(r["rect_pt"][1] - 106), 8)                                          # top of the drawing, not the stub text
            code, r = self.crop(pdf, "Fig. 1")                                                      # both panels = one figure
            self.assertEqual(code, 0, r)
            self.assertEqual(r["page"], 2)
            self.assertGreater(r["rect_pt"][3], 590)                                                # runs down through panel (b)
            code, r = self.crop(pdf, "Fig. 2", page=3)                                              # crop_all asks the stub's own page
            self.assertEqual((code, r["page"], r["band"]["via"]), (0, 3, "stub"))

    def test_gate_still_applies_after_forward_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "g.pdf"
            self.caption_list_doc(pdf)
            code, r = self.crop(pdf, "Fig. 2")
            self.assertEqual((code, r["gate"]["verdict"]), (0, "PASS"))                              # negative: a clean cut passes
            doc = fitz.open(str(pdf))
            doc[2].draw_rect(fitz.Rect(120, 600, 480, 812), fill=(0, 0, 0))    # ink running down to the band's lower edge
            bad = pdf.parent / "g2.pdf"
            doc.save(str(bad))
            doc.close()
            code, r = self.crop(bad, "Fig. 2")
            self.assertEqual(r["band"]["layout"], "figure-after-caption")
            self.assertEqual((code, r["gate"]["verdict"]), (3, "FAIL"))                              # positive: exit-3 rule still fires

    def test_ordinary_layout_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "o.pdf"
            doc = fitz.open()
            p = doc.new_page(width=595, height=842)
            for i in range(3):
                line(p, 60 + 12 * i, "A body paragraph line that is long enough to count as running text in the page column here.")
            draw_figure(p, 120, 150, 480, 400)
            line(p, 420, "Figure 1: The ordinary layout, caption under the figure, with enough words to be a caption.")
            footer(p, 1)
            doc.save(str(pdf))
            doc.close()
            code, r = self.crop(pdf, "Fig. 1")
            self.assertEqual(code, 0, r)
            self.assertEqual(r["page"], 1)
            self.assertNotIn("layout", r["band"])                                                    # negative: the new path stayed out

    def test_bare_label_without_a_listed_caption_is_not_a_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "b.pdf"
            doc = fitz.open()
            p = doc.new_page(width=595, height=842)
            for i in range(3):
                line(p, 60 + 12 * i, "A body paragraph line that is long enough to count as running text in the page column here.")
            draw_figure(p, 120, 150, 380, 400)
            line(p, 420, "Figure 1:")                                                                # label-only caption, figure ABOVE it
            draw_figure(p, 120, 470, 380, 700)                                                       # and another drawing below it
            footer(p, 1)
            doc.save(str(pdf))
            doc.close()
            code, r = self.crop(pdf, "Fig. 1")
            self.assertEqual(code, 0, r)
            self.assertLess(r["rect_pt"][3], 410)                                                    # the figure above, not the drawing below
            self.assertNotIn("layout", r["band"])

    def test_image_order_fallback_and_count_guard(self):
        def build(path, n_images):
            doc = fitz.open()
            p1 = doc.new_page(width=595, height=842)
            line(p1, 80, "Figure 1: First caption with several words in it about the first measurement.")
            line(p1, 120, "Figure 2: Second caption with several words in it about the second measurement.")
            footer(p1, 1)
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 80), False)
            pix.set_rect(pix.irect, (30, 90, 200))
            for k in range(n_images):
                pg = doc.new_page(width=595, height=842)
                pg.insert_image(fitz.Rect(100, 100, 400, 330), pixmap=pix)
                footer(pg, 2 + k)
            doc.save(str(path))
            doc.close()

        with tempfile.TemporaryDirectory() as tmp:
            ok = Path(tmp) / "ok.pdf"
            build(ok, 2)
            code, r = self.crop(ok, "Fig. 2")
            self.assertEqual(code, 0, r)
            self.assertEqual((r["page"], r["band"]["via"], r["band"]["rank"]), (3, "image-order", 2))      # positive: 2 captions, 2 images
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.pdf"
            build(bad, 3)
            code, r = self.crop(bad, "Fig. 2")
            self.assertNotIn("layout", r.get("band", {}))                                                   # negative: 3 images != 2 captions
            self.assertIn("order unprovable", json.dumps(r))


if __name__ == "__main__":
    unittest.main()
