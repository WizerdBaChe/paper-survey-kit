---
xi: 1
what: "Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics — 核心邏輯（slogan＋讀書心得詮釋＋角色表）；由 story.json 生成，是論文核心邏輯關聯索引的葉節點 (keypoint note generated from story.json)"
tags: [paper-story, keypoint, literature, logic/hang-function-on-existing-geometry, logic/one-knob-scan-against-scaling-law]
aliases: ["Placeholder2026_wax-delay-bridges keypoint", "Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics 核心邏輯", "Placeholder 2026 核心邏輯"]
date: 2026-11-03
status: live
kind: literature
source: "file: Placeholder2026_wax-delay-bridges/story.json"
verified: "generated 2026-11-03 by paper-distill library.py"
review-when: "story.json of any accepted run changes (re-run library.py readme)"
domain: []
promoted-to: "-"
---
# 核心邏輯：Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics

> Ada Placeholder et al. · 2026 · Journal of Imaginary Microfluidics 1, 101-108 (fictional) · run `Placeholder2026_wax-delay-bridges` · 由 `library.py` 生成，改 story.json 再重生，不要手改。

## Slogan

**把要控制的時序量掛在既有製程步驟已決定的幾何尺寸上；先寫下它該服從的標度律，再只掃這一個尺寸去對照；最後用一個實際任務驗收用途。**

## 解讀（讀書心得的終極詮釋）

作者面對的是一個很具體的問題：多步驟檢測要試劑依序到達，紙裝置卻讓試劑一起到達；手上的計時元件，糖障壁變異大、閥要加零件。他們先退一步，把『時序量』（延遲）掛在一個本來就由既有製程決定的尺寸上——蠟印刷已經在定義通道，所以多印一段只部分熔融的蠟橋，橋長 L 就成了延遲的旋鈕；這樣做之所以合理，是因為不必再加材料或組裝。接著他們在量測之前先寫下標度律：把橋當成低滲透率的多孔區段，Washburn 型關係預測 t = k·L²，預測先寫下，數據才有機會推翻它。然後只掃橋長這一個尺寸（1–5 mm，每個長度 5 個元件），把平均延遲與虛線對照。最後用一個實際任務驗收用途：把試劑 B 放在 3 mm 橋之後，兩步驟顏色檢測的訊號是同時給藥的 1.8 倍。我從這裡帶走的是這個建構順序；也帶走一個提醒：這條邏輯的每一步都只在一組條件（23 °C、45 % RH）下被量過，Abstract 的 15 分鐘與對濕度穩健，是第三步之外的延伸，不是被量到的結果。

## slogan 裡的角色 ＝ 在這篇

| 角色 | 在這篇＝ | 出處 |
|---|---|---|
| 要控制的時序量 | 試劑抵達檢測區的延遲時間（delay time，量到 42–612 s） | Fig. 2, p.2 §3.1 |
| 既有製程步驟已決定的幾何尺寸 | 蠟印刷本來就定義通道，橋長 L（1–5 mm）是同一個印刷步驟多印的一段尺寸 | p.1 §1, §2.1 |
| 它該服從的標度律 | Washburn 型 t = k·L²（k = 24.6 s/mm²），橋視為低滲透率多孔區段 | p.2 §2.3 |
| 只掃這一個尺寸 | 橋長 L = 1、2、3、4、5 mm 五個值，每個長度 5 個元件，其他條件固定在 23 °C、45 % RH | p.1 §2.1, §2.2 |
| 一個實際任務 | 兩步驟顏色檢測：試劑 B 放在 3 mm 橋之後，對照同時給藥（n = 3） | Fig. 4, p.3 §3.3 |

## 邏輯型（tags）

#logic/hang-function-on-existing-geometry #logic/one-knob-scan-against-scaling-law

## 相關論文

- （尚無）

## 檔案

- [[Placeholder2026_wax-delay-bridges/narrative-record|敘事紀錄]] · [[Placeholder2026_wax-delay-bridges/reading-record|學習紀錄]] · [說明頁](Placeholder2026_wax-delay-bridges/paper-explainer.html)（`paper-explainer.html`：一頁、逐圖判讀與口述稿都在裡面）
- 最脆弱的一環：從第三步到 Abstract 的外推：『最長 15 分鐘』與『對濕度穩健』兩句沒有任何量測點。
- 可移植到：我的專案要讓兩個試劑依序到達時，可以把『時序量掛在既有製程尺寸上、先寫標度律、單旋鈕掃描、用同時給藥當對照』當成第一輪試驗的設計邏輯。

相關：[[KEYPOINTS]] · [[home]]
