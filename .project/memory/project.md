# 專案全貌 - Project Overview

> 此文件描述專案的靜態資訊，較少變動
> 最後更新：2026-06-15（由 /adf.design 初始化）

## 🎯 專案簡介

### 專案目標
**txt2speech** 是一個輔助「演講練習」的 Web 工具。使用者貼上/上傳演講稿（中英交雜），透過 **Google Gemini TTS** 生成示範朗讀音檔，協助練習口條、節奏與**英文發音**。發音與重點表現完全依賴 Gemini TTS 內建多語能力與 prompt / audio tags，**不引入額外教練 LLM**。

### 核心功能
- 功能 1：講稿輸入——**貼上文字 或 上傳 `.md` 檔**（後端將 markdown 正規化為純文字後送 TTS）
- 功能 2：前端參數控制 TTS 輸出——音色（30 種預建 voice）、語速、風格（透過 prompt + audio tags）
- 功能 3：呼叫 Gemini TTS 生成示範音檔（含長稿切塊），前端線上播放與下載
- 功能 4：每次請求**重新產生**，不做去重快取/比對
- 功能 5：**歷史紀錄**——持久化每次結果（音檔 + metadata），提供清單查看、線上播放、下載

### 目標用戶
需要練習中英交雜演講、特別在意英文發音與表達的個人使用者（本機單人使用為主）。

### 專案範圍
- **包含**：文字輸入、TTS 參數控制、Gemini TTS 合成、音檔播放/下載、長稿切塊
- **不包含**：
  - ❌ 獨立教練 LLM 分析（重點/發音指導交由 TTS prompt 與文檔能力）
  - ❌ 使用者錄音上傳 → ASR 比對與發音評分
  - ❌ 全中文演講教學、即時互動式語音對話
  - ❌ 多租戶帳號/計費（本機單人、無認證）
  - ❌ 去重快取/比對（相同輸入仍重新產生；但結果會存入歷史）

## 🏗️ 系統架構

### 整體架構
```
┌─────────────────┐  POST /api/synthesize ┌────────────────────────────────────┐
│  Frontend        │ ───(text+params)───▶ │       Python FastAPI Backend        │
│  Next.js (TS)    │ ◀──(audio meta)───── │  （/api/* 經 next rewrite 同路徑）    │
│  輸入/參數       │                       │ ┌────────┐  ┌──────────────────┐   │
│  播放器/歷史清單 │  GET /api/history     │ │ api    │─▶│ tts              │   │
│                  │ ◀──(list)─────────── │ │ 驗證   │  │ prompt組裝+切塊   │───┼─▶ Gemini TTS
│                  │  GET /api/audio/{id}  │ │ md正規 │  │ (8192-token上限)  │   │  (gemini-3.1-
│                  │ ◀──(play/download)─── │ └───┬────┘  └────────┬─────────┘   │   flash-tts-preview)
└─────────────────┘                        │     │      ┌─────────▼─────────┐  │  ◀── PCM 24kHz
                                           │     │      │ audio: PCM→WAV     │  │
                                           │     ▼      └─────────┬─────────┘  │
                                           │ ┌──────────────────────▼────────┐ │
                                           │ │ storage: SQLite(metadata)      │ │
                                           │ │        + 檔案系統(音檔)         │ │
                                           │ └────────────────────────────────┘ │
                                           └────────────────────────────────────┘
            本機各自啟動：next dev :3000 / uvicorn :8000
```

### 核心模組

| 模組 | 功能 | 技術 | 狀態 |
|------|------|------|------|
| frontend | 講稿輸入（貼上 / 上傳 .md）、參數選項（voice/語速/風格）、播放器、歷史清單、下載 | Next.js + TS | ⚫ 未開始 |
| api | FastAPI app、CORS、`/api/health`、`/api/voices` 與 M2 短稿 `POST /api/synthesize` 已落地；history/audio、md→純文字正規化待續 | FastAPI | 🟡 部分完成（TASK-001/002/006） |
| tts | prompt 組裝、Gemini adapter 與雙條件切塊器已落地（完整 prompt token accounting；段落/句子/char fallback；lazy google-genai import；audio inline_data 健全性檢查+retry；502/504 mapping；count_tokens）；long synthesize 整合待 TASK-008 | google-genai | 🟡 部分完成（TASK-003/004/007） |
| audio | raw PCM 24kHz mono 16-bit → WAV 封裝與 frame alignment 已落地；多塊串接/長稿整合待續 | stdlib `wave` | 🟡 部分完成（TASK-005） |
| storage | 持久化音檔（檔案系統）+ metadata（SQLite）、歷史分頁查詢 | SQLite + fs | ⚫ 未開始 |
| config | `GEMINI_API_KEY`、`DATA_DIR`、`CORS_ORIGINS` 設定管理 | pydantic-settings | 🟢 已完成（TASK-001） |

### 設計模式
- **Adapter**：以 `tts` 模組封裝 Gemini，隔離 preview 模型變動。
- **持久化但不去重**：每次請求重新產生並寫入歷史；不做相同輸入的去重快取。
- **Metadata/檔案分離**：SQLite 存 metadata，音檔存檔案系統，以 id 關聯。

### 通訊機制
- 前端 → 後端：HTTP，前端一律呼叫 `/api/*`，由 **Next.js `rewrites` 同路徑 proxy** 到 FastAPI :8000（免 CORS）。
- 後端 → Gemini：`google-genai` SDK（HTTPS）。

### API 端點（草案）
- `POST /api/synthesize`：M2 暫時 contract 直接回 `audio/wav` bytes；M4 將改為 `{id, created_at, metadata, audio_url}` 並接 storage/metadata 流程。
- `GET /api/history?limit=50&offset=0`：歷史清單分頁，回 `items/total/limit/offset/has_more`。
- `GET /api/audio/{id}`：serve 音檔，支援線上播放（Range）與下載（`?download=1`）。
- `GET /api/voices`：回 30 種預建 voice 清單（前端下拉選單）。
- `DELETE /api/history/{id}`：刪除單筆歷史（檔案 + metadata）。

## 🔧 技術上下文

### 技術棧
詳見 `.project/context/tech-stack.md`。摘要：Next.js(TS) 前端 + Python FastAPI 後端 + google-genai SDK + Gemini 3.1 Flash TTS Preview；本機各自啟動（next dev / uvicorn）。

### 開發環境
- **作業系統**：macOS（darwin）
- **版本控制**：Git
- **執行情境**：本機開發為主；前端 `next dev`、後端 `uvicorn` 各自啟動

## 📊 品質指標
- 單次合成端到端延遲可接受（短稿 < 數秒；長稿因切塊累加）
- 長稿正確切塊且片段串接無明顯接縫
- API 金鑰僅存在後端，不外洩至前端

## 🔐 安全性考量
- `GEMINI_API_KEY` 僅後端持有，前端不接觸；以 `.env` 注入、不入版控。
- 後端為唯一對外呼叫 Gemini 的出口，前端不直接持金鑰。

## ⚠️ 主要風險與未決問題
- **TTS 輸入 8192-token 上限**：TASK-007 已完成雙條件切塊器；長稿仍需於 TASK-008 整合真實 Gemini `count_tokens`、逐塊合成與 PCM 串接接縫處理（最高風險）。
- **語速控制方式**（已降為低風險）：經官方文件確認可用 Director's Notes `Pacing:` + inline `[very slow/fast]` 控制，寫在 prompt 內；細部以實測微調。
- **SynthID 浮水印**：Gemini TTS 所有輸出皆內嵌隱形 AI 浮水印（產品事實，無需處理，使用者知悉即可）。
- **Preview 模型變動**：`gemini-3.1-flash-tts-preview` 為 preview，API 可能變動，以 adapter 隔離。
- **前後端協調**：CORS / proxy 需設定妥當（前端連後端 :8000）。
- **成本與速率限制**：不做快取，每次重新產生會持續消耗音訊 tokens（已知取捨）。

## 🗺️ 範圍（單一 Phase）
單一交付，不分階段：
- 輸入：貼上文字 或 上傳 `.md`（後端正規化為純文字）
- 參數：voice / 語速 / 風格（prompt + audio tags）
- 合成：Gemini TTS（含 8192-token 切塊與片段串接），每次重新產生
- 輸出：前端線上播放 + 下載
- 歷史：持久化每次結果，提供清單查看 / 線上播放 / 下載

**驗收**：貼上或上傳一段中英交雜 `.md`／文字，選定 voice 與參數後取得可播放並可下載的示範音檔；該筆結果出現在歷史清單，可重新播放與下載。

**範圍外**：去重快取/比對、其他檔案格式（docx/pdf）、教練 LLM、使用者錄音 ASR 評分。

---
*此文件為專案靜態資訊，由 `/adf.design` 生成*
*更新頻率：低（專案結構變更時）*
