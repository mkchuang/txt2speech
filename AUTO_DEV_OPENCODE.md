# 自動化開發流程

> 目的：用 OpenCode CLI 負責 develop、Codex CLI 負責 code review / update-memory、Codex app 負責仲裁、驗證、commit 與可選 push。
> 原則：每個 CLI 階段都必須在同一個 session 內先執行 `adf.load-memory`，再執行該階段 action。
> 核心安全線：Memory Bank finalization、commit、push 都必須晚於 Codex app 的 scope / acceptance / verification gate。

## Inputs

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `TASK_ID` | yes | 例如 `TASK-002` |
| `MAX_REVIEW_LOOPS` | no | 預設 `3`，超過後停止並交由 Codex app 仲裁 |
| `TARGET_BRANCH` | no | 預設目前 branch |
| `REMOTE` | no | 預設 `origin` |
| `DO_COMMIT` | no | 預設 `no`；只有明確設為 `yes` 才 commit |
| `DO_PUSH` | no | 預設 `no`；只有明確設為 `yes` 或使用者明確要求才 push |

## Pipeline

### 0. Codex App Preflight

```text
Codex app:
  preflight:
    - 確認 WORKSPACE / git root / current branch
    - 確認 TASK_ID 存在於 active task backlog
    - 從 TASK_ID 解析 allowed file set
    - 檢查 git status 與 staged changes
    - 若 DO_PUSH=yes，先 git fetch REMOTE 並回報 ahead/behind
```

Preflight commands：

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git diff --cached --name-only
```

若 `DO_PUSH=yes`：

```bash
git fetch "$REMOTE"
git rev-list --left-right --count "$REMOTE/$TARGET_BRANCH"...HEAD
```

中止條件：
- `TASK_ID` 不存在或 active design / task backlog 無法判定。
- working tree 已有與本 task 無關的 staged changes。
- allowed file set 無法從 task backlog 或使用者指令界定。
- `DO_PUSH=yes` 但 local / remote branch 關係不清楚。

### 1. Develop

```text
OpenCode CLI:
  one session:
    $adf.load-memory
    $adf.develop TASK_ID
```

實際 CLI 範本：

```bash
opencode run --dir "$WORKSPACE" \
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.develop $TASK_ID。請依 TASK scope 實作與驗證；只處理 allowed file set 內檔案。不要 commit、push、stage 檔案。若需要更新 Memory Bank，請只列出 memory update candidate，不要把未 review / 未仲裁的狀態寫成 final done。"
```

要求：
- `adf.develop` 必須對應 approved plan / `TASK_ID` acceptance criteria。
- 只處理 `TASK_ID` scope 內的檔案。
- 不得刪除、覆蓋或 stage out-of-scope user files。
- 不得 commit / push。
- 若 agent 因 skill 規範實際修改 Memory Bank，該修改視為 provisional；Codex app 必須在 finalization gate 重新審核。
- 回報必須包含：修改檔案、驗證命令與結果、殘留風險、memory update candidate。

### 2. Review

```text
Codex CLI:
  one session:
    $adf.load-memory
    $adf.code-review TASK_ID
```

實際 CLI 範本：

```bash
codex exec -C "$WORKSPACE" \
  -s danger-full-access \
  --dangerously-bypass-approvals-and-sandbox \
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.code-review $TASK_ID。審查目前 git working tree 的 $TASK_ID 未提交變更，並檢查是否越出 allowed file set。請用 Critical/Major/Minor/Suggestion 分類；若可接受請明確寫 REVIEW PASS，否則寫 REVIEW FAIL 並列出 blocking findings。"
```

Review output 必須包含明確結論：

```text
REVIEW PASS
```

或：

```text
REVIEW FAIL
```

Findings 必須分級：
- `Critical`：阻擋 commit，必修
- `Major`：阻擋 commit，必修
- `Minor`：可由 Codex app 仲裁是否修
- `Suggestion`：不阻擋

Review 必須額外標示：
- 是否發現 out-of-scope diff。
- acceptance criteria 是否可由目前 evidence 支撐。
- 哪些驗證尚未由 reviewer 親自執行。

### 3. Review Fail Loop

若 review fail：

```text
OpenCode CLI:
  one session:
    $adf.load-memory
    $adf.develop <fix Critical/Major review findings for TASK_ID>
```

實際 CLI 範本：

```bash
opencode run --dir "$WORKSPACE" \
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.develop，修正 $TASK_ID code review findings。只修 Critical/Major blockers；不要修改、刪除或 stage out-of-scope user files；不要 commit、push、stage 檔案。完成後回報修改檔案、驗證結果與 memory update candidate。"
```

然後回到 **2. Review**。

中止條件：
- Review loop 次數超過 `MAX_REVIEW_LOOPS`
- Codex review 未輸出 `REVIEW PASS` / `REVIEW FAIL`
- OpenCode 修改 out-of-scope 檔案且無法安全分離
- Working tree 出現非本 task 的 staged changes
- 修正需要改變 approved plan 或 task scope

### 4. Codex App 仲裁與驗證

```text
Codex app:
  仲裁與驗證總控:
    - 檢查 TASK 驗收標準
    - 檢查 working tree 與變更 scope
    - 判斷 Codex CLI review 結論是否可信
    - 決定 Minor / Suggestion 是否需要回修
    - 補跑最小有效驗證
    - 必要時使用 Playwright / browser-use 做 E2E 或瀏覽器驗證
    - 決定是否進入 Memory Bank finalization
```

仲裁責任：
- 確認 OpenCode develop 是否真的完成 `TASK_ID`
- 確認 Codex review 是否明確輸出 `REVIEW PASS` 或 `REVIEW FAIL`
- Review fail 時整理 Critical/Major findings，交回 OpenCode 修正
- Review pass 時仍要抽查 acceptance criteria 與 staged scope
- 檢查 working tree diff 是否只包含 allowed file set
- 判斷 provisional Memory Bank diff 是否可信、是否太早宣告完成
- 發現驗證不足、scope 污染或 review 結論不可信時，中止 commit 並回到 fail loop

驗證責任：
- 依 `TASK_ID` 的 acceptance criteria 補跑 targeted verification
- 對 schema / API / UI / E2E 等高風險項目做二次確認
- 前端或端到端流程有變更時，啟動服務並做 browser 驗證
- 驗證命令與結果需在最終回報中摘要

E2E 適用時機：
- 前端 UI / browser workflow 有變更
- API 端到端流程有變更
- TASK 驗收標準明確要求 E2E

通過條件：
- Review output 為 `REVIEW PASS`。
- Critical / Major findings 為空。
- acceptance criteria 有實際 evidence。
- `git diff --name-only` 未超出 allowed file set，或超出的檔案已由使用者明確批准。
- 若 Memory Bank 有 provisional update，內容只包含 durable 狀態、驗證結果、殘留風險與下一步。

### 5. Memory Bank Finalization

只有 **4. Codex App 仲裁與驗證** 通過後才執行。

```text
Codex CLI:
  one session:
    $adf.load-memory
    $adf.update-memory
```

實際 CLI 範本：

```bash
codex exec -C "$WORKSPACE" \
  -s danger-full-access \
  --dangerously-bypass-approvals-and-sandbox \
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.update-memory。背景：$TASK_ID 已完成 code review 與 Codex app 仲裁驗證，REVIEW PASS，Critical/Major 無 blocker，acceptance criteria 已有 evidence。請更新 Memory Bank，只記 durable 狀態、驗證結果、殘留風險與下一步；不要寫入冗長流水帳。"
```

要求：
- Memory Bank 只記 durable 狀態、驗證結果、殘留風險與下一步。
- 不寫入冗長操作流水帳。
- 若 develop 階段已留下 provisional memory diff，Codex app 必須確認內容仍正確；不正確就修正或回到 fail loop。

### 6. Commit

只有 `DO_COMMIT=yes` 或使用者明確要求 commit 才執行。

```text
Codex app:
  final gate -> 精準 stage -> commit
```

Stage 規則：
- 禁止使用 `git add .`
- 只 stage `TASK_ID` scope 內檔案
- 可 stage 對應的 `.project/design/*` 與 `.project/memory/*` durable 更新
- 不 stage out-of-scope untracked files

Commit 前檢查：
- `git status --short`
- `git diff --cached --check`
- 最小有效驗證已通過
- Codex review 結論為 `REVIEW PASS`
- commit message 使用專案規範
- staged files 必須符合 allowed file set
- `DO_PUSH` 不得被 commit 階段隱含觸發

Commit message 格式：

```text
feat(scope): 簡短描述

Co-authored-by: <Agent Name> (<model-or-runtime>)
```

### 7. Push

只有 `DO_PUSH=yes` 或使用者明確要求 push 才執行；commit 不代表自動 push。

Push 前檢查：
- `git fetch "$REMOTE"`
- 回報 `REMOTE/TARGET_BRANCH` 與 local branch 的 ahead / behind 數。
- 確認目前 commit 是本輪產生或使用者指定要 push 的 commit。

Push：
- push 到 `REMOTE/TARGET_BRANCH`
- push 後確認 `git status --short`
- 若仍有 out-of-scope untracked files，回報但不刪除

## Safety Rules

- Memory Bank 與 Design 是 repo-local source of truth。
- 每次 CLI action 都必須在同一 session 內先 load memory。
- Codex app 必須先完成 preflight，並維護本輪 allowed file set。
- OpenCode 使用 `opencode run --dir "$WORKSPACE"`，確保工作目錄正確。
- Codex CLI 使用 `codex exec -C "$WORKSPACE" -s danger-full-access --dangerously-bypass-approvals-and-sandbox`，避免 approval/sandbox 阻擋自動流程。
- Prompt 內的 `\$adf.*` 必須 escape `$`，避免 shell 提前展開。
- Codex app 是最終仲裁者，不讓 develop agent 直接 commit/push。
- Memory Bank finalization 不得早於 Codex app 的 targeted verification。
- Commit 與 push 是兩個獨立決策；沒有明確 `DO_PUSH=yes` 或使用者要求時不得 push。
- 不自動刪除 user-owned 或 out-of-scope 檔案。
- 若 task scope、review finding 或 working tree 邊界不清楚，停止並回報仲裁。
