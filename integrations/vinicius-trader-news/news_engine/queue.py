"""Generic SQLite work queue with leases, retries and deterministic idempotency.

No background service is started automatically. All operations are explicit.
"""
from __future__ import annotations

import json
import sqlite3
import time


def enqueue(conn: sqlite3.Connection, kind: str, payload: dict, dedup_key: str, *, now=None) -> bool:
    now = time.time() if now is None else now
    cur = conn.execute("""INSERT OR IGNORE INTO jobs(kind,payload,dedup_key,status,
                      available_at,created_at) VALUES(?,?,?,'pending',?,?)""",
                       (kind, json.dumps(payload, ensure_ascii=False), dedup_key, now, now))
    conn.commit()
    return bool(cur.rowcount)


def claim(conn, *, lease_seconds=60, now=None) -> dict | None:
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("""SELECT * FROM jobs WHERE
                (status='pending' AND available_at<=?) OR
                (status='leased' AND leased_until<=?)
                ORDER BY available_at,id LIMIT 1""", (now, now)).fetchone()
        if row is None:
            conn.commit()
            return None
        conn.execute("""UPDATE jobs SET status='leased',attempts=attempts+1,
                        leased_until=?,last_error=NULL WHERE id=?""",
                     (now + lease_seconds, row["id"]))
        conn.commit()
        job = dict(row)
        job["attempts"] += 1
        job["payload"] = json.loads(job["payload"])
        return job
    except Exception:
        conn.rollback()
        raise


def ack(conn, job_id: int):
    conn.execute("UPDATE jobs SET status='done',leased_until=NULL WHERE id=? AND status='leased'", (job_id,))
    conn.commit()


def fail(conn, job_id: int, error: str, *, max_attempts=3, delay_seconds=60,
         backoff_factor=1, now=None):
    if not 1 <= backoff_factor <= 10:
        raise ValueError("backoff_factor must be between 1 and 10")
    if not 0 <= delay_seconds <= 86400:
        raise ValueError("delay_seconds must be between 0 and 86400")
    now = time.time() if now is None else now
    row = conn.execute("SELECT attempts FROM jobs WHERE id=? AND status='leased'", (job_id,)).fetchone()
    if row is None:
        return
    status = 'dead' if row['attempts'] >= max_attempts else 'pending'
    retry_delay = min(86400, delay_seconds * backoff_factor ** min(max(0, row['attempts'] - 1), 20))
    conn.execute("""UPDATE jobs SET status=?,available_at=?,leased_until=NULL,last_error=?
                    WHERE id=?""", (status, now + retry_delay, str(error)[:400], job_id))
    conn.commit()


def stats(conn) -> dict:
    counts = {r['status']: r['c'] for r in conn.execute('SELECT status,COUNT(*) c FROM jobs GROUP BY status')}
    return {k: counts.get(k, 0) for k in ('pending', 'leased', 'done', 'dead')}


def diagnostics(conn, *, now=None) -> dict:
    """Privacy-safe numerical status only, never job payloads or feed URLs."""
    now = time.time() if now is None else now
    result = stats(conn)
    row = conn.execute(
        """SELECT
        SUM(CASE WHEN status='pending' AND available_at<=? THEN 1 ELSE 0 END) ready,
        SUM(CASE WHEN status='pending' AND available_at>? THEN 1 ELSE 0 END) delayed,
        SUM(CASE WHEN status='leased' AND leased_until<=? THEN 1 ELSE 0 END) expired_leases
        FROM jobs""",
        (now, now, now),
    ).fetchone()
    result.update({
        "ready": int(row["ready"] or 0),
        "delayed": int(row["delayed"] or 0),
        "expired_leases": int(row["expired_leases"] or 0),
    })
    return result
