from unittest.mock import MagicMock

from app.tts.prompt import build_prompt
from app.tts.chunker import (
    ChunkingError,
    chunk_transcript,
    estimate_tokens,
    MAX_TOKEN_LIMIT,
    MAX_CHUNK_CHARS,
)

SHORT_TEXT = "Hello. This is a short test."
TWO_PARAGRAPHS = "First paragraph here.\n\nSecond paragraph goes here."
LONG_ASCII = ("A" * 100 + " ") * 30  # ~3000 chars
CN_EN_MIX = (
    "這是第一段中文文字，包含一些英文詞彙 like this one here。"
    "We continue with more English content and some "
    "Chinese characters like 測試 and 範例 mixed in.\n\n"
    "第二段開始，這裡有更多中英混雜的內容。"
    "Another English sentence follows after this Chinese one."
)


class TestEstimateTokens:
    def test_empty_string_returns_zero(self) -> None:
        assert estimate_tokens("") == 0

    def test_short_ascii(self) -> None:
        # "Hello" = 5 chars. 5/4 = 1.25 → 1
        assert estimate_tokens("Hello") == 1

    def test_ascii_paragraph(self) -> None:
        text = "a" * 400
        assert estimate_tokens(text) == 100  # 400/4

    def test_pure_cjk(self) -> None:
        text = "你好世界" * 100  # 400 CJK chars
        assert estimate_tokens(text) == 266  # 400/1.5 = 266.67

    def test_mixed_cn_en(self) -> None:
        text = "Hello 你好 World 世界"  # 10 ASCII + 4 CJK
        tokens = estimate_tokens(text)
        assert tokens > 1
        assert tokens < len(text)


class TestChunkShortInput:
    def test_empty_transcript(self) -> None:
        assert chunk_transcript("") == []

    def test_whitespace_only(self) -> None:
        assert chunk_transcript("   \n  \n  ") == []

    def test_short_text_single_chunk(self) -> None:
        result = chunk_transcript(SHORT_TEXT)
        assert len(result) == 1
        assert result[0] == SHORT_TEXT

    def test_two_paragraphs_short(self) -> None:
        result = chunk_transcript(TWO_PARAGRAPHS)
        assert len(result) == 1
        assert "First paragraph" in result[0]
        assert "Second paragraph" in result[0]


class TestChunkCharLimitTrigger:
    def test_char_limit_triggers_paragraph_split(self) -> None:
        # Each paragraph ~1500 chars, two paragraphs → exceeds 2500 combined
        para_a = ("A" * 75 + " ") * 20  # ~1520 chars
        para_b = ("B" * 75 + " ") * 20  # ~1520 chars
        text = f"{para_a}\n\n{para_b}"

        result = chunk_transcript(text, max_chunk_chars=2500, max_tokens=99999)
        assert len(result) == 2
        assert len(result[0]) <= 2500
        assert len(result[1]) <= 2500

    def test_char_limit_respects_custom_max(self) -> None:
        text = ("X" * 100 + " ") * 10  # ~1010 chars
        result = chunk_transcript(text, max_chunk_chars=500)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 500

    def test_char_limit_triggers_sentence_split(self) -> None:
        # Build one large paragraph with multiple sentences, exceeding char limit
        long_sent = "X" * 1500 + ". "
        sentences = " ".join(f"Sentence number {i}." for i in range(10))
        para = long_sent + sentences + " " + ("Y" * 1500 + ".")
        result = chunk_transcript(para, max_chunk_chars=2500, max_tokens=99999)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 2500


class TestChunkTokenLimitTrigger:
    def test_token_limit_triggers_split(self) -> None:
        # Create many paragraphs that individually are small in chars
        # but collectively exceed token limit
        paragraphs = [f"Paragraph {i} with some content here." for i in range(1, 200)]
        text = "\n\n".join(paragraphs)

        result = chunk_transcript(text, max_tokens=800, max_chunk_chars=99999)
        assert len(result) >= 2
        for chunk in result:
            assert estimate_tokens(chunk) <= 800

    def test_token_limit_with_count_tokens_fn(self) -> None:
        # Mock count_tokens_fn: each paragraph costs 500 tokens
        def mock_count(text: str) -> int:
            return text.count("Paragraph") * 500

        paragraphs = [f"Paragraph {i} with some content." for i in range(1, 10)]
        text = "\n\n".join(paragraphs)

        result = chunk_transcript(
            text,
            max_tokens=1500,
            max_chunk_chars=99999,
            count_tokens_fn=mock_count,
        )
        assert len(result) >= 3  # Each chunk can hold at most 3 paragraphs

    def test_token_limit_with_overhead(self) -> None:
        # Overhead of 200 tokens leaves only 800 for content
        paragraphs = [f"Paragraph {i} with some content here." for i in range(1, 50)]
        text = "\n\n".join(paragraphs)

        result = chunk_transcript(
            text,
            max_tokens=1000,
            max_chunk_chars=99999,
            prompt_overhead_tokens=200,
        )
        for chunk in result:
            total = 200 + estimate_tokens(chunk)
            assert total <= 1000


class TestFullPromptTokenNotExceedLimit:
    STYLE = "natural and clear"
    PACING = "natural"
    ACCENT = "match the transcript language"
    VOICE = "Puck"

    def test_full_prompt_token_within_limit(self) -> None:
        """Verify each chunk's full rendered prompt tokens ≤ max_tokens."""
        # Build a moderate transcript that will be split
        paragraphs = [f"Paragraph {i} with content. " * 5 for i in range(1, 30)]
        text = "\n\n".join(paragraphs)

        # Calculate real prompt overhead tokens
        overhead_prompt = build_prompt("", self.STYLE, self.PACING, self.ACCENT, self.VOICE)
        overhead_tokens = estimate_tokens(overhead_prompt)

        result = chunk_transcript(
            text,
            max_tokens=2000,
            max_chunk_chars=99999,
            prompt_overhead_tokens=overhead_tokens,
        )

        for chunk in result:
            full_prompt = build_prompt(chunk, self.STYLE, self.PACING, self.ACCENT, self.VOICE)
            full_tokens = estimate_tokens(full_prompt)
            assert full_tokens <= 2000

    def test_full_prompt_token_with_defaults(self) -> None:
        """With max_tokens=7500, full prompt should be well within limit."""
        paragraphs = [f"Section {i}: " + "X" * 2000 for i in range(1, 5)]
        text = "\n\n".join(paragraphs)

        # Overhead prompt
        overhead_prompt = build_prompt("", self.STYLE, self.PACING, self.ACCENT, self.VOICE)
        overhead_tokens = estimate_tokens(overhead_prompt)

        result = chunk_transcript(
            text,
            max_tokens=MAX_TOKEN_LIMIT,
            max_chunk_chars=MAX_CHUNK_CHARS,
            prompt_overhead_tokens=overhead_tokens,
        )

        for chunk in result:
            full_prompt = build_prompt(chunk, self.STYLE, self.PACING, self.ACCENT, self.VOICE)
            full_tokens = estimate_tokens(full_prompt)
            assert len(chunk) <= MAX_CHUNK_CHARS
            assert full_tokens <= MAX_TOKEN_LIMIT


class TestSingleChunkNotExceedBothLimits:
    def test_each_chunk_below_char_limit(self) -> None:
        text = ("A" * 500 + ". ") * 10
        result = chunk_transcript(text, max_chunk_chars=2500, max_tokens=99999)
        for chunk in result:
            assert len(chunk) <= 2500

    def test_each_chunk_below_token_limit(self) -> None:
        text = ("Paragraph content here. ") * 200
        result = chunk_transcript(text, max_tokens=500, max_chunk_chars=99999)
        for chunk in result:
            assert estimate_tokens(chunk) <= 500

    def test_each_chunk_below_both_limits(self) -> None:
        paragraphs = [f"Content {i}: " + "X" * 400 for i in range(1, 20)]
        text = "\n\n".join(paragraphs)

        overhead_prompt = build_prompt("")
        overhead_tokens = estimate_tokens(overhead_prompt)

        result = chunk_transcript(
            text,
            max_tokens=2000,
            max_chunk_chars=2500,
            prompt_overhead_tokens=overhead_tokens,
        )

        for chunk in result:
            assert len(chunk) <= 2500
            assert overhead_tokens + estimate_tokens(chunk) <= 2000

    def test_no_single_empty_chunk(self) -> None:
        text = "Valid content here."
        result = chunk_transcript(text)
        assert len(result) >= 1
        for chunk in result:
            assert chunk.strip()


class TestSuperLongSingleSentence:
    def test_long_sentence_hard_split(self) -> None:
        # A sentence longer than max_chunk_chars with no paragraph breaks
        long_sentence = ("word " * 1000) + "."
        result = chunk_transcript(long_sentence, max_chunk_chars=2000, max_tokens=99999)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 2000

    def test_long_sentence_respects_token_limit(self) -> None:
        long_sentence = "text " * 600 + "."  # ~3000 chars
        result = chunk_transcript(long_sentence, max_tokens=200, max_chunk_chars=99999)
        assert len(result) >= 2
        for chunk in result:
            assert estimate_tokens(chunk) <= 200

    def test_cjk_long_sentence(self) -> None:
        long_sentence = "這是一個非常長的句子" * 200 + "。"
        result = chunk_transcript(long_sentence, max_chunk_chars=2000, max_tokens=99999)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 2000

    def test_cjk_sentence_boundaries_without_spaces(self) -> None:
        text = (
            "第一句內容。第二句內容。第三句內容。"
            "第四句內容。第五句內容。"
        )
        result = chunk_transcript(text, max_chunk_chars=10, max_tokens=99999)
        assert len(result) >= 3
        assert all(chunk.endswith("。") for chunk in result)
        assert all("。第" not in chunk for chunk in result)

    def test_no_sentence_boundaries_long_text(self) -> None:
        # Text without any sentence-ending punctuation
        text = "hello " * 1500
        result = chunk_transcript(text, max_chunk_chars=2000, max_tokens=99999)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 2000


class TestMixedChineseEnglish:
    def test_cn_en_mixed_paragraphs(self) -> None:
        result = chunk_transcript(CN_EN_MIX, max_chunk_chars=500, max_tokens=99999)
        for chunk in result:
            assert len(chunk) <= 500

    def test_cn_en_token_estimation(self) -> None:
        # CJK chars contribute more tokens per char (~1 char/token vs ~4 chars/token)
        # Same char count: CJK should have higher token estimate
        cn_text = "測試" * 50     # 100 CJK chars → ~66 tokens
        en_text = "ab" * 50       # 100 ASCII chars → ~25 tokens
        assert estimate_tokens(cn_text) > estimate_tokens(en_text)

    def test_cn_en_paragraph_boundary_preserved(self) -> None:
        text = "中文第一段\n\nEnglish second paragraph.\n\n第三段混合 content."
        result = chunk_transcript(text, max_chunk_chars=99999, max_tokens=99999)
        assert len(result) == 1
        assert "中文第一段" in result[0]
        assert "English second paragraph" in result[0]

    def test_mixed_cn_en_token_limit_triggers(self) -> None:
        """CJK-heavy text should trigger token limit faster than ASCII."""
        cn_paragraphs = [
            f"第{i}段：這是測試用的中文內容，包含一些描述。"
            for i in range(1, 100)
        ]
        text = "\n\n".join(cn_paragraphs)

        result = chunk_transcript(text, max_tokens=1000, max_chunk_chars=99999)
        assert len(result) >= 2


class TestChunkBoundaries:
    def test_paragraphs_not_split_within(self) -> None:
        """A paragraph that fits should not be split."""
        text = "Short paragraph one.\n\nShort paragraph two.\n\nShort paragraph three."
        result = chunk_transcript(text)
        assert len(result) == 1
        # All three paragraphs present
        assert result[0].count("\n\n") == 2

    def test_chunks_are_non_empty(self) -> None:
        text = "a. " * 1000
        result = chunk_transcript(text, max_chunk_chars=500, max_tokens=99999)
        for chunk in result:
            assert len(chunk) > 0

    def test_all_content_preserved(self) -> None:
        text = "Hello world. This is a test.\n\nAnother paragraph here."
        result = chunk_transcript(text)
        combined = "".join(result)
        # All non-whitespace content characters should be preserved
        original_chars = set(text.strip())
        result_chars = set(combined.strip())
        for c in original_chars:
            assert c in result_chars

    def test_custom_limits_propagate(self) -> None:
        text = ("A" * 300 + ". ") * 10
        result = chunk_transcript(text, max_chunk_chars=1000, max_tokens=500)
        for chunk in result:
            assert len(chunk) <= 1000
            assert estimate_tokens(chunk) <= 500


class TestCountTokensFnIntegration:
    def test_count_tokens_fn_called(self) -> None:
        mock_fn = MagicMock(return_value=100)
        text = "Paragraph one.\n\nParagraph two."
        chunk_transcript(text, count_tokens_fn=mock_fn)
        assert mock_fn.call_count >= 2  # At least once per paragraph

    def test_count_tokens_fn_overrides_estimation(self) -> None:
        # Each paragraph costs 4000 tokens, two paragraphs exceed 7000
        def high_count(text: str) -> int:
            return (text.count("\n\n") + 1) * 4000

        paragraphs = ["Para one.", "Para two.", "Para three.", "Para four."]
        text = "\n\n".join(paragraphs)
        result = chunk_transcript(
            text,
            max_tokens=7000,
            max_chunk_chars=99999,
            count_tokens_fn=high_count,
        )
        # Each paragraph costs 4000, so at most 1 per chunk
        assert len(result) >= 3

    def test_count_tokens_fn_with_zero_tokens(self) -> None:
        def zero_count(_text: str) -> int:
            return 0

        text = "A" * 5000
        # Should still split due to char limit even if tokens are 0
        result = chunk_transcript(
            text,
            max_tokens=7500,
            max_chunk_chars=2500,
            count_tokens_fn=zero_count,
        )
        for chunk in result:
            assert len(chunk) <= 2500


class TestTokenOnlyOverflow:
    """Token-limit-driven char split for no-space text (单字/CJK)."""

    STYLE = "natural and clear"
    PACING = "natural"
    ACCENT = "match the transcript language"
    VOICE = "Puck"

    def _overhead(self) -> int:
        return estimate_tokens(build_prompt("", self.STYLE, self.PACING, self.ACCENT, self.VOICE))

    def test_single_long_word_ascii_token_only_overflow(self) -> None:
        """max_tokens=200, max_chunk_chars large, single ASCII word — each
        chunk's estimate_tokens + overhead <= 200."""
        text = "a" * 10000
        overhead = self._overhead()
        result = chunk_transcript(
            text,
            max_tokens=200,
            max_chunk_chars=99999,
            prompt_overhead_tokens=overhead,
        )
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 99999
            assert overhead + estimate_tokens(chunk) <= 200

    def test_cjk_no_space_token_only_overflow(self) -> None:
        """CJK text without spaces, token-only limit should still trigger split."""
        text = "這是一個沒有空格的長句子用於測試分塊功能" * 200
        overhead = self._overhead()
        result = chunk_transcript(
            text,
            max_tokens=200,
            max_chunk_chars=99999,
            prompt_overhead_tokens=overhead,
        )
        assert len(result) >= 2
        for chunk in result:
            assert overhead + estimate_tokens(chunk) <= 200

    def test_full_prompt_estimate_not_exceed_max_tokens(self) -> None:
        """build_prompt(chunk) full estimate must never exceed max_tokens."""
        text = ("Paragraph " * 50 + ". ") * 20
        overhead = self._overhead()
        result = chunk_transcript(
            text,
            max_tokens=500,
            max_chunk_chars=99999,
            prompt_overhead_tokens=overhead,
        )
        assert len(result) >= 2
        for chunk in result:
            full_prompt = build_prompt(chunk, self.STYLE, self.PACING, self.ACCENT, self.VOICE)
            full_tokens = estimate_tokens(full_prompt)
            assert full_tokens <= 500

    def test_full_prompt_boundary_rounding_does_not_leak(self) -> None:
        """Full prompt estimate must not exceed max_tokens at rounding edge."""
        result = chunk_transcript(
            "a" * 1690,
            max_tokens=500,
            max_chunk_chars=99999,
            style=self.STYLE,
            pacing=self.PACING,
            accent=self.ACCENT,
            voice=self.VOICE,
        )
        assert len(result) >= 2
        for chunk in result:
            full_prompt = build_prompt(
                chunk, self.STYLE, self.PACING, self.ACCENT, self.VOICE
            )
            assert estimate_tokens(full_prompt) <= 500

    def test_long_notes_without_explicit_overhead_uses_prompt_context(self) -> None:
        text = ("Paragraph " * 50 + ". ") * 20
        long_notes = "x" * 1000
        result = chunk_transcript(
            text,
            max_tokens=1500,
            max_chunk_chars=99999,
            style=long_notes,
            pacing=long_notes,
            accent=long_notes,
            voice=self.VOICE,
        )
        assert len(result) >= 2
        for chunk in result:
            full_prompt = build_prompt(
                chunk, long_notes, long_notes, long_notes, self.VOICE
            )
            assert estimate_tokens(full_prompt) <= 1500

    def test_prompt_overhead_over_budget_raises(self) -> None:
        long_notes = "x" * 1000
        try:
            chunk_transcript(
                "Hello world.",
                max_tokens=500,
                max_chunk_chars=99999,
                style=long_notes,
                pacing=long_notes,
                accent=long_notes,
                voice=self.VOICE,
            )
        except ChunkingError:
            pass
        else:
            assert False, "Expected ChunkingError when prompt overhead exceeds budget"

    def test_count_tokens_fn_path_respects_overhead_and_token_limit(self) -> None:
        """Custom count_tokens_fn must also respect overhead + chunk <= max_tokens."""

        def fixed_count(text: str) -> int:
            return max(1, len(text) // 3)

        text = "Hello world. " * 200
        overhead = self._overhead()
        result = chunk_transcript(
            text,
            max_tokens=300,
            max_chunk_chars=99999,
            prompt_overhead_tokens=overhead,
            count_tokens_fn=fixed_count,
        )
        assert len(result) >= 2
        for chunk in result:
            assert overhead + fixed_count(chunk) <= 300

    def test_default_overhead_not_zero(self) -> None:
        """Default prompt_overhead_tokens must be >0 for safety."""
        text = "Hello world. " * 50
        # Don't pass overhead explicitly — check default kicks in
        result = chunk_transcript(
            text,
            max_tokens=100,
            max_chunk_chars=99999,
        )
        # Default overhead will consume some tokens, forcing more chunks
        assert len(result) >= 1
        for chunk in result:
            assert len(chunk) <= 99999
            assert estimate_tokens(build_prompt(chunk)) <= 100
