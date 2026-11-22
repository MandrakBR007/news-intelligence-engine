"""Offline experimental fingerprint versions; ingestion keeps legacy v1.

The content identity hash is deliberately unchanged. V2 only changes tokens
used for approximate SimHash/Jaccard; it cannot compare with stored V1 hashes
without an explicit version-aware migration.
"""
from __future__ import annotations

import re
import unicodedata

from . import dedup
from .util import content_hash, normalize_text, simhash, tokenize

LEGACY_VERSION = "v1_ascii"
UNICODE_VERSION = "v2_unicode"


def tokenize_unicode(text: str) -> list[str]:
    """Casefold and strip combining accents before whole-token matching."""
    value = unicodedata.normalize("NFKD", normalize_text(text).casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", value)


def fingerprint_versioned(item: dict, *, version: str = LEGACY_VERSION) -> dict:
    """Compute a version-labelled fingerprint, without changing stored identity."""
    if version not in (LEGACY_VERSION, UNICODE_VERSION):
        raise ValueError("unsupported fingerprint version")
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    combined = title + " " + summary
    tokens = tokenize(combined) if version == LEGACY_VERSION else tokenize_unicode(combined)
    return {
        "version": version,
        "content_hash": content_hash(title, summary),
        "simhash": simhash(tokens),
        "tokens": tokens,
    }


def compare_versions(items: list[dict]) -> dict:
    """Expose per-item differences; never compare cross-version simhash values."""
    rows = []
    for index, item in enumerate(items):
        legacy = fingerprint_versioned(item, version=LEGACY_VERSION)
        unicode = fingerprint_versioned(item, version=UNICODE_VERSION)
        baseline = dedup.fingerprint(item)
        if legacy["simhash"] != baseline["simhash"] or legacy["content_hash"] != baseline["content_hash"]:
            raise AssertionError("legacy fingerprint compatibility violated")
        rows.append({
            "index": index,
            "content_hash_unchanged": legacy["content_hash"] == unicode["content_hash"],
            "tokens_changed": legacy["tokens"] != unicode["tokens"],
            "simhash_changed": legacy["simhash"] != unicode["simhash"],
            "legacy_tokens": legacy["tokens"],
            "unicode_tokens": unicode["tokens"],
        })
    return {
        "mode": "offline_research_only",
        "versions": [LEGACY_VERSION, UNICODE_VERSION],
        "total": len(rows),
        "token_changes": sum(row["tokens_changed"] for row in rows),
        "simhash_changes": sum(row["simhash_changed"] for row in rows),
        "rows": rows,
        "limitations": (
            "Unicode v2 approximate fingerprints are incompatible with existing v1 "
            "simhash records without a versioned backfill/reindex. This function "
            "does not update SQLite, ingestion defaults, or exact content identity."
        ),
    }
