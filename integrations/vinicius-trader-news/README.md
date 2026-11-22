# Vinicius Trader — Isolated News Integration (sanitized)

**Status:** self-contained, sanitized news-collection reference package; not deployed or automatically integrated.

Read the technical specification: [English](docs/INTEGRATION_TECHNICAL_EN.txt) · [Português (Brasil)](docs/INTEGRACAO_TECNICA_PTBR.txt).

**Contribution credit:** Vinicius Trader (supplied package and proposed improvements, as identified by the recipient). The original MIT copyright notice is retained in [LICENSE](LICENSE).

The provider-specific AI/LLM integration and credential setup documentation were removed. Source news database and generated cache/dashboard artifacts were not distributed. The remaining `/api` paths refer only to a local read-only HTTP interface.

**Offline demo:** `python -B -m news_engine demo --data-dir ./local_demo`.

**Do not extract over or auto-import into the main News Intelligence Engine.** This is a separate evaluation artifact.
