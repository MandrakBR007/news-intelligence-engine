# News Intelligence Engine — Public V3 Roadmap

**Status:** proposal for community discussion, **not a released V3**.  
**Languages:** English (this document) · [Português (Brasil)](ROADMAP_V3.pt-BR.md)  
**Last reviewed:** 2026-11-21

## Mission and scope

Evolve the standalone, local-first, open-source news research toolkit while preserving its transparent and testable foundations. V2 already has configurable RSS/Atom/flat JSON ingestion; an HTTPS-only bounded fetcher; conditional cache; exact and near-deduplication; SQLite item revisions and a job queue; a local-only dashboard/API; and optional, manually invoked generic topic classification via an external AI provider.

V3 is a **proposal backlog**, not a commitment to dates or new capabilities. The project does **not** claim validated financial forecasts or include automated financial execution. All example data must be synthetic or clearly permitted for redistribution.

## Priorities and community tasks

| Priority | Workstream | Initial issue | Expected outcome | Evidence required |
|---|---|---|---|---|
| P0 | Feed parsing resilience | [#6](https://github.com/MandrakBR007/news-intelligence-engine/issues/6) | Better handling of incomplete, malformed and unusually long RSS/Atom/JSON records | Offline synthetic tests; no weaker URL/security restrictions |
| P0 | Causal timestamp and revision provenance | [#7](https://github.com/MandrakBR007/news-intelligence-engine/issues/7) | Documented separation of source-reported publication and locally observed times; revision invariants | Reproducible fixtures for missing times, duplicates, changed content |
| P0 | Generic classifier evaluation | [#8](https://github.com/MandrakBR007/news-intelligence-engine/issues/8) | Transparent, bilingual synthetic benchmark for topic labels | Confusion counts, per-class metrics, stated uncertainty and limitations |
| P1 | Optional AI integration robustness | [#9](https://github.com/MandrakBR007/news-intelligence-engine/issues/9) | Stronger mocked provider contracts, privacy and failure handling | Offline test suite, no secrets in outputs, no real API calls in CI |
| P1 | Observability and diagnostics | Proposed: discuss first | Local health summary, bounded error categories, queue and feed status | Privacy-safe, deterministic output; no raw credentials, URL query secrets or sensitive responses |
| P2 | User experience and accessibility | Proposed: discuss first | Clearer bilingual setup guides, dashboard accessibility, error explanations | Manual accessibility review and documented offline tests |
| P2 | Developer experience and integration surfaces | Proposed: discuss first | Stable documented read-only local schemas and contribution examples | Backward compatibility plan, synthetic fixtures, versioning policy |

**Priority meaning:** P0 = security/correctness foundation; P1 = reliability and maintainability; P2 = usability/extension. Priority is *not* an implementation deadline.

## Proposed delivery stages (no promised dates)

**Stage A — Specifications and fixtures.** Discuss assumptions and write synthetic test cases. Establish present behavior before changing it.

**Stage B — Focused implementation.** Small Pull Requests by workstream; preserve old tests and add regression coverage. Keep external services optional and invoked explicitly.

**Stage C — Validation and documentation.** Offline CI, CodeQL review, code-owner/maintainer review, README updates in both languages, and clear limitations. Review feedback before marking a feature done.

## Definition of done

A task is complete only if:

1. The behavior is documented and scoped in an Issue or PR, including the risk and affected interfaces.
2. Synthetic, deterministic, network-free tests exercise normal, missing, malformed and repeated input as appropriate.
3. `python -B -m unittest discover -s tests -v` and `python -B tools/check_public_package.py` pass.
4. Required GitHub Actions checks pass, relevant CodeQL alerts are addressed, and reviewers can inspect the change.
5. No real keys, private data, proprietary logic, private endpoints or unlicensed third-party source content are introduced.
6. Documentation is updated in English and Brazilian Portuguese where user-facing behavior changes.

## Boundaries / non-goals

- No unattended external AI requests, embedded credentials, default background process or mandatory paid integration.
- No live brokerage, account, order, portfolio or trade-management features; no market-prediction performance claims.
- No fabricated source publication timestamp or retroactive representation of historical imports as live observations.
- No weakening HTTPS-only, DNS/IP controls, response-size constraints, loopback-only HTTP or minimal CLI output exposure.
- Security disclosures belong in [SECURITY.md](../SECURITY.md), not in public Issues.

## How to participate

Browse [Issues](https://github.com/MandrakBR007/news-intelligence-engine/issues) and select an open V3 task. For broader design questions, use [Discussions](https://github.com/MandrakBR007/news-intelligence-engine/discussions). Keep contributions small, link the relevant Issue and follow [CONTRIBUTING.md](../CONTRIBUTING.md). New ideas are welcome and can be added after review; this roadmap does not restrict creative suggestions.
