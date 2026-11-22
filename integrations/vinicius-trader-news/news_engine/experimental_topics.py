"""Experimental, offline EN/PT topic matcher; not used by the ingestion pipeline.

Rule vocabulary is intentionally explicit and auditable. Neither the matching
score nor the impact bucket is a validated probability or market forecast.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .util import normalize_text

# Phrases are matched as contiguous normalized tokens, never substrings.
# The original English keywords are retained as a starting point.
LEXICON = {
    "economic_data": (
        "inflation", "employment", "economic", "gdp", "prices",
        "consumer price index", "price index", "jobless claims",
        "statistical bulletin", "inflacao", "emprego", "desemprego",
        "indicadores economicos", "produto interno bruto", "indice de precos",
        "atividade economica", "dados economicos", "fiscal statistics",
    ),
    "monetary_policy": (
        "central bank", "interest rates", "monetary policy", "policy committee",
        "monetary authority", "borrowing costs", "policy rate",
        "banco central", "juros", "politica monetaria", "autoridade monetaria",
        "taxa basica", "decisao monetaria", "comite de politica monetaria",
    ),
    "business": (
        "earnings", "revenue", "company", "industry", "business",
        "quarterly sales", "store results", "corporate results",
        "empresa", "companhia", "receita", "faturamento", "resultados trimestrais",
        "lucro operacional", "balanco corporativo", "vendas",
    ),
}

# Single-word compatibility terms for baseline monetary-policy cases. Kept
# narrow to avoid treating ordinary uses of "bank" or "rates" as policy news.
MONETARY_CONTEXT = ("central bank", "banco central", "monetary authority",
                    "autoridade monetaria", "policy committee",
                    "comite de politica monetaria")


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", normalize_text(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _phrase_count(tokens: tuple[str, ...], phrase: str) -> int:
    needle = tuple(_normalize(phrase).split())
    length = len(needle)
    if not length:
        return 0
    return sum(tokens[i:i + length] == needle for i in range(len(tokens) - length + 1))


def classify_experimental(item: dict) -> dict:
    """Classify with explicit phrase matching and expose unmatched/ambiguous status."""
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    tokens = tuple(_normalize(title + " " + summary).split())
    scores = Counter()
    matched = {}
    for topic, phrases in LEXICON.items():
        hits = [(phrase, _phrase_count(tokens, phrase)) for phrase in phrases]
        selected = [phrase for phrase, count in hits if count]
        matched[topic] = selected
        scores[topic] = sum(count for _, count in hits)

    # Preserve the baseline's standalone English monetary cues only when a
    # central-bank context is present; otherwise "rates" is too generic.
    if any(_phrase_count(tokens, phrase) for phrase in MONETARY_CONTEXT):
        for phrase in ("interest", "rates", "policy", "bank", "central"):
            if _phrase_count(tokens, phrase) and phrase not in matched["monetary_policy"]:
                scores["monetary_policy"] += _phrase_count(tokens, phrase)
                matched["monetary_policy"].append(phrase)

    highest = max(scores.values(), default=0)
    if highest == 0:
        return {
            "topic": "general", "status": "unmatched",
            "impact": "low", "confidence": 0.0, "matched": [],
            "topic_scores": dict(scores),
        }
    winners = [topic for topic in LEXICON if scores[topic] == highest]
    if len(winners) != 1:
        return {
            "topic": "general", "status": "ambiguous",
            "impact": "low", "confidence": 0.0, "matched": [],
            "topic_scores": dict(scores),
        }
    winner = winners[0]
    impact = "high" if highest >= 5 else ("medium" if highest >= 2 else "low")
    return {
        "topic": winner, "status": "matched", "impact": impact,
        "confidence": round(min(1.0, highest / 5.0), 3),
        "matched": matched[winner], "topic_scores": dict(scores),
    }
