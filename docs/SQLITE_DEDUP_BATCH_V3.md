# SQLite batch and exact-first deduplication (V3)

## Scope

- The pipeline uses one SQLite savepoint around **each `process_items` batch**.
  Item and source-revision inserts are atomic: on failure, the entire batch
  rolls back rather than persisting partially written items.
- Independent calls to `store.insert_item` and `store.add_revision` keep
  their historical default auto-commit behavior. The batch opts out with
  `commit=False` and releases a savepoint once all records succeed.
- A savepoint within an existing caller transaction does **not** commit that
  transaction. Callers can still roll back their own work.
- An in-memory `content_hash -> cluster_id` index gives constant-time
  exact lookup within an ingestion run. Exact identity is always checked
  before any approximate matching; an earlier near match cannot hide a
  later exact identity.
- The original ordered, full-history SimHash/Jaccard approximate scan and
  clustering thresholds remain unchanged. No retention window is added.

## Behavioral change

If an exact content match occurs later than a near match in stored order,
it now wins. This intentionally corrects exact-vs-near precedence and may
change classification of that edge case compared to V2. All other
approximate comparisons retain their original order.

## Limits and measurements

Exact lookup is expected O(1) per item with the batch-maintained index,
but approximate comparisons still scan stored history. No numeric speedup
is claimed without a matched benchmark on representative data and hardware.
The full set of historic fingerprint rows is still loaded in memory.
No schema migration, token normalization, fingerprint version change,
dedup window, classifier change, or external feed operation is included.

A failed batch rolls back `items` and `item_revisions` writes made by
that batch. Feed HTTP cache updates may be committed independently during
fetch and are **not** part of this savepoint. SQLite crash durability still
uses the configured journal settings.

## Verification

```sh
python -B -m unittest discover -s tests -v
```

Offline tests cover exact-before-near precedence, full-batch rollback,
failed revision writes, nested caller-owned transactions, and standalone
store compatibility. Run CI and review local results before merging.
