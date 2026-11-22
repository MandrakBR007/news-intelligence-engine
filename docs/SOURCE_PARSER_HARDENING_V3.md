# Source and parser hardening (V3)

This change strengthens the **explicit, opt-in** public feed collector. No feed is
fetched automatically. HTTPS-only, no redirects, public-only DNS resolution,
TLS hostname validation, and bounded response reads remain mandatory.

## HTTP behavior

- Reject malformed `Content-Length` with `FeedSecurityError`; never trust the
  advertised size instead of the bounded body read.
- Permit fallback across **previously vetted public** DNS addresses for
  connection/transport errors only. A failed TLS authentication or an actual
  HTTP response does **not** trigger another IP attempt.
- Reject control characters, non-ASCII, and oversized (>200-character)
  ETag/Last-Modified validator values both on receipt and before request
  reuse. Unsafe values become missing metadata; prior cache rows are still
  guarded when reused. No raw validator values appear in public diagnostics.

## Parser behavior

- Reject non-object/non-array JSON roots with a predictable `ValueError`.
- Ignore nested/list/boolean JSON field values instead of stringifying them
  into titles, summaries, identifiers or date fields.
- Support `dc:date` and `content:encoded` as fallbacks when normal RSS
  publication/summary fields are absent or empty. Existing field precedence
  is preserved.

## Intentional exclusions

There is **no silent per-field truncation** in this PR. The same title and
summary feed deduplication hashes and SQLite revisions; truncation could cause
content aliasing and needs an explicit, separately tested data contract.
The raw full-feed payload cap (2 MB) and 500-item cap remain unchanged.

No pipeline, database schema, dedup algorithm, classifier or publication-time
quality migration is included. The lab still needs real-world authorized feed
testing. All regression fixtures are synthetic and make no network calls.

## Verify

From the repository root:

```sh
python -B -m unittest discover -s tests -v
```

CI checks must be green before merge.
