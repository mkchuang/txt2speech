# ADR-001: 採用單一 Gemini TTS + prompt 驅動，不引入教練 LLM

> **狀態**: accepted（待 plan 批准後生效）
> **日期**: 2026-06-15
> **關聯**: `plan-2026-06-15-gemini-tts-speech-practice.md`、`.project/memory/project.md`

## 背景

txt2speech 目標是輔助演講練習：上傳中英交雜講稿，產生示範朗讀以練習口條與英文發音。早期構想包含一個獨立「教練 LLM」分析講稿、產出重點與發音指導（結構化文字），再由 TTS 生成音檔。使用者最終決定**不需要教練模型**：重點由講稿本身與 TTS 的表現力控制即可。

關鍵技術事實（官方文件）：`gemini-3.1-flash-tts-preview` 支援 expressive audio tags 與自然語言風格控制、中英混語、30 種預建 voice，但**不支援 structured output / function calling**。

## 方案比較

| 方案 | 說明 | 優點 | 缺點 |
|---|---|---|---|
| A. TTS-only + prompt 驅動（採用） | 只用 TTS 模型，靠 voice/speed/style prompt + audio tags 控制表現 | 單一模型、單次呼叫鏈、低成本/低延遲、實作簡單 | 表現力受 prompt 表達力限制；語速無直接參數 |
| B. 教練 LLM + TTS 兩段式 | 文字模型先產結構化指導，再 TTS 合成 | 可輸出顯式重點/IPA 指導 | 兩段呼叫成本/延遲翻倍；TTS 模型本就不支援 structured output，需第二個模型；複雜度高 |

## 決策

採用**方案 A：TTS-only、prompt 驅動**。不在系統內放置任何教練/分析 LLM。所有「重點、語氣、語速、發音風格」皆透過 `tts/prompt.py` 組裝的自然語言 prompt 與 audio tags、以及前端可選的 voice/speed/style 參數表達。

## 理由

- 符合使用者明確需求（不要教練模型）。
- TTS 模型不支援 structured output，教練能力本須另一模型，與「簡單」目標相悖。
- 單次呼叫鏈大幅降低成本、延遲與失敗面。

## 控制機制（2026-06-15 補充，官方文件 + Context7 確認）

「prompt 驅動」的具體手段已確認，皆寫在 `generate_content` 的 `contents` 文字內，config 僅選 voice：

- **Inline audio tags**：方括號，如 `[whispers]`、`[laughs]`、`[excited]`、`[very slow]`、`[very fast]`。官方明示**無窮舉清單、鼓勵實驗**。
- **Director's Notes**：結構化區塊 `### DIRECTOR'S NOTES` + `Style:` / `Pacing:` / `Accent:`，三軸獨立控制。
- **語速**：由 `Pacing:` 與 inline `[very slow/fast]` 控制 → 先前「語速無直接參數」風險**已解除**。
- **重點強調**：以 inline tag 包詞或 transcript 母音拉長（`Beauuutiful`）達成；無專屬 emphasis markup。

設計含意：因標籤非窮舉，前端應提供**有限預設選項 + 自由 Director's Notes 文字框**，不硬編死標籤表；`tts/prompt.py` 負責把選項組成上述 prompt 結構。

## 影響

- 系統只有一個 AI 依賴（Gemini TTS），`tts/` 模組即唯一 AI 邊界，易以 adapter 隔離 preview 變動。
- 語速/語氣/口音/重點強調皆有文檔化控制手段，**TTS-only 架構足以滿足需求**，無教練 LLM 之必要。
- 殘留風險集中在「8192-token 切塊 + PCM 串接」與 preview API 變動，與本決策無關。
- 若日後確需顯式發音指導文字（如逐字 IPA 報告），屬新需求，應回到 `design` 擴充 baseline，而非在本架構內偷加模型。
