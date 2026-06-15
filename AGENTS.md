# AI Development Configuration v6

> Claude Code、OpenCode、Codex CLI、Gemini CLI 共用的專案入口指南。
> `CLAUDE.md`、`AGENTS.md`、`GEMINI.md` 內容應保持一致。
> 版本：v6.0.0

## 工作約定

- 對使用者回覆時使用繁體中文。
- 進行實質變更前，先讀 `.project/memory/`、`.project/design/current.md`、`.project/context/`。
- Memory Bank 與 Design 是 repo-local source of truth。
- 依已批准的 plan 與 `TASK-xxx` 推進，不自行發明新架構。
- 除非使用者明確要求，避免覆蓋 `.project/` 下的 user-owned 路徑。
- 回報保持簡潔、具體，並附上實際驗證結果。

## 真實來源

- 專案全貌：`.project/memory/project.md`
- 團隊狀態：`.project/memory/workspace-team.md`
- 個人記憶：`.project/memory/workspace-mk-chuang.md`
- 單人模式記憶：`.project/memory/workspace.md`
- 當前設計：`.project/design/current.md`
- 設計、歸檔與 ADR：`.project/design/`
- 專案上下文：`.project/context/`

## ADF 指令與技能

V6 工作流程一律使用 `adf.` 前綴。

| 工作流程 | Claude/OpenCode/Gemini 指令 | Codex 技能 |
| --- | --- | --- |
| 說明 | `/adf.help` | `$adf.help` |
| 載入記憶 | `/adf.load-memory` | `$adf.load-memory` |
| 身份與狀態 | `/adf.whoami` | `$adf.whoami` |
| 專案定義 | `/adf.design` | `$adf.design` |
| 代碼分析 | `/adf.analyze` | `$adf.analyze` |
| 架構規劃 | `/adf.planner` | `$adf.planner` |
| 驗證計畫 | `/adf.validate-plan` | `$adf.validate-plan` |
| 任務拆解 | `/adf.breakdown` | `$adf.breakdown` |
| 開發實作 | `/adf.develop` | `$adf.develop` |
| 代碼審查 | `/adf.code-review` | `$adf.code-review` |
| 更新記憶 | `/adf.update-memory` | `$adf.update-memory` |
| 歸檔記憶 | `/adf.archive-memory` | `$adf.archive-memory` |
| 歸檔設計 | `/adf.archive-design` | `$adf.archive-design` |

## 安裝路徑

| 工具 | 指令 / 技能 | Agents |
| --- | --- | --- |
| Claude Code | `.claude/commands/adf.*.md` | `.claude/agents/` |
| OpenCode | `.opencode/commands/adf.*.md` | `.opencode/agents/` |
| Codex CLI | `.agents/skills/adf.*/SKILL.md` | `.codex/agents/` |
| Gemini CLI | `.gemini/commands/adf.*.toml` | 無 agents；ADF skills 由 `.gemini/settings.json` 停用以避免同名衝突 |

## 開發流程

1. `adf.load-memory` 還原專案上下文。
2. 新專案使用 `adf.design`，既有 repo 使用 `adf.analyze`。
3. `adf.planner` 建立或更新 implementation plan。
4. 計畫品質或 handoff 風險重要時，執行 `adf.validate-plan`。
5. 需要可執行任務時，執行 `adf.breakdown`。
6. 已批准工作用 `adf.develop` 實作。
7. 實際變更用 `adf.code-review` 審查。
8. 有 durable 決策、進度或風險時，執行 `adf.update-memory`。

## Git 與驗證

- Commit 應保持單一職責。
- Commit message 以中文為主，必要時保留英文技術名詞。
- 依變更範圍執行最小但有效的驗證。
- 變更 template 或 installed artifact 時，提交前檢查 manifest 與 drift。
- AI 協助的提交需使用通用 footer，不得硬編單一 agent 身份：

```text
Co-authored-by: <Agent Name> (<model-or-runtime>)
```
