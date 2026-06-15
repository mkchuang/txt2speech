---
name: archive-design
description: 歸檔已完成的設計文件，並確認知識已同步回流
---

# Archive Design

## Overview

將已完成的設計文件整理到 archive，避免 `design/` 目錄被歷史方案淹沒。若提供 `$ARGUMENTS`，將其視為指定 plan、月份或檢查模式。

## When to Use

- 設計文件已明確標示 `implemented`、`abandoned` 或其他可歸檔終態
- Memory Bank、README、ADR 或其他 source of truth 已吸收必要結論
- 使用者要求整理 design 目錄或執行 archive check

## When NOT to Use

- plan 仍是 active、in progress、待驗證或使用者指出尚未完成
- 只是要更新設計狀態，應先修改 plan / memory，不直接歸檔
- 尚未確認 durable knowledge 已回流到正確文件

## Core Process

1. 掃描 `.project/design/plan-*.md`，找出設計狀態為 `implemented`、`abandoned` 或其他明確終態的文件。
2. 若 `$ARGUMENTS` 包含 `--check`，只做檢查並回報可歸檔清單與缺漏，不執行移動。
3. 對每個候選文件檢查前置條件：設計狀態為 `implemented`、所有任務已完成、知識已回流。
4. 做文檔同步檢查，輸出 project.md 更新建議、README.md 更新建議、ADR 或 context 更新建議。
5. 若知識尚未回流，先停止並要求更新 source of truth；不要用 archive 掩蓋缺漏。
6. 按月歸檔：建立歸檔目錄：`mkdir -p .project/design/archive/YYYY-MM/`。
7. 移動設計文件：`mv plan-*.md archive/YYYY-MM/`，必要時更新設計狀態或 archive index。
8. 若被歸檔文件是 `current.md` 指向的 active design，先更新或清理 `current.md`，並明確回報 symlink 指向。
9. 更新 workspace memory，記錄歸檔結果、知識回流狀態與後續建議。

## Verification

- 回報每個歸檔文件的原路徑、目標路徑與終態
- 明確說明 `current.md` 是否受影響；若是 symlink，回報新的指向
- 檢查 active / in-progress design 沒有被移入 archive
- `--check` 模式必須明確回報未修改任何檔案
- 確認知識已回流到 Memory Bank、README、ADR 或 `.project/context/` 中的正確位置
- 若只是檢查模式，回報不歸檔也能正常運作

## 輸出重點

- 歸檔了哪些設計文件
- 有哪些文檔已同步更新
- 歸檔目錄位置
- 哪些文件不可歸檔，以及缺少哪些回流項

## Current Design Handling

- 若 `current.md` 指向待歸檔文件，歸檔前必須決定新的 active design、移除 symlink 或標示目前沒有 active design。
- 若 `current.md` 是 symlink，移動檔案前後都要回報實際指向。
- 若使用者明確說某 design 尚未完成，即使 metadata 看似 implemented，也不得歸檔。
- 若 design 已 abandoned，仍需確認 memory 不再把它列為 pending option。

## Archive Index Rules

- 歸檔位置固定使用 `.project/design/archive/YYYY-MM/`。
- workspace memory 應保留 archive index，讓下次 load-memory 能找到歷史 plan。
- 對 implemented plan，只保留必要摘要與後續風險；不要把整份 plan 複製進 memory。

## Maintenance / Safety Notes

- 歸檔前以 design 文件狀態與使用者最新指示為準，不只依賴舊 memory
- 遇到狀態矛盾時停止，先修正 plan / memory，不做移動
- 不把「待決」或「需重新驗證」的文件當成 completed archive
- active design、in-progress plan、待驗證 task 或剛被使用者指出尚未完成的設計不可歸檔

## 重要原則

- 歸檔是整理，不是必要流程
- implemented 狀態下知識就應該已經回流，archive 只是整理歷史
- `--check` 模式只檢查不同步與可歸檔項，不改動任何檔案
- 文檔同步檢查是歸檔前置條件，不應省略
- 不歸檔也能正常運作；archive 不能成為功能正確性的前提

## Next Step

- 發現 active design 被誤歸檔時，先還原並修正 memory
- 歸檔完成且有 durable 狀態變更時，接 `update-memory`
