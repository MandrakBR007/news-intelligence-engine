# Classifier opt-in research preview V3

This is a **read-only, offline, explicitly invoked** research adapter. It does
**not** enable the experimental classifiers in ingestion or replace the current
production keyword classification.

Use a **local JSON file** containing an article title and summary, e.g.:

```json
{"title": "Banco central mantém juros", "summary": "Synthetic example"}
```

Then run from the repository root:

```sh
python -B -m tools.preview_classifier_modes --input example.json --mode all
```

Modes: `baseline`, `multilingual`, `contextual`, and `all` (comparison).
The CLI accepts only a single JSON object up to 64 KB, uses no network, does
not modify the SQLite database, and does not print the raw article text,
matched phrases, or uncalibrated confidence values.

The preview's `status` can be `matched`, `unmatched`, `ambiguous`, or
`needs_review`, depending on the chosen engine. **Never interpret
`needs_review` as a correct `general` decision**. In that case `topic`
is `null`, and `candidate_topic` is an unconfirmed suggestion.

The baseline mode uses the frozen standard keyword configuration; custom
topics are allowed only through the Python API. This does not represent the
per-user pipeline configuration unless deliberately supplied.

## Deliberate scope boundary

No configuration switch activating the models in ingestion, no schema
migration, and no persisted alternate classifications are included. Turning
on these experimental engines for real data would require a separate
versioned decision schema, review workflow, backward-compatibility plan,
and independent real-world validation of coverage and error rates.

Existing synthetic tests and datasets are not a new independent holdout.
No claims about real-news performance, probabilities or downstream impact
are made. No external AI is invoked.

Verify:

```sh
python -B -m unittest discover -s tests -v
```
