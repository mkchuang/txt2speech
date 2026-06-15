# 架構設計方案 - txt2speech Gemini TTS 練講工具

> **設計日期**: 2026-06-15
> **作者**: mkchuang
> **狀態**: approved（2026-06-15，兩輪 validate-plan WARN findings 全數收斂）
> **設計類型**: whole-project
> **規模評估**: L（跨 6 模組、新外部整合 Gemini、前後端兩進程）

## Planning Scope

這是 **whole-project implementation plan**。專案在 `adf.design` 階段已被使用者明確收斂為**單一交付（單一 phase）**，因此本 plan 涵蓋整個 baseline，內部以實作里程碑（M1–M8）排序 rollout，不存在被省略的後續 product phase。

對應 baseline：`.project/memory/project.md`、`.project/context/tech-stack.md`、`.project/context/conventions.md`。

## 需求分析

### 硬約束（不可違反）
- TTS 模型固定 `gemini-3.1-flash-tts-preview`，**單次輸入 ≤ 8,192 tokens**，輸出 PCM 24kHz mono 16-bit。
- 不引入教練 LLM；重點/發音/語速表現靠 **prompt + audio tags + voice/參數**（見 ADR-001）。
  - **控制機制已確認（官方文件 + Context7）**：tags 與 Director's Notes 皆寫在 `contents` prompt 文字內，config 僅選 voice。
    - Inline tags（方括號，非窮舉、需實驗）：`[whispers]`/`[laughs]`/`[excited]`/`[very slow]`/`[very fast]` …
    - Director's Notes（結構化區塊）：`### DIRECTOR'S NOTES` + `Style:` / `Pacing:` / `Accent:` 三軸獨立控制。
    - **語速 = Director's Notes `Pacing:` + inline `[very slow/fast]`**（不再是猜測）。
    - 重點強調：inline tag 包詞或 transcript 母音拉長（如 `Beauuutiful`）；無專屬 emphasis markup。
- 輸入：貼上文字 **或** 上傳 `.md`（後端正規化為純文字）。
- 中英交雜，聚焦英文發音；發音正確性依賴模型內建能力。
- 每次請求**重新產生**，不做去重快取。
- 須**持久化歷史**：清單查看、線上播放、下載。
- `GEMINI_API_KEY` 僅後端持有，不入前端/版控。
- 本機開發；前端 `next dev`、後端 `uvicorn` 各自啟動（不使用 PM2）。

### 軟約束（可協商）
- 輸出格式 WAV 為主（無需外部編碼器）；MP3 可選。
- 語速以 Director's Notes `Pacing:` 控制（前端可給離散等級 + 自由文字框），細部以實測微調。
- 歷史無保留上限（本機單人，量不大）。

## 架構方案

整體拓撲（前端 Next.js UI + 後端 FastAPI 全邏輯）已於 design 階段與使用者定案，本節只比較**仍開放的核心軸：合成執行模型**。

### 方案 A：同步合成（request 內完成）
`POST /api/synthesize` 在單一請求內完成「md 正規化 → 切塊 → 逐塊呼叫 Gemini → PCM 串接 → 存檔 → 寫 DB → 回傳 metadata」，前端拿到 `audio_url` 後播放。

- 優點：實作簡單、無 job 狀態機、無輪詢；本機單人足夠。
- 缺點：長稿（多塊）請求時間長，前端需 loading 狀態與合理 timeout。

### 方案 B：非同步 job + 輪詢
`POST /api/synthesize` 建立 job 回 `job_id`，背景 worker 合成，前端輪詢 `GET /api/jobs/{id}` 取狀態與結果。

- 優點：長稿不阻塞、可顯示進度。
- 缺點：需 job 狀態管理、背景任務、額外端點與前端輪詢；對本機單人過度設計。

## 結構化評估

| 維度 | 權重 | 方案 A 同步 | 方案 B 非同步 | 說明 |
|---|---:|---:|---:|---|
| 實作複雜度 | 0.30 | 9 | 4 | A 無狀態機/worker |
| 本機單人適配 | 0.25 | 9 | 6 | 無並發壓力 |
| 長稿體驗 | 0.20 | 6 | 9 | B 可顯示進度 |
| 可維護性 | 0.15 | 8 | 6 | A 路徑單純 |
| 擴充性 | 0.10 | 5 | 9 | B 易加佇列 |
| **加權總分** | | **7.85** | **6.05** | |

## 推薦方案

**採用方案 A（同步合成）**。理由：本機單人、無並發；A 以最小複雜度滿足全部硬需求。長稿延遲以「前端 loading + 後端逐塊 log + 合理 timeout（建議 client 120s）」緩解。

**推薦會改變的條件**：若實測常見講稿需切成多塊且總合成時間 > ~60s 造成體感不佳，或日後要支援多人並發，再升級為方案 B（plan 已預留 `tts` 與 `storage` 邊界，可加 job 層而不改既有模組）。

## 變更差異（Delta）

> 全新專案，無既有原始碼可改；以下 ADDED 即完整建置清單，MODIFIED 僅針對既有 repo 配置檔，無 REMOVED。

### ADDED（新增）

| 檔案/模組 | 說明 | 風險 |
|---|---|---|
| `backend/app/config.py` | pydantic-settings 載入 `GEMINI_API_KEY`、`DATA_DIR`、CORS 來源 | 低 |
| `backend/app/main.py` | FastAPI app、CORS、路由註冊、`/api/health` | 低 |
| `backend/app/ingest/markdown.py` | `.md`/文字 → 純文字（去除 md 語法），保留段落換行 | 中：去除規則需覆蓋常見 md |
| `backend/app/tts/prompt.py` | prompt 組裝器：固定 preamble +`### DIRECTOR'S NOTES`(Style/Pacing/Accent) + inline audio tags +`### TRANSCRIPT`(原文)；preamble 明示只朗讀 TRANSCRIPT、勿讀出 notes | 中：避免把指令朗讀出來 |
| `backend/app/tts/chunker.py` | **雙條件切塊**：`count_tokens`(安全上限 ~7,500) **且** `MAX_CHUNK_CHARS≈2,500`（可調常數，M3 實測校正）；段落優先、必要時句子切分（切點落在自然停頓以降低接縫感） | 高：8192 上限 + 3.1 長音訊一致性漂移 |
| `backend/app/tts/client.py` | Gemini adapter：逐塊 `generate_content`；**回應健全性檢查**（`inline_data` 存在、audio bytes 非空、mime 為音訊）；空/非音訊/classifier 誤拒 → retry+backoff；錯誤映射 502/504 | 高：preview 偶發回 text token / 無 audio / 誤拒 |
| `backend/app/audio/pcm.py` | 串接多塊 raw PCM → 單一 WAV（stdlib `wave`）；可選 MP3 | 中：sample 參數需正確 |
| `backend/app/storage/db.py` | SQLite schema（**M4 即含 `source` 欄位，預設 `'text'`，避免 M5 migration**）、CRUD（建立/分頁列表/取得/刪除） | 中：路徑遍歷防護 |
| `backend/app/storage/files.py` | 音檔存 `data/audio/{id}.wav`、安全路徑解析 | 中：path traversal |
| `backend/app/api/synthesize.py` | `POST /api/synthesize`：正規化→切塊→合成→存→回 metadata | 中 |
| `backend/app/api/history.py` | `GET /api/history?limit=50&offset=0`（回 `items/total/limit/offset/has_more`）、`DELETE /api/history/{id}` | 低 |
| `backend/app/api/audio.py` | `GET /api/audio/{id}`：Range 串流播放、`?download=1` 下載 | 中：Range/Content-Disposition |
| `backend/app/api/voices.py` | `GET /api/voices`：回 30 種預建 voice 清單 | 低 |
| `backend/tests/` | 切塊、PCM 串接、md 正規化、prompt 組裝單元測試（Gemini mock） | 低 |
| `backend/pyproject.toml` | 依賴：fastapi, uvicorn, google-genai, pydantic-settings, markdown, beautifulsoup4 | 低 |
| `frontend/app/page.tsx` | 主頁：文字輸入/上傳 .md、voice 選擇、少量 tag preset buttons（插入游標位置）、自由 Director's Notes 文字框（Style/Pacing/Accent）、生成、播放器 | 中 |
| `frontend/components/AudioPlayer.tsx` | 線上播放器（HTML5 audio + 下載鈕） | 低 |
| `frontend/components/HistoryList.tsx` | 歷史清單：最新 50 筆 + 底部 `Load more`（limit/offset）、播放/下載/刪除 | 中 |
| `frontend/lib/api-client.ts` | 呼叫後端 API 封裝 | 低 |
| `frontend/`（scaffolding） | `package.json`/`tsconfig.json`/`next.config.js` 等由 `create-next-app` 產生；本表只列淨增應用檔，scaffolding 不逐一列舉。樣式先用內建/最小 CSS，不綁 Tailwind | 低 |
| `frontend/next.config.js` | `rewrites()` 將 `/api/*` **同路徑** proxy 到後端 :8000（避免 CORS；前後端與測試一律用 `/api/*`） | 低 |
| `data/`（執行期） | 音檔 + `app.sqlite`，已在 `.gitignore` | 低 |
| `.env.example` | 範例環境變數（不含真實金鑰） | 低 |
| `README.md` | 啟動指南（後端 uvicorn、前端 next dev） | 低 |

### MODIFIED（修改）

| 檔案/模組 | 變更內容 | 影響範圍 | 風險 |
|---|---|---|---|
| `.project/context/conventions.md` | 已填入命名/目錄/錯誤處理/測試規範 | 文件 | 低 |
| `.project/design/current.md` | 指向本 plan | 文件 | 低 |

### REMOVED（移除）
無。

### UNCHANGED（有依賴但不動）
- ADF 框架檔（`.adf/`、`.claude/`、`.agents/` 等）：與實作無耦合。

## 實施計劃

| 階段 | 變更內容 | 風險等級 | 驗收方式 | 回滾方案 |
|---|---|---|---|---|
| M1 後端骨架 | config、main、`/api/health`、`/api/voices` | 低 | `curl /api/health` 200；`/api/voices` 回清單 | 刪 backend，無外部副作用 |
| M2 單塊合成 | tts/prompt、tts/client、audio/pcm；短稿 `/api/synthesize`（不切塊、不存）。⚠️ **暫時 internal contract**：此階段回 WAV bytes，M4 改回 metadata+audio URL；前端 M6 須對齊 M4 後的 shape，勿依賴此暫時回傳 | 高 | 一段短英文 → 回可播放 WAV bytes；回應健全性檢查生效（空/非音訊會 retry） | 還原至 M1 |
| M3 切塊與串接 | tts/chunker（token + `MAX_CHUNK_CHARS≈2,500` 雙條件、段落/句子邊界）、PCM 串接長稿 | 高 | **程序化**：①Σsample 數守恆 ②frame-alignment（總 byte 偶數、% frame_size==0）③sine PCM 多塊復原比對原始。**人耳**：長稿整體音色/節奏一致、接縫無感（感知層，手動回歸） | 停用切塊，限制輸入長度 |
| M4 持久化與歷史 | storage/db、storage/files、history 路由（**limit/offset 分頁**）、audio 路由（Range/下載）、DELETE | 中 | 合成後出現在 `/api/history`（回 items/total/has_more）；`/api/audio/{id}` 可播放與下載；DELETE 移除檔+列 | 保留合成、停用歷史寫入 |
| M5 markdown 正規化 | ingest/markdown；設定 `source` 來源標記（欄位已於 M4 建好，**無 schema migration**） | 中 | 上傳含 `#/*/code` 的 .md → 朗讀無 md 符號，且 `source='md'` | 改為原文直送（不正規化） |
| M6 前端核心 | page、AudioPlayer、api-client、next rewrites | 中 | 瀏覽器輸入→生成→線上播放→下載成功 | 回退至 API 手動測試 |
| M7 前端歷史 | HistoryList（播放/下載/刪除） | 中 | 歷史清單顯示、可重播/下載/刪除 | 隱藏歷史面板 |
| M8 整合與文件 | 端到端、`.env.example`、README、最小測試補齊 | 低 | 全流程 e2e 通過；新環境照 README 可啟動 | — |

## 測試策略
- **單元（pytest，Gemini mock）**：
  - `chunker`：**雙條件**（token 上限 + 字元/長度上限）皆觸發切點、單塊不超兩者上限、超長單句處理、中英混段。
  - `pcm`：①串接後 Σsample 數 == sum(各塊)；②frame-alignment 斷言（總 byte 為偶數、% frame_size==0，抓位元組錯位爆音）；③固定 sine wave 切多塊→串接→復原與原始逐 sample 比對；④WAV header 正確、單塊與多塊在短稿等價。
    > 註：鄰塊「感知接縫」屬獨立合成語音的固有不連續，不以 sample 差值閾值自動判定（會 flaky）；以「切點落在靜音/句界」設計緩解 + 人耳回歸。
  - `markdown`：標題/清單/程式碼/連結 → 純文字；段落保留。
  - `prompt`：含固定 preamble +`### DIRECTOR'S NOTES`+`### TRANSCRIPT` 結構；speed/style/voice 組合產生預期字串。
  - `client`（mock）：回應健全性檢查——`inline_data` 缺失/audio bytes 空/非音訊 mime → 觸發 retry+backoff；超過重試上限 → 映射 502/504 並記 error。
- **整合**：以假 PCM 回應替換 Gemini，驗 `/api/synthesize → /api/history → /api/audio/{id}` 串接與 DB/檔案一致性。
- **手動驗證**：真實 Gemini 跑一段中英交雜稿，人耳確認英文發音與語速等級可辨；長稿串接無接縫。
- **覆蓋重點**：切塊與串接是最高風險，必須有測試；Gemini 呼叫本身以 mock 隔離、不在 CI 打真 API。

## Rollout / Rollback
- **Rollout**：依 M1→M8 漸進；每個 M 可獨立驗收後再前進。前端在 M6 才接入，之前以 `curl`/pytest 驗 API。
- **可觀測**：後端 `logging` 記錄每次合成的塊數、各塊 token 估計、Gemini 延遲與失敗；歷史 `status` 欄位留存成敗。
- **Rollback**：本機無部署，逐 M 以 git 還原；資料層（`data/`）與程式分離，回滾程式不影響既有歷史檔。
- **失敗模式處置**：Gemini 配額/錯誤 → 回 502/504 + 歷史記 error；切塊失敗 → 拒絕並提示縮短輸入。

## 決策與 Open Questions

**已決策（本 plan 採用，待你批准）**
1. 合成執行模型 = **同步**（方案 A）。
2. 主要輸出 = **WAV**（raw PCM 串接後一次封裝，無需 ffmpeg）；MP3 列為可選後續。
3. 前後端連線 = **Next.js `rewrites` proxy** 到 :8000（免 CORS 設定）。
4. TTS 控制 = **Director's Notes（Style/Pacing/Accent）+ inline audio tags**，寫入 `contents` prompt；前端提供有限預設選項 + 自由 Director's Notes 文字框（不硬編死標籤表，因官方標籤非窮舉、需實驗）。語速由 `Pacing:` 控制。
5. markdown 正規化 = **server-side**（`markdown`→HTML→`BeautifulSoup` 取文字）。
6. 切塊 = **雙條件**：SDK `count_tokens`（安全上限 ~7,500，留 margin）**且** `MAX_CHUNK_CHARS≈2,500`（起始值，可調常數，M3 實測校正，緩解 3.1 長音訊一致性漂移）；段落優先、必要時句子切分，切點盡量落在自然停頓。
7. 架構決策見 **ADR-001**（TTS-only、prompt 驅動）。
8. **TTS robustness**：prompt 固定 preamble + `### TRANSCRIPT` 包住原文，明示勿朗讀 Director's Notes；client 檢查 `inline_data`/非空 audio/音訊 mime，空或非音訊回傳 retry+backoff。
9. **Q3 歷史分頁（已決策）**：`GET /api/history?limit=50&offset=0` 回 `items/total/limit/offset/has_more`；前端最新 50 筆 + `Load more`。**不做**搜尋/篩選/tag/日期區間。納入 **M4**。
10. **Q4 重點強調 UX（已決策）**：baseline = 手動 inline tags（`[slowly]`/`[emphasize]`/`[pause]`/`[excited]`/`[very slow]` …）+ 少量 preset buttons（插入游標位置）+ 自由 Director's Notes 文字框（Style/Pacing/Accent）。**不做**選段自動包 tag、rich editor、逐段 emphasis UI（列後續）。

**Open Questions（剩餘，不阻塞 M1–M4）**
- Q2：是否需要 MP3 輸出（牽涉 ffmpeg 依賴）？預設先不做，stdlib `wave` 輸出 WAV。

---
*本文件狀態 **approved**（2026-06-15）；已由 `breakdown` 拆為 18 個 TASK（見 `tasks-2026-06-15-gemini-tts-speech-practice.md`），可交 `develop` 實作。*
