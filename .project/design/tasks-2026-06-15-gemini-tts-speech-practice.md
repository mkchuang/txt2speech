# Task Backlog - txt2speech Gemini TTS 練講工具

> **來源 plan**: `plan-2026-06-15-gemini-tts-speech-practice.md`（狀態 approved）
> **產生**: 2026-06-15 by adf.breakdown
> **消費者**: adf.develop
> **里程碑對應**: M1–M8（見 plan 實施計劃）

## 關鍵路徑與並行

- **關鍵路徑**：TASK-001 → 003/004/005 → 006 → 007 → 008 → 011 → 013 → 016 → 017 → 018
- **可早並行**：TASK-002（voices）、009（db）、010（files）、015（前端 scaffolding）可在骨架後即並行
- **高風險**：TASK-004（Gemini 整合）、007/008（切塊與 PCM 串接）— 須先過單元測試再往下
- **依賴圖無循環**

## 依賴總覽

```
001 ─┬─ 002
     ├─ 003 ─┐
     ├─ 004 ─┼─ 006 ─ 007 ─ 008 ─ 011 ─ 013 ─┐
     ├─ 005 ─┘                    │           │
     ├─ 009 ─┬─ 011               └─ 014 ──┐  │
     └─ 010 ─┘                              │  │
        └──── 012(需 009,010)               │  │
015 ─ 016(需 002,013,014) ─ 017(需 012) ──── 018(需全部)
```

---

## M1 — 後端骨架

### TASK-001 — 後端專案骨架 + config
- **Phase**: M1 ｜ **優先級**: P0 ｜ **依賴**: 無
- **檔案**: `backend/pyproject.toml`、`backend/app/main.py`、`backend/app/config.py`、`.env.example`
- **內容**: 建 FastAPI app、CORS、`/api/health`；`pydantic-settings` 載入 `GEMINI_API_KEY`、`DATA_DIR`、`CORS_ORIGINS`；依賴：fastapi/uvicorn/google-genai/pydantic-settings/markdown/beautifulsoup4。
- **驗收**: `uvicorn app.main:app` 啟動；`curl /api/health` → 200；缺 `GEMINI_API_KEY` 啟動時明確報錯。

### TASK-002 — `GET /api/voices`
- **Phase**: M1 ｜ **優先級**: P1 ｜ **依賴**: 001
- **檔案**: `backend/app/api/voices.py`、`main.py`(註冊)
- **內容**: 回 30 種預建 voice 靜態清單（name + 簡述）。
- **驗收**: `GET /api/voices` 回 30 筆；前端可作下拉資料源。

---

## M2 — 單塊合成（⚠️ 暫時 internal contract：此階段 /api/synthesize 回 WAV bytes，M4 改回 metadata）

### TASK-003 — `tts/prompt.py` prompt 組裝器
- **Phase**: M2 ｜ **優先級**: P0 ｜ **依賴**: 001
- **檔案**: `backend/app/tts/prompt.py`
- **內容**: 組 `固定 preamble + ### DIRECTOR'S NOTES(Style/Pacing/Accent) + ### TRANSCRIPT(原文)`；preamble 明示僅朗讀 TRANSCRIPT、勿讀出 notes；保留使用者 inline tags。
- **驗收**: 單元測試——含三區塊結構；voice/pacing/style/accent 組合產生預期字串；notes 不混入 transcript。

### TASK-004 — `tts/client.py` Gemini adapter（單塊）
- **Phase**: M2 ｜ **優先級**: P0 ｜ **依賴**: 001、003 ｜ **風險**: 高
- **檔案**: `backend/app/tts/client.py`
- **內容**: `generate_content(model=gemini-3.1-flash-tts-preview, contents=prompt, config=...AUDIO+VoiceConfig)`；**回應健全性檢查**（`inline_data` 存在、audio bytes 非空、mime 為音訊）；空/非音訊/classifier 誤拒 → retry+backoff；超上限 → 映射 502/504。封裝 `count_tokens`。
- **驗收**: mock 測試——正常回 PCM bytes；空/非音訊回應觸發 retry，最終映射 502/504 並記 error。**不在 CI 打真 API**。

### TASK-005 — `audio/pcm.py` PCM→WAV
- **Phase**: M2 ｜ **優先級**: P0 ｜ **依賴**: 001
- **檔案**: `backend/app/audio/pcm.py`
- **內容**: stdlib `wave` 將 raw PCM(24kHz/mono/16-bit) 封裝 WAV；frame-alignment 工具。
- **驗收**: 單元測試——WAV header 正確、單塊封裝可被標準播放器讀取。

### TASK-006 — `POST /api/synthesize`（短稿，不切塊/不存）
- **Phase**: M2 ｜ **優先級**: P0 ｜ **依賴**: 003、004、005
- **檔案**: `backend/app/api/synthesize.py`、`main.py`
- **內容**: 串 prompt→client→pcm，回 WAV bytes（**暫時 contract**，註解標明 M4 將改）。
- **驗收**: 一段短英文 → 回可播放 WAV；健全性檢查生效。

---

## M3 — 切塊與串接（高風險）

### TASK-007 — `tts/chunker.py` 雙條件切塊
- **Phase**: M3 ｜ **優先級**: P0 ｜ **依賴**: 004 ｜ **風險**: 高
- **檔案**: `backend/app/tts/chunker.py`
- **內容**: 雙條件——`count_tokens ≤ ~7,500` **且** `len ≤ MAX_CHUNK_CHARS≈2,500`（可調常數）；段落優先、必要時句子切分，切點落自然停頓。
  - ⚠️ token 數須以**完整 rendered prompt** 計（preamble + Director's Notes + TRANSCRIPT chunk），或以「chunk + 固定 overhead + notes margin」估算，**不可只算 transcript**（否則加上 notes 後仍可能逼近上限）。
- **驗收**: 單元測試——兩條件各自觸發切點、**含 notes/preamble 的完整 prompt token 不超上限**、單塊不超兩上限、超長單句處理、中英混段。

### TASK-008 — PCM 多塊串接 + 長稿 synthesize
- **Phase**: M3 ｜ **優先級**: P0 ｜ **依賴**: 005、006、007 ｜ **風險**: 高
- **檔案**: `backend/app/audio/pcm.py`(concat)、`api/synthesize.py`
- **內容**: 逐塊合成→raw PCM 串接→一次封裝 WAV。
- **驗收**: 程序化——①Σsample 守恆 ②frame-alignment（總 byte 偶數、% frame_size==0）③固定 sine PCM 多塊復原逐 sample 比對；長稿 e2e（mock client）。**感知接縫**人耳回歸，不以 sample 差值閾值自動判定。

---

## M4 — 持久化與歷史

### TASK-009 — `storage/db.py` SQLite schema + CRUD（分頁）
- **Phase**: M4 ｜ **優先級**: P0 ｜ **依賴**: 001
- **檔案**: `backend/app/storage/db.py`
- **內容**: schema 欄位：`id, created_at, text_excerpt, char_count, source(預設 'text'), voice, pacing/style/accent, format, audio_path, duration_ms, status`；CRUD：建立 / 分頁列表(limit/offset) / 取得 / 刪除。**source 欄位 M4 即建好，避免 M5 migration**。
- **驗收**: 單元測試——建立、分頁列表回 `items/total/limit/offset/has_more`、取得、刪除。

### TASK-010 — `storage/files.py` 音檔存取 + 安全路徑
- **Phase**: M4 ｜ **優先級**: P0 ｜ **依賴**: 001
- **檔案**: `backend/app/storage/files.py`
- **內容**: 存 `data/audio/{id}.wav`；id 驗證、安全路徑解析（拒 path traversal）。
- **驗收**: 單元測試——存取正常；`../`、絕對路徑等惡意 id 被拒。

### TASK-011 — synthesize 接 storage（取代 M2 暫時 contract）
- **Phase**: M4 ｜ **優先級**: P0 ｜ **依賴**: 008、009、010
- **檔案**: `backend/app/api/synthesize.py`
- **內容**: 合成後寫檔 + 寫 DB；回傳改為 `{id, created_at, metadata, audio_url=/api/audio/{id}}`。
- **驗收**: 合成後 DB 有列、`data/audio/{id}.wav` 存在、回 metadata + audio_url；失敗記 `status=error`。

### TASK-012 — `GET /api/history` 分頁 + `DELETE /api/history/{id}`
- **Phase**: M4 ｜ **優先級**: P1 ｜ **依賴**: 009、010（DELETE 需刪檔）
- **檔案**: `backend/app/api/history.py`、`main.py`
- **內容**: `GET /api/history?limit=50&offset=0` → `items/total/limit/offset/has_more`（時間倒序）；DELETE 移除檔 + 列。
- **驗收**: 分頁格式正確；DELETE 後檔與列皆消失（測試可經 storage 層直接 seed 一筆紀錄+檔，不必依賴真合成）。

### TASK-013 — `GET /api/audio/{id}`（Range + 下載）
- **Phase**: M4 ｜ **優先級**: P1 ｜ **依賴**: 010、011
- **檔案**: `backend/app/api/audio.py`、`main.py`
- **內容**: serve 音檔，支援 Range（206 partial）線上播放、`?download=1` 設 Content-Disposition。
- **驗收**: Range 請求回 206 + 正確 bytes；`?download=1` 觸發下載；未知 id → 404。

---

## M5 — markdown 正規化

### TASK-014 — `ingest/markdown.py` + synthesize 接 source
- **Phase**: M5 ｜ **優先級**: P1 ｜ **依賴**: 011
- **檔案**: `backend/app/ingest/markdown.py`、`api/synthesize.py`
- **內容**: `markdown`→HTML→`BeautifulSoup` 取純文字，保留段落換行；synthesize 依輸入來源設 `source`（欄位 M4 已建，**無 migration**）。
- **驗收**: 單元測試——標題/清單/程式碼/連結 → 純文字、段落保留；上傳 .md 後該筆 `source='md'`。

---

## M6 — 前端核心

### TASK-015 — Next.js scaffolding + rewrites proxy
- **Phase**: M6 ｜ **優先級**: P0 ｜ **依賴**: 無（整合驗收需後端）
- **檔案**: `frontend/`（create-next-app 產生）、`frontend/next.config.js`
- **內容**: App Router + TS；`rewrites()` 將 `/api/*` 同路徑 proxy 到 :8000；樣式用最小 CSS（不綁 Tailwind）。
- **驗收**: `next dev` 起；前端打 `/api/health` 經 proxy 通。

### TASK-016 — 主頁 UI + api-client + AudioPlayer
- **Phase**: M6 ｜ **優先級**: P0 ｜ **依賴**: 015、002、013、014（`.md` 上傳需後端 markdown 正規化已就緒）
- **檔案**: `frontend/app/page.tsx`、`frontend/components/AudioPlayer.tsx`、`frontend/lib/api-client.ts`
- **內容**: 文字輸入/上傳 .md、voice 下拉、少量 tag preset buttons（插入游標）、自由 Director's Notes（Style/Pacing/Accent）、生成、播放器 + 下載。
- **驗收**: 瀏覽器輸入/上傳 → 生成 → 線上播放 → 下載成功。

---

## M7 — 前端歷史

### TASK-017 — `HistoryList` 清單（分頁 + 操作）
- **Phase**: M7 ｜ **優先級**: P1 ｜ **依賴**: 016、012
- **檔案**: `frontend/components/HistoryList.tsx`
- **內容**: 最新 50 筆 + 底部 `Load more`（limit/offset）；每筆播放/下載/刪除。
- **驗收**: 清單顯示、Load more 追加、重播/下載/刪除皆作用。

---

## M8 — 整合與文件

### TASK-018 — e2e 串接 + README + 環境檔
- **Phase**: M8 ｜ **優先級**: P1 ｜ **依賴**: 全部
- **檔案**: `README.md`、`.env.example`、`backend/tests/`(補齊)
- **內容**: 全流程 e2e（真實 Gemini 跑一段中英交雜稿，人耳確認英文發音/語速可辨、長稿接縫）；README 啟動指南（後端 uvicorn、前端 next dev）。
- **驗收**: 照 README 在新環境可啟動；全流程 e2e 通過；單元測試（chunker/pcm/markdown/prompt/client mock）綠燈。

---

## 摘要

| 里程碑 | TASKs | 風險 |
|---|---|---|
| M1 骨架 | 001, 002 | 低 |
| M2 單塊合成 | 003, 004, 005, 006 | 高（004） |
| M3 切塊串接 | 007, 008 | 高 |
| M4 持久化歷史 | 009, 010, 011, 012, 013 | 中 |
| M5 markdown | 014 | 中 |
| M6 前端核心 | 015, 016 | 中 |
| M7 前端歷史 | 017 | 中 |
| M8 整合文件 | 018 | 低 |

共 18 個 TASK。
