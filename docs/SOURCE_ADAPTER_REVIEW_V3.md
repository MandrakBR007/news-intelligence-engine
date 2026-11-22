# V3 source-adapter separation: security contracts first

**Issue #14 — assessment / preparatory tests, not a module migration.**

The current `news_engine.sources` implements both input parsers (RSS 2.0, Atom 1.0 and flat JSON) and outbound HTTPS safety. Its size is not evidence of a defect. Splitting it without guarding security boundaries could introduce SSRF or import regressions.

## Candidate boundaries (proposal only)

- `fetch_security`: HTTPS URL validation, public-only DNS resolution, validated-IP TCP connection, original hostname TLS verification, refusal of redirects, bounded response sizes.
- `feed_parsers`: RSS, Atom and configurable JSON parsing, explicit record bounds and refusal of DTD/entity declarations.
- `sources`: stable public compatibility façade and explicit `collect` orchestration.

Do not remove public `news_engine.sources` exports without a versioned compatibility plan. Existing tests patch `news_engine.sources.socket.getaddrinfo`: import paths and test injection points must remain compatible or be intentionally migrated with explicit review.

## Offline regression coverage

The new `tests/test_source_contracts.py` tests:
- rejected schemes, local/IP literals, userinfo, fragments, unusual ports and malformed URLs
- refusal of a DNS answer that mixes public and private addresses
- a pinned connection to a validated IP and TLS verification against the original hostname
- raw socket cleanup on TLS errors
- redirects and oversized responses rejected, with connection cleanup
- conditional HTTP 304 behavior
- DTD/entity rejection and parser basics
- existence of existing public compatibility imports

These tests use mocks and synthetic text only. They do not test the real network or prove the absence of all SSRF variants. Any future module split must demonstrate identical externally observable behavior and pass the existing offline suite.

## Risks to evaluate before refactoring

Check failure handling for malformed DNS/TLS results, response content-type and size, URL canonicalization, shared host rate limits, and request timeouts. No relaxations to HTTPS-only and loopback-only restrictions. No automatic background tasks or external AI calls.

## Português

Esta etapa prepara a separação dos adaptadores sem mudar os módulos em produção. Testamos URL, DNS público, conexão por IP validado, hostname original no TLS, redirecionamento, limite de resposta, XML e compatibilidade de imports. A divisão em submódulos é apenas proposta; o comportamento público permanece igual.
