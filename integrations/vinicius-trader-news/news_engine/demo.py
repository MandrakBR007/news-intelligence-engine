"""Offline news-ingestion demo with entirely synthetic content."""
from __future__ import annotations

from . import config as config_mod
from . import dashboard, pipeline, store

SYNTHETIC_ITEMS = [
    {"source": "demo", "external_id": "demo-1", "title": "Fictional quarterly inflation bulletin",
     "summary": "A synthetic economic prices report for testing ingestion, not a real release.",
     "link": "https://example.org/demo-1", "published_at": "2026-01-01T09:00:00+00:00"},
    {"source": "demo", "external_id": "demo-2", "title": "Example central bank interest policy update",
     "summary": "Synthetic policy announcement used as placeholder data.",
     "link": "https://example.org/demo-2", "published_at": "2026-01-01T10:00:00+00:00"},
    {"source": "demo", "external_id": "demo-3", "title": "Sample company revenue bulletin",
     "summary": "Synthetic business earnings summary with no connection to real issuers.",
     "link": "https://example.org/demo-3", "published_at": "2026-01-01T11:00:00+00:00"},
    {"source": "demo", "external_id": "demo-4", "title": "Fictional quarterly inflation bulletin",
     "summary": "A synthetic economic prices report for testing ingestion, not a real release.",
     "link": "https://example.org/demo-4", "published_at": "2026-01-01T12:00:00+00:00"},
]


def run(data_dir="data", config_path=None) -> dict:
    cfg = config_mod.load_config(config_path)
    cfg["feeds"] = []
    result = pipeline.run(cfg, data_dir, feed_loader=lambda _cfg: SYNTHETIC_ITEMS)
    conn = store.connect(result["db_path"])
    store.init_db(conn)
    out = dashboard.build(conn, config_mod.dashboard_path(cfg, data_dir))
    conn.close()
    result["dashboard"] = str(out)
    result["note"] = "Synthetic demo only. No network, no external data."
    return result
