import re
from typing import Callable

from .prompt import build_prompt, DEFAULT_STYLE, DEFAULT_PACING, DEFAULT_ACCENT

MAX_TOKEN_LIMIT = 7500
MAX_CHUNK_CHARS = 2500
TOKEN_ACCOUNTING_MARGIN = 1

_CJK_RANGE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[。！？.!?])\s*")


class ChunkingError(ValueError):
    """Raised when no valid chunk can fit within the configured limits."""


def estimate_tokens(text: str) -> int:
    """Estimate token count from character composition.

    Heuristic: ~4 ASCII chars/token, ~1.5 CJK chars/token.
    Always returns at least 1 for non-empty text.
    """
    if not text:
        return 0
    cjk_count = len(_CJK_RANGE.findall(text))
    ascii_count = len(text) - cjk_count
    return max(1, int(ascii_count / 4.0 + cjk_count / 1.5))

def _prompt_overhead_tokens(
    style: str,
    pacing: str,
    accent: str,
    voice: str,
) -> int:
    return estimate_tokens(build_prompt("", style, pacing, accent, voice))


def _text_tokens(
    text: str,
    count_tokens_fn: Callable[[str], int] | None,
) -> int:
    return count_tokens_fn(text) if count_tokens_fn else estimate_tokens(text)


def _rendered_prompt_tokens(
    chunk: str,
    style: str,
    pacing: str,
    accent: str,
    voice: str,
) -> int:
    return estimate_tokens(build_prompt(chunk, style, pacing, accent, voice))


def _fits(
    text: str,
    max_tokens: int,
    max_chunk_chars: int,
    count_chunk_tokens_fn: Callable[[str], int],
) -> bool:
    if len(text) > max_chunk_chars:
        return False
    return count_chunk_tokens_fn(text) <= max_tokens


def _char_split_token_aware(
    text: str,
    max_tokens: int,
    max_chunk_chars: int,
    count_chunk_tokens_fn: Callable[[str], int],
) -> list[str]:
    """Split text character by character, respecting both token and char limits.

    Each returned piece is guaranteed to pass _fits.
    """
    if not text:
        return []

    pieces: list[str] = []
    buf: list[str] = []

    for ch in text:
        test = "".join(buf) + ch
        if not _fits(
            test, max_tokens, max_chunk_chars,
            count_chunk_tokens_fn,
        ):
            if buf:
                pieces.append("".join(buf))
                buf = []
            elif not _fits(
                ch, max_tokens, max_chunk_chars,
                count_chunk_tokens_fn,
            ):
                raise ChunkingError("single character cannot fit within token/char limits")
        buf.append(ch)

    if buf:
        pieces.append("".join(buf))

    return pieces


def _force_split(
    text: str,
    max_tokens: int,
    max_chunk_chars: int,
    count_chunk_tokens_fn: Callable[[str], int],
) -> list[str]:
    """Split text into pieces that each satisfy both limits.

    Prefers word boundaries (space); falls back to token-aware character-level
    split for text without spaces or for single words that exceed limits.

    Each returned piece is guaranteed to pass _fits.
    """
    words = text.split(" ")
    if len(words) == 1:
        return _char_split_token_aware(
            text, max_tokens, max_chunk_chars,
            count_chunk_tokens_fn,
        )

    pieces: list[str] = []
    buf: list[str] = []

    for word in words:
        candidate = " ".join(buf + [word]) if buf else word

        if _fits(candidate, max_tokens, max_chunk_chars, count_chunk_tokens_fn):
            buf.append(word)
        else:
            if buf:
                pieces.append(" ".join(buf))
                buf = []

            if _fits(word, max_tokens, max_chunk_chars, count_chunk_tokens_fn):
                buf.append(word)
            else:
                for sub in _char_split_token_aware(
                    word, max_tokens, max_chunk_chars,
                    count_chunk_tokens_fn,
                ):
                    pieces.append(sub)
                buf = []

    if buf:
        pieces.append(" ".join(buf))

    return pieces


def chunk_transcript(
    transcript: str,
    *,
    max_tokens: int = MAX_TOKEN_LIMIT,
    max_chunk_chars: int = MAX_CHUNK_CHARS,
    count_tokens_fn: Callable[[str], int] | None = None,
    prompt_overhead_tokens: int | None = None,
    style: str = DEFAULT_STYLE,
    pacing: str = DEFAULT_PACING,
    accent: str = DEFAULT_ACCENT,
    voice: str = "",
) -> list[str]:
    """Split transcript into chunks respecting token and character limits.

    Strategy: paragraph-first → sentence fallback → token-aware character-level
    split for text without spaces or for single words that exceed limits.

    Args:
        transcript: Raw transcript text to split.
        max_tokens: Maximum token count for the full rendered prompt
                    (overhead + chunk).
        max_chunk_chars: Maximum character count for each chunk.
        count_tokens_fn: Optional function `(text: str) -> int` for exact
                         token counting. If None, uses estimate_tokens().
        prompt_overhead_tokens: Pre-computed token count of the fixed prompt
                                parts (preamble + Director's Notes + section
                                headers). Added to chunk token estimate.
                                If None, computed from build_prompt("", style,
                                pacing, accent, voice). Explicit overhead mode
                                uses a one-token margin for split-estimate
                                rounding safety.
        style: Director's Notes style used when computing default overhead.
        pacing: Director's Notes pacing used when computing default overhead.
        accent: Director's Notes accent used when computing default overhead.
        voice: Voice preamble used when computing default overhead.

    Returns:
        List of transcript chunks. Each chunk satisfies:
          - len(chunk) <= max_chunk_chars
          - prompt_overhead_tokens + chunk_tokens <= max_tokens
        Returns empty list for empty/whitespace-only input.
    """
    if not transcript or not transcript.strip():
        return []

    if prompt_overhead_tokens is None and count_tokens_fn is None:
        def count_chunk_tokens(chunk: str) -> int:
            return _rendered_prompt_tokens(chunk, style, pacing, accent, voice)
    else:
        if prompt_overhead_tokens is None:
            prompt_overhead_tokens = _prompt_overhead_tokens(style, pacing, accent, voice)
        prompt_overhead_tokens = int(prompt_overhead_tokens)

        def count_chunk_tokens(chunk: str) -> int:
            return (
                prompt_overhead_tokens
                + _text_tokens(chunk, count_tokens_fn)
                + TOKEN_ACCOUNTING_MARGIN
            )

    if count_chunk_tokens("") >= max_tokens:
        raise ChunkingError("prompt overhead is greater than or equal to max_tokens")

    paragraphs = _PARAGRAPH_SPLIT.split(transcript.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    JOINER = "\n\n"

    def _check(text: str) -> bool:
        return _fits(text, max_tokens, max_chunk_chars, count_chunk_tokens)

    def _join(parts: list[str]) -> str:
        return JOINER.join(parts)

    def _finalize() -> None:
        if current:
            chunks.append(_join(current))
            current.clear()

    for para in paragraphs:
        candidate = _join(current + [para]) if current else para

        if _check(candidate):
            current.append(para)
            continue

        _finalize()

        if _check(para):
            current.append(para)
        else:
            sentences = _SENTENCE_END.split(para)
            sentences = [s.strip() for s in sentences if s.strip()]

            for sent in sentences:
                candidate = _join(current + [sent]) if current else sent

                if _check(candidate):
                    current.append(sent)
                    continue

                _finalize()

                if _check(sent):
                    current.append(sent)
                else:
                    for sub in _force_split(
                        sent, max_tokens, max_chunk_chars,
                        count_chunk_tokens,
                    ):
                        candidate = _join(current + [sub]) if current else sub
                        if _check(candidate):
                            current.append(sub)
                        else:
                            _finalize()
                            current.append(sub)

    _finalize()
    return chunks
