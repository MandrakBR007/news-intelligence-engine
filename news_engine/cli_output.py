"""Privacy-minimized JSON reporting for explicit CLI commands.

Outputs are summaries, not dumps of upstream, SDK, environment or exception
objects. Only intentionally public research metadata and numeric counts are
sent to standard output. Detailed user-provided records stay in local SQLite.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

from .gemini_client import PUBLIC_QUESTIONS

_REDACT = "[redacted]"
_SENSITIVE = re.compile(
    r"(?i)(?:\b(?:password|passphrase|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|bearer|authorization|credential|client[_-]?secret|"
    r"private[_-]?key)\b\s*[:=]\s*\S+|"
    r"\bBearer\s+\S+|https?://[^\s/@]+@)"
)
_COUNT_FIELDS = ("total", "new", "near_duplicate", "exact_duplicate",
                 "new_clusters", "new_revisions", "errors")
_STATS_COUNTS = ("total", "clusters", "revisions", "unknown_publication_time")
_QUEUE_FIELDS = ("pending", "leased", "done", "dead", "ready", "delayed", "expired_leases")


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _label(value, max_length=100):
    if not isinstance(value, str):
        return _REDACT
    text = "".join(c for c in value if c.isprintable()).strip()[:max_length]
    return _SENSITIVE.sub(_REDACT, text)


def _counts(data, fields):
    if not isinstance(data, dict):
        return {}
    return {name: int(data[name]) for name in fields
            if isinstance(data.get(name), int) and not isinstance(data[name], bool)}


def _stats(value):
    value = value if isinstance(value, dict) else {}
    result = _counts(value, _STATS_COUNTS)
    for key, label in (("topics", "topic"), ("impacts", "impact"), ("sources", "source")):
        rows = value.get(key, [])
        result[key] = [{label: _label(row.get(label)), "c": int(row["c"])}
                       for row in rows if isinstance(row, dict)
                       and isinstance(row.get("c"), int) and not isinstance(row["c"], bool)] \
                      if isinstance(rows, list) else []
    return result


def _review(value):
    if not isinstance(value, dict) or value.get("enabled") is not True:
        return {"enabled": False, "reason": "Review disabled or optional integration unavailable."}
    answers = value.get("answers") if isinstance(value.get("answers"), dict) else {}
    filtered = {}
    for question, definition in PUBLIC_QUESTIONS.items():
        answer = answers.get(question)
        answer = answer if isinstance(answer, dict) else {}
        fields = {}
        if question == "category":
            choice = answer.get("choice")
            if choice in definition["criteria"]:
                fields["choice"] = choice
            probs = answer.get("probabilities")
            if isinstance(probs, dict):
                fields["probabilities"] = {key: n for key in definition["criteria"]
                                           if (n := _number(probs.get(key))) is not None
                                           and 0.0 <= n <= 1.0}
        else:
            n = _number(answer.get("noul"))
            if n is not None and 0.0 <= n <= 1.0:
                fields["noul"] = n
        confidence = _number(answer.get("confidence"))
        if confidence is not None and 0.0 <= confidence <= 1.0:
            fields["confidence"] = confidence
        filtered[question] = fields
    return {"enabled": True, "api_version": "v1beta", "answers": filtered}


def public_result(command, value):
    """Return a strictly allowlisted CLI result, avoiding opaque/raw outputs."""
    value = value if isinstance(value, dict) else {}
    if command == "review":
        return _review(value)
    if command in ("stats",):
        return _stats(value)
    if command == "queue-stats":
        return _counts(value, _QUEUE_FIELDS)
    if command == "health":
        return {
            "status": "ok" if value.get("status") == "ok" else "unknown",
            **_counts(value, ("items", "feed_cache_entries", "feeds_with_unexpected_status")),
            "last_feed_check_at": _label(value["last_feed_check_at"], 40)
                if isinstance(value.get("last_feed_check_at"), str) else None,
            "last_item_observed_at": _label(value["last_item_observed_at"], 40)
                if isinstance(value.get("last_item_observed_at"), str) else None,
            "queue": _counts(value.get("queue"), _QUEUE_FIELDS),
        }
    if command == "enqueue-feeds":
        return {"added": _counts(value, ("added",)).get("added", 0),
                "queue": _counts(value.get("queue"), _QUEUE_FIELDS)}
    if command == "work-once":
        status = value.get("status")
        result = {"status": status if status in ("done", "empty", "retry_or_dead", "deferred") else "error"}
        result.update(_counts(value, ("job_id",)))
        if result["status"] == "done":
            result["counts"] = _counts(value.get("counts"), _COUNT_FIELDS)
        elif result["status"] == "retry_or_dead":
            # Do not print raw exception messages; their payloads may contain URLs or tokens.
            result["error"] = "feed_processing_failed"
        return result
    if command in ("demo", "collect"):
        result = {"counts": _counts(value.get("counts"), _COUNT_FIELDS),
                  "stats": _stats(value.get("stats"))}
        # Keep just filenames, never absolute paths that might include usernames.
        for name in ("db_path", "dashboard"):
            if isinstance(value.get(name), str):
                result[name] = Path(value[name]).name
        if command == "demo":
            result["note"] = "Synthetic demo only. No network, no external data."
        else:
            # The raw errors list may contain arbitrarily detailed HTTP/SDK exceptions.
            errors = value.get("errors")
            result["error_count"] = len(errors) if isinstance(errors, list) else 0
        return result
    if command == "dashboard":
        return {"dashboard": Path(value["dashboard"]).name} if isinstance(value.get("dashboard"), str) else {}
    return {"status": "unknown_command"}
