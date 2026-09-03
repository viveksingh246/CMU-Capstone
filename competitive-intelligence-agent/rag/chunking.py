"""Document chunking for RAG indexing."""

from __future__ import annotations

from typing import Any

# Approximate 4 characters per token (checkpoint 3.1: 500-800 token chunks)
CHARS_PER_TOKEN = 4
DEFAULT_CHUNK_TOKENS = 650
DEFAULT_OVERLAP_RATIO = 0.15


def chunk_document(
    text: str,
    metadata: dict[str, Any] | None = None,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_ratio: float = DEFAULT_OVERLAP_RATIO,
) -> list[dict[str, Any]]:
    """Split a document into overlapping chunks with metadata preserved."""
    if not text or not text.strip():
        return []

    chunk_size = chunk_tokens * CHARS_PER_TOKEN
    overlap = int(chunk_size * overlap_ratio)
    step = max(chunk_size - overlap, 1)

    chunks: list[dict[str, Any]] = []
    base_meta = metadata or {}

    for index, start in enumerate(range(0, len(text), step)):
        chunk_text = text[start : start + chunk_size].strip()
        if not chunk_text:
            continue

        chunk_meta = {
            **base_meta,
            "chunk_index": index,
            "char_start": start,
            "char_end": start + len(chunk_text),
        }
        chunks.append({"text": chunk_text, "metadata": chunk_meta})

        if start + chunk_size >= len(text):
            break

    return chunks
