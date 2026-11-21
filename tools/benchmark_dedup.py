"""Print the reproducible public synthetic benchmark; never contacts external services."""
import json
from news_engine.dedup_benchmark import evaluate


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
