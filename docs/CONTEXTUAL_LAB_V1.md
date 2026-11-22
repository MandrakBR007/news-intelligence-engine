# Contextual Intelligence Lab V1 (experimental)

This opt-in offline classifier **does not** change the ingestion pipeline or
existing baseline and multilingual classifiers. Import directly from
`news_engine.contextual_topics` to test it:

```python
from news_engine.contextual_topics import classify_contextual
result = classify_contextual({"title": "Museum exhibition about inflation"})
```

The implementation is a **conservative lexical context probe**, not semantic
language understanding. It reuses the existing experimental topic classifier,
then checks the headline for cultural, educational, historical and metaphorical
context signals. It returns `needs_review` with a `candidate_topic` and
explicit evidence when a topic match is suspicious. A narrowly defined set
of present-day event anchors prevents background summary mentions from
silencing an otherwise explicit release headline. No general-context headline
is automatically certified as out-of-scope.

Statuses:
- `matched`: topic matches a lexicon and no unresolved contextual warning.
- `needs_review`: no topic evidence, an ambiguous tie, or conflicting title
  context. `topic="general"` in this state is only a compatibility label.

All evidence fields contain **matching phrases**, not original sensitive news
text. Callers should treat `candidate_topic` as unconfirmed. This is an
experimental API, not production confidence or verified causal reasoning.

Run from the repository root:

```sh
python -B -m unittest discover -s tests -v
```

The existing 40-case adversarial fixture is **not changed** or used for tuning
in this PR. The upcoming comparative work should report both selective
accuracy on matched cases **and coverage/abstention**, including false
review flags. Do not optimize the same test set and subsequently call it a
fresh holdout. Independent, authorized data will still be necessary before a
production decision. No external models, feeds or API keys are required.
