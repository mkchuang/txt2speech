---
name: validate-plan
description: 評審設計文件的完整性、一致性與開發可行性
agent: plan-reviewer
argument-hint: 可選：指定 plan、章節或想特別檢查的風險。
---

# Validate Plan

## Overview

專門審查 `plan-*.md`，不審代碼。若提供 `$ARGUMENTS`，將其視為指定 plan、特定章節或想特別檢查的風險。

## When to Use

- 使用者要求驗證、審查或確認 design plan 是否可交付
- plan 需要 handoff 給 `breakdown` / `develop` 前先找矛盾與缺口
- 依賴、phase、驗收標準、migration 或 rollout 風險重要

## When NOT to Use

- 審查對象是實際 code diff，改用 `code-review`
- plan 尚未形成，仍在產生方案，改用 `planner`
- 使用者要直接修 plan 或實作 task，改用 `planner` 或 `develop`

## Inputs / Scope

- `$ARGUMENTS` 可指定 plan path、章節、task 範圍或特別要驗證的 contract
- 未指定時，優先讀 `.project/design/current.md`
- 結論必須能讓使用者判斷是否可進入 `breakdown` / `develop`

## Escalation Boundary

- 若找出 blocker，輸出 `FAIL` 並指出具體修正，不繼續假設可開發
- 若只有局部風險，輸出 `WARN` 並列出可接受條件
- 不在 validate-plan 中重寫整個方案；需要改設計時交回 `planner`

## 執行步驟

1. 讀取目標 plan 與相關 `current.md`、decision、memory。
2. 檢查結構完整性、依賴關係、phase 切分、驗收標準與架構一致性。
3. 優先指出會阻塞 `develop` 的矛盾、遺漏或循環依賴。
4. 給出 `PASS` / `WARN` / `FAIL` 結論與具體修正建議。

## 檢查重點

- task 與 phase 是否可實作
- 規格是否前後一致
- 驗收標準是否可驗證
- rollout 與 migration 路徑是否合理

## 重要原則

- validate-plan 不審實作細節
- finding 要具體對應文件段落
- 若 plan 已足夠進開發，應明確說明可往下走

## Next Step

- plan 有 blocker：交回 `planner` 修正
- plan 可拆解：交給 `breakdown`
- plan 已有可執行 task：交給 `develop`
