# page-fill-gate — 人讀的 HTML 頁面有沒有用掉它拿到的寬度

status: live 2026-09-04 · owner: 使用者裁決（寬度缺陷診斷 `outputs/html-width-void-diagnosis-2026-09-04.md`）

## 它守哪一條性質

在這台機器（2560×1440 @150% → 邏輯視窗 1707×830；外接 FHD 1920×950）上，人讀的 HTML 交付物
**不得留下不對稱的右側空白**。具名缺陷叫 **靠左錨定上限 (left-anchored cap)**：頁面容器或有
底色／邊框、獨佔一列的區塊被 `max-width` 卡住又靠左貼齊，右邊空一大塊。2026-09-04 量到一個殼
的 `max-width:1060px` 擴散成 13 份交付物，使用率只有 60–69%。

置中而左右對稱的空白（短篇閱讀欄）是另一種、被允許的形狀。**一頁該填多少，看它的類別。**

2026-10-31 起第二條性質：**頁面不得自相矛盾**——同 class 的同級元素要長得一樣、同一個元件不得在樣式表裡用兩個名字宣告兩次（見〈頁內一致性〉，只示警）。

## 類別是資料，不是程式分支

`page_classes.json` 一列＝一類：`mode`（centered / fill / centered-or-fill）＋門檻。頁面用
`<html data-page-class="…">` 宣告；沒宣告的頁面由結構推斷，判決降級（FAIL→WARN），因為閘門
只能裁它判定得了的事。推斷升格為宣告的觸發條件寫在 `unknown_policy.promotion_trigger`。

| class | 中文 | 內容類 | 規則 | 目前對應 |
|---|---|---|---|---|
| document-short | 短篇閱讀頁 | prose | 置中、左右留白差 ≤ 8px、fill ≥ 45% | audience-fit 報告、owner-view |
| dialog | 單一置中對話框 | node | 置中、左右留白差 ≤ 8px，沒有 fill 下限 | 解鎖／登入卡（2026-10-19，fb:86425480） |
| document-long | 長篇參考文件 | prose | reach ≥ 85%；`data-rail` 側欄算內容 | 研究專案教科書殼血脈（主文＋本節速查 rail） |
| deck | 一頁一螢幕簡報 | figure-led | 每張 `.slide` 各自量，reach ≥ 85% | deck-shell（vault、paper-story、paper-distill、研究專案快照） |
| tool | 操作型 GUI | node | reach ≥ 90%；> 1920px 的上限是 clamp 不是 cap | DIT、AssetVault GUI、HTMLToolsLobby 工具 |
| diagram | 圖為主載體 | diagram | 置中對稱 **或** reach ≥ 85%；fill ≥ 60% | diagram-authoring 產物 |
| dashboard | 卡片與表格儀表 | node | reach ≥ 85% | auto-fit 卡片格；入口頁（VIEWS、啟動頁）也量這一類 |
| showcase | 圖主展示頁 | figure-led | 置中對稱 **或** reach ≥ 85%；fill ≥ 60%；滿版色帶當背景不算內容 | 專案介紹、作品展示（2026-10-02） |

**兩套分類合成一張表**（2026-10-02）：`class`（頁型）決定寬度怎麼量；「內容類」（`content`
欄）決定樣式規則去哪裡讀，定義在 `page_classes.json` 的 `content_classes`。node 類是操作介面，
不屬於 `~/.claude/references/design-axes/` 的呈現媒材。

**滿版色帶（`backdrop_bands`）**：開了這個選項的類別，寬度 ≥ 98%、自己沒有文字的上色區塊
當背景，不算內容，裡面的子元素照量。沒有這個選項時，色帶頁一律量到 reach 100%，色帶裡
靠左被卡寬的內容欄看不見（測試的 showcase 負例以 dashboard 量會 PASS）。

**內嵌 SVG**：HTML 裡內嵌 `<svg>` 的 `tagName` 是小寫，2026-10-02 前沒畫框線的 SVG 不被當
成內容；已修正，修正前後對 6 頁已交付頁面的判定完全相同。

**新類別怎麼加**：在 `page_classes.json` 加一列（`zh`、`mode`、門檻、`notes`），在
`tests/test_fill_gate.py` 的 `CASES` 加一對正負 fixture，跑測試；少任一邊，測試會故意失敗
（單邊校準等於沒校準）。不要為新類別寫程式分支，也不要在規則檔用散文開例外。

**公式溢出（`defect_clipped_overflow`，2026-10-13）**：reach 只量頁面右緣，量不到「一行公式比自己的框寬、
尾端（通常是框起來的答案）要左右捲才看得到」。每個符合 `selectors`（`math[display=block]`、`.katex-display`、
`mjx-container[display=true]`）的方塊，`scrollWidth − clientWidth > tolerance_px` 就算一筆，整份文件都量（不限前三屏），
任何類別都適用；在 gating 視窗是 FAIL，advisory 視窗（1280）照例降成 WARN。輸出列出最近的標題、寬度比與式子開頭。
對照：`fixtures/known-bad-formula-overflow.html` 每次都必須 FAIL；實例正對照是修正前的 Silicon Photonics HW5（commit
`bc9e168`，1707 px 量到 6 行）。

**區塊層級升格**：某個選擇器的「較窄靠左區塊」被人回報過一次後，把選擇器前綴寫進
`block_fail_selectors`，該類發現從 WARN 變 FAIL。

## 用法

```powershell
python ~/.claude\tools\page-fill-gate\fill_gate.py <built.html> [...] [--viewport 1707x830] [--class deck] [--json] [--quiet]
python ~/.claude\tools\page-fill-gate\tests\test_fill_gate.py      # 每類正負各一，controls 必須觸發
```

每次執行都先跑七個對照：`fixtures/known-bad-left-cap.html` 與 `fixtures/known-bad-formula-overflow.html` 必須 FAIL、`fixtures/known-good-fill.html`
與 `fixtures/known-good-fixed-panel.html`（置中欄＋右下角固定面板）必須 PASS，另有三個頁內一致性對照（見下一節）；任一沒觸發就整次無效（RuntimeError）。
固定定位 (position:fixed) 的元素**連同其所有子孫**都不算內容——它浮在頁面上方；例外是標了 `data-rail` 的側欄，
以及蓋滿視窗的固定外殼（`inset:0` 的 app／deck 殼本身就是頁面）。2026-10-12 前只排除固定元素本身，
面板裡的文字被當成內容，置中頁被誤判「不置中」(fb:bfa19018)。

`data-rail` 可以標**多個、在左或在右**：中心在頁面中線右邊的延伸右緣，在左邊的延伸左緣。
用途是「左側目錄欄＋置中內文＋右側對稱留白欄」這種版面：兩欄都標，閘門才知道右邊的空白是刻意留的。
2026-10-31 前只認第一個 `data-rail`、而且一律當右緣，標了左欄反而把置中頁判成不置中（PersonalSite 文章頁）。
右邊留白沒標仍然 FAIL（閘門無從得知是刻意的），標了左欄但內文靠左也仍然 FAIL；兩組對照在 `tests/test_fill_gate.py`。
導覽列 (`<nav>`) 預設當頁面外框、不算內容；屬於內容格線的 nav（頁首連結列、置中版面右側目錄）在 nav 或其祖先標
`data-fill-content` 就計入（2026-10-19，fb:ee9813a8：站名把左邊撐住、右邊沒人撐，置中頁被讀成靠左）。
沒有推斷宣告時，第一張投影片隱藏的分頁簡報也會被認成 deck（看第一張「顯示中」的投影片）。
量測時所有網路請求都擋掉，只放行 localhost／127.0.0.1／[::1]／`*.localhost`：用 `astro preview` 或
`python -m http.server` 量含根目錄絕對路徑資源的建置站（fb:072d2f5d）。退出碼 0 無 FAIL、1 有 FAIL、2 儀器缺席
（Playwright／Chromium 不在）——2 的時候呼叫端要大聲 WARN 並且不得宣稱此性質。

一行輸出長這樣：`fill-gate: FAIL 1707x830  class=document-long reach=69% fill=64% void L/R=72/439px  教科書….html`，
`reach` 是內容右緣到內容區右緣的比例，`fill` 是內容左右緣之間的比例，chrome（固定側欄 TOC）已扣除。

## 量法（一句話說清楚它看得見什麼、看不見什麼）

只算有字、有底色／邊框、或是媒體的方塊，純包裝層不算，所以 `.sfit` 之類滿版 wrapper 不會遮掉裡面
卡在 56em 的框。deck 類逐張 `.slide` 量前 8 張；一次只顯示一張的分頁簡報（其餘 `display:none`／`visibility:hidden`／`[hidden]`／被隱藏的外層），每張在自己的量測期間被暫時強制顯示、量完原樣還原（L-125，2026-10-11），逐張結果在 `rows[i]["areas"]`。方塊只算「在量測區內看得到的那一段」（被 overflow 裁掉、停在畫面外、出血進 slide 內距的部分不算），所以 reach／fill 不會超過 100%；舊版會，而且超過時會把靠左被卡寬的頁面量成 PASS。看不見的：字元級的閱讀行寬（那是設計判斷，
留給人）、高度方向的溢出（那是 fit-gate 的事）、外觀好不好看（人眼）。

## 頁內一致性 (in-page consistency，2026-10-31)

**加了什麼性質。** 閘門原本只問「頁面有沒有用掉它的寬度」。2026-10-31 使用者裁決再加一條：**頁面不得自相矛盾**，
並且「同一個專案裡，同一個元件只宣告一次，像程式不重複宣告」。起因是 PersonalSite 首頁：四個同級的 `h2.section-title`
量出 22／22／32／32 px（一條情境規則只放大了其中兩個），而且兩組樣式被換了 class 名稱抄第二份（`.proj-thumb` 抄
`.story-thumb`、`.page-head .standfirst`／`.byline` 抄 `.prose` 的）。寬度閘門全數通過。兩個檢查都**只示警**
（WARN 單獨出現退出碼仍是 0），寬度檢查的輸出不變，新的發現放在 `--json` 的 `sibling_drift`、`duplicate_rules` 兩個鍵。

| 檢查 | 看什麼 | 它判得定的 | 它判不定的（所以只 WARN） |
|---|---|---|---|
| **C2 同級一致** | 可見元素按（標籤，class 清單，宣告的 ARIA 狀態）分組、組內 ≥ 2 個，比 `font-size`／`font-weight`／`font-family`／`line-height`／`letter-spacing` 的計算值 | 這幾個元素量出來不一樣（量測事實） | 作者是不是故意要不一樣（A/B 對照面板、工具類 class） |
| **S3 規則重複宣告** | 載入後讀瀏覽器實際套用的樣式表（CSSOM，遞迴進 `@media`／`@supports`／`@layer`），找選擇器不同卻宣告相同的規則對 | 共有哪些宣告、幾條 | 這是「抄了一份」還是「兩個元件共用一個設計值或重置樣式」 |

**狀態分組（2026-10-31 加）：** 帶 `aria-current`／`aria-selected`／`aria-pressed`／`aria-expanded`／`aria-checked` 的元素（值不是空、`false` 或 `undefined`）另成一組，例如目錄裡加粗的「目前這一章」。分組只看屬性名稱、不看值（`aria-current="page"` 與 `="true"` 同組）；同一狀態的元素之間照樣比；consistency 階段本身出錯時 `consistency_status` 記 WARN，不記 PASS；被分開的元素數記在 `state_split`。起因：閱讀框架模板 (research-site-shell) 在每一頁的目錄都被報 `a.l1` 500 對 700。

**C2 的三個脈絡濾網**（都計數並印在 `--json`，不是默默丟掉）：`<svg>` 內的元素不比（計算值是 viewBox 的使用者單位，圖產生器本來就逐節點設）；
同一條相對宣告碰到不同父層（`0.9em`、無單位 `line-height`）換算後相同就不算漂移；整組元素只是繼承父層的值也不算（那是父層的事）。
無單位行高 (unitless line-height) 繼承的是「數字」，子元素字級不同時 px 值就不同：子元素的「行高÷自身字級」等於父層的「行高÷父層字級」時也算繼承，但整組要用同一種讀法全部成立（全組 px 相同，或全組比值相同），混用不算——父層若宣告 px，一個成員繼承 px、另一個自己宣告剛好等於父層比值的數字，仍會報出（2026-11-02 加；起因：說明網頁的 `span.val` 在數字卡裡跟著 1.3、在日期行裡跟著 1.8，被誤報）。
濾網各有一個「關掉濾網就會報、開著就安靜」的測試頁，證明它們不是死碼。
**濾網的代價（已知殘留）：** 「整組元素只是繼承父層的值」會**藏住設在共用外層上的漂移**——例如四個 `h2.section-title` 都不自己宣告字級、
全由各自的外層 `section` 決定，而外層一個 22px 一個 32px，這組會被記成 `inherited_only` 而不報；這個差異屬於外層那個 class 的同級比較，
外層有自己的 class 且同 class 的外層有兩個以上時，才可能由外層那組的比較抓到，其餘情況不報。這三個計數（`svg_skipped`、`relative_equal`、`inherited_only`）
在**同頁還有別的一致性發現時**會印在最後一行（「同級檢查比對了 N 組；擱置、未判定：…」），沒有任何發現的頁面輸出不變，計數一律在 `--json`。

**S3 的兩條證據通道。** `copy`：共有 ≥ 5 條宣告且佔較短那條規則的 ≥ 0.8（`.proj-thumb` 對 `.story-thumb`）。`same-target`：**同一個 class
在兩個脈絡裡各宣告一次**（`.prose .standfirst` 對 `.page-head .standfirst`），只要共有 ≥ 2 條且 ≥ 0.6，因為「名字相同」本身就是大半的證據；
3 條宣告的分叉在 `copy` 通道看不見，把 K 降到 3 會讓分叉總數多約十倍（24 組變 231 組）。不報的：兩條規則共用同一個選擇器、選擇器名稱相同（`.btn:hover` 對 `.btn:focus`，同一元件的狀態或
媒體變體）、一邊的名稱包含另一邊（`.bar .btn` 對 `.btn`，情境覆寫）、只共享狀態 class（`.tab.is-active` 對 `.chip.is-active`）、目標只是標籤（`.a h2` 對 `.b h2`）。
瀏覽器把 `border: none` 序列化成四條長手宣告，所以同一個縮寫家族的長手宣告合併成一條再數（沒合併的突變版，兩條重置規則會被報成共有 6 條）。
一個分叉印一行（依「兩個選擇器差在哪些名字」分組，`.proj-thumb` 的本體、`:hover`、`img` 三條規則是同一行）。
連結的 `file://` 樣式表瀏覽器不讓腳本讀，閘門在本機讀檔補上（只讀本機檔與 loopback）；還是讀不到的列在 `--json` 的 `unread`，
本機的另外印一行，不會被當成「沒有重複」。補讀有三道限制：**不跟轉址**（loopback 回 302 就算讀不到，目標可能在任何地方）、**不走系統代理**、
**讀取上限 2,000,000 位元組**（`file:` 與 loopback `http` 一樣；超過整份算 `unread`，不拿截斷的半份當完整的來判）。補讀回來的樣式表若含
`@import`，目標列進 `unread`（`replaceSync` 會忽略 `@import`，那份其實沒讀到）。
**成本上界：** 超過 5000 條的規則不比，被超過 150 條規則共用的宣告（`margin: 0` 一類樣板）不計入共有數；兩者都回報在 `--json`
的 `not_checked`，並印一行「部分比對、未比對：…」，不會被讀成「沒有重複」（上限內的頁面此行不出現；校準樣本 35 份最多 252 條規則、最長的共用清單 37 條，無一觸及，開關上限前後的分叉組數同為 51）。

**對照（每次執行都跑，用數值斷言，不只看標籤）。**

| 對照檔 | 內容 | 必須 |
|---|---|---|
| `fixtures/known-bad-consistency-prefix.html` | PersonalSite 修正前 `a1cb5d7` 的真實 CSS（逐字，`git show` 取出）＋最小標記 | WARN；`h2.section-title` 的 `font-size` 同時出現 `22px`（×2）與 `32px`（×2）；點名 `.proj-thumb`／`.story-thumb` 與 `.page-head .standfirst`／`.prose .standfirst` 兩組分叉 |
| `fixtures/known-good-consistency-postfix.html` | 修正後 `b6b3c9c` 的真實 CSS＋新 class 的標記 | 上述 h2 漂移與兩組分叉都消失（該作者 CSS 裡別的重複仍在，所以狀態可為 PASS 或 WARN）；**且確實量過**：`h2.section-title` 這組被比對、n=4、無漂移 |
| `fixtures/known-good-consistency-clean.html` | 三個同級標題字級一致、不同 class 各自大小、規則只共用兩三條；另有 `span.val` 分別繼承 1.3 與 1.8 兩種無單位行高（2026-11-02 加） | PASS 且完全沒有發現；**且確實量過** |

「確實量過」是先於所有「沒有」類斷言的檢查：C2 比對組數 > 0、S3 解析規則數 > 0、`unread` 為空。少了它，一個根本沒跑的檢查（結果 `None`）也能通過每一條「沒有 X」的斷言。
一致性階段若丟例外，寬度判定不受影響（已 FAIL 的仍 FAIL、退出碼 1），該列多一行「consistency not computed: …」，`--json` 的 `consistency_error` 有值；
但三個對照檔本身讀不到一致性數值時，仍視為儀器故障（退出碼 2）。

CSS 副本在 `fixtures/personalsite-prefix/`、`fixtures/personalsite-postfix/`。測試另有 13 個合成頁（同 class 不同大小示警、同大小與不同 class 安靜、
三個濾網、無單位行高繼承安靜而自己宣告示警（含「px 父層＋宣告值剛好等於父層比值」必須示警，2026-11-02）、複製卡片示警、僅共享三條安靜、同名兩脈絡示警、狀態變體／情境覆寫／`@media` 同選擇器安靜、縮寫合併）、`find_forks` 純函式 14 個案例、
升格只對指定選擇器生效且預設空清單。

**升格。** `sibling_fail_selectors`（`page_classes.json`，預設空）：同一個選擇器被人回報過一次後，前綴寫進去，該組漂移變 FAIL；升格的發現排在第一行（FAIL 一定點名它的選擇器，不會被「只印前 6 組」或 JSON 的 40 組上限切掉）。空字串前綴會讓所有漂移都升格，載入時直接拒絕（退出碼 2）。S3 沒有升格（抄不抄是寫程式的判斷，閘門替作者決定不了）。

### 門檻怎麼定的（2026-10-31 量測）

樣本：33 份人讀 HTML，分屬 24 套不同的 CSS——`~/.claude/outputs` 的交付物 15 份、`views.json` 列的產生頁 8 份、PersonalSite `dist` 10 頁（從 `dist` 副本以
loopback 伺服器讀，沒有寫進 PersonalSite）；另有修正前後兩個真實對照。1707×830。

**C2：** 比了 8,388 個元素；三個濾網前 17 筆發現（10 頁），濾網後 3 筆（3 頁），濾網各自拿掉：SVG 內 475 個元素不比、相對相等 15 組、純繼承 14 組。
剩下 3 筆我的判讀：`span.val` 的 `line-height` 24.18／23.44px（當時判讀為真的小漂移；2026-11-02 量出是兩個父層各給 1.3、1.8 的無單位行高，判讀作廢，改由繼承濾網過濾）、`span.num` 在教科書裡 16／14.88／14／20px（脈絡混用，不確定）、
`span.lab` 的 `line-height` 19.58／20.16px（前後對照版面，兩個版本本來就不同，刻意）。

**S3：** 同一批資料、不同 K／R 下，24 套 CSS 的分叉總數（`same-target` 通道固定 2／0.6）：

| min_shared | R=0.6 | R=0.8 | 每套 CSS 平均（R=0.6） | 修正前 `.proj-thumb` 分叉 |
|---|---|---|---|---|
| 2 | 1602 | 673 | 66.8 | 找得到 |
| 3 | 471 | 231 | 19.6 | 找得到 |
| 4 | 129 | 100 | 5.4 | 找得到 |
| **5** | **44** | **24（選用）** | 1.8（R=0.8：1.0） | 找得到（共有 5／6，`img` 那條 5／5） |
| 6 | 23 | 11 | 1.0 | **找不到** |

選 K=5、R=0.8：K=6 就失去唯一的真實正例，所以它**剛好站在邊緣**（共有 5 條、min_shared 就是 5），我不把它說成有餘裕；要更靈敏就降到 K=4／R=0.8，代價是每套 CSS 多報約 3 個。
選用門檻下 24 組、其中**不同的分叉 8 個**（同一份站台 CSS 在 10 頁重複出現）：`.proj`／`.work-row`、`.hero .lede`／`.intro .lede`、
`#refcard`／`.pcard`、`.hero .av`／`.line .av`、`button,nav`／`input,select`、`.fig video`／`.fig-svg svg`——我判為真分叉或合理疑似 6 個——以及 `.hr`／`.hx`（按鈕重置）與
`.site-foot`／`.story-player figcaption`（都是「灰色小字橫排」）2 個雜訊。**沒壓得掉的雜訊類：** 泛用重置宣告（`background:none; border:none; cursor:pointer; color`）與共用設計值
（灰色小字＋flex）會湊滿門檻；A/B 對照頁的刻意差異；工具類 class（`.num`）在不同脈絡各自設大小。判讀是我按「是否值得抽成一個基底＋修飾」判的，不是第二個人看過的標註。

人讀交付物（`outputs` 15 份、產生頁 8 份）在選用門檻下 S3 只有 4 份各報 1～2 個分叉，C2 只有 3 份有發現；其餘安靜。

## 接線位置

| 誰呼叫 | 何時 |
|---|---|
| 研究專案的簡報建置閘（未出貨） | fit 三視窗之後，同一批 built html |
| paper-story `render_story.py` S7b | 每次渲染，緊接 S7 fit |
| 研究專案的案卷與討論包測試（未出貨） | DOM 段 |
| diagram-authoring `carrier-playbook.md` B-5 | 交付前的 containment 量測旁邊（上界之外補下界） |
| 全域規則 | `ops/environment.md` §Display（性質）、`rules/deliverable-doc-refs.md`（HTML 與產生器路徑觸發）、CLAUDE.md 一行 |

## 基準（修正前，2026-09-04 量測）

| 檔案 | class | 1707×830 reach | 判決 |
|---|---|---|---|
| 研究專案教科書／案卷 index | document-long | 69% | FAIL（靠左上限 1060px） |
| PaperSurvey onepage KEYPOINT 框 | deck | 框 65% 於同列獨佔 | WARN（區塊） |
| mfp-audit-f5 | diagram | 對稱 218/218px | PASS |
| 研究專案技術版簡報 | deck | 96% | PASS |
| audience-fit 前後對照 | document-short | 對稱 | PASS |

## 修正後（2026-09-04 同日量測，殼修好、重建鏈跑完）

| 檔案 | class | 1707×830 reach | 1920×950 | 判決 |
|---|---|---|---|---|
| 研究專案教科書（流動主欄＋本節速查 rail） | document-long | 100%（fill 95%） | 100%（96%） | PASS |
| 研究專案案卷 index ＋ 三案卷 | document-long | 100%（95%） | 100%（96%） | PASS |
| PaperSurvey 六篇 onepage／talk-deck（S7b） | deck | 93–100% | 97–100% | PASS |
| 研究專案四份簡報（fit_gate 內建 fill） | deck | 100% | 100% | PASS |
| HTMLToolsLobby 15 個工具（上限改 clamp 1920） | tool | 99% | 99% | PASS |
| cpo-architecture-v1／vault svg-diagram demo | diagram | 98%／91% | 92%／86% | PASS |
| audience-fit 前後對照（置中 900px） | document-short | 對稱 426/426 px | 532/532 px | PASS |

殼的已驗收行為回歸（hover 卡、點跳、Backspace、G 詞彙表、手機單欄、1280 隱藏 rail、列印隱藏 rail、
正對照）15/15，腳本在該輪的暫存區（未保留）；教科書在 390px 的橫向溢出（一個 `<th>` 與
nowrap 代號）**修正前就存在**，記為既有技術債，不在本輪。

review-when：螢幕或縮放改變（改 `reference_viewports`）；Anthropic 內建 artifact-design 的行寬措辭改變；
新增類別列（同一個 commit 補 fixture 對）；Playwright `page.evaluate` 語意改變。
