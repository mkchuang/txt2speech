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
- [x] 任務 5：完成 TASK-002 `GET /api/voices` 靜態清單（30 種 Gemini TTS voice，review/app gate pass）
- [x] 任務 6：完成 TASK-003 `tts/prompt.py` prompt 組裝器（fixed 3 sections + note/voice sanitizer，review/app gate pass）
- [x] 任務 7：完成 TASK-004 `tts/client.py` Gemini adapter（mock tests pass，lazy google import，review/app gate pass）
- [x] 任務 8：完成 TASK-005 `audio/pcm.py` PCM→WAV（review/app gate pass）
- [x] 任務 9：完成 TASK-006 `POST /api/synthesize` 短稿合成（M2 暫時回 WAV bytes，review pass）
- [x] 任務 10：完成 TASK-007 `tts/chunker.py` 雙條件切塊（review/app 仲裁驗證：REVIEW PASS）
- [x] 任務 11：完成 TASK-008 PCM 多塊串接 + 長稿 synthesize（review/app gate pass）
- [x] 任務 12：完成 TASK-009 `storage/db.py` SQLite schema + CRUD（分頁，review/app gate pass）
- [x] 任務 13：完成 TASK-010 `storage/files.py` 音檔存取 + 安全路徑（review/app gate pass）
- [x] 任務 14：完成 TASK-011 synthesize 接 storage（取代 M2 暫時 contract；review/app gate pass）
- [x] 任務 15：完成 TASK-012 `GET /api/history` 分頁 + `DELETE /api/history/{id}`（review/app gate pass）
- [x] 任務 16：完成 TASK-013 `GET /api/audio/{id}`（Range + 下載；review/app gate pass）
- [x] 任務 17：完成 TASK-014 markdown→plain text normalizer + synthesize 接 `source`（review/app gate pass）
- [x] 任務 18：完成 TASK-015 Next.js scaffolding + rewrites proxy（review/app 仲裁驗證：REVIEW PASS）
- [x] 任務 19：完成 TASK-016 主頁 UI + api-client + AudioPlayer（code review / Codex app 仲裁驗證：REVIEW PASS）
- [x] 任務 20：完成 TASK-017 HistoryList 清單（OpenCode develop、Codex app 仲裁驗證、兩輪 Codex code review，最終 REVIEW PASS）
- [ ] 下一步：依 active plan 開 TASK-018 e2e 串接 + README + 環境檔

### 當前技術挑戰
1. **TTS 切塊 + PCM 串接品質**（最高風險）
   - 狀態：TASK-007/008 已完成雙條件切塊器、長稿逐塊合成、raw PCM 多塊串接與一次 WAV 封裝。
   - 已落地能力：token limit + char limit、段落優先、句子 fallback、CJK 標點無空白句界、no-space / single long word 的 token-aware char fallback。
   - token accounting：預設 heuristic 以完整 `build_prompt(chunk, style, pacing, accent, voice)` 估 token；explicit overhead/custom counter path 使用 `TOKEN_ACCOUNTING_MARGIN = 1`，prompt overhead 超 budget 會 raise `ChunkingError`。
   - 接縫測試（程序化）：Σsample 守恆、frame-alignment 斷言、sine PCM 多塊復原比對；**不**用 sample 差值閾值判接縫（獨立合成語音會 flaky）→ 感知層人耳回歸仍待 M8/真實 Gemini 手動驗證。
   - count_tokens 策略：長稿 synthesize 僅用 Gemini `count_tokens` 取得固定 prompt overhead；chunk 內容使用本地 estimate，避免 no-space/char fallback 時產生大量遠端 token-count 呼叫。

2. **語速/語氣控制**（已解除為低風險）
   - 狀態：機制已確認（官方文件 + Context7）
   - 方向：Director's Notes（Style/Pacing/Accent）+ inline audio tags 寫入 contents prompt；語速由 Pacing 控制。tags 非窮舉→前端給預設選項 + 自由文字框

3. **preview 模型可能變動**
   - 狀態：已緩解設計
   - 方向：TASK-004 已以 `GeminiTtsClient` 作為唯一 google-genai 邊界；module import lazy load SDK，mock 測試覆蓋空/非音訊/timeout retry 與 `count_tokens`

### 短期目標（本月）
- 目標 1：完成 M1（TASK-001 + TASK-002 已 pass）
- 目標 2：完成 M1–M5（後端骨架 + 合成 + 切塊串接 + 持久化/歷史 + markdown 正規化）
- 目標 3：完成 M6 前端核心（TASK-015 scaffold/proxy + TASK-016 主頁 UI/api-client/AudioPlayer 已完成）
- 目標 4：完成 M7 前端歷史清單播放/下載/刪除（TASK-017 已完成）
- 目標 5：開 TASK-018，完成真實 Gemini e2e、人耳 playback、README 與環境檔回歸

### 待解決問題
- [x] plan-2026-06-15-gemini-tts-speech-practice 已 **approved**（2026-06-15），已 breakdown 為 18 TASK
- [x] Q1 語速控制 → 已確認（Director's Notes Pacing + inline tags）
- [x] Q3 歷史分頁 → 已決策：limit/offset + Load more，無搜尋（納入 M4）
- [x] Q4 重點強調 → 已決策：手動 inline tags + preset buttons + 自由 Director's Notes；選段強調列後續
- [ ] Q2 是否需 MP3 輸出（牽涉 ffmpeg 依賴；預設不做，WAV via stdlib wave）

---

## 📊 模組開發狀態

*最後更新：2026-06-15（TASK-017 review pass / update-memory）*

| 模組 | 功能 | 開發狀態 | 驗證狀態 | 說明 |
|------|------|----------|----------|------|
| config | 設定/金鑰 | 🟢 已完成 | 🟢 已驗證 | TASK-001：pydantic-settings 載入 `GEMINI_API_KEY`/`DATA_DIR`/`CORS_ORIGINS` |
| api | FastAPI app + health/voices/synthesize/history/audio/md source | 🟢 M5 已完成 | 🟢 health/voices/synthesize/history/audio/md source 已驗證 | TASK-001：`/api/health`；TASK-002：`/api/voices`；TASK-011：`POST /api/synthesize` 回 metadata/audio_url；TASK-012：history/delete；TASK-013：audio Range + download；TASK-014：`source='md'` normalize 後合成並寫 metadata |
| tts | prompt 組裝器 + Gemini adapter + 雙條件切塊器 + 長稿 synthesize 整合完成 | 🟢 M3 已完成 | 🟢 prompt/client/chunker/synthesize mock 已驗證 | TASK-003/004/007/008；`count_tokens` 僅算 prompt overhead，chunk 內容本地估算 |
| audio | PCM→WAV + 多塊 concat | 🟢 M3 已完成 | 🟢 PCM/WAV/concat 已驗證 | TASK-005/008：24kHz mono 16-bit 預設、frame alignment、stdlib `wave` WAV 封裝、raw PCM 多塊串接 |
| storage | SQLite metadata + 檔案系統 | 🟢 M4 已完成 | 🟢 DB/file/synthesize/history/audio integration 已驗證 | TASK-009：`storage/db.py` schema + create/list/get/delete；TASK-010：`storage/files.py` save/resolve/delete + path traversal 防護；TASK-011：synthesize 寫 completed/error row；TASK-012：history list/delete 串 DB + file；TASK-013：audio endpoint 讀 `DATA_DIR/audio/{id}.wav` |
| ingest | markdown→plain text normalizer | 🟢 M5 已完成 | 🟢 heading/list/code/link/paragraph 與 synthesize md source 已驗證 | TASK-014 |
| frontend | Next.js scaffold + rewrites proxy + 主頁 UI/api-client/AudioPlayer/HistoryList | 🟢 M7 前端歷史已完成 | 🟢 lint/tsc/audit/ci dry-run/app gate smoke 已驗證 | TASK-015：App Router + TypeScript，無 Tailwind；`/api/:path*` 同路徑 proxy 到 FastAPI :8000。TASK-016：文字/.md 輸入、voice/style/pacing/accent、inline tag insertion、生成後播放/下載已接 API contract。TASK-017：HistoryList 50 筆初載、Load more、completed audio 播放/下載、error row 無播放/下載且可刪除、synthesize 成功後 refresh |

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
   - 殘留風險：Gemini adapter、voices、短稿 synthesize 已於後續 TASK 完成；剩餘高風險為 TASK-007/008 切塊與長稿串接。
2. **TASK-002 review**
   - 狀態：REVIEW PASS；Critical/Major/Minor/Suggestion 皆無，未發現 out-of-scope diff。
   - 驗證：`python3 -m pytest tests/test_voices.py -v` 通過（7 passed）；`python3 -m compileall -q app tests/test_voices.py`、`git diff --check` 通過；live uvicorn `/api/voices` 回 `count=30 first=Zephyr last=Sulafat`。
   - 殘留風險：前端 dropdown 尚未整合；真實 Gemini TTS 合成屬後續 TASK，不在 TASK-002 範圍。
3. **TASK-003 review**
   - 狀態：REVIEW PASS；前一輪 Major（note 欄位可注入 section marker）已修正，最終 Critical/Major/Minor/Suggestion 皆無。
   - 驗證：`python3 -m pytest backend/tests/ -v` 通過（32 passed）；`python3 -m compileall -q backend/app/tts/prompt.py backend/tests/test_prompt.py` 通過；新增 voice/style/pacing/accent 換行與 `###` marker injection 測試。
   - 殘留風險：尚未接 Gemini SDK / 真實 TTS 合成；TASK-004 需將 voice 寫入 SDK config，並以 mock 驗證回應健全性與 retry/error mapping。
4. **TASK-004 review**
   - 狀態：REVIEW PASS；Critical/Major 無 blocker，Minor line-length 已於提交前修正。
   - 驗證：`python3 -m pytest backend/tests/ -v` 通過（49 passed）；`python3 -m compileall -q backend/app/tts/client.py backend/tests/test_client.py` 通過；backend `.venv` 可建立 `GenerateContentConfig` speech_config/voice config。
   - 殘留風險：`/api/synthesize` integration 已於 TASK-006 完成；真實 Gemini API 呼叫仍待手動驗證。
5. **TASK-005 review**
   - 狀態：REVIEW PASS；Critical/Major/Minor/Suggestion 無 blocker，未發現 out-of-scope diff。
   - 驗證：`python3 -m pytest backend/tests/test_pcm.py -v` 通過（25 passed）；`python3 -m pytest backend/tests/ -v` 通過（74 passed）；`python3 -m compileall -q backend/app/audio/pcm.py backend/tests/test_pcm.py`、`git diff --check`、行寬/trailing whitespace 檢查皆通過。
   - 殘留風險：短稿 `/api/synthesize` 整合已於 TASK-006 完成；多塊 raw PCM 串接與感知層人耳回歸待 TASK-008。
6. **TASK-006 review**
   - 狀態：REVIEW PASS；Critical/Major 無 blocker。
   - durable contract：M2 `POST /api/synthesize` 直接回 `audio/wav` bytes；M4 才切換 `{id, created_at, metadata, audio_url}` 與 storage/metadata 流程。
   - 驗證：`text`/`voice` whitespace-only 回 422；`voice` strip 後送 client；transcript text 保留原始內容；`TtsClientError` 依 `status_code` 回應；PCM/WAV conversion 問題回 502。
   - 證據：`backend/tests/test_synthesize.py` 16 passed；`backend/tests/` 90 passed；`compileall` 通過；`git diff --check` 通過。
   - 殘留風險：尚未做真實 Gemini API 呼叫、人耳播放檢查、storage/audio_url metadata；chunking 已於 TASK-007 完成，long synthesize 整合待 TASK-008。
7. **TASK-007 review**
   - 狀態：REVIEW PASS；Critical/Major/Minor/Suggestion 無 findings，acceptance criteria 已有 evidence。
   - durable contract：`backend/app/tts/chunker.py` 提供雙條件切塊；token budget 以完整 prompt 或 explicit overhead/custom counter + 1-token margin 計算，prompt overhead 超 budget 會 raise `ChunkingError`。
   - 驗證：`backend/tests/test_chunker.py` 45 passed；`backend/tests/` 135 passed；`compileall`、`git diff --check`、no-index whitespace、舊 tolerance 掃描通過。Regression：`"a" * 1690` 在 `max_tokens=500` 下不再產生 full prompt 501，chunks full prompt tokens = 500 / 78。
   - 殘留風險：尚未呼叫真實 Gemini `count_tokens`；TASK-008 需整合 chunker + Gemini `count_tokens`/long synthesize + PCM concat。
8. **TASK-008 review**
   - 狀態：REVIEW PASS；前一輪 P2（遠端 `count_tokens` 被 splitter per-candidate 呼叫）已修正，最終無可行 blocker。
   - durable contract：`POST /api/synthesize` 會先 chunk transcript，逐塊 build prompt + Gemini TTS，將 raw PCM blocks concat 後一次封裝 WAV；目前仍維持暫時 `audio/wav` response，M4/TASK-011 才切 metadata/audio_url。
   - token 策略：Gemini `count_tokens` 只用於固定 prompt overhead；chunk 內容用本地 estimate，避免長 no-space input 造成大量遠端 token-count 呼叫。
   - 驗證：`backend/tests/` 156 passed；`backend/tests/test_synthesize.py backend/tests/test_pcm.py` 62 passed；`compileall` 與 `git diff --check` 通過；Codex CLI review 第三輪無 findings。
   - 殘留風險：尚未真實 Gemini 長稿/人耳播放驗證；感知接縫仍留 M8 manual regression。
9. **TASK-009 review**
   - 狀態：REVIEW PASS；已修正單元測試誤用 production default `data/app.sqlite` 的隔離問題，最終無 blocker。
   - durable contract：`backend/app/storage/db.py` 建立 `syntheses` SQLite schema（含 `source` 預設 `text`，避免 M5 migration）與 create/list/get/delete；list 回 `items/total/limit/offset/has_more` 並以 `created_at DESC, rowid DESC` 穩定排序。
   - 驗證：`backend/tests/test_storage_db.py` 24 passed；`backend/tests/` 180 passed；`compileall` 與 `git diff --check` 通過；Codex CLI review 無 findings。
   - 殘留風險：`files.py` 安全路徑與 `synthesize` metadata/audio_url 整合仍待 TASK-010/011。
10. **TASK-010 review**
    - 狀態：REVIEW PASS；Critical/Major 無 blocker，Codex CLI review 未發現 correctness/security/maintainability 缺陷。
    - durable contract：`backend/app/storage/files.py` 只接受 `[A-Za-z0-9_-]` audio id，拒絕空值、null byte、絕對路徑與 `..` path component；音檔固定解析為 `DATA_DIR/audio/{id}.wav`，提供 save/resolve/delete。
    - 驗證：`backend/tests/test_storage_files.py` 28 passed；`backend/tests/` 208 passed；`compileall` 與 `git diff --check` 通過。
    - 殘留風險：`POST /api/synthesize` 仍維持 M2/M3 暫時 `audio/wav` response；TASK-011 需接 DB + file storage 並改回 metadata/audio_url contract。
11. **TASK-011 review**
    - 狀態：REVIEW PASS；Critical/Major 無 blocker，Codex CLI review 未發現 correctness issue。
    - durable contract：`POST /api/synthesize` 已取代 M2/M3 暫時 WAV response；成功時寫入 WAV 檔與 `completed` DB row，回 `{id, created_at, metadata, audio_url}`；TTS/chunk/PCM/save 失敗時盡量寫入 `error` row 並回同一 `id`。
    - 驗證：`backend/tests/test_synthesize.py backend/tests/test_storage_db.py` 66 passed；`backend/tests/` 223 passed；`compileall` 與 `git diff --check` 通過。
    - 殘留風險：`GET /api/audio/{id}` 仍待 TASK-013；真實 Gemini / 人耳播放回歸仍留 M8。
12. **TASK-012 review**
    - 狀態：REVIEW PASS；Critical/Major/Minor/Suggestion 無 findings，未發現 out-of-scope diff。
    - durable contract：`GET /api/history?limit=50&offset=0` 回 `items/total/limit/offset/has_more`，item 附 `audio_url`；`DELETE /api/history/{id}` 先確認 DB row，刪 `DATA_DIR/audio/{id}.wav` 後刪 DB row，檔案已不存在時仍可刪 row。
    - 驗證：`backend/tests/test_history.py` 12 passed；`backend/tests/` 235 passed；`compileall`、`git diff --check` 與 trailing whitespace 檢查通過。
    - 殘留風險：`GET /api/audio/{id}` Range/下載已由 TASK-013 完成；前端 history list/delete 使用已由 TASK-017 完成。
13. **TASK-013 review**
    - 狀態：REVIEW PASS；Critical/Major/Minor/Suggestion 無 findings，未發現 out-of-scope diff。
    - durable contract：`GET /api/audio/{id}` 先確認 DB row 與 `DATA_DIR/audio/{id}.wav` 存在；使用 Starlette `FileResponse` 支援 full response、Range 206、`Accept-Ranges`/`Content-Range`，`?download=1` 設 `Content-Disposition: attachment`。
    - 驗證：`backend/tests/test_audio_api.py` 9 passed；`backend/tests/` 244 passed；`compileall` 與 `git diff --check` 通過。
    - 殘留風險：M4 後端持久化/歷史已完成；真實 Gemini / 人耳播放回歸仍留 M8，markdown 正規化已於 TASK-014 完成。
14. **TASK-014 review**
    - 狀態：REVIEW PASS；Critical/Major 無 blocker，acceptance criteria 已有 evidence。
    - durable contract：`backend/app/ingest/markdown.py` 將 heading/list/code/link/paragraph 等 markdown 正規化為純文字；`POST /api/synthesize source='md'` 會先 normalize，再走既有 chunk/TTS/storage pipeline，DB/metadata `source` 寫入 `md`。
    - 驗證：`backend/tests/` 283 passed；targeted markdown/synthesize 78 passed；`compileall` 與 `git diff --check` 通過。
    - 殘留風險：特殊 Markdown/HTML 表格或巢狀結構的朗讀語意尚未以真實講稿人工回歸；前端 `.md` 上傳整合已於 TASK-016 完成，真實 Gemini / 人耳回歸仍留 M8。
15. **TASK-015 review**
    - 狀態：REVIEW PASS；Critical/Major/Minor 無 findings，acceptance criteria 已有 evidence。
    - durable contract：`frontend/` 已由 create-next-app 建立 App Router + TypeScript scaffold（無 Tailwind）；`frontend/next.config.ts` 將 `/api/:path*` 同路徑 proxy 到 `http://localhost:8000/api/:path*`；`frontend/package.json` 以 npm overrides 固定 `postcss@8.5.15` 並同步 lockfile；已移除 generator nested `frontend/AGENTS.md` / `frontend/CLAUDE.md` 避免 agent instruction drift。
    - 驗證：`npm ci --dry-run`、`npm run lint`、`npx tsc --noEmit`、`git diff --check` 通過；`npm ls postcss` 顯示 `postcss@8.5.15 overridden`，`npm audit --audit-level=low` 回 `found 0 vulnerabilities`；`curl http://localhost:3000/api/health` 經 proxy 回 200 `{"status":"ok"}`；Browser smoke 顯示頁面非空；ports 已清理。
    - 殘留風險：TASK-016 已完成主頁 UI、api-client、AudioPlayer；HistoryList 分頁/播放/下載/刪除已由 TASK-017 補完。
16. **TASK-016 review**
    - 狀態：REVIEW PASS；第二輪 Critical/Major/Minor/Suggestion 皆無，Codex app 仲裁 gate pass。
    - durable contract：`frontend/app/page.tsx`、`frontend/lib/api-client.ts`、`frontend/components/AudioPlayer.tsx` 已完成文字/.md 輸入、voice/style/pacing/accent、inline tag insertion、生成後線上播放與下載，維持 `/api/synthesize` metadata/audio_url 與 `/api/audio/{id}` contract。
    - 驗證：`cd frontend && npm run lint`、`npx tsc --noEmit`、`npm audit --audit-level=low`（0 vulnerabilities）、`npm ci --dry-run`、`git diff --check` 通過；Playwright fallback smoke 以 mock backend + Next dev 執行實際 click/type/upload/play/download，覆蓋 `title=txt2speech`、tag insertion 產生 `Hello [pause] world.`、text `source=text voice=Zephyr` 且 style/pacing/accent metadata 存在、`.md source=md voice=Puck`、`/api/audio/mock-task-016` 播放/下載與 WAV/attachment headers、desktop/mobile 無水平 overflow；臨時服務/artifacts 已清理，3000/8000 無 listener。
    - 殘留風險：in-app Browser target 當輪不可用，已由 MCP Playwright fallback 完成 app gate；HistoryList 已由 TASK-017 完成；真實 Gemini / 人耳 playback 回歸仍留 M8。
17. **TASK-017 review**
    - 狀態：REVIEW PASS；OpenCode develop、Codex app 仲裁驗證與兩輪 Codex code review 後，Critical/Major/Minor/Suggestion 皆無 blocker。
    - durable contract：`frontend/components/HistoryList.tsx` 新增 history 清單；`frontend/lib/api-client.ts` 新增 `HistoryItem`/`HistoryListResponse`/`fetchHistory`/`deleteHistoryItem`；`frontend/app/page.tsx` 掛載 HistoryList 並在 synthesize 成功後 refresh；`frontend/app/page.module.css` 新增 history styles。`status=error` row 不顯示播放/下載但可 delete。
    - 驗證：`git diff --check`、`npm run lint`、`npx tsc --noEmit`、`npm run build`、`npm audit --audit-level=low`、`npm ci --dry-run` 通過；Playwright mock backend + Next dev 覆蓋 50/65 history、Load more 65/65、completed audio wav 200、download attachment、error row、delete 後 UI/API 64/64、mobile 390 無水平 overflow。
    - 殘留風險：真實 Gemini / 人耳 playback、README/e2e 與環境檔仍留 TASK-018。

---

## 📈 進度追蹤

### 專案里程碑
- [x] **M1**: 後端骨架（TASK-001 health/config + TASK-002 voices pass）
- [x] **M2**: 單塊短稿合成（TASK-003/004/005/006 pass，暫回 WAV bytes）
- [x] **M3**: 切塊與串接（TASK-007/008 pass）
- [x] **M4**: 持久化與歷史（TASK-009 SQLite metadata、TASK-010 file storage helper、TASK-011 synthesize storage integration、TASK-012 history/delete、TASK-013 audio endpoint 全部完成）
- [x] **M5**: markdown 正規化（TASK-014 pass）
- [x] **M6**: 前端核心（TASK-015 scaffold/proxy + TASK-016 主頁 UI/api-client/AudioPlayer 已完成）
- [x] **M7**: 前端歷史（TASK-017 HistoryList 清單：分頁 + 播放/下載/刪除已完成）
- [ ] **M8**: 整合與文件（下一步 TASK-018 e2e 串接 + README + 環境檔）

### 最近完成

#### 本週
- ✅ TASK-001：後端 FastAPI 骨架、pydantic-settings config、`/api/health`、`.env.example`、package init 完成；`.gitignore` 已改為只忽略 `/data/audio/`，避免 `backend/app/audio` 被忽略。
- ✅ TASK-002：`GET /api/voices` 回 30 種 Gemini TTS 預建 voice（`name` + `description`），可作前端下拉資料源。
- ✅ TASK-003：`tts/prompt.py` 組固定 preamble + `### DIRECTOR'S NOTES` + `### TRANSCRIPT`；保留 transcript inline tags，對 voice/style/pacing/accent 做單行 sanitizer。
- ✅ TASK-004：`tts/client.py` 封裝 Gemini TTS 單塊 adapter、audio response 健全性檢查、retry/backoff、502/504 mapping 與 `count_tokens`。
- ✅ TASK-005：`audio/pcm.py` 提供 raw PCM 24kHz mono 16-bit 預設、frame alignment 檢查與 stdlib `wave` WAV 封裝。
- ✅ TASK-006：`POST /api/synthesize` 完成短稿單塊合成路由，整合 prompt builder、Gemini TTS adapter 與 PCM→WAV helper；M2 暫回 `audio/wav` bytes。
- ✅ TASK-007：`tts/chunker.py` 完成雙條件切塊器，覆蓋完整 prompt token accounting、段落/句子 fallback、CJK/no-space/single long word fallback。
- ✅ TASK-008：`POST /api/synthesize` 完成長稿逐塊合成與 raw PCM 多塊串接，維持暫時 `audio/wav` response；`count_tokens` 僅算 prompt overhead。
- ✅ TASK-009：`storage/db.py` 完成 SQLite metadata schema + create/list/get/delete；分頁回 `items/total/limit/offset/has_more`，`source` 欄位已在 M4 建好。
- ✅ TASK-010：`storage/files.py` 完成 `DATA_DIR/audio/{id}.wav` 安全路徑解析、寫檔與刪檔；拒絕 `../`、絕對路徑、null byte 與非法 id。
- ✅ TASK-011：`POST /api/synthesize` 接入 DB + file storage，成功回 metadata/audio_url 並寫 `completed`，失敗回同一 id 並盡量寫 `error`。
- ✅ TASK-012：`GET /api/history` 完成 limit/offset 分頁，`DELETE /api/history/{id}` 完成音檔 + metadata 刪除；檔案已不存在時仍可刪除 DB row。
- ✅ TASK-013：`GET /api/audio/{id}` 完成 WAV serve、Range 206 與 `?download=1` attachment 下載；未知 id / missing file 回 404。
- ✅ TASK-014：完成 markdown→plain text normalizer；`POST /api/synthesize source='md'` 會 normalize 後合成並將 DB/metadata `source` 寫為 `md`。
- ✅ TASK-015：完成 `frontend/` create-next-app scaffold（App Router + TypeScript，無 Tailwind）與 `frontend/next.config.ts` rewrites；`/api/:path*` 經 Next proxy 到 FastAPI :8000，lint/tsc/proxy smoke 與 Browser smoke 通過。
- ✅ TASK-016：完成主頁 UI、api-client 與 AudioPlayer；文字與 `.md` 上傳可送 synthesize contract，生成結果可線上播放與下載；第二輪 review/app gate 通過。
- ✅ TASK-017：完成 HistoryList 清單、分頁、播放、下載、刪除與 synthesize 成功後 refresh；error row 不顯示播放/下載但可刪除；最終 review/app gate 通過。

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
| 2026-06-15 | TASK-006 維持 M2 暫時 contract：`POST /api/synthesize` 回 `audio/wav` bytes，M4 才回 `{id, created_at, metadata, audio_url}` | 讓短稿合成先驗 prompt/client/PCM→WAV integration，避免提前拉入 storage/metadata 複雜度 | plan M2/M4 |
| 2026-06-15 | TASK-008 長稿切塊時不把遠端 `count_tokens` 傳入 splitter；只用來算固定 prompt overhead | 避免 no-space/char fallback 對 Gemini 發出大量 token-count API 呼叫；以本地估算維持可預期成本/延遲 | code review |
| 2026-06-15 | TASK-011 將 `POST /api/synthesize` 切回 metadata/audio_url contract，id 同時關聯 DB row 與 `DATA_DIR/audio/{id}.wav` | 前端播放/歷史需要穩定 id 與音檔 URL；避免前端依賴 M2/M3 暫時 WAV response | plan M4 |
| 2026-06-15 | TASK-015 前端 scaffold 使用 App Router + TypeScript、無 Tailwind，並以 Next rewrites 做 `/api/*` 同路徑 proxy | 對齊 active plan、避免 CORS 與前端持有後端 origin；移除 nested agent docs 避免 instruction drift | plan M6 |

### 待確認事項
- [x] plan 已 approved；4 項建議決策（WAV / proxy / Director's Notes / 雙條件切塊）皆採用
- [ ] 下一步銜接 TASK-018 e2e 串接 + README + 環境檔；真實 Gemini / 人耳 playback 留此 task 驗證。

### 討論備註
[最近討論的重要內容...]

---

## 📝 Code Review 記錄

### 最近審查

| 日期 | 範圍 | 結果 | 說明 |
|------|------|------|------|
| 2026-06-15 | TASK-001 後端骨架 + config | 通過 | REVIEW PASS；Critical/Major 無 blocker；acceptance criteria 已有 evidence |
| 2026-06-15 | TASK-002 `GET /api/voices` | 通過 | REVIEW PASS；Critical/Major/Minor/Suggestion 無；30 筆 Gemini TTS voice 與官方清單相符 |
| 2026-06-15 | TASK-003 `tts/prompt.py` prompt 組裝器 | 通過 | REVIEW PASS；已修正 note/voice section marker injection；32 backend tests 通過 |
| 2026-06-15 | TASK-004 `tts/client.py` Gemini adapter | 通過 | REVIEW PASS；mock 覆蓋 normal/invalid/timeout/count_tokens；49 backend tests 通過 |
| 2026-06-15 | TASK-005 `audio/pcm.py` PCM→WAV | 通過 | REVIEW PASS；frame alignment/WAV header/frame count/roundtrip/custom params 已覆蓋；74 backend tests 通過 |
| 2026-06-15 | TASK-006 `POST /api/synthesize` 短稿合成 | 通過 | REVIEW PASS；Critical/Major 無 blocker；16 synthesize tests、90 backend tests、compileall、diff check 通過 |
| 2026-06-15 | TASK-007 `tts/chunker.py` 雙條件切塊 | 通過 | REVIEW PASS；Critical/Major/Minor/Suggestion 無 findings；45 chunker tests、135 backend tests、compileall、diff/whitespace checks 通過 |
| 2026-06-15 | TASK-008 PCM 多塊串接 + 長稿 synthesize | 通過 | REVIEW PASS；已修正 per-candidate 遠端 count_tokens 風險；156 backend tests、compileall、diff check 通過 |
| 2026-06-15 | TASK-009 `storage/db.py` SQLite schema + CRUD | 通過 | REVIEW PASS；已修正 singleton 測試隔離；24 storage DB tests、180 backend tests、compileall、diff check 通過 |
| 2026-06-15 | TASK-010 `storage/files.py` 音檔存取 + 安全路徑 | 通過 | REVIEW PASS；28 storage files tests、208 backend tests、compileall、diff check 通過 |
| 2026-06-15 | TASK-011 synthesize 接 storage | 通過 | REVIEW PASS；synthesize+storage DB targeted 66 passed、backend 223 passed、compileall、diff check 通過 |
| 2026-06-15 | TASK-012 history 分頁 + delete | 通過 | REVIEW PASS；history 12 passed、backend 235 passed、compileall、diff check 通過 |
| 2026-06-15 | TASK-013 audio Range + download | 通過 | REVIEW PASS；audio API 9 passed、backend 244 passed、compileall、diff check 通過 |
| 2026-06-15 | TASK-014 markdown normalizer + synthesize source | 通過 | REVIEW PASS；backend 283 passed、targeted 78 passed、compileall、diff check 通過 |
| 2026-06-15 | TASK-015 frontend scaffold + rewrites proxy | 通過 | REVIEW PASS；Critical/Major/Minor 無 findings；lint、tsc、diff check、proxy curl、Browser smoke 通過 |
| 2026-06-15 | TASK-016 主頁 UI + api-client + AudioPlayer | 通過 | REVIEW PASS；第二輪 Critical/Major/Minor/Suggestion 無 findings；lint、tsc、audit、npm ci dry-run、diff check、Playwright fallback app gate 通過 |
| 2026-06-15 | TASK-017 HistoryList 清單 | 通過 | REVIEW PASS；Critical/Major/Minor/Suggestion 無 blocker；lint、tsc、build、audit、npm ci dry-run、diff check、Playwright app gate 通過 |

### 審查統計
- 總審查次數：17
- 通過審查：17
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
