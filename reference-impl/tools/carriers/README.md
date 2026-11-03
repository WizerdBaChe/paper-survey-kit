# carriers — 說明型交付物的載體位置（維護手冊）

說明型的網頁與簡報不手寫。內容照固定格式寫成一份內容檔 (content file)，由這裡登錄的載體 (carrier) 機械式產出成品，成品裡寫入產生印記 (generator stamp)。規則本體：`~/.claude\rules\explainer-deliverables.md`（使用者裁定 2026-10-09）。

## 一句話流程

```powershell
python -X utf8 ~/.claude\tools\carriers\build.py validate <名稱>.explainer.json
python -X utf8 ~/.claude\tools\carriers\build.py build --carrier html-explainer --content <名稱>.explainer.json --out <名稱>.html
python -X utf8 ~/.claude\tools\carriers\build.py build --carrier pptx-explainer --content <名稱>.explainer.json --out <名稱>.pptx
python -X utf8 ~/.claude\tools\carriers\build.py check <名稱>.html --content <名稱>.explainer.json
```

`build` 依序做：內容檢查 → 轉成載體 → 跑該載體的關卡 → 全過才蓋印記。這些都在一個暫存檔上做，全過才換上 `--out` 的正式檔名；任何一關失敗，原本的成品原封不動，也不會留下沒印記的檔。`check` 一定要帶 `--content`，不帶就看不出「內容已改、成品沒重建」。

相依套件：`jsonschema`、`python-pptx`、`Pillow`；網頁載體的寬度關卡另需 `playwright` 與 Chromium（`tools/page-fill-gate` 用）。

內容檔的寫法限制（`build.py validate` 會檢查）：
- 圖檔用相對路徑，而且要在內容檔所在資料夾之內（不能 `../` 到外面、不能用絕對路徑）；格式限 `.png`、`.jpg`、`.jpeg`、`.gif`（兩種載體都能嵌入的交集）。
- 詞彙的 `term`／`en`、出處的 `label`、`meta.author`、數字卡的 `value`／`unit` 是純文字欄位，不能放 `**` 或 `[[..]]`；其他文字欄位可以放，但 `[[..]]` 不能包在 `**粗體**` 裡。
- 內容雜湊 (content digest) 包含圖檔本身：只換圖、文字沒動，成品一樣會判成 `stale`。

## 這裡有什麼

| 位置 | 是什麼 |
|---|---|
| `schema/explainer-1.schema.json` | 內容格式 `explainer/1`：章節、段落、條列、步驟、表格、圖、提示框、數字卡、引言、詞彙、出處。只說「講什麼」，不含版面 |
| `common/` | 所有載體共用、且只有這些共用：內容檢查 (`content.py`)、行內標記解析 (`inline.py`：`**粗體**`、`[[g:詞彙]]`、`[[r:出處]]`、`[[s:章節]]`)、印記 (`stamp.py`) |
| `registry.json` | 載體登錄表：編號、版本、狀態、吃哪種內容格式、產出副檔名、適合的讀法、關卡、上游來源、何時要複查 |
| `html-explainer/` | 說明網頁：單一 HTML 檔，沿用已驗收的研究站閱讀框架（左側導覽、右側本節速查、可拖寬可收合、滑過看定義） |
| `pptx-explainer/` | 說明簡報：16:9 PPTX，沿用 AssetVault 的 python-pptx 輔助程式（中文字型、語言標記、字級分層、防孤行） |
| `samples/sample.explainer.json` | 標準範例內容；任何載體改動都要用它重建並通過 |
| `samples/built/` | 範例的成品，給人打開看用（不進 git，隨時可用 `build` 重建） |
| `build.py` | 唯一入口：`list`、`validate`、`build`、`check`、`scan`、`selftest` |

## 隔離規則（為什麼一個載體一個資料夾）

- 每個載體只引用 `common/`，**不引用別的載體**。改網頁載體不會動到任何簡報，反之亦然。
- 每個載體資料夾都有：`CARRIER.md`（自己的規則、內容與版面對照表、改版紀錄）、`render.py`、`gates.py`、`vendor/`（上游檔案的逐位元組複本，記 sha256 與出處）、`tests/`。
- 上游（AssetVault 的閱讀框架或簡報輔助程式）有新版時，登錄表的 `review_when` 會觸發：更新 `vendor/` 複本、升版本號。複本是複本，上游路徑只是出處，不是依賴。

## 維護規則

1. **改一個載體**：只改它的資料夾 → `registry.json` 該列 `version` +1 → `CARRIER.md` 改版紀錄加一行 → 跑 `build.py selftest`，要 ALL PASS。selftest 預設包含每個載體的單元測試（約 1 分鐘）；`--quick` 跳過單元測試，只能在修改途中用，不能當改版關卡。登錄表的 `gates` 欄要和載體實際跑的關卡一致，selftest 會比對。舊成品保留它當時的版本印記，要更新就重建。
2. **加一個載體**（例如新的簡報樣式、文件格式）：開新資料夾（同樣四件＋tests）→ 登錄表加一列 → `selftest` 用標準範例跑過。資料夾有 `render.py` 卻沒登錄、或登錄了卻沒資料夾，`selftest` 都會判失敗。
3. **退役一個載體**：登錄表 `status` 改成 `retired`，資料夾不刪。
4. **內容格式不夠用**：改格式（新版本號），所有吃這個格式的載體一起更新並通過 `selftest`；不在某一份交付物裡另開旁路。
5. **成品不手改**：要改字改內容檔，要改版面改載體，然後重建。`check` 會把手改過的成品判成 `edited`，內容改了但沒重建的判成 `stale`。

## 判決的嚴重度與看得到／看不到什麼

- `build`：內容或關卡失敗＝**FAIL**，不蓋印記（下游要拿去用的東西，硬性）。
- `check`：`ok`／`unstamped`／`edited`／`stale`，非 ok 一律 exit 1。
- `scan <資料夾>`：只列出每個 HTML／PPTX 的判決，不擋任何東西。
- 看得到：成品是不是由登錄的載體、從哪份內容（含圖檔）、哪一版產生；建好之後有沒有被改過，包括檔案屬性（例如 PPTX 標題）和印記本身；內容是否已經比成品新（要帶 `--content`；`scan` 不比對內容，所以看不到這一項）。
- **看不到**：內容寫得好不好、畫面好不好看。網頁的寬度與結構、簡報的字級與框位置有各自的關卡，但最後的畫面要由人看過才算。

## 設計時查過的既有做法（prior-art）

`references/PROJECTS.md` 與 recall 查詢；AssetVault `candidates/research-site-shell`（當時的閱讀框架；2026-10-18 起升格為資產 `assets/pattern-template/html-css/research-site-shell`，D-40）與 `assets/pattern-template/python/pptx-deck-builder`；`rules/deliverable-doc-refs.md`、`rules/office-deck-deliverables.md`、`rules/node-promotion.md` PR-3；記憶 `generic-verification-layer-trigger`（2026-09-29 判斷跨載體層太早，這次由使用者裁定推翻）；open-slide-borrow-deck 的 `check_deck.py`；paper-story 的 `render_story.py`／`lab_deck.py` 與 claude-se-history 的 `build_site.py`（專案內既有的產生器，列為舊制，不回頭改）。
