from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
import trafilatura

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; AgenticSearch/0.1; +https://github.com/) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class FetchResult:
    url: str
    text: str
    status_code: int | None = None
    error: str | None = None


def fetch_page_text(url: str, timeout_s: float = 20.0) -> FetchResult:
    """Download HTML and extract main text (trafilatura)."""
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True, headers={"User-Agent": DEFAULT_UA}) as client:
            r = client.get(url)
            status = r.status_code
            if status >= 400:
                return FetchResult(url=url, text="", status_code=status, error=f"HTTP {status}")
            html = r.text
    except Exception as e:
        logger.debug("fetch failed %s: %s", url, e)
        return FetchResult(url=url, text="", status_code=None, error=str(e))

    text = trafilatura.extract(html, url=url, include_comments=False, include_tables=True) or ""
    text = " ".join(text.split())
    return FetchResult(url=url, text=text, status_code=status, error=None)
