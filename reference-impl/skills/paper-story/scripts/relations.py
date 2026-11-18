"""People / group / paper relations for paper-story, read from tools/research-graph (proposal 十合一正式版收斂 R1/R3,
user ruling 2026-11-18: 「說明頁的一切都保留甚至擴充（…人物關聯+論文關係資料庫…）」).

One reader for every consumer (story_explainer 人物與關聯 section, lab_deck header group line, Relations slides), so the
three never disagree. research-graph is called through its CLI (`rg.py --json paper|relate`), the tool's public interface.

Every lookup returns a dict with `status`:
  ok           the graph holds the work; `data` is the rg output
  absent       no DOI in story.json, or the work is not in the corpus — consumers print 「庫內無資料」, never drop the block
  unavailable  rg.py failed (graph not built, tool missing, PAPER_STORY_RG=off) — printed the same way, with the reason
Groups are rule-inferred (research-graph README, Group): a consumer always labels them inferred / 推定.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

RG = Path(__file__).resolve().parents[3] / "tools" / "research-graph" / "rg.py"
_CACHE: dict = {}
# Replaceable in selftests: (verb, query) -> (returncode, stdout). The default runs the real CLI.
RUNNER = None


def _run(verb: str, q: str):
    if RUNNER is not None:
        return RUNNER(verb, q)
    if os.environ.get("PAPER_STORY_RG", "").lower() == "off":
        return 9, ""
    if not RG.is_file():
        return 8, ""
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(RG), "--json", verb, q],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 7, ""
    return r.returncode, r.stdout


def _rg(verb: str, q: str) -> dict:
    key = (verb, q, RUNNER)
    if key in _CACHE:
        return _CACHE[key]
    code, out = _run(verb, q)
    try:
        data = json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        data = {}
    if data.get("error") == "work not in corpus":
        res = {"status": "absent", "reason": "not in corpus", "corpus": data.get("corpus", "")}
    elif code != 0 or not data or data.get("error"):
        reason = {9: "PAPER_STORY_RG=off", 8: "research-graph not installed", 7: "research-graph call failed"}.get(
            code, data.get("error") or f"rg.py exit {code}")
        res = {"status": "unavailable", "reason": reason}
    else:
        res = {"status": "ok", "data": data, "corpus": data.get("corpus", "")}
    _CACHE[key] = res
    return res


def doi_of(story: dict) -> str:
    return ((story.get("source") or {}).get("doi") or "").strip()


def paper_of(story: dict) -> dict:
    d = doi_of(story)
    if not d:
        return {"status": "absent", "reason": "no DOI in story.json"}
    return _rg("paper", d)


def relate(dois: list[str]) -> dict:
    dois = [d for d in dict.fromkeys(x.strip() for x in dois) if d]
    if len(dois) < 2:
        return {"status": "absent", "reason": "fewer than two DOIs"}
    return _rg("relate", ",".join(dois))


YEARS_RE = re.compile(r"\s*\(\d{4}[–-]\d{4}\)\s*$")


def group_short(label: str) -> str:
    """'Ada Lin group @ Test University (2020–2020)' -> 'Ada Lin group @ Test University'."""
    return YEARS_RE.sub("", label or "").strip()


def group_line(story: dict, rel: dict | None = None) -> tuple[str, str]:
    """(text, origin) for the header group: the presenter's own en.group / source.group wins ('stated'); else the corresponding
    author's inferred research-graph group ('inferred'); else ('', 'none')."""
    stated = ((story.get("en") or {}).get("group") or (story.get("source") or {}).get("group") or "").strip()
    if stated:
        return stated, "stated"
    rel = rel if rel is not None else paper_of(story)
    if rel.get("status") == "ok":
        gs = rel["data"].get("groups") or []
        pick = next((g for g in gs if g.get("lead_is_corresponding")), gs[0] if gs else None)
        if pick:
            return group_short(pick["label"]), "inferred"
    return "", "none"


def byline(story: dict) -> str:
    """First author et al. (the advisor's database line asks for the author; the full list stays in the explainer)."""
    au = (story.get("source") or {}).get("authors") or []
    if not au:
        return ""
    a = au[0].strip()
    surname = a.split(",")[0].strip() if "," in a else (a.split()[-1] if a.split() else a)   # 'Lin, A.' / 'Ada Lin' -> 'Lin'
    return surname + (" et al." if len(au) > 1 else "")


def library_dois(run_dir: Path) -> dict[str, str]:
    """{doi: run folder name} of the sibling runs in the same library (PaperSurvey home): the explainer relates a paper to
    every paper already read, so a ten-paper set's members find each other without a set declaration. Only depth-1 folders
    without a leading underscore (calibration / templates are not the library); no reparse point is entered."""
    out = {}
    home = run_dir.resolve().parent
    for d in sorted(home.iterdir()):
        try:
            if not d.is_dir() or d.name.startswith(("_", ".")) or d.is_symlink() or (getattr(os.lstat(d), "st_file_attributes", 0) & 0x400):
                continue
        except (OSError, AttributeError):
            continue
        f = d / "story.json"
        if d.resolve() == run_dir.resolve() or not f.is_file():
            continue
        try:
            doi = doi_of(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
        if doi:
            out[doi] = d.name
    return out


def norm(doi: str) -> str:
    d = (doi or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d if d.startswith("doi:") else "doi:" + d


LINK_ZH = {"shared_author": "共同作者", "same_group": "同一團隊（推定）", "cites": "引用", "coupled": "書目耦合（引用相同文獻）",
           "co_cited": "共被引（常被一起引用）", "predecessor": "前作（同作者群的較早論文）", "concept_relation": "概念關係",
           "near_group": "接近的團隊"}
LINK_EN = {"shared_author": "shared author", "same_group": "same group (inferred)", "cites": "cites", "coupled": "bibliographic coupling",
           "co_cited": "co-cited", "predecessor": "predecessor", "concept_relation": "concept relation"}
