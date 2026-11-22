# Temporal provenance integrity V3 (Issue #7)

This PR strengthens **new** observations without backfilling old SQLite rows or
changing the existing `parse_dt(value) -> str | None` API.

## Observation chronology

Within each new pipeline item:

1. `first_seen_at` is sampled before classification and also stored as
   `ingested_at` for backward compatibility with existing metadata.
2. The publication timestamp is normalized independently of observation.
3. The topic classification is calculated.
4. `classified_at` is sampled after classification.

This fixes the earlier inverted clock order, but **does not** claim that
`ingested_at` is the physical SQLite commit time. Accurate commit-time
provenance would require a separate schema/event contract.

## Publication timestamp quality

The new helper `parse_dt_details(value, observed_at=None)` returns a normalized
UTC timestamp together with one of:

- `reported_tz`: source supplied an explicit timezone or offset
- `reported_naive_utc`: source supplied a timezone-less timestamp, interpreted
  as UTC as in the existing behavior
- `future_suspect`: publication time is more than 24 hours after the supplied
  observation time; it is preserved, not automatically discarded
- `missing_or_invalid`: missing or unparseable timestamp; publication time
  remains `NULL`

The 24-hour future tolerance is a conservative diagnostic heuristic, **not** a
claim that publication is definitively false. `parse_dt` remains a
compatibility wrapper that returns only `str | None`.

Parsers now propagate their source timezone quality on the optional
`FeedItem.published_quality` field, because UTC normalization alone loses
whether the original timestamp was naive. The pipeline respects supported
parser-provided quality, but `future_suspect` determined at observation takes
precedence. Generic already-normalized dict inputs without prior quality have
limited provenance (their offset is explicit in the normalized value).

## Compatibility and limits

- The existing SQLite `items.published_quality` column is reused. No table
  rewrite, migration, or historical correction occurs; older `reported`
  values remain unchanged.
- No change to source ordering, deduplication, fingerprints, titles, summaries,
  queue, or external-network behavior.
- New timestamp-quality strings may require downstream consumers that assumed
  `published_quality == "reported"` to accept the more specific values.
- All regression data is synthetic and deterministic. No external feeds or
  remote services are used.

Verify from the repository root:

```sh
python -B -m unittest discover -s tests -v
```

Review GitHub CI before merging.
