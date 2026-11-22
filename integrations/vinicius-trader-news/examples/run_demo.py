"""Run the offline synthetic demo from the repository root."""
from pathlib import Path

from news_engine import demo

if __name__ == "__main__":
    print(demo.run(Path("./data-demo")))
