"""Deterministic, synthetic pairwise deduplication benchmark (no network or models)."""
from __future__ import annotations

from . import dedup
from .util import hamming, jaccard

# Every pair is written for this fixture, without using real article content.
# Labels represent human-authored test assumptions, not real-world accuracy.
SYNTHETIC_PAIRS = [
    (
        {"title": "Battery researchers publish energy storage report", "summary": "A laboratory issues a synthetic report on batteries"},
        {"title": "Battery researchers publish energy storage report", "summary": "A laboratory issues a synthetic report on batteries"},
        True, "exact",
    ),
    (
        {"title": "City publishes new transit schedule", "summary": "Bus routes updated for the weekend"},
        {"title": "City publishes new transit schedule", "summary": "Weekend bus routes updated"},
        True, "near_reordered",
    ),
    (
        {"title": "Research team releases flood map", "summary": "Synthetic flood mapping study for local planners"},
        {"title": "Research team releases flood map", "summary": "Synthetic flood mapping study for local planners revised"},
        True, "near_revision",
    ),
    (
        {"title": "Researchers publish ocean map", "summary": "Synthetic bluewater survey of coastal reefs"},
        {"title": "Researchers publish airport map", "summary": "Synthetic bluewater survey of coastal reefs"},
        False, "shared_vocabulary_different_event",
    ),
    (
        {"title": "City approves new transport plan", "summary": "Bus lanes planned for eastern district"},
        {"title": "City rejects new transport plan", "summary": "Bus lanes planned for eastern district"},
        False, "opposite_decision",
    ),
    (
        {"title": "Synthetic report on wind turbines", "summary": "New components tested for coastal energy"},
        {"title": "Synthetic report on solar panels", "summary": "New components tested for coastal energy"},
        False, "shared_topic_different_subject",
    ),
    (
        {"title": "Library opens at noon on Saturday", "summary": "A local schedule change is announced"},
        {"title": "Museum opens at noon on Saturday", "summary": "A local schedule change is announced"},
        False, "shared_template_different_entity",
    ),
    (
        {"title": "Health agency announces vaccine study", "summary": "Volunteers sought for a synthetic trial"},
        {"title": "Weather agency announces storm study", "summary": "Volunteers sought for a synthetic trial"},
        False, "unrelated_domain",
    ),
]


def evaluate(*, hamming_threshold: int = 8, jaccard_threshold: float = 0.75) -> dict:
    """Evaluate all labelled pairs; thresholds are diagnostic, not optimized here."""
    if not 0 <= hamming_threshold <= 64:
        raise ValueError("hamming_threshold must be between 0 and 64")
    if not 0 <= jaccard_threshold <= 1:
        raise ValueError("jaccard_threshold must be between 0 and 1")
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    cases = []
    for left, right, expected, case_id in SYNTHETIC_PAIRS:
        a, b = dedup.fingerprint(left), dedup.fingerprint(right)
        predicted = dedup.is_near(a, b, hamming_threshold, jaccard_threshold)
        key = ("tp" if expected else "fp") if predicted else ("fn" if expected else "tn")
        counts[key] += 1
        cases.append({
            "id": case_id, "expected_duplicate": expected, "predicted_duplicate": predicted,
            "hamming": hamming(a["simhash"], b["simhash"]),
            "jaccard": round(jaccard(a["tokens"], b["tokens"]), 4),
        })
    precision_denom = counts["tp"] + counts["fp"]
    recall_denom = counts["tp"] + counts["fn"]
    return {
        "dataset": "synthetic-pairs-v1",
        "pairs": len(cases),
        "thresholds": {"hamming": hamming_threshold, "jaccard": jaccard_threshold},
        "counts": counts,
        "precision": counts["tp"] / precision_denom if precision_denom else None,
        "recall": counts["tp"] / recall_denom if recall_denom else None,
        "cases": cases,
    }
