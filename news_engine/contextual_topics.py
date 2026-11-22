"""Conservative, explainable EN/PT context probe; never used in ingestion.

The rules flag suspicious keyword matches for review. They do not claim
natural-language understanding, nor do they predict market impacts.
"""
from __future__ import annotations

from .experimental_topics import _normalize, _phrase_count, classify_experimental

# Context indicators are confined to the headline: casual summary references
# alone cannot override the headline's leading subject.
NON_NEWS_CONTEXT = {
    "culture": (
        "museum", "exhibition", "gallery", "film", "movie", "festival",
        "museu", "exposicao", "galeria", "filme", "festival", "biblioteca", "library",
        "book titled", "livro chamado", "exhibit", "mostra de arte",
    ),
    "education": (
        "school", "classroom", "lesson", "lecture", "professor", "course",
        "escola", "aula", "professor", "curso", "seminario academico",
    ),
    "historical": (
        "historical", "ancient", "history of", "historic exhibit",
        "historico", "historia da", "roma antiga", "antiguidade",
    ),
    "metaphorical": (
        "river bank", "bank of clouds", "banco da praca", "banco de praca",
    ),
}

# Deliberately limited contemporaneous-event anchors for explicit headlines.
CURRENT_EVENT_ANCHORS = {
    "economic_data": (
        "inflation report", "inflation measure", "employment report", "economic data",
        "consumer price index", "indice de inflacao", "dados economicos",
        "relatorio de emprego", "pib recua", "pib cresce",
    ),
    "monetary_policy": (
        "central bank holds", "central bank raises", "central bank cuts",
        "banco central mantem", "banco central eleva", "banco central reduz",
        "autoridade monetaria anuncia", "policy rate decision",
    ),
    "business": (
        "company reports earnings", "company announces merger",
        "empresa divulga balanco", "companhia anuncia fusao",
        "varejista registra lucro",
    ),
}


def _hits(tokens: tuple[str, ...], phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if _phrase_count(tokens, phrase)]


def classify_contextual(item: dict) -> dict:
    """Return a conservative topic decision plus auditable review evidence.

    ``needs_review`` never implies the headline is out of scope;
    ``general`` is only a compatibility label when review is needed.
    """
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    base = classify_experimental({"title": title, "summary": summary})
    title_tokens = tuple(_normalize(title).split())
    contexts = {key: _hits(title_tokens, words)
                for key, words in NON_NEWS_CONTEXT.items()}
    contexts = {key: hits for key, hits in contexts.items() if hits}
    anchors = _hits(title_tokens, CURRENT_EVENT_ANCHORS.get(base["topic"], ()))
    evidence = {
        "matched_topic_phrases": list(base["matched"]),
        "title_context_cues": contexts,
        "title_current_event_anchors": anchors,
        "topic_scores": dict(base["topic_scores"]),
    }
    if base["status"] != "matched":
        return {
            "topic": "general", "status": "needs_review",
            "reason": "topic_ambiguous" if base["status"] == "ambiguous" else "no_topic_evidence",
            "candidate_topic": None, "evidence": evidence,
        }
    if contexts and not anchors:
        return {
            "topic": "general", "status": "needs_review",
            "reason": "non_news_context_in_title", "candidate_topic": base["topic"],
            "evidence": evidence,
        }
    return {
        "topic": base["topic"], "status": "matched",
        "reason": "topic_evidence_with_context_check", "candidate_topic": base["topic"],
        "evidence": evidence,
    }
