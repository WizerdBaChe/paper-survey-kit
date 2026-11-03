#!/usr/bin/env python
"""paper-distill crop_all — every figure and table caption of a run through crop.py (ink mode), with a backup.

Why (Retort & Rove card WC-06, 2026-09-27): runs cropped before the ink crop and the border-ink gate (crop.py since
2026-09-26) fail that gate on most figures, and units.py needs every crop's rect to tell figure-internal text from
body text. This re-cuts them all the same mechanical way and records each verdict; it never tunes a crop by hand.

Targets: for each figures.json caption, the first caption of a (kind, num) -> figures/F<num>.png or T<num>.png; a
later caption with the same (kind, num) on another page (a continued table, "Table 2. Cont.") -> <name>_p<page>.png.
Any other file in figures/ (paper-story variants such as F3a.png, F9F11.png, deck/; other names such as S1.png) is
never touched.

Not a target (listed under "skipped" in --plan, so the same figure is not cropped twice; Kumar 2022 preprint, which
lists its captions first and repeats a label-only line above each figure, 2026-11-03):
  stub   a caption that is only a label ("Figure 2:") while another caption of the same (kind, num) carries text; the
         figure is cropped under that one (crop.py finds it on the following page)
  panel  a later panel caption ("Figure 1(b): ...") on the page of an already targeted caption of the same figure

A run with source_kind text|jats has no PDF (ingest.py --text / --jats): nothing is cropped, a message says so, exit 0.
The reader views the publisher figure or the JATS graphic link instead; figures.json still lists label + caption.

  --plan (default)  print what would be moved and written; write nothing
  --apply           move each existing target file into figures/_previous/<tag>/ (stop, moving nothing, if a file
                    of that name is already there), run crop.py per target, write source/crops.json
                    (schema paper-distill/crops@1: crop.py's own JSON and exit code per target). A gate FAIL (exit 3)
                    keeps its file; UNDET (exit 2) and errors are recorded; nothing is retried with manual flags.
Usage:
  python crop_all.py --run <run_dir> [--apply] [--tag YYYY-MM-DD]
  python crop_all.py --accepted <PaperSurvey home> [--apply] [--tag YYYY-MM-DD]
Exit: 0 done (verdicts are in crops.json, not in the exit code); 1 a backup name collision or a missing input.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CROP = Path(__file__).resolve().parent / "crop.py"
SCHEMA = "paper-distill/crops@1"
TEXTLIKE = ("text", "jats")   # source_kind values of a run with no PDF (ingest.py --text / --jats)
LABEL = r"(?:fig\.?|figure|table|scheme)\s*S?\d+"
STUB = re.compile(r"^" + LABEL + r"(?:\s?\([a-z]\))?\s*[.:|\-–—]?\s*$", re.I)   # a caption that is only its label
PANEL = re.compile(r"^" + LABEL + r"\s?\([a-z]\)", re.I)                          # a caption of one panel: "Figure 1(b): ..."


def source_kind(run):
    """pdf | text | jats | url: _meta.json source_kind, else figures.json source_kind, else pdf (runs made before
    ingest.py wrote it). Shared by units.py and verify_run.py so the three scripts read one answer."""
    for name in ("_meta.json", "source/figures.json"):
        p = Path(run) / name
        if p.is_file():
            try:
                k = json.loads(p.read_text(encoding="utf-8")).get("source_kind")
            except (OSError, ValueError):
                k = None
            if k:
                return k
    return "pdf"


def unit_resolves(unit, line_text):
    """True when a structure.json unit's `line` of paper.txt holds the unit: a section/subsection when the line
    contains its title (or is the heading textsrc reads that title from: 'A B S T R A C T' -> Abstract), a figure or
    table when the line starts its caption. Shared by units.py and verify_run.py (text/JATS runs)."""
    import textsrc  # stdlib only, beside this file
    fold = lambda s: re.sub(r"[\W_]+", "", (s or "").casefold())
    text, line = fold(unit.get("text")), fold(line_text)
    if unit.get("kind") in ("figure", "table"):
        n = min(len(text), len(line), 24)
        return n > 0 and text[:n] == line[:n]
    h = textsrc.heading_of(line_text or "")
    return bool(text) and (text in line or (h is not None and fold(h[1]) == text))


def is_stub(caption):
    return bool(STUB.match(" ".join((caption.get("caption") or "").split())))


def targets(captions, skipped=None):
    """Crop targets of a caption list. A caption that is not a target is appended to `skipped` (if given) as
    {caption_index, label, page, why}."""
    seen, names, out = set(), set(), []
    full = {(c.get("kind"), c.get("num")) for c in captions if not is_stub(c)}
    targeted_pages = set()
    for i, c in enumerate(captions):
        kind, num = c.get("kind"), c.get("num")
        if kind not in ("figure", "table") or num is None:
            continue
        why = None
        if is_stub(c) and (kind, num) in full:
            why = "stub: label-only caption; the figure is cropped under the caption of the same label that has text"
        elif PANEL.match(" ".join((c.get("caption") or "").split())) and (kind, num, c.get("page")) in targeted_pages:
            why = "panel: another caption of the same figure on this page is already a target"
        if why:
            if skipped is not None:
                skipped.append({"caption_index": i, "label": c.get("label"), "page": c.get("page"), "why": why})
            continue
        targeted_pages.add((kind, num, c.get("page")))
        base = ("T" if kind == "table" else "F") + str(num)
        name = base if (kind, num) not in seen else f"{base}_p{c.get('page')}"
        k = 2
        while name in names:
            name = f"{base}_p{c.get('page')}-{k}"
            k += 1
        seen.add((kind, num))
        names.add(name)
        out.append({"caption_index": i, "label": c.get("label"), "kind": kind, "num": num, "page": c.get("page"),
                    "name": name, "file": f"figures/{name}.png"})
    return out


def plan(run, tag):
    figs = run / "source" / "figures.json"
    if not figs.is_file():
        return None, f"no {figs}"
    skipped = []
    ts = targets(json.loads(figs.read_text(encoding="utf-8")).get("captions", []), skipped)
    backup = run / "figures" / "_previous" / tag
    moves = [(run / t["file"], backup / f"{t['name']}.png") for t in ts if (run / t["file"]).is_file()]
    clash = [str(d) for _, d in moves if d.exists()]
    return {"targets": ts, "moves": moves, "backup": backup, "clash": clash, "skipped": skipped}, None


def textlike_note(run, kind):
    """The message of a run that has no PDF: figures are listed in figures.json, not cropped."""
    figs = run / "source" / "figures.json"
    try:
        caps = json.loads(figs.read_text(encoding="utf-8")).get("captions", []) if figs.is_file() else []
    except (OSError, ValueError):
        caps = []
    return {"run": run.name, "skipped": True, "source_kind": kind,
            "reason": f"source_kind {kind}: no PDF, so nothing is cropped; figures.json lists label + caption only. "
                      "The reader views the publisher figure or the JATS graphic link instead "
                      "(an unseen figure makes no claim about what it shows).",
            "figures_listed": [c.get("label") for c in caps]}


def apply(run, p, tag):
    p["backup"].mkdir(parents=True, exist_ok=True)
    for src, dst in p["moves"]:
        shutil.move(str(src), str(dst))
    results = []
    for t in p["targets"]:
        cp = subprocess.run([sys.executable, "-X", "utf8", str(CROP), "--run", str(run), "--caption", t["label"],
                             "--page", str(t["page"]), "--out", t["file"]],
                            capture_output=True, text=True, encoding="utf-8")
        rec = {**t, "exit": cp.returncode, "result": None}
        lines = cp.stdout.strip().splitlines()
        try:
            rec["result"] = json.loads(lines[-1]) if lines else None
        except json.JSONDecodeError:
            rec["stdout"] = cp.stdout[-500:]
        if cp.returncode not in (0, 2, 3):
            rec["error"] = cp.stderr.strip()[-800:]
        results.append(rec)
    out = {"schema": SCHEMA, "tag": tag, "crop_py": str(CROP.name), "moved": [d.name for _, d in p["moves"]],
           "results": results}
    (run / "source" / "crops.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def verdict(rec):
    if rec.get("exit") not in (0, 2, 3):
        return "ERROR"
    return ((rec.get("result") or {}).get("gate") or {}).get("verdict", "UNDET")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--accepted", type=Path, help="PaperSurvey home: every index.json entry with kind == accepted")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--tag", default=datetime.date.today().isoformat(), help="backup folder name under figures/_previous/")
    a = ap.parse_args(argv)
    if a.accepted:
        index = json.loads((a.accepted / "index.json").read_text(encoding="utf-8"))
        runs = [a.accepted / e["run_id"] for e in index.get("entries", []) if e.get("kind") == "accepted"]
    elif a.run:
        runs = [a.run]
    else:
        ap.error("give --run or --accepted")
    plans = {}
    for run in runs:
        kind = source_kind(run)
        if kind in TEXTLIKE:
            print(json.dumps(textlike_note(run, kind), ensure_ascii=False))
            continue
        p, err = plan(run, a.tag)
        if err:
            print(json.dumps({"run": run.name, "error": err}, ensure_ascii=False))
            return 1
        if p["clash"]:
            print(json.dumps({"run": run.name, "error": "backup name already taken; nothing moved", "clash": p["clash"]},
                             ensure_ascii=False))
            return 1
        plans[run] = p
    for run, p in plans.items():
        if not a.apply:
            line = {"run": run.name, "plan": True, "targets": [t["name"] for t in p["targets"]],
                    "move": [f"{s.relative_to(run).as_posix()} -> {d.relative_to(run).as_posix()}" for s, d in p["moves"]]}
            if p["skipped"]:
                line["skipped"] = p["skipped"]
            print(json.dumps(line, ensure_ascii=False))
            continue
        before = {f.name for f in (run / "figures").iterdir() if f.is_file()}
        out = apply(run, p, a.tag)
        backed = sorted(f.name for f in p["backup"].iterdir() if f.is_file())
        v = Counter(verdict(r) for r in out["results"])
        after = {f.name for f in (run / "figures").iterdir() if f.is_file()}
        line = {"run": run.name, "targets": len(out["results"]), "verdicts": dict(sorted(v.items())),
                "moved": len(out["moved"]), "backup_files": len(backed),
                "backup_complete": set(out["moved"]) <= set(backed),
                "untouched": sorted(before - {f"{t['name']}.png" for t in p["targets"]})[:40],
                "new_names": sorted(after - before)}
        if p["skipped"]:
            line["skipped"] = [f"{s['label']}@p{s['page']}" for s in p["skipped"]]
        print(json.dumps(line, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
