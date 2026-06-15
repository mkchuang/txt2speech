# 技術棧定義

> **用途**：定義專案使用的技術棧，供 AI agent 理解技術約束
> **填寫時機**：`adf.design` 初始化專案時
> **引用者**：所有 agent（透過 CLAUDE.md 引用）
> **最後更新**：2026-06-15

---

## 程式語言

| 語言 | 版本 | 用途 |
|------|------|------|
| TypeScript | Next.js 內建 | 前端（Next.js） |
| Python | 3.11+ | 後端 API 與 Gemini TTS 呼叫 |

## 框架與函式庫

| 名稱 | 版本 | 用途 |
|------|------|------|
| Next.js | latest（App Router） | 前端 UI（簡單：輸入、參數、播放器） |
| FastAPI | latest | 後端 REST API（`/synthesize`） |
| Uvicorn | latest | ASGI server |
| google-genai | latest | Gemini SDK（呼叫 TTS 模型） |
| pydantic-settings | latest | 設定與機密管理（`GEMINI_API_KEY`） |
| pydub / ffmpeg | latest | PCM 24kHz → WAV/MP3、片段串接 |
| SQLite | 內建（Python `sqlite3`） | 歷史 metadata 儲存（音檔存檔案系統） |

## 建置工具

| 工具 | 版本 | 用途 |
|------|------|------|
| pip / venv（或 uv） | - | Python 依賴管理 |
| npm / pnpm | - | 前端依賴管理 |

## AI 模型

| 模型 | 用途 | 關鍵限制 |
|------|------|---------|
| `gemini-3.1-flash-tts-preview` | 文字 → 語音示範音 | 輸入上限 8,192 tokens；輸出音訊上限 16,384 tokens；輸出 PCM 24kHz mono 16-bit；支援中英混語、expressive audio tags、自然語言風格控制、30 種預建 voice、最多 2 語者；**不支援** structured output / function calling / caching |

> 不使用獨立教練 LLM；發音與重點表現由 TTS prompt + audio tags 控制。

## 目標平台
- **執行環境**：macOS 本機開發；前端 `next dev`、後端 `uvicorn` 各自啟動
- **編譯目標**：不適用（Web 應用）

## 外部依賴與服務

| 服務/API | 用途 | 備註 |
|----------|------|------|
| Google Gemini API | TTS 合成 | 需 `GEMINI_API_KEY`，僅後端持有 |

## 技術限制
- TTS 單次輸入 ≤ 8,192 tokens → 長講稿須切塊。
- 語速控制無直接參數，靠 prompt / audio tags 表達，需實測。
- `GEMINI_API_KEY` 不得進入前端或版控。
- preview 模型，API 可能變動，需以 adapter 隔離。

---
*此檔案為靜態技術棧定義，變更技術棧時請同步更新*
