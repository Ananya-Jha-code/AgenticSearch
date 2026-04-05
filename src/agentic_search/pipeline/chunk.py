from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    start_char: int


def chunk_text(text: str, max_chars: int = 8000, overlap: int = 200) -> list[TextChunk]:
    """Split long pages for LLM context limits; overlap reduces boundary cuts."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [TextChunk(text=text, start_char=0)]
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(TextChunk(text=text[start:end], start_char=start))
        if end >= len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks
