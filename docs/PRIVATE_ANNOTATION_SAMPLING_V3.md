# Private, human-labelled news sampling (offline)

The PR adds a **read-only local** sampling tool for building a human-annotated
evaluation set for the existing three topic engines. It DOES NOT collect or
download news, verify whether news is genuine, assign gold labels, train a
model, use Gemini, or change the production classifier.

## Preparing an evaluation sample

Only after you have legally collected genuine, relevant feed items in your
local SQLite `data/news.db`, run these commands from the repository root:

```powershell
python -B -m tools.export_annotation_sample --db data/news.db --output data/manual_labels_001.json --limit 40 --seed 42
```

The output contains *unredacted article titles and summaries*. Keep it in an
ignored local directory, such as `data/`. Never commit/push/upload the
annotation file or paste private articles into public issues or PRs. The tool
refuses to overwrite an existing annotation file.

Cases are sampled uniformly from the **first stored item in each cluster**,
rather than from every repeated article, with a reproducible random seed.
This reduces repeated-near-duplicate contamination, but selection remains
based on the available SQLite collection. It does not guarantee language,
publisher or class balance; it loads eligible cluster candidates into memory.
A flawed/biased collection is still flawed. For final evaluation, record
dates, publication sources and inclusion criteria *privately* and consider
separate temporal and publisher-disjoint held-out samples.

The generated JSON has this structure:

```json
[
  {
    "id": "local-0001",
    "language": "",
    "title": "<to be filled from your local database>",
    "summary": "<to be filled from your local database>",
    "expected_topic": ""
  }
]
```

Language and reference topic are blank **by design**. A reviewer must
independently label `language` as `en` or `pt-BR`, and `expected_topic`
as `economic_data`, `monetary_policy`, `business` or `general`. A second
reviewer for a subset is preferable; track disagreements separately. Do NOT
copy labels from any classification model.

Once independently annotated, run:

```powershell
python -B -m tools.evaluate_labelled_news --input data/manual_labels_001.json
```

This existing evaluator prints **aggregate metrics only** and never outputs
unredacted article content. An empty sample is not accepted for evaluation;
collect data first. The sampler itself does not need or use a network
connection and does not modify the source database.

For local checks:

```powershell
python -B -m unittest discover -s tests -v
```
