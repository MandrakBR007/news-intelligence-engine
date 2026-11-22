# Unicode Fingerprint Lab (experimental, offline only)

The existing production deduplication remains `v1_ascii`. This opt-in
laboratory provides `v2_unicode` for comparing tokenization and SimHash
without changing the pipeline or any stored fingerprints.

```python
from news_engine.fingerprint_versions import compare_versions
result = compare_versions([{"title": "Inflação e política monetária", "summary": ""}])
```

## Why versioning matters

The original `tokenize` splits Portuguese accented words incorrectly.
The new implementation uses Unicode NFKD normalization, case folding, and
combining-mark removal, then matches ASCII alphanumeric tokens. Examples:
`inflação -> inflacao`; `política -> politica`; `produção -> producao`.

**This changes approximate fingerprint bits.** Existing SQLite `simhash`
values were computed with the V1 tokenization. A V2 fingerprint must not
be compared as if it were a V1 fingerprint, or clustering can become
misleading.

The content identity `content_hash` remains **exactly the same for the
same input** in both version modes. This PR deliberately does not change
that function, SQLite schema, pipeline, classification, historical rows,
or the active deduplication mode.

## Evaluation / migration decision

The diagnostic reports per-item V1/V2 tokens and whether approximate
fingerprints change, **not** a claimed accuracy improvement. Before any
future activation, evaluate pair-labelled independent EN/PT news,
false-positive clusters, and migration/backfill strategy (or a separate V2
fingerprint column with an explicit version). Test collisions and replay
against previously stored items. Never silently reinterpret stored V1
SimHashes as V2.

```sh
python -B -m unittest discover -s tests -v
```

No network requests, data modifications, or external AI services are used.
