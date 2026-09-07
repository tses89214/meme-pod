# meme-pod

梗圖 T 恤全自動流水線：抓熱門梗 → 生成設計 → 上架 Redbubble → Telegram 通知。

## Bot 服務規則
這隻 bot 有 serving Telegram：從 TG 來的訊息，回應一律用 `reply` 工具回到 TG，不能只留在 transcript 裡。

Telegram channel 模式下不要用 `AskUserQuestion`（會卡住等不到 TG 訊息），改用 `reply` 工具打字問問題，把使用者下一則 Telegram 訊息當作答案。

## bot-mailbox 規則（2026-09-07 放寬，見 `~/.claude/bot-mailbox/README.md`）
點名 meme-pod 的訊息，只要是 meme-pod 自己專案範圍內的事（問狀態、或要求改自己的資料檔/cron/設定/寫筆記），
`bot_mailbox_check.py` 的隔離 `claude -p` 子行程可以自主判斷並直接動手做，不用等人在終端機當面確認。
meme-pod 沒有任何動用真錢的操作，不適用「真錢下單」那條限制。看不懂或不是在問 meme-pod 自己的事才不回覆，一律轉發 Telegram 通知使用者。

## 每次會話流程

### 上班打卡（會話開始時）
1. 讀 `.claude/PROGRESS.md` 了解當前狀態與下一步
2. 讀 `.claude/DECISIONS.md` 了解重要設計決策

### 下班打卡（會話結束或任務完成時）
1. 更新 `.claude/PROGRESS.md`（當前狀態、已完成、下一步）
2. 若有新的重要設計決策，補記到 `.claude/DECISIONS.md`
3. 把儲存在 local 的記憶捕進去 `.claude/MEMORY.md`
4. Commit 所有已完成工作

判斷標準：短任務（單次會話可完成）可不更新進度檔。跨會話任務或有重要決策時必須更新。

## Development Rules

These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

### Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

### Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

### Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

### Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

### Rule 5 — Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

### Rule 6 — Token budgets are not advisory
Per-task: 4,000 tokens. Per-session: 30,000 tokens.
If approaching budget, summarize and start fresh.
Surface the breach. Do not silently overrun.

### Rule 7 — Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

### Rule 8 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

### Rule 9 — Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

### Rule 10 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

### Rule 11 — Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

### Rule 12 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.
