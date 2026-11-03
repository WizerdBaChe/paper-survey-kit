"""Tests of the html-explainer carrier against the golden sample.

  python -X utf8 -m unittest discover -s ~/.claude/tools/carriers/html-explainer/tests -v

Positive side: the golden sample renders, deterministically, with every block type in the DOM, and both
gates pass. Negative side (each control must make a gate FAIL, and the test records the detail the gate
printed for the good file and for the broken one, so the asserted value is seen to differ):
  a. data-page-class removed       -> structure False
  b. leftover "[[g:x]]" text        -> structure False
  c. an external <img src=http...>  -> structure False
  d. a content section deleted      -> structure False
  e. left-anchored painted blocks   -> fill_gate False
  f. a capped <main> column         -> main_fill False (fill_gate is blind to it on this shell; printed, not asserted)
"""
import hashlib
import subprocess
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARRIER = HERE.parent
ROOT = CARRIER.parent
SAMPLE = ROOT / "samples" / "sample.explainer.json"
SCHEMA = ROOT / "schema" / "explainer-1.schema.json"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(f"test_html_explainer_{name}", CARRIER / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render_mod, gates_mod = _load("render"), _load("gates")


class _Dom(HTMLParser):
    """Collects (tag, attrs, text-inside) for the elements the assertions look at."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.els, self._stack = [], []

    def handle_starttag(self, tag, attrs):
        el = {"tag": tag, "a": dict(attrs), "text": ""}
        self.els.append(el)
        self._stack.append(el)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i]["tag"] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        for el in self._stack:
            el["text"] += data

    def find(self, tag, cls=None, **attrs):
        out = []
        for e in self.els:
            if e["tag"] != tag:
                continue
            if cls is not None and cls not in (e["a"].get("class") or "").split():
                continue
            if any(e["a"].get(k.replace("_", "-")) != v for k, v in attrs.items()):
                continue
            out.append(e)
        return out


def _dom(text):
    d = _Dom()
    d.feed(text)
    d.close()
    return d


def _blocks(content):
    return [(s["id"], b) for s in content["sections"] for b in s["blocks"]]


class FillGateRowSeverityTest(unittest.TestCase):
    """v9 (sheet B2): which fill_gate rows block. Stubbed rows, no browser."""

    def row(self, status="PASS", width="PASS", cons=()):
        return {"status": status, "width_status": width, "consistency_reasons": list(cons)}

    def test_consistency_only_warn_passes(self):
        self.assertFalse(gates_mod._blocks(self.row("WARN", cons=["duplicate rules: a and b"])))

    def test_real_failures_block(self):
        cases = {"fail row": self.row("FAIL", "FAIL"),
                 "width warn (control e class)": self.row("WARN", "WARN"),
                 "advisory-downgraded consistency FAIL": self.row("WARN", cons=["advisory viewport — FAIL downgraded"]),
                 "consistency stage crashed": self.row("WARN", cons=["consistency not computed: boom"]),
                 "row without width_status, WARN": {"status": "WARN"}}
        for name, r in cases.items():
            with self.subTest(name):
                self.assertTrue(gates_mod._blocks(r), name)

    def test_row_without_width_status_pass(self):
        self.assertFalse(gates_mod._blocks({"status": "PASS"}))


class HtmlExplainerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="html-explainer-test-"))
        cls.content = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cls.a, cls.b = cls.tmp / "a" / "sample.html", cls.tmp / "b" / "sample.html"
        for p in (cls.a, cls.b):
            p.parent.mkdir()
            render_mod.render(cls.content, SAMPLE.parent, p)
        cls.text = cls.a.read_text(encoding="utf-8")
        cls.dom = _dom(cls.text)
        cls.good_gates = gates_mod.gates(cls.a)
        cls.good_structure = dict((n, (ok, d)) for n, ok, d in cls.good_gates)["structure"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _broken(self, name, edit):
        """Write a copy of the good page with `edit(text)` applied; assert the edit actually changed it."""
        new = edit(self.text)
        self.assertNotEqual(new, self.text, f"control {name}: the edit did not change the page (a no-op control proves nothing)")
        p = self.tmp / name / "sample.html"
        p.parent.mkdir(exist_ok=True)
        p.write_text(new, encoding="utf-8", newline="\n")
        return p

    # ---- positive side -------------------------------------------------------------------------------

    def test_determinism(self):
        self.assertEqual(self.a.read_bytes(), self.b.read_bytes(), "two renders of the same content differ")
        self.assertNotIn(b"\r", self.a.read_bytes(), "output must be LF-only")

    def test_root_element_and_skeleton(self):
        self.assertTrue(self.text.startswith(
            '<!doctype html>\n<html lang="zh-TW" data-page-class="document-long" data-audience="audience">\n<head>'))
        self.assertIn("</head>", self.text)
        self.assertIn("</main>", self.text)
        self.assertEqual(self.text.count("</head>"), 1)

    def test_every_schema_block_type_is_in_the_sample_and_in_the_dom(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        schema_types = {b["properties"]["type"]["const"] for b in schema["$defs"]["block"]["oneOf"]}
        used = {b["type"] for _, b in _blocks(self.content)}
        self.assertEqual(schema_types, used, "the golden sample must exercise every block type of explainer/1")
        d = self.dom
        blocks = [b for _, b in _blocks(self.content)]
        by = lambda t: [b for b in blocks if b["type"] == t]
        main_p = [e for e in d.find("p") if not e["a"]]  # paragraphs of blocks carry no attributes
        self.assertGreaterEqual(len(main_p), len(by("para")))
        self.assertEqual(len(d.find("ul")), len(by("bullets")))
        self.assertEqual(len(d.find("ol", "steps")), len(by("steps")))
        self.assertEqual(len(d.find("span", "st-t")), sum(len(b["items"]) for b in by("steps")))
        self.assertEqual(len(d.find("span", "st-d")), sum(1 for b in by("steps") for i in b["items"] if i.get("text")))
        self.assertEqual(len(d.find("table")), len(by("table")))
        tbl = by("table")[0]
        self.assertEqual(len(d.find("th")), len(tbl["columns"]))
        self.assertEqual(len(d.find("caption")), 1)
        self.assertEqual(len(d.find("figure", "tb")), len(by("figure")))
        self.assertTrue(d.find("img")[0]["a"]["src"].startswith("data:image/png;base64,"))
        self.assertEqual(len(d.find("span", "fshow")), len(by("figure")))
        self.assertEqual(len(d.find("span", "fnot")), len([b for b in by("figure") if b.get("not_drawn")]))
        self.assertIn("圖中呈現：", d.find("span", "fshow")[0]["text"])
        self.assertIn("未畫出：", d.find("span", "fnot")[0]["text"])
        kinds = sorted(e["a"]["data-kind"] for e in d.find("div", "box") if "data-kind" in e["a"])
        self.assertEqual(kinds, sorted(b["kind"] for b in by("callout")))
        self.assertEqual(len(d.find("div", "metric")), sum(len(b["items"]) for b in by("metrics")))
        self.assertEqual(len(d.find("blockquote", "quote")), len(by("quote")))
        self.assertIn(by("quote")[0]["source"], d.find("footer")[0]["text"])

    def test_sections_nav_rail_glossary_refs(self):
        c, d = self.content, self.dom
        sections = d.find("section", "ch")
        self.assertEqual(len(sections), len(c["sections"]) + 2)  # + 詞彙 + 出處
        self.assertEqual([s["a"]["id"] for s in sections][:len(c["sections"])], [s["id"] for s in c["sections"]])
        self.assertTrue(all(s["a"]["id"] for s in sections))
        self.assertEqual(len(d.find("h2")), len(sections))
        nav = [e for e in d.find("a") if "data-sec" in e["a"]]
        self.assertEqual(len(nav), len(sections))
        self.assertEqual(len(d.find("dt")), len(c["glossary"]))
        self.assertEqual(len(d.find("ol", "refs")[0:1]), 1)
        self.assertEqual(len([e for e in d.find("li") if str(e["a"].get("id", "")).startswith("r_")]), len(c["refs"]))
        # rail: one entry per section that has a summary or takeaways, carrying exactly the content's words
        rail = json.loads(re.search(r'<script type="application/json" id="rail-data">(.*?)</script>', self.text, re.S).group(1))
        want = {s["id"]: s for s in c["sections"] if s.get("summary") or s.get("takeaways")}
        self.assertEqual(sorted(rail), sorted(want))
        for sid, s in want.items():
            self.assertEqual(rail[sid].get("s"), s.get("summary"))
            self.assertEqual(rail[sid].get("t"), s.get("takeaways"))
        # shell registry: every glossary term / ref label is a key, every hover token resolves
        m = re.search(r"window\.SITE_REFS = (\{.*?\});\nwindow\.SITE_SYMS = (\{.*?\});</script>", self.text, re.S)
        refs, syms = json.loads(m.group(1)), json.loads(m.group(2))
        self.assertEqual(sorted(syms), sorted(g["term"] for g in c["glossary"]))
        self.assertEqual(sorted(refs), sorted(r["label"] for r in c["refs"]))
        self.assertEqual(len(d.find("script", id="previews")), 1)
        for e in d.find("span", "sym"):
            self.assertIn(e["a"]["data-key"], syms)
        for e in d.find("span", "ref"):
            self.assertIn(e["a"]["data-key"], refs)

    def test_meta_and_colophon(self):
        m = self.content["meta"]
        visible = re.sub(r"<[^>]+>", "", self.text)
        for k in ("title", "subtitle", "date", "author", "purpose", "source_note"):
            self.assertIn(m[k], visible, k)
        self.assertEqual(self.dom.find("title")[0]["text"], m["title"])
        self.assertEqual(self.dom.find("h1", "title")[0]["text"], m["title"])
        self.assertIn(m["author"], self.dom.find("footer", "buildinfo")[0]["text"])

    def test_gates_all_pass(self):
        names = [n for n, _, _ in self.good_gates]
        self.assertEqual(names, ["fill_gate", "main_fill", "structure"])
        for name, ok, detail in self.good_gates:
            self.assertTrue(ok, f"{name}: {detail}")

    def test_vendored_files_unedited(self):
        # One source for "unedited": the asset file at the `base` commit consumers.py recorded in
        # asset-choices.json when it vendored the file (derived; no hand-copied hash to update, fb:38c88250).
        # A newer asset (vault-ahead) is reported by `consumers.py check` and the HMI point, not here.
        # Compared line-ending-normalised: ~/.claude's eol-sync rewrites working-tree endings after a commit.
        choices = json.loads((CARRIER / "asset-choices.json").read_text(encoding="utf-8"))["assets"]
        homes = {"research-site-shell": ("pattern-template", "html-css", "research-site-shell"),
                 "prose-doc-layer": ("style", "html-css", "prose-doc-layer")}
        vault = hkroots.path("WORK_ROOT", "AssetVault")
        seen = []
        for asset, decl in choices.items():
            for name, f in decl["files"].items():
                seen.append(name)
                raw = (CARRIER / f["to"]).read_bytes()
                lf = raw.replace(b"\r\n", b"\n")
                if vault and (Path(vault) / ".git").exists():
                    rel = "/".join(("assets",) + homes[asset] + (name,))
                    r = subprocess.run(["git", "-C", str(vault), "show", f"{f['base']}:{rel}"], capture_output=True)
                    self.assertEqual(r.returncode, 0, f"{name}: base {f['base']} not readable in AssetVault")
                    self.assertEqual(lf, r.stdout.replace(b"\r\n", b"\n"),
                                     f"{name}: differs from the asset at its recorded base {f['base']} (edited?)")
                self.assertIn(raw.decode("utf-8").replace("\r\n", "\n"), self.text, f"{name}: not inlined verbatim")
        self.assertEqual(sorted(seen), ["prose-doc-layer.css", "site.css", "site.js"])

    def test_text_is_escaped(self):
        c = json.loads(json.dumps(self.content))
        c["sections"][0]["blocks"][0]["text"] = 'x </script><img src=x onerror=alert(1)> & "q" **b</b>**'
        c["glossary"][0]["gloss"] = "gloss </script><b>"
        p = self.tmp / "esc" / "e.html"
        p.parent.mkdir(exist_ok=True)
        render_mod.render(c, SAMPLE.parent, p)
        t = p.read_text(encoding="utf-8")
        self.assertNotIn("<img src=x", t)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", t)
        self.assertEqual(t.count("</script>"), self.text.count("</script>"))
        self.assertTrue(gates_mod._structure(p)[0], gates_mod._structure(p)[1])

    # ---- negative controls ----------------------------------------------------------------------------

    def _structure_fails(self, name, edit, expect):
        bad = self._broken(name, edit)
        ok, detail = gates_mod._structure(bad)
        print(f"\n  [control {name}] good structure={self.good_structure[0]} ({self.good_structure[1][:60]}...)"
              f"\n  [control {name}] broken structure={ok} ({detail[:160]})")
        self.assertTrue(self.good_structure[0])
        self.assertFalse(ok, f"control {name}: the structure gate accepted a broken page")
        self.assertIn(expect, detail)
        # and through the public entry point, by name
        self.assertFalse(dict((n, o) for n, o, _ in gates_mod.gates(bad))["structure"])

    def test_control_a_missing_page_class(self):
        self._structure_fails("a-no-page-class", lambda t: t.replace(' data-page-class="document-long"', "", 1),
                              "no data-page-class")

    def test_control_b_leftover_marker(self):
        self._structure_fails("b-marker", lambda t: t.replace("<p>以前一份說明", "<p>[[g:x]] 以前一份說明", 1),
                              "unresolved '[['")

    def test_control_c_external_load(self):
        self._structure_fails("c-external", lambda t: t.replace("</main>", '<img src="https://example.com/x.png"></main>', 1),
                              "load from outside")

    def test_control_d_section_deleted(self):
        def drop(t):
            i = t.index('<section class="ch" id="rules"')
            j = t.index("</section>", i) + len("</section>")
            return t[:i] + t[j:]
        self._structure_fails("d-section-missing", drop, "data-sections")

    def _gate_pair(self, name, css):
        bad = self._broken(name, lambda t: t.replace("</head>", f"<style>{css}</style>\n</head>", 1))
        res = dict((n, (o, d)) for n, o, d in gates_mod.gates(bad))
        good = dict((n, (o, d)) for n, o, d in self.good_gates)
        return good, res

    def test_control_e_left_anchored_blocks_fail_fill_gate(self):
        good, res = self._gate_pair("e-blocks", ".box,.twrap{max-width:560px}")
        print(f"\n  [control e] good fill_gate={good['fill_gate'][0]} ({good['fill_gate'][1]})"
              f"\n  [control e] capped fill_gate={res['fill_gate'][0]} ({res['fill_gate'][1][:200]})")
        self.assertTrue(good["fill_gate"][0])
        self.assertFalse(res["fill_gate"][0], "the fill gate accepted left-anchored 560px painted blocks")

    def test_control_f_capped_main_fails_main_fill(self):
        good, res = self._gate_pair("f-main", "main{max-width:640px;margin-right:auto}")
        print(f"\n  [control f] good main_fill={good['main_fill'][0]} ({good['main_fill'][1]})"
              f"\n  [control f] capped main_fill={res['main_fill'][0]} ({res['main_fill'][1][:220]})"
              f"\n  [control f] (informational) capped fill_gate={res['fill_gate'][0]}: its reach is carried by the rail / hint bar")
        self.assertTrue(good["main_fill"][0])
        self.assertFalse(res["main_fill"][0], "main_fill accepted a main column capped at 640px")


if __name__ == "__main__":
    unittest.main()

