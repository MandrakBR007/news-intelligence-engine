# Three-way contextual topic comparison (research only)

The comparator evaluates three **unchanged** classifiers against the same
frozen, hand-authored synthetic examples:
1. Production keyword baseline.
2. Experimental bilingual phrase matcher.
3. Contextual probe, which may abstain and request review.

Run from the repository root with Python 3.11+:

```sh
python -B -m tools.compare_contextual_topics
python -B -m unittest discover -s tests -v
```

All 21 original, 20 additional, and 40 adversarial cases are evaluated
separately. These fixtures are neither representative live data nor a blind
independent test. Do **not** adjust these labels or classifiers in response
to the reported outcomes and call that independent validation.

## Read the metrics correctly

The baseline and multilingual results include ordinary accuracy and
confusion matrices. The contextual probe can abstain with
`status="needs_review"`. It reports:

- **Coverage:** matched cases / total cases.
- **Review rate:** abstentions / total cases.
- **Selective accuracy:** correct matched labels / matched cases.
  This can be high simply because hard cases were deferred. It must always
  be accompanied by coverage and review rate.
- **False review (relative):** a case deferred by the contextual probe
  that the multilingual classifier had labelled correctly.
- **Caught error (relative):** a case deferred by the contextual probe that
  the multilingual classifier had labelled incorrectly.
- Per-language coverage and selective accuracy, plus explicit case IDs.

Review is neither an automatically correct `general` label nor a
successful classification. Rates with zero denominators are JSON `null`.
These relative metrics are a diagnostic comparison, not a measured cost of
human review or a calibrated probability.

## Limits

This PR changes no classifier vocabulary, scoring, ingestion code, defaults,
or dataset labels. No external model or network request is required.
Context cues are lexical, not verified language comprehension. Production
replacement would require independent authorized real-world evaluation and
review of operating costs, false-positive rates and compatibility.
