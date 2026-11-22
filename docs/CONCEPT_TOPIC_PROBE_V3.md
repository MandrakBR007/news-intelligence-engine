# V3.3 — Optional concept-family topic probe

This branch adds **`concepts`**, a fifth, read-only research preview mode.
It does **not** alter the original classifier, earlier previews, feed
ingestion, database schema, queue, sources, or remote AI services.

## Motivation and evidence boundaries

The earlier `evidence` preview decided 19/20 cases in a Federal Reserve
**development** sample but abstained on all 23 labelled cases in a different
European Central Bank sample (14 economic_data, seven general, two
monetary_policy). The latter labels were assigned with AI assistance and
five ambiguous examples were excluded; this is a *diagnostic* result, not an
independently blinded estimate. The BCE headlines and their failure modes
have informed this implementation, so **neither sample is a valid holdout**
for this V3.3 classifier.

## Design

- Uses token-boundary **concept families**, rather than complete memorized
  headlines or institution-specific names.
- Distinguishes monetary-policy *decisions/discussion* from bank
  *interest-rate statistics* and *monetary-developments reports*.
- Economic datasets include balance-of-payments, wages, inflation,
  employment, investment positions and similar statistical concepts.
- Bank supervision, enforcement and financial-stability concepts map
  provisionally to `general` in the current four-label taxonomy.
- Contradictory concepts and vague/insufficient headlines return
  `needs_review` with a null topic, **not** a false `general` decision.
- No sentiment, market impact, confidence probabilities or exposure of
  original text in the preview response.

This is a **narrow rule probe**, not a semantic language model.
The four public topic labels omit distinct regulatory and financial-stability
classes; that is a known taxonomy limitation, not something that should be
hidden by adding more keywords.

## Usage (local, explicitly invoked)

```sh
python -B -m unittest discover -s tests -v
python -B -m tools.preview_classifier_modes --input path/to/one_article.json --mode concepts
python -B -m tools.evaluate_labelled_news --input data_holdout_v3/manual_labels_holdout_review.json
```

The last command requires every case to have a supported nonempty label.
When there are intentionally uncertain labels, **filter them in memory**
rather than overwriting or guessing, e.g.:

```python
import json
from news_engine.independent_evaluation import evaluate

with open("data_holdout_v3/manual_labels_holdout_review.json", encoding="utf-8-sig") as stream:
    sample = json.load(stream)
allowed = {"economic_data", "monetary_policy", "business", "general"}
print(evaluate([row for row in sample if row.get("expected_topic") in allowed]))
```

Never commit local news text, private data or labels to Git.
Existing examples and the 23 AI-assisted BCE labels are **development
diagnostics**; comparison of their numbers before/after adding the concept
lexicon cannot establish improvement in unseen data.

## Required before production

Freeze the rules. Collect a genuinely new prospective, multi-institution
sample. Have independent reviewers assign labels *without model predictions*,
record ambiguous cases and adjudication, report all-case correct rate plus
selective accuracy **and coverage**, and track false positives in monetary
policy. Do not activate this mode in ingestion until separately approved and
validated, including API/schema compatibility and review workflow.
