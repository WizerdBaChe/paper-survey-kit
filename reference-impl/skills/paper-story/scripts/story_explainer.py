"""story.json (+ cards.json) -> <run>/paper-explainer.explainer.json -> paper-explainer.html via tools/carriers.

Since 2026-10-12 (user ruling: 「html改用我們新版的說明頁格式」) the class-A HTML of a paper-story run is ONE
explainer page built by the registered `html-explainer` carrier; onepage.html / talk-deck.html are retired
(render_story.py --legacy-html still writes them for an old run). This script is a pure mapping: it adds no
words of its own beyond fixed section headings and table column names; every sentence comes from story.json
or cards.json.

Usage:
  python story_explainer.py --run <run_dir> [--no-build]
Exit: 0 built and `build.py check` ok; 1 build/check failed; 2 bad input.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_story as RS  # noqa: E402  (tile helpers and the ONE talk-script builder; render_story imports this module lazily, no cycle)

CARRIERS = Path(__file__).resolve().parents[3] / "tools" / "carriers"   # <config home>/tools/carriers, relative so a copied tree finds its own
BUILD = CARRIERS / "build.py"
STEM = "paper-explainer"
CARRIER = "html-explainer"

STATUS_ZH = {"achieved": "達到（實測）", "partly": "部分達到", "simulated-only": "僅模擬／計算", "not-shown": "沒有證明"}
KIND_ZH = {"fabrication": "製作", "model": "設計／模型", "simulation": "模擬", "measurement": "量測", "analysis": "分析"}
VERDICT_ZH = {"provisional": "暫可採信 (provisional)", "leaning": "傾向成立 (leaning)",
              "hypothetical": "假說程度 (hypothetical)", "withhold": "保留判斷 (withhold)"}
DRIFT_ZH = {"over-claim": "說過頭", "grafted-result": "嫁接的結果", "no-criterion": "沒有判準",
            "method-after-the-fact": "事後補的方法", "figure-unasked": "沒被問的圖", "limitation-aside": "限制一筆帶過",
            "weaker-instrument": "較弱的證據工具", "discussion-new-data": "討論裡的新資料",
            "selective-condition": "挑選條件", "abstract-mismatch": "摘要與內文不符", "other": "其他"}
AXIS = (("entry_point", "切入點", "what", "why"), ("central_claim", "核心主張", "what", "why_matters"),
        ("method_choice", "方法選擇", "what", "why"), ("evaluation_plan", "評估計畫", "what_to_show", "why"),
        ("presentation", "呈現方式", "order", "why"))
FIG_READ = (("look", "看什麼"), ("see", "會看到"), ("against", "對照"), ("means", "所以"))
RUN_ID = re.compile(r"\b([A-Z][A-Za-z]+)(\d{4})_[a-z0-9-]+")


def clean(s):
    """Text for an audience page: run ids become 'Author Year'; stray markup characters are neutralised."""
    s = "" if s is None else str(s)
    s = RUN_ID.sub(lambda m: f"{m.group(1)} {m.group(2)}", s)
    return s.replace("**", "＊＊").replace("[[", "［［")


def slug(s, used):
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:30] or "t"
    if not base[0].isalnum():
        base = "t" + base
    out, n = base, 2
    while out in used:
        out = f"{base}-{n}"; n += 1
    used.add(out)
    return out


def glossary(story):
    used, out = set(), []
    for t in story.get("terms", []):
        gid = slug(t.get("en") or t["term"], used)
        if not re.match(r"^[a-z0-9]", gid):
            gid = slug("term-" + str(len(out) + 1), used)
        gloss = clean(t.get("gloss", "")) or clean(t.get("zh", "")) or "—"
        if t.get("zh") and t["zh"] not in gloss:
            gloss = f"{clean(t['zh'])}。{gloss}"
        g = {"id": gid, "term": clean(t["term"]), "gloss": gloss}
        if t.get("en") and t["en"] != t["term"]:
            g["en"] = clean(t["en"])
        out.append(g)
    return out


class Marker:
    """Wrap the FIRST occurrence of every glossary term in the page's running text with [[g:id]] (define-before-use)."""

    def __init__(self, gl):
        self.todo = sorted(((g["term"], g["id"]) for g in gl), key=lambda x: -len(x[0]))

    def __call__(self, text):
        text = clean(text)
        for term, gid in list(self.todo):
            pat = re.escape(term)
            if re.match(r"^[\x00-\x7f]+$", term):
                pat = r"(?<![A-Za-z0-9-])" + pat + r"(?![A-Za-z0-9-])"
            # never inside an existing marker
            for m in re.finditer(pat, text):
                before = text[:m.start()]
                if before.count("[[") > before.count("]]"):
                    continue
                text = text[:m.start()] + f"[[g:{gid}]]" + text[m.end():]
                self.todo.remove((term, gid))
                break
        return text


def refs(story):
    out = []
    for i, r in enumerate(story.get("en", {}).get("references", []), 1):
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", r)
        tag, body = (m.group(1), m.group(2)) if m else (f"Ref {i}", r)
        au = re.match(r"^([^,(]+)", body)
        yr = re.search(r"\((\d{4})", body)
        label = f"{tag}：{au.group(1).strip() if au else ''} {yr.group(1) if yr else ''}".strip()
        ref = {"id": f"ref-{i}", "label": label, "detail": clean(body)}
        doi = re.search(r"https?://doi\.org/\S+", body)
        if doi:
            ref["href"] = doi.group(0).rstrip(".")
        out.append(ref)
    return out


def table(caption, columns, rows):
    return {"type": "table", "caption": caption, "columns": columns, "rows": [[clean(c) for c in r] for r in rows]}


def script_blocks(story, M):
    """Blocks of the 口述稿 section: deep mode (deck + talk) = render_story.talk_parts (the builder the retired talk-script.md
    used, so the words are not re-implemented here); story mode = render_story.story_script_parts (onepage.script + tile notes).
    The builders return plain tuples; this adds the glossary markers and the bold labels."""
    if "deck" in story and "talk" in story:
        ex = RS.talk_parts(story)[1]
    else:
        ex = RS.story_script_parts(story)
        if "talk" in story:   # talk without a deck: talk_parts cannot run, but the outline / if-asked / closing must still be printed
            ex = ex + RS.talk_only_parts(story["talk"])
    blocks = []
    for b in ex:
        kind = b[0]
        if kind == "head":
            blocks.append({"type": "para", "text": "**" + clean(b[1]) + "**"})
        elif kind == "labelled":
            blocks.append({"type": "para", "text": f"**{clean(b[1])}**" + ("：" + M(b[2]) if b[2] else "")})
        elif kind == "bullets":
            blocks.append({"type": "bullets", "items": [M(x) for x in b[1]]})
        elif kind == "steps":
            items = []
            for title, parts in b[1]:
                it = {"title": clean(title)}
                txt = "　".join(f"**{lab}**：" + M(t) for lab, t in parts if t)
                if txt:
                    it["text"] = txt
                items.append(it)
            blocks.append({"type": "steps", "items": items})
    return blocks


def talk_section_text(run_dir: Path):
    """Plain text of the built explainer's 口述稿 section (glossary markers resolved to their terms, bold removed) — what S9
    reads. '' when the content file has no such section."""
    cf = run_dir / f"{STEM}.explainer.json"
    if not cf.is_file():
        return ""
    c = json.loads(cf.read_text(encoding="utf-8"))
    terms = {g["id"]: g["term"] for g in c.get("glossary", [])}
    sec = next((s for s in c.get("sections", []) if s.get("id") == "script"), None)
    if not sec:
        return ""
    out = []
    for b in sec.get("blocks", []):
        if b["type"] == "para":
            out.append(b["text"])
        elif b["type"] == "bullets":
            out += b["items"]
        elif b["type"] == "steps":
            out += [it["title"] + " " + it.get("text", "") for it in b["items"]]
    txt = "\n".join(out).replace("**", "")
    return re.sub(r"\[\[g:([a-z0-9-]+)\]\]", lambda m: terms.get(m.group(1), m.group(1)), txt)


def build_content(run_dir: Path):
    story = json.loads((run_dir / "story.json").read_text(encoding="utf-8"))
    cpath = run_dir / "cards.json"
    cards = json.loads(cpath.read_text(encoding="utf-8")) if cpath.exists() else {}
    src, run, logic = story["source"], story["run"], story.get("logic", {})
    gl = glossary(story); M = Marker(gl)
    sections = []

    # 1 keypoint
    blocks = [{"type": "callout", "kind": "key", "title": "Keypoint", "text": M(logic.get("keypoint", ""))}]
    if logic.get("keypoint_description"):
        blocks.append({"type": "para", "text": M(logic["keypoint_description"])})
    if logic.get("bindings"):
        blocks.append(table("Keypoint 的每個角色在這篇指什麼", ["角色", "在這篇", "出處"],
                            [[b["role"], b["referent"], b.get("locator", "")] for b in logic["bindings"]]))
    wm = story.get("why_me", {})
    wb = [M(f"為什麼讀：{wm['why_read']}")] if wm.get("why_read") else []
    if wm.get("helps"):
        wb.append(M(f"對我有什麼幫助：{wm['helps']}"))
    if wm.get("question_i_bring"):
        wb.append(f"帶著的問題：{clean(wm['question_i_bring'])}")
    if wb:
        blocks.append({"type": "bullets", "items": wb})
    sections.append({"id": "keypoint", "heading": "Keypoint：這篇教我的邏輯", "summary": "先看抽象出來的設計邏輯，再看它在這篇裡指的是什麼。",
                     "takeaways": [b["role"] for b in logic.get("bindings", [])][:6], "blocks": blocks})

    # 2 brief
    br, op = story.get("brief", {}), story.get("onepage", {}).get("table", {})
    blocks = []
    for k, lab in (("problem", "問題"), ("approach", "做法"), ("differs", "和別人的不同")):
        if br.get(k):
            blocks.append({"type": "para", "text": f"**{lab}**：" + M(br[k])})
    if op:
        # user ruling 2026-11-03 G2: four or five rows per onepage.fields (default five, Features kept)
        four = RS.onepage_fields(story.get("onepage", {})) == "four"
        blocks.append(table("論文一頁：" + ("四個欄位" if four else "五個欄位"), ["欄位", "內容"],
                            [[lab, op[k]] for k, lab in (("structure", "結構"), ("features", "特色"), ("method", "方法"),
                                                         ("result", "結果"), ("conclusion", "結論"))
                             if op.get(k) and not (four and k == "features")]))
    if br.get("methods"):
        blocks.append(table("用到的所有方法：每個方法回答一個問題", ["方法", "種類", "回答的問題", "出處"],
                            [[m["name"], KIND_ZH.get(m.get("kind"), m.get("kind", "")), m.get("answers", ""), m.get("locator", "")]
                             for m in br["methods"]]))
    if br.get("verdicts"):
        blocks.append(table("有沒有做到？怎麼判讀？", ["目標", "怎麼判", "結果", "判定", "出處"],
                            [[v["goal"], v.get("judged_by", ""), v.get("result", ""), STATUS_ZH.get(v.get("status"), v.get("status", "")),
                              v.get("locator", "")] for v in br["verdicts"]]))
    if blocks:
        sections.append({"id": "brief", "heading": "一眼看懂：問題、方法與成果", "summary": "問題、全部方法、每個目標有沒有做到。",
                         "takeaways": [f"{v['goal']}：{STATUS_ZH.get(v.get('status'), '')}" for v in br.get("verdicts", [])][:6],
                         "blocks": blocks})

    # 3 axis
    ax = story.get("axis", {})
    rows = []
    for key, lab, wk, yk in AXIS:
        a = ax.get(key)
        if a:
            rows.append([lab, a.get(wk, ""), a.get(yk, ""), a.get("locator", "")])
    if rows:
        blocks = [table("主軸：每一步做了什麼、為什麼這樣做", ["項目", "做了什麼", "為什麼", "出處"], rows)]
        mc = ax.get("method_choice", {})
        for k, lab in (("alternatives", "沒選的替代做法"), ("necessity", "拿掉會怎樣"), ("dead_ends", "走不通的路")):
            if mc.get(k):
                blocks.append({"type": "para", "text": f"**{lab}**：" + M(mc[k])})
        for key, lab, _, _ in AXIS:
            q = ax.get(key, {}).get("quote")
            if q:
                blocks.append({"type": "quote", "text": clean(q), "source": f"{lab}，{clean(ax[key].get('locator', ''))}"})
        sections.append({"id": "axis", "heading": "主軸：為什麼是這個切入點與方法", "summary": "切入點、核心主張、方法、評估與呈現，各附原因。",
                         "blocks": blocks})

    # 4 storyline
    sl = story.get("storyline", [])
    if sl:
        blocks = []
        arc = story.get("talk", {}).get("story_arc", {})
        if arc.get("spine"):
            blocks.append({"type": "callout", "kind": "note", "title": "故事主線", "text": M(arc["spine"])})
        blocks.append({"type": "steps", "items": [{"title": clean(b["beat"]),
                                                   "text": M(f"{b['what']} 為什麼：{b['why']}（{b.get('locator', '')}）")} for b in sl]})
        if arc.get("craft"):
            blocks.append(table("作者怎麼讓人相信這個故事", ["段落", "手法", "為什麼有效", "出處"],
                                [[c.get("beat", ""), c.get("move", ""), c.get("why_it_works", ""), c.get("locator", "")] for c in arc["craft"]]))
        sections.append({"id": "storyline", "heading": "故事線：作者怎麼講這個研究", "summary": "依作者的敘事順序，每一段都附為什麼。",
                         "blocks": blocks})

    # 5 figures
    fcards = {f.get("file"): f for f in cards.get("figures", [])}
    blocks, seen = [], set()
    if "deck" not in story:
        # story mode (no deck): the walk is built from the one-page TILES (user ruling 2026-11-03 G1/G5) — every file of a tile,
        # its figure_read and its spoken notes; a deck run keeps the per-deck-page walk below
        for k, t in enumerate(story.get("onepage", {}).get("figures", [])):
            fs = [fn for fn in RS.tile_files(t) if (run_dir / fn).is_file()]
            if not fs:
                continue
            fr = t.get("figure_read") or {}
            step = RS.STEP_ZH.get(t.get("step", ""), "")
            label = f"({chr(97 + k)}) {t.get('caption', '')}" + (f" · {t['locator']}" if t.get("locator") else "") + (f"（{step}）" if step else "")
            for j, fn in enumerate(fs):
                shows = fr.get("see") or fcards.get(fn, {}).get("shows") or t.get("why") or t.get("caption", "") or label
                fig = {"type": "figure", "src": fn.replace("\\", "/"), "shows": clean(shows),
                       "caption": clean(label + (f"，第 {j + 1}／{len(fs)} 張" if len(fs) > 1 else ""))}
                nd = fcards.get(fn, {}).get("blind_spot")
                if nd and fn not in seen:
                    fig["not_drawn"] = clean(nd)
                seen.add(fn)
                blocks.append(fig)
            if t.get("why"):
                blocks.append({"type": "para", "text": "**為什麼放這一格**：" + M(t["why"])})
            if t.get("necessity"):
                blocks.append({"type": "callout", "kind": "note", "title": "旁證為什麼不能省", "text": M(t["necessity"])})
            steps = [{"title": lab, "text": M(fr[kk])} for kk, lab in FIG_READ if fr.get(kk)]
            if steps:
                blocks.append({"type": "steps", "items": steps})
            if t.get("notes"):
                blocks.append({"type": "para", "text": "**口述時這樣走**：" + M(t["notes"])})
    for p in story.get("deck", {}).get("pages", []):
        f = p.get("figure")
        if not f or not (run_dir / f).is_file():
            continue
        fr = p.get("figure_read", {})
        shows = fr.get("see") or fcards.get(f, {}).get("shows") or p.get("takeaway") or p["title"]
        fig = {"type": "figure", "src": f.replace("\\", "/"), "caption": clean(f"{p['title']}（{p.get('locator', '')}）"), "shows": clean(shows)}
        nd = fcards.get(f, {}).get("blind_spot")
        if nd and f not in seen:
            fig["not_drawn"] = clean(nd)
        seen.add(f)
        blocks.append(fig)
        if p.get("highlights"):
            blocks.append({"type": "bullets", "items": [M(h) for h in p["highlights"]]})
        steps = [{"title": lab, "text": M(fr[k])} for k, lab in FIG_READ if fr.get(k)]
        if steps:
            blocks.append({"type": "steps", "items": steps})
        if p.get("takeaway"):
            blocks.append({"type": "callout", "kind": "key", "title": "帶走一句", "text": M(p["takeaway"])})
    if blocks:
        sections.append({"id": "figures", "heading": "逐圖判讀", "summary": "每張圖先看座標與圖例，再看結果，最後才讀意義。", "blocks": blocks})

    # 5b spoken script (user ruling 2026-11-03: the talk script lives INSIDE the explainer and is the only talk section; talk-script.md is no longer written).
    # Deep mode prints the renderer's own talk-script builder (talk_parts); story mode prints onepage.script + each tile's notes.
    sc = script_blocks(story, M)
    if sc:
        sections.append({"id": "script", "heading": "口述稿",
                         "summary": "報告時要說的話：開場、分段、每頁怎麼講、被問到怎麼答、結尾。" if "deck" in story else
                                    "每頁的講法：先說出處與目的，再逐格走圖（座標、看到什麼、代表什麼），不唸表格。", "blocks": sc})

    # 6 audit
    blocks = []
    if cards.get("claims"):
        blocks.append(table("深讀審計：主張與證據", ["#", "主張", "判定", "還缺什麼"],
                            [[f"主張 {i}", c["text"], VERDICT_ZH.get(c.get("verdict"), c.get("verdict", "")), c.get("missing", "")] for i, c in enumerate(cards["claims"], 1)]))
    dr = story.get("drift", [])
    if dr:
        blocks.append(table("敘事偏離：論文怎麼說 vs 證據到哪裡", ["位置", "種類", "偏離了什麼", "為什麼要緊"],
                            [[d.get("where", ""), DRIFT_ZH.get(d.get("kind"), d.get("kind", "")), d.get("what_drifted", ""),
                              d.get("why_it_matters", "")] for d in dr]))
    if blocks:
        sections.append({"id": "audit", "heading": "深讀審計：哪些可信、哪些要打折", "summary": "每個主張的判定，以及論文敘事偏離證據的地方。",
                         "takeaways": [f"主張 {i}：{VERDICT_ZH.get(c.get('verdict'), '')}" for i, c in enumerate(cards.get("claims", []), 1)][:6],
                         "blocks": blocks})

    # 7 logic chain
    ch = logic.get("chain", [])
    if ch:
        blocks = [{"type": "steps", "items": [{"title": clean(c["step"]),
                                               "text": M(f"{c.get('in_this_paper', '')} 為什麼成立：{c.get('warrant', '')}"
                                                         + (f" 限制：{c['qualifier']}" if c.get("qualifier") else "")
                                                         + f"（{c.get('backing', '')}）")} for c in ch]}]
        fr_ = logic.get("fragile", {})
        if fr_.get("what"):
            blocks.append({"type": "callout", "kind": "warn", "title": "最脆弱的一環", "text": M(f"{fr_['what']} {fr_.get('why', '')}")})
        pt = logic.get("portable", {})
        if pt.get("where"):
            blocks.append({"type": "callout", "kind": "note", "title": "可以搬到哪裡用",
                           "text": M(f"{pt['where']} {pt.get('why', '')}" + (f" 不適用：{pt['when_not']}" if pt.get("when_not") else ""))})
        rel = logic.get("relations", [])
        if rel:
            blocks.append({"type": "bullets", "items": [M(f"{r['run']}：{r.get('why', '')}") for r in rel]})
        sections.append({"id": "logic", "heading": "邏輯鏈：每一步為什麼成立", "summary": "Keypoint 拆成步驟，每步附依據、限制與出處。",
                         "takeaways": [c["step"] for c in ch][:6], "blocks": blocks})

    # (the former 8 「上台要點」 section is gone — user ruling 2026-11-03 「只留「口述稿」section」: its outline, if-asked memos and
    # closing are printed by the 口述稿 section above, see script_blocks)

    # 9 search / future
    en = story.get("en", {})
    blocks = []
    fw = en.get("future_work", {})
    items = [clean(x.get("text", x) if isinstance(x, dict) else x) for x in fw.get("paper", []) + fw.get("mine", [])]
    if items:
        blocks.append({"type": "bullets", "items": items})
    se = en.get("search", {})
    if se:
        si = [clean(x) for x in se.get("layers", []) if isinstance(x, str)]
        if se.get("query"):
            si.append(f"Query: {clean(se['query'])}")
        for k in ("backward", "forward"):
            if se.get(k):
                si.append(f"{clean(se[k].get('head', k))}：" + "；".join(clean(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)) for x in se[k].get("items", [])))
        if se.get("stop"):
            si.append(f"Stop: {clean(se['stop'])}")
        if si:
            blocks.append({"type": "bullets", "items": si})
    if blocks:
        sections.append({"id": "next", "heading": "延伸與找資料", "summary": "論文自己說的下一步、值得試的延伸、怎麼找相關文獻。", "blocks": blocks})

    authors = src.get("authors", [])
    meta = {"title": clean(src["title"]), "subtitle": clean(f"{', '.join(authors[:3])}{' et al.' if len(authors) > 3 else ''} · {src.get('venue', '')}"),
            "date": (run.get("created") or "1970-01-01")[:10], "audience": "audience", "lang": "zh-TW",
            "purpose": "看完之後能說出這篇的設計邏輯、每張圖在說什麼、哪些數字可信、哪些要打折。",
            "source_note": clean(f"由論文深讀與敘事紀錄機械轉出；原文 {src.get('url') or src.get('doi', '')}")}
    if run.get("presenter"):
        meta["author"] = clean(f"報告者 {run['presenter']}")
    return {"schema": "explainer/1", "meta": meta, "glossary": gl, "refs": refs(story), "sections": sections}


def build(run_dir: Path, do_build=True):
    content = build_content(run_dir)
    cf = run_dir / f"{STEM}.explainer.json"
    # newline="\n": the consuming repos pin *.json to LF, and Path.write_text would write CRLF on Windows
    with open(cf, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(content, ensure_ascii=False, indent=1) + "\n")
    print(f"content: {cf.name} ({len(content['sections'])} sections, {len(content['glossary'])} terms, {len(content['refs'])} refs)")
    if not do_build:
        return 0
    out = run_dir / f"{STEM}.html"
    r = subprocess.run([sys.executable, "-X", "utf8", str(BUILD), "build", "--carrier", CARRIER, "--content", str(cf), "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip()); print(r.stderr.strip()) if r.stderr.strip() else None
    if r.returncode:
        return 1
    c = subprocess.run([sys.executable, "-X", "utf8", str(BUILD), "check", str(out), "--content", str(cf)],
                       capture_output=True, text=True, encoding="utf-8")
    print(c.stdout.strip())
    return 0 if c.returncode == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True); ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args(argv)
    if not (a.run / "story.json").is_file():
        print(f"no story.json in {a.run}", file=sys.stderr); return 2
    return build(a.run, not a.no_build)


if __name__ == "__main__":
    sys.exit(main())
