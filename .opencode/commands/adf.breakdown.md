---
name: adf.breakdown
description: 將已批准的設計文件拆成可執行 TASK 清單
agent: task-planner
---

# Breakdown

## Overview

把已批准的 `plan-*.md` 轉成可執行的 task backlog。若提供 `$ARGUMENTS`，將其視為指定設計文件、phase 範圍或拆解限制。

## When to Use

- 已有 approved plan，需要拆成可交給 `develop` 的 `TASK-xxx`
- plan 已足夠穩定，但缺少依賴、驗收標準或實作順序
- 使用者要求 task list、breakdown、phase backlog 或 handoff-ready tasks

## When NOT to Use

- plan 尚未批准或仍有架構分歧，改用 `planner`
- 需求是審查 plan 是否可行，改用 `validate-plan`
- 使用者要直接實作已拆好的 task，改用 `develop`

## Inputs / Scope

- `$ARGUMENTS` 可指定 plan path、phase、task 編號範圍或拆解粒度限制
- 未指定時，優先讀 `.project/design/current.md`
- 輸出必須留在原 plan 或指定 task 文件中，保持與設計文件可追溯

## Escalation Boundary

- 若 plan 缺少必要決策、驗收不可判定或依賴無法解開，停止並回到 `planner`
- 若發現 task 拆解會改變架構承諾，停止並要求先更新 plan
- 不用模糊 task 或「研究一下」掩蓋無法交付的工作單元

## 執行步驟

1. 定位目標設計文件；未指定時，優先使用 `.project/design/current.md` 指向的 plan。
2. 讀取 design、decision、memory 與 context，確認目前已定稿的架構邊界。
3. 依據依賴關係拆成 `TASK-xxx`，每個 task 都要有 phase、優先級、依賴、檔案、驗收標準。
4. 明確標出關鍵路徑、可並行區段與風險較高的 task。
5. 將 task 清單回寫到設計文件或對應 task 文件，避免脫離原始 plan。

## 產出要求

- 每個 task 都應該是可執行、可驗收、可追蹤的最小工作單元
- 依賴圖必須無循環
- 驗收標準應對應具體檔案、命令或使用者可觀察結果

## 重要原則

- breakdown 不重做架構設計；若 plan 本身有矛盾，應先回到 `validate-plan` 或 `planner`
- task 粒度要足夠讓 `develop` 直接實作，不要停留在抽象待辦
- 不以「先做做看」掩蓋未決策項

## Next Step

- 驗證 plan 品質：交給 `validate-plan`
- 依 task 開始實作：交給 `develop`
