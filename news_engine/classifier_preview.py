"""Explicit, offline classifier preview; never called by ingestion.

Experimental modes do not change the SQLite topic/impact/confidence schema.
An abstention is not a 'general' topic decision. No raw article text or
matched phrases are returned to callers of this privacy-minimized preview.
"""
from __future__ import annotations

from . import classify, config, contextual_topics, evidence_topics, experimental_topics

MODES = ("baseline", "multilingual", "contextual", "evidence")


def preview(item: dict, *, mode: str, topics=None) -> dict:
    """Compare a selected classifier without persisting or changing ingestion."""
    if mode not in MODES:
        raise ValueError("unsupported classifier preview mode")
    source = {
        "title": str(item.get("title") or ""),
        "summary": str(item.get("summary") or ""),
    }
    if mode == "baseline":
        result = classify.classify(
            source, config.DEFAULT_TOPICS if topics is None else topics
        )
        return {
            "mode": mode,
            "status": "matched" if result["topic"] != "general" else "unmatched",
            "topic": result["topic"],
            "candidate_topic": result["topic"] if result["topic"] != "general" else None,
            "reason": "baseline_keyword_match" if result["topic"] != "general"
                      else "no_baseline_keyword_match",
        }
    if mode == "multilingual":
        result = experimental_topics.classify_experimental(source)
        return {
            "mode": mode,
            "status": result["status"],
            "topic": result["topic"] if result["status"] == "matched" else None,
            "candidate_topic": result["topic"] if result["status"] == "matched" else None,
            "reason": "multilingual_phrase_match" if result["status"] == "matched"
                      else ("topic_ambiguous" if result["status"] == "ambiguous"
                            else "no_multilingual_phrase_match"),
        }
    if mode == "evidence":
        return {"mode": mode, **evidence_topics.classify_evidence(source)}
    result = contextual_topics.classify_contextual(source)
    decided = result["status"] == "matched"
    return {
        "mode": mode,
        "status": result["status"],
        "topic": result["topic"] if decided else None,
        "candidate_topic": result["candidate_topic"],
        "reason": result["reason"],
    }


def preview_all(item: dict, *, topics=None) -> dict:
    """Offer a same-input side-by-side view without any production write."""
    return {
        "mode": "comparison",
        "results": {
            mode: preview(item, mode=mode, topics=topics)
            for mode in MODES
        },
    }
