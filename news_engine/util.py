"""Dependency-free text and time helpers. Missing dates stay unknown."""
from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value) -> str | None:
    """Return an ISO UTC timestamp or None. Never invent publication times."""
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError, IndexError):
            try:
                dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return None
    if dt.tzinfo is None:
        # Assumption: missing timezone means UTC, flagged by the caller if needed.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def normalize_text(text) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(text).lower())


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_hash(title, summary) -> str:
    return sha256_hex(normalize_text(title).lower() + "\n" + normalize_text(summary).lower())


def simhash(tokens, bits: int = 64) -> int:
    if not tokens:
        return 0
    counts = [0] * bits
    for token in tokens:
        digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(bits):
            counts[i] += 1 if (digest >> i) & 1 else -1
    value = 0
    for i in range(bits):
        if counts[i] > 0:
            value |= 1 << i
    return value


def hamming(a: int, b: int) -> int:
    return bin((int(a) ^ int(b)) & ((1 << 64) - 1)).count("1")


def jaccard(a, b) -> float:
    sa, sb = set(a or []), set(b or [])
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def safe_text(value) -> str:
    return html.escape(str(value or ""), quote=True)
