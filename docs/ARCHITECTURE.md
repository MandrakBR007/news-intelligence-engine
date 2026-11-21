# Architecture — public, local-first V2

```text
Configured public HTTPS feed (RSS / Atom / JSON)
           | validate URL -> resolve public DNS -> connect pinned IP (TLS)
           | enforce 2 MB / no redirect / If-None-Match
           v
      sources.collect()
           |
           v
    pipeline.process_items() ----> configurable keyword topics
           |                           (deterministic, non-predictive)
           v
    SQLite items / item_revisions / feed_cache
           |
           +---- dashboard.html / localhost-only read-only HTTP API
           |
           +---- optional manual `review` -> Gemini Decision 1

Optional task workflow:
  `enqueue-feeds` -> SQLite jobs -> `work-once` -> sources.collect()
       (retry with lease; no long-running service included)
```

## Causality model

`published_at` reflects a date reported by the source, **nullable** if missing/invalid. It is not a proof of first public availability. `first_seen_at` is the timestamp the local ingestion sees a new content hash. `ingested_at` and `classified_at` are local UTC timestamps. Historical imports should not be claimed to be prospective observations.

## Content history

`items` deduplicates identical content globally by hash and clusters near duplicates. `item_revisions` preserves distinct content versions for the same `(source, external_id)` with an observation timestamp. It is an append-only version log, not a complete diff engine. Feed URL `ETag`/`Last-Modified` and last check are stored separately.

## Queue

The SQLite queue uses `BEGIN IMMEDIATE` claims, leases, retry delays and dead states. Expired leases can be reclaimed. Job handlers must remain idempotent; public ingest uses content hashes. The included worker is deliberately single-job and explicitly invoked.

## Safety boundaries

There is no price feed, automatic market decision, scheduler, hidden cloud service or private configuration in this package. Generic example classifiers are intentionally simple and replaceable. No remote HTTP bind is allowed.
