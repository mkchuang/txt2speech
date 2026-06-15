---
name: adf.archive-memory
description: 歸檔過長或過時的工作記憶，保持 workspace 精簡
---

# Archive Memory

## Overview

將過長或過時的 workspace 記憶移到 archive，保留當前仍需要的工作上下文。若提供 `$ARGUMENTS`，將其視為指定歸檔範圍、時間窗口或保留內容要求。

## When to Use

- workspace memory 超過維護閾值，或長歷史已干擾目前工作恢復
- 階段、版本或設計收尾後，需要把 durable lessons 移到 archive
- 使用者明確要求整理或壓縮 Memory Bank

## When NOT to Use

- active design、進行中 task 或待驗證狀態尚未清楚
- 本輪只有單一 durable 決策，改用 `update-memory`
- 不確定哪些內容仍是當前工作上下文時，先做只讀檢查

## Core Process

1. 判斷團隊或單人模式，檢查 `.project/team.yaml`、workspace 文件行數與現有 `.project/archive/`。
2. 只有符合維護條件時才建議歸檔：workspace-team.md 超過 500 行、workspace-$user.md 超過 500 行、單人 workspace 時間跨度超過 30 天、階段切換或版本發布前。
3. 歸檔前確認範圍：時間窗口、要移出的歷史內容、保留最近的任務和狀態。
4. 建立 `.project/archive/workspace-YYYY-MM.md`，寫入歸檔時間、原始文件與時間範圍。
5. 移動已完成任務、歷史會話、舊審查記錄與不再活躍的背景內容。
6. active workspace 必須保留系統狀態總覽、當前架構方案、進行中的任務、active design、模組狀態與下一步。
7. 更新 workspace 的歷史歸檔索引，列出 archive path、時間範圍與摘要。
8. 若不滿足歸檔條件或使用者只要檢查，回報 no-op，不改檔。

## Verification

- 回報實際更新的 workspace memory 與 archive 檔案
- 確認 active design、進行中 task、待決策項仍留在 active memory
- 檢查 archive 中沒有把未完成工作寫成 completed fact
- 若只做檢查或判定 no-op，明確回報未修改檔案
- 回讀 archive 與 active workspace，確認歸檔索引可追溯
- 確認 `.project/archive/workspace-YYYY-MM.md` 存在且包含原始文件與時間範圍

## 適用情境

- 團隊模式下 `workspace-team.md` 或 `workspace-<用戶>.md` 超過 `500` 行
- 單人模式下 `workspace.md` 超過 `500` 行
- 單人模式下工作記憶時間跨度超過 `30 天`
- 版本發布、階段切換或大量歷史任務已完成

## 保留內容規則

- active memory 保留當前工作重點、進行中的任務、active design、已知 blocker、下一步與歷史歸檔索引。
- archive 保存完成里程碑、過期工作細節、歷史審查記錄、已解決問題與長背景。
- 不把仍需 follow-up、仍在驗證、尚未決策或可能影響下一步的內容移出 active memory。
- 歸檔是移動與整理，不是刪除；重要資訊必須仍能從歷史歸檔索引找回。

## Archive Format

- archive 文件標題使用 `# 工作記憶歸檔 - YYYY-MM`。
- front matter 或開頭摘要要包含歸檔時間、原始文件、時間範圍與保留策略。
- 歷史內容可以壓縮，但不能改寫已完成 / 未完成狀態。
- active workspace 的歷史歸檔索引至少包含 archive path、時間範圍與一句話摘要。
- archive 中保留原始事實與日期；摘要可以壓縮，但不應重新詮釋未完成狀態。
- 若同時歸檔 team 與 personal memory，分別建立可追蹤段落，避免混淆責任邊界。

## Safety Checks

- 歸檔前先讀 active design 與 current workspace，確認下一步仍可被 `load-memory` 找到。
- 歸檔後再次檢查 active memory 行數、進行中的任務與 active design 指向。
- 若發現 active memory 與 archive 內容互相矛盾，停止並要求人工確認。
- 不因超過閾值就強制歸檔；閾值只是建議檢查的 trigger。

## Maintenance / Safety Notes

- Memory Bank 是上下文恢復工具，不是操作日誌
- 歸檔前後都要以 repo-local file state 與使用者最新指示核對
- 不把尚未完成、誤標 completed 或仍需 audit 的項目移出 active memory
- 團隊模式下若要歸檔 personal workspace，先確認不會覆蓋或移走他人當前狀態

## 重要原則

- 歸檔前先確認保留內容，不要把進行中的狀態一起移走
- 歸檔是整理，不是刪除；重要資訊仍應可追溯
- 具體閾值是啟動歸檔建議的預設條件，不是每次都要強制執行

## Next Step

- 發現 durable 新決策但不需歸檔時，改用 `update-memory`
- 歸檔後若 active design 指向改變，重新執行 `load-memory` 核對狀態
