---
xi: 1
what: "【學習紀錄】Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics — 閱讀分析過程：key point 先行、IMRAD 拆解、主張審計、圖表判讀、寫作解剖、定位 (paper-distill reading record: the learning document)"
tags: [paper-distill, reading-record, literature]
aliases: ["Placeholder 2026 閱讀紀錄", "Placeholder2026_wax-delay-bridges", "Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics reading record"]
date: 2026-11-03
status: live
kind: literature
source: "file: Placeholder2026_wax-delay-bridges/source/paper.pdf"
verified: "read-in-full 2026-11-03 by Claude Sonnet 5.5; locators spot-checked by Presenter: pending"
review-when: "a second paper contradicts C1, or the presenter's own key point differs from §0"
domain: []
promoted-to: "-"
---

# 【學習紀錄】閱讀分析過程：Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics

> **這份文件是什麼**：我讀這篇論文的完整過程與判斷，給我自己學習用（怎麼讀、怎麼審、怎麼抽精華）。
> 它不是講稿，也不是給聽眾看的頁面——那些由 `paper-story` 產出：論文說明頁 `paper-explainer.html`，其中「口述稿」一節就是報告時我要說的話（因人而異，改成自己的話）。

| 檔案 | 用途 | 讀者 |
|---|---|---|
| `reading-record.md`（本檔） | 學習紀錄：閱讀分析過程 | 我 |
| `paper-explainer.html`（`paper-story` 產出，有跑才有） | 論文說明頁（練習・複習用），含「口述稿」一節 | 我（上台前） |
| `cards.json` | 機器契約：本檔的資料來源（`paper-story` 也讀它） | 工具 |

`paper-distill` · run `Placeholder2026_wax-delay-bridges` · depth `full` · 來源類型 paper · 取得層級 full · 修訂 r1

> 讀法：每一節先列「自問」，再給答案。每句話帶來源標記 —— `[author]` 論文說的（有出處）、`[verified]` 我對照圖表確認過、`[inferred]` 我從論文材料推論、`[assumed]` 未驗證的假設。出處寫 `p.N / Fig.N / Table N / Eq.N / §N`；找不到就寫「無法定位」。

## 0. 審計摘要先行（這篇的證據撐得住什麼）

- C1（會被引用的那句）：[author] 1–5 mm 的蠟橋使前緣延遲 42–612 s，延遲大致依橋長平方成長，變異低於 15 %（單一條件：23 °C、45 % RH，每長度 5 個元件）。 —— 證據種類 E1 · 判定 **provisional** · 仍缺 第二批紙／蠟、不同日期的重複；比較 t = a·L^b 或 a·L + c 的替代擬合；每長度只有 5 個元件，CV 的信賴區間未報。
- 站得住的：[verified] 在 23 °C、45 % RH、5 個元件／長度下，延遲隨橋長單調上升且大致遵循平方（Fig. 2）；變異點估計低於 15 %（Fig. 3）。
- 還缺的：[inferred] 其他濕度／批次的重複、與糖障壁並排的對照、比 L² 更好的替代模型、兩步驟檢測的反向對照與足夠的 n。
- 對我們的意義：我們跑多步驟紙基檢測：若要靠印刷長度排序試劑，這篇給了一個零額外材料的候選與一組可抄的設計數字，但只能當成『在 23 °C、45 % RH 一個條件下可能可行』的起點。[inferred]
- Key point（邏輯抽取）不在本檔：→ `paper-story` 的 `narrative-record.md`／`story.json`（run：Placeholder2026_wax-delay-bridges（同資料夾 narrative-record.md）；若尚未跑，寫「未跑」）

<details><summary>先寫你的版本（看下面審計之前，先寫下你認為這篇「證據撐得住什麼」）</summary>

> __

</details>

## 1. 取用卡 (Intake)

- 自問：Abstract 說要解決什麼？Conclusion 主張什麼？Introduction 宣稱什麼貢獻？只准指一張圖時作者會指哪張？我為什麼挑這篇？
- 書目：Ada Placeholder；Ben Fixture；Cleo Mockridge，《Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics》，Journal of Imaginary Microfluidics 1, 101-108 (fictional) 2026，DOI 
- Abstract 的問題：[author] 紙基裝置多半讓所有試劑同時到達，多步驟檢測需要依序到達（Abstract, p.1）。
- Conclusion 的主張（待測試的那句）：[author] 延遲 42–612 s、變異低於 15 %、不加材料，且兩步驟檢測訊號為同時給藥的 1.8 倍；結論是「wax delay bridges are a practical way to sequence reagents on paper」（§5, p.4）。這是整篇要被測試的那一句，不是要接受的摘要。
- Introduction 宣稱的貢獻：[author] 問「已經定義通道的蠟印步驟，能不能同時定義時間」；若前緣依橋長平方變慢（Washburn 型模型），延遲就變成印刷尺寸而非材料性質（§1, p.1）。
- 作者會指的那張圖：Fig. 2（延遲 vs 橋長，含二次擬合）：作者若只准指一張圖，會指這張——它同時承載「長度決定延遲」與「平方關係」兩個宣稱（p.2）。[inferred]
- 判斷：deep —— 相關度高、方法權重高（結果取決於橋這個設計）、但證據深度低（每長度 5 個元件、單一濕度、兩步驟檢測 n = 3）：依標尺仍 deep，但審計判定會限制能借多少。[inferred]
- 為什麼挑這篇：Presenter 所在的實驗室要跑多步驟紙基檢測（試劑必須依序到達）。這篇宣稱可以把「等待時間」做成一個印出來的長度，想先看它的證據撐得住什麼、哪一句可以借去排序試劑、哪一句不能。[inferred]
- 與實驗室的關聯（domain profile：）：多步驟紙基檢測的試劑排序：這篇給出一個零額外材料的候選計時元件，但目前只在 23 °C、45 % RH 一組條件下量過。[inferred]
- 深度標尺（相關度／方法權重／證據深度，各 high・mid・low）：high ／ high ／ low

## 1b. 詞彙表 (Glossary) — 第一遍先找出這篇 paper 的主角

- 自問：哪些詞反覆出現（標題／摘要／簡介先看）？它是主角、解釋框架、領域共用、還是本文特有？我目前還不懂它什麼？第二遍要追問它什麼？
- 工具：`scripts/glossary.py` 給的是頻率與首次出現頁（bytes）；分類與「還不懂」是我填的。留 10–15 個。

| 詞 | 頻率 | 四類 | 目前還不懂什麼 | 第二遍要追問什麼 |
|---|---|---|---|---|
| wax delay bridge | 5 | coined | 它與常見的蠟障壁／蠟印刷延遲元件差在哪裡？『partially fused』如何控制？ | 本文有沒有跟其他蠟障壁比較？熔融程度的量測在哪？ |
| partially fused | 2 | coined | 『部分』是多少？哪個參數（溫度、時間）控制它？ | §2.1 的 120 °C/60 s 與全阻隔的 150 °C/120 s 之間有沒有掃描？ |
| delay time | 2 | subject | 無橋基準的值是多少、怎麼量？ | §2.2 的基準取了幾次？ |
| bridge length | 5 | subject | 寬度與厚度是否固定？ | L 是怎麼控制的，印刷解析度是多少？ |
| Washburn | 2 | frame | 本文用的是原式，還是只借它的 L² 形狀？ | k 的物理成分有沒有被分別量測？ |
| permeability | 3 | frame | 橋的滲透率有沒有被直接量過？ | 與 k 的關聯在哪裡驗證？ |
| sugar barrier | 4 | field | [3] 的 CV 是怎麼定義、n 是多少？ | 能否並排量測？ |
| magnetic valves | 1 | field | 『加零件』的成本沒有量化。 | Table 1 的『added parts and assembly』是否有成本數字？ |
| coefficient of variation | 2 | field | n = 5 的 CV 信賴區間多寬？ | 圖上為什麼沒有誤差棒？ |
| two-step assay | 3 | subject | 檢測的化學是什麼？ | 試劑 A 與 B 各是什麼？ |
| simultaneous delivery | 4 | field | 是作者自己做的基準（self-eval）。 | 有沒有更合理的基準，例如糖障壁排序？ |
| detection zone | 2 | field | 區域大小與判定準則沒寫。 | 前緣到達的判定準則是什麼？ |
| fluid front | 2 | field | 前緣是用肉眼還是影像處理判定？ | §2.2 的 30 fps 影片如何轉成時間？ |

- 本文特有（coined）的詞：是新概念，還是舊概念換名字？→ §4 slop 診斷「名詞替換」的輸入清單。

## 2. 骨架卡 (Skeleton) — IMRaD 是思考順序，不是格式

- 自問：每一節在整篇論證裡的「功能」是什麼？作者放了什麼材料？我理解了什麼？哪一段放錯地方（為什麼放在這裡）？Results 有沒有偷渡解讀、Discussion 有沒有偷渡新資料？

| 區段 | 它要完成什麼 | 作者放了哪些材料 | 我目前理解什麼 |
|---|---|---|---|
| Introduction（問題／前人／缺口） | 建立問題、前人、缺口，並把假說（t 正比於 L²）預先說出。 | 紙基裝置便宜無泵 [1]；多步驟需要依序給藥；兩類計時元件（糖障壁 [3]、機械／磁閥 [2]）各有缺點；假說：延遲成為印刷尺寸（§1, p.1）。 | [verified] 缺口三要素都看得到；但「糖障壁變異大」只有引用 [3]，作者自己沒有並排測。 |
| Methods（工具／採樣／流程／模型） | 讓研究可重複：裝置、量測、模型、兩步驟檢測。 | §2.1 通道 2 mm × 40 mm、全阻隔 150 °C 120 s、橋 L = 1–5 mm、120 °C 60 s；§2.2 20 µL 染色緩衝液、30 fps、每長度 5 個元件、23 °C 45 % RH；§2.3 t = k·L² 最小平方；§2.4 兩步驟檢測各 3 個元件（p.1–2）。 | [verified] 幾何與溫度時間給得完整；缺紙張批次、蠟種類與厚度、前緣判定準則、檢測是哪一種化學、綠色通道如何換算強度。 |
| Results（What，客觀） | 報告發現（What），不解讀。 | §3.1 延遲 42→612 s、k = 24.6 s/mm²、R² = 0.97、SD 4 s→81 s（Fig. 2）；§3.2 CV 9.3–13.2 %（Fig. 3、Table 1）；§3.3 0.38 ± 0.05 vs 0.21 ± 0.04 a.u.（Fig. 4）。 | [verified] 數字與圖一致；§3.2 的「低於文獻 25 %」已經在比較，不只是報告。 |
| Discussion（Why，詮釋） | 詮釋與限制。 | 二次趨勢支持多孔低滲透率區段的圖像；SD 隨長度放大，長延遲需更嚴的加熱控制；只量過一種濕度；糖障壁數字取自文獻（§4, p.4）。 | [verified] Discussion 自己承認了兩個最大破口（單一濕度、借來的基準），但 Abstract 與 Conclusion 沒有把它們帶進去。 |

- 缺口三要素：問題 多步驟紙基檢測需要試劑依序到達 [author]。 ／ 前人 糖障壁（變異大 [3]）與機械／磁閥（加零件 [2]）[author]。 ／ 缺口 沒有「不加材料、不加零件、可重現」的計時元件——作者宣稱蠟印刷步驟本身可以補上 [author]。
- Method 四元素：工具 蠟印刷＋加熱於層析紙；錄影 30 fps（§2.1–2.2）。 ／ 採樣 5 個橋長 × 5 個元件；兩步驟檢測 2 組 × 3 個元件（§2.2, §2.4）。 ／ 流程 20 µL 染色緩衝液置於入口，量前緣比無橋通道多出的時間（§2.2）。 ／ 模型 Washburn 關係 t = k·L²，k 以最小平方擬合五個平均值（§2.3）。
- 放錯位置的段落（為什麼放在這裡）：where: §1 的引用順序 [1]、[3]、[2]（p.1） / looks_like: 引用編號未依首次出現順序 / why_here: [inferred] 先講糖障壁 [3] 再講閥 [2]，敘事順序優先於編號；小問題，但顯示參考文獻在寫完文字後才排。；where: Table 1（p.3） / looks_like: Results 裡的比較表，三欄的來源不同 / why_here: [verified] 它夾在 §3.2 與 §3.3 之間，用結果段的位置承載文獻比較；蠟橋欄是自己量的，糖障壁與閥欄是文獻數字。
- What／Why 混用處：§3.2「The coefficient of variation stays between 9.3 % and 13.2 %」之後立即拿來與文獻 25 % 比較，是 Results 中的詮釋 [verified]。；§4 Discussion 才第一次說「All measurements were made at one humidity」，而 Abstract 已說 robust across ambient humidity [verified]。

## 3. 核心卡 (Core) — 這篇研究如何成立？還缺什麼？

- 自問：研究問題是什麼、為何重要？用什麼設計、資料哪來、怎麼分析？發現什麼？有哪些限制？作者宣稱帶來什麼新的東西？
- RQ：[author] 蠟印刷步驟能不能同時決定試劑到達的時間（§1）。 · Methods：[author] 部分熔融的蠟橋＋Washburn 型 L² 模型＋兩步驟檢測示範（§2）。 · Results：[author] 1–5 mm 橋給 42–612 s 延遲；CV 9.3–13.2 %；兩步驟訊號 1.8 倍（§3）。 · Limitations：[author] 只量過一種濕度；糖障壁變異取自文獻；SD 隨長度成長（§4）。[inferred] 另有：n = 5 與 n = 3、單一檢測、無反向對照。
- 宣稱的貢獻 `[author]`：[author] 「A partially fused wax bridge turns timing into a printed length.」（§5, p.4）
- 如何成立：[verified] 在 23 °C、45 % RH、5 個元件／長度下，延遲隨橋長單調上升且大致遵循平方（Fig. 2）；變異點估計低於 15 %（Fig. 3）。 · 還缺什麼（留給 §4 裁決）：[inferred] 其他濕度／批次的重複、與糖障壁並排的對照、比 L² 更好的替代模型、兩步驟檢測的反向對照與足夠的 n。

| 前人方法 | 作者說不足之處 | 公平嗎 `[inferred]` |
|---|---|---|
| Dissolvable sugar barriers [3] | delay varies strongly from device to device (§1) | [inferred] 部分公平但不可驗證：25 % 是文獻數字，且 [3] 的作者之一就是本文作者；沒有並排量測。 |
| Mechanical or magnetic valves [2] | add parts and assembly steps that undo the low cost of paper (§1) | [inferred] 這是成本論證而非精度論證——Table 1 自己寫閥的變異低於 5 %，比蠟橋好；作者沒有量化「額外成本」。 |

**前提盤點（Assumptions）**——自問：這篇把哪些前提當成真的、沒有去測？寫在哪裡（還是根本沒寫）？如果它是假的，哪條主張／哪一步邏輯會倒？

| 前提 | 出處（或 implicit） | 有測嗎 | 若為假，倒的是 | 來源 |
|---|---|---|---|---|
| 蠟橋可視為均質、低滲透率的多孔區段 (homogeneous porous section of lower permeability) | §2.3 p.2 | no | C2 的 Washburn 機制說明與 C1 的 L² 外推都會倒；模型只用平均值擬合、沒有孔隙結構或滲透率的獨立量測。 | author |
| 23 °C、45 % RH 的結果可以代表使用現場的濕度條件 (ambient humidity) | §4 p.4 | no | C3 的「robust across ambient humidity」與 15 分鐘延遲都失去依據；作者自己預期 k 會隨濕度改變。 | author |
| 文獻中糖障壁的 25 % 變異 (sugar barrier variation) 與本文量測條件可比 | §4 p.4 | no | C4 的「比糖障壁更可重現」不成立；CV 的定義、n、條件在 [3] 中都不在本文可核對範圍。 | author |
| 20 µL 染色緩衝液量到的延遲 (dyed buffer delay) 可預測兩步驟檢測中試劑 B 的延遲 | implicit | no | C5 的 1.8 倍是否來自『延遲』而非橋的其他效應無法歸因。 | inferred |

## 4. 主張審計 (Claim audit) — 證據夠不夠，不只在不在

- 自問：這篇會被引用的是哪句主張？哪張圖／表撐它？那是哪一種證據？還缺什麼？我最多能說到什麼程度？作者是自己跟自己比嗎？有沒有「應該失敗」的對照？

| ID | 主張 (claim) | 類型 | 觸及範圍 (reach) | 證據（出處 → 內容） | 種類 | 仍缺什麼 | 判定 | 來源 | 備註 |
|---|---|---|---|---|---|---|---|---|---|
| C1 | [author] 1–5 mm 的蠟橋使前緣延遲 42–612 s，延遲大致依橋長平方成長，變異低於 15 %（單一條件：23 °C、45 % RH，每長度 5 個元件）。 | specific | direction、magnitude | Fig. 2 · §3.1 p.2 → 平均延遲 ± SD 對橋長（n = 5）＋虛線 t = k·L²（k = 24.6 s/mm²）；42 s → 612 s [verified, 圖上讀值]。；Fig. 3 · §3.2 p.2–3 → 各長度 CV 約 9.3–13.2 %，全部在 15 % 線下 [verified]。 | E1 | 第二批紙／蠟、不同日期的重複；比較 t = a·L^b 或 a·L + c 的替代擬合；每長度只有 5 個元件，CV 的信賴區間未報。 | provisional | verified | paper-measured：42 s、612 s、k = 24.6、CV 9.3–13.2 %。re-derived：由文中兩個端點 42 s 與 612 s 得局部冪次 ln(612/42)/ln 5 ≈ 1.66，不是 2；圖上 L = 1–3 mm 的點落在虛線上方約 15–20 s（4–5 個 SD 以上），L = 4–5 mm 才貼線 [verified, 圖上讀值，約略]。R² = 0.97 只有 5 個平均值、單一參數過原點，不能區分 L² 與 L^1.7。n = 5 的 CV 以 χ² 估 95 % 區間約為點估計的 0.6–2.9 倍（9.3 % → 約 5.6–27 %）[re-derived]，所以「低於 15 %」是點估計、不是上界。可以說：在這一組條件下觀察到。 |
| C2 | [author] 二次趨勢支持「橋是低滲透率多孔區段」的 Washburn 型圖像，因此延遲是印刷尺寸而非材料性質。 | mechanism | mechanism、causation | §2.3 p.2 → t = k·L² 由 Washburn 關係推得，k 收納黏度、表面張力、有效孔徑——一個擬合參數。；§4 p.4 → 「The quadratic trend supports the picture」——以擬合優度回頭支持機制。 | E3 | 橋的滲透率或孔隙結構的獨立量測（例如不同熔融度、不同加熱時間的橋）；一個應該失敗的對照，如未加熱的橋或完全熔融的橋；替代模型比較。均質多孔區段 (homogeneous porous section)、低滲透率 (lower permeability) 是未測前提。 | hypothetical | inferred | one-sided：只有『應該成功』的情況（不同長度的同種橋）；沒有會隔離機制的反例。self-eval：k 是用同一批五個平均值擬合，再用同一批平均值說擬合很好。k 的各物理成分（黏度、表面張力、孔徑）從未分別量測。framework 層：Washburn 是借來的標準模型，不是本文新貢獻。可以說：若模型成立則；不可以說：explains／because。 |
| C3 | [author] 該方法提供最長 15 分鐘的延遲，且在環境濕度範圍內穩健（Abstract）。 | prediction | magnitude、generality | §3.1 p.2 → 本文實測最大延遲 612 s ≈ 10.2 分鐘（L = 5 mm）；Abstract 的 15 分鐘 = 900 s 沒有任何量測點。；§2.2 p.1 · §4 p.4 → 只在 23 °C、45 % RH 量測；Discussion 自己說「we expect the constant k to shift at other humidities」。；Table 1 p.3 → 「delay 60-900 s」這個 900 s 出現在糖障壁那一列（文獻值），不是蠟橋那一列（42-612 s）。 | none | L ≳ 6 mm 的量測（由 k = 24.6 反推 900 s 需約 6.0 mm，超出所測範圍 [re-derived]，而且 SD 預期更大）；至少三種濕度的重複。未測前提：現場濕度與 23 °C／45 % RH 等價 (ambient humidity)。 | withhold | author | promotional：「robust」「up to」。Abstract 與本文衝突兩處：15 分鐘 vs 實測 612 s；robust across humidity vs 作者自己的 §4 預期 k 會漂移。兩者都不是數據，是 Abstract 的外推或借自比較欄的數字。只能說：claimed, not shown。 |
| C4 | [author] 蠟橋比糖障壁更可重現（CV < 15 % vs 約 25 %），並且不需要額外材料，是三種計時元件中成本最低的選擇（Fig. 3、Table 1）。 | testable | magnitude、practical | Fig. 3 · §3.2 p.3 → 蠟橋 5 個 CV 長條對 [3] 的 25 % 灰色長條——灰條是文獻值，不是本文量測 [verified]。；Table 1 p.3 → 三欄混合：蠟橋 42–612 s／9–13 %（本文量測），糖障壁 60–900 s／約 25 %（[3]），機械閥 5 % 以下（[2]）[verified, 頁面影像：它是一段文字，不是格線表]。；§4 p.4 → 「taken from the literature rather than measured side by side with our devices」——作者自己承認。 | E2 | 糖障壁與蠟橋在同一紙、同一溫濕度、同一 n 並排量測；以及一個成本或組裝時間的量化。未測前提：文獻的 CV 與本文可比 (sugar barrier variation comparable)。 | withhold | author | term substitution check：『wax delay bridge』與『partially fused』是本文特有的詞（coined），[inferred] 概念上接近紙基裝置常見的蠟障壁／蠟印刷延遲元件，需要文獻查核才能判定是新概念還是換名；本文沒有與蠟障壁做比較。比較是 cross-study：[3] 的作者之一 C. Mockridge 也是本文第三作者（自我引用）。n = 5 的 CV 區間與 25 % 重疊（上限 27–38 %）[re-derived]。機械閥的變異低於 5 %，比蠟橋好；『no extra material』只算了材料，沒算印刷與加熱的步驟時間。「no moving part」為真但不是對手所說的缺點。只能說：claimed, not shown。 |
| C5 | [author] 把試劑 B 放在 3 mm 橋之後，兩步驟顏色檢測的訊號為同時給藥的 1.8 倍（Abstract 寫成「doubles」）。 | specific | magnitude、causation、significance | Fig. 4 · §3.3 p.3 → 兩根長條：同時給藥 0.21 ± 0.04、定時釋放（L = 3 mm）0.38 ± 0.05 a.u.；y 軸從 0 開始、誤差棒為 SD、每組 3 個元件 [verified]。；§2.4 p.2 → n = 3 each；強度由照片綠色通道讀取。 | E1 | 更多元件（n = 3 太小）、反向對照（一個『不該改善』的檢測，或把橋換成同長度的非延遲區段）、是什麼檢測與 A、B 是什麼。未測前提：緩衝液延遲預測試劑延遲 (dyed buffer delay)。 | provisional | verified | paper-measured：0.38、0.21。re-derived：0.38/0.21 = 1.81（與文中 1.8 相符）；以 Welch t 檢定（假設 ± 為樣本 SD、n = 3）t ≈ 4.6、df ≈ 3.8、p ≈ 0.011，所以在這三個元件上差異是真的，但對 n = 3 的單一檢測；『doubles』是 1.8 的湊整，promotional。誰比較：自己對自己（同時給藥是作者自己的基準 → self-eval）。positive-only。可以說：在 3 個元件、一個檢測上觀察到 1.8 倍。 |

- 這篇實際做了什麼：新框架 否 ／ 新名詞 是 ／ 具體案例 是 ／ 實驗或推導 是 —— [inferred] 新名詞（wax delay bridge）＋ 一個示範檢測（n = 3）＋ 一組實驗與一個擬合。沒有新框架：Washburn 是借來的標準關係。
- 觸及範圍欄填 `reach` 的英文代碼（以「、」分隔）；主張宣稱了哪幾軸（方向／大小／因果／機制／真實元件／普遍性…），判定逐軸套用，證據撐不到的那一軸寫進「仍缺什麼」（定義見 `~/.claude/references/writing-norms/claim-reach.md` §1）
- 判定→措辭：provisional「在 N 個元件、X 條件下顯示」／ leaning「傾向、可能」／ hypothetical「若模型成立則」／ withhold「宣稱、未顯示」

## 5. 圖表判讀 (Figure cards) — 先看圖，再看作者怎麼說

- 自問：這張圖回答哪一個問題？要看的三件事？它實際顯示什麼？撐哪條主張？座標軸／誤差棒／樣本數／基準線有沒有問題？這種圖看不到什麼？

### F1 · p.1 Fig. 1
- 回答的問題：裝置長什麼樣、蠟橋放在哪裡？ · 要看的三件事：橋位於入口與檢測區之間、寬度與通道相同、標註 L = 1–5 mm、120 °C 60 s、示意圖有沒有比例
- 它顯示 `[verified]`：[verified, 已看過裁圖] 一張示意圖：左端藍色方塊標「inlet (reagent B)」，中段一塊褐色方塊標「wax delay bridge, length L」，右端綠色方塊標「detection zone」，三者以淺色通道連接，通道標「cellulose channel (w = 2 mm)」，下方雙向箭頭標 L = 1–5 mm、120 °C for 60 s。沒有尺度條，沒有試劑 A。 · 撐的主張：C1（說明裝置） · 注意：示意圖不是照片：橋的實際邊緣、蠟滲入深度、是否均質都看不到——這正是 C2 的未測前提。入口標為 reagent B，但 §2.2 的量測是把染色緩衝液放在入口，圖上沒有試劑 A 的位置。 · 看不到：示意圖看不到熔融程度（『partially fused』的核心）與任何變異。
### F2 · p.2 Fig. 2
- 回答的問題：延遲時間是否隨橋長按平方成長？ · 要看的三件事：資料點與虛線的殘差有沒有系統性、誤差棒隨長度如何變化、擬合是否過原點、有幾個點
- 它顯示 `[verified]`：[verified, 已看過裁圖] 橫軸橋長 1.0–5.0 mm、縱軸延遲 0–700 s。五個藍點（n = 5）約在 42、≈117、≈236、≈393、612 s，誤差棒從 L = 1 的幾乎看不見（SD 4 s）長到 L = 5 的 ±81 s；橘色虛線 t = k·L²（R² = 0.97）。L = 1、2、3 mm 的點都在虛線上方約 15–20 s，L = 4、5 mm 的點落在線上。圖例只寫 n = 5。 · 撐的主張：C1；對 C2 只是一致、不是機制證據 · 注意：只有 5 個平均值、一個過原點的參數；殘差呈系統性（短橋全部在線上方）；沒有 log-log 圖或替代模型；誤差棒是 SD，不是 SE。局部冪次約 1.66 [re-derived]。 · 看不到：平均值圖看不到個別元件的散佈（只有 SD），也看不到 L > 5 mm 的行為（Abstract 的 15 分鐘要靠外推）。
### F3 · p.3 Fig. 3
- 回答的問題：延遲的變異有多大、比糖障壁小嗎？ · 要看的三件事：CV 隨長度的趨勢、灰色長條是誰量的、15 % 虛線代表什麼（門檻還是引用）
- 它顯示 `[verified]`：[verified, 已看過裁圖] 長條圖：1–5 mm 的藍色長條約 9.5、9.3、10.2、11.6、13.2 %，全部低於橘色點線 15 %；最右側灰色長條「sugar barrier (ref. [3])」約 25 %。y 軸從 0 開始。沒有誤差棒。 · 撐的主張：C1（變異）、C4（比較） · 注意：灰色長條是文獻值、不是本文量測；藍色長條沒有信賴區間（n = 5 的 CV 區間很寬）；15 % 虛線是作者自己畫的門檻，不是標準。CV 隨長度上升（9.3→13.2 %），這個趨勢指向 L > 5 mm 時超過 15 %。 · 看不到：CV 看不到絕對散佈：5 mm 的 SD 是 81 s（約 1.4 分鐘）；也看不到批次間（run-to-run）變異。
### F4 · p.3 Fig. 4
- 回答的問題：延遲試劑 B 有沒有讓兩步驟檢測的訊號變強？ · 要看的三件事：基準（同時給藥）是否合理、誤差棒是什麼、n 是多少、y 軸是否從 0 開始
- 它顯示 `[verified]`：[verified, 已看過裁圖] 兩根長條：灰色「simultaneous delivery」約 0.21 a.u.（誤差棒約 0.17–0.25）；藍色「timed release (L = 3 mm)」約 0.38 a.u.（約 0.33–0.43）。y 軸 0.0–0.5、從 0 開始。圖上沒有標 n，n = 3 與 SD 在圖說裡。 · 撐的主張：C5 · 注意：n = 3；只有一個檢測；兩個條件，沒有第三條件（例如 3 mm 的非延遲區段）；誤差棒大約是差距的一半，單看圖不能判斷。 · 看不到：兩條長條看不到過程：延遲的時間點、試劑 A 結合了多少、是不是橋本身（而不是時序）改變了訊號。
### F5 · p.3 Table 1
- 回答的問題：三種計時元件如何比較？ · 要看的三件事：哪些欄位是本文量測、哪些是文獻值、延遲範圍的上限、『added material』欄的定義
- 它顯示 `[verified]`：[verified, 已看頁面影像 p003：Table 1 在 PDF 裡是一段文字，不是格線表，所以 crop 失敗、沒有裁圖] 三行：蠟橋 delay 42-612 s、variation 9-13 %、no added material；糖障壁 [3] delay 60-900 s、variation about 25 %、added sugar layer；機械閥 [2] delay set by the user、variation below 5 %、added parts and assembly。 · 撐的主張：C4；同時揭露 C3 的 15 分鐘（900 s）是糖障壁那一列的上限 · 注意：混合本文量測與文獻數字，同一表格沒有標記來源；延遲上限 900 s 與 Abstract 的「up to 15 minutes」相同。 · 看不到：文字化的表看不到單位與 n；也沒有成本欄的量化。

## 6. 寫作解剖 (Writing craft) — 從這篇學怎麼寫一篇論文

- 自問：作者怎麼從問題走到主張（論證鏈）？方法段給了讀者什麼、我照著做還缺什麼？設計資料有哪些數字？每張圖是為了證明什麼而這樣畫？結果的數字怎麼報？限制怎麼講？哪幾句值得借？

**論證鏈**

| 步驟 | 我的話 | 論文裡做這件事的句子在 |
|---|---|---|
| problem | 多步驟檢測需要試劑依序到達，紙裝置卻同時送達。 | p.1 §1 |
| gap | 糖障壁變異大、閥加零件，沒有便宜又可重現的計時元件。 | p.1 §1 |
| hypothesis | 若前緣依橋長平方變慢，延遲就是印刷尺寸而非材料性質（Washburn 型預測）。 | p.1 §1 |
| approach | 在蠟通道上印一段只部分熔融的橋，長度 1–5 mm。 | p.1 §2.1 |
| evidence | 量延遲對長度、CV、兩步驟檢測，三組結果各一張圖。 | p.2–3 §3.1–3.3 |
| claim | 蠟橋把計時變成印刷長度，是排序試劑的實用方法。 | p.4 §5 |

- 方法段給了什麼：通道 2 mm × 40 mm；全阻隔 150 °C 120 s；橋 L = 1–5 mm、120 °C 60 s；20 µL 染色緩衝液；30 fps；每長度 5 個元件；23 °C、45 % RH；t = k·L² 最小平方；兩步驟檢測各 3 個元件，綠色通道強度。
- 照著做還缺什麼：紙的型號與批次、蠟的種類與印刷厚度、前緣到達檢測區的判定準則、無橋通道的基準延遲是怎麼取的、兩步驟檢測的化學與 A／B 試劑、強度的換算與背景扣除。
- 呈現順序（好不好）：裝置 → 量測 → 模型 → 檢測：照結果的順序排，好跟；但把 Fig. 1 放在 Introduction 末尾而不是 Methods，讀者要跳頁。
- **設計資料表** `[author]`：channel width = 2 mm、length = 40 mm；full barrier 150 °C/120 s；bridge L = 1–5 mm at 120 °C/60 s；sample 20 µL；measure at 23 °C/45 % RH；k = 24.6 s/mm²；assay bridge 3 mm [author, p.1–2 §2.1–2.4, §3.1]

**圖證設計**

| 圖 | 為了證明什麼 | 為什麼選這種圖 | 註 |
|---|---|---|---|
| p.2 Fig. 2 | t 與 L² 成正比 | 點＋誤差棒＋擬合線：同時給資料與模型；沒有殘差圖或 log-log。 | [inferred] 線性軸上的拋物線，肉眼很容易接受；要檢驗冪次，log-log 更誠實。 |
| p.3 Fig. 3 | 可重現：比自己的門檻低、比舊方法低 | 長條圖＋一條門檻線＋一根灰條。 | [inferred] 灰條與藍條用同一軸，視覺上把『文獻值』與『本文量測』放在同等地位。 |
| p.3 Fig. 4 | 延遲帶來訊號提升 | 兩條長條、y 軸從 0。 | [inferred] 誠實的軸；但只有兩條件，視覺差距大於統計把握。 |

- 結果怎麼寫：每個結果句帶平均值與 ± SD，並指向圖（例如「the standard deviation is 4 s at 1 mm and 81 s at 5 mm」，p.2）：好的地方是 n 在圖說裡報；壞的地方是 R² 與 CV 都沒有信賴區間，而且 Abstract 把『1.8 倍』寫成『doubles』。
- 限制怎麼寫：限制放在 Discussion，簡短、誠實（單一濕度、基準取自文獻、SD 隨長度成長）。分類：單一濕度＝真正的邊界（約束 → 約束 C3 的 generality → 不可以結論到其他濕度）；『基準取自文獻』＝可修的缺陷（並排量測即可）；『SD 隨長度成長』＝真正的邊界。問題在於這些限制沒有回到 Abstract 與 Conclusion。
- 可借句型（≤15 字逐字＋出處＋用途）：「yet most paper devices deliver everything at once」（p.1 Abstract；gap 陳述：一個 yet 把現狀與需求對立）；「the delay becomes a printed dimension rather than a material property」（p.1 §1；貢獻宣稱：把假說說成『若…則』）；「the standard deviation is 4 s at 1 mm and 81 s at 5 mm」（p.2 §3.1；結果句：數字＋不確定度＋條件）；「All measurements were made at one humidity」（p.4 §4；限制句：直接、不迂迴）；「taken from the literature rather than measured side by side with our devices」（p.4 §4；承認基準來源：值得學，但要同時改 Abstract）
- 我的改寫練習：原句（Abstract）：The approach provides delays of up to 15 minutes, is robust across ambient humidity, and doubles the signal of a two-step colour assay. 改寫：Bridges of 1 to 5 mm delayed the fluid front by 42 to 612 s at 23 °C and 45 % RH; a 3 mm bridge raised the signal of one two-step assay 1.8-fold (n = 3). 改了什麼：上限換成實測最大值、補上條件、『robust』整個拿掉、『doubles』還原為 1.8 倍與 n。

## 7. 定位卡 (Positioning) — 縫隙在哪，對我們有什麼用

- 自問：作者說下一步是什麼？限制指向哪些沒做的事？跟我讀過的哪篇不一致？對我們的意義？借什麼、不借什麼？
- Future work：[author] 長延遲需要更緊的加熱控制（§4）；其餘沒有列。 · Limitations 指向：[author] 單一濕度、基準取自文獻（§4）。[inferred] 以及 n、單一檢測、無反向對照。 · 跨文獻不一致：[inferred] 本文與 Table 1 引用的 [2][3] 的數字（糖障壁 60–900 s、約 25 %）沒有其他獨立來源可對照；三篇參考文獻的作者都在本文作者名單內。 · 縫隙：[inferred] 並排量測蠟橋與糖障壁（同紙同條件）；至少三個濕度的 k(RH)；L > 5 mm 的區間；一個『不該改善』的檢測作反向對照。
- 對我們的意義：我們跑多步驟紙基檢測：若要靠印刷長度排序試劑，這篇給了一個零額外材料的候選與一組可抄的設計數字，但只能當成『在 23 °C、45 % RH 一個條件下可能可行』的起點。[inferred] · 借：design_data（2 mm 通道、橋 1–5 mm、120 °C/60 s、k = 24.6 s/mm²）當第一輪試驗的起點；以 SD 隨長度成長提醒自己控制加熱；兩步驟檢測的設計（B 在橋之後）。 · 不借：Abstract 的 15 分鐘與 robust across humidity；『比糖障壁更可重現』；R² = 0.97 當作機制證據；n = 3 的 1.8 倍。
- 脈絡（讀人不只讀篇，從參考文獻取）：這個群組的前作 [inferred] 三篇參考文獻 [1][2][3] 的第一作者分別是本文三位作者（紙裝置概論、磁閥、糖障壁）：這是一個小群組的連續作品，比較欄裡的對手也是自己人的前作。 · 還有誰在做 無法定位：參考文獻只有 3 條，沒有外部群組。 · 所屬社群 [inferred] 紙基微流體／即時檢測 (paper microfluidics, point-of-care)。

## 8. 學習筆記

- 難的地方：分辨『量到的 42–612 s』與『Abstract 說的 15 分鐘』：兩者差了一個外推，而那個 900 s 其實出現在比較表的另一列。
- 學到的詞（詞條候選）：wax delay bridge；partially fused；delay time；bridge length；Washburn；permeability；sugar barrier；magnetic valves；coefficient of variation；two-step assay；simultaneous delivery；detection zone；fluid front
- 一週後自我檢查三題：
  - Abstract 的『up to 15 minutes』在本文哪裡有量測點？（答案：沒有，最大 612 s，900 s 是 Table 1 糖障壁列的上限。）
  - Fig. 2 的 R² = 0.97 為什麼不能當作 L² 機制的證據？（只有 5 個平均值、過原點單參數、短橋系統性在線上方、局部冪次約 1.66。）
  - 『variation below 15 %』與『比糖障壁的 25 % 好』差在哪？（前者是自己 n = 5 的點估計，後者是跨研究比較，且 CV 區間重疊。）
- 作者做得好的地方（欣賞作者、同時保留懷疑——只列缺口等於只讀了一半）：[inferred] 作者把兩個最大的破口（單一濕度、借來的基準）老實寫進 Discussion；Fig. 4 的 y 軸從 0 開始；每個結果都有 ± SD 與 n；整篇只有一條主線，圖與論證一一對應。
- 練習建議：把 §3.2 與 Table 1 重寫成『誰量的／條件／n』三欄表，再決定哪些格子該填『借自 [3]』。
- 重讀排程（每一遍換問題）：第二遍帶 How（§3–§6：能不能向別人重走一遍作者的推理）；第三遍帶 Why（paper-story 的軸向與 `necessity`、§7：換一種方式會失效嗎、破綻在哪、怎麼改良）。上面的三題自我檢查各對應一層。

## 9. 給 paper-story 的素材（簡報由 paper-story 做；這裡只留它會取用的東西）

- 設計資料表：見 §6；圖清單（依故事順序）：F1 p.1 Fig. 1 → F2 p.2 Fig. 2 → F3 p.3 Fig. 3 → F4 p.3 Fig. 4 → F5 p.3 Table 1；可借句型：見 §6
- 判定詞供引用：C1 provisional（E1）；C2 hypothetical（E3）；C3 withhold（none）；C4 withhold（E2）；C5 provisional（E1）

## 10. 附錄

- 作者結論原文 `[author]`（p.4 §5）：「Delays of 42 to 612 s with a variation below 15 % were obtained with no added material, and a two-step assay gave 1.8 times the signal of simultaneous delivery.」
- 逐字引文與出處：
  - 「yet most paper devices deliver everything at once」 p.1 Abstract
  - 「the delay becomes a printed dimension rather than a material property」 p.1 §1
  - 「the standard deviation is 4 s at 1 mm and 81 s at 5 mm」 p.2 §3.1
  - 「All measurements were made at one humidity」 p.4 §4
  - 「taken from the literature rather than measured side by side with our devices」 p.4 §4
  - 「Delays of 42 to 612 s with a variation below 15 % were obtained with no added material, and a two-step assay gave 1.8 times the signal of simultaneous delivery.」 p.4 §5
- 過程紀錄（時間、工具、看過哪些頁、跳過什麼與為什麼）：2026-11-03：ingest（4 頁 PDF、5 個 caption）→ probe.py（11 單元、0 anomalies）→ glossary.py（31 候選，挑 13 個）→ crop_all.py（Fig. 1–4 裁圖並逐張看過；Table 1 在 PDF 裡是一段文字，crop 無內容可裁，改看 source/pages/p003.png；裁圖 gate 為 UNDET，因為對照 fixture 未出貨）→ units.py --check --twice（29 單元，hard_failures 空）→ 讀 p003.png → 寫 cards.json。跳過：無（全文 4 頁皆讀）。
- 驗證輸出：`verify_run.py` 由派工者另跑（本 skill 拆分後不再產 `gates.txt`；簡報閘門在 paper-story 的 `story-gates.txt`）；vault 檢查：kv-lint 未執行（kv-lint.py 不隨本 repo 出貨；本 run 無筆記庫）

相關：[[home]]
