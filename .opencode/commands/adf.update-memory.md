---
name: adf.update-memory
description: 將本輪決策、進度與風險回寫到 Memory Bank
---

# Update Memory

## Overview

把本輪工作中值得留下的決策、進度與風險寫回 Memory Bank。若提供 `$ARGUMENTS`，將其視為指定更新範圍、相關 task 或想強調的決策主題。

## When to Use

- 本輪有 durable 決策、里程碑、風險、驗證結果或後續上下文需要保留
- 設計或實作完成後，需要同步 team / personal workspace memory
- 使用者明確要求更新記憶

## When NOT to Use

- 本輪只是查詢、短暫探索或無新 durable signal
- 想保存完整操作日誌，應依賴 git diff、commit 或測試輸出，不塞進 Memory Bank
- 設計尚未批准且內容可能大幅變動，除非只記 open question 或決策背景

## Core Process

1. 辨識當前用戶並建立 `.project/memory/workspace-$current_user.md` 路徑；團隊模式由 `.project/team.yaml` 判定，否則使用單人模式。
2. 載入 `project.md`、team / personal / single-user workspace memory、active design 與相關 context。
3. 回顧近期變更，必要時使用 `git diff --stat HEAD~5`、`git status` 與 active plan 狀態找出 durable signal。
4. 對本輪內容套用一句話原則：做了什麼 + 為什麼 + 影響什麼。
5. 只記決策不記過程：保留 durable 決策、Task 進度、風險、blocker、review result、驗證結果與下一步。
6. 若設計文件包含 `Delta` 區塊，且 `.project/context/modules.md` 存在，執行 Delta 回寫 modules.md。
7. 視變更類型分流：
   - 專案全貌、架構狀態或長期風險：更新 `project.md`。
   - 團隊 milestone、cross-user blocker 或 shared next step：更新 `workspace-team`。
   - 個人任務、操作注意事項或本輪負責事項：更新 `workspace-$current_user`。
   - 單人模式：更新 `workspace.md`。
8. 若沒有新增 durable signal，做 no-op 並明確回報原因，保持無冗餘。

## Verification

- 列出實際更新的 Memory Bank 檔案
- 摘要新增的 durable signal，而不是複製整段 diff
- 若判定 no-op，明確說明沒有新增可保留記憶
- 檢查更新後的 memory 是否能讓下一次 `load-memory` 直接恢復目前狀態
- 確認沒有把可由 git log / commit message 查到的操作細節重複塞進 Memory Bank
- 若做了 Delta 回寫，回報更新的 modules.md 條目與依據

## 記錄原則

- 記決策與理由，不只記做了什麼
- 記例外與風險，不記流水帳
- 記可幫助下次快速恢復上下文的資訊
- 記數字不記感覺，例如記「RAM 使用降低 15%」，不要只寫「效能有所改善」
- 每條記錄優先回答「做了什麼 + 為什麼 + 影響什麼」
- 記決策不記過程；分析步驟、臨時命令與順利完成的細節不進 active memory
- Task 進度要寫清楚完成、partial、blocked 或下一步，不用模糊狀態
- 無冗餘：能從 git diff、commit 或測試輸出還原的低價值細節不重複寫入

## 更新範圍判斷

- 更新 `project.md`：主線版本、架構能力、ADR、長期風險、跨 task 後續項改變。
- 更新 `workspace-team.md`：團隊可見 milestone、active design 狀態、下一個 team task、baseline test risk 改變。
- 更新 `workspace-$current_user.md`：個人正在處理的 task、個人注意事項、環境限制、下一步操作。
- 更新 `workspace.md`：單人模式下合併上述 team / personal 狀態。
- 若只修 typo、格式、snapshot 或 commit message，且 Memory Bank 已可恢復上下文，通常 no-op。
- 若 review finding 被確認或修正，只有 blocker/residual risk/下一步改變時才寫入。

## No-op 條件

- 沒有 durable 決策、進度、風險、blocker、驗證結果或後續上下文變更。
- 變更只存在於 git diff 且不影響下一輪工作恢復。
- 記憶中已有同等訊息，新增內容只會重複。
- 本輪資訊尚未驗證，或使用者明確表示仍在討論中。

## 寫入格式

- 優先更新既有短句或表格列，避免新增長篇 session log。
- 每次更新後保留 active memory 精簡；長歷史應移到 archive，而不是累積在 active workspace。
- 對測試結果只記最小可追溯摘要，例如 targeted pass、known baseline failure、未跑的原因。

## Delta 回寫規則

- 只在設計文件存在明確 `Delta` 區塊，且 `.project/context/modules.md` 已存在時執行
- `ADDED` 模組要補入模組摘要與關鍵介面
- `MODIFIED` 模組要更新既有描述
- `REMOVED` 模組要刪除或標記已移除
- 若沒有 `Delta` 區塊或 `modules.md` 不存在，直接跳過，不要硬建新檔

## 重要原則

- Memory Bank 是上下文恢復工具，不是操作日誌
- 若本輪沒有新增決策或狀態變化，不要硬塞低價值內容
- modules delta 回寫前要先讀最新版本，避免覆蓋團隊模式下他人的更新
- team / personal memory 的責任邊界要清楚，不把個人操作細節升級成團隊事實
- 不把未完成 smoke、E2E 或 review 說成 done；code/test done 與真 smoke done 要分開記錄

## Maintenance / Safety Notes

- 團隊模式下優先避免覆蓋他人的 workspace 更新
- 不把未驗證猜測寫成已完成事實
- 數字、路徑、測試結果要可追溯

## Next Step

- 完成開發後可接 `code-review`
- 完成設計後可接 `validate-plan` 或 `breakdown`
- 記憶過長時可接 `archive-memory`
