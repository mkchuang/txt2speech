# txt2speech

輔助演講練習的 Web 工具。貼上或上傳中英交雜演講稿，透過 **Google Gemini TTS** 生成示範朗讀音檔，協助練習口條、節奏與英文發音。

## 系統需求

- Python 3.11+
- Node.js 20.9+
- Gemini API key（從 [Google AI Studio](https://aistudio.google.com/apikey) 取得）

## 快速啟動

### 1. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，填入 GEMINI_API_KEY
```

### 2. 啟動後端（FastAPI）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" google-genai pydantic-settings markdown beautifulsoup4 pytest httpx
set -a
source ../.env
set +a
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

後端健康檢查：http://localhost:8000/api/health（回 `{"status":"ok"}` 即啟動成功）

### 3. 啟動前端（Next.js）

```bash
cd frontend
npm ci
npm run dev
```

前端：http://localhost:3000（`/api/*` 會自動 proxy 到後端 :8000）

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| GET | `/api/health` | 健康檢查 |
| GET | `/api/voices` | 30 種預建 voice 清單 |
| POST | `/api/synthesize` | 合成音檔（`source=text` 純文字 / `source=md` 上傳 .md） |
| GET | `/api/history?limit=50&offset=0` | 歷史記錄分頁 |
| DELETE | `/api/history/{id}` | 刪除歷史記錄與音檔 |
| GET | `/api/audio/{id}` | 播放音檔（支援 Range 206） |
| GET | `/api/audio/{id}?download=1` | 下載音檔 |

## 技術棧

| 層 | 技術 |
|----|------|
| 前端 | Next.js (App Router + TypeScript) |
| 後端 | Python FastAPI |
| TTS | Gemini 3.1 Flash TTS Preview |
| 儲存 | SQLite (metadata) + 檔案系統 (WAV 音檔) |

## 測試

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

## 端到端檢查

後端與前端都啟動後，在瀏覽器開啟 http://localhost:3000：

1. 貼上一段中英交雜演講稿。
2. 選擇 voice、style、pacing、accent 後按下合成。
3. 確認產生結果可播放、可下載，且出現在 History。
4. 對長稿重複測試，確認多段合成後仍可播放。

英文發音、語速與長稿接縫屬於人耳感知驗證；自動測試只驗證 API、切塊、WAV frame alignment、markdown 正規化、metadata/audio storage 與 mock client 行為。
