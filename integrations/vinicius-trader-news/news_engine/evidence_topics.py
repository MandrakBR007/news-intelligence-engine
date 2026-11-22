"""Opt-in evidence-first topic probe; never called from ingestion.

This deliberately narrow classifier is a research hypothesis, not a trained
model. A review/abstention is not a general-topic decision.
"""
from __future__ import annotations

from .experimental_topics import _normalize

# Phrase rules are anchored to the actual headline, never the source name.
POLICY = (
    "minutes of the federal open market committee",
    "fomc statement",
    "discount rate meetings",
    "monetary policy decision",
    "policy rate decision",
    "central bank raises interest rates",
    "central bank cuts interest rates",
    "banco central eleva juros",
    "banco central reduz juros",
    "ata do comite de politica monetaria",
)
ECONOMIC = (
    "consumer price index",
    "inflation report",
    "employment report",
    "gross domestic product",
    "survey of consumer finances",
    "indice de precos ao consumidor",
    "relatorio de inflacao",
    "dados de emprego",
)
BUSINESS = (
    "company reports earnings",
    "reports quarterly earnings",
    "company announces merger",
    "empresa divulga resultados",
    "companhia anuncia fusao",
)
# Explicitly administrative or supervisory releases; never monetary merely
# because a bank or the Federal Reserve is named.
ADMINISTRATIVE = (
    "enforcement action",
    "enforcement actions",
    "approval of application",
    "approval of two applications",
    "comment period",
    "fed challenge winners",
    "fomc meetings in",
    "federal open market committee meetings in",
    "third party risk management guidance",
    "pricing effective",
)
NON_NEWS = (
    "museum", "exhibition", "lecture", "classroom", "historical",
    "museu", "exposicao", "palestra", "aula", "historico",
)


def _hit(title: str, phrases: tuple[str, ...]) -> bool:
    # Space padding prevents partial token collisions after normalization.
    haystack = " " + title + " "
    return any(" " + _normalize(phrase) + " " in haystack for phrase in phrases)


def classify_evidence(item: dict) -> dict:
    """Return a narrow topic decision or explicitly require review.

    Private text is never included in output. No model scores, probabilities,
    or estimated market impacts are produced.
    """
    title = _normalize(str(item.get("title") or ""))
    summary = _normalize(str(item.get("summary") or ""))
    if not title:
        return {"topic": None, "status": "needs_review", "reason": "missing_title",
                "candidate_topic": None}
    if _hit(title, NON_NEWS):
        return {"topic": None, "status": "needs_review", "reason": "non_news_context",
                "candidate_topic": None}

    signals = {
        "monetary_policy": _hit(title, POLICY),
        "economic_data": _hit(title, ECONOMIC),
        "business": _hit(title, BUSINESS),
    }
    matched = [topic for topic, hit in signals.items() if hit]
    if len(matched) > 1:
        return {"topic": None, "status": "needs_review", "reason": "conflicting_topic_evidence",
                "candidate_topic": None}
    if matched:
        return {"topic": matched[0], "status": "matched", "reason": "explicit_headline_evidence",
                "candidate_topic": matched[0]}
    if _hit(title, ADMINISTRATIVE):
        return {"topic": "general", "status": "matched",
                "reason": "explicit_administrative_headline", "candidate_topic": "general"}
    return {"topic": None, "status": "needs_review", "reason": "insufficient_headline_evidence",
            "candidate_topic": None}
