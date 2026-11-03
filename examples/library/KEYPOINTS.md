---
xi: 1
what: "PaperSurvey 論文核心邏輯快速關聯索引——每篇一段：slogan、讀書心得詮釋首句、邏輯型、相關論文；按邏輯型分組 (index of every accepted paper's construction logic, grouped by pattern)"
tags: [paper-story, keypoints, topic-map, index]
aliases: ["論文核心邏輯索引", "核心邏輯關聯索引", "keypoints index", "PaperSurvey KEYPOINTS"]
date: 2026-11-03
status: live
kind: topic-map
source: "paper-distill library.py readme"
verified: "generated 2026-11-03 by paper-distill library.py"
review-when: "story.json of any accepted run changes (re-run library.py readme)"
domain: []
promoted-to: "-"
---

# PaperSurvey — 論文核心邏輯快速關聯索引

由 `library.py` 從每篇正本的 `story.json` 生成（2026-11-03），共 1 篇。每篇的 slogan 是抽象的建構規則；點進去的 keypoint 筆記有讀書心得詮釋與「角色＝在這篇」表。圖譜視圖裡，共用邏輯型或明寫相關的論文互相連線。

## 每篇一段

### [[Placeholder2026_wax-delay-bridges_keypoint|Placeholder2026_wax-delay-bridges]] · 2026 · Wax Delay Bridges for Timed Reagent Release in Paper Microfluidics

- **Slogan**：把要控制的時序量掛在既有製程步驟已決定的幾何尺寸上；先寫下它該服從的標度律，再只掃這一個尺寸去對照；最後用一個實際任務驗收用途。
- **解讀首句**：作者面對的是一個很具體的問題：多步驟檢測要試劑依序到達，紙裝置卻讓試劑一起到達；手上的計時元件，糖障壁變異大、閥要加零件。他們先退一步，把『時序量』（延遲）掛在一個本來就由既有製程決定的尺寸上——蠟印刷已經在定義通道，所以多印一段只部分熔融的蠟橋，橋長 L 就成了延遲的旋鈕；這樣做之所以合理，是因為不必再加材料或組裝。
- **邏輯型**：#logic/hang-function-on-existing-geometry #logic/one-knob-scan-against-scaling-law
- **深讀判定 C1**：provisional

## 按邏輯型分組

- `#logic/hang-function-on-existing-geometry`：[[Placeholder2026_wax-delay-bridges_keypoint|Placeholder2026_wax-delay-bridges]]
- `#logic/one-knob-scan-against-scaling-law`：[[Placeholder2026_wax-delay-bridges_keypoint|Placeholder2026_wax-delay-bridges]]

## 明寫的相關

- （尚無）

相關：[[README]] · [[home]]
