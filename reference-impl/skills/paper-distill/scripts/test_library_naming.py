"""Regression for the 2026-09-04 migrate orphan (copy-census R8, retired 2026-09-19).

`migrate` rewrote run ids inside files but not inside file NAMES, so each moved
paper folder kept `<old id>_keypoint.md` beside the regenerated canonical note.
Both sides of each check are asserted: what must move / be reported, and what
must stay put / stay silent.

    python test_library_naming.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import library  # noqa: E402


def touch(path: Path, text="x\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class RetireOldNamed(unittest.TestCase):

    def setUp(self):
        self.dst = Path(tempfile.mkdtemp(prefix="pd-lib-")) / "Bose2024_x"
        self.old = "20260903_Bose2024_x"

    def test_old_named_note_moves_to_previous(self):
        touch(self.dst / f"{self.old}_keypoint.md")
        moved = library.retire_old_named(self.dst, self.old)
        self.assertEqual([self.dst / "_previous" / f"{self.old}_keypoint.md"], moved)
        self.assertFalse((self.dst / f"{self.old}_keypoint.md").exists())

    def test_canonical_and_unrelated_files_stay(self):
        keep = [touch(self.dst / "Bose2024_x_keypoint.md"), touch(self.dst / "story.json", "{}"),
                touch(self.dst / "20260903_Bose2024_xy_keypoint.md")]  # a LONGER id is not this id
        self.assertEqual([], library.retire_old_named(self.dst, self.old))
        for p in keep:
            self.assertTrue(p.exists(), p.name)


class StrayKeypoints(unittest.TestCase):

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="pd-home-"))
        paper = self.home / "Bose2024_x"
        touch(paper / "cards.json", "{}")
        touch(paper / "Bose2024_x_keypoint.md")
        touch(self.home / "_calibration" / "Bose2024_x" / "blind-Y" / "20260903_Bose2024_x-y_keypoint.md")
        touch(paper / "_previous" / "20260903_Bose2024_x_keypoint.md")
        self.paper = paper

    def test_clean_library_reports_nothing(self):
        # labelled copy areas (_calibration/, _previous/) are the sanctioned homes
        self.assertEqual([], library.stray_keypoints(self.home))

    def test_a_dated_note_beside_the_canonical_one_is_reported(self):
        stray = touch(self.paper / "20260903_Bose2024_x_keypoint.md")
        self.assertEqual([stray], library.stray_keypoints(self.home))


class RewriteIdsStaysInside(unittest.TestCase):
    """The vault root holds junctions into a skill folder and LexiconVault (measured 2026-10-19); a --home
    above PaperSurvey must not rewrite files behind them."""

    def test_junction_target_is_not_rewritten(self):
        base = Path(tempfile.mkdtemp(prefix="pd-rw-"))
        home, outside = base / "home", base / "outside"
        touch(home / "P1" / "note.md", "OLDID here\n")
        touch(outside / "domain.md", "OLDID outside\n")
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(home / "domains"), str(outside)], capture_output=True)
        if r.returncode != 0:
            self.skipTest("junction fixture not creatable")
        n = library.rewrite_ids(home, {"OLDID": "NEWID"})
        self.assertEqual("NEWID here\n", (home / "P1" / "note.md").read_text(encoding="utf-8"))
        self.assertEqual("OLDID outside\n", (outside / "domain.md").read_text(encoding="utf-8"))
        self.assertEqual(1, n)


class ExplainerLink(unittest.TestCase):
    """2026-11-03 (user ruling): the README 檔案 column and the keypoint note link the ONE explainer page (說明頁), not 一頁 / 多頁.
    Rung 0 (example tests). Positive: a paper whose folder holds paper-explainer.html gets the link. Negative: one without it gets
    none, and the retired labels are gone even while an old onepage.html is still in the folder."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="pd-expl-"))
        self.entries = []
        for paper, has in (("Aaa2024_with", True), ("Bbb2024_without", False)):
            d = self.home / paper
            touch(d / "story.json", json.dumps({"logic": {"keypoint": "k", "keypoint_description": "d"}, "source": {"title": "T", "authors": ["A B"], "year": 2024}}))
            touch(d / "onepage.html", "<html></html>")
            if has:
                touch(d / "paper-explainer.html", "<html></html>")
            self.entries.append({"paper": paper, "run_id": paper, "path": str(d), "kind": "accepted", "year": 2024, "title": "T", "keypoint_title": "k",
                                 "c1_verdict": "", "products": [f for f in library.PRODUCT_FILES if (d / f).exists()]})

    def test_readme_links_the_explainer_only_where_it_exists(self):
        library.write_readme(self.home, {"entries": self.entries})
        rows = {l.split("`")[1]: l for l in (self.home / "README.md").read_text(encoding="utf-8").splitlines() if l.startswith("| `")}
        self.assertIn("[說明頁](Aaa2024_with/paper-explainer.html)", rows["Aaa2024_with"])
        self.assertNotIn("說明頁", rows["Bbb2024_without"])
        for r in rows.values():
            self.assertNotIn("一頁", r)
            self.assertNotIn("多頁", r)

    def test_keypoint_note_links_the_explainer(self):
        out = library.write_keypoint_note(self.home, self.entries[0], {e["run_id"]: e for e in self.entries})
        txt = out.read_text(encoding="utf-8")
        self.assertIn("[說明頁](Aaa2024_with/paper-explainer.html)", txt)
        self.assertNotIn("練習用一頁", txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
