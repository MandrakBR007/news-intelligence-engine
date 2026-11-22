"""Opt-in per-feed cooldown on manually invoked jobs; no scheduler or external calls."""
from __future__ import annotations

import hashlib
import sqlite3
import time


def feed_key(url: str) -> str:
    """Use a hashed lookup key so the cooldown table does not expose feed URLs."""
    if not isinstance(url, str) or not url:
        raise ValueError("feed URL required")
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def reserve_or_defer(conn: sqlite3.Connection, job_id: int, url: str, *,
                     interval_seconds: int, now=None) -> bool:
    """Atomically reserve the next start time or defer without consuming an attempt.

    Returns True when the job may fetch; False when it was requeued for cooldown.
    With interval=0 no state is written (original V2 behavior).
    """
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int):
        raise ValueError("interval_seconds must be an integer")
    if not 0 <= interval_seconds <= 86400:
        raise ValueError("interval_seconds must be between 0 and 86400")
    if interval_seconds == 0:
        return True
    now = time.time() if now is None else now
    key = feed_key(url)
    conn.execute("BEGIN IMMEDIATE")
    try:
        job = conn.execute(
            "SELECT status FROM jobs WHERE id=?", (job_id,)
        ).fetchone()
        if not job or job["status"] != "leased":
            raise ValueError("job must be leased before reserving a cooldown")
        row = conn.execute(
            "SELECT next_allowed_at FROM feed_cooldowns WHERE source_key=?", (key,)
        ).fetchone()
        if row is not None and row["next_allowed_at"] > now:
            # Move to pending and cancel claim's attempt increment. No fetch occurred.
            conn.execute(
                """UPDATE jobs SET status='pending',available_at=?,leased_until=NULL,
                   attempts=attempts-1 WHERE id=? AND status='leased'""",
                (row["next_allowed_at"], job_id),
            )
            conn.commit()
            return False
        conn.execute(
            """INSERT INTO feed_cooldowns(source_key,next_allowed_at) VALUES(?,?)
               ON CONFLICT(source_key) DO UPDATE SET
               next_allowed_at=excluded.next_allowed_at""",
            (key, now + interval_seconds),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
