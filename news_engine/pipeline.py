"""Public news ingestion: feed -> deterministic dedup -> metadata -> SQLite.

No trading logic, model-based market claims, private data, or automatic API calls.
"""
from __future__ import annotations

from . import classify as classify_mod
from . import config as config_mod
from . import dedup, sources, store
from .util import iso_now, parse_dt


def _normalize(item):
    return item.as_dict() if isinstance(item, sources.FeedItem) else dict(item)


def process_items(conn, config: dict, raw) -> dict:
    items = [_normalize(x) for x in raw]
    existing = store.fingerprints(conn)
    dedup_cfg = config.get("dedup", {})
    hamming_threshold = int(dedup_cfg.get("hamming_threshold", 8))
    jaccard_threshold = float(dedup_cfg.get("jaccard_threshold", 0.75))
    counts = {"total": len(items), "new": 0, "near_duplicate": 0,
              "exact_duplicate": 0, "new_clusters": 0, "new_revisions": 0}
    for item in items:
        fingerprint = dedup.fingerprint(item)
        cluster, kind = dedup.assign_cluster(fingerprint, existing, hamming_threshold, jaccard_threshold)
        classified_at = iso_now()
        classification = classify_mod.classify(item, config.get("topics", []))
        first_seen_at = iso_now()
        published_at = parse_dt(item.get("published_at"))
        rec = {
            "content_hash": fingerprint["content_hash"], "cluster_id": cluster,
            "source": str(item.get("source") or "unknown"),
            "external_id": str(item.get("external_id") or fingerprint["content_hash"]),
            "title": item.get("title"), "summary": item.get("summary"),
            "link": item.get("link"), "published_at": published_at,
            "published_quality": "reported" if published_at else "missing_or_invalid",
            "first_seen_at": first_seen_at, "ingested_at": first_seen_at,
            "classified_at": classified_at,
            "topic": classification["topic"], "impact": classification["impact"],
            "confidence": classification["confidence"],
            "status": "new" if kind == "new" else ("near_duplicate" if kind == "near" else "duplicate"),
            "simhash": fingerprint["simhash"],
        }
        inserted = store.insert_item(conn, rec)
        if store.add_revision(conn, rec):
            counts["new_revisions"] += 1
        if inserted:
            if kind == "new":
                counts["new"] += 1
                counts["new_clusters"] += 1
            else:
                counts["near_duplicate"] += 1
            existing.append({"content_hash": rec["content_hash"], "simhash": rec["simhash"],
                             "cluster_id": cluster})
        else:
            counts["exact_duplicate"] += 1
    return counts


def run(config, data_dir, feed_loader=None) -> dict:
    db = config_mod.db_path(config, data_dir)
    conn = store.connect(db)
    store.init_db(conn)
    try:
        if feed_loader is not None:
            raw, errors = feed_loader(config), []
        else:
            raw, errors = sources.collect(
                config.get("feeds", []),
                cache_get=lambda url: store.get_cache(conn, url),
                cache_put=lambda url, meta: store.put_cache(conn, url, meta))
        counts = process_items(conn, config, raw)
        counts["errors"] = len(errors)
        return {"db_path": str(db), "counts": counts, "errors": errors, "stats": store.stats(conn)}
    finally:
        conn.close()
