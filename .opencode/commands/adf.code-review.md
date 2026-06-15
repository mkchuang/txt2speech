---
name: adf.code-review
description: 審查實際代碼變更，找出正確性、風險與測試缺口
agent: code-reviewer
---

# Code Review

## Overview

聚焦審查實際代碼 diff，而不是評審 plan。若提供 `$ARGUMENTS`，將其視為指定 diff、檔案範圍或審查重點。

## When to Use

- 使用者要求 review、code review、PR review 或安全檢查
- 工作樹、commit、PR 或指定檔案已有實際變更可審查
- 需要找出 bug、回歸風險、測試缺口或維護性問題

## When NOT to Use

- 審查對象是設計文件或任務拆解，改用 `validate-plan`
- 使用者要你直接修 bug 或實作功能，改用 `develop`
- 沒有可讀 diff、檔案範圍或明確審查基準

## Inputs / Scope

- `$ARGUMENTS` 可指定 PR、commit range、檔案、目錄或審查重點
- 未指定時，先讀目前工作樹 diff 與相關上下文
- 只審查實際變更，不把無關重構列為本輪要求

## Escalation Boundary

- 若缺少 base/head 或 diff 無法判定，先要求明確範圍
- 若發現設計層矛盾，將其標為需要 `planner` 處理，不在 code review 內重設計
- 若驗證需要外部環境，明確標示未驗證風險與建議 evidence

## 執行步驟

1. 取得待審查的變更範圍，必要時先確認 base/head 或工作樹 diff。
2. 以正確性、回歸風險、安全性、可維護性與測試完整性為主軸審查。
3. 優先列出 findings，依嚴重度排序並附檔案與行號參考。
4. 若沒有阻塞性問題，也要明確說明殘留風險與測試缺口。

## 輸出格式

- `Critical`：必須修復，阻擋合併
- `Major`：應該修復，影響品質或穩定性
- `Minor`：建議修復，改善可讀性或一致性
- `Suggestion`：可選優化

## 重要原則

- findings 優先於摘要
- 不用抽象評語取代具體問題
- 若審查對象其實是設計文件，應改用 `validate-plan`

## Next Step

- 有 blocker 時交回 `develop` 修正
- 無 blocker 時可接 `update-memory` 或提交流程
