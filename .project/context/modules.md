# 模組規格索引

> 此檔案由 `/analyze` 初始建立，由 `/planner` 和 `/update-memory` 漸進更新
> 最後更新：2026-06-15
> **容量指引**：每模組摘要限 10 行，詳細規格限 30 行。超過 100 個模組時建議按領域分段索引。

## 模組總覽

> 狀態：plan-2026-06-15 已 approved；TASK-001 已落地後端 skeleton/config/health，TASK-002 已落地 `/api/voices`，TASK-003 已落地 prompt 組裝器，其他模組仍依 task backlog 推進。

| 模組 | 目錄 | 行為摘要 | 分析深度 | 最後更新 |
|------|------|---------|---------|---------|
| config | backend/app/config.py | 載入 GEMINI_API_KEY / DATA_DIR / CORS 設定；缺 key 啟動 gate 已驗證 | ✅ 已驗證 | 2026-06-15 |
| api | backend/app/api/ | FastAPI app + /api/health、/api/voices 已實作且驗證；synthesize / history / audio 路由待續 | 🟡 部分實作 | 2026-06-15 |
| ingest | backend/app/ingest/ | markdown→純文字正規化 | 📋 規劃 | 2026-06-15 |
| tts | backend/app/tts/ | prompt 組裝器已實作：fixed preamble + Director's Notes + TRANSCRIPT，voice/style/pacing/accent sanitizer；Gemini adapter、count_tokens 切塊待續 | 🟡 部分實作 | 2026-06-15 |
| audio | backend/app/audio/ | 多塊 raw PCM 串接 → WAV（stdlib wave） | 📋 規劃 | 2026-06-15 |
| storage | backend/app/storage/ | SQLite metadata + 檔案系統音檔、歷史 CRUD | 📋 規劃 | 2026-06-15 |
| frontend | frontend/ | Next.js UI：輸入/參數/播放器/歷史清單 | 📋 規劃 | 2026-06-15 |

> 分析深度：📋 摘要/規劃 | 🟡 部分實作 | ✅ 已驗證 | 📖 詳細（實作後由 /analyze 或 /update-memory 補）

---

## 資料流拓撲

> 描述系統主要資料流路徑，由 /analyze 第二層掃描產出。
> 嵌入式影音系統應重點描述：影像幀/音訊幀的產出 → 處理 → 分發 → 輸出路徑。

### 影像資料流
```
[來源] → [處理] → [佇列] → [輸出端點]
例：ISP → Encoder(H.264) → stm_queue → RTSP/NDI/SRT/HLS
```

### 音訊資料流
```
[來源] → [處理] → [佇列] → [輸出端點]
```

### 佇列拓撲
| 佇列名稱 | 生產者 | 消費者 | 深度 | 丟幀策略 |
|----------|--------|--------|------|---------|
| [名稱] | [模組] | [模組] | [N 幀] | [丟舊/丟新/阻塞] |

---

## 線程架構

> 描述系統的線程模型，由 /analyze 第二層掃描產出。
> 重點：獨立 thread 的職責、排程策略、同步機制、CPU 親和性。

| 線程名稱 | 入口函數 | 職責 | 排程策略 | CPU 親和性 | 同步機制 |
|----------|---------|------|---------|-----------|---------|
| [名稱] | [函數] | [一句話] | [SCHED_RR/FIFO/OTHER] | [CPU N] | [barrier/mutex/cond/queue] |

### 線程啟動順序
```
[啟動順序圖或 barrier 同步描述]
```

### 關鍵同步點
- [描述 thread 間的關鍵同步邏輯，如 barrier 統一啟動、mutex 保護的共享資源]

---

## 模組詳細規格

### [模組名] — [一句話描述]

**行為摘要**：[模組做什麼，2-3 句話]

**關鍵介面**：
- `function_name()` — [說明]

**依賴**：
- 上游：[提供資料給本模組的模組]
- 下游：[本模組提供資料的模組]
- 共享資源：[共享的 buffer、queue、IPC]

**約束**：
- [記憶體/即時性/併發/硬體依賴]

**最後分析**：2026-06-15 by [/analyze | /planner]

---
*此檔案為漸進式累積，不需要一次填完所有模組*
*被 /planner 觸及的模組會自動補充詳細規格*
