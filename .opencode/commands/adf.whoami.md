---
name: adf.whoami
description: 顯示當前用戶身份、工作模式與個人工作摘要
---

# Whoami

顯示目前是誰在工作、處於團隊或單人模式，以及個人記憶中最重要的工作摘要。若提供 `$ARGUMENTS`，將其視為想額外檢查的身份或記憶主題。

## 執行步驟

1. 讀取 `git config user.name` / `git config user.email`；若沒有，再回退到系統用戶。
2. 將名稱標準化成 user id，並判斷 `.project/team.yaml` 是否存在。
3. 檢查對應的 workspace memory 是否存在，以及最近活動與當前任務摘要。
4. 用精簡格式回報身份、模式、個人記憶位置與工作狀態。

## 輸出重點

- 顯示名稱、email、user id
- 顯示團隊模式或單人模式
- 顯示個人記憶位置與是否存在
- 顯示當前任務與最近活動摘要

## 重要原則

- `whoami` 是狀態摘要，不重做 `load-memory`
- 若個人記憶不存在，明確提示可先執行 `load-memory`
