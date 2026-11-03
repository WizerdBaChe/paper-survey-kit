---
xi: 1
what: paper-story 口述稿的實驗室慣例——從四份既有簡報的演講者備註原文抽出的開場公式、分段句、被問備忘、結尾「研究依據／對後續的幫助」 (talk-script conventions taken verbatim from the lab decks' speaker notes)
tags: [skill-reference, paper-story, talk-script, speaker-notes, lab-conventions]
aliases: [口述稿慣例, 演講者備註, 開場公式, 研究依據, lab speaker notes, talk conventions]
date: 2026-09-03
status: live
---

# Talk conventions — how this lab actually speaks (from the decks' notes)

Read on 2026-09-03 from the speaker notes of the four reference decks
(`labmate deck A` — per-slide narration; `labmate deck C` —
opening line and a closing synthesis; the other two carry no notes). The
first version of the talk script was NOT modelled on these; the user asked,
and this file is the correction. Patterns are quoted in the presenters' own
words so the register is theirs, not mine. In the public kit every example sentence quoted from a labmate's
talk is replaced by an invented one in the same register (the originals are unpublished talk notes); the
patterns, the counter-examples and the rules drawn from them are unchanged.

## 1. Opening formula (deck A, slide 1)

「教授、各位學長姐大家好，我是〇〇〇。今天我要報告的題目是《…》，這篇論文在 ＜年＞
年發表於 ＜期刊＞，主要探討蠟橋長度對紙基微流道延遲時間的影響。」

→ `talk.opening` = greeting to 教授、各位學長姐 + 我是 + 題目 + 年份與期刊 + 「主要
探討」 one clause. With the Keypoint page in front, the opening continues with
「我讀它是因為…，它對我的幫助是…」 before the outline.

## 2. Outline sentence (deck A, slide 2)

「這次的報告分為五個部分說明。」 → `talk.outline` = that sentence with the real
N and the part names.

## 3. Per-page narration (deck A, slide 3)

Plain background narration in short declaratives, one idea per sentence:
「首先簡單介紹紙基微流道的背景。紙基裝置不需要幫浦、成本很低。但多步驟檢測需要試劑
依序到達，所以需要計時元件。」
→ `deck.pages[].notes` in this register: what is SAID, not what is on the slide.

## 4. The parenthetical self-note for questions (deck A, slide 3)

「( Washburn：液體在多孔介質中前進的距離和時間的平方根成正比… 所以延遲大致隨
橋長平方增加。)」 — a bracketed mechanism note kept in the notes for when
someone asks. → `talk.if_asked[]` = `{q, a}`; the renderer prints them in
brackets at the end of the page's notes, exactly this way.

Question kinds (added 2026-09-14, researcher.tw B-13): `kind` = `clarify` (a fact the
audience missed — answer with the number and where it is), `challenge` (the method or a
claim is questioned), `extend` (what it means beyond the paper — answer from the
closing's 下一步). A challenge carries `challenge = {admit, reason, settle}`: 承認 →
為什麼這樣選（from the axis card）→ 什麼證據能定案, still in this plain register.
Journal-club questions are mostly challenges, so write those first. The bracket memo
stays the voice: the explainer's 口述稿 section (formerly `talk-script.md`) groups them by kind and prints a challenge as
「（q → 承認：…；為什麼這樣選：…；什麼證據能定案：…）」. The article's fourth kind
(questions asked to display the asker) needs no prepared answer and is not modelled.

## 5. Closing synthesis (deck C, last slide)

「這 10 篇文獻主要幫助我建立三個研究依據：第一，…；第二，…；第三，…。因此我的研究
就是想看，在＜結構＞中加入＜新條件＞後，是否能改善＜指標＞，同時觀察是否增加＜代價＞。」
and 「有什麼優化：讀這些論文後，我覺得最大的幫助是後續我可以量測＜量 1＞、＜量 2＞、
＜量 3＞…」

→ `talk.closing = {basis, help, next}`: 這篇（或這些）文獻幫我建立的研究依據 →
因此我的研究想看… → 對後續量測／設計的具體幫助（可量什麼、可調什麼）。This is
the lab's own version of 「對我有什麼幫助」 and it goes on the last deck page
and at the end of the explainer's 口述稿 section.

## 6. What the notes do NOT do (and this skill adds)

The reference notes never say why the authors chose their method, never
state the evaluation plan, and never mark where the paper's claim exceeds
its evidence. Those come from the axis card and the drift list; they are
spoken on the Method and Results pages in the same plain register, one
sentence each, e.g. 「他們選陽極化而不是乾蝕刻，是因為離子損傷區本來就長不出
多孔矽，可以直接當罩。」

## 7. Narrative voice — notes that tell the story (round 4, 2026-09-14)

Why this section exists: the presenter found the round-3 Tran script 「生硬」 — it reported
data and figure contents with no story and no correct 先後連接; the advisor asked that a talk
say up front why the paper is worth reading, what all its methods are, whether it reached its
goals and how that was judged, put figures first and explain them, and show how the paper tells
its research story. Read against three decks from 2026-08-31 … 09-07 (
labmate deck D, labmate deck E — single-paper talks in this lab; a conference talk (deck F)
multi-paper + patent survey, another lab, English notes). Quoted as patterns and counter-examples.

**Page shape: bridge → figure walk → why → takeaway → hand-off question.**

1. **Bridge** (`bridge`, the first spoken clause) picks up the previous page's question —
   「要知道損耗從哪裡來，作者先看平台上已經在用的兩種波導」. A page that opens on its own topic
   (「再來是元件的 IV 特性。」 deck D slide 8) is a list item, not a step of a story.
2. **Figure walk** (`figure_read`): point, then read — what the axes and panels are, what to
   look at, what it is compared with, so what. deck E slide 6 does it: 「右上這張圖是延遲時間和
   橋長的關係」 → the trend with bridge length → why 3 mm was chosen. The comparison sentence
   is the most valuable one (deck E slide 8: 「作者先做了一條沒有蠟橋的通道，因為它沒有
   經過部分熔融，所以可以用來比較…」). Counter: reading condition = value strings off the slide
   (deck D slide 8: 「在 23 °C、45 % RH 的條件下，L = 1 mm 延遲 42 s、L = 5 mm 延遲 612 s」) — the numbers
   are the highlight's job; the voice says what they mean.
3. **Why**: one sentence naming the constraint behind the choice (§6).
4. **Takeaway** (`takeaway`): the one sentence the audience carries out, said before moving on.
5. **Hand-off** (superseded by §8 item 3, round 7): end on the question the next page answers — 「實際到底量到多少，要看下一頁怎麼
   量。」 deck F slide 11 makes the same move inside one page ("Why is this related to BLT?" and
   then the answer). The presenter's final notes open each page by placing it in the structure instead.

Rules:

- **Premise before use.** A term, constraint or baseline appears on or before the page that
  relies on it (Tran: sidewall scattering, Fig. 3a, before the shallow rib, Fig. 2). Reordering
  the paper's figures for this is allowed; the page keeps the figure's own number.
- **Connectives carry the logic** — 因為／所以／但是／於是／那…; S20 counts ≥ 2 distinct per page.
  The count reads Chinese only (English notes are not measured) and is a proxy — the intro
  chain of deck D slides 4–5 (problem → prior fix → its flaw → this paper, 但是／因此) is what
  it is standing in for. What the proxy stands in for: each connective names the relation that
  actually holds between the two pages (contrast, cause, condition, extension, qualification,
  consequence) — `~/.claude/references/writing-norms/paragraph-plan.md` §2. A 所以 between two
  pages that are only in sequence passes S20 and still fails the talk.
- **Never read a highlight aloud, never speak a numbered process list** (deck D slide 6:
  「1. 印蠟 … 6. 加熱定形」) — say the one step that matters and why; the rest
  stays on the slide.
- **Say measured vs simulated.** Both single-paper decks name 「模擬」 among the methods that 驗證 the
  result; a simulation corroborates a mechanism, it does not verify a device. The Verdict page's
  status column is spoken, not only printed. This is the `real-device` axis of
  `~/.claude/references/writing-norms/claim-reach.md` §1; the same section names the other axes a
  closing sentence can overreach on (one champion device → `generality`, a fit → `mechanism`).
- **Opening concrete, key point at the close** (user ruling round 7, 2026-09-21, every deck — overturns round 5's
  「Keypoint搬回前面」, itself the reversal of round 4). The opening tells why read · the problem · the move ·
  whether it worked, through the Key points page; the slogan is shown AND spoken on the closing logic-chain /
  storyline page, after the paper is walked, where every step can point back at a page the audience has
  already seen. Saying it up front as well is allowed. S20 warns when the slogan is not spoken at the close.
- **The closing does not extrapolate past the verdict** (counter: deck D's conclusion
  「因此這個技術也可以應用在未來所有的＜應用＞上」).
- **No empty notes on a Results page** (deck E slide 7; deck F slides 5, 14, 15) and no self-memo in
  the voice (deck F slide 13 「TC 是什麼」) — memos go to `if_asked`.
- **Fit the slot — only when there is one.** Round 5 (user, 2026-09-14): 「時段沒有限制，只要完整都可以。
  因此語速跟字數都不是重點」 — `deck.minutes` is optional and a run without it skips the spoken estimate;
  completeness wins. When a slot IS given: a told page is longer than a reported one (Tran: ≈ 150 → 330 CJK-eq per page),
  so the voice has a budget: S17 prints the spoken estimate (CJK-eq ÷ 250 per minute — an
  assumption until the presenter times one rehearsal) beside the page-based cut plan. Over the
  slot, drop C pages and compress B pages before shortening a figure walk.

## 8. The notes voice — the presenter's own (round 7, 2026-09-21; every deck)

Source: the user's final `0921上台版本(中文).pptx` (Mu 2020), notes written by the presenter, ruled 「應該要有
的樣子」 (`formal-deck.md` §2c). Compared page by page with the notes paper-story put in the 0914 build (`lab-deck.pptx`).
Scope (user 2026-09-21: 「全部簡報都照這個改」; the deck's point is 「備註語氣」 and 「圖文搭配」): this section governs the
notes of EVERY deck — `deck.pages[].notes`, hence the formal deck and the explainer's 口述稿 section (formerly also the class A talk deck and `talk-script.md`) — for every
paper type. Where §7 disagrees, this section wins; §7's figure walk, why, premise-before-use and measured-vs-simulated
rules still stand. Quotes are the presenter's words.

Measured: 20 content pages, 165–608 chars per page (median ≈ 400), ≈ 8.5 k chars in all; CJK share 35–90 % (English terms
inline, never translated when the slide uses the English word); References slides carry no notes.

1. **Title note = the paper's identity and my honest reason**: year, publisher and journal, article type; the first author and
   the corresponding author with affiliation and position, and whether the group still works on the topic — two sentences, no
   biography; then why I chose it, in the modest register: 「雖然不是發表在頂級期刊的突破性文章，但…很適合拿來讓我學習如何整合
   各論文們的資料」. (The 0914 build's 998-char note — group history, students' later careers, source routes — was cut to 298.)
2. **Outline note = one roadmap sentence** in the order of the pages; no 「分為 N 個部分」 count required here.
3. **Open each page by placing it in the structure**, not with the previous page's hand-off question: 「前面四種都是在 XY 平面上
   改 taper 的形狀，接下來開始則進入利用 Z 方向的結構」, 「第二種 vertical 方法可以看成把剛才的多層 waveguide 做得更進一步」,
   「這頁就是進一步解釋上一頁為甚麼…」. The taxonomy is the thread; §7's 「那…？」 page endings do not appear.
4. **Mechanism first, in a plain image, then the term**: 「也就是直觀的『沒被吃進去』」, 「像走樓梯一樣，一層一層往下…transfer」,
   「叉子版本」. Explain what the structure does to the mode before any number.
5. **Answer the obvious question inside the narration**: 「但為甚麼不用特別大的 waveguide 截面積呢？」 → multimode. No bracketed
   if-asked memos in these notes.
6. **Walk a figure only where the reader could misread it**: 「這張圖是反方向呈現的…要從右往左看」, 「左邊是 top view…右邊則是
   side view」, 「圖中的 a 跟 b 是兩種不同版本」. The panel description the slide dropped (R7-6) lives here.
7. **Number, then its price**: 「可以做到 0.4 dB…但缺點也很直接，就多層 waveguide，就多一組…alignment 的製程控制問題」.
8. **One critical-reading caveat, only where it changes how to use the number**: text vs Table 1 disagree → 「當作結構性能的
   mapping，而不是拿來做非常精確的排名」; simulated vs measured; bandwidth defined at 1 dB vs 3 dB. Not in the voice: reference
   numbers, caption-error hunts, the paper's section locators, 「我不替作者下結論」 audit framing — those stay in
   `narrative-record.md` and in the 口述稿 section's bracketed if-asked memos, never in a page's narration.
9. **My project stays off the content pages**: relevance goes to the title note (why I read it) and the Conclusion (what later
   papers must add — CPO, multi-channel); no sentence about the presenter's own project on a family page.
10. **Conclusion note separates the author's stance from my two takeaways and the limits**; the logic-chain note retells the
    whole paper once as SITUATION → BUT → Steps, ending on what the review is really for (「提供一個可以繼續放入新 design 的分類框架」).
11. **Future-work note gives one reason per extension**, each tied to a family already shown (multi-layer SiN ← upper waveguides
    and multi-stage).
12. **No personal fact the task does not need, and none the user did not give** (user ruling 2026-11-01): a note in the presenter's voice states no circumstance, plan or history of the user beyond
    what the slide needs; an assumed circumstance (「我之後要做…」 never told) is a defect, not colour.

The renderers copy `deck.pages[].notes` into every product, so these rules bind whoever authors the notes at N4 / N6. The
Thanks slide's notes are free (user: 「那邊都是隨便講講」).

## 9. The ten-paper per-page walk — a labmate's pattern (user ruling 2026-11-03)

Source: a labmate's ten-paper talk (one page per paper), analysed page by page in the origin's reference
notes (not shipped).
Scope: the one-page-per-paper format (`presentation-formats.md` §1, `story@6`), not the single-paper deck of §1–§8. The page's
script, which now lives in the explainer's 口述稿 section and in the pptx notes, walks the page in this order:

1. **One source sentence** (`onepage.script.source_line`): 「這邊是 ＜年＞ 年發表在 ＜期刊＞ 的文章」 — every page has it.
2. **One purpose sentence** (`purpose_line`): 「主要是探討……」.
3. **Walk the tiles one by one, in argument order** (`tiles[].step`: context → series → trend → mechanism): 「圖 X 是 ＜縱軸＞
   對 ＜橫軸＞」 → 「可以看到……」 (with the number) → 「代表說／這可能是因為……」; the tile's `notes` carry exactly this.
   A side-evidence tile is announced as one — one sentence on the condition it establishes (`necessity`) — then the walk
   returns to the argument.
4. **The table is not read aloud**: speech = walking the figures, the table = the written summary the audience reads
   themselves. The clauses the density step cut from a cell go to the notes, not into a recitation of the table.
5. **No per-page closing**: the next page starts with its own source sentence. (That talk's opening and ending were not
   recorded, so whether the whole talk closes with 「對我的研究有什麼幫助」 is not established by this pattern; §5 still governs
   a single-paper talk.)

Length follows the number of tiles and the process complexity: a process + structure + transport page ≈ 3 min, a two-step
argument ≈ 1.7 min. §8's voice rules (plain-image mechanism, number-then-price, one caveat) apply inside each tile's notes.
