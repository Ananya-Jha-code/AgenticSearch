from __future__ import annotations

import argparse
import json
import logging
import sys

from agentic_search.config import get_settings
from agentic_search.pipeline.run import run_pipeline


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    p = argparse.ArgumentParser(description="Agentic search: topic → table + sources")
    p.add_argument("query", help="Topic query")
    p.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON instead of a short table summary",
    )
    args = p.parse_args()
    settings = get_settings()
    out = run_pipeline(args.query, settings=settings)
    if args.json:
        print(json.dumps(out.model_dump(), indent=2, ensure_ascii=False))
        if out.errors:
            sys.exit(1)
        return
    print(f"Query: {out.query}\n")
    if out.errors:
        print("Warnings/errors:")
        for e in out.errors:
            print(f"  - {e}")
        print()
    if not out.entities:
        print("No entities extracted. Set API keys and try again.")
        sys.exit(1)
    for i, ent in enumerate(out.entities, 1):
        print(f"{i}. {ent.entity_name}")
        for k, cell in ent.attributes.items():
            srcs = "; ".join(s.url for s in cell.sources[:2])
            print(f"   {k}: {cell.value}")
            if srcs:
                print(f"      → {srcs}")
        print()


if __name__ == "__main__":
    main()
