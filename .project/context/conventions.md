# 編碼規範

> **用途**：定義專案的編碼風格和慣例，供 AI agent 生成符合規範的代碼
> **填寫時機**：`adf.design` 初始化專案時
> **引用者**：developer、code-reviewer agent

---

## 命名規範

| 對象 | 風格 | 範例 |
|------|------|------|
| 檔案名 | [snake_case/kebab-case/PascalCase] | [example_file.py] |
| 函數/方法 | [snake_case/camelCase] | [get_user_name] |
| 類別/結構 | [PascalCase] | [UserManager] |
| 常數 | [UPPER_SNAKE_CASE] | [MAX_RETRY_COUNT] |
| 變數 | [snake_case/camelCase] | [user_count] |

## 目錄結構

```
[描述專案的目錄結構慣例]
src/
├── [模組分類方式]
├── ...
```

## 代碼風格

- **縮排**：[空格數/Tab]
- **行寬上限**：[字元數]
- **括號風格**：[K&R/Allman/...]
- **引號**：[單引號/雙引號]

## 註解規範

- **函數註解**：[JSDoc/Doxygen/docstring/...]
- **行內註解**：[何時加、何時不加]
- **TODO 格式**：`// TODO(username): 說明`

## 錯誤處理

- [慣用的錯誤處理模式，例如「使用 Result<T, E> 而非 panic」]
- [日誌等級使用規則]

## 測試規範

- **測試框架**：[框架名稱]
- **測試檔案位置**：[與源碼同目錄/__tests__/tests/]
- **命名規則**：[test_功能_情境_預期結果]
- **覆蓋率要求**：[百分比，如適用]

## 版本控制

- **分支策略**：[GitFlow/Trunk-based/...]
- **Commit 訊息**：[Conventional Commits/自訂格式]

---
*此檔案為靜態編碼規範，團隊共識變更時請同步更新*
