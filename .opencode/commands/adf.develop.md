---
name: adf.develop
description: 依已批准設計或 TASK 實作代碼並完成驗證
agent: developer
---

# Develop

## Overview

基於已批准的 `plan-*.md` 或 `TASK-xxx` 直接實作。若提供 `$ARGUMENTS`，將其視為指定 task、phase 範圍或實作限制。

## When to Use

- 已有 approved plan、明確 TASK，或使用者明確指定要實作的設計文件
- 需求重點是修改代碼、模板、測試或文件產物，而不是重新設計架構
- 驗收標準可從 plan、TASK 或使用者指令中直接讀出

## When NOT to Use

- 需求仍在比較方案、技術選型或架構邊界未決，改用 `planner`
- 使用者只要求設計審查，改用 `validate-plan`
- 沒有 plan / task / 明確 scope，且合理預設會造成大範圍變更

## Inputs / Scope

- `$ARGUMENTS` 可是 plan path、TASK id、phase 名稱、檔案範圍或限制條件
- 未提供 `$ARGUMENTS` 時，讀取 `.project/design/current.md` 找下一個可執行 task
- 只實作本輪 scope 內的交付物；遇到相鄰但未列入 plan 的 gap，記為 follow-up

## Escalation Boundary

- 發現 plan 自相矛盾、缺少必要決策或驗收不可判定時，停止並回到 `planner`
- 發現實作會跨越 plan 明確禁止修改的模組時，停止並請使用者決策
- 發現測試需要不可用的外部系統時，提供可替代的最小 evidence，而不是假裝已驗證

## 執行步驟

1. 載入目前 plan、decision、workspace memory 與相關 context。
2. 確認本輪要交付的 task 與驗收標準，必要時先釐清阻塞條件。
3. 直接修改代碼、補測試並驗證結果，不只停留在分析或提案。
4. 若遇到新的架構決策，停止擴張範圍並回到 `planner`。
5. 更新工作記憶，記錄完成項、剩餘風險與下一步。

## 驗收要求

- 實作結果必須對應已批准的 plan 或 task
- 有對應驗證：測試、lint、CLI 驗證或使用者可觀察結果
- 不得用 workaround 掩蓋根因

## 重要原則

- 先理解再下手，但理解完成後就直接實作
- 不替使用者做新的架構決策
- 若工作樹有他人變更，不擅自回退

## Next Step

- 完成後執行對應測試與 `update-memory`
- 若需要審查實際 diff，交給 `code-review`
