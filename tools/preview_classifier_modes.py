"""Explicit offline classifier preview of one locally provided JSON article."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from news_engine.classifier_preview import MODES, preview, preview_all

MAX_PREVIEW_BYTES = 64000


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline, read-only classifier research preview")
    parser.add_argument("--input", required=True, help="Local JSON article file")
    parser.add_argument("--mode", choices=(*MODES, "all"), required=True)
    args = parser.parse_args(argv)
    path = Path(args.input)
    if path.stat().st_size > MAX_PREVIEW_BYTES:
        parser.error("input exceeds 64 KB")
    with path.open("rb") as handle:
        raw = handle.read(MAX_PREVIEW_BYTES + 1)
    if len(raw) > MAX_PREVIEW_BYTES:
        parser.error("input exceeds 64 KB")
    try:
        item = json.loads(raw)
    except (ValueError, UnicodeError):
        parser.error("input is not valid JSON")
    if not isinstance(item, dict):
        parser.error("input must contain a JSON object")
    if not all(key not in item or isinstance(item[key], str) or item[key] is None
               for key in ("title", "summary")):
        parser.error("title and summary must be strings")
    result = preview_all(item) if args.mode == "all" else preview(item, mode=args.mode)
    # Intentionally print only decision fields, never user-supplied news text.
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
