# 證據（EVIDENCE）

這份說明這次發版實際量了什麼、每條方法規則從哪來、哪些由程式強制、哪些不宣稱。
行號以 v1.0.0 的 `reference-impl/` 為準，每次發版重新核對。

## 實測（v1.0.0）

環境：Windows 11、Python 3.12.7、PyMuPDF 1.26.7、python-pptx 1.0.2、playwright 1.62.0、jsonschema 4.26.0、pytest 9.1.1。

**驗收控制（`verify/controls_run.txt`）：10 of 10 ok。** 每一行印出正確版與突變版兩個值：

| id | 正確版 | 突變版 |
|---|---|---|
| K1–K5a | 五個 selftest 都 exit 0（各自內含必須失敗的壞輸入） | — |
| K5b | paper-distill 單元測試 50 passed | — |
| K6 | verify_run：V2 PASS，0 FAIL | 結論引句加上捏造字 → V2 WARN「not found verbatim」 |
| K7a | verify_story exit 0，V2 無 FAIL | 清空 `axis.entry_point.why` → exit 2，V2 FAIL |
| K7b | verify_story V11 無 FAIL | 偏移第 1 列引句加字 → exit 2，V11 FAIL |
| K8 | 示範論文文字層 sha256 `47a2aa796d1f7327` | 重新產生 → 同一個值 |

K6 的突變在第一次寫錯欄位（cards.json 沒有叫 `quote` 的欄位），控制項當場判 MISMATCH，改成 V2 真正比對的
`paper_says.conclusion_quote` 後才通過。這次失敗沒有被吞掉，就是控制項本身會報錯的證據。

**示範成果（`examples/library/Placeholder2026_wax-delay-bridges/`）**，作者 session 以外由維護者重跑：

- `verify_run.py`：VERIFY PASS，0 FAIL、0 WARN；學習紀錄 67 個出處標籤、13 個詞彙。
- `render_story.py`：RESULT PASS，0 FAIL、0 WARN（`story-gates.txt`）。重點數字：主軸 5 項、故事線 7 段、邏輯鏈 4 環；
  19 句引句逐字找到；11 / 11 章節圖表被引用；十種偏移徵兆中 5 種找到（7 列）、5 種宣告 none；key point 5 個角色全部綁定。
- `verify_story.py`：VERIFY PASS，0 FAIL；why-density 33。
- `lab_deck.py --base blank`：17 張投影片（封面、15 頁內容、Thanks），L1–L9、L11 PASS；L10 未跑（見下方「不宣稱」）。
- 圖說檢查：控制組 ok，5 個圖說全部通過；裁圖 4 張 PASS，Table 1 是純文字表格，沒有可裁的圖（crop 記為 ERROR，屬預期）。
- 示範論文刻意埋的四個缺口，審計都抓到：摘要「最長 15 分鐘」vs 實測最大 612 秒；「各種濕度都穩定」只測 23 °C／45 % RH；
  糖障壁比較借自作者自己的舊文；兩步驟檢測 n = 3（摘要寫 doubles，實為 1.8 倍）。另外抓到一個沒刻意埋的：
  L² 擬合只有 5 個平均值，兩端點推得的指數約 1.66 而非 2（re-derived）。

## 規則來源（origin records）

這些規則不是一次寫成的，而是原作者在自己的論文庫上反覆跑、出錯後補上。來源紀錄留在各檔案的出處行（provenance line）裡，日期與 lesson id 保留：

- **偏移引句要逐字比對（S10）**：早期版本的偏移表把轉述當成引句，上台被問到原文時對不上。
- **圖的內容從圖本身讀**：一次讀圖只看圖說，把圖說的「趨勢」寫成圖上看得到的結果；`crop.py` 的壞樣本 `crop-gate-bad_tran2018-F6.png` 就是那次裁錯的圖。
- **圖說檢查的控制組**：`caption-check_tran2018-F4.json` 是一段 160 字被截斷的圖說（必須 FAIL）與完整圖說（必須 PASS）。
- **key point 必須是抽象邏輯（S15/S16）**：兩次在主軸還沒做完就抽 key point，結果寫成摘要；所以 N3 排在主軸之後。
- **正式簡報的版面規則（L1–L12）**：從投影片實際在 PowerPoint 裡的量測歸納（標題換行、文字溢出框、頁尾區）。

## 強制對照表（Enforcement map）

「程式強制」= 違反時腳本判 FAIL 或 WARN；「流程規則」= 寫在方法文件裡，靠作者與讀者遵守，腳本不判。

| 規則（文件出處） | 強制方式 | 位置 |
|---|---|---|
| story.json 符合 schema | 程式強制（FAIL） | `reference-impl/skills/paper-story/scripts/render_story.py:205`（S1）；`verify_story.py:189`（V1） |
| 每一步都有「為什麼」，且不是重複 what（paper-story SKILL.md） | 程式強制（FAIL） | `render_story.py:220`（S2）；`verify_story.py:208`（V2） |
| 主軸、故事線、邏輯鏈、偏移每項附出處 | 程式強制（FAIL） | `render_story.py:245`（S3） |
| 偏移的每列引句逐字出現在 `source/paper.txt` | 程式強制（FAIL） | `render_story.py:783`（S10）；`verify_story.py:308` 轉成 V11 |
| 每個章節、圖、表都被引用或列入 skipped 並附理由 | 程式強制（FAIL） | `render_story.py:847`（S11） |
| 每個探針異常都被分類 | 程式強制 | `render_story.py:891`（S12） |
| 十種偏移徵兆逐一宣告 found / none | 程式強制 | `render_story.py:959`（S13） |
| key point 的每個角色都綁定到這篇的對應物 | 程式強制（FAIL） | `render_story.py:382`（S15） |
| key point 不含數字與單位 | 程式強制（WARN） | `verify_story.py:260`（V5） |
| 說明頁版面不溢出、頁面填滿度 | 程式強制 | `render_story.py:1465`（S7）、`render_story.py:1506`（S7b）；`reference-impl/tools/page-fill-gate/` |
| cards.json 符合 schema，出處標籤只能是 author / verified / inferred / assumed | 程式強制（FAIL） | `reference-impl/skills/paper-distill/assets/cards.schema.json:122`；`paper-distill/scripts/verify_run.py:203`（V1） |
| 判定詞只能是 provisional / leaning / hypothetical / withhold | 程式強制（schema enum） | `cards.schema.json:143` |
| 審計引句逐字出現在文字層 | 程式強制（WARN，文字層可能不完整） | `verify_run.py:240`（V2） |
| 頁碼出處不超過論文頁數；§ 出處必須是 structure.json 的章節 | 程式強制（FAIL） | `verify_run.py:105`、`verify_run.py:150`（V3） |
| 學習紀錄至少 15 個出處標籤 | 程式強制（WARN） | `verify_run.py:270`（V6） |
| 裁圖不得裁壞（已知壞樣本必須被擋） | 程式強制（雙側） | `paper-distill/scripts/crop.py:98`、`crop.py:102` |
| 圖說截斷檢查 | 程式強制（雙側） | `paper-distill/scripts/ingest.py:237` |
| 投影片 4:3、全英文、最後一頁是 Thanks | 程式強制（FAIL） | `paper-story/scripts/lab_deck.py:1013`（L1）、`lab_deck.py:1015`（L2）、`lab_deck.py:1028`（L4） |
| 投影片文字不超出框、標題一行（PowerPoint 量測） | 程式強制（需 `--render`） | `lab_deck.py:1131`（L10） |
| 倒著讀（結論→摘要→圖→前言→方法） | 流程規則 | `paper-distill/SKILL.md` |
| 圖的內容從圖本身讀，不從圖說抄 | 流程規則（裁圖品質由 crop gate 擋，讀法本身不判） | `paper-distill/references/` |
| 自建基準標 self-eval；只有正面實驗時機制主張最多到 hypothetical | 流程規則 | `paper-distill/references/claim-audit.md` |
| 判定詞給得合不合理 | 流程規則（讀者判斷） | — |
| 「為什麼」寫得對不對、key point 能不能搬到別篇 | 流程規則（讀者判斷） | `paper-story/references/logic-extraction.md` |
| 作者不驗自己（verify 由另一個 session 跑） | 流程規則 | 兩個 SKILL.md |
| 說明頁與正式簡報不互轉 | 流程規則 | `paper-story/SKILL.md` |

## 不宣稱

- 不宣稱審計結論正確：腳本只證明「有寫、有出處、引句是原文」，不證明判斷是對的。
- 不宣稱在 Windows 以外能跑；macOS / Linux 未實測。
- 不宣稱在真實論文上的表現：這個 repo 只附虛構論文的成果；原作者在真實論文上的評估資料沒有出貨（有版權與個資問題）。
- `--render`（L10，用 PowerPoint 實際量文字是否溢出框）這次發版沒有跑；示範簡報只過了 python-pptx 能判的 L1–L9、L11。
  投影片在 PowerPoint 裡實際長什麼樣，是人工驗收 A 必驗第 3 項。
- 說明頁與簡報的外觀沒有被任何檢查閘「證明好看」：版面量測只量溢出與填滿度，外觀由人看過才算數。
- carriers selftest 的上游素材比對（asset comparison）在沒有原作者 AssetVault 時是 UNDETERMINED，不是 PASS。
- 示範論文的文字層、頁圖由 `make_paper.py` 產生；K8 只比對文字層 sha256，不比對 PDF 位元組（PDF 內含時間戳記）。
