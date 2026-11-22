"""Run the local, synthetic topic classifier benchmark; no network required."""
import json

from news_engine.topic_benchmark import evaluate


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2, sort_keys=True))
