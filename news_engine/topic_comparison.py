"""Offline baseline-versus-experimental evaluation on labelled synthetic cases."""
from __future__ import annotations

from collections import Counter

from . import classify, config, experimental_topics
from .topic_benchmark import LABELS, load_cases


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def _summarize(rows: list[dict], key: str) -> dict:
    confusion = {label: {other: 0 for other in LABELS} for label in LABELS}
    for row in rows:
        confusion[row["expected"]][row[key]] += 1
    per_class = {}
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in LABELS if other != label)
        fn = sum(confusion[label][other] for other in LABELS if other != label)
        per_class[label] = {
            "support": sum(confusion[label].values()),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": _ratio(tp, tp + fp),
            "recall": _ratio(tp, tp + fn),
        }
    per_language = {}
    for lang in ("en", "pt-BR"):
        subset = [row for row in rows if row["language"] == lang]
        correct = sum(row[key] == row["expected"] for row in subset)
        per_language[lang] = {
            "cases": len(subset), "correct": correct,
            "accuracy": _ratio(correct, len(subset)),
        }
    correct = sum(row[key] == row["expected"] for row in rows)
    return {
        "total": len(rows), "correct": correct, "accuracy": _ratio(correct, len(rows)),
        "confusion": confusion, "per_class": per_class,
        "per_language": per_language,
    }


def compare(cases: list[dict] | None = None) -> dict:
    """Use the same cases for both classifiers; never modify the baseline."""
    cases = load_cases() if cases is None else cases
    rows = []
    for item in cases:
        expected = item["expected_topic"]
        if expected not in LABELS:
            raise ValueError("unsupported reference topic")
        source = {"title": item["title"], "summary": item["summary"]}
        baseline = classify.classify(source, config.DEFAULT_TOPICS)
        experimental = experimental_topics.classify_experimental(source)
        rows.append({
            "id": item["id"], "language": item["language"], "expected": expected,
            "baseline": baseline["topic"], "experimental": experimental["topic"],
            "experimental_status": experimental["status"],
            "baseline_correct": baseline["topic"] == expected,
            "experimental_correct": experimental["topic"] == expected,
        })
    regressed = [row["id"] for row in rows
                 if row["baseline_correct"] and not row["experimental_correct"]]
    recovered = [row["id"] for row in rows
                 if not row["baseline_correct"] and row["experimental_correct"]]
    return {
        "dataset": "synthetic-comparison-v1",
        "baseline": _summarize(rows, "baseline"),
        "experimental": _summarize(rows, "experimental"),
        "recovered_case_ids": recovered,
        "regressed_case_ids": regressed,
        "experimental_status_counts": dict(Counter(row["experimental_status"] for row in rows)),
        "cases": rows,
        "limitations": "Small hand-labelled synthetic fixtures, not blinded or representative "
                       "of real-world news; keyword scores are not calibrated probabilities.",
    }
