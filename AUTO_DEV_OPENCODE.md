# 自動化開發流程

> 目的：用 OpenCode CLI 負責 develop、Codex CLI 負責 code review / update-memory、Codex app 負責仲裁與 commit/push。
> 原則：每個 CLI 階段都必須在同一個 session 內先執行 `adf.load-memory`，再執行該階段 action。

## Inputs

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `TASK_ID` | yes | 例如 `TASK-002` |
| `MAX_REVIEW_LOOPS` | no | 預設 `3`，超過後停止並交由 Codex app 仲裁 |
| `TARGET_BRANCH` | no | 預設目前 branch |
| `REMOTE` | no | 預設 `origin` |

## Pipeline

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
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.develop $TASK_ID。請依 TASK scope 實作、驗證，並依 adf.develop skill 規範更新 Memory Bank。"
```

要求：
- `adf.develop` 必須依 skill 規範更新 Memory Bank。
- 只處理 `TASK_ID` scope 內的檔案。
- 不得刪除、覆蓋或 stage out-of-scope user files。

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
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.code-review。審查目前 git working tree 的 $TASK_ID 未提交變更。請用 Critical/Major/Minor/Suggestion 分類；若可接受請明確寫 REVIEW PASS，否則寫 REVIEW FAIL 並列出 blocking findings。"
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
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.develop，修正 $TASK_ID code review findings。只修 Critical/Major blockers；不要修改、刪除或 stage out-of-scope user files。完成後請依 adf.develop skill 規範更新 Memory Bank，並回報修改檔案與驗證結果。"
```

然後回到 **2. Review**。

中止條件：
- Review loop 次數超過 `MAX_REVIEW_LOOPS`
- Codex review 未輸出 `REVIEW PASS` / `REVIEW FAIL`
- OpenCode 修改 out-of-scope 檔案且無法安全分離
- Working tree 出現非本 task 的 staged changes

### 4. Review Pass

若 review pass：

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
  "請依序在同一個 session 內執行 \$adf.load-memory 與 \$adf.update-memory。背景：$TASK_ID 已完成 code review，REVIEW PASS，Critical/Major 無 blocker。請更新 Memory Bank，只記 durable 狀態、驗證結果、殘留風險與下一步；不要寫入冗長流水帳。"
```

要求：
- Memory Bank 只記 durable 狀態、驗證結果、殘留風險與下一步。
- 不寫入冗長操作流水帳。

### 5. Codex App 仲裁與驗證

```text
Codex app:
  仲裁與驗證總控:
    - 檢查 TASK 驗收標準
    - 檢查 working tree 與變更 scope
    - 判斷 Codex CLI review 結論是否可信
    - 決定 Minor / Suggestion 是否需要回修
    - 補跑最小有效驗證
    - 必要時使用 Playwright / browser-use 做 E2E 或瀏覽器驗證
    - 決定是否進入 commit/push
```

仲裁責任：
- 確認 OpenCode develop 是否真的完成 `TASK_ID`
- 確認 Codex review 是否明確輸出 `REVIEW PASS` 或 `REVIEW FAIL`
- Review fail 時整理 Critical/Major findings，交回 OpenCode 修正
- Review pass 時仍要抽查 acceptance criteria 與 staged scope
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

### 6. Commit And Push

```text
Codex app:
  仲裁 -> 精準 stage -> commit -> push
```

Stage 規則：
- 禁止使用 `git add .`
- 只 stage `TASK_ID` scope 內檔案
- 可 stage 對應的 `.project/design/*` 與 `.project/memory/*` durable 更新
- 不 stage out-of-scope untracked files

Commit 前檢查：
- `git diff --cached --check`
- 最小有效驗證已通過
- Codex review 結論為 `REVIEW PASS`
- commit message 使用專案規範

Commit message 格式：

```text
feat(scope): 簡短描述

Co-authored-by: Claude (GPT-5.5)
```

Push：
- push 到 `REMOTE/TARGET_BRANCH`
- push 後確認 `git status --short`
- 若仍有 out-of-scope untracked files，回報但不刪除

## Safety Rules

- Memory Bank 與 Design 是 repo-local source of truth。
- 每次 CLI action 都必須在同一 session 內先 load memory。
- OpenCode 使用 `opencode run --dir "$WORKSPACE"`，確保工作目錄正確。
- Codex CLI 使用 `codex exec -C "$WORKSPACE" -s danger-full-access --dangerously-bypass-approvals-and-sandbox`，避免 approval/sandbox 阻擋自動流程。
- Prompt 內的 `\$adf.*` 必須 escape `$`，避免 shell 提前展開。
- Codex app 是最終仲裁者，不讓 develop agent 直接 commit/push。
- 不自動刪除 user-owned 或 out-of-scope 檔案。
- 若 task scope、review finding 或 working tree 邊界不清楚，停止並回報仲裁。
