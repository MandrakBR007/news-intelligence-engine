"""Evaluate a frozen adversarial topic fixture without changing either classifier.

Run from the repository root:
    python -B -m tools.evaluate_adversarial_topics
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from news_engine.topic_benchmark import load_cases
from news_engine.topic_comparison import compare

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "synthetic_topic_adversarial_v1.json"


def evaluate() -> dict:
    cases = load_cases(FIXTURE)
    result = compare(cases)
    by_id = {case["id"]: case for case in cases}
    sections = {}
    for row in result["cases"]:
        note = by_id[row["id"]]["note"]
        section = sections.setdefault(note, {"total": 0, "baseline_correct": 0,
                                             "experimental_correct": 0})
        section["total"] += 1
        section["baseline_correct"] += int(row["baseline_correct"])
        section["experimental_correct"] += int(row["experimental_correct"])
    return {
        "fixture": FIXTURE.name,
        "frozen_cases": len(cases),
        "by_challenge_tag": dict(sorted(sections.items())),
        "baseline": result["baseline"],
        "experimental": result["experimental"],
        "regressed_case_ids": result["regressed_case_ids"],
        "recovered_case_ids": result["recovered_case_ids"],
        "experimental_status_counts": result["experimental_status_counts"],
        "cases": result["cases"],
        "limitations": (
            "Hand-authored synthetic stress cases, not a blind independent sample; "
            "labels and challenge tags are editorial choices. "
            "No production changes, model calibration, or market forecasting."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, ensure_ascii=False))
