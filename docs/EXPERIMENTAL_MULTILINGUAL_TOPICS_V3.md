# Experimental multilingual topic classifier (offline lab)

**Status: research-only.** Nothing in this branch modifies the ingestion
pipeline, `news_engine.classify.classify`, or the default production
configuration. The experimental matcher is invoked only by the separate
comparison script and explicitly importing its function.

## Running the experiment

From repository root on Python 3.11+:

```sh
python -B -m tools.compare_topics
python -B -m unittest discover -s tests -v
```

The first command compares the unchanged baseline classifier to
`news_engine.experimental_topics.classify_experimental` on the original
21-case synthetic benchmark and on a **separate additional 20-case synthetic
challenge**. Both datasets are hand-authored and public-domain-style synthetic
text. The additional challenge was created during implementation and is **not
a truly blind or representative holdout**; it is a regression probe, not an
unbiased estimate of performance.

The comparator prints overall and per-language accuracy, per-class
precision/recall, confusion matrices, recovered cases, regressions, and
individual classifications. A null precision/recall means that the
denominator was zero, not that performance was 0%.

## Design and constraints

- Unicode NFKD + accent removal and word/phrase boundary matching support
  English and Brazilian Portuguese.
- The dictionary is explicit and audited in source. Multiword phrases are
  counted by contiguous normalized tokens; English standalone rate/bank terms
  require policy context.
- If no rule matches, `status="unmatched"` and the compatibility topic is
  `general`. If two categories tie for highest nonzero score,
  `status="ambiguous"` and the compatibility topic is also `general`.
  The status should be preserved when considering a future schema/API.
- The `confidence` field remains an uncalibrated match-density heuristic.
  No market prediction, financial impact, confidence probability, or
  production readiness is implied.
- Larger dictionaries increase possible **false positives** and overlapping
  topic labels. Inspect new errors on both languages before discussing any
  opt-in rollout; neither dataset is an acceptance gate.
- Do not tune on the additional challenge and then call the same set
  independent validation. Future evaluation requires separately labelled,
  authorized data and clear provenance.

No network calls, AI services, secrets, external feeds, background processing,
or private research materials are involved.
