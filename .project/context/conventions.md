# 編碼規範

> **用途**：定義專案的編碼風格和慣例，供 AI agent 生成符合規範的代碼
> **填寫時機**：`adf.design` 初始化專案時
> **引用者**：developer、code-reviewer agent

---

## 命名規範

| 對象 | 風格 | 範例 |
|------|------|------|
| Python 檔案名 | snake_case | `tts_client.py` |
| Python 函數/方法 | snake_case | `synthesize_speech` |
| Python 類別 | PascalCase | `TtsClient` |
| 常數 | UPPER_SNAKE_CASE | `MAX_INPUT_TOKENS` |
| TS 檔案/元件 | 元件 PascalCase、其餘 kebab-case | `HistoryList.tsx`、`api-client.ts` |
| TS 函數/變數 | camelCase | `fetchHistory` |
| TS 類別/元件 | PascalCase | `AudioPlayer` |
| API 路徑 | kebab-case、複數資源 | `/api/history`、`/api/audio/{id}` |

## 目錄結構

```
txt2speech/
├── backend/                # Python FastAPI
│   ├── app/
│   │   ├── main.py         # FastAPI app + 路由註冊
│   │   ├── config.py       # pydantic-settings（GEMINI_API_KEY 等）
│   │   ├── api/            # 路由（synthesize / history / audio / voices）
│   │   ├── tts/            # Gemini adapter、prompt 組裝、切塊
│   │   ├── audio/          # PCM→WAV、串接
│   │   ├── storage/        # SQLite + 檔案系統
│   │   └── ingest/         # markdown→純文字
│   ├── tests/
│   └── pyproject.toml
├── frontend/               # Next.js (App Router, TS)
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
└── data/                   # 執行期音檔 + SQLite（.gitignore）
```

## 代碼風格

- **Python**：PEP 8、4 空格縮排、type hints 全面、docstring；錯誤回傳明確、及時釋放資源
- **TypeScript**：2 空格縮排、優先 `const`、單引號、嚴格模式
- **行寬上限**：Python 100、TS 100

## 註解規範

- **Python**：函數 docstring（用途、參數、回傳、例外）
- **TS**：複雜邏輯加註；公開函式 JSDoc
- **TODO 格式**：`# TODO(mkchuang): 說明` / `// TODO(mkchuang): 說明`

## 錯誤處理

- 後端：所有外部呼叫（Gemini、檔案、DB）包 try/except，回傳明確 HTTP 狀態與訊息；不吞例外
- Gemini 失敗：記錄並回 502/504，歷史記 `status=error`
- 日誌：`logging`，外部呼叫與失敗路徑至少 INFO/ERROR

## 測試規範

- **後端**：pytest；切塊邏輯、PCM 串接、md 正規化以單元測試覆蓋；Gemini 呼叫以 mock 隔離
- **測試檔案位置**：`backend/tests/`
- **命名規則**：`test_<模組>_<情境>_<預期>`

## 版本控制

- **分支策略**：`feature/...`、`bugfix/...`、`hotfix/...`
- **Commit 訊息**：`類型(範圍): 描述`（feat/fix/docs/refactor/test/chore/perf），中文為主
- **AI footer**：`Co-authored-by: <Agent> (<model>)`

---
*此檔案為靜態編碼規範，團隊共識變更時請同步更新*
