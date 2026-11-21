"""Explicit, single-job worker. Reuses public ingestion; no scheduled process."""
from __future__ import annotations

from . import pipeline, queue, sources, store
from .util import iso_now


def enqueue_feeds(conn, config: dict, *, batch_id=None) -> int:
    batch_id = batch_id or iso_now()
    count = 0
    for feed in config.get("feeds", []):
        if feed.get("url"):
            name = feed.get("name", "feed")
            if queue.enqueue(conn, "fetch_feed", {"feed": feed}, f"{batch_id}:{name}:{feed['url']}"):
                count += 1
    return count


def work_once(conn, config: dict, *, fetcher=None, now=None) -> dict:
    job = queue.claim(conn, now=now)
    if job is None:
        return {"status": "empty"}
    try:
        if job["kind"] != "fetch_feed":
            raise ValueError("unrecognized job type")
        raw, errors = sources.collect(
            [job["payload"]["feed"]],
            cache_get=lambda url: store.get_cache(conn, url),
            cache_put=lambda url, meta: store.put_cache(conn, url, meta),
            fetcher=fetcher)
        if errors:
            raise ValueError(errors[0]["error"])
        counts = pipeline.process_items(conn, config, raw)
        queue.ack(conn, job["id"])
        return {"status": "done", "job_id": job["id"], "counts": counts}
    except Exception as exc:
        settings = config.get("queue", {})
        queue.fail(conn, job["id"], f"{type(exc).__name__}: {exc}",
                   max_attempts=int(settings.get("max_attempts", 3)),
                   delay_seconds=int(settings.get("retry_delay_seconds", 120)),
                   backoff_factor=int(settings.get("retry_backoff_factor", 1)), now=now)
        return {"status": "retry_or_dead", "job_id": job["id"], "error": type(exc).__name__}
