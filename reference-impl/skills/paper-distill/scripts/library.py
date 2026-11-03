#!/usr/bin/env python
"""paper-distill library — the persistent, searchable index of runs, and the human-facing layout.

  python library.py [--home DIR] init
  python library.py [--home DIR] register <run_dir> [--kind accepted|calibration] [--label L]
                                                       upsert from cards.json (+ story.json), rebuild README / KEYPOINTS / keypoint notes
  python library.py [--home DIR] list
  python library.py [--home DIR] find <term>            NFKC-folded substring over title/keypoint/tags/author/patterns
  python library.py [--home DIR] readme                 rebuild README.md, KEYPOINTS.md and every accepted run's keypoint note
  python library.py [--home DIR] migrate --plan plan.json [--apply]
                                                       move folders per plan, rewrite ids everywhere, re-register (dry-run by default)

LAYOUT (naming over routing — user ruling 2026-09-04; before it every run was a dated sibling and the README said
「共 9 篇」 for 3 papers):

  <home>/<PaperId>/                     ONE accepted run per paper; PaperId = <FirstAuthor><Year>_<short-title-slug>
  <home>/_calibration/<PaperId>/<label>/ comparison / calibration copies (run.id = <PaperId>__<label>), never siblings
  <home>/README.md                      one row per paper (+ a 校準紀錄 section); regenerated from the layout
  <home>/KEYPOINTS.md                   論文核心邏輯快速關聯索引: every accepted paper's slogan + reading + logic patterns,
                                        wikilinks to each paper's keypoint note; grouped by pattern (Obsidian graph/tag view)
  <home>/<PaperId>/<PaperId>_keypoint.md  per-paper keypoint note (kind: literature): slogan, 解讀, role table, patterns as
                                        tags, relations as wikilinks — generated from story.json, never hand-edited

Persistence is the part of Template 3 (IG DcvzXtiEdIe) worth keeping: tagged, linked, versioned, searchable. Search folds
NFKC + casefold (variant-recall rule: fold the rule, never enumerate spellings).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
import sys as _hksys  # machine roots at run time (platform/codemod_roots.py, build plan H-1)
from pathlib import Path as _HKPath
_hksys.path.insert(0, str(_HKPath(__file__).resolve().parents[3] / "hooks" / "_lib"))
import roots as hkroots  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_home = os.environ.get("PAPER_DISTILL_HOME") or hkroots.expand("${NOTES_VAULT}/literature/PaperSurvey")
DEFAULT_HOME = Path(_home) if _home else None  # None: pass --home (NOTES_VAULT unset)
CALIB = "_calibration"
TEXT_EXT = (".json", ".md", ".txt")
# paper-explainer.html is the ONE class-A page per paper since 2026-11-03 (user ruling: the scattered one-page / multi-page / talk-deck
# HTML are consolidated into it); the retired names stay listed so an older run that still holds them is recorded as it is.
PRODUCT_FILES = ("reading-record.md", "narrative-record.md", "paper-explainer.html", "onepage.html", "talk-deck.html", "talk-script.md",
                 "lab-deck.pptx", "lab-onepage.pptx", "story.json", "cards.json")


def fold(s):
    return unicodedata.normalize("NFKC", s or "").casefold()


def first_sentence(s, n=2):
    parts = [p for p in re.split(r"(?<=[。！？])", (s or "").replace("\n", "")) if p.strip()]
    return "".join(parts[:n])


def load_index(home: Path):
    idx = home / "index.json"
    if not idx.exists():
        home.mkdir(parents=True, exist_ok=True)
        idx.write_text(json.dumps({"schema": "paper-distill/index@2", "home": str(home), "entries": []},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    data = json.loads(idx.read_text(encoding="utf-8"))
    data["schema"] = "paper-distill/index@2"
    return data


def save_index(home: Path, data):
    (home / "index.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def kind_of(run_dir: Path, home: Path):
    try:
        rel = run_dir.resolve().relative_to(home.resolve())
    except ValueError:
        return "accepted", "", run_dir.name
    parts = rel.parts
    if parts and parts[0] == CALIB and len(parts) >= 3:
        return "calibration", parts[2], parts[1]
    return "accepted", "", parts[0] if parts else run_dir.name


def entry_from_cards(run_dir: Path, cards, home: Path, kind=None, label=None):
    src = cards.get("source", {})
    story_p = run_dir / "story.json"
    st, story_id = {}, ""
    if story_p.exists():
        try:
            st = json.loads(story_p.read_text(encoding="utf-8"))
            story_id = st.get("run", {}).get("id", "") or ""
        except Exception:
            st = {}
    lg = st.get("logic", {}) if st else {}
    kp_title = lg.get("keypoint", "") or (cards.get("keypoint") or {}).get("title", "")
    claims = cards.get("claims") or [{}]
    authors = src.get("authors") or []
    k, lab, paper = kind_of(run_dir, home)
    kind = kind or k
    label = label or lab
    # 2026-09-03 bridge: the index carries BOTH ids; a story run in a copied folder registers under its own id with
    # distill_run pointing at the shared deep-read; nothing is written back into cards.json.
    return {
        "run_id": story_id or cards["run"]["id"], "distill_run": cards["run"]["id"], "story_run": story_id,
        "paper": paper, "kind": kind, "label": label,
        "path": str(run_dir), "mode": (st.get("run", {}) or {}).get("mode", "") if st else "",
        "story_schema": st.get("schema", "") if st else "", "model": (st.get("run", {}) or {}).get("model", "") if st else "",
        "products": [f for f in PRODUCT_FILES if (run_dir / f).exists()],
        "title": src.get("title", ""), "first_author": authors[0] if authors else "",
        "year": src.get("year"), "venue": src.get("venue", ""), "doi": src.get("doi", ""),
        "source_type": src.get("type", ""), "depth": cards["run"].get("depth", ""),
        "created": cards["run"].get("created", ""), "revision": cards["run"].get("revision", 1),
        "keypoint_title": kp_title, "keypoint_reading": first_sentence(lg.get("keypoint_description", "")),
        "patterns": lg.get("patterns") or [], "relations": lg.get("relations") or [],
        "c1_verdict": claims[0].get("verdict", ""),
        "domain_profile": cards.get("intake", {}).get("domain_profile", ""),
        "tags": sorted({t for t in [cards.get("intake", {}).get("domain_profile", ""), src.get("type", "")] if t}),
        "related": [], "registered": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def card(what, tags, aliases, kind, source, extra=None):
    lines = ["---", "xi: 1", "what: " + json.dumps(what, ensure_ascii=False), "tags: [" + ", ".join(tags) + "]",
             "aliases: [" + ", ".join(json.dumps(a, ensure_ascii=False) for a in aliases) + "]",
             f"date: {dt.date.today().isoformat()}", "status: live", f"kind: {kind}", "source: " + json.dumps(source, ensure_ascii=False),
             f"verified: \"generated {dt.date.today().isoformat()} by paper-distill library.py\"",
             "review-when: \"story.json of any accepted run changes (re-run library.py readme)\"", "domain: []", "promoted-to: \"-\""]
    lines += extra or []
    return "\n".join(lines + ["---", ""])


def keypoint_note_name(paper):
    return f"{paper}_keypoint.md"


def upgrade_entry(e):
    """index@1 entries (before 2026-09-04) lack paper / kind / label — derive them so a mixed index still renders."""
    e.setdefault("paper", e.get("run_id", "?"))
    e.setdefault("kind", "accepted")
    e.setdefault("label", "")
    e.setdefault("products", [])
    e.setdefault("patterns", [])
    e.setdefault("relations", [])
    e.setdefault("keypoint_reading", "")
    return e


def write_keypoint_note(home: Path, e, by_paper):
    """Per-paper keypoint note — the Obsidian 論文核心邏輯快速關聯索引 leaf (user request 2026-09-04)."""
    run_dir = Path(e["path"])
    sp = run_dir / "story.json"
    if not sp.exists():
        return None
    st = json.loads(sp.read_text(encoding="utf-8"))
    lg, src = st.get("logic", {}), st.get("source", {})
    paper = e["paper"]
    tags = ["paper-story", "keypoint", "literature"] + [f"logic/{p}" for p in (lg.get("patterns") or [])]
    aliases = [f"{paper} keypoint", f"{src.get('title','')[:70]} 核心邏輯", f"{(src.get('authors') or ['?'])[0].split()[-1]} {src.get('year','')} 核心邏輯"]
    what = f"{src.get('title','')} — 核心邏輯（slogan＋讀書心得詮釋＋角色表）；由 story.json 生成，是論文核心邏輯關聯索引的葉節點 (keypoint note generated from story.json)"
    body = [f"# 核心邏輯：{src.get('title','')}", "",
            f"> {(src.get('authors') or ['?'])[0]} et al. · {src.get('year','')} · {src.get('venue','')} · run `{e['run_id']}` · 由 `library.py` 生成，改 story.json 再重生，不要手改。", "",
            "## Slogan", "", f"**{lg.get('keypoint','')}**", "",
            "## 解讀（讀書心得的終極詮釋）", ""] + [p.strip() for p in re.split(r"\n\s*\n|\n", lg.get("keypoint_description", "")) if p.strip()] + ["",
            "## slogan 裡的角色 ＝ 在這篇", "", "| 角色 | 在這篇＝ | 出處 |", "|---|---|---|"]
    body += [f"| {b.get('role','')} | {b.get('referent','')} | {b.get('locator','')} |" for b in lg.get("bindings") or []]
    body += ["", "## 邏輯型（tags）", "", " ".join(f"#logic/{p}" for p in (lg.get("patterns") or [])) or "（未標）", ""]
    same = {}
    for p in lg.get("patterns") or []:
        for other in by_paper.values():
            if other["paper"] != paper and p in (other.get("patterns") or []):
                same.setdefault(other["paper"], set()).add(p)
    body += ["## 相關論文", ""]
    for r in lg.get("relations") or []:
        tgt = by_paper.get(r.get("run", ""), {}).get("paper") or r.get("run", "")
        body += [f"- [[{keypoint_note_name(tgt)[:-3]}|{tgt}]]：{r.get('why','')}"]
    for other, ps in sorted(same.items()):
        body += [f"- [[{keypoint_note_name(other)[:-3]}|{other}]]：共用邏輯型 {', '.join(sorted(ps))}"]
    if not (lg.get("relations") or same):
        body += ["- （尚無）"]
    body += ["", "## 檔案", "",
             f"- [[{paper}/narrative-record|敘事紀錄]] · [[{paper}/reading-record|學習紀錄]] · [說明頁]({paper}/paper-explainer.html)（`paper-explainer.html`：一頁、逐圖判讀與口述稿都在裡面）",
             f"- 最脆弱的一環：{(lg.get('fragile') or {}).get('what','')}",
             f"- 可移植到：{(lg.get('portable') or {}).get('where','')}", "", "相關：[[KEYPOINTS]] · [[home]]", ""]
    out = run_dir / keypoint_note_name(paper)
    out.write_text(card(what, tags, aliases, "literature", f"file: {paper}/story.json") + "\n".join(body), encoding="utf-8")
    return out


def write_keypoints_index(home: Path, data):
    acc = sorted([e for e in data["entries"] if e.get("kind", "accepted") == "accepted" and e.get("keypoint_title")], key=lambda e: (e.get("year") or 0, e["paper"]))
    lines = [card("PaperSurvey 論文核心邏輯快速關聯索引——每篇一段：slogan、讀書心得詮釋首句、邏輯型、相關論文；按邏輯型分組 (index of every accepted paper's construction logic, grouped by pattern)",
                  ["paper-story", "keypoints", "topic-map", "index"], ["論文核心邏輯索引", "核心邏輯關聯索引", "keypoints index", "PaperSurvey KEYPOINTS"], "topic-map", "paper-distill library.py readme"),
             "# PaperSurvey — 論文核心邏輯快速關聯索引", "",
             f"由 `library.py` 從每篇正本的 `story.json` 生成（{dt.date.today().isoformat()}），共 {len(acc)} 篇。每篇的 slogan 是抽象的建構規則；點進去的 keypoint 筆記有讀書心得詮釋與「角色＝在這篇」表。圖譜視圖裡，共用邏輯型或明寫相關的論文互相連線。", ""]
    lines += ["## 每篇一段", ""]
    for e in acc:
        note = keypoint_note_name(e["paper"])[:-3]
        lines += [f"### [[{note}|{e['paper']}]] · {e.get('year','')} · {e.get('title','')}", "",
                  f"- **Slogan**：{e['keypoint_title']}",
                  f"- **解讀首句**：{e.get('keypoint_reading','') or '（未填）'}",
                  f"- **邏輯型**：{' '.join('#logic/' + p for p in e.get('patterns') or []) or '（未標）'}",
                  f"- **深讀判定 C1**：{e.get('c1_verdict','')}", ""]
    pats = {}
    for e in acc:
        for p in e.get("patterns") or []:
            pats.setdefault(p, []).append(e)
    lines += ["## 按邏輯型分組", ""]
    for p, es in sorted(pats.items()):
        lines += [f"- `#logic/{p}`：" + "、".join(f"[[{keypoint_note_name(x['paper'])[:-3]}|{x['paper']}]]" for x in es)]
    if not pats:
        lines += ["- （尚無邏輯型標記）"]
    lines += ["", "## 明寫的相關", ""]
    by_id = {e["run_id"]: e for e in data["entries"]}
    n = 0
    for e in acc:
        for r in e.get("relations") or []:
            tgt = by_id.get(r.get("run", ""), {}).get("paper") or r.get("run", "")
            lines += [f"- {e['paper']} → {tgt}：{r.get('why','')}"]; n += 1
    if not n:
        lines += ["- （尚無）"]
    lines += ["", "相關：[[README]] · [[home]]", ""]
    (home / "KEYPOINTS.md").write_text("\n".join(lines), encoding="utf-8")


def write_readme(home: Path, data):
    acc = sorted([e for e in data["entries"] if e.get("kind", "accepted") == "accepted"], key=lambda e: (-(e.get("year") or 0), e["paper"]))
    cal = sorted([e for e in data["entries"] if e.get("kind") == "calibration"], key=lambda e: (e["paper"], e.get("label", "")))
    lines = [card("PaperSurvey 論文庫索引——一篇論文一列（正本）：slogan、深讀判定、產物；校準副本另列一節 (library index: one row per paper, calibration copies in their own section)",
                  ["paper-distill", "library", "index", "topic-map"], ["論文庫", "讀過的論文", "paper library", "PaperSurvey index"], "topic-map", "paper-distill library.py register"),
             "# PaperSurvey — 文獻庫", "",
             f"由 `library.py register` 重建（{dt.date.today().isoformat()}）；正本 {len(acc)} 篇，校準副本 {len(cal)} 份。搜尋：`python library.py find <詞>`。核心邏輯索引：[[KEYPOINTS]]。", "",
             "資料夾＝一篇論文（`<第一作者><年>_<短標題>`），裡面只有這篇的正本 run；比較／校準用的副本在 `_calibration/<論文>/<標籤>/`。每篇的人讀檔：`reading-record.md`（學習紀錄：閱讀分析過程）、`narrative-record.md`（敘事紀錄：主軸／故事線／邏輯抽取）、`<論文>_keypoint.md`（核心邏輯：slogan＋解讀＋角色表）、`paper-explainer.html`（說明頁：練習・複習用，不是上台稿；論文一頁、逐圖判讀、口述稿都在這一頁裡）；正式簡報＝實驗室 pptx 範本改英文（`lab-deck.pptx`，明確要求時才做）。", "",
             "## 正本（一篇一列）", "",
             "| 論文 | 年 | 標題 | Slogan（核心邏輯） | 深讀判定 C1 | 檔案 |", "|---|---|---|---|---|---|"]
    for e in acc:
        p = e["paper"]
        files = " · ".join(x for x in [
            f"[[{p}/reading-record|學習]]" if "reading-record.md" in e.get("products", []) else "",
            f"[[{p}/narrative-record|敘事]]" if "narrative-record.md" in e.get("products", []) else "",
            f"[[{keypoint_note_name(p)[:-3]}|核心邏輯]]" if (Path(e["path"]) / keypoint_note_name(p)).exists() else "",
            f"[說明頁]({p}/paper-explainer.html)" if (Path(e["path"]) / "paper-explainer.html").exists() or "paper-explainer.html" in e.get("products", []) else "",
            "正式pptx" if any(x.startswith("lab-") for x in e.get("products", [])) else ""] if x)
        lines.append(f"| `{p}` | {e.get('year') or ''} | {e.get('title','')} | {e.get('keypoint_title','')} | {e.get('c1_verdict','')} | {files} |")
    lines += ["", "## 校準紀錄（比較用副本，不是正本）", ""]
    if cal:
        lines += ["| 論文 | 標籤 | 模式 | 模型 | 路徑 |", "|---|---|---|---|---|"]
        lines += [f"| `{e['paper']}` | {e.get('label','')} | {e.get('mode','')} | {e.get('model','')[:40]} | `{Path(e['path']).relative_to(home) if str(e['path']).startswith(str(home)) else e['path']}` |" for e in cal]
    else:
        lines += ["（無）"]
    lines += ["", "相關：[[KEYPOINTS]] · [[home]]", ""]
    (home / "README.md").write_text("\n".join(lines), encoding="utf-8")


def rebuild_all(home: Path, data):
    for e in data["entries"]:
        upgrade_entry(e)
    by_paper = {e["run_id"]: e for e in data["entries"]}
    for e in data["entries"]:
        if e.get("kind", "accepted") == "accepted":
            write_keypoint_note(home, e, by_paper)
    # products list may now include the keypoint note's existence; README reads the filesystem for it
    write_readme(home, data)
    write_keypoints_index(home, data)
    for p in stray_keypoints(home):
        print(f"[warn] stray keypoint note beside the canonical one: {p.relative_to(home)} "
              f"— move it into {p.parent.name}/{PREVIOUS}/ (naming-and-placement PL-4)", file=sys.stderr)


def register(home: Path, data, run_dir: Path, kind=None, label=None):
    cards = json.loads((run_dir / "cards.json").read_text(encoding="utf-8"))
    e = entry_from_cards(run_dir.resolve(), cards, home, kind, label)
    data["entries"] = [x for x in data["entries"] if x["run_id"] != e["run_id"] and x.get("path") != e["path"]] + [e]
    save_index(home, data)
    rebuild_all(home, data)
    return e


# ---------------------------------------------------------------- migrate (2026-09-04, naming over routing)
# AP-74 copy-of: hooks/_lib/tree.py::is_reparse — research-papers ships this skill without hooks/_lib (rules/tree-walk-reparse.md, packaged helper)
def is_reparse(p: Path) -> bool:
    try:
        return p.is_symlink() or bool(getattr(os.lstat(p), "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def files_inside(root: Path):
    """Regular files under root, never entering a junction or symlink (rglob and os.walk enter NTFS
    junctions; the vault root holds two, into a skill folder and LexiconVault)."""
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [n for n in dirnames if not is_reparse(d / n)]
        yield from (d / n for n in filenames if not is_reparse(d / n))


def rewrite_ids(root: Path, mapping):
    """Replace every old id by its new id in every text file under root — longest ids first (one old id can be a prefix
    of another: 20260903_Bose2024_… vs …-sin-y). Returns the number of files changed."""
    keys = sorted(mapping, key=len, reverse=True)
    changed = 0
    for p in files_inside(root):
        if p.suffix.lower() not in TEXT_EXT or p.name == "index.json":
            continue
        if PREVIOUS in p.relative_to(root).parts:
            continue  # a retired copy keeps the text it had when it was retired
        try:
            t = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        t2 = t
        for k in keys:
            t2 = t2.replace(k, mapping[k])
        if t2 != t:
            p.write_text(t2, encoding="utf-8"); changed += 1
    return changed


PREVIOUS = "_previous"


def retire_old_named(dst: Path, old_id: str):
    """Move top-level files whose NAME embeds the old run id into dst/_previous/ (never delete).
    rewrite_ids rewrites ids inside file text but not in file names, so the 2026-09-04 migrate left
    `20260903_<paper>_keypoint.md` beside the regenerated `<paper>_keypoint.md` — a copy at the
    canonical level (naming-and-placement PL-4), caught 10 days later by copy-census R8."""
    moved = []
    for p in sorted(dst.iterdir()):
        if p.is_file() and p.name.startswith(old_id + "_"):
            (dst / PREVIOUS).mkdir(exist_ok=True)
            target = dst / PREVIOUS / p.name
            shutil.move(str(p), str(target))
            moved.append(target)
    return moved


def stray_keypoints(home: Path):
    """Keypoint notes at a paper folder's top level that are not that folder's canonical note."""
    out = []
    for d in sorted(home.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or not (d / "cards.json").exists():
            continue
        out += [p for p in sorted(d.glob("*_keypoint.md")) if p.name != keypoint_note_name(d.name)]
    return out


def migrate(home: Path, data, plan_p: Path, apply: bool):
    """plan.json: {"moves": [{"from": "<old folder>", "paper": "<PaperId>", "kind": "accepted|calibration", "label": "<label>"}]}.
    Dry-run prints the moves and the id map; --apply moves the folders (shutil.move, never delete), rewrites ids in every
    text file of the library (story.json run.id / distill_run / relations, cards.json, _meta.json, records, aliases),
    stamps previous_ids, re-registers every run and rebuilds README / KEYPOINTS / keypoint notes."""
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    mapping, moves = {}, []
    for m in plan["moves"]:
        src = home / m["from"]
        if not src.is_dir():
            print(f"[skip] {m['from']}: no such folder"); continue
        if m["kind"] == "accepted":
            new_id, dst = m["paper"], home / m["paper"]
        else:
            new_id, dst = f"{m['paper']}__{m['label']}", home / CALIB / m["paper"] / m["label"]
        old_id = m["from"]
        if old_id != new_id:
            mapping[old_id] = new_id
        moves.append((src, dst, old_id, new_id, m["kind"], m.get("label", "")))
    print("PLAN")
    for src, dst, old, new, kind, label in moves:
        print(f"  {kind:<11} {src.relative_to(home)}  ->  {dst.relative_to(home)}   id {old} -> {new}")
    print(f"  id map: {len(mapping)} rewrite(s)")
    if not apply:
        print("dry-run only — pass --apply to move"); return 0
    for src, dst, old, new, kind, label in moves:
        if dst.exists():
            print(f"[abort] destination exists: {dst}"); return 2
    for src, dst, old, new, kind, label in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"moved {src.name} -> {dst.relative_to(home)}")
    for src, dst, old, new, kind, label in moves:
        if old != new:
            for p in retire_old_named(dst, old):
                print(f"retired old-named {p.name} -> {p.relative_to(home)}")
    n = rewrite_ids(home, mapping)
    print(f"rewrote ids in {n} file(s)")
    # stamp AFTER the rewrite — the first run stamped before it and the rewrite turned every previous_id into the new id (2026-09-04)
    for src, dst, old, new, kind, label in moves:
        for name in ("story.json", "cards.json", "_meta.json"):
            p = dst / name
            if p.exists():
                j = json.loads(p.read_text(encoding="utf-8"))
                node = j.get("run", j) if name != "_meta.json" else j
                key = "run_id" if name == "_meta.json" else "id"
                node[key] = new
                prev = [x for x in node.get("previous_ids", []) if x != new]
                if old != new and old not in prev:
                    prev.append(old)
                node["previous_ids"] = prev
                if name == "_meta.json":
                    j["kind"] = kind; j["label"] = label; j["paper"] = dst.name if kind == "accepted" else dst.parent.name
                p.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    data["entries"] = []
    for src, dst, old, new, kind, label in moves:
        register(home, data, dst, kind, label)
    for d in sorted(home.iterdir()):
        if d.is_dir() and d.name != CALIB and (d / "cards.json").exists() and not any(e["path"] == str(d.resolve()) for e in data["entries"]):
            register(home, data, d)
    print(f"re-registered {len(data['entries'])} run(s); README / KEYPOINTS / keypoint notes rebuilt")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", type=Path, default=DEFAULT_HOME)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    r = sub.add_parser("register"); r.add_argument("run_dir", type=Path); r.add_argument("--kind", choices=["accepted", "calibration"]); r.add_argument("--label", default=None)
    sub.add_parser("list")
    f = sub.add_parser("find"); f.add_argument("term")
    sub.add_parser("readme")
    mg = sub.add_parser("migrate"); mg.add_argument("--plan", type=Path, required=True); mg.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    if a.home is None:
        ap.error("--home is required: set PAPER_DISTILL_HOME, or NOTES_VAULT in adapt/host.toml")
    data = load_index(a.home)
    if a.cmd == "init":
        rebuild_all(a.home, data)
        print(json.dumps({"home": str(a.home), "entries": len(data["entries"])}))
    elif a.cmd == "register":
        e = register(a.home, data, a.run_dir, a.kind, a.label)
        print(json.dumps({"registered": e["run_id"], "kind": e["kind"], "paper": e["paper"], "entries": len(data["entries"])}, ensure_ascii=False))
    elif a.cmd == "list":
        for e in sorted(data["entries"], key=lambda x: (x.get("kind", ""), x.get("paper", ""))):
            print(f"{e.get('kind','?'):<11} {e['run_id']}\t{e.get('year') or ''}\t{e.get('title','')[:60]}\t→ {e.get('keypoint_title','')[:70]}")
    elif a.cmd == "find":
        t = fold(a.term)
        hits = [e for e in data["entries"] if any(t in fold(str(e.get(k, ""))) for k in
                ("title", "keypoint_title", "keypoint_reading", "first_author", "venue", "doi", "domain_profile", "run_id", "paper"))
                or any(t in fold(x) for x in e.get("tags", []) + e.get("patterns", []))]
        print(json.dumps(hits, ensure_ascii=False, indent=1))
    elif a.cmd == "readme":
        rebuild_all(a.home, data)
        print(json.dumps({"readme": str(a.home / 'README.md'), "keypoints": str(a.home / 'KEYPOINTS.md')}))
    elif a.cmd == "migrate":
        return migrate(a.home, data, a.plan, a.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
