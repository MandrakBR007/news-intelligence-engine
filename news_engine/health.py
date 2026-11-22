"""Privacy-minimized, read-only operational health diagnostics.

Never include feed URLs, source names, payloads, exception messages, or tokens.
The function does no network I/O and requires an already-open SQLite database.
"""
from __future__ import annotations

from . import queue


def diagnostic_snapshot(conn) -> dict:
    """Return fixed numerical fields and an optional latest collection timestamp."""
    row = conn.execute(
        """SELECT COUNT(*) AS total,
        COALESCE(SUM(CASE WHEN last_status IS NOT NULL
            AND last_status NOT IN (200, 304) THEN 1 ELSE 0 END), 0) AS bad_status,
        MAX(checked_at) AS latest FROM feed_cache"""
    ).fetchone()
    item_row = conn.execute(
        "SELECT COUNT(*) AS total, MAX(first_seen_at) AS latest FROM items"
    ).fetchone()
    return {
        "status": "ok",
        "items": int(item_row["total"]),
        "feed_cache_entries": int(row["total"]),
        "feeds_with_unexpected_status": int(row["bad_status"]),
        "last_feed_check_at": row["latest"],
        "last_item_observed_at": item_row["latest"],
        "queue": queue.diagnostics(conn),
    }
