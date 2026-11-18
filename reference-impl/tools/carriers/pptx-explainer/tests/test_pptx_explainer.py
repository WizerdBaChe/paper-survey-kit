"""pptx-explainer: render the golden sample, assert the deck, and fire every gate on a known-bad copy.

Run: python -X utf8 -m unittest discover -s ~/.claude/tools/carriers/pptx-explainer/tests -v

Rung 0/1 evidence (examples + enumeration over the sample's own blocks). Every negative control prints the
asserted value on BOTH sides (clean deck vs mutated deck) so a control that does not move its value is visible.
"""
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CARRIERS = Path(__file__).resolve().parents[2]
PE = CARRIERS / "pptx-explainer"
SAMPLE = CARRIERS / "samples" / "sample.explainer.json"
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402
ASSET = (hkroots.path("WORK_ROOT", "AssetVault", "assets", "pattern-template", "python", "pptx-deck-builder")
         or Path("X:/synth/work-root/AssetVault/assets/pattern-template/python/pptx-deck-builder"))  # unset: absent
sys.path.insert(0, str(CARRIERS))

from PIL import Image  # noqa: E402
from typing import Any, cast  # noqa: E402
from pptx import Presentation as _Presentation  # noqa: E402
Presentation: Any = _Presentation   # python-pptx types every shape as BaseShape; the tests probe shape kinds at run time
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

from common import content as content_mod  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(f"pe_test_{name}", PE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render, gates = _load("render"), _load("gates")


def all_text(path):
    """Every text frame, table cell and notes text of a deck, slide by slide."""
    prs = Presentation(str(path))
    out = []
    for s in prs.slides:
        parts = []
        for sh in s.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                parts += [c.text_frame.text for r in sh.table.rows for c in r.cells]
        parts.append(s.notes_slide.notes_text_frame.text if s.has_notes_slide else "")
        out.append(parts)
    return out


def shapes_named(prs, name):
    return [(i, sh) for i, s in enumerate(prs.slides, 1) for sh in s.shapes if sh.name == name]


def gate_map(path):
    return {n: (ok, d) for n, ok, d in gates.gates(path)}


class SampleDeck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="pptx-explainer-test-"))
        cls.content = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cls.out = cls.tmp / "sample.pptx"
        render.render(cls.content, SAMPLE.parent, cls.out)
        cls.findings = list(render.FINDINGS_LAST)
        cls.prs = Presentation(str(cls.out))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, name):
        dst = self.tmp / name
        shutil.copyfile(self.out, dst)
        return dst

    # -------------------------------------------------------------- preconditions
    def test_sample_is_valid_content(self):
        self.assertEqual(content_mod.validate(self.content, SAMPLE.parent), [])

    def test_vendored_files_match_recorded_sha_and_asset(self):
        text = (PE / "CARRIER.md").read_text(encoding="utf-8")
        for fn in ("deck_builder.py", "deck_layout.py"):
            # line-ending-normalised: ~/.claude's eol-sync rewrites working-tree endings after a commit
            lf = lambda p: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            sha = lf(PE / "vendor" / fn)
            self.assertRegex(text, fn + r"[^\n]*" + sha, f"CARRIER.md does not record the LF sha256 of vendor/{fn}")
            if ASSET.exists():
                self.assertEqual(sha, lf(ASSET / fn), f"vendor/{fn} differs from the AssetVault asset")
        if not ASSET.exists():
            # every recorded-sha check above has run for BOTH files; only the asset comparison is skipped
            print(f"UNDETERMINED: carriers pptx-explainer: asset folder {ASSET} is absent here, "
                  "so the vendor copies were not compared to the asset")
            self.skipTest(f"BLOCKED: asset folder {ASSET} not reachable; vendor copies not compared to the asset")

    # -------------------------------------------------------------- structure
    def test_slide_count_and_determinism(self):
        n_sections = len(self.content["sections"])
        floor = 1 + 2 + n_sections + 3      # cover + guide + overview + sections + glossary + refs + colophon
        n = len(self.prs.slides)
        self.assertGreaterEqual(n, floor)
        self.assertEqual(n, 11)              # golden sample: cover + guide + 4 sections (5 slides) + overview + glossary + refs + colophon - see CARRIER.md
        again = self.tmp / "again.pptx"
        render.render(self.content, SAMPLE.parent, again)
        self.assertEqual(all_text(self.out), all_text(again), "same content must give the same slide texts")

    # -------------------------------------------------------------- start guide / end overview (D4, 2026-11-16)
    def _slide_texts(self, prs, i):
        s = prs.slides[i]
        parts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        parts += [c.text_frame.text for sh in s.shapes if getattr(sh, "has_table", False) and sh.has_table
                  for r in sh.table.rows for c in r.cells]
        return "\n".join(parts)

    def test_guide_is_a_route_without_answers(self):
        """Example test (rung 0): slide 2 lists every section heading and its summary, and no takeaway."""
        txt = self._slide_texts(self.prs, 1)
        self.assertIn("這份簡報的路線", txt)
        for i, sec in enumerate(self.content["sections"], 1):
            self.assertIn(f"第 {i} 節", txt)
            self.assertIn(render.Ctx(self.content).plain(sec["heading"]), txt)
        for sec in self.content["sections"]:
            for t in sec.get("takeaways", []):
                self.assertNotIn(t, txt, "the start guide carries the route, never the answers")

    def test_overview_is_a_take_home_map(self):
        """Example test (rung 0): the slide before the glossary restates the purpose and every section's takeaways."""
        idx = next(i for i, s in enumerate(self.prs.slides)
                   if any(sh.has_text_frame and sh.text_frame.text == "全貌：帶回去用" for sh in s.shapes))
        txt = self._slide_texts(self.prs, idx)
        self.assertIn("讀完能做到", txt)
        for sec in self.content["sections"]:
            for t in sec.get("takeaways", []):
                self.assertIn(t, txt)
        self.assertIn("詞彙", self._slide_texts(self.prs, idx + 1))

    def test_negative_one_section_has_no_menus(self):
        one = json.loads(json.dumps(self.content))
        one["sections"] = one["sections"][:1]
        out = self.tmp / "one.pptx"
        render.render(one, SAMPLE.parent, out)
        texts = "\n".join(self._slide_texts(Presentation(str(out)), i) for i in range(len(Presentation(str(out)).slides)))
        sample = "\n".join(self._slide_texts(self.prs, i) for i in range(len(self.prs.slides)))
        counts = (sample.count("這份簡報的路線"), sample.count("全貌：帶回去用"))
        print(f"\n  menus: sample={counts}  one-section={(texts.count('這份簡報的路線'), texts.count('全貌：帶回去用'))}")
        self.assertEqual(counts, (1, 1))
        self.assertNotIn("這份簡報的路線", texts)
        self.assertNotIn("全貌：帶回去用", texts)

    def test_each_block_type_produced_its_shape(self):
        prs, sample = self.prs, self.content
        want = {"para": ".para", "bullets": ".bullets", "steps": ".step1", "table": ".table", "figure": ".figure",
                "callout": ".callout", "metrics": ".metric1", "quote": ".quote", "code": ".code"}
        seen = set()
        for sec in sample["sections"]:
            for bi, b in enumerate(sec["blocks"], 1):
                nm = f"{sec['id']}.{bi}{want[b['type']]}"
                hits = shapes_named(prs, nm)
                self.assertTrue(hits, f"block {sec['id']}.{bi} ({b['type']}) produced no shape named {nm}")
                seen.add(b["type"])
        self.assertEqual(seen, set(want), "the golden sample must exercise every block type")
        # table is a native table, figure is a picture
        _, tbl = shapes_named(prs, "carriers.1.table")[0]
        self.assertTrue(tbl.has_table)
        self.assertEqual([c.text for c in tbl.table.rows[0].cells], sample["sections"][2]["blocks"][0]["columns"])
        _, pic = shapes_named(prs, "flow.2.figure")[0]
        self.assertEqual(pic.shape_type, MSO_SHAPE_TYPE.PICTURE)
        with Image.open(SAMPLE.parent / "sample-figure.png") as im:
            src_ar = im.height / im.width
        self.assertAlmostEqual(pic.height / pic.width, src_ar, places=2, msg="picture aspect must be the measured one")
        # figure card lines
        self.assertEqual(shapes_named(prs, "flow.2.figcard-label1")[0][1].text_frame.text, "圖中呈現")
        self.assertEqual(shapes_named(prs, "flow.2.figcard-label2")[0][1].text_frame.text, "未畫出")
        # the three callout kinds are three different fills
        fills = set()
        for sec in ("why", "rules"):
            for i, sh in [(i, sh) for i, s in enumerate(prs.slides, 1) for sh in s.shapes
                          if sh.name.startswith(sec + ".") and sh.name.endswith(".callout-bg")]:
                fills.add(str(sh.fill.fore_color.rgb))
        self.assertEqual(len(fills), 3, f"key/note/warn callouts must be filled differently, got {fills}")
        # takeaways closing box sits on the section's last slide
        kick = [i for i, s in enumerate(prs.slides, 1)
                if any(sh.name == "kicker" and sh.text_frame.text == "第 1 節" for sh in s.shapes)]
        tk = [i for i, _ in shapes_named(prs, "why.takeaways-head")]
        self.assertEqual(tk, [max(kick)])
        self.assertEqual(shapes_named(prs, "why.takeaways-head")[0][1].text_frame.text, "本節重點")
        # glossary / refs / colophon slides
        self.assertTrue(shapes_named(prs, "glossary.table") and shapes_named(prs, "refs.table"))
        self.assertTrue(shapes_named(prs, "colophon.1.para"))
        cover = " ".join(all_text(self.out)[0])
        for v in (sample["meta"]["title"], sample["meta"]["subtitle"], sample["meta"]["purpose"],
                  sample["meta"]["date"], sample["meta"]["author"]):
            self.assertIn(v, cover)

    def test_inline_tokens_rendered(self):
        prs = self.prs
        _, para = shapes_named(prs, "why.1.para")[0]
        runs = [r for p in para.text_frame.paragraphs for r in p.runs]
        bold = {r.text for r in runs if r.font.bold}
        self.assertTrue({"內容只寫一次", "轉接器", "內容檔"} <= bold, f"bold / gloss runs: {bold}")
        self.assertIn("〔使用者裁定 2026-10-09〕", para.text_frame.text)
        _, bl = shapes_named(prs, "carriers.3.bullets")[0]
        self.assertIn("為什麼要把內容和載體分開", bl.text_frame.text)          # [[s:why]] -> the section heading
        self.assertNotIn("[[", " ".join(sum(all_text(self.out), [])))

    def test_notes_declare_every_slide(self):
        for i, s in enumerate(self.prs.slides, 1):
            nt = s.notes_slide.notes_text_frame.text
            self.assertIn("這頁回答：", nt, f"slide {i}")
            self.assertIn("圖種：", nt, f"slide {i}")

    def test_type_tiers_and_separate_title_description(self):
        prs = self.prs
        for i in (2, 3, 4):
            s = prs.slides[i - 1]
            title = [sh for sh in s.shapes if sh.name == "title"]
            desc = [sh for sh in s.shapes if sh.name == "description"]
            self.assertEqual(len(title), 1)
            self.assertEqual(len(desc), 1, f"slide {i}: title and description must be two objects")
            self.assertGreaterEqual(min(r.font.size.pt for r in title[0].text_frame.paragraphs[0].runs), 25.5)
            self.assertEqual(max(r.font.size.pt for r in desc[0].text_frame.paragraphs[0].runs), 16)

    def test_every_run_has_cjk_font_and_lang(self):
        n = 0
        for s in self.prs.slides:
            for sh in s.shapes:
                frames = [sh.text_frame] if sh.has_text_frame else []
                if getattr(sh, "has_table", False) and sh.has_table:
                    frames += [c.text_frame for r in sh.table.rows for c in r.cells]
                for tf in frames:
                    for p in tf.paragraphs:
                        for r in p.runs:
                            if not r.text.strip():
                                continue
                            n += 1
                            rpr = r._r.rPr
                            self.assertEqual(rpr.get("lang"), "zh-TW", r.text)
                            self.assertIsNotNone(rpr.find(qn("a:ea")), r.text)
        self.assertGreater(n, 100)

    def test_flat_no_theme_effects_and_named_shapes(self):
        n_decor = 0
        for i, s in enumerate(self.prs.slides, 1):
            for sh in s.shapes:
                el = sh._element
                if el.tag == qn("p:cxnSp") or sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                    eff = el.find(qn("p:spPr")).find(qn("a:effectLst"))
                    self.assertIsNotNone(eff, f"slide {i} {sh.name}: no explicit empty effectLst (inherits theme shadow)")
                    self.assertEqual(len(eff), 0, f"slide {i} {sh.name}: effectLst is not empty")
                    n_decor += 1
                is_content = bool(
                    (sh.has_text_frame and sh.text_frame.text.strip())
                    or (getattr(sh, "has_table", False) and sh.has_table)
                    or sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
                if is_content:
                    self.assertFalse(re.match(r"(TextBox|Rectangle|Table|Picture|Rounded)", sh.name),
                                     f"slide {i}: content shape keeps a default name {sh.name!r}")
        self.assertGreater(n_decor, 10)

    def test_layout_findings_are_not_overflow(self):
        bad = [f for f in self.findings if f["gate"] in ("overflow", "fit", "title-wrap")]
        self.assertEqual(bad, [], f"layout findings that mean content does not fit: {bad}")

    # -------------------------------------------------------------- gates: clean deck passes
    def test_gates_pass_on_the_sample(self):
        g = gate_map(self.out)
        self.assertTrue({"type_audit", "structure", "geometry"} <= set(g))
        for name, (ok, detail) in g.items():
            self.assertTrue(ok, f"{name}: {detail}")
        print("\n  clean deck:", {k: v[1] for k, v in g.items()})

    # -------------------------------------------------------------- negative controls
    def test_negative_a_nine_point_run_fails_type_audit(self):
        bad = self.copy("nine-pt.pptx")
        prs = Presentation(str(bad))
        _, para = [(i, sh) for i, s in enumerate(prs.slides, 1) for sh in s.shapes if sh.name == "why.1.para"][0]
        para.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
        prs.save(str(bad))
        clean, mutated = gate_map(self.out), gate_map(bad)
        print(f"\n  control (a) type_audit: clean={clean['type_audit']}  9pt={mutated['type_audit']}")
        self.assertTrue(clean["type_audit"][0])
        self.assertFalse(mutated["type_audit"][0])
        self.assertIn("9", mutated["type_audit"][1])                       # the asserted value is the 9 pt itself
        self.assertTrue(mutated["structure"][0], "the 9 pt copy must still be structurally fine")

    def test_negative_b_leftover_marker_fails_structure(self):
        bad = self.copy("marker.pptx")
        prs = Presentation(str(bad))
        _, para = [(i, sh) for i, s in enumerate(prs.slides, 1) for sh in s.shapes if sh.name == "why.1.para"][0]
        para.text_frame.paragraphs[0].runs[-1].text += "[[r:x]]"
        prs.save(str(bad))
        clean, mutated = gate_map(self.out), gate_map(bad)
        print(f"\n  control (b) structure: clean={clean['structure']}  marker={mutated['structure']}")
        self.assertTrue(clean["structure"][0])
        self.assertFalse(mutated["structure"][0])
        self.assertIn("[[", mutated["structure"][1])
        self.assertTrue(mutated["type_audit"][0])

    def test_negative_marker_in_table_cell_and_in_notes(self):
        for where in ("table", "notes"):
            bad = self.copy(f"marker-{where}.pptx")
            prs = Presentation(str(bad))
            if where == "table":
                tbl = [sh for s in prs.slides for sh in s.shapes if sh.name == "carriers.1.table"][0]
                tbl.table.cell(1, 0).text_frame.paragraphs[0].runs[0].text += "[[g:nope]]"
            else:
                prs.slides[3].notes_slide.notes_text_frame.text += " [[s:nope]]"
            prs.save(str(bad))
            ok, detail = gate_map(bad)["structure"]
            self.assertFalse(ok, where)
            self.assertIn("[[", detail, where)

    def test_negative_missing_notes_declaration_fails_structure(self):
        bad = self.copy("no-notes.pptx")
        prs = Presentation(str(bad))
        prs.slides[1].notes_slide.notes_text_frame.text = "just a remark"
        prs.save(str(bad))
        ok, detail = gate_map(bad)["structure"]
        print(f"\n  control notes: clean={gate_map(self.out)['structure'][1][:40]!r}  mutated={detail[:70]!r}")
        self.assertFalse(ok)
        self.assertIn("slide 2", detail)

    def test_negative_dropped_slide_fails_structure(self):
        bad = self.copy("dropped.pptx")
        prs = Presentation(str(bad))
        lst = prs.slides._sldIdLst
        for _ in range(len(prs.slides) - 3):                                 # leave fewer slides than 1 + sections
            lst.remove(lst[-1])
        prs.save(str(bad))
        ok, detail = gate_map(bad)["structure"]
        self.assertFalse(ok)
        self.assertIn("slides <", detail)

    def test_negative_geometry_overlap_and_off_slide(self):
        clean = gate_map(self.out)["geometry"]
        self.assertTrue(clean[0])
        bad = self.copy("overlap.pptx")
        prs = Presentation(str(bad))
        quote = [sh for s in prs.slides for sh in s.shapes if sh.name == "why.3.quote"][0]
        callout = [sh for s in prs.slides for sh in s.shapes if sh.name == "why.2.callout"][0]
        quote.top = callout.top                                              # text on text
        prs.save(str(bad))
        ok1, d1 = gate_map(bad)["geometry"]
        self.assertFalse(ok1)
        self.assertIn("overlaps", d1)
        bad2 = self.copy("off-slide.pptx")
        prs = Presentation(str(bad2))
        quote = [sh for s in prs.slides for sh in s.shapes if sh.name == "why.3.quote"][0]
        quote.left = prs.slide_width - Inches(1)
        prs.save(str(bad2))
        ok2, d2 = gate_map(bad2)["geometry"]
        self.assertFalse(ok2)
        self.assertIn("outside the slide", d2)
        print(f"\n  control geometry: clean={clean[1][:50]!r}  overlap={d1[:60]!r}  off-slide={d2[:50]!r}")

    def test_gates_never_raise_on_garbage(self):
        junk = self.tmp / "junk.pptx"
        junk.write_bytes(b"not a zip")
        res = gates.gates(junk)
        self.assertEqual({n for n, _, _ in res}, {"type_audit", "structure", "geometry"})
        self.assertTrue(all(ok is False for _, ok, _ in res), res)

    def test_end_to_end_build_and_stamp(self):
        sys.path.insert(0, str(CARRIERS))
        spec = importlib.util.spec_from_file_location("carriers_build_for_test", CARRIERS / "build.py")
        assert spec is not None and spec.loader is not None
        bmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bmod)
        out = self.tmp / "e2e.pptx"
        ok, lines = bmod.build("pptx-explainer", SAMPLE, out)
        self.assertTrue(ok, "\n".join(lines))
        verdict, _ = bmod._stamp.check(out)
        self.assertEqual(verdict, "ok")


class ContinuationDeck(unittest.TestCase):
    """A section bigger than one slide continues on '<heading>（續）' slides; nothing is lost or reordered."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="pptx-explainer-cont-"))
        rows = [[f"第{i}列", f"項目{i}", "說明文字" * 6] for i in range(1, 31)]
        sents = "".join(f"這是第{i}句，說明一件事情的來龍去脈。" for i in range(1, 41))
        cls.content = {
            "schema": "explainer/1",
            "meta": {"title": "長內容測試", "date": "2026-10-09", "audience": "audience", "lang": "zh-TW"},
            "sections": [
                {"id": "long", "heading": "很長的一節", "summary": "一頁放不下。", "takeaways": ["一", "二"],
                 "blocks": [
                     {"type": "para", "text": sents},
                     {"type": "bullets", "items": [f"第{i}個要點，說明它為什麼重要。" for i in range(1, 26)]},
                     {"type": "table", "caption": "三十列", "columns": ["編號", "名稱", "說明"], "rows": rows},
                     {"type": "steps", "items": [{"title": f"步驟{i}", "text": "把這一步做完，" * 6} for i in range(1, 9)]},
                     {"type": "metrics", "items": [{"label": f"指標{i}", "value": str(i), "unit": "個"} for i in range(1, 14)]},
                 ]},
            ],
        }
        assert content_mod.validate(cls.content, cls.tmp) == []
        cls.out = cls.tmp / "long.pptx"
        render.render(cls.content, cls.tmp, cls.out)
        cls.prs = Presentation(str(cls.out))
        cls.findings = list(render.FINDINGS_LAST)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_continuation_slides_exist_and_are_titled(self):
        titles = [[sh.text_frame.text for sh in s.shapes if sh.name == "title"] for s in self.prs.slides]
        titles = [t[0] for t in titles if t]
        self.assertEqual(titles[0], "很長的一節")
        cont = [t for t in titles if t == "很長的一節（續）"]
        self.assertGreaterEqual(len(cont), 4, titles)
        print(f"\n  long section -> {len(self.prs.slides)} slides, {len(cont)} continuation slides, findings={self.findings}")

    def test_nothing_lost_in_the_split(self):
        text = "\n".join("\n".join(p) for p in all_text(self.out))
        for i in range(1, 41):
            self.assertIn(f"這是第{i}句", text)
        for i in range(1, 26):
            self.assertIn(f"第{i}個要點", text)
        for i in range(1, 31):
            self.assertIn(f"第{i}列", text)
        for i in range(1, 9):
            self.assertIn(f"步驟{i}", text)
        for i in range(1, 14):
            self.assertIn(f"指標{i}", text)
        self.assertIn("本節重點", text)

    def test_table_header_repeats_on_every_fragment(self):
        frags = [sh for s in self.prs.slides for sh in s.shapes if getattr(sh, "has_table", False) and sh.has_table]
        self.assertGreaterEqual(len(frags), 2)
        for sh in frags:
            self.assertEqual([c.text for c in sh.table.rows[0].cells], ["編號", "名稱", "說明"])
        self.assertEqual(sum(len(sh.table.rows) - 1 for sh in frags), 30)

    def test_order_is_preserved(self):
        text = "\n".join("\n".join(p) for p in all_text(self.out))
        pos = [text.index(k) for k in ("這是第1句", "第1個要點", "第1列", "步驟1", "指標1", "本節重點")]
        self.assertEqual(pos, sorted(pos))

    def test_split_metric_cards_keep_one_width(self):
        widths = {round(sh.width / 914400, 2) for s in self.prs.slides for sh in s.shapes
                  if sh.name.startswith("long.5.metric") and sh.name.endswith("-bg")}
        self.assertEqual(len(widths), 1, f"split metrics changed card width: {widths}")

    def test_gates_pass_on_the_long_deck(self):
        for name, ok, detail in gates.gates(self.out):
            self.assertTrue(ok, f"{name}: {detail}")


class OversizeBlock(unittest.TestCase):
    """An unsplittable block taller than a slide is reported, and the geometry gate refuses the build."""

    def test_oversize_callout_is_reported_and_gate_fails(self):
        tmp = Path(tempfile.mkdtemp(prefix="pptx-explainer-big-"))
        try:
            content = {"schema": "explainer/1",
                       "meta": {"title": "過大區塊", "date": "2026-10-09", "audience": "audience", "lang": "zh-TW"},
                       "sections": [{"id": "big", "heading": "一個放不下的提示框", "summary": "不可拆的區塊。",
                                     "blocks": [{"type": "callout", "kind": "note", "text": "這是一段很長的說明。" * 80}]}]}
            self.assertEqual(content_mod.validate(content, tmp), [])
            out = tmp / "big.pptx"
            render.render(content, tmp, out)
            kinds = [f["gate"] for f in render.FINDINGS_LAST]
            g = gate_map(out)
            print(f"  oversize callout: findings={kinds}  geometry={g['geometry']}")
            self.assertIn("overflow", kinds)
            self.assertFalse(g["geometry"][0])
            self.assertRegex(g["geometry"][1], r"outside the slide|page-number band")
            self.assertTrue(g["structure"][0] and g["type_audit"][0])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# explainer/2 `code` block (v2): the literal text reaches the slide character for character. Control pair: the
# real renderer passes the literal check, a mutant that tokenises inline markup in code text fails the same check.
CODE_LITERAL = ('powershell -ExecutionPolicy Bypass -File "$HOME\\Downloads\\x"\n'
                "Write-Host '**not bold**' & <b>tag</b> \"q\"\n"
                "\n"
                "\t$a = @{ k = 'v' }[0]  # [x] [[g:nope]] [[r:nope]]")
CODE_LITERAL_NO_BRACKET_MARKERS = CODE_LITERAL.replace("[[g:nope]] [[r:nope]]", "")


def _code_content(text, extra=None, schema="explainer/2"):
    blocks = [{"type": "code", "text": text, "lang": "powershell", "caption": "指令範例"}]
    if extra:
        blocks += extra
    return {"schema": schema,
            "meta": {"title": "程式碼測試", "date": "2026-11-04", "audience": "audience", "lang": "zh-TW"},
            "sections": [{"id": "c1", "heading": "指令", "summary": "照抄執行。", "blocks": blocks}]}


def _code_shape_text(path):
    """The text of the shape named c1.1.code, plus its runs' typefaces and sizes."""
    prs = Presentation(str(path))
    hits = shapes_named(prs, "c1.1.code")
    if not hits:
        return None, set(), set()
    tf = hits[0][1].text_frame
    runs = [r for p in tf.paragraphs for r in p.runs]
    return tf.text, {r.font.name for r in runs}, {r.font.size.pt for r in runs}


class CodeBlockDeck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="pptx-explainer-code-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def build(self, name, content):
        self.assertEqual(content_mod.validate(content, self.tmp), [])
        out = self.tmp / f"{name}.pptx"
        render.render(content, self.tmp, out)
        return out

    def test_literal_survives_character_for_character_in_consolas(self):
        out = self.build("good", _code_content(CODE_LITERAL))
        text, fonts, sizes = _code_shape_text(out)
        print(f"\n  [literal] expected={CODE_LITERAL!r}\n  [literal] deck    ={text!r}  fonts={fonts} sizes={sizes}")
        self.assertEqual(text, CODE_LITERAL)
        self.assertEqual(fonts, {"Consolas"})
        self.assertEqual(sizes, {14.0})                       # the body floor: nothing shrinks, long lines wrap
        g = gate_map(out)
        for name in ("type_audit", "structure", "geometry"):
            self.assertTrue(g[name][0], f"{name}: {g[name][1]}")      # incl. a literal [[g:..]] in code text
        fill = [sh for _, sh in shapes_named(Presentation(str(out)), "c1.1.code-bg")]
        self.assertEqual(len(fill), 1)
        self.assertEqual(str(fill[0].fill.fore_color.rgb), "F1F3F5")   # the light fill

    def test_negative_control_inline_markup_mutant_is_caught(self):
        content = _code_content(CODE_LITERAL_NO_BRACKET_MARKERS)
        real_text, _, _ = _code_shape_text(self.build("real", content))
        original = render.prepare

        def mutant(b, c, tag):
            n = original(b, c, tag)
            if n["k"] == "code":      # the defect under test: code text run through the inline tokeniser
                n["lines"] = [c.plain(ln) for ln in n["lines"]]
            return n
        setattr(render, "prepare", mutant)
        try:
            mut_text, _, _ = _code_shape_text(self.build("mutant", content))
        finally:
            setattr(render, "prepare", original)
        print(f"\n  [mutant] real  ={real_text!r}\n  [mutant] mutant={mut_text!r}")
        self.assertEqual(real_text, CODE_LITERAL_NO_BRACKET_MARKERS)
        self.assertNotEqual(mut_text, CODE_LITERAL_NO_BRACKET_MARKERS, "the literal check did not notice inline markup")
        self.assertNotIn("**not bold**", cast(str, mut_text))

    def test_long_line_wraps_inside_the_box_and_keeps_every_character(self):
        long_line = "Get-ChildItem " + " ".join(f"-Path C:\\Users\\x\\folder{i}" for i in range(40))
        out = self.build("long", _code_content(long_line))
        text, _, sizes = _code_shape_text(out)
        self.assertEqual(text, long_line)
        self.assertEqual(sizes, {14.0})
        self.assertNotIn("overflow", [f["gate"] for f in render.FINDINGS_LAST])
        self.assertTrue(gate_map(out)["geometry"][0], gate_map(out)["geometry"][1])

    def test_tall_code_splits_across_slides_without_losing_a_line(self):
        lines = [f"Write-Output 'line {i}'" for i in range(1, 61)]
        out = self.build("tall", _code_content("\n".join(lines)))
        prs = Presentation(str(out))
        parts = [sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.name == "c1.1.code"]
        self.assertGreaterEqual(len(parts), 2, "60 lines cannot fit one slide")
        self.assertEqual("\n".join(parts), "\n".join(lines))
        self.assertTrue(all(ok for ok, _ in gate_map(out).values()), gate_map(out))


V1_FIXTURE = {"schema": "explainer/1",
              "meta": {"title": "舊格式", "date": "2026-10-09", "audience": "audience", "lang": "zh-TW"},
              "sections": [{"id": "old", "heading": "第一版內容", "summary": "只用第一版的區塊。",
                            "blocks": [{"type": "para", "text": "這份內容宣告 explainer/1，**照舊**可以建。"},
                                       {"type": "bullets", "items": ["不含 code 區塊"]}]}]}


class V1BackwardCompat(unittest.TestCase):
    """Backward-compat control: explainer/1 content validates, renders and passes every gate as before v2."""

    def test_v1_validates_renders_and_passes_every_gate(self):
        tmp = Path(tempfile.mkdtemp(prefix="pptx-explainer-v1-"))
        try:
            self.assertEqual(content_mod.validate(V1_FIXTURE, tmp), [])
            out = tmp / "v1.pptx"
            render.render(V1_FIXTURE, tmp, out)
            g = gate_map(out)
            self.assertEqual(sorted(g), ["geometry", "structure", "type_audit"])
            for name, (ok, detail) in g.items():
                self.assertTrue(ok, f"{name}: {detail}")
            self.assertIn("照舊", " ".join(sum(all_text(out), [])))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
