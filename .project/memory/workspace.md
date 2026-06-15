# 工作記憶 - Workspace Memory

> 此文件記錄動態工作狀態，頻繁更新
> 最後更新：[由 /update-memory 指令更新]
>
> **模式說明**：
> - **團隊模式**：使用 `workspace-team.md` + `workspace-<用戶>.md`
> - **單人模式**：使用此文件 `workspace.md`
> - 模式由 `.project/team.yaml` 存在與否決定

## 📊 系統狀態總覽

| 文件 | 狀態 | 大小 | 最後更新 |
|------|------|------|----------|
| project.md | ✅ 已初始化（/adf.design） | - | 2026-06-15 |
| workspace.md | ✅ 已初始化 | - | 2026-06-15 |
| current.md | ✅ 指向 plan-2026-06-15-gemini-tts-speech-practice（approved） | - | 2026-06-15 |

### 維護提醒
- 當前文件大小：[行數]
- 上次歸檔：無
- 建議：超過 500 行時執行 `/archive-memory`

### 快速操作
```bash
# 常用指令
/load-memory      # 載入記憶總覽
/update-memory    # 更新此文件
/archive-memory   # 歸檔歷史記錄
/design           # 專案定義
/planner             # 架構設計
/develop          # 開發實施
```

---

## 🏗️ 當前架構方案

| 項目 | 內容 |
|------|------|
| **採用方案** | Next.js 前端 + Python FastAPI 後端，純 Gemini TTS（無教練 LLM） |
| **設計文件** | plan-2026-06-15-gemini-tts-speech-practice.md（**approved**）；ADR-001；tasks-2026-06-15-...md（18 TASK） |
| **選定原因** | 需求收斂為「帶參數控制的 Gemini TTS 練講工具」；前端簡單(Next.js)、後端沿用 Python 呼叫 google-genai |
| **關鍵決策** | ①不引入教練 LLM，靠 TTS prompt+audio tags ②TTS=gemini-3.1-flash-tts-preview ③本機各自啟動（next dev / uvicorn），不用 PM2 ④發音依文檔內建能力 ⑤輸入=貼上文字或上傳.md ⑥單一 phase、不做去重快取、每次重新產生 ⑦歷史紀錄：SQLite(metadata)+檔案系統(音檔)，提供查看/線上播放/下載 |
| **最後更新** | 2026-06-15 |

---

## 🎯 當前工作重點

### 本週主要任務
- [x] 任務 1：以 /adf.design 定義專案大框架（完成）
- [x] 任務 2：/adf.planner 產出 whole-project plan（已 approved）
- [x] 任務 3：/adf.breakdown 拆出 18 個 TASK（tasks-2026-06-15-...md）
- [x] 任務 4：/adf.develop 完成 TASK-001 後端骨架 + config（code review / Codex app 仲裁驗證：REVIEW PASS）
- [ ] 任務 5：下一步依關鍵路徑開 TASK-003/004/005；TASK-002 voices 可並行補齊 M1

### 當前技術挑戰
1. **TTS 切塊 + PCM 串接品質**（最高風險）
   - 狀態：規劃（排 pytest 必測）
   - 方向：**雙條件切塊**（count_tokens ~7,500 + `MAX_CHUNK_CHARS≈2,500` 可調常數，M3 實測校正）、切點落自然停頓、raw PCM 串接再一次封裝 WAV
   - ⚠️ 實作約束：token 須以**完整 rendered prompt**（preamble+Director's Notes+TRANSCRIPT）計，勿只算 transcript（否則加 notes 後逼近 8192 上限）
   - 接縫測試（程序化）：Σsample 守恆、frame-alignment 斷言、sine PCM 多塊復原比對；**不**用 sample 差值閾值判接縫（獨立合成語音會 flaky）→ 感知層人耳回歸

2. **語速/語氣控制**（已解除為低風險）
   - 狀態：機制已確認（官方文件 + Context7）
   - 方向：Director's Notes（Style/Pacing/Accent）+ inline audio tags 寫入 contents prompt；語速由 Pacing 控制。tags 非窮舉→前端給預設選項 + 自由文字框

3. **preview 模型可能變動**
   - 狀態：已緩解設計
   - 方向：tts/ adapter 為唯一 AI 邊界，隔離 API 變動

### 短期目標（本月）
- 目標 1：完成 M1（TASK-001 已 pass；TASK-002 voices 待做）
- 目標 2：完成 M1–M4（後端骨架 + 合成 + 切塊串接 + 持久化/歷史）

### 待解決問題
- [x] plan-2026-06-15-gemini-tts-speech-practice 已 **approved**（2026-06-15），已 breakdown 為 18 TASK
- [x] Q1 語速控制 → 已確認（Director's Notes Pacing + inline tags）
- [x] Q3 歷史分頁 → 已決策：limit/offset + Load more，無搜尋（納入 M4）
- [x] Q4 重點強調 → 已決策：手動 inline tags + preset buttons + 自由 Director's Notes；選段強調列後續
- [ ] Q2 是否需 MP3 輸出（牽涉 ffmpeg 依賴；預設不做，WAV via stdlib wave）

---

## 📊 模組開發狀態

*最後更新：2026-06-15（TASK-001 review pass / update-memory）*

| 模組 | 功能 | 開發狀態 | 驗證狀態 | 說明 |
|------|------|----------|----------|------|
| config | 設定/金鑰 | 🟢 已完成 | 🟢 已驗證 | TASK-001：pydantic-settings 載入 `GEMINI_API_KEY`/`DATA_DIR`/`CORS_ORIGINS` |
| api | FastAPI app + health；synthesize/history/audio/voices 待續 | 🟡 部分完成 | 🟢 health 已驗證 | TASK-001：`/api/health`；其餘路由待後續 TASK |
| tts | Gemini adapter + 切塊 | ⚫ 未開始 | ⚫ 未驗證 | M2/M3，最高風險 |
| audio | PCM→WAV 串接 | ⚫ 未開始 | ⚫ 未驗證 | M2/M3 |
| storage | SQLite + 檔案系統 | ⚫ 未開始 | ⚫ 未驗證 | M4 |
| ingest | markdown 正規化 | ⚫ 未開始 | ⚫ 未驗證 | M5 |
| frontend | Next.js UI + 歷史 | ⚫ 未開始 | ⚫ 未驗證 | M6/M7 |

### 狀態圖例
- ⚫ **未開始**: 尚未開始開發/測試
- 🟡 **進行中**: 正在進行
- 🟢 **已完成**: 開發完成/測試通過
- 🔴 **受阻**: 遇到阻礙/測試失敗
- 🟣 **需重構**: 功能可用但需要改進

### 🚨 問題與阻塞
1. **TASK-001 review**
   - 狀態：REVIEW PASS；Critical/Major 無 blocker，acceptance criteria 已有 evidence。
   - 驗證：缺 `GEMINI_API_KEY` 會報 `Field required`；假 key 可啟動 uvicorn；`/api/health` 回 200 `{"status":"ok"}`；`python3 -m compileall -q app` 與 `git diff --check` 通過。
   - 殘留風險：尚未觸及 Gemini adapter、voices、synthesize/history/audio/storage；後續高風險仍是 TASK-004、TASK-007、TASK-008。

---

## 📈 進度追蹤

### 專案里程碑
- [ ] **M1**: 後端骨架（TASK-001 pass；TASK-002 voices 待做）
- [ ] **M2**: 核心功能開發
- [ ] **M3**: 測試和優化
- [ ] **M4**: 部署上線

### 最近完成

#### 本週
- ✅ TASK-001：後端 FastAPI 骨架、pydantic-settings config、`/api/health`、`.env.example`、package init 完成；`.gitignore` 已改為只忽略 `/data/audio/`，避免 `backend/app/audio` 被忽略。

#### 上週
- ✅ [完成項目 1]：待補充

### 版本規劃
- **v0.1.0**: 基礎功能（目標：待補充）
- **v0.2.0**: 核心功能（目標：待補充）
- **v1.0.0**: 正式版本（目標：待補充）

---

## 📝 會話記錄

### 最近重要決策

| 日期 | 決策 | 原因 | ADR |
|------|------|------|-----|
| 2026-06-15 | TTS-only、prompt 驅動，不引入教練 LLM | TTS 模型不支援 structured output；使用者要簡單 | ADR-001 |
| 2026-06-15 | 合成執行採同步（方案 A） | 本機單人、最小複雜度（加權 7.85 vs 6.05） | plan 決策表 |
| 2026-06-15 | 輸出 WAV（raw PCM 串接，免 ffmpeg）；前後端用 next rewrites proxy | 降依賴、免 CORS | plan 決策表 |
| 2026-06-15 | TTS 控制用 Director's Notes(Style/Pacing/Accent)+inline tags，寫入 contents | 官方確認語法；語速/重點可控，免教練 LLM | ADR-001 |
| 2026-06-15 | validate-plan=WARN，修 5 項 contract drift（/api/* 統一、雙條件切塊、TTS retry/空音訊、WAV 去 ffmpeg、M2 暫時 contract）+ 定 Q3/Q4 | 進 breakdown 前收斂漂移 | plan |

### 待確認事項
- [x] plan 已 approved；4 項建議決策（WAV / proxy / Director's Notes / 雙條件切塊）皆採用
- [ ] TASK-001 已通過 review/update-memory，進入 commit/push gate；下一步銜接 TASK-002 或關鍵路徑 TASK-003/004/005

### 討論備註
[最近討論的重要內容...]

---

## 📝 Code Review 記錄

### 最近審查

| 日期 | 範圍 | 結果 | 說明 |
|------|------|------|------|
| 2026-06-15 | TASK-001 後端骨架 + config | 通過 | REVIEW PASS；Critical/Major 無 blocker；acceptance criteria 已有 evidence |

### 審查統計
- 總審查次數：1
- 通過審查：1
- 需修復：0

---

## 📚 歷史歸檔索引

| 歸檔文件 | 時間範圍 | 說明 |
|----------|----------|------|
| [無歸檔記錄] | - | - |

---
*使用 `/update-memory` 更新此文件*
*使用 `/archive-memory` 歸檔歷史記錄*
*更新頻率：高（每次會話結束時）*
