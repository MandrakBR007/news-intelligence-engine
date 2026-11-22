"""Local-only sampling of stored news for independent manual annotation.

No network, no classification, and no writes to the source SQLite database.
Output includes only text needed by a reviewer, never source URLs or predictions.
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path


def sample_for_annotation(db_path, *, limit=40, seed=42) -> list[dict]:
    """Choose reproducible, distinct clusters without model-based selection."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
        raise ValueError("limit must be an integer from 1 to 200")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    path = Path(db_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("database path must be a regular file")
    # Read-only URI prevents accidental schema initialization or DB modification.
    uri = path.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, cluster_id, title, summary FROM items "
            "WHERE title IS NOT NULL AND TRIM(title) != '' ORDER BY id"
        )
        candidates = []
        seen_clusters = set()
        for row in rows:
            key = row["cluster_id"] or f"id:{row['id']}"
            if key in seen_clusters:
                continue
            seen_clusters.add(key)
            candidates.append((str(row["title"]), str(row["summary"] or "")))
    finally:
        conn.close()
    selected = random.Random(seed).sample(candidates, min(limit, len(candidates)))
    # Deliberately blank reference labels and languages. No classifier may
    # automatically fill these fields or determine what is 'real' news.
    return [
        {
            "id": f"local-{index:04d}",
            "language": "",
            "title": title,
            "summary": summary,
            "expected_topic": "",
        }
        for index, (title, summary) in enumerate(selected, 1)
    ]
