#!/usr/bin/env python
"""paper-story consolidate_html — retire the scattered class-A HTML of existing runs in favour of ONE paper-explainer.html.

  python consolidate_html.py --home <PaperSurvey dir>                  DRY RUN (default): per run folder, which retired HTML exists and
                                                                       whether paper-explainer.html can be built from story.json / cards.json
  python consolidate_html.py --home <dir> --apply [--rebuild]          build the explainer where it is missing, then MOVE the retired HTML
                                                                       into <run>/archive/retired-html-20261103/ with a 說明.md note
  python consolidate_html.py --selftest                                two-sided calibration on a fixture library (incl. a real junction)

Why (user ruling 2026-11-03): the one-page, talk-deck and keypoint-onepager HTML are consolidated into ONE explainer page per paper
(the one-page, the figure walk and the talk script all live inside it). Nothing is deleted: a retired file is MOVED, a name that already
exists in the archive folder is never overwritten (reported instead), an existing paper-explainer.html is kept unless --rebuild is given
(it is rebuilt only to pick up the new 口述稿 section; the old one is then replaced by the carrier's own build, which stamps it).

A run folder = a directory holding story.json or cards.json (or one of the retired files). The walk never enters a junction or symlink
(rules/tree-walk-reparse.md): every pruned link is named in the report as `reparse-point <path> -> <target>`. A run folder's own
subfolders (source/, figures/, archive/ ...) are not walked: the retired files are looked for at its top level only.
A run folder with no retired HTML is not consolidated (no explainer is invented for it); with --rebuild an existing explainer of such a
run is refreshed. Exit 0 always for a dry run; with --apply exit 1 when a build or a move failed.
"""
import argparse
import datetime as dt
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[2] / "hooks" / "_lib"))
from tree import is_reparse  # noqa: E402  (hooks/_lib/tree.py — the one copy for tools that ship with hooks/_lib)

RETIRED = ("onepage.html", "talk-deck.html", "keypoint-onepager.html")
EXPLAINER = "paper-explainer.html"
ARCHIVE_DIR = "retired-html-20261103"


def find_runs(home: Path):
    """(run_dirs, pruned_links). Never enters a reparse point; stops descending at a run folder."""
    runs, pruned = [], []
    for dirpath, dirnames, _ in os.walk(home):
        d = Path(dirpath)
        keep = []
        for n in sorted(dirnames):
            p = d / n
            if is_reparse(p):
                try:
                    tgt = os.readlink(p)
                except OSError:
                    tgt = "?"
                pruned.append((p, tgt))
            else:
                keep.append(n)
        dirnames[:] = keep
        if (d / "story.json").is_file() or (d / "cards.json").is_file() or any((d / r).is_file() for r in RETIRED):
            runs.append(d)
            dirnames[:] = []   # a run's subfolders are its own business
    return runs, pruned


def buildable(run: Path):
    """(True, '') when the explainer content can be mapped from story.json (+ cards.json); (False, why) otherwise. Writes nothing."""
    if not (run / "story.json").is_file():
        return False, "no story.json (a distill-only run: the explainer maps story.json)"
    try:
        import story_explainer
        c = story_explainer.build_content(run)
    except Exception as e:   # an older schema may lack a key the mapping reads
        return False, f"{e.__class__.__name__}: {str(e)[:80]}"
    return (True, f"{len(c['sections'])} sections") if c.get("sections") else (False, "mapping produced no section")


def plan(run: Path):
    found = [r for r in RETIRED if (run / r).is_file()]
    ok, why = buildable(run)
    has = (run / EXPLAINER).is_file()
    return {"run": run, "retired": found, "explainer": has, "buildable": ok, "why": why}


def note_text(moved, run: Path):
    today = dt.date.today().isoformat()
    lines = ["# 退役的 HTML（2026-11-03 整併）", "",
             f"整併日期：{today}。依使用者裁定（2026-11-03），每篇論文的練習・複習用 HTML 只留一份 `paper-explainer.html`（說明頁）：",
             "論文一頁、逐圖判讀、口述稿都在這一頁裡，不再另外放一頁式、多頁式或精華一頁的 HTML。", "",
             "這個資料夾裡的檔案是被移來的舊產物，原樣保留、沒有刪除：", ""]
    lines += [f"- `{n}`" for n in moved]
    lines += ["", "要還原：把檔案搬回上一層（`" + run.name + "/`）即可。重新產生舊版頁面只能用 `render_story.py --legacy-html`，"
              "而且只適用舊 run。", ""]
    return "\n".join(lines)


def apply_one(p: dict, rebuild: bool):
    """Build (when missing, or --rebuild) then move. Returns (ok, [message lines])."""
    run, msgs, ok = p["run"], [], True
    if p["buildable"] and (rebuild or not p["explainer"]):
        import story_explainer
        rc = story_explainer.build(run)
        msgs.append(f"explainer {'rebuilt' if p['explainer'] else 'built'} (rc {rc})")
        ok &= rc == 0
    elif not p["explainer"]:
        # without an explainer the retired pages are the only HTML of this run: do not move them
        return False, [f"no explainer and not buildable ({p['why']}) — retired HTML left in place"]
    if not (run / EXPLAINER).is_file():
        return False, msgs + ["paper-explainer.html is still missing after the build — retired HTML left in place"]
    if not p["retired"]:
        return ok, msgs + ["no retired HTML to move"]
    dst = run / "archive" / ARCHIVE_DIR
    dst.mkdir(parents=True, exist_ok=True)
    moved = []
    for n in p["retired"]:
        if (dst / n).exists():
            msgs.append(f"{n}: already in {dst.name}/ — not overwritten, left in place"); ok = False
            continue
        shutil.move(str(run / n), str(dst / n)); moved.append(n)
    if moved:
        existing = sorted(x.name for x in dst.glob("*.html"))
        (dst / "說明.md").write_text(note_text(existing, run), encoding="utf-8")
        msgs.append(f"moved {moved} -> archive/{ARCHIVE_DIR}/ (+ 說明.md)")
    return ok, msgs


def selftest():
    """Two-sided: a run with retired HTML and no explainer is built and archived (positive); a run that has nothing retired, a run
    that cannot be built, and a run behind a REAL junction are left byte-identical (negative). The dry run writes nothing."""
    import contextlib
    import io
    import subprocess
    import tempfile
    import render_story
    import story_explainer  # noqa: F401  (imported before stdout is redirected: both modules reconfigure sys.stdout at import)
    td = Path(tempfile.mkdtemp(prefix="consolidate-selftest-"))
    home, outside = td / "home", td / "outside"
    home.mkdir(); outside.mkdir()
    sample = render_story.make_sample(td / "sample")
    for nm in ("A_needs_build", "B_clean"):
        shutil.copytree(sample, home / nm)
    for nm in ("onepage.html", "talk-deck.html"):
        (home / "A_needs_build" / nm).write_text("<html>retired</html>", encoding="utf-8")
    (home / "B_clean" / EXPLAINER).write_text("<html>kept</html>", encoding="utf-8")
    (home / "C_no_story").mkdir()
    (home / "C_no_story" / "cards.json").write_text("{}", encoding="utf-8")
    (home / "C_no_story" / "keypoint-onepager.html").write_text("<html>only html</html>", encoding="utf-8")
    shutil.copytree(sample, outside / "D_behind_link"); (outside / "D_behind_link" / "onepage.html").write_text("<html>outside</html>", encoding="utf-8")
    link_ok = subprocess.run(["cmd", "/c", "mklink", "/J", str(home / "_calibration"), str(outside)], capture_output=True).returncode == 0

    def snap(root):
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
    before_all, out_before = snap(home), snap(outside)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_dry = main(["--home", str(home)])
    dry = buf.getvalue()
    results = [("dry-run-writes-nothing", rc_dry == 0 and snap(home) == before_all and snap(outside) == out_before),
               ("dry-run-lists-retired", "onepage.html, talk-deck.html" in dry and "A_needs_build" in dry and "explainer MISSING" in dry),
               ("dry-run-flags-unbuildable", "cannot build (no story.json" in dry),
               ("dry-run-names-the-link", (not link_ok) or ("reparse-point" in dry and "_calibration" in dry and "D_behind_link" not in dry))]
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc_apply = main(["--home", str(home), "--apply"])
    a = home / "A_needs_build"
    results += [("apply-builds-explainer", (a / EXPLAINER).is_file()),
                ("apply-moves-retired", not (a / "onepage.html").exists() and (a / "archive" / ARCHIVE_DIR / "onepage.html").read_text(encoding="utf-8") == "<html>retired</html>"
                 and (a / "archive" / ARCHIVE_DIR / "talk-deck.html").is_file() and "onepage.html" in (a / "archive" / ARCHIVE_DIR / "說明.md").read_text(encoding="utf-8")),
                ("apply-keeps-clean-run", (home / "B_clean" / EXPLAINER).read_text(encoding="utf-8") == "<html>kept</html>" and not (home / "B_clean" / "archive").exists()),
                ("apply-leaves-unbuildable", (home / "C_no_story" / "keypoint-onepager.html").is_file() and not (home / "C_no_story" / "archive").exists() and rc_apply == 1),
                ("apply-never-enters-link", snap(outside) == out_before)]
    ok = True
    print("consolidate_html selftest — two-sided")
    for name, hit in results:
        ok &= bool(hit)
        print(f"  {'OK ' if hit else 'BAD'} {name}")
    if not ok:
        print("--- apply output ---\n" + buf2.getvalue()[-1800:])
    if not link_ok:
        print("  NOTE junction fixture not creatable on this machine: the pruning controls are uncalibrated")
        ok = False
    print("temp dir:", td)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--home", type=Path, help="the PaperSurvey library folder")
    ap.add_argument("--apply", action="store_true", help="build the missing explainers, then move the retired HTML (default: dry run)")
    ap.add_argument("--rebuild", action="store_true", help="with --apply: also rebuild an explainer that already exists")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.home:
        ap.error("--home <PaperSurvey dir> (or --selftest)")
    if not a.home.is_dir():
        print(f"no such folder: {a.home}", file=sys.stderr)
        return 2
    runs, pruned = find_runs(a.home)
    plans = [plan(r) for r in runs]
    print(f"consolidate_html — {'APPLY' if a.apply else 'DRY RUN'} — home {a.home} — {len(plans)} run folder(s)")
    for p in plans:
        rel = p["run"].relative_to(a.home) if p["run"] != a.home else Path(".")
        state = ("explainer present" if p["explainer"] else "explainer MISSING") + \
                (f"; can build ({p['why']})" if p["buildable"] else f"; cannot build ({p['why']})")
        print(f"  {str(rel):<95} retired: {', '.join(p['retired']) or '-':<32} {state}")
    for link, tgt in pruned:
        print(f"  reparse-point {link} -> {tgt}  (not entered)")
    n_ret = sum(len(p["retired"]) for p in plans)
    n_miss = sum(1 for p in plans if not p["explainer"])
    n_cant = sum(1 for p in plans if not p["explainer"] and not p["buildable"])
    print(f"summary: {n_ret} retired HTML file(s) in {sum(1 for p in plans if p['retired'])} run folder(s); "
          f"{n_miss} run(s) without paper-explainer.html, of which {n_cant} cannot be built; {len(pruned)} link(s) pruned")
    if not a.apply:
        print("dry run: nothing written. Re-run with --apply to build and move.")
        return 0
    bad = 0
    for p in plans:
        # a run with nothing retired is not consolidated (no explainer is invented for it); --rebuild only refreshes an existing one
        if not p["retired"] and not (a.rebuild and p["explainer"] and p["buildable"]):
            continue
        ok, msgs = apply_one(p, a.rebuild)
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {p['run'].relative_to(a.home) if p['run'] != a.home else '.'}: " + "; ".join(msgs))
    print("RESULT:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
