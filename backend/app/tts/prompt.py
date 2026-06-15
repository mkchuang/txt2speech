import re

DEFAULT_STYLE = "natural and clear"
DEFAULT_PACING = "natural"
DEFAULT_ACCENT = "match the transcript language"
WHITESPACE_PATTERN = re.compile(r"\s+")


def _normalize_prompt_value(value: str) -> str:
    normalized = WHITESPACE_PATTERN.sub(" ", value).strip()
    without_markers = normalized.replace("#", "")
    return WHITESPACE_PATTERN.sub(" ", without_markers).strip()


def _normalize_note(value: str, default: str) -> str:
    return _normalize_prompt_value(value) or default


def build_prompt(
    transcript: str,
    style: str = "",
    pacing: str = "",
    accent: str = "",
    voice: str = "",
) -> str:
    """Build the Gemini TTS instruction prompt for one transcript chunk."""

    preamble_lines = [
        "You are a professional narrator.",
        "Read only the transcript section aloud.",
        "Use the director's notes only as delivery guidance.",
        "Do not speak section headings, labels, or director's notes.",
    ]
    normalized_voice = _normalize_prompt_value(voice)
    if normalized_voice:
        preamble_lines.insert(0, f"Voice: {normalized_voice}")

    notes_parts = [
        f"Style: {_normalize_note(style, DEFAULT_STYLE)}",
        f"Pacing: {_normalize_note(pacing, DEFAULT_PACING)}",
        f"Accent: {_normalize_note(accent, DEFAULT_ACCENT)}",
    ]

    sections: list[str] = ["\n".join(preamble_lines)]
    sections.append("### DIRECTOR'S NOTES\n" + "\n".join(notes_parts))
    sections.append("### TRANSCRIPT\n" + transcript)

    return "\n\n".join(sections)
