# News Intelligence Engine — Public V2

**Languages:** English (this page) · [Português (Brasil)](README.pt-BR.md)

A **local-first, extensible toolkit for public financial news and economic-event research**. It collects *user-configured* feeds, groups duplicates, keeps event revisions and observation timestamps, and provides a local dashboard. Contributions are welcome via Issues, Discussions and Pull Requests after the repository owner enables them.

**Scope:** this public edition demonstrates generic data engineering, not price prediction. Keyword-based categories and AI output are research metadata, not validated forecasts. No live market integration or automated financial actions are included.

## Public V3 roadmap (proposed)

The next development priorities are documented in the [V3 Roadmap (English)](docs/ROADMAP_V3.md) and [Roteiro V3 (Português)](docs/ROADMAP_V3.pt-BR.md). These are **proposals, not released features**. Community-ready tasks are tracked in [Issues #6–#9](https://github.com/MandrakBR007/news-intelligence-engine/issues?q=is%3Aissue+is%3Aopen+%22%5BV3%5D%22). New ideas are welcome via [Discussions](https://github.com/MandrakBR007/news-intelligence-engine/discussions).

## Features

- RSS 2.0, Atom 1.0 and configurable flat JSON feeds.
- Outbound HTTPS on port 443 only; DNS results must be public, connections are pinned to validated IPs, redirects are refused, and feed size is capped at 2 MB.
- Conditional requests using `ETag` and `Last-Modified`; unchanged (`304`) responses do not create events.
- Exact deduplication, near-duplicate clusters, and versioned content for the same source ID.
- UTC metadata: `published_at` (nullable), `first_seen_at`, `ingested_at`, `classified_at`, and a publication quality flag. Missing source timestamps are **never** replaced by the current time.
- Local SQLite queue with leases, retry/dead state and an explicit one-job worker.
- Static HTML dashboard and an HTTP interface restricted to the loopback address.
- Optional **Gemini Decision 1** example for *broad topic classification only*, invoked explicitly with a CLI command; no automatic API charges.
- Offline synthetic examples; Python standard library for the core.

## Optional local installation (V2-compatible)

Python 3.11+ can install the core as a local package with no mandatory runtime dependencies:

```bash
python -m pip install -e .
news-engine demo --data-dir data
```

The original `python -B -m news_engine` commands remain supported. Optional AI support is `pip install -e ".[gemini]"` (only used for explicit `review`); developer diagnostics use `pip install -e ".[dev]"`. See [engineering notes](docs/ENGINEERING_V3.md). Installation does not start network collection or a background process.

## Experimental deduplication benchmark (V3 proposal)

An offline, synthetic [pairwise benchmark](docs/DEDUP_BENCHMARK.md) covers near duplicates and false merges. Run `python -m tools.benchmark_dedup` from the repository root. The new optional `dedup.compare_stored_tokens` setting enables Jaccard comparison with existing stored articles; it is **off by default** and changes no historical cluster IDs. Do not interpret synthetic metrics as real-world accuracy.

## Requirements and offline quick start

Python **3.11+** is recommended (the core uses the standard library).

```bash
python -B -m unittest discover -s tests -v
python -B -m news_engine demo --data-dir data
python -B -m news_engine stats --data-dir data
python -B -m news_engine dashboard --data-dir data
```

The demo makes **zero network requests**. The `data/` directory is local and ignored by Git.

## Public-feed collection (explicit network opt-in)

1. Copy `examples/config.example.json` to `config.json`.
2. Replace `https://example.org/news.xml` with a permitted, public HTTPS feed you control or have permission to access.
3. Run:

```bash
python -B -m news_engine collect --config config.json --data-dir data
python -B -m news_engine serve --config config.json --data-dir data
```

Local UI: `http://127.0.0.1:8080/`; JSON endpoints: `/api/stats`, `/api/items`.

**Queue option:**

```bash
python -B -m news_engine enqueue-feeds --config config.json --batch-id example-round-1 --data-dir data
python -B -m news_engine work-once --config config.json --data-dir data
python -B -m news_engine queue-stats --data-dir data
```

These commands are *manual*. There is no included scheduler, daemon or automatic startup. `work-once` processes at most one job. For another pass, use a new batch ID.

## Optional Gemini Decision 1 (explicit network opt-in)

This sends the selected news title/summary to Google's API. It requires your own API key and optional package. It is **not** called during `demo`, `collect`, or `work-once`.

```bash
python -m pip install -r requirements-optional.txt
# Set GEMINI_API_KEY through your shell/environment, never in repository files.
# In config.json, set gemini.enabled to true.
python -B -m news_engine review --config config.json --item-id 1 --data-dir data
```

The public example uses `client.decisions.create(model="gemini-decision-1", ...)` with **generic choices** (`economy`, `policy`, `business`, `other`) and a text-sufficiency check. Its confidence values must not be treated as measured predictive accuracy. The SDK and real API were **not tested** as part of the offline validation package.

## Project structure

```text
news_engine/  Python modules and CLI
examples/     Synthetic feed, configuration and demo
tests/       Offline tests
docs/        Architecture, usage and security notes
.github/     Pull Request / Issue templates and tests workflow
```

## Privacy and security

This package ships with no real feed contents, accounts, API keys, databases, logs, or deployment configs. The outbound fetcher refuses HTTP, private IPs, IP literals, redirects and non-443 ports. It does not follow redirects. Only specify sources you are permitted to read or redistribute metadata from. The local web interface is intentionally unauthenticated and **cannot bind to a remote address**.

See [SECURITY.md](SECURITY.md) and [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md).

## How to contribute

Start with a [bug report](.github/ISSUE_TEMPLATE/bug_report.md), a [feature request](.github/ISSUE_TEMPLATE/feature_request.md), or a focused pull request. Reproduce an issue using synthetic data; add offline tests; and explain what changed. See [CONTRIBUTING.md](CONTRIBUTING.md) for the English guide or [CONTRIBUTING.pt-BR.md](CONTRIBUTING.pt-BR.md) for Portuguese.

**Security:** Never post API keys or sensitive details in public issues. Read [SECURITY.md](SECURITY.md) ([Português](SECURITY.pt-BR.md)) for private vulnerability reports.

## Community and licensing

This repository is licensed under the [MIT License](LICENSE). Please read the [Code of Conduct](CODE_OF_CONDUCT.md). Contributions are reviewed by maintainers before merging. The public package does not claim validated financial forecasts or unattended live integrations.
