# Security model — public V2

## Network

- **Offline by default:** tests, demo, dashboard, stats and queue status make no external requests.
- **Collector opt-in:** `collect` and `work-once` contact only user-configured HTTPS feeds; no auto-start.
- The fetcher rejects `file://`, HTTP, user-info, explicit non-443 ports, IP literals, private/reserved DNS addresses, unsafe hostnames and redirects.
- Each resolved IP is checked for public/global scope. The TLS connection is explicitly established to a validated IP while verifying the certificate for the original DNS hostname (reduces DNS-rebinding risk). DNS failure fails closed.
- Response bodies are limited to 2 MB, and connection timeouts are enforced. Do not use untrusted feeds with unlimited data or content rights.
- No proxy support and no automatic redirect following. Sources that require these are intentionally incompatible.

## Storage and timestamps

The data directory is local. The source publication timestamp can be null; `first_seen_at` and `ingested_at` are distinct. This does not prove a data item was delivered at the exact time the publisher posted it. The queue and revision log use SQLite; make backups before changing schemas.

## Local dashboard

The HTTP API is unauthenticated and refuses any bind that is not a loopback IP. It implements GET only. The dashboard escapes untrusted content. Do not expose it through public reverse proxies without separate authentication.

## Gemini Decision 1

- Disabled by default and never invoked by collection or the queue worker.
- Only `review` explicitly submits text to Google's API with a user-supplied key.
- It sends item title/summary (truncated), not local database files.
- The public example only classifies a broad topic and sufficiency. Provider scores are not validation of predictive accuracy.
- Online correctness, pricing and provider availability are outside the offline test suite.

## Supply chain and contributions

Pull-request CI runs with read-only repository permissions, no secrets, and no execution of downloaded project-specific scripts. Keep external contributions independent of deployment systems. Report security issues privately using `SECURITY.md`.

## Residual risks

No software is completely free of bugs. This is not a hardened multi-user service; it is a local development toolkit. Large or specially crafted XML/JSON inputs may still require additional parser hardening before untrusted production-scale use.
