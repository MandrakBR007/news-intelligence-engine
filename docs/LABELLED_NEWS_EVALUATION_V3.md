# User-labelled news evaluation — offline research

This utility evaluates the three **frozen** topic engines against a locally
supplied, user-annotated dataset. It does not acquire news, make network calls,
change classifier rules, or write into SQLite. **No real news sample is bundled,
and no real-data accuracy has yet been measured by this PR.**

Use a locally stored JSON **array** with entries following this schema:

```json
[
  {
    "id": "anonymous-case-001",
    "language": "pt-BR",
    "title": "Example headline supplied by a reviewer",
    "summary": "Example text supplied by a reviewer",
    "expected_topic": "general"
  }
]
```

The supported reference labels are `economic_data`, `monetary_policy`,
`business`, and `general`. Languages are `en` and `pt-BR`. Use
independently annotated real news with legal permission; record collection
dates, data provenance, sampling protocol, ambiguity policy, and reviewer
agreement **outside the JSON submitted to this evaluator**. Do not label
examples by copying model predictions. Keep any private headlines and source
URLs out of public pull requests. This tool makes no claim that labels are
independent or representative.

Run from the repository root:

```sh
python -B -m tools.evaluate_labelled_news --input path/to/local_labels.json
```

Output includes only aggregate counts, coverage, selective accuracy,
review/unmatched/ambiguous rates, confusion counts among decisions, and
breakdown by language. It never prints article text, case IDs or URLs.

The contextual `needs_review` status is **not** a correct prediction and
is excluded from selective accuracy's denominator. Overall correct/total is
also reported so a low-coverage model cannot look artificially successful.
Metrics with zero eligible examples are `null`, not 100%.

Use a new independently labelled sample and publish only non-sensitive
aggregate statistics if desired. An unrepresentative sample, small size,
or disagreement among human reviewers limits conclusions.

No production activation or threshold gating is performed. All tests use
synthetic fixtures only.
