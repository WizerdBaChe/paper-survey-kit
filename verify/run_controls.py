"""Run the kit's machine acceptance controls (docs/BUILD-SPEC.md §7) on a scratch copy.

Usage (from the repo root):  python -X utf8 verify/run_controls.py <new-scratch-dir>

<new-scratch-dir> must not exist or must be empty; reference-impl/ and the example run are copied
there, mutated and deleted. Each two-sided control prints BOTH asserted values (correct vs mutant).
Evidence rung: 0 (example controls, each two-sided with both asserted values printed).
Needs: Python 3.12, PyMuPDF, python-pptx, Pillow, lxml, jsonschema, playwright + chromium, matplotlib, pytest.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN_NAME = "Placeholder2026_wax-delay-bridges"
if len(sys.argv) != 2:
    sys.exit(__doc__)
work = Path(sys.argv[1]).resolve()
if work.exists() and any(work.iterdir()):
    sys.exit(f"refusing: {work} exists and is not empty (it would be deleted)")
if work == REPO or REPO in work.parents or work in REPO.parents:
    sys.exit(f"refusing: {work} overlaps the repo {REPO}")

RI = work / "reference-impl"
LIB = work / "library"
ENV = dict(os.environ, HK_HOST_TOML=str(REPO / "verify" / "host.toml"), PAPER_DISTILL_HOME=str(LIB),
           PYTHONIOENCODING="utf-8")
results: list[tuple[str, bool]] = []


def run(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-X", "utf8", *args], cwd=cwd or work, env=ENV, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = p.stdout + p.stderr
    for form in (str(work), work.as_posix()):
        out = out.replace(form, "<scratch>")
    for form in (str(REPO), REPO.as_posix()):
        out = out.replace(form, "<repo>")
    return p.returncode, out


def report(cid: str, ok: bool, line: str) -> None:
    results.append((cid, ok))
    print(f"{cid:<4} {line} -> {'ok' if ok else 'MISMATCH'}")


def fresh_run() -> Path:
    run_dir = LIB / RUN_NAME
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(REPO / "examples" / "library" / RUN_NAME, run_dir)
    return run_dir


def fails(out: str) -> int:
    return len(re.findall(r"^\s*[A-Z]+\d+[a-z]?\s+FAIL\b", out, re.M))


def mutate_json(path: Path, keys: list, fn) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    node = data
    for k in keys[:-1]:
        node = node[k]
    node[keys[-1]] = fn(node[keys[-1]])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return "/".join(map(str, keys))


def versions() -> str:
    import platform
    from importlib.metadata import PackageNotFoundError, version
    out = [f"python {platform.python_version()}", f"{platform.system()} {platform.release()}"]
    for pkg in ("pymupdf", "python-pptx", "playwright", "jsonschema", "pytest"):
        try:
            out.append(f"{pkg} {version(pkg)}")
        except PackageNotFoundError:
            out.append(f"{pkg} absent")
    return ", ".join(out)


def main() -> int:
    print(f"env: {versions()}")
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO / "reference-impl", RI)
    PS, PD = RI / "skills" / "paper-story" / "scripts", RI / "skills" / "paper-distill" / "scripts"

    # K1-K5 selftests (each selftest carries its own known-good and known-bad inputs)
    for cid, args, want in (
        ("K1", [str(PS / "render_story.py"), "--selftest"], "SELFTEST PASS"),
        ("K2", [str(PS / "lab_deck.py"), "--selftest"], "SELFTEST PASS"),
        ("K3", [str(RI / "tools" / "carriers" / "build.py"), "selftest"], "selftest: ALL PASS"),
        ("K4", [str(RI / "tools" / "page-fill-gate" / "tests" / "test_fill_gate.py")], "test_fill_gate: PASS"),
        ("K5a", [str(PD / "glossary.py"), "--selftest"], "selftest OK"),
    ):
        rc, out = run(args)
        report(cid, rc == 0 and want in out, f"{Path(args[0]).name} {' '.join(args[1:])}: exit {rc}, '{want}' {'found' if want in out else 'absent'}")
    rc, out = run(["-m", "pytest", "-q", "-p", "no:cacheprovider", *sorted(str(p.name) for p in PD.glob("test_*.py"))], cwd=PD)
    tail = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)]
    report("K5b", rc == 0, f"paper-distill pytest: exit {rc}, {tail[-1].strip('= ') if tail else 'no summary'}")

    # K6 evidence audit of the shipped run: clean vs one claim quote altered
    run_dir = fresh_run()
    rc0, out0 = run([str(PD / "verify_run.py"), str(run_dir)])
    # V2 compares paper_says.conclusion_quote, the abstract head and craft sentence patterns with paper.txt
    keys = ["paper_says", "conclusion_quote"]
    where = mutate_json(run_dir / "cards.json", keys, lambda s: s + " ZZQX invented words")
    rc1, out1 = run([str(PD / "verify_run.py"), str(run_dir)])
    # verify_run rules a missing quote WARN, not FAIL (a PDF text layer can be incomplete), so the asserted
    # value is V2's status, not the FAIL count
    v2s = lambda o: (re.search(r"^\s*V2\s+(PASS|WARN|FAIL|SKIP)\b", o, re.M) or [None, "absent"])[1]
    report("K6", fails(out0) == 0 and v2s(out0) == "PASS" and v2s(out1) == "WARN" and "not found verbatim" in out1,
           f"verify_run: shipped V2 {v2s(out0)}, FAIL lines {fails(out0)} (exit {rc0}) vs quote altered at {where} V2 {v2s(out1)} (exit {rc1})")

    # K7 story gates of the shipped run: clean vs an emptied why vs an altered drift quote
    run_dir = fresh_run()
    rc0, out0 = run([str(PS / "verify_story.py"), str(run_dir)])
    mutate_json(run_dir / "story.json", ["axis", "entry_point", "why"], lambda s: "")
    rc1, out1 = run([str(PS / "verify_story.py"), str(run_dir)])
    run_dir = fresh_run()
    story = json.loads((run_dir / "story.json").read_text(encoding="utf-8"))
    qi = next(i for i, d in enumerate(story["drift"]) if d.get("quote"))
    mutate_json(run_dir / "story.json", ["drift", qi, "quote"], lambda s: s + " ZZQX")
    rc2, out2 = run([str(PS / "verify_story.py"), str(run_dir)])
    v2 = lambda o: bool(re.search(r"^V2\s+FAIL", o, re.M))
    v11 = lambda o: bool(re.search(r"^V11\s+FAIL", o, re.M))
    report("K7a", rc0 == 0 and rc1 == 2 and not v2(out0) and v2(out1),
           f"verify_story: shipped exit {rc0}, V2 FAIL {v2(out0)} vs entry_point.why emptied exit {rc1}, V2 FAIL {v2(out1)}")
    report("K7b", rc0 == 0 and rc2 == 2 and not v11(out0) and v11(out2),
           f"verify_story: shipped V11 FAIL {v11(out0)} vs drift[{qi}].quote altered exit {rc2}, V11 FAIL {v11(out2)}")

    # K8 the fictional paper regenerates with the same text layer
    import fitz  # PyMuPDF
    gen = work / "paper"
    shutil.copytree(REPO / "examples" / "fictional-paper", gen, ignore=shutil.ignore_patterns("*.pdf", "figs"))
    rc, out = run([str(gen / "make_paper.py")])

    def text_sha(pdf: Path) -> str:
        with fitz.open(pdf) as d:
            return hashlib.sha256("".join(p.get_text() for p in d).encode("utf-8")).hexdigest()[:16]
    a, b = text_sha(REPO / "examples" / "fictional-paper" / "paper.pdf"), text_sha(gen / "paper.pdf") if rc == 0 else "missing"
    report("K8", a == b, f"make_paper.py text-layer sha256: shipped {a} vs regenerated {b}")

    shutil.rmtree(work)
    bad = [c for c, ok in results if not ok]
    print(f"controls: {len(results) - len(bad)} of {len(results)} ok" + (f"; MISMATCH: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
