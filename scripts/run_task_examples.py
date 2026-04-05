"""Run the three task.txt example queries and print a short summary (for README / manual QA)."""
from __future__ import annotations

import json
import os
import sys

# Ensure project root on path when run as python scripts/run_task_examples.py
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

# Override .env for a cheaper multi-query evaluation (remove to use .env TOP_K_URLS).
os.environ["TOP_K_URLS"] = "3"

from agentic_search.config import get_settings  # noqa: E402
from agentic_search.pipeline.run import run_pipeline  # noqa: E402

EXAMPLES = [
    "AI startups in healthcare",
    "top pizza places in Brooklyn",
    "open source database tools",
]


def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    out_path = os.path.join(_ROOT, "evaluation_runs.json")
    rows = []
    for q in EXAMPLES:
        r = run_pipeline(q, settings=settings)
        rows.append(
            {
                "query": q,
                "entity_count": len(r.entities),
                "search_hit_count": len(r.search_hits),
                "errors": r.errors,
                "sample_entities": [e.entity_name for e in r.entities[:5]],
            }
        )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
