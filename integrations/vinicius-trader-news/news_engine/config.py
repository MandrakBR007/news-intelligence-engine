"""Local configuration. No private endpoints or strategy defaults."""
from __future__ import annotations

import copy
import json
from pathlib import Path

DEFAULT_TOPICS = [
    {"id": "economic_data", "keywords": ["inflation", "employment", "economic", "gdp", "prices"]},
    {"id": "monetary_policy", "keywords": ["central", "bank", "interest", "rates", "policy"]},
    {"id": "business", "keywords": ["earnings", "revenue", "company", "industry", "business"]},
]
DEFAULTS = {
    "storage": {"path": "news.db"},
    "dashboard": {"path": "dashboard.html"},
    "dedup": {"hamming_threshold": 8, "jaccard_threshold": 0.75},
    "topics": DEFAULT_TOPICS,
    "feeds": [],
    "queue": {"max_attempts": 3, "retry_delay_seconds": 120},
    "http": {"host": "127.0.0.1", "port": 8080},
}


def _merge(base, override):
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path=None):
    config = copy.deepcopy(DEFAULTS)
    if path:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        config = _merge(config, data)
    return config


def resolve(data_dir, value) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path(data_dir) / path


def db_path(config, data_dir) -> Path:
    return resolve(data_dir, config["storage"]["path"])


def dashboard_path(config, data_dir) -> Path:
    return resolve(data_dir, config["dashboard"]["path"])
