"""Opt-in Gemini Decision 1 integration for GENERIC news topic sorting.

No financial prediction, trading policies, or private prompts. Never called from
collect(), demo(), or the queue worker. It sends title/summary to Google only
when the user explicitly executes the CLI `review` command.
"""
from __future__ import annotations

import os

DEFAULT_TIMEOUT_MS = 15000

PUBLIC_QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "Select the most appropriate broad category based ONLY on the supplied headline and summary.",
        "criteria": {
            "economy": "Economic releases, employment, inflation or national accounts.",
            "policy": "Public institutions, monetary policy, laws or government decisions.",
            "business": "Company or industry announcements, earnings or business updates.",
            "other": "None of the other descriptions clearly apply or evidence is insufficient.",
        },
    },
    "text_sufficient": {
        "type": "noul",
        "instructions": "Does the supplied text provide enough evidence to identify a broad category?",
        "criteria": {
            "true_description": "Clear, specific context identifying the subject.",
            "false_description": "Vague, context-free or contradictory text.",
        },
    },
}


def enabled(key_env="GEMINI_API_KEY") -> bool:
    return bool(os.environ.get(key_env))


def review(title: str, summary: str, *, client=None, model="gemini-decision-1",
           key_env="GEMINI_API_KEY", timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    """Explicit network operation unless an injected mock is supplied."""
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1000 <= timeout_ms <= 120000:
        raise ValueError("timeout_ms must be an integer between 1000 and 120000")
    if client is None:
        key = os.environ.get(key_env)
        if not key:
            return {"enabled": False, "reason": f"{key_env} is not set"}
        try:
            from google import genai
        except ImportError as exc:
            return {"enabled": False, "error": f"Install google-genai>=3.2.0: {exc}"}
        client = genai.Client(api_key=key, http_options={"api_version": "v1beta", "timeout": timeout_ms})
    text = "Public news metadata only. No market-price forecast requested.\n" + (
        "Title: " + str(title)[:600] + "\nSummary: " + str(summary)[:2400])
    try:
        response = client.decisions.create(model=model, input=text, questions=PUBLIC_QUESTIONS)
    except Exception:
        # API exceptions may include credentials, prompts or raw HTTP responses.
        # Never surface them in a user-facing result.
        return {"enabled": False, "reason": "external_review_failed"}
    answers = getattr(response, "answers", {})
    clean = {}
    for name in PUBLIC_QUESTIONS:
        ans = answers.get(name) if isinstance(answers, dict) else getattr(answers, name, None)
        if ans is None:
            raise ValueError(f"Decision API response missing '{name}'")
        clean[name] = {}
        for field in ("choice", "noul", "confidence", "probabilities"):
            value = ans.get(field) if isinstance(ans, dict) else getattr(ans, field, None)
            if value is not None:
                clean[name][field] = value
    return {"enabled": True, "model": model, "api_version": "v1beta", "answers": clean}
