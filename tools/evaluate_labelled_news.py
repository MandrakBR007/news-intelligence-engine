"""Run local, aggregate-only evaluation on a user-provided labelled JSON file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from news_engine.independent_evaluation import evaluate

MAX_BYTES = 2_000_000


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline labelled-news classification audit")
    parser.add_argument("--input", required=True, help="Local JSON list of labelled cases")
    args = parser.parse_args(argv)
    path = Path(args.input)
    if path.stat().st_size > MAX_BYTES:
        parser.error("dataset exceeds size limit")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        parser.error("dataset exceeds size limit")
    try:
        cases = json.loads(raw)
    except (ValueError, UnicodeError):
        parser.error("invalid JSON dataset")
    result = evaluate(cases)
    # No raw text, URL, annotation identifiers or per-case predictions printed.
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
