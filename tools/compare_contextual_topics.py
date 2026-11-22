"""Run a diagnostic three-way comparison on the existing frozen synthetic sets."""
from __future__ import annotations

import json
from pathlib import Path

from news_engine.contextual_comparison import compare_three
from news_engine.topic_benchmark import load_cases

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "original_21": ROOT / "examples" / "synthetic_topic_benchmark_v1.json",
    "additional_20": ROOT / "examples" / "synthetic_topic_challenge_v1.json",
    "adversarial_40": ROOT / "examples" / "synthetic_topic_adversarial_v1.json",
}


def evaluate_all() -> dict:
    return {
        key: compare_three(load_cases(path))
        for key, path in FIXTURES.items()
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_all(), ensure_ascii=False, indent=2, sort_keys=True))
