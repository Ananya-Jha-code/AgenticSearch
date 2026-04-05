from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agentic_search.config import get_settings
from agentic_search.pipeline.run import run_pipeline

_STATIC = Path(__file__).resolve().parents[1] / "static"
_INDEX = _STATIC / "index.html"

app = FastAPI(title="Agentic Search", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    # Optional overrides could be added here later


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    """Simple web UI: enter a topic query and view the results table with sources."""
    return FileResponse(_INDEX)


@app.post("/search")
def search(req: SearchRequest):
    settings = get_settings()
    result = run_pipeline(req.query.strip(), settings=settings)
    return result.model_dump()
