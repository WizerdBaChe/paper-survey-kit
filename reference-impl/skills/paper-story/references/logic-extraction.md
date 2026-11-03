---
xi: 1
what: paper-story 的邏輯抽取（key point）規則——把故事線抽象成可移植的邏輯句、帶 warrant 的邏輯鏈、脆弱處與可移植性；含 Ow 2010 與 Zhang 2021 兩個帶 why 的範例 (logic extraction rules: abstract the storyline into a transferable logic with warrants, fragility and portability)
tags: [skill-reference, paper-story, logic-extraction, keypoint, toulmin]
aliases: [邏輯抽取, key point 新定義, 抽象邏輯句, 邏輯鏈 warrant, 脆弱處, 可移植性, logic chain]
date: 2026-09-03
status: live
---

# Logic extraction — the key point is an abstracted logic, with its whys

`paper-story` Stage N3. User definition (2026-09-03): 精煉 is not "the biggest
highlight"; it is 「基於一個貫徹全篇的邏輯敘事進行闡述再進行抽象化的邏輯抽取」 —
elaborate the storyline that runs through the whole paper, then abstract it
into its logic. The key point is that abstraction: what I now understand
about HOW THIS RESEARCH WAS CONSTRUCTED, stated so it could be reused on a
different problem. Every step carries a why (Toulmin's warrant); the first
draft of this rule had only how and what, and the user rejected it.

## 1. Output (`story.logic`)

| Field | Rule |
|---|---|
| `keypoint` | The SLOGAN. ONE sentence, ≤ 90 CJK-equivalent chars, in the abstract register: no material names, no numbers; verbs of construction (把…改當…、以…定…、依…逐項驗收、放開…掃描…). It must read as a pattern another paper could follow — **and it must not be over-abstract** (user ruling 2026-09-04, Test 0c): every role noun carries the qualifier that tells a reader which kind of thing it is (製程副作用, 面型自由度, 沉積化學根源 — never bare 副作用, 自由度, 根源). Printed verbatim by every product; never re-compressed into a box. |
| `keypoint_description` | The 讀書心得的終極詮釋 (user ruling 2026-09-04). One or two narrative paragraphs, 200–700 CJK-eq, that a reader who has NOT read the paper can follow: what the authors faced, what they did first / next / last with the paper's concrete nouns beside each abstract move, why each move follows, what I take away. Test: paste it alone into a note — does it work as the final interpretation of the reading? If not, it is not done. Required on `story@4`. |
| `bindings[]` | `{role, referent, locator}` ×≥3: every role noun or verb phrase of the slogan, copied verbatim, bound to what it stands for in THIS paper with the paper's own nouns (the event sentence Test 0 rejects AS the keypoint is exactly what belongs here). Every clause of the slogan (split on ；) has ≥1 binding — S15 FAIL otherwise. The one-page strip decorates each role with a hover card 在這篇＝referent. |
| `chain[]` | 3–5 steps, each `{step, in_this_paper, warrant, backing, qualifier}`: `step` = the move in abstract form; `in_this_paper` = the same move as the concrete event in this paper (required on @4 — a telegram like 「副作用 → 控制元件」 alone is what the user rejected on 2026-09-04); `warrant` = WHY the step follows from the previous one (the belief or constraint that licenses it); `backing` = where the paper supports it (locator) or `[inferred]`; `qualifier` = how far it holds (Toulmin's qualifier: "on these samples", "in geometric optics"). |
| `patterns[]` · `relations[]` | optional: 1–3 kebab-case slugs naming the reusable pattern(s) (`side-effect-as-boundary`, `one-free-variable-scan`, `replace-root-cause`…) and explicit links to other library runs with the why — the library's `KEYPOINTS.md` and each run's `keypoint.md` are generated from them (2026-09-04). |
| `fragile` | `{what, why}`: the weakest link and why it is weakest (usually the beat whose why is `[assumed]` or whose evaluation had no criterion). |
| `portable` | `{where, why, when_not}`: where I could reuse the logic (the user's project, named), why it transfers, and when it would not. |

## 2. Three tests (replace the old "whole-paper / author / consistency")

**Test 0 — rule vs event** (user ruling 2026-09-03, Ow 2010). Replace every noun in
the key point by its ROLE. If the sentence still instructs a builder, it is a rule;
if it needs the paper's nouns to mean anything, it is an event description and is
rejected even when it contains no numbers. The user chose run B's

> 把製程副作用當成下一步的邊界，讓形狀由邊界自行收斂；把單一宣稱拆成幾個可視的驗收
> 動作；最後把既有能力疊上同一載體，當作延伸而非新能力。

over the main session's 「把上一步製程的副作用改當下一步的控制元件，讓光罩幾何直接
決定產物尺寸；再依應用指標逐項驗收，最後示範平台能與既有能力疊合」— the second
passed the no-numbers test and still narrates this paper (光罩、產物、平台 are its
nouns, not roles); the first is a rule anyone could apply to another process.

**Test 0b — binding** (user finding 2026-09-04, on the three accepted one-pages). After Test 0
passes, list every role noun and verb phrase of the slogan and write beside each what it IS in
this paper (`bindings[]`). A role you cannot bind is a hole; a hole invites a wrong reading, and
「錯誤的詮釋比沒解釋更糟糕」. The user's own examples: Ow's 形狀 and 載體, Zhang's 結構、自由度、
模型、最低點 and the actions 掃過候選、定位, Bose's 操作範圍兩端、下游各自指標、問題原本座標 — all
bindable, none bound on the page. The slogan is still the rule; the bindings are the explanation
the rule cannot carry.

**Test 0c — not over-abstract** (user ruling 2026-09-04: 「slogan 的文字描述不應該過度抽象」). Read
the slogan alone: can a reader place each role in a KIND of thing (a process side-effect, a shape
degree of freedom, a deposition chemistry) without the bindings? If a role is bare (副作用, 自由度,
根源, 載體), give it its qualifier (製程副作用, 面型自由度, 沉積化學根源, 同一電化學載體). The 70-char
cap moved to 90 for exactly this; the paragraph-length reading goes to `keypoint_description`, never
into the slogan.

1. **Abstraction test** — delete every noun that names a material, device,
   instrument or number; does the sentence still say something? If it
   collapses, it was a summary. (「在矽上用離子照射做凹面鏡」collapses; 「把上一步
   製程的副作用改當下一步的控制元件」survives.)
2. **Why test** — for each chain step, ask 「為什麼作者敢走這一步？」 and check the
   warrant answers it with a constraint or belief, not with a restatement.
   A chain with an empty warrant is not extracted logic; it is a table of contents.
3. **Reuse test** — can `portable.where` name a concrete decision in the
   user's project that the logic would change? If not, the abstraction floated
   too high; add one qualifier back.

## 3. Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| "方法＋證據＋邊界壓成一句" | still a content summary (the v1.1 mistake) |
| "這篇證明了 X" | that is the paper's claim, not its logic |
| axis phrased as 「能不能…」 with no 為什麼 | a question without its reason is not an axis |
| chain steps without warrants | how/what only — the exact defect the user named |
| abstraction with no `portable.where` | floated too high to be a learning |
| a key point that mentions a figure number | not abstract |
| the slogan printed alone, roles unbound (「讓形狀由邊界自行收斂」 with no 形狀 = …) | Test 0b hole — the reader cannot re-explain it even after reading the paper (2026-09-04) |
| the slogan re-compressed to fit a box (連接詞、限定詞被刪) | a second lossy pass on an already-abstract sentence; the box is gone on @4 |
| a bare role noun (自由度, 載體) where the paper's kind of thing is known | Test 0c over-abstraction — add the qualifier, not the paper's proper noun |
| `keypoint_description` that is the slogan again, or a summary of results | not the 讀書心得終極詮釋 — it must walk first / next / last with concrete nouns and whys |

## 4. Worked examples (with the whys the first round lacked)

These two examples teach the FORM. They are also the library's own runs: a `story`-mode
page on either paper does not re-derive from them — it cites the deep run
(`logic.reused_from`, SKILL.md Intake 「library check」; round 2 run S1 reused this
section's Ow sentence verbatim because the brief forbade the sibling folder, which is the
same outcome by the wrong path).

> These two examples ARE the first real runs' papers (Ow 2010, Zhang 2021). A
> run on either of them is therefore a consistency test, not a blind test — both
> 2026-09-03 calibration agents flagged this themselves. Calibration papers must
> be papers not worked here; a future blind calibration takes a third paper.

### Ow 2010 — Fabrication of concave silicon micro-mirrors

- 切入點：矽上凹面微鏡的製程要「簡單且可控」。**為什麼是這個切入點**：凹面微鏡的
  應用（光鑷、腔 QED、互連）都要位置精準、可陣列化；既有矽路線靠 HF/HNO₃ 濕蝕加
  多步驟硬罩（步驟多、對位難），氣泡法位置隨機；而這個群組手上正好有大面積離子
  照射微加工與多孔矽（PSi）犧牲層的工具鏈（他們自己的 Ref 15–19）——切入點是
  「用手上工具的一個已知性質去解別人的罩問題」 `[inferred，p.2 §1.1–1.2]`。
- 邏輯抽取（key point）：「把製程副作用當成下一步的邊界，讓形狀由邊界自行收斂；把單一
  宣稱拆成幾個可視的驗收動作；最後把既有能力疊上同一載體，當作延伸而非新能力。」
  （2026-09-03 使用者裁定採 run B 的規則句；主 session 原句「把上一步製程的副作用改當下一步
  的控制元件，讓光罩幾何直接決定產物尺寸；再依應用關心的指標逐項驗收產物；最後示範平台能與
  既有能力疊合」是事件描述——見 §2 Test 0。）
- 邏輯鏈（含 warrant）：
  1. 副作用→控制元件。warrant：離子損傷區電阻升高、PSi 長不動（Ref 17 已知），所以
     它天然是 HF 陽極化的抗蝕罩——不用另外鍍硬罩。backing p.3 §1.2–§2。qualifier：
     劑量夠高（3×10¹⁴）才完全停止。
  2. 幾何→尺寸自停止。warrant：等向蝕刻前緣從中心孔往下、往兩側等速擴張，兩側在環
     下方相遇就不再擴大，所以 D = C + A 由光罩決定，不靠時間控制。backing p.4 §2、
     Fig. 3。qualifier：深度 ≥ A/2 才會合。
  3. 指標逐項驗收。warrant：應用要的是「能聚焦的平滑球面」，所以驗收項是形狀
     （SEM）、粗糙度（AFM）、光學功能（焦點）——每項一張圖。backing Fig. 2–5。
     qualifier：n = 3、1 顆；沒有門檻。
  4. 疊合示範。warrant：同一電化學平台能用電流密度調 PSi 孔隙率（折射率），所以
     凹面上直接長 DBR 是平台的自然延伸。backing p.7–8 §3.2、Fig. 6。qualifier：只
     有影像與線掃，無光譜。
- 脆弱處：第 2 步的「可控」只有機制論證沒有分布量測；第 3 步驗收沒寫門檻——
  為什麼脆弱：故事的價值全押在「可控」，而可控恰好是唯一沒被量的。
- 可移植：另一種基材上的同類微鏡製程。為什麼可移植：邏輯不依賴矽，依賴「某一步的副作用能當
  下一步的罩」與「幾何自停止」；何時不可移植：新基材上找不到自停止的等向蝕刻化學時，
  第 2 步整段失效，只能借第 3 步的驗收表。

### Zhang 2021 — Aspheric and spherical concave micro-mirror for vertical coupling

- 切入點：凹面鏡的面型（conic k）是否還能再降垂直耦合損耗。**為什麼是這個切入點**：
  同組前作已把球面凹面鏡做到 1.02 dB、平面 45° 鏡 4.56 dB，反射式路線本身已被
  接受；剩下沒被動過的自由度只有「面型」，而非球面的會聚能力理論上更強、卻沒人
  用在垂直耦合——切入點是「在已被接受的結構上放開最後一個自由度」 `[inferred，p.1 §1]`。
- 邏輯抽取：「在已被接受的結構上放開一個自由度，以單一指標做參數掃描找最佳點，
  用歷史基準定位改善幅度；模擬先行，製作留待下一步。」
- 邏輯鏈（含 warrant）：
  1. 放開自由度。warrant：其他自由度（材料、NA、尺寸）已由前作固定，只剩面型；
     conic 方程用一個 k 就涵蓋五種面型，掃描成本低。backing p.1 §2、Eq. 1。
  2. 單一指標掃描。warrant：垂直耦合的價值只看損耗，且幾何光學在 300–600 µm 尺度
     足夠，所以 ray tracing 掃 θ 與 R 即可。backing p.2 §2、Fig. 2。qualifier：
     忽略繞射、公差、波長。
  3. 歷史基準定位。warrant：讀者只認前作數字，所以用 4.56／1.02 dB 定位 0.8 dB。
     backing p.2–3。qualifier：模擬對量測，跨方法比。
  4. 模擬先行。warrant：會議短文、先佔位；製作留待 freeform 下一步。backing p.3 §3。
- 脆弱處：第 3 步——自己模擬的球面 1.28 dB 沒有和前作 1.02 dB 對齊基準就拿來比；
  為什麼脆弱：改善幅度的可信度全靠基準一致。
- 可移植：自己專案的選型。為什麼可移植：「放開一個自由度、單一指標掃描」不依賴材料；
  何時不可移植：自己專案的評估若不只一個指標（例如還有公差、波段），單一指標掃描會漏掉真正的
  約束。

## 5. Where the key point goes

- The one-page's Keypoint strip prints `logic.keypoint` VERBATIM (no `keypoint_box`
  since @4 — the box invited a second compression), with each bound role decorated
  for a hover card 在這篇＝referent, and a closed 「展開解讀」 toggle holding the
  `keypoint_description` and the role table. Class A only; the lab layout is
  untouched until the reader opens it (ruling R3-1, 2026-09-04).
- The one-page's pages 2–3 (class A): 「Keypoint 解讀」 = slogan + description + role
  table; 「邏輯鏈」 = the chain with 在這篇 / warrant / qualifier / backing, then
  fragile + portable. The glossary follows.
- `deck.pages[0]` — the Keypoint page: why I read it / what it helps me with /
  the slogan (roles decorated) + the bindings in one line + the description under
  a toggle / the entry point with its why.
- `paper-explainer.html` — its Keypoint section prints the slogan, 解讀 and the bindings table, and the 口述稿 section
  follows the lab's speaking formula, so the spoken opening can say what each role is. (Until 2026-11-03 the Keypoint
  line, 解讀 and bindings were the preamble of a separate `talk-script.md`; that file is no longer written — historical.)
- `narrative-record.md` §1 — slogan, 解讀, role table, the full chain with 在這篇 and
  warrants.
- Class B (the lab's PPTX) prints the slogan only; the presenter carries the reading.
- `keypoint.md` (per run) + `KEYPOINTS.md` (library) — generated by `library.py`
  from `logic` (2026-09-04): the Obsidian 論文核心邏輯快速關聯索引.

### Worked bindings for the two examples (Test 0b applied, 2026-09-04)

Ow 2010 — 製程副作用＝離子照射的損傷區長不出多孔矽 (p.3 §1.2)；下一步的邊界＝那個損傷區直接當
HF 陽極化的抗蝕罩 (p.3 §2)；形狀＝球面凹鏡的直徑 D＝C＋A，由光罩環寬決定 (p.4 §2, Fig.3)；可視的驗收
動作＝SEM 形貌、AFM 粗糙度、顯微鏡量焦點各一張圖 (Fig.2–5)；既有能力＝同一電化學平台調 PSi 孔隙率
(p.7 §3.2)；同一載體＝凹面本身，在其上直接長 DBR (Fig.6)。

Zhang 2021 — 既有結構＝同組前作已接受的反射式凹面鏡垂直耦合路線 (p.1 §1)；最後一個自由度＝
鏡面的面型，conic 常數 k (Eq.1)；同一模型＝ray tracing，先掃安裝角 θ 再掃半徑 R (p.2 §2, Fig.2)；
最低點＝每種 k 在其最佳 R 下的耦合損耗 (Table 1)；舊基準＝前作的 1.02 dB 球面與 4.56 dB 平面鏡 (p.1)；
驗證留給下一步＝製作與量測留給 freeform 後續 (p.3 §3)。
