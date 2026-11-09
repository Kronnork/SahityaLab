"""Transparent, reviewer-driven screening and deduplication."""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable

from ..models import Article, Decision, ScreeningDecision


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.casefold())


def normalize_doi(doi: str | None) -> str:
    value = (doi or "").strip().casefold()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .;,")


def deduplicate(articles: Iterable[Article]) -> tuple[list[Article], list[dict[str, str]]]:
    kept: list[Article] = []
    duplicates: list[dict[str, str]] = []
    seen_doi: dict[str, str] = {}
    seen_title: dict[str, str] = {}
    for article in articles:
        doi_key = normalize_doi(article.doi)
        title_key = normalize_title(article.title)
        kept_id = seen_doi.get(doi_key) if doi_key else None
        if kept_id is None and title_key:
            kept_id = seen_title.get(title_key)
        if kept_id is not None:
            duplicates.append({"duplicate_id": article.id, "kept_id": kept_id, "title": article.title})
            if doi_key:
                seen_doi.setdefault(doi_key, kept_id)
            if title_key:
                seen_title.setdefault(title_key, kept_id)
            continue
        if doi_key:
            seen_doi[doi_key] = article.id
        if title_key:
            seen_title[title_key] = article.id
        kept.append(article)
    return kept, duplicates


def screen_rule_based(articles: Iterable[Article], include_terms: list[str], exclude_terms: list[str]) -> list[ScreeningDecision]:
    """Generate *suggestions* only. A human must confirm each decision."""
    decisions: list[ScreeningDecision] = []
    for article in articles:
        haystack = f"{article.title} {article.abstract} {' '.join(article.keywords)}".casefold()
        excluded = [term for term in exclude_terms if term.casefold() in haystack]
        included = [term for term in include_terms if term.casefold() in haystack]
        if excluded:
            decision, reasons = Decision.UNCERTAIN, [f"Potential exclusion term: {x}" for x in excluded]
        elif included:
            decision, reasons = Decision.UNCERTAIN, [f"Potential relevance term: {x}" for x in included]
        else:
            decision, reasons = Decision.PENDING, ["No configured screening terms matched; manual assessment required."]
        decisions.append(ScreeningDecision(article_id=article.id, decision=decision, reasons=reasons, reviewer="SahityaLab rule suggestion"))
    return decisions


def reconcile_reviewers(decisions: Iterable[ScreeningDecision]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[ScreeningDecision]] = defaultdict(list)
    for decision in decisions:
        grouped[decision.article_id].append(decision)
    result: dict[str, dict[str, object]] = {}
    for article_id, items in grouped.items():
        votes = {item.decision for item in items if item.decision != Decision.PENDING}
        result[article_id] = {
            "decisions": [x.model_dump(mode="json") for x in items],
            "agreement": len(votes) <= 1,
            "consensus": next(iter(votes)).value if len(votes) == 1 else ("conflict" if votes else "pending"),
            "requires_adjudication": len(votes) > 1,
        }
    return result
