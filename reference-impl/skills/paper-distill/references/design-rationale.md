---
xi: 1
what: paper-distill 的設計紀錄——邊界契約、六篇貼文與四份實驗室簡報的分析、使用者思維習慣如何轉成規則、決策 D-1…D-14、先例重疊、驗證證據、可反駁性 (design record of the paper-distill skill)
tags: [skill-reference, paper-distill, design-record, know-why]
aliases: [paper-distill 設計理由, 論文精煉 skill 為什麼這樣設計, boundary contract paper-distill, 讀論文 pipeline 設計紀錄]
date: 2026-09-02
status: live
---

# paper-distill 設計紀錄（know-why）

> 人讀文件。給未來要改這個 skill 的人（或 session）看：為什麼是這個形狀、哪些是借來的、哪些是刻意不做的。
> 建置日 2026-09-02；主迴圈 Fable 5.1，ops-relaxation L2（常設裁定）。

## 0. 邊界契約 (Boundary Contract) — paper-distill skill

0. Premises：(P-env verified) PyMuPDF 1.26 / python-pptx 1.0 / Playwright + chromium 在本機可用；AssetVault `briefing-deck-shell`、`pptx-deck-builder` 存在（sha 已記）。(P-intent reported, user) 「key point 先行」＝**讀者的個人結論**，不是論文結論；第一份產出是給使用者**學習**的過程紀錄。(P-validity ASSUMED, model) 六篇貼文的方法適用於元件／光子領域論文——blast radius：圖表檢查表與 Method 四元素的對映可能要改，pipeline 骨架不受影響。
1. Interpretation forks：「一頁式簡報（html/pptx）＋解釋頁」→ 讀成同一個單檔的第 1 頁＋第 2 頁（isolation point：`render_onepager.py build_slides`）；「兩種報告簡報怎麼接上」→ 讀成**評估＋契約，不建渲染器**（isolation：`deck-formats.md` §5）；文獻庫位置未指定 → `<work>\PaperSurvey`（isolation：env `PAPER_DISTILL_HOME`；2026-09-03 起文獻庫改在 `<PAPER_HOME>`，此處保留當時的預設值作為決策紀錄）。
2. Boundary inputs：掃描 PDF（無文字層）→ 標 ocr_needed、access=partial；付費牆 URL → access=abstract、主張全 withhold；無圖的論文 → 一頁式顯示紅色缺圖框（不靜默）；專利／技術文件 → 四功能對映表；> 20 頁 PDF → Read 分批。
3. Acceptance：機器：`render_onepager.py --selftest` 12 項雙邊校準 PASS；樣本 `gates.txt` 無 FAIL；`ingest.py` 對本機 PDF 產出全部檔案。人眼（A 必驗）：見交付訊息清單；唯一未經真論文驗證＝整條 pipeline 的判斷品質（第一次真實運行才算）。
4. Non-goals & degradation：不做文獻搜尋、不做逐段批註文件（PaperLens）、不建多頁簡報渲染器、不自動存入 LexiconVault。降級順序：PPTX 版 → 圖表檢查表的領域擴充 → 第 3 頁全表 → 核心（SKILL.md＋四份方法文件＋analysis 模板＋HTML 一頁式＋閘門）不降。

## 0b. 2026-09-02 晚：使用者五項裁定（第二輪，看過合成樣本後）

> 歷史紀錄（2026-11-03 註記）：下表 R-A、R-D 的「落地」欄寫的 `talk-script.md`、`keypoint-onepager.*` 是當時的產物名；09-03 拆 skill 後已由 `paper-story` 接手，現行對應物是 `paper-explainer.html` 的「口述稿」一節（`talk-script.md` 自 2026-11-03 起不再產出）。

| 裁定 | 內容（使用者原意） | 落地 |
|---|---|---|
| R-A 檔名與標題要講用途 | 「這是讓我學習分析的過程紀錄、還是拿來講的、還是讓我知道最大重點的？」 | 三份人讀檔改名：`reading-record.md`【學習紀錄】、`talk-script.md`【口述稿】、`keypoint-onepager.html/.pptx`【全篇精華・一頁】；每份檔頭第一段自述用途；一頁式第 2 頁是用途說明（D-16） |
| R-B key point 是全篇精煉 | 「keypoint 應該要是一個非常精煉的全篇重點，不是抓單一項目來說」——合成樣本那句是失敗的 | 重定義：一句話同時壓縮方法／證據／邊界，三根支柱各帶出處；全篇測試（刪任一節還成立＝單一項目）；「對我們該做什麼」移出 key point 到「對我們的意義」（D-17，`keypoint-rules.md` 重寫） |
| R-C 多頁簡報保留論文自身分項 | 「打破既定格式」指的是閱讀順序不照簡報順序，不是改簡報；簡報是閱讀後的整理產物 | `deck-formats.md` v2：格式 A 照論文章節分項、前加 key point 頁、後加「對我們」；閱讀協定明寫「閱讀順序 ≠ 簡報順序」（D-18） |
| R-D 備忘錄＝口述內容 | 「這是報告的口述內容，本來就是因人而異，會不會整理與報告就看這邊」；畫面要多一句 key point | `cards.talk` → `talk-script.md`：每段「說／橋／若被問」的口語稿＋「我的版本」空白節；同文進 PPTX 備註；一頁式加 `KEY POINT｜全篇精華` 標籤列（D-19） |
| R-E Method 與圖證拉高 | PaperSurvey 的最終目的是學會寫一篇完整論文 | 新增 Stage 5 寫作解剖（`writing-craft.md`：論證鏈、方法段給了什麼／缺什麼、設計資料表、圖證設計、句型）；deck 權重 Methods 3–4 頁、Results 4–6 頁（D-20） |
| OQ-1 | PaperSurvey 名稱同意；位置搭配新建的 Obsidian 資料庫 | D-15（另一 session 已落地 `<PAPER_HOME>`）；run 內每份 `.md` 遵守 vault 卡片契約、跑 kv-lint |
| OQ-4 | 同意名詞自動成為詞條候選 | 待辦：run 結束後把 `terms[]` 寫成 `00-inbox/` 的 `kind: term-candidate` 草稿（AGENTS.md §3 第二列）；本輪未建，列在交付訊息 |

## 0c. 2026-09-03 第三輪裁定：拆成兩個 skill

使用者看過三份真實 run 後裁定：(1) 一頁式仍是「圖文描述」，敘事核心（主軸、故事線、為什麼選這方法、預期怎麼評估、統計與視覺化怎麼呈現）完全沒被當主體；(2) key point 應是「貫徹全篇的邏輯敘事 → 抽象化的邏輯抽取」，且每一步要有 why；(3) IMRAD 深讀是一套完整方法論與產物，呈現是另一個輸出樣貌 → 拆成兩個 skill，各自做完整，再橋接（比照 SRG ↔ LSE）；(4) 一頁式＝實驗室格式（3–6 圖＋五格表）＋一個 Keypoint；多頁式保留原設計、第一頁插 Keypoint、每頁圖＋短文字重點；(5) 所有專有名詞要有 Wikipedia page-preview 式 hover。

| D | 決定 | 為什麼 | 被拒的替代 |
|---|---|---|---|
| D-21 | 拆成 `paper-distill`（證據層：深讀、審計、寫作解剖、學習紀錄）與 `paper-story`（敘事層：主軸／故事線帶 why、邏輯抽取、實驗室兩種簡報、口述稿、全詞彙 hover） | 兩個物件不同、產物不同；模型缺「敘事」這個物件類別，加 mode 也產不出來 | 單一 skill 加 mode（同一物件模型會再產出圖文描述） |
| D-22 | 橋接＝共用 run 資料夾與工具（ingest/crop/library）、依情況互相呼叫、判定詞只由 distill 產生 | 比照 SRG ↔ LSE 的不綁定關係 | 硬依賴（story 一定要先 distill） |
| D-23 | why 軸採 Heilmeier（骨幹）＋ CARS Move 2（切入點）＋ Toulmin warrant（每環）＋ Mensh & Kording 單一貢獻（主軸測試） | 使用者要求評估標準解法；四者各擁一種 why，研究寫作教學本就合用 | Sinek Why-How-What（無評估問題）、5 Whys（非論證結構） |
| D-24 | 本 skill 的 render_onepager／keypoint-rules／deck-formats 封存到 `archive/2026-09-03-split/` | 被使用者否決的呈現層；閘門機制已搬到 paper-story | 直接刪除 |
| D-26 | key point 加 Test 0「規則 vs 事件」：名詞全換成角色後仍能指導建構者才是規則 | 使用者裁定 2026-09-03：Ow 2010 選 run B 的句子（抽象規則），主 run 的句子「回到描述事件」（光罩、產物、平台是名詞不是角色）——沒有數字也可能是事件描述 | 只靠「無材料名、無數字」的抽象測試（不夠） |
| D-27 | 一頁式 Conclusion 格＝作者的收尾（必留）＋「深讀判定：」＋讀者判定；S4b WARN；B 類 `Authors: … | Verdict: …` | 使用者裁定 2026-09-03：報告時要知道原作者怎麼收尾；三個 run 都自發這樣做 | 格子只留作者內容（原規則）；只留讀者判定 |
| D-28 | 看錯／漏看＝亂掰同級：`probe.py` 抽出結構單元與可判定異常（重複章節號、未被引用的圖、摘要數字不在正文）→ `structure.json`；story.json @2 每列偏離帶逐字 `quote`（S10 FAIL 查不到）；覆蓋閘 S11（每個單元被引用或列入 `coverage.skipped` 附理由）；異常歸類閘 S12；verify V11–V14 重跑 | 使用者裁定 2026-09-03 + 查證：CONSORT／PRISMA 的「每項填頁碼」＝覆蓋表；Elsevier 結構化審稿試點提高覆蓋與結論一致度、但「數據是否支持」一致度仍最低（判斷不能靠清單）；factored verification 顯示每篇 LLM 摘要 0.6–1.6 條捏造主張、逐條對原文查才降 → 捏造用查詢、遺漏用清單、判斷用第二讀者 | 只加自檢提示（無儀器）；只靠雙讀互抓（漏看兩人都跳過的）；固定審稿問題集當儀器（只提升覆蓋不提升判斷） |
| D-25 | 產物分兩類：html＝使用者練習／學習／快速複習用；正式簡報＝實驗室 pptx 範本改英文（換字、換圖、微調），明確要求時才做；不用工具把 html 轉 pptx（`--pptx-from-story` 只在明確要求時，且標 INFO 非上台稿） | 使用者裁定 2026-09-03（第一份 story run 全數通過檢核之後）：html 排版「能看且方便看，但很醜不能用來展示」；上台的格式與語言由實驗室範本決定；範本副本 `<NOTES_VAULT>\_attachments\lab-decks (not shipped)\`、程序 `paper-story/references/formal-deck.md` | 由 story.json 直出 pptx 當上台稿（已建，降為明確要求時才用）；砍掉 html（它是使用者的複習媒介） |
| D-29 | 偏離清單儀器化（skill-co-upgrade 第 1 輪）：story.json @3 每列偏離帶 `kind`（§4 十類枚舉＋`other`）、`coverage.drift_checklist` 對十類各標 found／none，S13 WARN 未表態的類別（宣告 none 卻被第二讀者找到＝晉升 FAIL）；一頁式圖帶 `kind`（evidence／schematic／motivation），S4c WARN 非證據圖；新增第十類 `abstract-mismatch`；verify V15／V16；既有四個 run 維持 @2（驗證器回報「未宣告」，不改已驗收產物） | 使用者裁定 2026-09-03（Gb8、Gb9 納入）；盲測 X／Y 各走了對方沒走的類別（X 獨有 4、Y 獨有 2）；把四個真實 run 的 21 列偏離套進枚舉時有 3 列（Ow d3、Bose X d7、Y d1）不屬任何一類 → 第十類；四個 run 的一頁式都放了製程流程圖 → S4c 在真實案例上全部觸發（待使用者裁定是否縮窄） | 只在 prompt 要求「逐條走」（校準證明不被走）；`kind` 用自由文字（不可判定）；S13 FAIL（判斷仍在讀者，嚴重度依消費者） |
| D-31 | 折入四篇新貼文（B-7…B-10）：核心需求已被兩個 skill 滿足，只加**六個可選欄位＋一個 bytes 工具**——`intake.triage.depth_ruler`（三軸）、Stage 0b 詞彙表（`glossary.py` 算頻率／首現頁／縮寫展開，reader 填 `terms[].role/unclear/ask_next`）、`core.assumptions[]`（前提盤點，`tested: no` 進該主張的 `missing`）、`position.lineage`（從參考文獻取，不建作者資料庫）、`learning.admire`、paper-story `axis.method_choice.necessity/dead_ends`；What/How/Why 對映成重讀排程而非新卡；claim-audit 加「單篇＝一種可能性」的判定天花板 | 使用者 2026-09-03 交四篇貼文要求「梳理並評估如何併入」；逐項對照後大多已被 09-03 拆分後的 why 軸／邏輯抽取／判定校準吸收，真正沒有欄位的只有前提、卡關、反事實必要性、詞彙四類、脈絡；全部設為可選（既有 run 不失效：三個 distill run V1 PASS、story selftest 36/36）；工具只做可判定的部分（詞頻、參考文獻切除、縮寫展開有雙邊 selftest） | 開第三個 skill 或加 mode（沒有新的物件類別）；把 What/How/Why 做成三張新卡（與 stage 重複）；作者網絡資料庫（沒有第二個消費者）；research identity／研究風格（不是讀單篇的事） |
| D-32 | D-31 六個欄位的量測先於答案：`evals/measurement-plan-new-fields-2026-09-03.md` 預先登錄指標／門檻／正負對照／儀器故障定義；可判定部分進 `verify_run.py` V9–V12 與 `verify_story.py` V18（欄位缺席一律 SKIP，舊 run 不開始警告；在 Ow／Z 副本上做雙邊 fixture）；判斷部分交盲的第二讀者（四類一致度、前提漏看、找一步換了也行的步驟）；量測後可修儀器，但要留前後與觸發案例，且在下一個 run 才驗 | 使用者裁定 2026-09-03：真實 run 要同時量測與校準，沒規範就先評估能不能做，「不要看著答案寫題目」，保留量測後修儀器的可能性由當下的 LLM 判定 | 等第一個 run 跑完再定指標（就是看著答案寫題目）；把判斷類做成 regex 閘門（必要性的反事實無法可判定，會變成拒絕一切或放過一切）；用 LLM 自評自己填的欄位 |
| D-30 | skill-co-upgrade 第 2 輪（使用者裁定：先跑 @3 從零 run 的尖端測試、派工測十篇一頁模式、主 session 只統籌）：story 模式契約（story.json 可無 deck／talk，schema `allOf` 只在 deep 要求；S5／S9 SKIP；V7 依存在與否）；S6／V8 排除詞彙表頁；`logic.reused_from`＋Intake「圖書館檢查」（圖書館已有的論文，story 模式引用深讀 run 的 key point，不重抽）；`quote_source: page-image`（文字層整段缺漏時 S10 降 WARN 交派工者核圖，預設仍 FAIL 並保留回歸案例）；`coverage.checklist_provenance`（回填的 none＝無此類列，非宣告）；晉升觸發改為觀察層級（同一觀察歸在別類＝分類歧見，不是漏看）；Cover 條數上限 6；keypoint_box 重複標籤 S4 WARN；S14／V17 雜字元（西里爾等，希臘字母允許）；qfold 折疊 U+2212 | 四個 sonnet run（Z 從零 @3 deep；S1–S3 story 模式）全部 V1–V17 PASS；Z 邊讀邊宣告清單找到的 9 類＝X∪Y；S1 在 Ow 找 8 類 vs 主 run 回填的 4 類（兩類受 §4 例子污染、兩類真新）；S2 的 PDF 文字層整段缺 Abstract 迫使換引文；Z 因 schema 上限把五段大綱砍成三段；S3 自己 grep 到 製程схема；三張一頁式都獨立成立 | 先派工再讓執行者撞 story 模式的牆（四個 run 付一次已知代價）；把 worked examples 從 skill 移進圖書館（新論文就沒範例可學）；S10 對找不到的引文一律降 WARN（捏造就藏得住） |
| D-33 | 折入 IG DcoRWkeDbKW「學術表達的七層結構」（B-12）：本 skill 只補 `craft.argument_chain[]` 的第三環 `hypothesis`（含 `none stated` 記法）與 `gap to next: unstated` 一項；**產出方向**（寫自己的稿）整條外送 `scientific-research-guide` §6.8 ＋ `deliverables.md` T6c | 使用者 2026-09-17 把核心重述為一個物件「Story Line」，有分析（拆別人的論文）與產出（寫自己的稿）兩個方向。分析方向逐環對照後，七環中六環已被覆蓋——①②④⑤⑥⑦ 落在 `argument_chain` 與各 stage，`paper-story` 的 `storyline[].why` ＋ `logic.chain[].warrant` 已是讀側的 story line——真正沒有欄位的只有第三環「為何預期會成立（理論／物理模型／機制）」；`core.assumptions[]` 記的是未經檢驗的**前提**，不是假說的**導出**，兩者不可互代。產出方向按 B-8 既有裁定（使用者自己的研究不歸本 skill）外送。貼文詞彙屬計量經濟體系（識別策略／識別假設／穩健性檢驗），不匯入本 skill，理工對應詞在 §6.8 列表 | 把七層做成一組新卡（與既有 stages 重複）；為「避免跳層」加 `verify_run.py` 閘門（新增 gate，成本高於目前價值 → FUTURE-WORK，觸發：任一真實 run 因為跳層而誤判）；改 `paper-story` round-5 的 `brief`（三問是刻意壓縮，動它與使用者裁定衝突）；動任一 SKILL.md 或加觸發詞（沿用 B-4 的 R1 形狀，且 ops-health 已報 description 預算吃緊）|

## 1. 輸入一：六篇貼文說了什麼、拿了什麼

| 貼文（post-brief 記錄） | 核心主張 | 進了哪個 Stage | 沒照抄的地方 |
|---|---|---|---|
| DahnbFTHP74（2026-07-08）NotebookLM 像研究者一樣讀 | IMRaD 是思考順序不是格式；先看見骨架、追問「這段為什麼在這」、用自己的話重寫再請工具修 | Stage 1 骨架卡；「先寫你的版本」框 | Method 四元素改成元件領域對映 |
| DclLP5SHNJ9 Day 05（2026-08-28） | 先辨認功能再處理細節；結構檢查表（區段×要完成什麼×放了什麼材料×我理解什麼）；三種失敗（只記名詞／只抄結果／方法當結論） | Stage 1 的表就是它 | 貼文自己「五步」對「四列」的標題錯誤不沿用 |
| DcvzXtiEdIe 四種模板（2026-09-01） | 判斷→理解→寫作→定位四循環；3 分鐘判斷；RQ/M/R/Limitations→貢獻；縫隙來自 Future Work＋Limitations＋跨文獻不一致；素材庫要標籤化／關聯化／版本化／可檢索 | Stage 0、2、5；`library.py` | 模板 2 只問證據在不在、不問夠不夠——由 Day 04 補上成 Stage 3；模板 3（寫作骨架）降為 deck_hints |
| DciJ5PqHGTZ Day 04（2026-08-27） | claim→evidence→層次→仍缺→判斷；四種主張類型；「這篇實際做了什麼」四格；slop 診斷；「能發表≠值得用來建立判斷」 | Stage 3 主張審計（本 skill 的儀器） | L1–L4 讀成矩陣不讀成階梯；證據**種類**與判定**強度**拆成兩欄 |
| DcAwx8FnDeF 原子短文（2026-08-14） | 一個想法、五句、≤250 字；結構先於內容；寫不短＝沒想清楚；寫下我的看法；日更＋週末重寫＝內化 | Stage 6 key point 的**形**；G4 閘門 | 貼文內兩套結構詞彙只留五句版 |
| Dbvd1RpkxDh PGY 職前加油站（2026-08-07） | 倒著讀（結論→摘要→圖，內文最後）；頁數≈分鐘×1.5；章節權重；≥4 張圖；每種圖看三件事 | Stage 0 讀序；`deck_hints`；Stage 4 的「三件事」格式 | 圖表清單從臨床換成元件／光子；印象管理的立場不採 |
| DcmugEmlLuv Research Reading OS（2026-08-29；2026-09-03 折入） | 讀論點不讀方法；paper＝一種可能性的證據；Problem→Assumption→Storyline→Method；研究旅程有 Failure；欣賞＋懷疑；讀人不只讀篇 | Stage 2 `core.assumptions[]`；Stage 6 `position.lineage`；`learning.admire`；claim-audit 判定天花板；paper-story `axis.method_choice.dead_ends` | 說服框架（Idea→Story→Evidence→Reader）已是 Stage 5 論證鏈＋故事線，不重複；Author Network 不建資料庫（觸發條件：十篇簡報要分組、或文獻庫過 ~20 篇） |
| Dc0UmGqE9UF Day 07（2026-09-03） | 先大量接觸再深讀；深度表（相關度×方法權重×證據深度）；推敲（重現方法）→琢磨（一題多法） | Stage 0 q5 深度標尺 `intake.triage.depth_ruler`，混合情況在 reading-method 補裁 | 推敲已是 Stage 5 `missing_to_reproduce`；琢磨／research identity／兩種研究風格是使用者自己的研究 → scientific-research-guide |
| Dcw-nw0Grl1 Day 08（2026-09-02） | What→How→Why 三次有目的的重讀；每層留文本證據＋自己的判斷；「換一種方式會失效嗎」 | 對映成既有 stage 的**重讀排程**（reading-method §Three purposeful re-reads）；反事實 → paper-story `axis.method_choice.necessity` | 不另開三張卡（stage 就是換問題；來源標記＋自問就是兩種沉積）；「回到文本修正」＝另一 session 跑 verify_run＋drift 對 C1，已存在 |
| Dc0XR8aHJwm Day 09（2026-09-03） | 第一遍先建 glossary：10–15 個反覆出現的詞、頻率、四類、還不懂什麼、第二遍要問什麼 | Stage 0b＋`scripts/glossary.py`（詞頻與首現頁＝bytes）；`terms[].role/freq/unclear/ask_next`；`coined` 進 slop 名詞替換 | PDF 內 highlight 不採（run 資料夾的文字層＋出處是同一件事的耐久形式） |

六篇合起來缺的一塊，正是使用者要的：沒有一篇說「讀完之後**你**的結論是什麼、跟你的工作有什麼關係」。四種模板的循環停在「找縫隙」，Day 04 停在「暫時判斷」；原子短文有「我的看法」但對象是任意題目。本 skill 把三者接起來：審計（Day 04）→ 定位（模板 4）→ 個人結論（原子短文）→ 先行。

## 2. 輸入二：四份實驗室簡報的診斷（47 頁，2026-09-02 拆解）

現況骨架與缺陷見 `deck-formats.md` §2。對設計有直接影響的三個事實：

1. 結論永遠在最後（單篇格式倒數第二頁；十篇格式每篇表格最後一列）——所以一頁式的第一個帶狀區是 key point，`analysis.md` §0 是 key point。
2. 講者觀點在頁面上是零；唯一一段真正的綜合（D4 把十篇分三類、連到自己的下一個實驗）藏在演講者備註——所以「對我們的意義／借／不借」是一頁式的固定區塊，不是備註。
3. 「Conclusion」格子是摘要改寫——所以有 G2 閘門（key point 與作者文字的 3-gram 重疊 > 45% 就警告），而且作者結論**逐字**引用、放小放右。

保留的：五格表（Structure/Features/Method/Result/Conclusion）的紀律，換成骨架卡的四列＋`contribution_claimed`。

## 3. 輸入三：使用者的思維習慣 → 規則

側寫（20 條、有出處）由子代理從 PHILOSOPHY.md、CLAUDE.md、memory、ops、DIT README 整理；直接落地的：

| 習慣 | 落點 |
|---|---|
| 前提標記、可反駁性、模型結論可被證據推翻但使用者前提不能被自動推翻 | 每句 `[author]/[verified]/[inferred]/[assumed]`；key point 帶 holds_when / overturned_by、origin=model |
| 證據優先於宣稱；宣稱強度 ≤ 證據強度；數字帶量測出處 | Stage 3 表；判定→措辭校準表；G5 動詞閘門；數字四種標籤 |
| 檢查器讀 emitted artifact、雙邊校準、gate 只判它能判的、嚴重度看消費者 | 先看圖再看敘述；self-eval 降級；`--selftest` 12 項雙邊；G8 拿不到儀器就 WARN 轉發；FAIL/WARN 依消費者 |
| 一問題一視圖 | 圖卡的 `question` 與 `blind_spot` 欄 |
| 拒絕的選項比選中的更重要；不要為了做而做 | `candidates_rejected`；前人「拒絕表」；停手判準；渲染器不建 |
| 學習＝降噪後的決策骨架視圖（DIT） | `analysis.md` 是過程紀錄不是摘要：自問→答案→落選→為什麼 |
| 待裁事項放訊息頭尾 | 交付訊息的「開放問題」獨立放最後 |
| 定義先於使用 | 詞彙條＋G 詞彙表＋hover 定義卡；G6 閘門 |

## 4. 決策

| D | 決定 | 為什麼 | 被拒的替代 |
|---|---|---|---|
| D-1 | 做成 skill，腳本只做 bytes→bytes | 讀論文需要「意見」，只能在主 session 發生（post-brief 的分界問題：這一步需不需要意見？） | 獨立工具跑本地 LLM（PaperLens 路線；品質核心元件會變成不可換的黑箱） |
| D-2 | key point 是讀者判斷，與 `paper_says` 分欄；作者測試 | 使用者的核心要求；分欄才能被閘門檢查 | 一個「conclusion」欄位由模型自由填（會退化成摘要） |
| D-3 | `cards.json` 是契約；模板與內容分離；簡報格式是渲染器 | PaperLens design-inputs §2 的成本結構分析仍成立：只有批註／判斷需要智慧 | 每種簡報各自重讀論文 |
| D-4 | 證據種類 E1–E4 與判定強度拆欄 | Day 04 的表照字面讀會矛盾（外部驗證→暫不下結論） | 沿用 L1–L4 單一階梯 |
| D-5 | 先寫檔再跑閘門；嚴重度依消費者；每道閘門有正對照 | 全域 gate 規則；memory gate-severity-by-consumer | 閘門失敗就不產檔（沒有東西可看） |
| D-6 | 殼與 PPTX helper **逐字**複製並記 sha（G9 偵測漂移） | rules/deliverable-doc-refs.md「不要重造」；手動移植是漂移來源 | 執行期直接讀 AssetVault 路徑（搬家就斷） |
| D-7 | 文獻庫預設 `<work>\PaperSurvey`，env 可改 | 實驗室交付物在 <work>（研究專案前例）；一行環境變數換位置 | 放 <media>/分析（那是貼文） |
| D-8 | 深度 full／standard／triage | 對應單篇多頁、十篇一頁、要不要讀三種真實情境 | 只有一種深度（十篇×full 不可行） |
| D-9 | 不建多頁與十篇渲染器 | 沒有真實 cards.json 就沒有版面的量測依據 | 用合成樣本先做（第一次真論文就重排） |
| D-10 | PDF 連結由使用者下載；HTML 用 WebFetch | 本 session 的安全規則：下載檔案需逐次同意 | 腳本自動抓 PDF |
| D-11 | analysis.md 繁中；skill 檔英文；模板繁中 | 語言政策依主要消費者 | 全英文（使用者要讀的學習紀錄） |
| D-12 | 「先寫你的版本」框在模型候選之上（摺疊） | 貼文 1 與原子短文都說順序就是內化；DIT 說結構視圖本身就有價值 | 只給模型答案 |
| D-13 | 圖表檢查表換成使用者領域 | 來源是臨床；使用者領域是半導體元件／光波導 | 保留臨床表（留在附錄致意） |
| D-14 | 一頁式版面沿用殼的三件套語彙，圖是 `.fig-main` 直接子元素 | 第一版把圖包在 `.stack` 裡，殼的 fit A 段不作用，References 條蓋到圖上——**截圖迴圈抓到、文字閘門全綠**，正是「文字閘門看不到版面」的實例 | 自己寫一套 CSS |
| D-16 | 三份人讀檔以用途命名，檔頭自述用途 | 使用者 R-A：讀者要一眼知道這份是學習用、講稿用、還是看重點用 | 保留 analysis.md／onepager.html 通用名 |
| D-17 | key point＝全篇精煉（方法＋證據＋邊界一句）＋三支柱；「對我們」獨立 | 使用者 R-B；第一版把單一主張＋實驗室決策當 key point，是定位不是精華 | 允許單一主張式 key point（作者也寫得出） |
| D-18 | 閱讀順序與簡報順序脫鉤；多頁簡報照論文分項 | 使用者 R-C；簡報是閱讀後的整理產物 | 依審計重排簡報（v1 提案） |
| D-19 | `talk` 區塊＝口語稿（說／橋／若被問），檔尾留「我的版本」 | 使用者 R-D：口述因人而異，整理與報告的能力就在這裡練 | 五句原子短文當講稿（是推理軌跡，不是口語） |
| D-20 | 新增 Stage 5 寫作解剖；Methods 與圖證頁數最多 | 使用者 R-E：最終目的是學會寫論文 | 只在 deck hints 提寫作骨架（v1） |
| D-15 | 文獻庫預設改為 `<PAPER_HOME>`（取代 D-7；OQ-1 就此結案） | 2026-09-02 使用者把 R5 委託 Claude 裁定：論文筆記與 domain profile、概念筆記同住一個 Obsidian vault；`<work>\PaperSurvey` 從未建立，零遷移；env 覆寫機制不變 | 留在 <work>（與 vault 分家，第二個文獻家） |

## 5. 先例重疊（prior-art，建置前查過）

- **PaperLens**（<projects>/PaperLens，設計中）：雙欄逐段批註閱讀文件，兩個鏡頭。不同產品；借了模板／內容分離、Annotator 唯一智慧元件、BR-1 原文逐字、BR-9 結論可回溯。
- **literature-search-extract**：檢索與萃取服務；trigger dict 原本把「這篇 paper 的重點」路由給它——已在字典加消歧（要報／key point／一頁式 → 本 skill）；本 skill 需要查標準名詞或前人結果時反過來呼叫它。
- **scientific-research-guide**：使用者自己研究的顧問；借 domain profiles 做 `intake.domain_profile` 與關聯句。
- **post-brief**：讀→解說→歸檔的迴圈與「意見的分界」；<media>/分析 就是它的產物。
- **audience-fit**：「簡易版＝加解釋層不刪內容」就是第 2 頁的形狀。
- **AssetVault** `briefing-deck-shell`／`pptx-deck-builder`：逐字沿用。
- **<projects>/LLM-Summary-maker**、**MindMap_Maker**：存在但未讀 README（只看了檔名）——可能是舊的摘要工具；未沿用，若要合併另開評估。
- **Paper2Chat**：使用者 2026-07-15 裁定不沿用（技術債）。

## 6. 驗證證據（2026-09-02）

- `render_onepager.py --selftest`：12 項雙邊校準全部 OK（good sample 無 FAIL/WARN；G1/G3/G7 各自的壞樣本 FAIL；G2/G4/G5/G6 各自的壞樣本 WARN；G8 儀器兩個正對照觸發；G9 改一個 byte 觸發）。
- 合成樣本 `--make-sample --pptx --fit-check --check-shell`：G1–G7、G9、P1 PASS；G8 第一版 WARN（第 1 頁縮到 0.82／0.78 才吻合）→ 截圖顯示 References 條蓋圖（D-14）→ 圖改為 `.fig-main` 直接子元素後 1707×830 以 scale 1 吻合，但 1280×720 仍疊字（grid `min-height:0` 讓格子縮到比右欄文字還矮）→ 加 `min-height:min-content` 後無疊字、1280×720 縮到 0.74（WARN，密度問題留 OQ-2）。
- **儀器本身抓到一次假通過**：G8 的「4000 px 已知溢出」正對照在前兩輪 OK，是因為那個空 div 在殼的 flex 欄裡會縮成 0，真正讓頁面溢出的是當時的疊字缺陷；疊字修好後正對照立刻失效（回報「儀器故障」）。修法＝對照塊改成不可縮（`flex:0 0 auto; min-height`）。這正是「從不失敗的正對照等於沒有對照」的實例——留在此處作為證據。
- `ingest.py` 對 `<projects>/fortesting1.pdf`（1 頁非論文）：run 資料夾、paper.md、頁圖、figures.json、cards.json 預填、_meta.json 全部產出；`crop.py --bbox` 產圖。標題猜測對非論文 PDF 退到 first-line（預期）。
- PPTX 經 PowerPoint COM 轉圖兩張（`投影片1.PNG`／`投影片2.PNG`）人眼掃過一次。
- **未驗證**：整條 pipeline 對真實論文的判斷品質；analysis.md 模板的實際填寫體驗；URL 路徑（WebFetch → paper.md）。這三項只有第一次真實運行能驗。
- **2026-09-03 第一次真實運行（三份 run，兩篇論文）**：判斷品質已驗——全文見 `evals/calibration-2026-09-03.md`。要點：閘門與獨立驗收器在三份真實 run 上全 PASS（G8 在 1280×720 一律 WARN）；同一篇兩份獨立 run 的 key point 各漏一角（DBR／D=C+A），互抓成立，單份 run 不能自證全篇測試；當場修了 10 項（驗收器 V2 假陰性降級、V8 數字比對、PPTX 表格壓字、第 2 頁分頁、Read 拒開 PDF 的替代路徑、paper.txt、A 的 key point 壓縮與假設、承重圖規則、DOI 外查政策、派工 `--year`）。URL 路徑仍未驗。

## 7. 可反駁性宣告

- holds-when：論文有可讀文字層、有圖、屬使用者領域（元件／光子／材料）；報告場合是 journal club 型（10–15 分鐘）。
- overturned-by：第一次真實運行顯示 Stage 3 的表對工程論文填不出「證據種類」；或使用者實測認為一頁式的資訊量不對（太多／太少）；或 Fable 以外的主迴圈跑不動七個 stage。
- evidence tier：方法＝六篇公開貼文（非同儕審查）＋使用者自己的規則；機制＝本機腳本已測；判斷品質＝未測（合成樣本不算）。
- not covered：掃描 PDF 的 OCR；多語論文（中文論文的 IMRaD 對映未試）；十篇合成頁。

## 8. 開放問題（待使用者裁定）

- OQ-1 文獻庫位置 `<work>\PaperSurvey` 可以嗎？（一行 env 可改）— **結案 2026-09-02，D-15**：改為 vault 內 `<PAPER_HOME>`。
- ~~OQ-2~~ 結案：畫面加 `KEY POINT` 標籤列；備忘錄改為口述稿格式（R-D）。
- ~~OQ-3~~ 結案：Methods 與圖證權重拉高（R-E，Stage 5 + deck 權重）。
- ~~OQ-4~~ 結案：同意自動產生詞條候選草稿（進 vault `00-inbox/`，`kind: term-candidate`）——實作待辦。
- OQ-5（新）多頁簡報的 key point 頁是否也放第 1 頁（使用者說的「先行」是對一頁式說的）？
- OQ-6（新）詞條候選草稿的落點：vault `00-inbox/`（AGENTS.md §3）還是等 LexiconVault M1？
