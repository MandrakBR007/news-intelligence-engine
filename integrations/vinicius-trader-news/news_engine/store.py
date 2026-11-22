"""Small SQLite store. Research metadata and event versions are local only."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content_hash TEXT UNIQUE,
  cluster_id TEXT,
  source TEXT,
  external_id TEXT,
  title TEXT,
  summary TEXT,
  link TEXT,
  published_at TEXT,
  first_seen_at TEXT,
  topic TEXT,
  impact TEXT,
  confidence REAL,
  status TEXT,
  simhash INTEGER,
  published_quality TEXT,
  ingested_at TEXT,
  classified_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_items_cluster ON items(cluster_id);
CREATE INDEX IF NOT EXISTS idx_items_published ON items(published_at);
CREATE TABLE IF NOT EXISTS item_revisions (
 id INTEGER PRIMARY KEY,
 source TEXT NOT NULL, external_id TEXT NOT NULL,
 content_hash TEXT NOT NULL, title TEXT, summary TEXT,
 observed_at TEXT NOT NULL,
 UNIQUE(source,external_id,content_hash)
);
CREATE TABLE IF NOT EXISTS feed_cache (
 url TEXT PRIMARY KEY, etag TEXT, last_modified TEXT,
 last_status INTEGER, checked_at TEXT
);
CREATE TABLE IF NOT EXISTS jobs (
 id INTEGER PRIMARY KEY,
 kind TEXT NOT NULL,
 payload TEXT NOT NULL,
 dedup_key TEXT NOT NULL UNIQUE,
 status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0,
 available_at REAL NOT NULL,
 leased_until REAL,
 last_error TEXT,
 created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_ready ON jobs(status,available_at);
CREATE TABLE IF NOT EXISTS feed_cooldowns (
  source_key TEXT PRIMARY KEY,
  next_allowed_at REAL NOT NULL
);
"""


def connect(path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_db(conn) -> None:
    # For compatibility with the first public demo's SQLite schema.
    conn.executescript(SCHEMA)
    columns = {r["name"] for r in conn.execute("PRAGMA table_info(items)")}
    for name in ("published_quality", "ingested_at", "classified_at"):
        if name not in columns:
            conn.execute(f"ALTER TABLE items ADD COLUMN {name} TEXT")
    conn.commit()


def _signed64(value):
    if value is None:
        return None
    value = int(value)
    return value - (1 << 64) if value >= (1 << 63) else value


def insert_item(conn, rec: dict, *, commit: bool = True) -> int:
    simhash = _signed64(rec.get("simhash"))
    cur = conn.execute(
        """INSERT OR IGNORE INTO items(content_hash,cluster_id,source,external_id,title,summary,
           link,published_at,first_seen_at,topic,impact,confidence,status,simhash,
           published_quality,ingested_at,classified_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (rec.get("content_hash"), rec.get("cluster_id"), rec.get("source"),
         rec.get("external_id"), rec.get("title"), rec.get("summary"), rec.get("link"),
         rec.get("published_at"), rec.get("first_seen_at"), rec.get("topic"),
         rec.get("impact"), rec.get("confidence"), rec.get("status"), simhash,
         rec.get("published_quality"), rec.get("ingested_at"), rec.get("classified_at")))
    if commit:
        conn.commit()
    return cur.rowcount


def add_revision(conn, rec: dict, *, commit: bool = True) -> bool:
    """Keep each source ID's distinct content version, even across repeated runs."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO item_revisions
           (source,external_id,content_hash,title,summary,observed_at) VALUES(?,?,?,?,?,?)""",
        (rec.get("source", ""), rec.get("external_id", ""), rec["content_hash"],
         rec.get("title"), rec.get("summary"), rec.get("first_seen_at")))
    if commit:
        conn.commit()
    return bool(cur.rowcount)


def get_cache(conn, url: str) -> dict:
    row = conn.execute("SELECT etag,last_modified FROM feed_cache WHERE url=?", (url,)).fetchone()
    return dict(row) if row else {}


def put_cache(conn, url: str, meta: dict) -> None:
    from .util import iso_now
    previous = get_cache(conn, url)
    etag = meta.get("etag") or previous.get("etag")
    modified = meta.get("last_modified") or previous.get("last_modified")
    conn.execute("""INSERT INTO feed_cache(url,etag,last_modified,last_status,checked_at)
                    VALUES(?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET
                    etag=excluded.etag,last_modified=excluded.last_modified,
                    last_status=excluded.last_status,checked_at=excluded.checked_at""",
                 (url, etag, modified, meta.get("status"), iso_now()))
    conn.commit()


def all_items(conn, limit: int = 1000) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM items ORDER BY id DESC LIMIT ?", (limit,))]


def dashboard_items(conn, limit: int = 200) -> list[dict]:
    return [dict(row) for row in conn.execute(
        """SELECT * FROM items
           ORDER BY julianday(CASE
             WHEN published_quality='future_suspect' THEN first_seen_at
             ELSE COALESCE(published_at,first_seen_at)
           END) DESC, id DESC LIMIT ?""",
        (limit,),
    )]


def get_item(conn, item_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return dict(row) if row else None


def list_items(conn, limit: int = 200) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT published_at,source,title,topic,impact,cluster_id,status FROM items "
        "ORDER BY id DESC LIMIT ?", (limit,))]


def topic_observations(conn, since: str, until: str) -> list[dict]:
    """Return recent per-feed topic observations, including exact duplicate revisions."""
    return [dict(row) for row in conn.execute(
        """SELECT topic,source,observed_at,title,impact,link FROM (
             SELECT topic,source,first_seen_at AS observed_at,title,impact,link FROM items
             UNION ALL
             SELECT items.topic,item_revisions.source,item_revisions.observed_at,
                    item_revisions.title,items.impact,NULL
             FROM item_revisions
             JOIN items ON items.content_hash=item_revisions.content_hash
           )
           WHERE topic IS NOT NULL AND source IS NOT NULL AND TRIM(source)!=''
             AND observed_at IS NOT NULL
             AND julianday(observed_at)>julianday(?)
             AND julianday(observed_at)<=julianday(?)
           ORDER BY topic,source,observed_at""",
        (since, until),
    )]


def distinct_source_count(conn) -> int:
    row = conn.execute(
        """SELECT COUNT(DISTINCT source) AS count FROM (
             SELECT source FROM items
             UNION
             SELECT source FROM item_revisions
           ) WHERE source IS NOT NULL AND TRIM(source)!=''"""
    ).fetchone()
    return int(row["count"])


def recent_news_count(conn, since: str, until: str) -> int:
    row = conn.execute(
        """SELECT COUNT(DISTINCT content_hash) AS count FROM (
             SELECT content_hash,first_seen_at AS observed_at FROM items
             UNION ALL
             SELECT content_hash,observed_at FROM item_revisions
           )
           WHERE observed_at IS NOT NULL
             AND julianday(observed_at)>julianday(?)
             AND julianday(observed_at)<=julianday(?)""",
        (since, until),
    ).fetchone()
    return int(row["count"])


def fingerprints(conn, *, include_tokens: bool = False) -> list[dict]:
    """Read old fingerprint fields; optionally reconstruct Jaccard tokens from local text.

    No schema changes or external calls. The default preserves V2 behavior.
    """
    if not include_tokens:
        return [dict(r) for r in conn.execute("SELECT content_hash,simhash,cluster_id FROM items")]
    from .util import tokenize
    rows = conn.execute("SELECT content_hash,simhash,cluster_id,title,summary FROM items")
    return [
        {"content_hash": row["content_hash"], "simhash": row["simhash"],
         "cluster_id": row["cluster_id"],
         "tokens": tokenize((row["title"] or "") + " " + (row["summary"] or ""))}
        for row in rows
    ]


def stats(conn) -> dict:
    total = conn.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    clusters = conn.execute("SELECT COUNT(DISTINCT cluster_id) c FROM items").fetchone()["c"]
    revisions = conn.execute("SELECT COUNT(*) c FROM item_revisions").fetchone()["c"]
    missing = conn.execute("SELECT COUNT(*) c FROM items WHERE published_at IS NULL").fetchone()["c"]
    topics = [dict(r) for r in conn.execute("SELECT topic, COUNT(*) c FROM items GROUP BY topic ORDER BY c DESC")]
    impacts = [dict(r) for r in conn.execute("SELECT impact, COUNT(*) c FROM items GROUP BY impact ORDER BY c DESC")]
    sources = [dict(r) for r in conn.execute("SELECT source, COUNT(*) c FROM items GROUP BY source ORDER BY c DESC")]
    return {"total": total, "clusters": clusters, "revisions": revisions,
            "unknown_publication_time": missing, "topics": topics, "impacts": impacts, "sources": sources}
