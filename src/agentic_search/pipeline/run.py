from __future__ import annotations

import logging

from agentic_search.config import Settings, get_settings
from agentic_search.models.schemas import EntityRow, PipelineResult, SearchHit
from agentic_search.pipeline.chunk import chunk_text
from agentic_search.pipeline.extract import llm_extract_entities
from agentic_search.pipeline.fetch import fetch_page_text
from agentic_search.pipeline.merge import merge_entity_rows
from agentic_search.pipeline.search import get_retriever

logger = logging.getLogger(__name__)

# Chunk size for LLM stays below typical limits while allowing multi-chunk pages
_CHUNK_CHARS = 8000


def run_pipeline(query: str, settings: Settings | None = None) -> PipelineResult:
    """Search web → fetch pages → LLM extract per chunk → merge entities with provenance."""
    settings = settings or get_settings()
    errors: list[str] = []
    retriever = get_retriever(settings)
    hits: list[SearchHit] = retriever.search(query, count=settings.top_k_urls)
    if not hits:
        errors.append("No search results. Check SEARCH_PROVIDER and API keys, or use fixture mode.")

    all_partial: list[EntityRow] = []
    pages_fetched = 0
    chunks_processed = 0

    for hit in hits:
        fr = fetch_page_text(hit.url, timeout_s=settings.fetch_timeout_s)
        if fr.error:
            errors.append(f"{hit.url}: {fr.error}")
            continue
        if not fr.text or len(fr.text) < 80:
            errors.append(f"{hit.url}: little or no extractable text")
            continue
        pages_fetched += 1
        chunks = chunk_text(fr.text, max_chars=_CHUNK_CHARS, overlap=200)
        for ch in chunks:
            chunks_processed += 1
            rows = llm_extract_entities(query, hit.url, ch.text, settings)
            all_partial.extend(rows)

    merged = merge_entity_rows(all_partial)
    return PipelineResult(
        query=query,
        entities=merged,
        search_hits=hits,
        errors=errors,
        meta={
            "pages_fetched": pages_fetched,
            "chunks_processed": chunks_processed,
        },
    )
