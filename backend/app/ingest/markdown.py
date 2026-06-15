"""Markdown to plain text normalizer with paragraph preservation."""

import re

import markdown
from bs4 import BeautifulSoup

BLOCK_TAGS = (
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "p",
    "pre",
    "td",
    "th",
)


def normalize_markdown(text: str) -> str:
    """Convert markdown text to plain text, preserving paragraph breaks.

    Strips markdown syntax while preserving textual content and paragraph
    structure.

    Args:
        text: Raw markdown string.

    Returns:
        Plain text with paragraphs separated by double newlines.
    """
    if not text or not text.strip():
        return ""

    html = markdown.markdown(text, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("img"):
        tag.decompose()

    for tag in soup.find_all("a"):
        tag.unwrap()

    blocks: list[str] = []
    for tag in soup.find_all(BLOCK_TAGS):
        if tag.find_parent(BLOCK_TAGS):
            continue
        separator = "\n" if tag.name == "pre" else " "
        block_text = tag.get_text(separator, strip=True)
        if block_text:
            blocks.append(_strip_unparsed_markdown_marks(block_text))

    if not blocks:
        fallback = soup.get_text(" ", strip=True)
        return _strip_unparsed_markdown_marks(fallback) if fallback else ""

    return "\n\n".join(blocks)


def _strip_unparsed_markdown_marks(text: str) -> str:
    return re.sub(r"~~(.+?)~~", r"\1", text)
