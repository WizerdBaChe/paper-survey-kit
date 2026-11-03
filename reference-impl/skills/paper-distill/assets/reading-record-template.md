---
xi: 1
what: "【學習紀錄】{{source.title}} — 閱讀分析過程：key point 先行、IMRAD 拆解、主張審計、圖表判讀、寫作解剖、定位 (paper-distill reading record: the learning document)"
tags: [paper-distill, reading-record, literature]
aliases: ["{{source.first_author}} {{source.year}} 閱讀紀錄", "{{run.id}}", "{{source.title}} reading record"]
date: {{run.created_date}}
status: live
kind: literature
source: "file: {{run.id}}/source/paper.pdf"
verified: "read-in-full {{run.created_date}} by {{run.model}}; locators spot-checked by {{run.presenter}}: pending"
review-when: "a second paper contradicts C1, or the presenter's own key point differs from §0"
domain: [{{intake.domain_profile}}]
promoted-to: "-"
---

# 【學習紀錄】閱讀分析過程：{{source.title}}

> **這份文件是什麼**：我讀這篇論文的完整過程與判斷，給我自己學習用（怎麼讀、怎麼審、怎麼抽精華）。
> 它不是講稿，也不是給聽眾看的頁面——那些由 `paper-story` 產出：論文說明頁 `paper-explainer.html`，其中「口述稿」一節就是報告時我要說的話（因人而異，改成自己的話）。

| 檔案 | 用途 | 讀者 |
|---|---|---|
| `reading-record.md`（本檔） | 學習紀錄：閱讀分析過程 | 我 |
| `paper-explainer.html`（`paper-story` 產出，有跑才有） | 論文說明頁（練習・複習用），含「口述稿」一節 | 我（上台前） |
| `cards.json` | 機器契約：本檔的資料來源（`paper-story` 也讀它） | 工具 |

`paper-distill` · run `{{run.id}}` · depth `{{run.depth}}` · 來源類型 {{source.type}} · 取得層級 {{source.access}} · 修訂 r{{run.revision}}

> 讀法：每一節先列「自問」，再給答案。每句話帶來源標記 —— `[author]` 論文說的（有出處）、`[verified]` 我對照圖表確認過、`[inferred]` 我從論文材料推論、`[assumed]` 未驗證的假設。出處寫 `p.N / Fig.N / Table N / Eq.N / §N`；找不到就寫「無法定位」。

## 0. 審計摘要先行（這篇的證據撐得住什麼）

- C1（會被引用的那句）：{{claims.0.text}} —— 證據種類 {{claims.0.kind}} · 判定 **{{claims.0.verdict}}** · 仍缺 {{claims.0.missing}}
- 站得住的：{{core.holds_up}}
- 還缺的：{{core.missing}}
- 對我們的意義：{{position.relevance}}
- Key point（邏輯抽取）不在本檔：→ `paper-story` 的 `narrative-record.md`／`story.json`（run：{{story_run}}；若尚未跑，寫「未跑」）

<details><summary>先寫你的版本（看下面審計之前，先寫下你認為這篇「證據撐得住什麼」）</summary>

> _{{learning.your_version_first}}_

</details>

## 1. 取用卡 (Intake)

- 自問：Abstract 說要解決什麼？Conclusion 主張什麼？Introduction 宣稱什麼貢獻？只准指一張圖時作者會指哪張？我為什麼挑這篇？
- 書目：{{source.authors}}，《{{source.title}}》，{{source.venue}} {{source.year}}，DOI {{source.doi}}
- Abstract 的問題：{{intake.triage.abstract_problem}}
- Conclusion 的主張（待測試的那句）：{{intake.triage.conclusion_claim}}
- Introduction 宣稱的貢獻：{{intake.triage.intro_contribution}}
- 作者會指的那張圖：{{intake.triage.one_figure}}
- 判斷：{{intake.triage.decision}} —— {{intake.triage.reason}}
- 為什麼挑這篇：{{intake.why_this}}
- 與實驗室的關聯（domain profile：{{intake.domain_profile}}）：{{intake.lab_relevance}}
- 深度標尺（相關度／方法權重／證據深度，各 high・mid・low）：{{intake.triage.depth_ruler.relevance}} ／ {{intake.triage.depth_ruler.method_weight}} ／ {{intake.triage.depth_ruler.evidence_depth}}

## 1b. 詞彙表 (Glossary) — 第一遍先找出這篇 paper 的主角

- 自問：哪些詞反覆出現（標題／摘要／簡介先看）？它是主角、解釋框架、領域共用、還是本文特有？我目前還不懂它什麼？第二遍要追問它什麼？
- 工具：`scripts/glossary.py` 給的是頻率與首次出現頁（bytes）；分類與「還不懂」是我填的。留 10–15 個。

| 詞 | 頻率 | 四類 | 目前還不懂什麼 | 第二遍要追問什麼 |
|---|---|---|---|---|
{{#terms}}| {{term}} | {{freq}} | {{role}} | {{unclear}} | {{ask_next}} |
{{/terms}}

- 本文特有（coined）的詞：是新概念，還是舊概念換名字？→ §4 slop 診斷「名詞替換」的輸入清單。

## 2. 骨架卡 (Skeleton) — IMRaD 是思考順序，不是格式

- 自問：每一節在整篇論證裡的「功能」是什麼？作者放了什麼材料？我理解了什麼？哪一段放錯地方（為什麼放在這裡）？Results 有沒有偷渡解讀、Discussion 有沒有偷渡新資料？

| 區段 | 它要完成什麼 | 作者放了哪些材料 | 我目前理解什麼 |
|---|---|---|---|
| Introduction（問題／前人／缺口） | {{skeleton.I.function}} | {{skeleton.I.materials}} | {{skeleton.I.understood}} |
| Methods（工具／採樣／流程／模型） | {{skeleton.M.function}} | {{skeleton.M.materials}} | {{skeleton.M.understood}} |
| Results（What，客觀） | {{skeleton.R.function}} | {{skeleton.R.materials}} | {{skeleton.R.understood}} |
| Discussion（Why，詮釋） | {{skeleton.D.function}} | {{skeleton.D.materials}} | {{skeleton.D.understood}} |

- 缺口三要素：問題 {{skeleton.gap.problem}} ／ 前人 {{skeleton.gap.prior}} ／ 缺口 {{skeleton.gap.gap}}
- Method 四元素：工具 {{skeleton.method_elements.tools}} ／ 採樣 {{skeleton.method_elements.sampling}} ／ 流程 {{skeleton.method_elements.procedure}} ／ 模型 {{skeleton.method_elements.model}}
- 放錯位置的段落（為什麼放在這裡）：{{skeleton.anomalies}}
- What／Why 混用處：{{skeleton.what_why_leaks}}

## 3. 核心卡 (Core) — 這篇研究如何成立？還缺什麼？

- 自問：研究問題是什麼、為何重要？用什麼設計、資料哪來、怎麼分析？發現什麼？有哪些限制？作者宣稱帶來什麼新的東西？
- RQ：{{core.rq}} · Methods：{{core.methods}} · Results：{{core.results}} · Limitations：{{core.limitations}}
- 宣稱的貢獻 `[author]`：{{core.contribution_claimed}}
- 如何成立：{{core.holds_up}} · 還缺什麼（留給 §4 裁決）：{{core.missing}}

| 前人方法 | 作者說不足之處 | 公平嗎 `[inferred]` |
|---|---|---|
{{#related_work}}| {{prior}} | {{author_says_insufficient}} | {{fair}} |
{{/related_work}}

**前提盤點（Assumptions）**——自問：這篇把哪些前提當成真的、沒有去測？寫在哪裡（還是根本沒寫）？如果它是假的，哪條主張／哪一步邏輯會倒？

| 前提 | 出處（或 implicit） | 有測嗎 | 若為假，倒的是 | 來源 |
|---|---|---|---|---|
{{#assumptions}}| {{premise}} | {{where}} | {{tested}} | {{if_false}} | {{origin}} |
{{/assumptions}}

## 4. 主張審計 (Claim audit) — 證據夠不夠，不只在不在

- 自問：這篇會被引用的是哪句主張？哪張圖／表撐它？那是哪一種證據？還缺什麼？我最多能說到什麼程度？作者是自己跟自己比嗎？有沒有「應該失敗」的對照？

| ID | 主張 (claim) | 類型 | 觸及範圍 (reach) | 證據（出處 → 內容） | 種類 | 仍缺什麼 | 判定 | 來源 | 備註 |
|---|---|---|---|---|---|---|---|---|---|
{{#claims}}| {{id}} | {{text}} | {{type}} | {{reach_flat}} | {{evidence_flat}} | {{kind}} | {{missing}} | {{verdict}} | {{origin}} | {{notes}} |
{{/claims}}

- 這篇實際做了什麼：新框架 {{did.framework}} ／ 新名詞 {{did.term}} ／ 具體案例 {{did.use_case}} ／ 實驗或推導 {{did.experiment_or_derivation}} —— {{did.note}}
- 觸及範圍欄填 `reach` 的英文代碼（以「、」分隔）；主張宣稱了哪幾軸（方向／大小／因果／機制／真實元件／普遍性…），判定逐軸套用，證據撐不到的那一軸寫進「仍缺什麼」（定義見 `~/.claude/references/writing-norms/claim-reach.md` §1）
- 判定→措辭：provisional「在 N 個元件、X 條件下顯示」／ leaning「傾向、可能」／ hypothetical「若模型成立則」／ withhold「宣稱、未顯示」

## 5. 圖表判讀 (Figure cards) — 先看圖，再看作者怎麼說

- 自問：這張圖回答哪一個問題？要看的三件事？它實際顯示什麼？撐哪條主張？座標軸／誤差棒／樣本數／基準線有沒有問題？這種圖看不到什麼？

{{#figures}}
### {{id}} · {{locator}}
- 回答的問題：{{question}} · 要看的三件事：{{look_for_flat}}
- 它顯示 `[verified]`：{{shows}} · 撐的主張：{{supports}} · 注意：{{caveat}} · 看不到：{{blind_spot}}
{{/figures}}

## 6. 寫作解剖 (Writing craft) — 從這篇學怎麼寫一篇論文

- 自問：作者怎麼從問題走到主張（論證鏈）？方法段給了讀者什麼、我照著做還缺什麼？設計資料有哪些數字？每張圖是為了證明什麼而這樣畫？結果的數字怎麼報？限制怎麼講？哪幾句值得借？

**論證鏈**

| 步驟 | 我的話 | 論文裡做這件事的句子在 |
|---|---|---|
{{#argument_chain}}| {{step}} | {{text}} | {{locator}} |
{{/argument_chain}}

- 方法段給了什麼：{{craft.methods_writing.given}}
- 照著做還缺什麼：{{craft.methods_writing.missing_to_reproduce}}
- 呈現順序（好不好）：{{craft.methods_writing.order}}
- **設計資料表** `[author]`：{{craft.methods_writing.design_data}}

**圖證設計**

| 圖 | 為了證明什麼 | 為什麼選這種圖 | 註 |
|---|---|---|---|
{{#figure_design}}| {{locator}} | {{designed_to_prove}} | {{chart_choice}} | {{note}} |
{{/figure_design}}

- 結果怎麼寫：{{craft.results_writing}}
- 限制怎麼寫：{{craft.limitations_writing}}
- 可借句型（≤15 字逐字＋出處＋用途）：{{sentence_patterns_flat}}
- 我的改寫練習：{{craft.my_rewrite}}

## 7. 定位卡 (Positioning) — 縫隙在哪，對我們有什麼用

- 自問：作者說下一步是什麼？限制指向哪些沒做的事？跟我讀過的哪篇不一致？對我們的意義？借什麼、不借什麼？
- Future work：{{position.future_work}} · Limitations 指向：{{position.limitations}} · 跨文獻不一致：{{position.cross_paper}} · 縫隙：{{position.gap}}
- 對我們的意義：{{position.relevance}} · 借：{{position.borrow}} · 不借：{{position.not_borrow}}
- 脈絡（讀人不只讀篇，從參考文獻取）：這個群組的前作 {{position.lineage.group_prior_work}} · 還有誰在做 {{position.lineage.who_else}} · 所屬社群 {{position.lineage.community}}

## 8. 學習筆記

- 難的地方：{{learning.hard}}
- 學到的詞（詞條候選）：{{terms_flat}}
- 一週後自我檢查三題：{{#self_check}}
  - {{.}}{{/self_check}}
- 作者做得好的地方（欣賞作者、同時保留懷疑——只列缺口等於只讀了一半）：{{learning.admire}}
- 練習建議：{{learning.practice}}
- 重讀排程（每一遍換問題）：第二遍帶 How（§3–§6：能不能向別人重走一遍作者的推理）；第三遍帶 Why（paper-story 的軸向與 `necessity`、§7：換一種方式會失效嗎、破綻在哪、怎麼改良）。上面的三題自我檢查各對應一層。

## 9. 給 paper-story 的素材（簡報由 paper-story 做；這裡只留它會取用的東西）

- 設計資料表：見 §6；圖清單（依故事順序）：{{figures_flat}}；可借句型：見 §6
- 判定詞供引用：{{claims_verdicts_flat}}

## 10. 附錄

- 作者結論原文 `[author]`（{{paper_says.locator}}）：「{{paper_says.conclusion_quote}}」
- 逐字引文與出處：{{quotes}}
- 過程紀錄（時間、工具、看過哪些頁、跳過什麼與為什麼）：{{process_log}}
- 驗證輸出：`verify_run.py` 由派工者另跑（本 skill 拆分後不再產 `gates.txt`；簡報閘門在 paper-story 的 `story-gates.txt`）；vault 檢查：kv-lint {{kvlint_result}}

相關：[[home]]
