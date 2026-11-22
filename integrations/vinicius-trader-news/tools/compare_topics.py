"""Run two offline synthetic comparisons; invoke as python -B -m tools.compare_topics."""
import json
from pathlib import Path

from news_engine.topic_comparison import compare
from news_engine.topic_benchmark import load_cases

HOLDOUT = Path(__file__).resolve().parents[1] / "examples" / "synthetic_topic_challenge_v1.json"


if __name__ == "__main__":
    output = {
        "original_fixture": compare(),
        "additional_challenge": compare(load_cases(HOLDOUT)),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
