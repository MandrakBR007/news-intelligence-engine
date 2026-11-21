# Synthetic near-duplicate benchmark / Benchmark sintético

**Status:** diagnostic only. Issue #12. No production thresholds are changed.

Run from the repository root:

```bash
python -m tools.benchmark_dedup
python -B -m unittest discover -s tests -v
```

The benchmark uses eight *invented* labelled text pairs (three duplicate, five negative), designed to expose false merges involving entities, opposite decisions and shared templates. It returns TP/FP/TN/FN, precision and recall, per-pair Hamming distances and Jaccard similarities. These fixtures are not representative of real news distribution; no external validation, trained embeddings or real feeds are involved. Do not interpret the metrics as production accuracy or optimize thresholds on these eight pairs alone.

**New opt-in setting:** `"dedup": {"compare_stored_tokens": true}`. Existing database rows already store title and summary. When enabled, tokens are reconstructed from those local fields to permit Jaccard comparison against previously ingested rows. There is **no migration**, external service or background process. **Default is false** to preserve existing clustering decisions. This option may change assignments for near matches: validate on a copied database, not live data.

Important boundaries:
- Existing SimHash/Hamming and exact hash matching remain unchanged.
- Jaccard uses an unordered token set, so shared vocabulary can produce false positives, especially in similar templates or opposing events.
- The first matching existing row selects the cluster; the assignment is order-sensitive. Pairwise benchmark results do not establish correctness for full incremental clustering.
- Re-running on an existing database does not rewrite historical cluster IDs. There is no retroactive reclustering.
- More synthetic fixtures, bilingual evaluation and a separate shadow evaluation are required before default changes.

## Português

O benchmark utiliza oito pares **totalmente sintéticos** com rótulos assumidos (três positivos, cinco negativos), medindo VP/FP/VN/FN, precisão e revocação. Os números **não são acurácia real**. A opção `compare_stored_tokens` é desativada por padrão, reconstrói tokens de título/resumo já armazenados e permite o uso de Jaccard contra registros persistidos, sem migração de banco. Ative apenas em uma cópia para avaliação; regras antigas e IDs históricos permanecem inalterados.
