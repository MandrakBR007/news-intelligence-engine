# Adversarial topic evaluation — synthetic V1

**Purpose:** challenge the currently merged baseline and experimental
EN/PT-BR topic matchers with a *new, explicitly frozen* set of 40 synthetic
headlines (20 per language). This work is diagnostic only.

## Protocol

1. The labelled dataset was committed first, independently of the evaluator.
2. Neither `news_engine.classify`, `news_engine.experimental_topics`,
   nor either vocabulary/configuration is modified by this PR.
3. The same 40 cases are passed to the existing `topic_comparison.compare`
   function. Results include confusion matrices, per-language accuracy,
   per-class precision/recall, recovered and regressed case IDs.
4. Additional challenge tags group common failure modes: homonyms,
   historical mentions, negation, educational contexts, paraphrases,
   overlap, and previously unseen synonyms. Case IDs and labels remain
   visible so mistakes are auditable.
5. Tests check deterministic evaluation and arithmetic invariants.
   **No minimum accuracy gate** is imposed: failed classifications are
   experimental findings, not CI failures.
6. Do not edit the dataset or dictionary in response to scores and still
   call this a clean holdout. Any subsequent tuning must use a separately
   named development set and a future untouched validation set.

## Run on Windows PowerShell, macOS, or Linux

From the repository root, on Python 3.11+:

```sh
python -B -m tools.evaluate_adversarial_topics
python -B -m unittest discover -s tests -v
```

These are handcrafted synthetic cases with editorial reference labels.
They **cannot** estimate live-news accuracy or prove generalization to
external publishers. No URLs are fetched, no third-party news is copied,
and no API calls, secrets, or trading code are involved.

### Interpretation

A correct `general` label with `experimental_status="unmatched"` indicates
that no keyword rules matched, not verified understanding of the headline.
False positives on museum, school, river bank, and historical mentions can
reveal keyword-only weaknesses. Negation examples test topic recognition,
**not** whether the classifier understands the direction of an event.
The `confidence` and `impact` values of the experimental matcher remain
uncalibrated heuristics, unrelated to financial predictions.

**Release policy:** retain the existing production classifier unchanged.
Any opt-in rollout requires further independent, authorized data review.
