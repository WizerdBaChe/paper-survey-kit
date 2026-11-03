"""Tests for the 2026-11-03 card B2: a run with no PDF (ingest.py --text / --jats) gets units, a clean crop_all and a
verify_run that SKIPs what needs pages; crop_all skips caption stubs. Every change has a positive case (the defect or the
new path MUST fire) and a negative case (a known-good input MUST pass unchanged); `test_*_disabled` tests switch a rule off
and require the positive case to stop firing, so the controls can fail.

Run: python -m unittest test_text_runs   (from scripts/)
"""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crop_all  # noqa: E402
import ingest  # noqa: E402
import units  # noqa: E402
import verify_run  # noqa: E402

PLAIN = "\n".join([
    "Thin Solid Films 10 (2021) 1001",
    "A Study of Low Loss Waveguides",
    "Jane Doe, John Roe",
    "ABSTRACT",
    "We measured the propagation loss of silicon nitride waveguides at 1550 nm with the cut-back method over",
    "twelve samples and found it to be low across the band. The result holds for all of the widths we made.",
    "1. Introduction",
    "Silicon photonics offers dense integration of optical components on a chip and the loss of the wave-",
    "guides sets the performance. A second sentence ends here.",
    "A new paragraph starts after the short line above and it goes on for a while across the full width of",
    "the text column so that the median line width is clearly larger than the short line that ended the first.",
    "Fig. 1. A cartoon of the sample.",
    "0.5",
    "1.0",
    "1.5",
    "Thin Solid Films 11 (2021) 1002",
    "The grating couplers were designed for the TE mode and the waveguides were measured on a long spiral of",
    "length one metre, which gave the numbers quoted in the abstract above and below this paragraph here.",
    "2. Conclusions",
    "We conclude that the waveguides are good enough for the circuits described in the introduction above it.",
    "Thin Solid Films 12 (2021) 1003",
    "References",
    "[1] J. Smith, Opt. Lett. 1 (2010) 2.",
    "[2] A. Doe, Opt. Express 3 (2012) 4.",
    ""])


JATS = ingest._JATS_CONTROL.replace(
    "<p>See Fig. 1.</p>",
    "<p>The propagation loss was measured with the cut-back method at 1550 nm, see Fig. 1 for the sample.</p>")


def run_main(mod, argv):
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, buf.getvalue(), err.getvalue()


def make_run(tmp, flag, content, name="paper.txt"):
    """ingest.py --text/--jats into a scratch home; returns the run folder."""
    src = Path(tmp) / name
    src.write_bytes(content.encode("utf-8"))      # LF as given: write_text would make CRLF on Windows
    code, out, err = run_main(ingest, [flag, str(src), "--home", str(Path(tmp) / "home"), "--first-author", "Test", "--year", "2026"])
    assert code == 0, err
    return Path(json.loads(out)["run_dir"])


def units_of(run, **kw):
    summary, code = units.run_one(run, True, True, None)
    return summary, code, json.loads((run / "source" / "units.json").read_text(encoding="utf-8"))


class SourceKind(unittest.TestCase):
    def test_kind_from_meta_then_figures_then_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            self.assertEqual(crop_all.source_kind(run), "pdf")                              # negative: a run made before the field
            (run / "source").mkdir()
            (run / "source" / "figures.json").write_text(json.dumps({"source_kind": "jats"}), encoding="utf-8")
            self.assertEqual(crop_all.source_kind(run), "jats")
            (run / "_meta.json").write_text(json.dumps({"source_kind": "text"}), encoding="utf-8")
            self.assertEqual(crop_all.source_kind(run), "text")                             # _meta.json wins
            (run / "_meta.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(crop_all.source_kind(run), "jats")                             # unreadable meta never crashes


class CropAllStubs(unittest.TestCase):
    KUMAR = [  # the Kumar 2022 shape: full captions on the caption-list page, label-only stubs above each figure
        {"page": 11, "kind": "figure", "num": 1, "label": "Figure 1", "caption": "Figure 1(a): Grazing incidence X-ray diffraction pattern."},
        {"page": 11, "kind": "figure", "num": 1, "label": "Figure 1", "caption": "Figure 1(b): The Raman spectrum of the films."},
        {"page": 11, "kind": "figure", "num": 2, "label": "Figure 2", "caption": "Figure 2: Variation of normalized resistivity."},
        {"page": 12, "kind": "figure", "num": 1, "label": "Figure 1", "caption": "Figure 1(a):"},
        {"page": 12, "kind": "figure", "num": 1, "label": "Figure 1", "caption": "Figure 1(b):"},
        {"page": 13, "kind": "figure", "num": 2, "label": "Figure 2", "caption": "Figure 2:"},
    ]

    def test_each_figure_once(self):
        skipped = []
        ts = crop_all.targets(self.KUMAR, skipped)
        self.assertEqual([t["name"] for t in ts], ["F1", "F2"])                              # positive: 6 entries, 2 figures
        self.assertEqual([s["caption_index"] for s in skipped], [1, 3, 4, 5])
        self.assertTrue(skipped[0]["why"].startswith("panel") and skipped[1]["why"].startswith("stub"))

    def test_stub_rule_disabled_crops_twice(self):
        saved = crop_all.is_stub, crop_all.PANEL
        crop_all.is_stub = lambda c: False
        crop_all.PANEL = type("Never", (), {"match": staticmethod(lambda s: None)})
        try:
            names = [t["name"] for t in crop_all.targets(self.KUMAR)]
        finally:
            crop_all.is_stub, crop_all.PANEL = saved
        self.assertGreater(len(names), 2, names)                                              # the control: without the rules every entry is a target
        self.assertEqual(names, ["F1", "F1_p11", "F2", "F1_p12", "F1_p12-2", "F2_p13"])

    def test_stub_alone_and_continued_table_stay_targets(self):
        only_stub = [{"page": 3, "kind": "figure", "num": 2, "label": "Figure 2", "caption": "Figure 2:"}]
        self.assertEqual([t["name"] for t in crop_all.targets(only_stub)], ["F2"])           # negative: no captioned twin, the stub is the only handle
        cont = [{"page": 4, "kind": "table", "num": 2, "label": "Table 2", "caption": "Table 2. Results of the anneal series."},
                {"page": 5, "kind": "table", "num": 2, "label": "Table 2", "caption": "Table 2. Cont."}]
        self.assertEqual([t["name"] for t in crop_all.targets(cont)], ["T2", "T2_p5"])       # negative: "Cont." is text, not a stub
        self.assertFalse(crop_all.is_stub({"caption": "Figure 7 shows the schematic of the device."}))


class CropAllTextRun(unittest.TestCase):
    def test_text_and_jats_runs_are_skipped_not_cropped(self):
        for flag, content, kind in (("--text", PLAIN, "text"), ("--jats", JATS, "jats")):
            with tempfile.TemporaryDirectory() as tmp:
                run = make_run(tmp, flag, content)
                real = crop_all.subprocess.run
                crop_all.subprocess.run = lambda *a, **k: self.fail("crop.py must not be started for a run without a PDF")
                try:
                    for extra in ([], ["--apply"]):
                        code, out, _ = run_main(crop_all, ["--run", str(run)] + extra)
                        rec = json.loads(out.strip().splitlines()[-1])
                        self.assertEqual((code, rec["skipped"], rec["source_kind"]), (0, True, kind))
                        self.assertIn("no PDF", rec["reason"])
                        self.assertIn("Fig. 1", rec["figures_listed"])
                finally:
                    crop_all.subprocess.run = real
                self.assertFalse((run / "source" / "crops.json").exists())                   # nothing was cropped, nothing recorded
                self.assertEqual(list((run / "figures").iterdir()), [])

    def test_pdf_run_still_plans(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "r"
            (run / "source").mkdir(parents=True)
            (run / "source" / "figures.json").write_text(json.dumps({"captions": CropAllStubs.KUMAR}), encoding="utf-8")
            (run / "_meta.json").write_text(json.dumps({"source_kind": "pdf"}), encoding="utf-8")
            code, out, _ = run_main(crop_all, ["--run", str(run)])
            rec = json.loads(out)
            self.assertEqual((code, rec["targets"], len(rec["skipped"])), (0, ["F1", "F2"], 4))   # negative: the PDF path plans, with its skip list
            self.assertNotIn("skipped", json.loads(run_main(crop_all, ["--run", str(self._plain_run(tmp))])[1]))

    def _plain_run(self, tmp):
        run = Path(tmp) / "plain"
        (run / "source").mkdir(parents=True)
        caps = [{"page": 1, "kind": "figure", "num": 1, "label": "Figure 1", "caption": "Figure 1. A real caption."}]
        (run / "source" / "figures.json").write_text(json.dumps({"captions": caps}), encoding="utf-8")
        return run


class TextUnits(unittest.TestCase):
    def test_plain_text_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--text", PLAIN)
            summary, code, doc = units_of(run)
            self.assertEqual((code, summary["hard_failures"]), (0, []), summary)
            self.assertTrue(summary["G_identical"])
            self.assertNotIn("pdf_sha256", doc["source"])
            self.assertEqual(doc["source"]["source_kind"], "text")
            by_kind = lambda k: [u for u in doc["units"] if u["kind"] == k]
            self.assertEqual([u["section"] for u in by_kind("heading")], ["§0", "§1", "§2"])
            self.assertEqual([u["text"][:14] for u in by_kind("abstract")], ["We measured th"])
            intro = [u for u in by_kind("paragraph") if u["section"] == "§1"]
            self.assertEqual(len(intro), 2, [u["text"][:30] for u in intro])                  # the short sentence-ending line breaks the paragraph
            self.assertIn("waveguides sets the performance", intro[0]["text"])               # dehyphenated: the paper writes "waveguides" elsewhere
            self.assertEqual([f["kind"] for f in intro[0]["fixes"]], ["dehyphenation"])
            self.assertEqual(units.apply_fixes(intro[0]["raw"], intro[0]["fixes"]), intro[0]["text"])
            self.assertEqual(sorted(r["raw"] for r in doc["removed"]), ["Thin Solid Films 10 (2021) 1001", "Thin Solid Films 11 (2021) 1002",
                                                                       "Thin Solid Films 12 (2021) 1003"])
            self.assertEqual([u["text"] for u in by_kind("figure_text")], ["0.5 1.0 1.5"])
            self.assertEqual([u["text"] for u in by_kind("caption")], ["Fig. 1. A cartoon of the sample."])
            self.assertEqual(len(by_kind("reference_list")), 1)
            self.assertTrue(by_kind("reference_list")[0]["text"].startswith("References [1] J. Smith"))
            self.assertEqual(doc["figures"][0]["caption_unit"], by_kind("caption")[0]["id"])
            for u in doc["units"]:                                                            # locators are lines of paper.txt
                self.assertIsNone(u["page"])
                self.assertEqual(u["line"], u["lines"][0][0])
                self.assertEqual(u["id"], f"L{u['line']}")
            lines = (run / "source" / "paper.txt").read_text(encoding="utf-8").splitlines()
            nonblank = {n for n, s in enumerate(lines, 1) if s.strip()}
            seen = [r[0] for u in doc["units"] for r in u["lines"]] + [r["line"][0] for r in doc["removed"]]
            self.assertEqual(sorted(seen), sorted(nonblank))                                  # every non-blank line exactly once

    def test_jats_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--jats", JATS, "p.xml")
            summary, code, doc = units_of(run)
            self.assertEqual((code, summary["hard_failures"]), (0, []), summary)
            kinds = [(u["kind"], u["section"]) for u in doc["units"]]
            self.assertIn(("abstract", "§0"), kinds)
            self.assertIn(("caption", "§2.1"), kinds)
            self.assertEqual([u["section"] for u in doc["units"] if u["kind"] == "heading"], ["§0", "§1", "§2", "§2.1"])
            self.assertIn(("backmatter", "§2.1"), kinds)                                      # Acknowledgements: back matter, not a section
            self.assertTrue(all(len(u["lines"]) == 1 for u in doc["units"] if u["kind"] == "paragraph"))   # one JATS line = one paragraph

    def test_unresolved_structure_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--text", PLAIN)
            sp = run / "source" / "structure.json"
            good = json.loads(sp.read_text(encoding="utf-8"))
            summary, code, _ = units_of(run)
            self.assertEqual((code, summary["structure_unresolved"]), (0, []))               # negative: ingest's own structure resolves
            bad = copy.deepcopy(good)
            next(u for u in bad["units"] if u["id"] == "§2")["line"] += 1                     # points at the line after the heading
            sp.write_text(json.dumps(bad), encoding="utf-8")
            summary, code, _ = units_of(run)
            self.assertEqual((code, summary["structure_unresolved"]), (1, ["§2"]))           # positive: reported and fatal
            self.assertTrue(any("structure_unresolved" in f for f in summary["hard_failures"]))
            real = units.unit_resolves
            units.unit_resolves = lambda u, t: True
            try:
                summary, code, _ = units_of(run)
            finally:
                units.unit_resolves = real
            self.assertEqual(summary["structure_unresolved"], [])                             # the control: with the rule off the bad line passes

    def test_dropped_line_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--text", PLAIN)
            _, _, doc = units_of(run)
            raw = (run / "source" / "paper.txt").read_text(encoding="utf-8")
            lines, _ = units.text_lines(raw)
            self.assertEqual(units.coverage(doc, lines), {"unaccounted": [], "double": [], "unknown": []})
            bad = copy.deepcopy(doc)
            dropped = next(u for u in bad["units"] if len(u["lines"]) > 1)["lines"].pop()
            self.assertEqual(units.coverage(bad, lines)["unaccounted"], [dropped])            # positive: the text coverage check fires
            (run / "source" / "structure.json").unlink()
            summary, code = units.run_one(run, True, False, None)
            self.assertEqual((code, "structure.json" in summary["error"]), (2, True))
            (run / "source" / "paper.txt").unlink()
            summary, code = units.run_one(run, True, False, None)
            self.assertEqual((code, summary["error"]), (2, "no source/paper.txt"))

    def test_foreign_text_still_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirty = PLAIN.replace("A second sentence ends here.", "A second sentence ends here. See www.example.org for data.")
            run = make_run(tmp, "--text", dirty)
            summary, code, doc = units_of(run)
            self.assertEqual(code, 1)                                                         # positive: furniture in a body unit is not waved through
            self.assertTrue(any(h["match"] == "www." for h in doc["checks"]["foreign_hits"]))

    def test_crop_regions_use_the_page_the_crop_landed_on(self):
        doc = {"results": [{"label": "Figure 2", "page": 11, "kind": "figure", "file": "figures/F2.png", "exit": 0,
                            "result": {"page": 13, "rect_pt": [1, 2, 3, 4], "gate": {"verdict": "PASS"}}},
                           {"label": "Table 2", "page": 10, "kind": "table", "file": "figures/T2.png", "exit": 0,
                            "result": {"page": 10, "rect_pt": [5, 6, 7, 8], "gate": {"verdict": "PASS"}}},
                           {"label": "Table 1", "page": 10, "kind": "table", "file": "figures/T1.png", "exit": 1, "result": None}]}
        caps = [{"label": "Figure 2", "page": 11}, {"label": "Table 2", "page": 10}, {"label": "Table 1", "page": 10}]
        out = units.crop_regions(doc, caps)
        self.assertEqual([(r["page"], r["caption_index"]) for r in out], [(13, 0), (10, 1), (10, 2)])   # positive: p.13; negative: equal pages unchanged, no result keeps the target's page


class VerifyTextRuns(unittest.TestCase):
    def verify(self, run):
        code, out, _ = run_main(verify_run, [str(run), "--json"])
        return code, {r["check"]: r for r in json.loads(out)}

    def write_cards(self, run, locators):
        cards = {"paper_says": {"conclusion_quote": "", "locator": ""},
                 "keypoint": {"pillars": [{"text": "x", "locator": loc} for loc in locators]}}
        (run / "cards.json").write_text(json.dumps(cards), encoding="utf-8")

    def test_text_run_skips_pages_and_judges_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--text", PLAIN)
            self.write_cards(run, ["§1", "§2", "Fig. 1"])
            _, rows = self.verify(run)
            self.assertEqual(rows["V3p"]["status"], "SKIP")                                   # needs PDF pages: SKIP with its reason, not FAIL
            self.assertIn("no PDF", rows["V3p"]["msg"])
            self.assertEqual(rows["V3"]["status"], "PASS")                                    # negative: real units cited
            self.assertEqual(rows["V13"]["status"], "PASS")
            self.assertNotIn("None", rows["V3"]["msg"])                                       # the old "<= None pages" message is gone
            self.write_cards(run, ["§1", "§9", "§1.4"])
            _, rows = self.verify(run)
            self.assertEqual(rows["V3"]["status"], "FAIL")                                    # positive: an invented section number
            self.assertIn("§9", rows["V3"]["msg"])
            self.write_cards(run, ["p.3", "Table 7"])
            _, rows = self.verify(run)
            self.assertEqual(rows["V3"]["status"], "WARN")                                    # a page cite in a source without pages; not a FAIL
            self.assertIn("p.3", rows["V3"]["msg"])
            self.assertEqual(sum(r["status"] == "FAIL" for k, r in rows.items() if k in ("V2", "V3", "V3p", "V13")), 0)

    def test_v13_structure_lines_must_hold_their_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp, "--jats", JATS, "p.xml")
            self.write_cards(run, ["§1"])
            _, rows = self.verify(run)
            self.assertEqual(rows["V13"]["status"], "PASS")                                   # negative
            sp = run / "source" / "structure.json"
            st = json.loads(sp.read_text(encoding="utf-8"))
            next(u for u in st["units"] if u["id"] == "§2")["line"] = 999
            sp.write_text(json.dumps(st), encoding="utf-8")
            _, rows = self.verify(run)
            self.assertEqual(rows["V13"]["status"], "FAIL")                                   # positive: a locator that does not resolve to a line
            self.assertIn("§2@line999", rows["V13"]["msg"])
            real = verify_run.unit_resolves
            verify_run.unit_resolves = lambda u, t: True
            try:
                _, rows = self.verify(run)
            finally:
                verify_run.unit_resolves = real
            self.assertEqual(rows["V13"]["status"], "FAIL")                                   # line 999 is out of range whatever the rule says
            st = json.loads(sp.read_text(encoding="utf-8"))
            next(u for u in st["units"] if u["id"] == "§2")["line"] = 4                       # an in-range line with other text
            sp.write_text(json.dumps(st), encoding="utf-8")
            verify_run.unit_resolves = lambda u, t: True
            try:
                _, rows = self.verify(run)
            finally:
                verify_run.unit_resolves = real
            self.assertEqual(rows["V13"]["status"], "PASS")                                   # the control: rule off, the wrong line is let through
            _, rows = self.verify(run)
            self.assertEqual(rows["V13"]["status"], "FAIL")                                   # rule on: caught

    def test_pdf_run_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "r"
            (run / "source").mkdir(parents=True)
            (run / "_meta.json").write_text(json.dumps({"source_kind": "pdf"}), encoding="utf-8")
            (run / "source" / "paper.txt").write_text("<!-- p.1 -->\nfoo\n<!-- p.2 -->\nbar\n", encoding="utf-8")
            (run / "source" / "figures.json").write_text(json.dumps({"pages": 2, "captions": []}), encoding="utf-8")
            self.write_cards(run, ["p.2"])
            _, rows = self.verify(run)
            self.assertNotIn("V13", rows)                                                     # negative: no text-run rows on a PDF run
            self.assertNotIn("V3p", rows)
            self.assertEqual((rows["V3"]["status"], rows["V3"]["msg"]), ("PASS", "all page locators ≤ 2; all cited figures/tables have caption anchors"))
            self.write_cards(run, ["p.9"])
            _, rows = self.verify(run)
            self.assertEqual(rows["V3"]["status"], "FAIL")                                    # a page beyond the PDF is still a FAIL


if __name__ == "__main__":
    unittest.main()
