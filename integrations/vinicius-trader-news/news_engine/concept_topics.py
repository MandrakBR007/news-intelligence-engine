"""Offline concept-family topic probe; separate from ingestion and existing engines.

The small lexicon expresses broad economic concepts, not entity names or
memorized article headlines. It is an interpretable research hypothesis;
abstention is deliberately not counted as a correct general prediction.
"""
from __future__ import annotations

from .experimental_topics import _normalize, _phrase_count

# Families are explicit, token-boundary phrase matches on the headline.
# Statistical bank *rates* are measurements, not interest-rate decisions.
CONCEPTS = {
    "economic_data": (
        "balance of payments", "balanca de pagamentos",
        "international investment position", "posicao de investimento internacional",
        "wage growth", "crescimento salarial",
        "interest rate statistics", "estatisticas de taxas de juros",
        "monetary developments", "agregados monetarios",
        "banking data", "dados bancarios",
        "economic indicators", "indicadores economicos",
        "consumer price index", "indice de precos ao consumidor",
        "inflation data", "dados de inflacao",
        "employment statistics", "estatisticas de emprego",
        "gross domestic product", "produto interno bruto",
        "quarterly national accounts", "contas nacionais trimestrais",
    ),
    "monetary_policy": (
        "monetary policy", "politica monetaria",
        "policy rate decision", "decisao da taxa basica",
        "interest rate decision", "decisao sobre juros",
        "fomc statement", "comunicado do copom",
        "federal open market committee", "comite de politica monetaria",
        "discount rate meetings", "reunioes sobre taxa de redesconto",
        "central bank raises rates", "central bank cuts rates",
        "banco central eleva juros", "banco central reduz juros",
    ),
    "business": (
        "corporate earnings", "resultados corporativos",
        "company earnings", "lucro da empresa",
        "quarterly revenue", "receita trimestral",
        "company merger", "fusao de empresas",
        "acquisition agreement", "acordo de aquisicao",
    ),
}
# Supervisory and financial-stability content has no dedicated public label;
# these narrow terms provisionally map to general, with policy conflicts held.
GENERAL = (
    "bank supervision", "supervisao bancaria",
    "supervisory action", "acao de supervisao",
    "enforcement action", "acao sancionadora",
    "approval of application", "aprovacao de requerimento",
    "financial stability", "estabilidade financeira",
    "risk management guidance", "orientacoes sobre gestao de riscos",
    "regulation proposal", "proposta de regulacao",
    "comment period", "prazo para comentarios",
)
CONTEXT_BLOCKERS = (
    "museum", "exhibition", "classroom", "lecture about", "history of",
    "museu", "exposicao", "sala de aula", "palestra sobre", "historia da",
)


def _matches(tokens: tuple[str, ...], phrases: tuple[str, ...]) -> bool:
    return any(_phrase_count(tokens, phrase) > 0 for phrase in phrases)


def classify_concepts(item: dict) -> dict:
    """Topic/status/reason only: never return headline text or keyword traces."""
    title = _normalize(str(item.get("title") or ""))
    if not title:
        return _review("missing_title")
    tokens = tuple(title.split())
    if _matches(tokens, CONTEXT_BLOCKERS):
        return _review("non_event_context")
    found = [label for label, phrases in CONCEPTS.items() if _matches(tokens, phrases)]
    if _matches(tokens, GENERAL):
        found.append("general")
    if len(found) > 1:
        return _review("conflicting_concepts")
    if not found:
        return _review("insufficient_concept_evidence")
    topic = found[0]
    return {"topic": topic, "status": "matched",
            "candidate_topic": topic, "reason": "headline_concept_match"}


def _review(reason: str) -> dict:
    return {"topic": None, "status": "needs_review",
            "candidate_topic": None, "reason": reason}
