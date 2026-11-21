# V3 engineering foundations (proposal / review branch)

This document describes additive work toward the proposed V3 roadmap. It is not a V3 release.

## Local Python packaging

Python 3.11+:

```bash
python -m pip install -e .
news-engine demo --data-dir data
python -B -m news_engine demo --data-dir data
```

Both commands explicitly run the same existing CLI. No network collection, AI review or daemon starts during installation. The core has **zero mandatory runtime dependencies**. Optional integrations and developer tools are explicit:

```bash
python -m pip install -e ".[gemini]"
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q --cov=news_engine --cov-report=term-missing
python -m mypy news_engine
```

Ruff uses a minimal correctness-rule baseline initially. MyPy is diagnostic and must be reviewed before becoming a blocking gate. No coverage threshold is imposed in this phase.

## Deterministic retry backoff

Existing default is unchanged: `retry_backoff_factor=1` means a fixed `retry_delay_seconds`. Setting `retry_backoff_factor=2` uses exponential delays relative to the number of attempts. The delay is bounded to 86400 seconds to prevent unbounded waiting; jobs reaching `max_attempts` still enter the existing `dead` state. No process is started automatically. This configuration does not replace per-source rate limits.

## Boundaries

The public package remains local-first, offline-testable and manually invoked. Do not expose a remote HTTP server, embed keys, add private endpoints, enable unattended external requests or claim predictive trading performance. Any Docker support should be opt-in, local-only, and separately security-reviewed. Keep compatibility for existing `python -m news_engine` users.

## Next review items

- Benchmark existing SimHash/Jaccard grouping with synthetic near-duplicate and false-positive fixtures before adding embeddings.
- Test Gemini malformed/missing responses, explicit consent and privacy with mocked providers.
- Consider a feed adapter split only after import-compatibility and SSRF-regression tests.
- Evaluate per-source cooldowns, observability and graceful cancellation without turning the worker into a default background service.
- Compare `_v2` tests to older tests before consolidating; suffixes alone do not mean duplicates.
