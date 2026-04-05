from __future__ import annotations

import re

from agentic_search.models.schemas import AttributeCell, EntityRow, SourceRef


def _norm_name(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _merge_sources(a: list[SourceRef], b: list[SourceRef]) -> list[SourceRef]:
    seen: set[tuple[str, str]] = set()
    out: list[SourceRef] = []
    for src in a + b:
        key = (src.url, src.quote[:200])
        if key in seen:
            continue
        seen.add(key)
        out.append(src)
    return out


def merge_entity_rows(partials: list[EntityRow]) -> list[EntityRow]:
    """Merge rows that refer to the same entity (normalized name). Union attributes and sources."""
    by_norm: dict[str, EntityRow] = {}
    for row in partials:
        key = _norm_name(row.entity_name)
        if not key:
            continue
        if key not in by_norm:
            by_norm[key] = EntityRow(
                entity_name=row.entity_name.strip(),
                attributes=dict(row.attributes),
            )
            continue
        existing = by_norm[key]
        for attr_name, cell in row.attributes.items():
            if attr_name not in existing.attributes:
                existing.attributes[attr_name] = cell
                continue
            cur = existing.attributes[attr_name]
            v1, v2 = cur.value.strip(), cell.value.strip()
            if v1 == v2:
                existing.attributes[attr_name] = AttributeCell(
                    value=cur.value,
                    sources=_merge_sources(cur.sources, cell.sources),
                )
            elif not v1:
                existing.attributes[attr_name] = cell
            elif not v2:
                pass
            else:
                existing.attributes[attr_name] = AttributeCell(
                    value=f"{cur.value}; {cell.value}",
                    sources=_merge_sources(cur.sources, cell.sources),
                )
    return list(by_norm.values())
