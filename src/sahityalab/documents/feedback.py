"""Classify and organise supervisor feedback without losing provenance."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ..models import CommentSeverity, SupervisorComment

RULES = {
    "theoretical_contribution": ["theoretical contribution", "theory", "novelty", "conceptual framework", "mechanism"],
    "literature_coverage": ["literature", "citation", "reference", "recent studies", "related work"],
    "methodology": ["method", "methodology", "sample", "sampling", "prisma", "protocol", "validity", "reliability"],
    "analysis_results": ["analysis", "result", "data", "table", "figure", "robustness", "statistical"],
    "discussion_implications": ["discussion", "implication", "interpretation", "contribution to practice"],
    "structure_clarity": ["structure", "clarity", "flow", "organise", "organize", "rewrite", "section"],
    "language_presentation": ["grammar", "language", "wording", "typo", "academic style", "proofread"],
    "research_design": ["research question", "objective", "scope", "boundary", "construct"],
}


def classify_comment(comment: SupervisorComment) -> SupervisorComment:
    text = comment.text.casefold()
    scored = [(category, sum(term in text for term in terms)) for category, terms in RULES.items()]
    best, score = max(scored, key=lambda item: item[1])
    comment.category = best if score else "unclassified"
    if comment.severity == CommentSeverity.UNKNOWN:
        if any(x in text for x in ["fundamental", "invalid", "cannot be accepted", "major concern", "must address"]):
            comment.severity = CommentSeverity.MAJOR
        elif any(x in text for x in ["typo", "grammar", "formatting", "punctuation"]):
            comment.severity = CommentSeverity.EDITORIAL
        elif any(x in text for x in ["minor", "small change", "please clarify"]):
            comment.severity = CommentSeverity.MINOR
        else:
            comment.severity = CommentSeverity.UNKNOWN
    return comment


def action_prompt(comment: SupervisorComment) -> str:
    category = comment.category
    suggestions = {
        "theoretical_contribution": "State the precise theoretical gap, explain the mechanism or boundary condition, and distinguish the contribution from adjacent theories.",
        "literature_coverage": "Identify the missing stream or seminal/recent source, explain why it is relevant, and integrate it into the argument rather than adding a citation list.",
        "methodology": "Report the design decision, rationale, data/source, procedure, and reproducibility details. Check alignment with the research questions.",
        "analysis_results": "Verify the underlying evidence, update the analysis or exhibit, and ensure each interpretation is traceable to results.",
        "discussion_implications": "Connect findings to prior literature, explain what changes theoretically or practically, and acknowledge boundary conditions.",
        "structure_clarity": "Revise the section logic and transitions while preserving the intended argument; check consistency across the manuscript.",
        "language_presentation": "Make a conservative language edit without changing claims, constructs, evidence, or authorial intent.",
        "research_design": "Make the question, objective, scope, and constructs explicit and traceable through the method and findings.",
    }
    return suggestions.get(category, "Interpret the feedback, decide on an evidence-based action, and record the decision and manuscript location.")


def process_comments(comments: Iterable[SupervisorComment]) -> list[SupervisorComment]:
    processed = []
    for comment in comments:
        comment = classify_comment(comment)
        comment.suggested_action = action_prompt(comment)
        processed.append(comment)
    return processed


def feedback_summary(comments: Iterable[SupervisorComment]) -> dict[str, object]:
    items = list(comments)
    return {
        "total": len(items),
        "by_category": dict(Counter(x.category for x in items)),
        "by_severity": dict(Counter(x.severity.value for x in items)),
        "open_items": sum(x.status.value == "open" for x in items),
    }
