---
name: help
description: 查看 ai-dev-flow 指令清單、工作流程與目錄結構摘要
---

# Help

顯示目前可用的 ADF workflow、推薦順序與主要目錄結構。若提供 `$ARGUMENTS`，將其視為指定主題、指令名稱或想聚焦的工作流。

## 核心指令

- `design`：定義新專案的目標、範圍與技術方向
- `analyze`：掃描既有代碼並建立專案上下文
- `planner`：設計 implementation plan
- `breakdown`：將 plan 拆成 `TASK-xxx`
- `develop`：依批准方案直接實作
- `validate-plan`：評審設計文件
- `code-review`：審查實際代碼變更
- `load-memory` / `update-memory` / `archive-memory` / `archive-design` / `whoami`

## 推薦工作流程

### 新專案

1. `design`
2. `planner`
3. `validate-plan`
4. `breakdown`（可選）
5. `develop`
6. `code-review`
7. `update-memory`

### 既有專案

1. `analyze`
2. `load-memory`
3. `planner`
4. `validate-plan`
5. `breakdown`（可選）
6. `develop`
7. `code-review`

## 主要目錄

- `.project/`：memory、design、context 與 archive
- `.claude/`：Claude commands / agents
- `.opencode/`：OpenCode commands / agents
- `.codex/`：Codex agents
- `.agents/skills/`：Codex skills
- `.gemini/commands/`：Gemini executable commands；ADF 會在 `.gemini/settings.json` 停用同名 ADF skills 避免衝突

## 重要原則

- 先設計、後實作
- 未批准的 plan 不直接進入 `develop`
- 記憶與設計文件是單一真相來源
