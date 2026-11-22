"""Offline audit of user-labelled topic cases, without inspecting any private feeds.

Reports aggregate decision quality and selective coverage. The caller, not this
tool, is responsible for the provenance and independence of supplied labels.
"""
from __future__ import annotations

from collections import Counter

from .classifier_preview import MODES, preview
from .topic_benchmark import LABELS


def _ratio(n, d):
    return round(n / d, 4) if d else None


def evaluate(cases: list[dict]) -> dict:
    """Compare frozen engines against externally supplied reference annotations."""
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation requires a nonempty list of labelled cases")
    ids = set()
    grouped = {}
    totals = {mode: {"matched": 0, "correct": 0, "reviews": 0,
                     "unmatched": 0, "ambiguous": 0} for mode in MODES}
    confusion = {mode: {label: {p: 0 for p in LABELS} for label in LABELS}
                 for mode in MODES}
    for case in cases:
        if not isinstance(case, dict) or not all(
            isinstance(case.get(k), str) for k in
            ("id", "language", "title", "summary", "expected_topic")
        ):
            raise ValueError("each case requires string id/language/title/summary/expected_topic")
        if not case["id"] or case["id"] in ids:
            raise ValueError("empty or duplicate case id")
        ids.add(case["id"])
        if case["language"] not in ("en", "pt-BR") or case["expected_topic"] not in LABELS:
            raise ValueError("unsupported language or expected topic")
        language = case["language"]
        grouped.setdefault(language, {mode: {"total": 0, "matched": 0,
                           "correct": 0, "needs_review": 0} for mode in MODES})
        source = {"title": case["title"], "summary": case["summary"]}
        for mode in MODES:
            result = preview(source, mode=mode)
            status, topic = result["status"], result["topic"]
            stats = totals[mode]
            grouped[language][mode]["total"] += 1
            if status == "matched":
                if topic not in LABELS:
                    raise ValueError("unsupported predicted label")
                stats["matched"] += 1
                grouped[language][mode]["matched"] += 1
                confusion[mode][case["expected_topic"]][topic] += 1
                if topic == case["expected_topic"]:
                    stats["correct"] += 1
                    grouped[language][mode]["correct"] += 1
            elif status == "needs_review":
                stats["reviews"] += 1
                grouped[language][mode]["needs_review"] += 1
            elif status in ("unmatched", "ambiguous"):
                stats[status] += 1
            else:
                raise ValueError("unsupported classifier status")
    n = len(cases)
    results = {}
    for mode, stats in totals.items():
        results[mode] = {
            **stats, "total": n,
            "coverage": _ratio(stats["matched"], n),
            "selective_accuracy": _ratio(stats["correct"], stats["matched"]),
            "review_rate": _ratio(stats["reviews"], n),
            "unresolved": n - stats["matched"],
            "correct_over_all_cases": _ratio(stats["correct"], n),
            "confusion_among_decided": confusion[mode],
            "by_language": {
                language: {
                    **per_mode[mode],
                    "coverage": _ratio(per_mode[mode]["matched"], per_mode[mode]["total"]),
                    "selective_accuracy": _ratio(
                        per_mode[mode]["correct"], per_mode[mode]["matched"]
                    ),
                } for language, per_mode in sorted(grouped.items())
            },
        }
    return {
        "total": n,
        "engines": results,
        "provenance": "user_supplied_labels_not_independently_verified",
        "limitations": (
            "These are aggregate results for the supplied cases only. "
            "Abstention never counts as correct; accuracy among decided cases "
            "must be interpreted alongside coverage. This tool cannot certify "
            "label validity, sample independence or real-world representativeness."
        ),
    }
