"""Reproducible offline topic benchmark with explicit synthetic human-authored labels.

Metrics are diagnostic for this fixture, not estimates of live-news accuracy.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import classify, config

DATASET_PATH = Path(__file__).resolve().parents[1] / "examples" / "synthetic_topic_benchmark_v1.json"
LABELS = ("economic_data", "monetary_policy", "business", "general")


def load_cases(path: str | Path = DATASET_PATH) -> list[dict]:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("topic benchmark must contain a nonempty list")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each benchmark case must be an object")
        if not all(isinstance(case.get(key), str) for key in
                   ("id", "language", "title", "summary", "expected_topic")):
            raise ValueError("benchmark case has missing or invalid fields")
        if case["id"] in seen:
            raise ValueError("duplicate benchmark case id")
        seen.add(case["id"])
        if case["language"] not in ("en", "pt-BR"):
            raise ValueError("unsupported fixture language")
        if case["expected_topic"] not in LABELS:
            raise ValueError("unsupported expected topic")
    return cases


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def evaluate(cases: list[dict] | None = None, topics: list[dict] | None = None) -> dict:
    """Compute transparent multiclass confusion and per-class metrics."""
    cases = load_cases() if cases is None else cases
    topics = config.DEFAULT_TOPICS if topics is None else topics
    confusion = {gold: {pred: 0 for pred in LABELS} for gold in LABELS}
    observed = []
    for case in cases:
        actual = case["expected_topic"]
        if actual not in LABELS:
            raise ValueError("unsupported expected topic")
        output = classify.classify({"title": case["title"], "summary": case["summary"]}, topics)
        predicted = output["topic"]
        if predicted not in LABELS:
            raise ValueError("unsupported predicted topic")
        confusion[actual][predicted] += 1
        observed.append({
            "id": case["id"],
            "language": case["language"],
            "expected": actual,
            "predicted": predicted,
            "correct": actual == predicted,
            "heuristic_score": output["confidence"],
        })
    metrics = {}
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[gold][label] for gold in LABELS if gold != label)
        fn = sum(confusion[label][pred] for pred in LABELS if pred != label)
        metrics[label] = {
            "support": sum(confusion[label].values()),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": _ratio(tp, tp + fp),
            "recall": _ratio(tp, tp + fn),
        }
    correct = sum(row["correct"] for row in observed)
    per_language = {}
    for language in ("en", "pt-BR"):
        rows = [row for row in observed if row["language"] == language]
        per_language[language] = {
            "cases": len(rows),
            "correct": sum(row["correct"] for row in rows),
            "accuracy": _ratio(sum(row["correct"] for row in rows), len(rows)),
        }
    return {
        "dataset": "synthetic-topic-v1",
        "total": len(observed),
        "correct": correct,
        "accuracy": _ratio(correct, len(observed)),
        "labels": list(LABELS),
        "confusion": confusion,
        "per_class": metrics,
        "per_language": per_language,
        "cases": observed,
        "limitations": ("Synthetic hand-labelled fixture only; labels may be ambiguous. "
                        "Heuristic score is not a calibrated probability or a "
                        "financial/market prediction."),
    }
