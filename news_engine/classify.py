"""Lightweight, configurable topic classification (no external services)."""
from __future__ import annotations

from .util import tokenize


def classify(item: dict, topics) -> dict:
    text = (item.get("title", "") + " " + item.get("summary", ""))
    tokens = tokenize(text)
    best_topic = None
    best_score = 0
    matched: list[str] = []
    for topic in topics or []:
        keywords = [str(k).lower() for k in topic.get("keywords", [])]
        score = sum(tokens.count(k) for k in keywords)
        if score > best_score:
            best_score = score
            best_topic = topic.get("id")
            matched = [k for k in keywords if k in tokens]
    if not best_topic:
        return {"topic": "general", "impact": "low", "confidence": 0.0, "matched": []}
    impact = "high" if best_score >= 5 else ("medium" if best_score >= 2 else "low")
    confidence = round(min(1.0, best_score / 5.0), 3)
    return {"topic": best_topic, "impact": impact, "confidence": confidence, "matched": matched}
