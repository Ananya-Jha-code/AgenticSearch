from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import httpx

from agentic_search.config import Settings
from agentic_search.models.schemas import SearchHit

logger = logging.getLogger(__name__)


@runtime_checkable
class Retriever(Protocol):
    def search(self, query: str, count: int) -> list[SearchHit]: ...


class BraveRetriever:
    """Brave Web Search API: https://api.search.brave.com/res/v1/web/search"""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, count: int) -> list[SearchHit]:
        if not self._api_key:
            logger.warning("BRAVE_API_KEY missing; returning no hits.")
            return []
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self._api_key, "Accept": "application/json"}
        params = {"q": query, "count": min(count, 20)}
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        out: list[SearchHit] = []
        for w in data.get("web", {}).get("results", []) or []:
            u = w.get("url") or ""
            if not u:
                continue
            out.append(
                SearchHit(
                    url=u,
                    title=(w.get("title") or "")[:500],
                    snippet=(w.get("description") or "")[:800],
                )
            )
        return out[:count]


class SerpApiRetriever:
    """Google via SerpAPI (engine=google)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, count: int) -> list[SearchHit]:
        if not self._api_key:
            logger.warning("SERPAPI_KEY missing; returning no hits.")
            return []
        url = "https://serpapi.com/search.json"
        params = {"engine": "google", "q": query, "num": min(count, 10), "api_key": self._api_key}
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        out: list[SearchHit] = []
        for it in data.get("organic_results", []) or []:
            u = it.get("link") or ""
            if not u:
                continue
            out.append(
                SearchHit(
                    url=u,
                    title=(it.get("title") or "")[:500],
                    snippet=(it.get("snippet") or "")[:800],
                )
            )
        return out[:count]


class FixtureRetriever:
    """Fixed URLs for offline structure tests (no search API). Content may change."""

    _URLS = (
        "https://en.wikipedia.org/wiki/Information_retrieval",
        "https://en.wikipedia.org/wiki/Web_search_engine",
    )

    def search(self, query: str, count: int) -> list[SearchHit]:
        hits = [
            SearchHit(url=u, title="Fixture", snippet=f"Offline fixture for query: {query[:80]}")
            for u in self._URLS[:count]
        ]
        return hits


def get_retriever(settings: Settings) -> Retriever:
    p = (settings.search_provider or "brave").lower().strip()
    if p == "serpapi":
        return SerpApiRetriever(settings.serpapi_key)
    if p == "fixture":
        return FixtureRetriever()
    return BraveRetriever(settings.brave_api_key)
