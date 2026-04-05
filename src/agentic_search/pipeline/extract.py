from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from agentic_search.config import (
    Settings,
    effective_llm_base_url,
    effective_llm_key,
    uses_openrouter,
)
from agentic_search.models.schemas import AttributeCell, EntityRow, SourceRef

logger = logging.getLogger(__name__)

SYSTEM = """You extract structured data from web page text for a user's topic query.
Rules:
- Only include entities clearly supported by the given page text. Do not invent facts.
- Every attribute value must list one or more sources: each source has the page URL and a short verbatim quote from the text that supports the value.
- Use the page_url provided as the URL in sources when the evidence is from this page.
- If nothing relevant exists, return an empty entities array.
- Suggest 3-8 attribute column names appropriate to the topic (e.g. for startups: "Funding", "Founded", "Focus").
Return strict JSON matching the schema described in the user message."""


def build_user_prompt(topic_query: str, page_url: str, page_text: str, max_chars: int) -> str:
    clipped = page_text[:max_chars]
    schema = """
JSON shape:
{
  "attribute_columns": ["string", ...],
  "entities": [
    {
      "entity_name": "string",
      "attributes": {
        "ColumnName": {
          "value": "string",
          "sources": [{"url": "string", "quote": "string"}]
        }
      }
    }
  ]
}
"""
    return f"""Topic query: {topic_query}
Page URL: {page_url}

Page text:
\"\"\"
{clipped}
\"\"\"
{schema}
Fill attribute keys using human-readable column names (you may use attribute_columns as a guide).
"""


def _parse_llm_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def llm_extract_entities(
    topic_query: str,
    page_url: str,
    page_text: str,
    settings: Settings,
) -> list[EntityRow]:
    api_key = effective_llm_key(settings)
    if not api_key:
        logger.error("Set OPENROUTER_API_KEY or OPENAI_API_KEY for LLM extraction.")
        return []

    user_msg = build_user_prompt(topic_query, page_url, page_text, settings.max_chars_per_page)
    base = effective_llm_base_url(settings).rstrip("/")
    url = base + "/chat/completions"
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if uses_openrouter(settings):
        if settings.openrouter_http_referer.strip():
            headers["HTTP-Referer"] = settings.openrouter_http_referer.strip()
        title = settings.openrouter_x_title.strip() or "AgenticSearch"
        headers["X-Title"] = title
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    }
    try:
        with httpx.Client(timeout=settings.llm_timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.warning(
                "LLM HTTP 401: invalid or missing API key — verify OPENROUTER_API_KEY "
                "or OPENAI_API_KEY and OPENAI_BASE_URL (no quotes; save .env)."
            )
            return []
        logger.warning("LLM HTTP %s: %s", e.response.status_code, e.response.text[:300])
        return []
    except Exception as e:
        logger.warning("LLM request failed: %s", e)
        return []

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = _parse_llm_json(content)
    except Exception as e:
        logger.warning("LLM parse failed: %s", e)
        return []

    return _parsed_to_entities(parsed, default_url=page_url)


def _parsed_to_entities(parsed: dict[str, Any], default_url: str) -> list[EntityRow]:
    out: list[EntityRow] = []
    for ent in parsed.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        name = (ent.get("entity_name") or "").strip()
        if not name:
            continue
        attrs_raw = ent.get("attributes") or {}
        attrs: dict[str, AttributeCell] = {}
        if not isinstance(attrs_raw, dict):
            continue
        for k, v in attrs_raw.items():
            if not isinstance(v, dict):
                continue
            val = str(v.get("value", "")).strip()
            sources: list[SourceRef] = []
            for s in v.get("sources") or []:
                if not isinstance(s, dict):
                    continue
                u = str(s.get("url") or default_url).strip()
                q = str(s.get("quote") or "")[:1200]
                if u:
                    sources.append(SourceRef(url=u, quote=q))
            if not sources and val:
                sources.append(SourceRef(url=default_url, quote=""))
            attrs[str(k)] = AttributeCell(value=val, sources=sources)
        out.append(EntityRow(entity_name=name, attributes=attrs))
    return out
