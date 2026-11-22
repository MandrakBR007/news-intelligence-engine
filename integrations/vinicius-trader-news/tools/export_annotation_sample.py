"""Explicit offline export of SQLite articles for independent human labelling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from news_engine.annotation_sampling import sample_for_annotation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only local sample export (contains unredacted article text)"
    )
    parser.add_argument("--db", required=True, help="Existing local SQLite database")
    parser.add_argument("--output", required=True, help="NEW private JSON output path")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    cases = sample_for_annotation(args.db, limit=args.limit, seed=args.seed)
    path = Path(args.output)
    if not path.parent.is_dir():
        parser.error("output directory must already exist")
    # Exclusive creation avoids overwriting human annotations. Refuse symlink
    # output on systems where it could redirect file writes outside expectations.
    if path.is_symlink():
        parser.error("output must not be a symlink")
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(cases, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError:
        parser.error("output file already exists")
    # Only aggregate counts printed; article text stays in the local JSON file.
    print(json.dumps({"exported": len(cases), "requires_human_labels": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
