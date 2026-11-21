"""Content fingerprints, exact deduplication and near-duplicate clustering."""
from __future__ import annotations

from .util import content_hash, hamming, jaccard, simhash, tokenize


def fingerprint(item: dict) -> dict:
    tokens = tokenize((item.get("title", "") + " " + item.get("summary", "")))
    return {
        "tokens": tokens,
        "simhash": simhash(tokens),
        "content_hash": content_hash(item.get("title", ""), item.get("summary", "")),
    }


def is_near(a: dict, b: dict, hamming_threshold: int = 8, jaccard_threshold: float = 0.75) -> bool:
    if hamming(a["simhash"], b["simhash"]) <= hamming_threshold:
        return True
    ta, tb = a.get("tokens"), b.get("tokens")
    if ta and tb:
        return jaccard(ta, tb) >= jaccard_threshold
    return False


def assign_cluster(fp: dict, existing, hamming_threshold: int = 8,
                   jaccard_threshold: float = 0.75) -> tuple[str, str]:
    for entry in existing:
        if entry["content_hash"] == fp["content_hash"]:
            return entry["cluster_id"], "exact"
        if is_near(fp, entry, hamming_threshold, jaccard_threshold):
            return entry["cluster_id"], "near"
    return fp["content_hash"][:16], "new"
