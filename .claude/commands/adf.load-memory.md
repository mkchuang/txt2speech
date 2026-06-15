---
name: load-memory
description: 載入 Memory Bank，顯示專案、團隊與個人工作狀態
---

# Load Memory

## Overview

讀取並呈現 Memory Bank 的當前狀態。若提供 `$ARGUMENTS`，將其視為指定想特別關注的檔案、用戶或狀態範圍。

## When to Use

- 使用者要求載入記憶、查看目前專案狀態、確認 active design 或團隊模式
- 新工作開始前需要恢復 workspace context
- 中斷後需要重新確認 file-backed state

## When NOT to Use

- 使用者要修改記憶內容，改用 `update-memory`
- 使用者要歸檔過長記憶，改用 `archive-memory`
- 使用者要實作或設計新功能，先讀取後再轉交 `planner` 或 `develop`

## Core Process

1. 辨識當前用戶，優先使用 `git config user.name`；若沒有設定，改用 `$USER` 或 `whoami`。
2. 將顯示名稱正規化為 `current_user`，使用小寫並以短橫線取代空格，建立 `.project/memory/workspace-{current_user}.md` 路徑。
3. 檢查 `.project/team.yaml` 判斷模式：
   - 存在：團隊協作模式。
   - 不存在：單人開發模式（向後相容）。
4. 檢查 `.project/`、`.project/memory/`、`.project/design/` 與 memory 文件行數，包含 `wc -l .project/memory/*.md`。
5. 團隊模式讀取 `.project/memory/project.md`、`.project/memory/workspace-team.md` 與 `.project/memory/workspace-{current_user}.md`。
6. 團隊模式下個人記憶不存在時，自動建立 `.project/memory/workspace-{current_user}.md`，並在輸出中明確回報首次建立。
7. 單人模式讀取 `.project/memory/project.md`、`.project/memory/workspace.md` 與 `.project/design/current.md`。
8. 彙整 `.project/design/current.md`、活躍 plan、目前任務、文件行數與最後更新時間。
9. 給出維護建議，例如需要初始化、歸檔、更新 active design 或補 planner。

## Verification

- 回報實際讀取的 memory / design 檔案
- 明確標示團隊模式或單人模式
- 若有建立個人記憶，回報建立路徑；若未修改，明確說明只讀
- 明確回報 current user 辨識來源，以及 `current_user` 對應的 workspace 檔案
- 若 `.project/design/current.md` 是 symlink，回報實際指向

## 維護建議判斷

- `workspace-team.md` 超過 `500` 行時，建議整理或歸檔
- 個人記憶檔案超過 `500` 行時，建議整理或歸檔
- `workspace-team.md > 500 行` 或 `.project/memory/workspace-$current_user.md > 500 行` 時，建議執行 `archive-memory`
- `project.md` 為空時，建議執行 `design` 或 `analyze`
- 缺少活躍架構文件時，建議執行 `planner`
- active design 指向不存在、狀態矛盾或 memory 與 filesystem 不一致時，回報需先修正 source of truth

## 輸出重點

- Memory Bank 文件狀態表
- 專案摘要、團隊進度與個人任務
- 活躍設計文件
- 維護建議與下一步操作
- 團隊協作模式下顯示 project / workspace-team / workspace-$current_user 三層摘要
- 單人開發模式（向後相容）下顯示 project / workspace 兩層摘要

## 狀態摘要規則

- 文件狀態表至少包含路徑、存在與否、行數、最後更新時間與是否為本輪讀取。
- 團隊狀態只摘要目前主線、最新完成、已知 blocker 與下一個可執行 task。
- 個人任務只摘要當前任務、正在進行的 design/task、注意事項與可交接資訊。
- 活躍設計要以 `.project/design/current.md` 實際指向為準；若沒有 current symlink，改列最近 active-looking plan 並標示推論。
- 維護建議要具體到下一個 command，例如 `archive-memory`、`planner`、`develop` 或 `update-memory`。
- 回覆中要區分「讀到的事實」與「根據檔案推論的下一步」。

## Conflict Handling

- 若 team memory、personal memory 與 active design 的下一步不一致，回報不一致來源，不直接改檔。
- 若個人 workspace 缺失且 auto-create 開啟，建立最小檔案；若 auto-create 不明，先回報缺失。
- 若 `.project/` 結構缺失，列出缺失檔案與最小初始化建議，不假設專案已定義。
- 若 memory 提到的 task 已被測試或 git history 推翻，標為 stale，不把它當成目前狀態。
- 若使用者提供 `$ARGUMENTS`，只加強該範圍的摘要，不跳過基本 team / current design 判讀。
- 若需要後續行動，輸出單一最合理 next step，而不是列出無優先序的長清單。

## 重要原則

- `load-memory` 只讀取並摘要，不直接改寫既有內容
- 唯一例外是首次載入時可自動建立缺失的個人記憶檔案
- 首次建立要明確回報建立位置，避免使用者誤以為已有既存內容
- 以 repo-local Memory Bank 與 Design 文件為 source of truth，不要求使用者重述 active plan
- 不把舊記憶中的 task 狀態當作事實；若與 filesystem 衝突，標示衝突並以 filesystem 為準

## Maintenance / Safety Notes

- 以 filesystem 實際狀態為準，不只依賴舊 memory 註記
- `current.md` 若是 symlink，必須回報實際指向
- 不把操作流水帳寫入 Memory Bank

## Next Step

- 需要設計時接 `planner`
- 需要實作時接 `develop`
- 需要整理過長記憶時接 `archive-memory`
