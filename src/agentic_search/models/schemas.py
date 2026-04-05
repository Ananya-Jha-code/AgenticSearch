from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Traceability: where a value came from."""

    url: str
    quote: str = Field(
        default="",
        description="Short verbatim snippet from the page supporting the value.",
    )


class AttributeCell(BaseModel):
    """One table cell: value plus all sources that support it."""

    value: str
    sources: list[SourceRef] = Field(default_factory=list)


class EntityRow(BaseModel):
    """One row in the output table: entity name + dynamic attributes."""

    entity_name: str
    attributes: dict[str, AttributeCell] = Field(default_factory=dict)


class SearchHit(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""


class PipelineResult(BaseModel):
    query: str
    entities: list[EntityRow]
    search_hits: list[SearchHit] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
