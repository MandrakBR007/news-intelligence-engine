# Evidence-first topic probe (opt-in research only)

This small V3 experiment adds a fourth preview mode, `evidence`, to
`news_engine.classifier_preview`. It makes **no changes** to ingestion,
production keyword classification, SQLite storage, feed collection, Gemini,
or any persistent schema. It uses only the local headline (not network access).

## Hypothesis from exploratory review

A 20-item, single-source Federal Reserve sample was manually reviewed with
AI assistance. Its labels were not independently blinded or verified and
**are development evidence, not a held-out accuracy test**. In that review,
a generic keyword `bank` generated administrative/supervisory headlines
classified as monetary policy, while simple baseline rules missed FOMC-related
headlines. Such distinctions are worth investigating without treating the
observed 20-item match as validated performance.

The new `evidence` preview uses narrow **headline-only** phrase anchors:
FOMC minutes/statements and discount-rate meeting minutes for monetary
policy; selected named economic statistical releases for economic data;
earnings and mergers for business; explicit enforcement, application
approval, and comment-period language for administrative `general`.
Everything else abstains as `needs_review`. A context such as museum
or lecture can trigger review. This is deliberately not a full
regulatory-news taxonomy or a calibrated model.

## Local usage

Preview a *single locally owned* JSON headline:

```sh
python -B -m tools.preview_classifier_modes --input path/to/article.json --mode evidence
```

Compare the four preview modes against locally supplied labelled cases:

```sh
python -B -m tools.evaluate_labelled_news --input data/manual_labels_002.json
```

The second command now reports an `evidence` aggregate alongside the three
frozen earlier modes. Outputs do not include raw article text. The local
dataset should not be committed or published.

## Validation boundary

Tests are synthetic, deterministic and offline; they check positive and
negative phrase evidence, review abstention, privacy and unchanged old
previews. Any performance claims require a **new**, prospectively sampled
and independently labelled multi-source holdout, accounting for selective
coverage and review rates. Do not use the earlier 20 development headlines
as an independent test.

Run `python -B -m unittest discover -s tests -v` before considering a merge.
Do not activate this classifier in the production pipeline without a
separate approval, compatibility plan and independent validation.
