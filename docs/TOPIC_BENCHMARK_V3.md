# Generic news topic benchmark (synthetic V1) / Avaliação de temas

This benchmark evaluates the existing rule-based `news_engine.classify.classify`
against a small **human-authored, synthetic** English and Brazilian Portuguese
reference set. It measures **topic labels**, not the financial implications
of headlines, not real-news accuracy, and not the correctness of a claim.

## Reproduce / Como executar

From repository root with Python 3.11+, without internet or API keys:

```sh
python -B -m tools.benchmark_topics
python -B -m unittest discover -s tests -v
```

The CLI prints deterministic JSON containing a confusion matrix
(`confusion[expected][predicted]`), per-class true positives, false positives,
false negatives, precision and recall, overall accuracy, per-language
accuracy, and individual labelled cases. Undefined precision or recall
is represented by JSON `null`, not zero or a fabricated percentage.

## Reference labels / Rótulos de referência

- `economic_data`: synthetic reports about economic statistics, inflation,
  employment and prices / indicadores de economia e inflação.
- `monetary_policy`: central bank announcements and monetary decisions /
  decisões de banco central e juros.
- `business`: corporate earnings, company results and industry disclosures /
  resultados empresariais e setor corporativo.
- `general`: explicitly out-of-scope topics (e.g. a museum or astronomy),
  not an inherently low-value news item / assunto fora das três categorias.

Cases labelled `ambiguous` deliberately contain terms from multiple
topics. Their reference label is an editorial assumption and not an
unambiguous ground truth. Each fixture records a `note`; disagreements
should be inspected rather than blindly optimized away.

The default dictionary contains English keywords. Portuguese examples
are deliberately included **without** translating or silently changing
production configuration. The multilingual gap is a measurable limitation
and a possible future, separately reviewed improvement.

## Interpretation / Como interpretar

- Confusion counts are exact **for this fixed synthetic fixture** only.
- Class precision is `TP/(TP+FP)`; recall is `TP/(TP+FN)`; both are
  undefined when their denominators equal zero.
- Accuracy is correct labels divided by all cases. Language-specific
  accuracy is reported separately to avoid hiding poor Portuguese coverage.
- The classifier's `confidence` field is a bounded keyword-match heuristic
  (`min(1, score/5)`), **not** empirically calibrated confidence. The JSON
  uses `heuristic_score` to make this distinction explicit.
- The classifier's `impact` is likewise a keyword-count bucket,
  **not** a forecast of market movement, volatility or importance.
- No third-party news text, credentials, external model or network
  access are needed. The test set is small and may not reflect live feeds.

This PR establishes measurement first; it makes **no changes** to the
default classifier or its topic configuration. Future changes can compare
their predictions and error counts against this documented baseline.
