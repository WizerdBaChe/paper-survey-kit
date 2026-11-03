---
xi: 1
what: "【敘事紀錄】{{source.title}} — 主軸與故事線（每步帶為什麼）、邏輯抽取、偏離處、簡報素材、口述要點、詞彙 (paper-story narrative record)"
tags: [paper-story, narrative-record, literature]
aliases: ["{{source.first_author}} {{source.year}} 敘事紀錄", "{{run.id}}", "{{source.title}} narrative record"]
date: {{run.created_date}}
status: live
kind: literature
source: "file: {{run.id}}/source/paper.pdf"
verified: "read-in-full {{run.created_date}} by {{run.model}}; whys tagged [author]/[inferred]/[assumed]; locators spot-checked by {{run.presenter}}: pending"
review-when: "the presenter's own keypoint differs from §1, or a paper-distill audit changes a verdict cited in §4"
domain: [{{domain_profile}}]
promoted-to: "-"
---

# 【敘事紀錄】{{source.title}}

> **這份文件是什麼**：這篇研究是「怎麼被建構、為什麼這樣建構」的重建，以及我從中抽出的邏輯。它餵一份練習用產物（`paper-explainer.html`【論文說明頁】，其中「口述稿」一節就是口述稿——給我練習、學習、快速複習用，不是上台稿）；真正要報時，以實驗室 pptx 範本改英文（`lab-deck.pptx`，明確要求時才做，不由 html 轉）。證據審計不在這裡（→ `paper-distill` 的 `reading-record.md`，若有：`{{run.distill_run}}`）。

| 檔案 | 用途 | 讀者 |
|---|---|---|
| `narrative-record.md`（本檔） | 敘事紀錄：主軸、故事線、邏輯抽取、偏離 | 我 |
| `paper-explainer.html` | 論文說明頁（練習・複習用）：Keypoint、一眼看懂、主軸、故事線、逐圖判讀、口述稿（實驗室慣例的講法：開場、分段、逐頁怎麼講、被問時、結尾）、深讀審計、邏輯鏈、延伸；由 story.json＋cards.json 機械產出，不手改 | 我（口述稿一節：上台前） |
| `lab-deck.pptx` / `lab-onepage.pptx` | 正式簡報：實驗室範本改英文（換字、換圖、微調），明確要求時才做 | 聽眾（上台） |
| `story.json` | 機器契約 | 工具 |

`paper-story` · run `{{run.id}}` · mode `{{run.mode}}` · 深讀 run：{{run.distill_run}}

> 標記：每個「為什麼」帶 `[author]`（論文自己說的）／`[inferred]`（我重建的）／`[assumed]`；出處 `p.N / Fig.N / §N`。

## 0. 為什麼讀它、對我有什麼幫助

- 為什麼讀它：{{why_me.why_read}}
- 對我有什麼幫助：{{why_me.helps}}
- 我帶著什麼問題來讀：{{why_me.question_i_bring}}（專案：{{why_me.project}}）

## 0b. 它在解什麼、用了哪些方法、有沒有做到、怎麼判讀（`brief`，schema @5）

- Q1 它在解什麼問題：{{brief.problem}}
- Q2 怎麼做、跟別人哪裡不同：{{brief.approach}}　差異：{{brief.differs}}（對話對象：{{brief.conversation}}）

| 方法 | 類型 | 回答什麼問題 | 出處 |
|---|---|---|---|
{{#brief.methods}}| {{name}} | {{kind}} | {{answers}} | {{locator}} |
{{/brief.methods}}

| Q3 目標 | 怎麼判讀 | 結果 | 有沒有達到 | 出處 |
|---|---|---|---|---|
{{#brief.verdicts}}| {{goal}} | {{judged_by}} | {{result}} | {{status}} | {{locator}} |
{{/brief.verdicts}}

## 1. 邏輯抽取先行（key point）

**{{logic.keypoint}}**
（slogan：一句抽象的建構邏輯；每個角色名詞帶其領域限定詞——製程副作用、面型自由度——讓讀者光看句子就能定位它是哪一類東西，2026-09-04 裁定 Test 0c；邏輯型：{{logic.patterns}}）

**解讀（讀書心得的終極詮釋——沒讀過論文的人也能跟著走）**：{{logic.keypoint_description}}

| slogan 裡的角色 | 在這篇＝ | 出處 |
|---|---|---|
{{#bindings}}| {{role}} | {{referent}} | {{locator}} |
{{/bindings}}

| # | 步驟（抽象） | 在這篇（具體事件句） | 為什麼這一步成立（warrant） | 依據 | 到哪為止 |
|---|---|---|---|---|---|
{{#chain}}| {{n}} | {{step}} | {{in_this_paper}} | {{warrant}} | {{backing}} | {{qualifier}} |
{{/chain}}

- 最脆弱的一環：{{logic.fragile.what}} —— 為什麼脆弱：{{logic.fragile.why}}
- 可移植到：{{logic.portable.where}} —— 為什麼可移植：{{logic.portable.why}} —— 何時不可移植：{{logic.portable.when_not}}

<details><summary>先寫你的版本（看模型的之前，先用一句抽象邏輯寫下你認為這篇是怎麼被建構的）</summary>

> _（空白）_

</details>

## 2. 主軸（每一項都要有為什麼）

- 自問：作者從哪裡切入，**為什麼是這個切入點**？中心主張是什麼，**為什麼值得**？選了什麼方法，**為什麼是它、為什麼會成功**、排除了什麼？要證明什麼才算成立，**為什麼這樣評估**？用什麼統計與視覺化，**為什麼這樣呈現**？

| 項目 | 是什麼 | 為什麼 | 出處 |
|---|---|---|---|
| 切入點 | {{axis.entry_point.what}} | {{axis.entry_point.why}} | {{axis.entry_point.locator}} |
| 中心主張 | {{axis.central_claim.what}} | {{axis.central_claim.why_matters}} | {{axis.central_claim.locator}} |
| 方法選擇 | {{axis.method_choice.what}}；排除：{{axis.method_choice.alternatives}}；必要性（換一種方式會失效嗎）：{{axis.method_choice.necessity}}；卡關／未成的嘗試：{{axis.method_choice.dead_ends}} | {{axis.method_choice.why}} | {{axis.method_choice.locator}} |
| 評估計畫 | 要證明：{{axis.evaluation_plan.what_to_show}}；指標：{{axis.evaluation_plan.metrics}}；門檻：{{axis.evaluation_plan.criteria}}；對照：{{axis.evaluation_plan.controls}}；預期：{{axis.evaluation_plan.expected}} | {{axis.evaluation_plan.why}} | {{axis.evaluation_plan.locator}} |
| 呈現 | 統計：{{axis.presentation.stats}}；視覺化：{{axis.presentation.visuals}}；順序：{{axis.presentation.order}} | {{axis.presentation.why}} | {{axis.presentation.locator}} |

## 3. 故事線（作者怎麼講的，每一拍帶為什麼）

| 拍 | 說了什麼 | 為什麼這一拍在這裡 | 出處 |
|---|---|---|---|
{{#storyline}}| {{beat}} | {{what}} | {{why}} | {{locator}} |
{{/storyline}}

## 3b. 這篇怎麼說完一個研究故事（`talk.story_arc`——可以學的寫法）

- 一句話的故事（And–But–Therefore）：{{talk.story_arc.spine}}

| 拍 | 作者在這裡做了什麼 | 為什麼對讀者有效 | 出處 |
|---|---|---|---|
{{#talk.story_arc.craft}}| {{beat}} | {{move}} | {{why_it_works}} | {{locator}} |
{{/talk.story_arc.craft}}

## 4. 偏離處（講出來的故事哪裡離開了主軸）

| 在哪 | 類別 | 偏離了什麼 | 為什麼要緊 | 原文（逐字） | 出處 |
|---|---|---|---|---|---|
{{#drift}}| {{where}} | `{{kind}}` | {{what_drifted}} | {{why_it_matters}} | 「{{quote}}」 | {{locator}} |
{{/drift}}

（若有深讀 run：引用其判定——{{distill_verdicts}}）

- 偏離清單逐條走（`narrative-axis.md` §4 十類，找到／沒有 — `coverage.drift_checklist`）：{{drift_checklist_flat}}
- 探針異常（`source/structure.json`）的歸類：{{anomalies_classified}}
- 沒用到的單元與原因（`coverage.skipped`）：{{coverage_skipped}}

## 5. 一頁式素材

- Keypoint 條（渲染器直接印 `logic.keypoint`，角色可 hover；`展開解讀` 攤開 §1 的解讀與角色表；不再有 keypoint_box）：{{logic.keypoint}}
- 五格表：Structure {{onepage.table.structure}} ／ Features {{onepage.table.features}} ／ Method {{onepage.table.method}} ／ Result {{onepage.table.result}} ／ Conclusion {{onepage.table.conclusion}}
- 圖（依故事線順序，每張都是證據圖 `kind: evidence`——示意／動機圖只進多頁式；為什麼選它）：{{onepage_figures_flat}}

## 6. 多頁配置（Keypoint 頁在前，之後照論文分項；每頁圖＋短文字重點）（`story` 模式＝十篇一頁：本節與 §7 寫「story 模式不產出」，不留空白佔位）

| # | 分項 | 層 | 標題 | 圖 | 這頁回答（asks） | 帶走（takeaway） | 出處 |
|---|---|---|---|---|---|---|---|
{{#pages}}| {{n}} | {{section}} | {{layer}} | {{title}} | {{figure}} | {{asks}} | {{takeaway}} | {{locator}} |
{{/pages}}

（每頁備註的形狀：bridge 接上一頁的問題 → 帶讀這張圖（看什麼／會看到／對照／所以）→ 為什麼 → 帶走 → 丟出下一頁的問題；重點條是白板上的字，不唸。）

## 7. 口述要點（實驗室慣例）

- 開場：{{talk.opening}}
- 分段句：{{talk.outline}}
- 結尾：研究依據 {{talk.closing.basis}} ／ 對後續的幫助 {{talk.closing.help}} ／ 下一步 {{talk.closing.next}}
- 被問時：{{if_asked_flat}}

## 8. 詞彙表（頁面上出現的每個專有名詞）

{{terms_flat}}

## 9. 附錄：過程紀錄

{{process_log}}

相關：[[home]]
