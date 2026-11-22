# Local health diagnostics and optional AI resilience

This PR adds **read-only, privacy-minimized** diagnostics and controlled
failure handling for an **explicit, opt-in** external AI review.

## Local health

From the repository root:

```sh
python -B -m news_engine health --data-dir data
```

When the local loopback server is **explicitly** started, it also exposes
`GET /api/health` on the same loopback-only address. No remote bind or
automatic network request is enabled.

The response is an allowlisted summary of item counts, cache entry counts,
non-200/304 cache statuses, queue state, and most recent recorded check/item
observation times. It does not contain feed URLs, ETags, source identifiers,
job payloads, exception details or API tokens. A returned `status: "ok"`
means the local diagnostic query completed; it **does not** attest that
sources, feeds, or external services are operational.

## Optional Gemini review

The manually invoked `review` command now uses a bounded 15-second
(default) API timeout and returns a generic `external_review_failed`
result for SDK request exceptions. No exception string is returned to the
CLI. The existing mock client interface and successful response shape are
unchanged. Timeout values must be integers in [1000, 120000] milliseconds.

Review remains disabled unless explicitly requested under the existing
configuration; no new background worker, telemetry, or API request is added.
No review results are automatically persisted or reused. Storing AI reviews
and implementing `--force` must be designed separately with explicit
cache keys, privacy controls and testable invalidation semantics.

## Verification

```sh
python -B -m unittest discover -s tests -v
```

All fixtures are local and synthetic. Test external SDK behavior separately
in a controlled opt-in environment before making availability claims.
