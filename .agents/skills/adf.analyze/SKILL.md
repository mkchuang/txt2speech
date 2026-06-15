---
name: adf.analyze
description: 掃描現有代碼庫並產出專案全貌與模組索引
agent: analyst
---

# Analyze

## Overview

用於理解既有專案，而不是設計新功能。若提供 `$ARGUMENTS`，將其視為分析範圍、優先模組或額外限制。

## When to Use

- 使用者要求掃描、分析或建立既有 repo 的專案全貌
- Memory Bank 或 `.project/context/modules.md` 不存在、過期或與現況不符
- 新接手 repo 時需要產生可供 `planner` / `develop` 使用的 file-backed context

## When NOT to Use

- 使用者要設計新功能或新架構，改用 `planner`
- 使用者只想查看已知狀態，改用 `load-memory`
- 已有明確 approved plan 且目標是實作，改用 `develop`

## Inputs / Scope

- `$ARGUMENTS` 可指定目錄、模組、技術面、分析深度或限制條件
- 未指定時，從 repo root、`.project/memory/` 與 `.project/context/` 建立全域分析範圍
- 分析結論必須回寫到 Memory Bank / context，而不是只輸出口頭摘要

## Escalation Boundary

- 若分析發現使用者真正需要的是功能方案，停止擴大掃描並轉回 `planner`
- 若 repo 太大或外部依賴不可取得，明確標出未掃描範圍與殘留風險
- 不把未讀到的模組、生成物或歷史假設寫成已確認事實

## 執行步驟

1. 載入 `.project/memory/`、`.project/context/` 與現有設計文件，確認是否已有可沿用的專案資訊。
2. 盤點目錄結構、技術棧、入口點、核心依賴與主要模組邊界。
3. 對第二層模組做摘要掃描，整理公開介面、依賴關係與重要約束。
4. 更新 `.project/memory/project.md` 與 `.project/context/modules.md`，內容必須是實際分析結果，不得只留下空模板。
5. 更新對應 workspace memory，記錄目前分析進度、已知風險與建議後續工作。

## 產出要求

- `.project/memory/project.md`：專案類型、技術棧、架構模式、核心模組摘要
- `.project/context/modules.md`：第二層模組索引、公開介面、模組依賴
- `workspace` 記憶：本輪分析範圍、未解問題、建議下一步

## 重要原則

- 以現況為準，不預設未被證實的架構意圖。
- 優先揭露模組邊界、實際入口與耦合點，而不是只列檔案名稱。
- 若發現需求其實是「新功能設計」，應明確建議切回 `planner` 或 `design`。

## Next Step

- 需要新功能方案：交給 `planner`
- 已有批准方案：交給 `develop`
- 只想查看目前上下文：交給 `load-memory`
