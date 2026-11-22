# Source adapter modularization — first compatibility-preserving step

**Issue #14 / staged V3 proposal, not a public V3 release.**

The parser portion of `news_engine.sources` has been extracted into
`news_engine.feed_parsers`. The existing `news_engine.sources` module still
exports `FeedItem`, `parse_rss`, `parse_json_list`, `collect`, and the
HTTP security API unchanged, including their signatures.

The HTTPS/DNS safety code, pinned TLS connection, URL validation and HTTP
fetching are deliberately **not moved** in this PR. Existing security tests
patch `news_engine.sources.socket` and `news_engine.sources.ssl`; moving
these implementation details could silently invalidate tests or change
failure behavior. A dedicated later PR can consider the move after further
contract testing.

## Compatibility and verification

- Core remains dependency-free and network-opt-in.
- No schema migration, feed configuration migration, scheduler or private
  integration is added.
- RSS/Atom/JSON record bounds and DTD refusal are unchanged.
- `tests/test_parser_facade.py` checks legacy import identity and parsing
  behavior using synthetic payloads.
- Existing source safety regression tests must remain green.

Run `python -B -m unittest discover -s tests -v` and
`python -B tools/check_public_package.py` before merging.

## Português

O parsing de RSS, Atom e JSON foi movido para `feed_parsers.py`,
mantendo os símbolos públicos e comportamento anterior em `sources.py`.
A parte de HTTPS, DNS, TLS e bloqueios SSRF continua intacta. Não há
coleta automática, migração de banco ou dependência adicional. Antes da
integração, verificar todos os testes offline e a revisão de segurança.
