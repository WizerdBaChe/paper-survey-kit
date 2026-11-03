"""carriers — build an explanatory deliverable from its content file into a registered carrier.

Rule: ~/.claude/rules/explainer-deliverables.md (user ruling 2026-10-09). Location rules: README.md.

  build.py list
  build.py validate <content.json>
  build.py build --carrier <id> --content <content.json> --out <file>     (validate -> render -> gates -> stamp)
  build.py check <output> --content <content.json>                         (ok | unstamped | edited | stale)
  build.py scan <root> [--json]                                            (stamped / unstamped explainer outputs under a root)
  build.py selftest [--quick]                                              (controls + golden sample + every carrier's unit tests)

Exit codes: 0 ok; 1 a gate/check failed; 2 usage or registry error.
Build is atomic: render, gates and stamp run on a temporary sibling file; only an output whose gates
all passed replaces --out. A failed build leaves the previous --out untouched and says so.
Severity by consumer: build/check are FAIL (a hard downstream reference — the stamp is what a
deliverable is recognised by); scan only reports. Ruler: the stamp proves WHICH carrier built the
file from WHICH content (text + figures) and that nothing changed since; it says nothing about content
quality or the rendered picture (carrier gates check structure/width/type floors; a human judges the
look). `check` without --content cannot see `stale`; scan never compares content.
"""
import argparse
import datetime as _dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from common import stamp as _stamp  # noqa: E402

REGISTRY = ROOT / "registry.json"
SAMPLE = ROOT / "samples" / "sample.explainer.json"
CARRIER_FILES = ("CARRIER.md", "render.py", "gates.py")
BUILD_NAMED = ("content", "stamp")       # registry gates that build.py itself runs
SCAN_SKIP = {".git", "node_modules", "vendor", "archive", ".venv", "venv", "site-packages", "dist", "__pycache__"}


def _content():
    from common import content  # jsonschema is needed only by validate/build
    return content


class RegistryError(Exception):
    pass


def registry():
    try:
        rows = json.loads(REGISTRY.read_text(encoding="utf-8"))["carriers"]
        return {r["id"]: r for r in rows}
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise RegistryError(f"{REGISTRY}: {e}") from e


def _module(cid, name):
    path = ROOT / cid / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"carrier_{cid.replace('-', '_')}_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(cid, content_path, out_path, _gates_override=None):
    """-> (ok, lines). Never stamps, and never replaces out_path with, an output whose gates failed."""
    reg = registry()
    if cid not in reg:
        return False, [f"carrier {cid!r} is not registered; known: {sorted(reg)}"]
    row = reg[cid]
    if row["status"] != "active":
        return False, [f"carrier {cid} status is {row['status']}, not active"]
    content_path, out_path = Path(content_path).resolve(), Path(out_path).resolve()
    if out_path.suffix.lower() != row["output_suffix"]:
        return False, [f"{cid} writes {row['output_suffix']} files, not {out_path.suffix}"]
    content = _content()
    try:
        data, csha = content.load(content_path)
    except (OSError, ValueError) as e:
        return False, [f"  content         : FAIL — cannot read {content_path}: {e}"]
    lines = []
    errs = content.validate(data, content_path.parent)
    lines.append(f"  content         : {'PASS' if not errs else 'FAIL'}")
    lines += [f"    - {e}" for e in errs]
    if errs:
        return False, lines + [f"  {out_path.name} untouched"]
    if data["schema"] not in row["consumes"]:
        return False, lines + [f"  {cid} consumes {row['consumes']}, content is {data['schema']}"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(f".{out_path.stem}.building{out_path.suffix}")
    try:
        try:
            _module(cid, "render").render(data, content_path.parent, tmp)
        except Exception as e:  # a renderer crash is a FAIL line, not a traceback
            return False, lines + [f"  render          : FAIL — {type(e).__name__}: {e}",
                                   "    " + traceback.format_exc(limit=3).strip().replace("\n", "\n    "),
                                   f"  {out_path.name} untouched"]
        ok = True
        gates_fn = _gates_override or _module(cid, "gates").gates
        try:
            results = gates_fn(tmp)
        except Exception as e:
            results = [("gates", False, f"{type(e).__name__}: {e}")]
        for name, gok, detail in results:
            ok &= bool(gok)
            lines.append(f"  {name:<16}: {'PASS' if gok else 'FAIL'}" + (f" — {detail}" if detail else ""))
        if not ok:
            lines.append(f"  stamp           : SKIPPED (a gate failed; {out_path.name} untouched, NOT a deliverable)")
            return False, lines
        _stamp.apply(tmp, {"carrier": cid, "version": row["version"], "schema": data["schema"],
                           "content_sha256": csha,
                           "built_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        verdict, detail = _stamp.check(tmp, csha)
        if verdict != "ok":
            lines.append(f"  stamp           : FAIL — {detail}")
            return False, lines + [f"  {out_path.name} untouched"]
        os.replace(tmp, out_path)
        lines.append(f"  stamp           : PASS — {_stamp.check(out_path, csha)[1]}")
        return True, lines
    finally:
        if tmp.exists():
            tmp.unlink()


def scan(root):
    root = Path(root).resolve()
    rows = []
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in (".html", ".htm", ".pptx") or not p.is_file():
            continue
        if any(part in SCAN_SKIP for part in p.relative_to(root).parts[:-1]):
            continue
        try:
            verdict, detail = _stamp.check(p)
            st = _stamp.read(p)[0] if verdict != "edited" else None
        except Exception as e:  # an unreadable output is reported, not skipped
            rows.append({"path": str(p), "verdict": "unreadable", "carrier": None, "detail": str(e)[:120]})
            continue
        rows.append({"path": str(p), "verdict": verdict, "carrier": (st or {}).get("carrier"), "detail": detail})
    return rows


# ------------------------------------------------------------------ selftest
def selftest(quick=False):
    content = _content()
    reg = registry()
    fails = []

    def expect(label, got, want):
        line = f"  control {label}: got {got!r}, expected {want!r}"
        print(line)
        if got != want:
            fails.append(line.strip())

    folders = {p.name for p in ROOT.iterdir() if p.is_dir() and (p / "render.py").exists()}
    for cid in sorted(set(reg) | folders):
        if cid not in reg:
            fails.append(f"folder {cid}/ has render.py but no registry row")
        elif cid not in folders:
            fails.append(f"registry row {cid} has no folder with render.py")
        else:
            missing = [f for f in CARRIER_FILES if not (ROOT / cid / f).exists()]
            if missing:
                fails.append(f"{cid}: missing {missing}")
    data, _ = content.load(SAMPLE)
    expect("golden sample validates", content.validate(data, SAMPLE.parent), [])
    for label, mutate in (
        ("unresolved [[g:]] in a block", lambda b: b["sections"][0]["blocks"][0].__setitem__("text", "x [[g:no-such-term]]")),
        ("unresolved [[g:]] in refs.detail", lambda b: b["refs"][0].__setitem__("detail", "見 [[g:no-such-term]]")),
        ("markup in a plain field (glossary.term)", lambda b: b["glossary"][0].__setitem__("term", "**粗**")),
        ("marker inside bold", lambda b: b["sections"][0]["blocks"][0].__setitem__("text", "**見 [[g:content]]**")),
        ("figure outside the content folder", lambda b: b["sections"][1]["blocks"][1].__setitem__("src", "../registry.png")),
        ("figure type not embeddable everywhere", lambda b: b["sections"][1]["blocks"][1].__setitem__("src", "x.svg")),
    ):
        bad = json.loads(json.dumps(data))
        mutate(bad)
        expect(f"validator rejects {label}", bool(content.validate(bad, SAMPLE.parent)), True)

    tmp = Path(tempfile.mkdtemp(prefix="carriers-selftest-"))
    try:
        for cid, row in sorted(reg.items()):
            if row["status"] != "active" or cid not in folders:
                continue
            suf = row["output_suffix"]
            out = tmp / f"sample-{cid}{suf}"
            ok, lines = build(cid, SAMPLE, out)
            print(f"[{cid}@{row['version']}] build {'PASS' if ok else 'FAIL'}")
            print("\n".join(lines))
            if not ok:
                fails.append(f"{cid}: golden sample build failed")
                continue
            ran = [n for n, _, _ in _module(cid, "gates").gates(out)]
            expect(f"{cid} registry gates == gates run", sorted(row["gates"]), sorted(set(ran) | set(BUILD_NAMED)))
            # the invariant: a failing gate never stamps and never replaces the previous output
            before = out.read_bytes()
            ok2, _ = build(cid, SAMPLE, out, _gates_override=lambda p: [("forced", False, "control")])
            expect(f"{cid} failing gate -> build False", ok2, False)
            expect(f"{cid} failing gate -> previous output untouched", out.read_bytes() == before, True)
            fresh = tmp / f"never-{cid}{suf}"
            build(cid, SAMPLE, fresh, _gates_override=lambda p: [("forced", False, "control")])
            expect(f"{cid} failing gate -> no output file", fresh.exists(), False)
            # tamper controls
            for label, fn in _tamper_cases(suf):
                t = tmp / f"t-{label}-{cid}{suf}"
                shutil.copyfile(out, t)
                fn(t)
                expect(f"{cid} {label}", _stamp.check(t)[0], "ok" if label == "no-op resave" else "edited")
            expect(f"{cid} wrong content digest -> stale", _stamp.check(out, "0" * 64)[0], "stale")
            # a changed figure with unchanged text makes the output stale
            fig_dir = tmp / f"fig-{cid}"
            shutil.copytree(SAMPLE.parent, fig_dir, ignore=shutil.ignore_patterns("built"))
            img = fig_dir / "sample-figure.png"
            img.write_bytes(img.read_bytes() + b"\0")
            expect(f"{cid} changed figure -> stale", _stamp.check(out, content.load(fig_dir / SAMPLE.name)[1])[0], "stale")
        if not quick:
            for cid in sorted(folders & set(reg)):
                tdir = ROOT / cid / "tests"
                if tdir.is_dir():
                    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", str(tdir)],
                                       capture_output=True, text=True, encoding="utf-8", errors="replace")
                    tail = [ln for ln in (r.stderr or "").splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
                    print(f"[{cid}] unit tests: {' | '.join(tail) or 'no summary'}")
                    if r.returncode != 0:
                        fails.append(f"{cid}: unit tests failed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for f in fails:
        print(f"FAIL - {f}")
    print("selftest: " + ("ALL PASS" if not fails else f"{len(fails)} FAIL") + (" (quick: unit tests skipped)" if quick else ""))
    return not fails


def _tamper_cases(suf):
    if suf == ".pptx":
        from pptx import Presentation

        def text_edit(p):
            prs = Presentation(str(p))
            for shape in prs.slides[0].shapes:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    shape.text_frame.paragraphs[0].runs[0].text += "（手改）"
                    break
            prs.save(str(p))

        def core_edit(p):
            prs = Presentation(str(p))
            prs.core_properties.title = "手改的標題"
            prs.save(str(p))

        def field_edit(p):
            prs = Presentation(str(p))
            st = json.loads(prs.core_properties.comments)
            st["carrier"] = "forged"
            prs.core_properties.comments = json.dumps(st)
            prs.save(str(p))

        def broken_stamp(p):
            prs = Presentation(str(p))
            prs.core_properties.comments = "使用者在檔案總管改了註解"
            prs.save(str(p))

        def resave(p):
            Presentation(str(p)).save(str(p))

        return [("text edit", text_edit), ("core-only edit", core_edit), ("stamp field edit", field_edit),
                ("broken stamp", broken_stamp), ("no-op resave", resave)]

    def html_sub(old, new):
        def f(p):
            t = p.read_text(encoding="utf-8")
            p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
        return f

    def field_edit(p):
        t = p.read_text(encoding="utf-8")
        p.write_text(t.replace("&quot;carrier&quot;: &quot;html-explainer&quot;", "&quot;carrier&quot;: &quot;forged&quot;", 1),
                     encoding="utf-8", newline="\n")

    def crlf(p):
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))

    return [("text edit", html_sub("</main>", "<p>手改</p></main>")), ("stamp field edit", field_edit),
            ("broken stamp", html_sub('<meta name="carrier-stamp" content="{', '<meta name="carrier-stamp" content="{x')),
            ("no-op resave", crlf)]


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    v = sub.add_parser("validate"); v.add_argument("content")
    b = sub.add_parser("build"); b.add_argument("--carrier", required=True); b.add_argument("--content", required=True); b.add_argument("--out", required=True)
    c = sub.add_parser("check"); c.add_argument("output"); c.add_argument("--content")
    s = sub.add_parser("scan"); s.add_argument("root"); s.add_argument("--json", action="store_true")
    t = sub.add_parser("selftest"); t.add_argument("--quick", action="store_true", help="skip the carriers' unit tests")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            for cid, r in registry().items():
                print(f"{cid}@{r['version']} [{r['status']}] {r['output_suffix']} {r['reading_mode']:<12} {r['label']}")
            return 0
        if a.cmd == "validate":
            content = _content()
            data, _ = content.load(a.content)
            errs = content.validate(data, Path(a.content).resolve().parent)
            print("\n".join(errs) if errs else "content: PASS")
            return 1 if errs else 0
        if a.cmd == "build":
            ok, lines = build(a.carrier, a.content, a.out)
            print(f"build {a.carrier} -> {a.out}")
            print("\n".join(lines))
            print("build: " + ("PASS" if ok else "FAIL"))
            return 0 if ok else 1
        if a.cmd == "check":
            csha = _content().load(a.content)[1] if a.content else None
            verdict, detail = _stamp.check(a.output, csha)
            print(f"{verdict}: {detail}")
            return 0 if verdict == "ok" else 1
        if a.cmd == "scan":
            rows = scan(a.root)
            if a.json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            else:
                for r in rows:
                    print(f"{r['verdict']:<10} {r.get('carrier') or '-':<16} {r['path']}")
                print(f"scan: {len(rows)} file(s); stale is not visible here (no content compared)")
            return 0
        if a.cmd == "selftest":
            return 0 if selftest(quick=a.quick) else 1
    except RegistryError as e:
        print(f"registry error: {e}")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
