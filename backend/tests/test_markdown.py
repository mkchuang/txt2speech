from app.ingest.markdown import normalize_markdown


class TestNormalizeMarkdown:
    def test_heading_stripped(self) -> None:
        result = normalize_markdown("# Hello World")
        assert result == "Hello World"

    def test_heading_level2_stripped(self) -> None:
        result = normalize_markdown("## Section Title")
        assert result == "Section Title"

    def test_bold_stripped(self) -> None:
        result = normalize_markdown("**bold** text")
        assert result == "bold text"

    def test_italic_stripped(self) -> None:
        result = normalize_markdown("*italic* and _also italic_")
        assert result == "italic and also italic"

    def test_bold_italic_combined(self) -> None:
        result = normalize_markdown("***bold italic*** normal")
        assert result == "bold italic normal"

    def test_code_block_preserved_without_fences(self) -> None:
        result = normalize_markdown("```python\nprint('hi')\n```")
        assert result == "print('hi')"

    def test_indented_code_block_preserved(self) -> None:
        result = normalize_markdown("Text before\n\n    indented code\n\nText after")
        assert "indented code" in result
        assert "Text before" in result
        assert "Text after" in result

    def test_inline_code_preserved_without_backticks(self) -> None:
        result = normalize_markdown("Use `code` here")
        assert result == "Use code here"

    def test_link_text_preserved_url_removed(self) -> None:
        result = normalize_markdown("[click here](https://example.com)")
        assert "click here" in result
        assert "https" not in result

    def test_image_removed(self) -> None:
        result = normalize_markdown("![alt text](image.png)")
        assert result == ""

    def test_paragraphs_separated_by_double_newline(self) -> None:
        result = normalize_markdown("First paragraph.\n\nSecond paragraph.")
        lines = result.split("\n\n")
        assert len(lines) >= 2
        assert "First paragraph" in lines[0]
        assert "Second paragraph" in lines[1]

    def test_unordered_list_strips_markers(self) -> None:
        result = normalize_markdown("- Item 1\n- Item 2\n- Item 3")
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
        assert "-" not in result

    def test_ordered_list_strips_numbers(self) -> None:
        result = normalize_markdown("1. First\n2. Second")
        assert "First" in result
        assert "Second" in result
        assert "1." not in result

    def test_blockquote_strips_marker(self) -> None:
        result = normalize_markdown("> quoted text")
        assert result == "quoted text"

    def test_mixed_chinese_english(self) -> None:
        result = normalize_markdown("**Hello** 世界\n\n*Goodbye* 朋友")
        assert "Hello 世界" in result
        assert "Goodbye 朋友" in result

    def test_complex_mixed_content(self) -> None:
        text = """# 演講標題

## 開場

各位來賓大家好，今天我想談談 **AI 的未來**。

- 第一個重點：*技術演進*
- 第二個重點：倫理考量

```python
print("this should be removed")
```

更多資訊請參考 [官方文件](https://example.com)。

謝謝大家。
"""
        result = normalize_markdown(text)
        assert "演講標題" in result
        assert "開場" in result
        assert "AI 的未來" in result
        assert "技術演進" in result
        assert "倫理考量" in result
        assert 'print("this should be removed")' in result
        assert "```" not in result
        assert "https" not in result
        assert "官方文件" in result
        assert "謝謝大家" in result

    def test_empty_string(self) -> None:
        assert normalize_markdown("") == ""

    def test_whitespace_only(self) -> None:
        assert normalize_markdown("   \n\n   \t  ") == ""

    def test_plain_text_unchanged(self) -> None:
        text = "This is just plain text with no markdown."
        result = normalize_markdown(text)
        assert result == text

    def test_single_paragraph_single_line_output(self) -> None:
        result = normalize_markdown("Hello world.")
        assert result == "Hello world."

    def test_multiline_paragraph_joined(self) -> None:
        result = normalize_markdown(
            "Line one of same paragraph.\nLine two of same paragraph."
        )
        assert "Line one" in result
        assert "Line two" in result

    def test_strikethrough_preserved_without_extension(self) -> None:
        result = normalize_markdown("~~deleted~~ kept")
        assert result == "deleted kept"

    def test_horizontal_rule_ignored(self) -> None:
        result = normalize_markdown("Above\n\n---\n\nBelow")
        assert "Above" in result
        assert "Below" in result
        assert "---" not in result

    def test_nested_formatting(self) -> None:
        result = normalize_markdown("**bold _and italic_ text**")
        assert result == "bold and italic text"

    def test_table_gets_text_content(self) -> None:
        text = """| Col A | Col B |
|-------|-------|
| A1    | B1    |
| A2    | B2    |"""
        result = normalize_markdown(text)
        assert "A1" in result
        assert "B1" in result
        assert "A2" in result
        assert "B2" in result

    def test_long_markdown_preserves_content(self) -> None:
        paragraphs = [f"Paragraph {i} with some **bold** content." for i in range(20)]
        text = "\n\n".join(paragraphs)
        result = normalize_markdown(text)
        for i in range(20):
            assert f"Paragraph {i}" in result
            assert "bold" in result
