# Timestamp provenance and revision invariants / Origem dos horários e revisões (V3)

This page documents the **current behavior**, not a proposed schema change.
Tests in `tests/test_timestamp_provenance.py` use synthetic inputs and a mocked
observation clock; no historical network ingestion is claimed.

## Field definitions / Definições

| SQLite field | Meaning / Significado | Origin / Origem |
| --- | --- | --- |
| `items.published_at` | Source-reported publication time, normalized to ISO UTC; null when missing or invalid / Publicação informada pela fonte; nula se ausente ou inválida | Feed record via `parse_dt` |
| `items.published_quality` | `reported` when a timestamp parses, otherwise `missing_or_invalid` / Indica se a data pôde ser interpretada | Ingestion pipeline |
| `items.first_seen_at` | Time the public pipeline first stores this distinct **content hash** / Primeira observação da versão de conteúdo armazenada | Local `iso_now()` |
| `items.ingested_at` | Currently set equal to `first_seen_at` on insertion / Atualmente igual ao primeiro registro | Local pipeline |
| `items.classified_at` | Time the topic classification code was invoked during the insertion attempt / Momento da classificação | Local `iso_now()` |
| `item_revisions.observed_at` | Observation time of the **first stored** distinct `(source, external_id, content_hash)` revision / Primeira observação dessa revisão específica | Copied from `first_seen_at` |

**Important limitations / Limitações:** `first_seen_at` is *not* a verified
first appearance on the internet or at the publisher. It is the local
pipeline's observation at ingest. A timestamp with no timezone is currently
assumed to be UTC by `parse_dt`, not independently verified. The simple
`published_quality` flag does not distinguish timezone-assumed values from
explicitly timezone-qualified values.

The pipeline invokes `iso_now()` for `classified_at` before invoking it for
`first_seen_at`; these fields are close but not necessarily identical. The
current design does not separately measure classification duration.

## Synthetic example / Exemplo sintético

A feed says `2026-04-03T09:45:00-03:00` and the pipeline observes it at
`2026-04-03T18:00:00+00:00`. The stored `published_at` is
`2026-04-03T12:45:00+00:00`; `first_seen_at` and `ingested_at` are
the local observation time. Publication time is **not** inferred from the
observation time if the feed date is absent or invalid.

If the same publisher and external ID later submit a changed headline,
a new `item_revisions` row is stored for its new content hash. An exact
repeat of a previously stored version does not overwrite its earlier
`observed_at`. Distinct publishers with the same exact content can share
one `items` row while retaining independent revision identities in
`item_revisions`.

## Ordering, uniqueness and migration

- `items.content_hash` is globally unique: `items` holds a representative
  of each unique content version, not every sighting by every publisher.
- `item_revisions` is unique on `(source,external_id,content_hash)`.
  Its `observed_at` records only the first observation of that version.
- SQL rows have no guaranteed implicit order. The tests use `ORDER BY id ASC`
  to assert insertion order; chronological reporting must request explicit
  ordering according to its intended timestamp.
- This PR **does not** change the database schema, backfill old rows, or
  change public interfaces. Any future stronger observation history or
  timezone-quality distinctions require a separately reviewed schema and
  backward-compatibility plan.

Run offline: `python -B -m unittest discover -s tests -v`.
