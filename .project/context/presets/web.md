# 專案 Prompt Engineering 指引

> **用途**：定義專案特定的 AI 行為指引，讓 agent 輸出更貼合領域需求
> **所有區塊皆為可選**：未填寫的區塊，agent 使用內建預設值
> **填寫時機**：`adf.design` 初始化專案時選擇 preset，或任何時候手動編輯
> **大小建議**：每個 agent 範例建議 50-100 行以內，避免佔用過多 context window
>
> **Preset**：`web` — Web 應用

---

## 🧠 角色補充

- 產品為前後端分離的 Web 應用，API 是系統的核心契約
- QPS 和水平擴展能力是架構設計的首要考量
- API 安全（認證、授權、輸入驗證、速率限制）不可妥協
- 前端效能預算：FCP ≤ 1.5 秒、TTI ≤ 3 秒、Bundle Size 嚴格管控
- 資料庫查詢必須有索引策略，N+1 查詢零容忍
- 快取策略需分層設計（CDN → 應用快取 → DB 快取）
- 所有 API 必須冪等設計，支援安全重試
- 可觀測性（Logging、Metrics、Tracing）是基礎設施而非附加功能
- SEO 需求視頁面類型決定（公開頁面 SSR/SSG，後台 SPA）

---

## 📏 評估框架

> `/planner`（architect）比較方案時使用的評估維度和評分標準。
> **覆寫規則**：此處定義的維度**取代**內建預設（不是疊加）。

### 評估維度

| 維度 | 評估重點 | 1 分（差） | 5 分（優） |
|------|----------|-----------|-----------|
| 效能 | 回應時間/吞吐量/資源使用 | P95 > 1 秒、無快取策略、DB 查詢未優化 | P95 < 200ms、多層快取、查詢全部有索引 |
| 可擴展性 | 水平擴展/無狀態設計/容量規劃 | 單體不可拆分、session 依賴本地狀態 | 無狀態服務、自動擴縮容、資料分片策略 |
| 可維護性 | 程式碼結構/測試覆蓋/部署便利性 | 無測試、手動部署、日誌不結構化 | 80%+ 測試覆蓋、CI/CD 全自動、結構化日誌 + tracing |
| 安全性 | 認證授權/輸入驗證/資料保護 | 無認證機制、SQL injection 風險、明文儲存 | OAuth2/JWT 完整、OWASP Top 10 防護、加密 at rest + in transit |
| 開發效率 | 開發速度/工具鏈成熟度/學習曲線 | 框架冷門、工具鏈不完整、新人上手慢 | 主流框架、完整工具鏈、良好文件和範例 |

### 權重規則

- **MVP 階段**：效能 15%、可擴展性 10%、可維護性 25%、安全性 15%、開發效率 35%
- **Growth 階段**：效能 25%、可擴展性 25%、可維護性 20%、安全性 20%、開發效率 10%
- **Scale 階段**：效能 30%、可擴展性 30%、可維護性 15%、安全性 20%、開發效率 5%

---

## ⚠️ 風險標準

> `/planner`、`/breakdown`、`/develop` 判斷變更風險等級的標準。
> **覆寫規則**：此處定義的標準**取代**內建預設。

| 風險等級 | 判斷標準 | 額外要求 |
|----------|----------|----------|
| 🟢 LOW | 新增 API endpoint、前端新頁面、不改動現有介面 | 單元測試 + API 測試通過 |
| 🟡 MEDIUM | 修改現有 API 回應格式、調整 DB schema、改動認證流程 | API 版本控制 + 整合測試 + 向後相容驗證 |
| 🔴 HIGH | 資料庫遷移（大表）、更換快取/佇列中介軟體、修改核心認證授權架構 | 架構審查 + 效能壓測 + 藍綠部署計劃 + 回滾方案 |

---

## 🔍 自我審查

> 各 agent 在輸出前的自我檢查問題（疊加到內建預設之上）。

### 架構設計（architect）

1. 服務是否無狀態？能否直接水平擴展至多實例？
2. 資料庫 schema 變更是否向後相容？是否有零停機遷移方案？
3. API 版本策略是否明確？舊版本的廢棄時程是否合理？
4. 快取失效策略是否完整？是否考慮了 cache stampede 和資料一致性？
5. 失敗場景下的降級策略是否定義？是否有 circuit breaker 機制？

### 開發實施（developer）

1. 所有 DB 查詢是否使用了適當的索引？是否避免了 N+1 查詢？
2. API 輸入是否做了完整的驗證和清理（sanitization）？
3. 敏感資料（密碼、token）是否避免出現在日誌和回應中？

### 代碼審查（code-reviewer）

1. 是否有未處理的 Promise/async 錯誤？是否有適當的錯誤邊界？
2. API 回應格式是否一致？錯誤碼是否標準化？
3. 是否有潛在的 SSRF、XSS、CSRF 或 injection 風險？

---

## 📝 範例

> 各 agent 的 few-shot example，展示期望的輸出深度和格式。
> **啟用規則**：有定義時自動啟用 few-shot 模式。

### architect 範例

> **需求**：為現有 REST API 後端新增即時通知系統，支援使用者層級的即時推送（訂單狀態更新、系統公告、協作通知），目標 10K 同時在線使用者。

**硬約束**：
- 同時支撐 10K WebSocket 連線，P99 推送延遲 ≤ 500ms
- 離線使用者上線後補收最近 7 天的未讀通知
- 與現有 JWT 認證體系整合，不引入新的認證機制
- 部署在現有 Kubernetes 叢集中

**軟約束**：
- 支援通知分類與已讀/未讀狀態
- 未來擴充：群組通知、@mention、通知偏好設定
- 前端支援瀏覽器通知（Notification API）

#### 方案 A：Redis Pub/Sub + WebSocket Gateway

獨立部署 WebSocket Gateway 服務，透過 Redis Pub/Sub 接收業務服務發送的通知事件，推送至對應用戶端。離線通知存入 PostgreSQL。

- 連線管理：Gateway 無狀態，連線資訊存 Redis，支援多實例
- 訊息投遞：Redis Pub/Sub channel per user，Gateway 訂閱活躍用戶
- 離線補償：上線時從 PostgreSQL 查詢未讀通知

#### 方案 B：Kafka + SSE 串流

使用 Kafka 作為通知事件匯流排，前端透過 Server-Sent Events（SSE）接收推送。每個用戶一個 Kafka consumer group，用 offset 管理已讀位置。

- 連線管理：SSE 連線由 API Gateway 持有，單向推送
- 訊息投遞：Kafka partition by user_id，保序投遞
- 離線補償：Kafka 保留 7 天，上線後從 last committed offset 消費

#### 結構化評估

| 維度 | 方案 A（Redis + WebSocket） | 方案 B（Kafka + SSE） |
|------|:--:|:--:|
| 效能 | 4 — Redis Pub/Sub 低延遲、推送即時 | 3 — Kafka 有 batch 延遲、SSE 無雙向通道 |
| 可擴展性 | 4 — Gateway 無狀態可水平擴展 | 5 — Kafka 天然分散式、partition 可擴展 |
| 可維護性 | 4 — 架構直觀、元件少 | 3 — Kafka 運維複雜度高 |
| 安全性 | 4 — WebSocket 升級時驗證 JWT | 4 — SSE 走 HTTPS、標準認證 |
| 開發效率 | 4 — 團隊有 Redis 和 WebSocket 經驗 | 2 — 需學習 Kafka 運維和 consumer group 管理 |

**Growth 階段權重加權**：A = 4.00 / B = 3.45

#### 推薦

**推薦方案 A（Redis Pub/Sub + WebSocket Gateway）**，理由：

1. 10K 連線規模下 Redis Pub/Sub 綽綽有餘，Kafka 的分散式優勢在此規模不明顯
2. WebSocket 支援雙向通訊，未來需要已讀回執或打字提示時可直接擴展
3. 團隊已有 Redis 運維經驗，不需要引入新的基礎設施
4. 架構簡單明確：Gateway 只負責連線管理和訊息轉發，業務邏輯留在原有服務

**擴展預案**：當連線數超過 50K 時，Redis Pub/Sub 換為 Redis Streams 以獲得持久化和 consumer group 支援。

#### 實施計劃

| 階段 | 任務 | 風險 | 產出 |
|------|------|------|------|
| P1 | WebSocket Gateway 基礎架構 + JWT 認證整合 | 🟡 MEDIUM | 連線建立 + 心跳 demo |
| P2 | Redis Pub/Sub 整合 + 推送投遞 | 🟢 LOW | 即時推送功能 |
| P3 | 離線通知儲存 + 上線補收機制 | 🟡 MEDIUM | 離線場景完整 |
| P4 | 前端 SDK + 瀏覽器通知整合 | 🟢 LOW | 前端功能完成 |
| P5 | 10K 連線壓測 + 監控告警 | 🟡 MEDIUM | 效能報告 + Grafana dashboard |

---
*Preset: web — Web 應用*
*適用於前後端分離的 Web 應用開發*
