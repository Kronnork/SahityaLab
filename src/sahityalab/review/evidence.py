"""Evidence table construction and deterministic descriptive summaries."""
from __future__ import annotations

from collections import Counter
from typing import Any

from ..models import Article


def evidence_table(articles: list[Article], extraction: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    extraction = extraction or {}
    rows = []
    for article in articles:
        extra = extraction.get(article.id, {})
        rows.append({
            "id": article.id,
            "title": article.title,
            "authors": "; ".join(article.authors),
            "year": article.year,
            "journal": article.journal,
            "doi": article.doi,
            "methodology": extra.get("methodology", ""),
            "context": extra.get("context", ""),
            "theory": extra.get("theory", ""),
            "key_findings": extra.get("key_findings", ""),
            "limitations": extra.get("limitations", ""),
            "research_question": extra.get("research_question", ""),
            "reviewer_notes": extra.get("reviewer_notes", ""),
        })
    return rows


def descriptive_profile(articles: list[Article]) -> dict[str, Any]:
    years = Counter(str(a.year) for a in articles if a.year)
    sources = Counter(a.source_database or "unspecified" for a in articles)
    journals = Counter(a.journal or "unspecified" for a in articles)
    return {
        "records": len(articles),
        "year_counts": dict(sorted(years.items())),
        "source_database_counts": dict(sources),
        "top_journals": journals.most_common(20),
        "doi_coverage": sum(bool(a.doi) for a in articles) / len(articles) if articles else 0.0,
        "abstract_coverage": sum(bool(a.abstract.strip()) for a in articles) / len(articles) if articles else 0.0,
    }
