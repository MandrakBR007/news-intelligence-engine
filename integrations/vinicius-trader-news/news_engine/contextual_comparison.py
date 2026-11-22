"""Offline three-way comparison with explicit contextual abstention metrics."""
from __future__ import annotations

from collections import Counter

from . import contextual_topics
from .topic_benchmark import LABELS
from .topic_comparison import compare


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def compare_three(cases: list[dict]) -> dict:
    """Report coverage separately from accuracy; review is not a correct label."""
    result = compare(cases)
    observed = []
    for case, pair in zip(cases, result["cases"], strict=True):
        if case["id"] != pair["id"]:
            raise ValueError("case order mismatch")
        context = contextual_topics.classify_contextual({
            "title": case["title"], "summary": case["summary"],
        })
        status = context["status"]
        if status not in ("matched", "needs_review"):
            raise ValueError("unsupported contextual status")
        topic = context["topic"] if status == "matched" else None
        if topic is not None and topic not in LABELS:
            raise ValueError("unsupported contextual label")
        observed.append({
            **pair,
            "contextual": topic,
            "contextual_status": status,
            "contextual_reason": context["reason"],
            "candidate_topic": context["candidate_topic"],
            "contextual_correct": topic == case["expected_topic"] if topic is not None else None,
        })

    reviewed = [row for row in observed if row["contextual_status"] == "needs_review"]
    decided = [row for row in observed if row["contextual_status"] == "matched"]
    correct = sum(row["contextual_correct"] is True for row in decided)
    false_review = [row["id"] for row in reviewed if row["experimental_correct"]]
    caught_errors = [row["id"] for row in reviewed if not row["experimental_correct"]]
    by_language = {}
    for language in ("en", "pt-BR"):
        subset = [row for row in observed if row["language"] == language]
        selected = [row for row in subset if row["contextual_status"] == "matched"]
        by_language[language] = {
            "total": len(subset),
            "matched": len(selected),
            "reviewed": len(subset) - len(selected),
            "coverage": _ratio(len(selected), len(subset)),
            "selective_accuracy": _ratio(
                sum(row["contextual_correct"] is True for row in selected), len(selected)
            ),
        }
    return {
        "total": len(observed),
        "baseline": result["baseline"],
        "experimental": result["experimental"],
        "contextual": {
            "matched": len(decided),
            "reviewed": len(reviewed),
            "coverage": _ratio(len(decided), len(observed)),
            "review_rate": _ratio(len(reviewed), len(observed)),
            "correct_among_matched": correct,
            "selective_accuracy": _ratio(correct, len(decided)),
            "false_review_vs_experimental_ids": false_review,
            "caught_experimental_errors_ids": caught_errors,
            "review_reasons": dict(sorted(Counter(row["contextual_reason"] for row in reviewed).items())),
            "per_language": by_language,
        },
        "cases": observed,
        "limitations": (
            "Review is not correctness, and selective accuracy ignores abstentions. "
            "False-review and caught-error counts are relative to the experimental "
            "classifier, not a production cost model. All labels are synthetic."
        ),
    }
