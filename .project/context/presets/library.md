# 專案 Prompt Engineering 指引

> **用途**：定義專案特定的 AI 行為指引，讓 agent 輸出更貼合領域需求
> **所有區塊皆為可選**：未填寫的區塊，agent 使用內建預設值
> **填寫時機**：`adf.design` 初始化專案時選擇 preset，或任何時候手動編輯
> **大小建議**：每個 agent 範例建議 50-100 行以內，避免佔用過多 context window
>
> **Preset**：`library` — 函式庫/SDK

---

## 🧠 角色補充

- 產品為提供給其他開發者使用的函式庫或 SDK，API 設計品質是生死線
- 向後相容是鐵律 — 任何 breaking change 都需要 major 版本號升級和遷移指南
- API 命名必須一致、可預測、自解釋，遵循最少驚訝原則（Principle of Least Astonishment）
- zero-dependency 是強烈偏好，每新增一個依賴都需要充分理由
- 型別安全不可妥協 — TypeScript 需完整型別定義、C/C++ 需 header 契約明確
- 文檔覆蓋率目標 100%：每個公開 API 必須有描述、參數說明、範例、異常情況
- 效能不能因為抽象而過度退化，hot path 需有 benchmark 數據佐證
- 錯誤處理模式必須統一（Result type / 例外 / 錯誤碼擇一），跨 API 一致
- 版本發布遵循語義化版本（SemVer），CHANGELOG 自動生成

---

## 📏 評估框架

> `/planner`（architect）比較方案時使用的評估維度和評分標準。
> **覆寫規則**：此處定義的維度**取代**內建預設（不是疊加）。

### 評估維度

| 維度 | 評估重點 | 1 分（差） | 5 分（優） |
|------|----------|-----------|-----------|
| API 設計 | 命名一致性/直覺性/可發現性 | 命名混亂、方法功能重疊、入參不直覺 | 命名可預測、職責單一、型別引導使用者正確使用 |
| 向後相容性 | Breaking change 控管/遷移路徑 | 頻繁 breaking change、無遷移指引 | 嚴格 SemVer、deprecation 週期明確、自動遷移工具 |
| 效能 | Hot path 延遲/記憶體開銷/bundle size | 抽象開銷大、無 benchmark、bundle 膨脹 | Hot path 有 benchmark 佐證、zero-copy 設計、tree-shakable |
| 文檔品質 | API 文檔/範例/遷移指南 | 無文檔或僅有 auto-gen、無範例 | 100% API 文檔 + 使用範例 + 遷移指南 + FAQ |
| 可維護性 | 內部結構/測試覆蓋/CI 品質 | 模組耦合高、測試不足、發版手動 | 模組職責清晰、90%+ 覆蓋率、全自動發版 |

### 權重規則

- **初版開發**：API 設計 35%、向後相容性 10%、效能 20%、文檔品質 20%、可維護性 15%
- **穩定維護**：API 設計 20%、向後相容性 30%、效能 20%、文檔品質 15%、可維護性 15%
- **大版本升級**：API 設計 30%、向後相容性 25%、效能 15%、文檔品質 20%、可維護性 10%

---

## ⚠️ 風險標準

> `/planner`、`/breakdown`、`/develop` 判斷變更風險等級的標準。
> **覆寫規則**：此處定義的標準**取代**內建預設。

| 風險等級 | 判斷標準 | 額外要求 |
|----------|----------|----------|
| 🟢 LOW | 新增 API（不影響現有）、改善文檔、新增內部工具方法 | 單元測試 + 文檔更新 |
| 🟡 MEDIUM | 標記 API 為 deprecated、修改內部實作（不改介面）、調整預設值 | 相容性測試 + CHANGELOG 更新 + deprecation 告警 |
| 🔴 HIGH | 移除/重新命名公開 API、修改回傳型別、改變錯誤處理模式 | 架構審查 + major 版本升級 + 遷移指南 + deprecation 過渡期 |

---

## 🔍 自我審查

> 各 agent 在輸出前的自我檢查問題（疊加到內建預設之上）。

### 架構設計（architect）

1. 新增/修改的 API 命名是否與現有 API 風格一致？是否遵循最少驚訝原則？
2. 此變更是否構成 breaking change？若是，遷移路徑和 deprecation 週期是否規劃？
3. 是否引入了新的外部依賴？是否有 zero-dependency 替代方案？
4. 公開介面的型別定義是否完整？使用者能否僅靠型別提示正確使用 API？
5. 效能敏感的路徑是否有 benchmark 數據支撐設計選擇？

### 開發實施（developer）

1. 所有公開 API 是否都有 JSDoc/docstring 並包含使用範例？
2. 錯誤處理是否遵循庫的統一模式？錯誤訊息是否對使用者有幫助？
3. 是否有可能洩漏內部實作細節到公開介面（例如暴露內部型別）？

### 代碼審查（code-reviewer）

1. 新增的 API 是否可以被 tree-shaking？是否會增加不使用此功能的使用者的 bundle size？
2. 型別定義是否過度寬鬆（如 `any`）或過度嚴格（影響使用彈性）？
3. 測試是否覆蓋了 API 的邊界情況、型別邊界、和錯誤路徑？

---

## 📝 範例

> 各 agent 的 few-shot example，展示期望的輸出深度和格式。
> **啟用規則**：有定義時自動啟用 few-shot 模式。

### architect 範例

> **需求**：將視訊會議 SDK 從 v2 升級至 v3，主要目標是統一事件系統（v2 混用 callback 和 EventEmitter）、新增 TypeScript 完整型別支援、並將 `join/leave` 改為 async/await 模式。

**硬約束**：
- v2 使用者必須有清晰的遷移路徑，提供 codemod 或逐步遷移指南
- v3 公開 API 100% TypeScript 型別覆蓋
- 不新增外部依賴（目前 zero-dependency）
- bundle size 增量 ≤ 5KB（gzip）

**軟約束**：
- v2 API 標記 deprecated 後保留至少 6 個月
- 支援 v2/v3 API 在同一專案中並存（過渡期）
- 內部模組可選擇性使用新事件系統重構

#### 方案 A：統一 EventTarget 模式

所有事件統一使用瀏覽器原生 `EventTarget` 介面（`addEventListener`/`removeEventListener`），`join/leave` 改為返回 `Promise`，v2 的 callback 風格透過 adapter 層相容。

- 事件系統：`EventTarget` 原生 API、自訂事件型別 `MeetingEvent<T>`
- async 化：`client.join()` → `Promise<JoinResult>`，內部用 state machine 管理
- 相容層：`v2Compat(client)` wrapper 將 v3 client 包裝為 v2 介面

#### 方案 B：自研 TypedEmitter

自研強型別事件發射器 `TypedEmitter<EventMap>`，透過泛型約束事件名稱和 payload 型別。`join/leave` 同樣改為 async，v2 callback 透過 overload 簽名相容。

- 事件系統：`TypedEmitter<{ joined: [participant: Participant]; left: [id: string] }>`
- async 化：`client.join()` → `Promise<JoinResult>`，同方案 A
- 相容層：v2 callback 參數透過函式 overload 保留，標記 `@deprecated`

#### 結構化評估

| 維度 | 方案 A（EventTarget） | 方案 B（TypedEmitter） |
|------|:--:|:--:|
| API 設計 | 3 — 原生 API 熟悉但 `addEventListener` 字串事件名易出錯 | 5 — 泛型約束提供編譯期事件名和型別檢查 |
| 向後相容性 | 4 — adapter 層隔離完整 | 4 — overload 自然過渡 |
| 效能 | 4 — 原生實作、零開銷 | 4 — 輕量自研、可控 |
| 文檔品質 | 3 — EventTarget 文件雖多但自訂事件文件需自寫 | 4 — 型別即文件、IDE 自動補全體驗優 |
| 可維護性 | 3 — 無法從型別推導支援的事件清單 | 5 — EventMap 集中定義、新增事件改一處 |

**大版本升級權重加權**：A = 3.40 / B = 4.50

#### 推薦

**推薦方案 B（自研 TypedEmitter）**，理由：

1. SDK 使用者最大的痛點是「不知道有哪些事件、payload 長什麼樣」 — TypedEmitter 讓 IDE 自動補全直接解決
2. EventMap 集中定義所有事件，新增事件只改一處，型別自動傳播到所有消費端
3. 自研 TypedEmitter ≤ 50 行程式碼、0 依賴、bundle 增量可忽略
4. v2 callback 透過 overload 自然共存，使用者可逐步遷移，不需要額外 adapter

**遷移策略**：
- Phase 1：發布 v2.x 最終版，所有 callback API 標記 `@deprecated`
- Phase 2：發布 v3.0，v2 overload 保留但 deprecated
- Phase 3：v3.1+ 移除 v2 overload（發布後 6 個月）

#### 實施計劃

| 階段 | 任務 | 風險 | 產出 |
|------|------|------|------|
| P1 | TypedEmitter 核心 + EventMap 型別定義 | 🟢 LOW | 事件系統核心模組 |
| P2 | `join/leave` async 化 + state machine | 🟡 MEDIUM | async API + 狀態管理 |
| P3 | v2 callback overload 相容層 | 🟡 MEDIUM | v2/v3 並存驗證 |
| P4 | 100% API 文檔 + 遷移指南 + codemod 腳本 | 🟡 MEDIUM | 文檔 + 遷移工具 |
| P5 | bundle size 驗證 + benchmark + beta 發布 | 🟢 LOW | v3.0-beta |

---
*Preset: library — 函式庫/SDK*
*適用於函式庫、SDK、框架等供其他開發者使用的專案*
