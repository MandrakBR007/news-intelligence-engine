# Synthetic feed parser edge cases / Casos-limite dos parsers

This document records **current** parser behavior for Issue #6. All examples
are synthetic and the tests run offline without any credentials or network.

| Case / Caso | RSS 2.0 | Atom 1.0 | JSON list |
| --- | --- | --- | --- |
| Missing or blank title / Título ausente | Skip entry | Skip entry | Skip entry |
| Missing body / Corpo ausente | Empty summary | Empty summary | Empty summary |
| Invalid or missing publication date / Data ausente ou inválida | `None` | `None` | `None` |
| Repeated ID / ID repetido | Entries retained | Entries retained | Entries retained |
| Malformed document / Documento inválido | XML parsing exception | XML parsing exception | JSON parsing exception |
| Excessive payload / Resposta grande | Reject over 2,000,000 bytes | Same | Same |
| Many entries / Muitos itens | First 500 examined | First 500 examined | First 500 examined |

The parsers do not deduplicate repeated external identifiers. Deduplication
and source-ID revision tracking occur in the downstream pipeline and database;
they should not be conflated with parser behavior.

Large individual fields *within* the total 2 MB payload are currently
preserved (after text normalization). There is no independent per-field
truncation limit. Such a limit would be a behavioral change, not a property
this test suite claims.

The first 500 entries/records are examined. Skipped invalid entries do not
cause later entries beyond that boundary to be considered.

Security controls live in `news_engine/sources.py` and are unchanged here:
HTTPS-only external hosts, public DNS/IP checks, pinned connections, TLS
hostname validation, no redirects, and bounded responses. Parser-only tests
must never contact external feeds.

Run the regression suite:

```sh
python -B -m unittest discover -s tests -v
```

These fixtures are evidence of offline parsing behavior only. They do not
establish live feed quality or guarantee resilience to all malformed inputs.
