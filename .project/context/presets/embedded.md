# 專案 Prompt Engineering 指引

> **用途**：定義專案特定的 AI 行為指引，讓 agent 輸出更貼合領域需求
> **所有區塊皆為可選**：未填寫的區塊，agent 使用內建預設值
> **填寫時機**：`adf.design` 初始化專案時選擇 preset，或任何時候手動編輯
> **大小建議**：每個 agent 範例建議 50-100 行以內，避免佔用過多 context window
>
> **Preset**：`embedded` — 嵌入式系統

---

## 🧠 角色補充

- 產品為資源受限的嵌入式裝置（MCU / SoC），RAM 和 Flash 是硬上限
- 設計時優先考慮最壞情況執行時間（WCET）而非平均效能
- 所有動態分配必須有上限，偏好 static allocation 與 memory pool
- 系統需 7×24 運行 30 天以上不重啟，記憶體洩漏零容忍
- 硬體依賴必須透過 HAL 層隔離，支援多平台移植
- 現場除錯機會有限，日誌與診斷機制必須內建且可遠端存取
- 中斷處理與即時性約束是架構設計的首要考量
- 韌體更新（OTA/USB）必須支援 fail-safe 回滾機制
- 所有外部輸入（感測器、通訊協定）必須做邊界檢查與防禦性處理

---

## 📏 評估框架

> `/planner`（architect）比較方案時使用的評估維度和評分標準。
> **覆寫規則**：此處定義的維度**取代**內建預設（不是疊加）。

### 評估維度

| 維度 | 評估重點 | 1 分（差） | 5 分（優） |
|------|----------|-----------|-----------|
| 資源效率 | RAM/Flash/CPU 使用量 | 超出硬體上限或無法估算用量 | 靜態可算、留有 20%+ 餘量、無動態分配 |
| 可靠性 | 長時間運行穩定性與錯誤恢復 | 無 watchdog、無錯誤處理、洩漏風險高 | 完整 watchdog/fail-safe、零洩漏設計、自動恢復 |
| 可維護性 | 程式碼結構與除錯便利性 | 硬體邏輯散落各處、無日誌、無法單元測試 | HAL 隔離完整、日誌分級可遠端查看、可 host 測試 |
| 可移植性 | 跨平台與硬體抽象程度 | 硬體操作直接寫死在業務邏輯中 | 完整 HAL/BSP 分層、僅需改 HAL 即可移植 |
| 安全性 | 輸入驗證/通訊安全/韌體完整性 | 無輸入檢查、明文通訊、無簽章驗證 | 所有輸入防禦性處理、加密通訊、安全開機鏈 |

### 權重規則

- **Prototype 階段**：資源效率 20%、可靠性 15%、可維護性 30%、可移植性 25%、安全性 10%
- **Production 階段**：資源效率 25%、可靠性 30%、可維護性 15%、可移植性 15%、安全性 15%
- **安全認證階段**：資源效率 15%、可靠性 25%、可維護性 10%、可移植性 10%、安全性 40%

---

## ⚠️ 風險標準

> `/planner`、`/breakdown`、`/develop` 判斷變更風險等級的標準。
> **覆寫規則**：此處定義的標準**取代**內建預設。

| 風險等級 | 判斷標準 | 額外要求 |
|----------|----------|----------|
| 🟢 LOW | 不涉及 HAL/Driver、不改變記憶體佈局、僅修改應用層邏輯 | 單元測試通過即可 |
| 🟡 MEDIUM | 修改 HAL 介面、改變 task 優先級或排程策略、調整 memory pool 大小 | 需 code review + 實機驗證計劃 |
| 🔴 HIGH | 修改中斷處理/DMA/時序邏輯、變更 bootloader 或 OTA 流程、改動通訊協定 | 需架構審查 + 實機長時間壓測 + 回滾方案 |

---

## 🔍 自我審查

> 各 agent 在輸出前的自我檢查問題（疊加到內建預設之上）。

### 架構設計（architect）

1. 所有 buffer/queue 是否都有明確的大小上限？是否以 static allocation 實作？
2. 最壞情況下的 CPU 使用率和記憶體佔用是否可計算？是否留有安全餘量？
3. 中斷延遲和 task 排程是否滿足即時性約束？有無優先級反轉風險？
4. 硬體依賴是否完全透過 HAL 隔離？能否在 host 環境執行單元測試？
5. 系統連續運行 30 天以上的場景下，有無資源洩漏或累積性錯誤風險？

### 開發實施（developer）

1. 是否避免了 malloc/free（或等效的動態分配）？若使用，是否有明確的上限和釋放保證？
2. 所有外部輸入（ADC、UART、SPI 資料）是否做了範圍檢查和超時處理？
3. 共享資源存取是否有適當的互斥保護？是否確認無死鎖路徑？

### 代碼審查（code-reviewer）

1. stack 使用量是否在安全範圍內？有無遞迴呼叫或可變長度陣列？
2. 是否有未保護的全域變數被多個 task/ISR 同時存取？
3. 錯誤路徑是否都有適當的資源清理和狀態恢復？

---

## 📝 範例

> 各 agent 的 few-shot example，展示期望的輸出深度和格式。
> **啟用規則**：有定義時自動啟用 few-shot 模式。

### architect 範例

> **需求**：重構現有的 camera 視訊串流 pipeline，目標平台為 ARM Cortex-A53 SoC（512MB RAM），需支援 1080p@30fps 擷取 + H.264 編碼 + RTSP 推流，同時保留本地預覽。

**硬約束**：
- RAM 上限 512MB（OS + App 可用 ≤ 380MB）
- pipeline 端對端延遲 ≤ 150ms
- CPU 佔用 ≤ 60%（保留餘量給其他服務）
- 7×24 連續運行不重啟

**軟約束**：
- 支援動態解析度切換（1080p/720p/480p）
- 未來擴充：增加第二路串流（sub-stream）
- 日誌可遠端查看

#### 方案 A：GStreamer Pipeline 架構

使用 GStreamer 框架搭配硬體 codec plugin，透過 `tee` 元素分流本地預覽與 RTSP 推流。

- buffer 管理：GStreamer 內建 buffer pool，設定上限 30 frames
- 記憶體：使用 DMA-BUF zero-copy，預估峰值 ≤ 180MB
- 擴充性：新增 sub-stream 只需加 `tee` 分支

#### 方案 B：自研 Ring Buffer Pipeline

自建 ring buffer + worker thread 架構，Camera → RingBuffer → Encoder → RingBuffer → RTSP Sender，預覽從第一級 ring buffer 分流。

- buffer 管理：固定大小 ring buffer（16 slots × 3MB = 48MB per stage）
- 記憶體：全靜態分配，峰值可精確計算 ≤ 160MB
- 擴充性：新增 sub-stream 需增加一組 ring buffer + encoder thread

#### 結構化評估

| 維度 | 方案 A（GStreamer） | 方案 B（自研 Pipeline） |
|------|:--:|:--:|
| 資源效率 | 3 — buffer pool 大小可控但有框架開銷 | 5 — 全靜態、可精算至 byte |
| 可靠性 | 3 — 依賴框架穩定性，錯誤恢復需自建 | 4 — 全自控但需自建 watchdog |
| 可維護性 | 4 — 社群文件豐富、pipeline 描述直觀 | 2 — 自建框架學習曲線高 |
| 可移植性 | 4 — GStreamer 跨平台，換 SoC 改 plugin | 3 — HAL 隔離度取決於實作品質 |
| 安全性 | 3 — 框架攻擊面較大 | 4 — 攻擊面小、可控性高 |

**Production 權重加權**：A = 3.35 / B = 3.55

#### 推薦

**推薦方案 A（GStreamer Pipeline）**，理由：

1. 可維護性優勢顯著 — 團隊 3 人中 2 人有 GStreamer 經驗
2. 資源效率可透過 DMA-BUF zero-copy 和 buffer pool 上限彌補
3. 方案 B 的分數優勢主要在資源效率，但方案 A 仍在硬約束範圍內
4. 長期維護成本：自研框架的 bug 修復全靠自己，GStreamer 有社群支援

**啟用條件**：若 GStreamer 在目標 SoC 的硬體 codec plugin 驗證失敗，則切換至方案 B。

#### 實施計劃

| 階段 | 任務 | 風險 | 產出 |
|------|------|------|------|
| P1 | 硬體 codec plugin 驗證 + DMA-BUF 測試 | 🔴 HIGH | 可行性報告 |
| P2 | Camera → Encoder pipeline 搭建 | 🟡 MEDIUM | 1080p 編碼 demo |
| P3 | RTSP 推流 + 本地預覽分流 | 🟡 MEDIUM | 完整 pipeline |
| P4 | 72 小時連續運行壓測 | 🟢 LOW | 穩定性報告 |
| P5 | 動態解析度切換實作 | 🟡 MEDIUM | 功能完成 |

---
*Preset: embedded — 嵌入式系統*
*適用於 MCU/SoC 嵌入式產品開發*
