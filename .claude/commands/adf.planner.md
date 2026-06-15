---
name: planner
description: 為功能或系統變更設計可執行的 implementation plan
agent: architect
argument-hint: 可選：提供需求摘要、限制條件或指定設計範圍。
---

# Planner

## Overview

用於基於既有 project-level baseline 回答「要怎麼細部實作」。若提供 `$ARGUMENTS`，將其視為需求摘要、限制條件、指定功能、指定 phase 或指定設計範圍。

## When to Use

- `adf.design` 已建立 project brief / architecture baseline，需要細化為 implementation plan
- 需求需要技術方案、架構邊界、ADR、migration 或 rollout 設計
- 現有 plan 不足以直接交給 `develop`
- 使用者正在比較方案或需要明確風險與驗收策略

## When NOT to Use

- 只是專案初始定義、產品範圍、tech stack 盤點或全專案大框架尚未建立，改用 `design`
- 已有 approved plan 且只缺實作，改用 `develop`
- 要審查既有 plan 的品質，改用 `validate-plan`

## Inputs / Scope

- `$ARGUMENTS` 可是需求摘要、既有 plan path、限制條件、指定模組、指定功能或指定 phase
- 未提供時，讀 `project.md`、`.project/design/current.md`、memory 與 context；若只有 project baseline 而沒有指定 feature / phase，預設細化整個 baseline，不只規劃 Phase 1
- 輸出必須能被 `breakdown` 或 `develop` 消費

## Escalation Boundary

- 若 `project.md` 缺少系統大框架、核心模組或 roadmap，停止並要求先回到 `design` 補 baseline
- 若需求含重大產品或安全取捨，明列 options 並等待使用者批准
- 若缺少必要事實，先用可驗證來源補齊；不能補齊時列為 open question
- 不在 planner 階段直接修改實作代碼

## 執行步驟

1. 載入 `project.md` 的 project-level baseline、`current.md`、decision records、memory 與 context，確認現有架構邊界。
2. 判斷本輪 scope：未指定功能或 phase 時，針對整個 baseline 做細部 implementation plan；有指定時才收斂到該 feature / phase。
3. 分析需求、風險、影響範圍與替代方案。
4. 產出 implementation plan，必要時補 ADR、遷移策略、測試策略與 rollout path。
5. 明確標示假設、風險與待決策點，等待批准後才進入開發。

## 產出要求

- 設計文件使用 repo 既有命名規則：`plan-YYYY-MM-DD-[short-kebab-topic].md`
- bugfix / refactor 可使用 `plan-YYYY-MM-DD-fix-[short-kebab-issue].md` 或 `plan-YYYY-MM-DD-refactor-[short-kebab-target].md`
- topic slug 必須描述實際主題，不可使用空泛的 `feature-name`、`new-feature` 或 `phase-1`
- 必要時補 `ADR-*`
- plan 內容必須符合 architect 的 `Plan Output Format Contract`
- 交代整體驗收方式、分階段路徑與風險控管；Phase 1 只能是 rollout 的第一段，不能取代 whole-project plan

## 重要原則

- planner 產出的是可被實作與驗證的方案，不是高層空話
- 若缺少 project-level baseline，應回到 `design`
- 未指定 feature / phase 時，不可自行把 whole-project planning 收窄成 Phase 1
- 未經批准不得直接執行實作

## Next Step

- 審查設計品質：交給 `validate-plan`
- 將 plan 拆成 tasks：交給 `breakdown`
