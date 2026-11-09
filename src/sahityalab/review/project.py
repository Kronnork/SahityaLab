"""Create reproducible review workspaces and review protocols."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..io import write_yaml
from .templates import review_manuscript_outline

DEFAULT_PROTOCOL: dict[str, Any] = {
    "project": {"title": "Untitled review", "review_type": "systematic_literature_review", "version": "0.1"},
    "research_questions": [],
    "framework": {"name": "", "components": {}},
    "eligibility": {"inclusion": [], "exclusion": []},
    "sources": [],
    "searches": [],
    "screening": {"title_abstract_reviewers": [], "full_text_reviewers": [], "conflict_resolution": "Third reviewer"},
    "extraction_fields": ["title", "authors", "year", "methodology", "context", "findings", "limitations"],
    "synthesis": {"approach": "thematic", "planned_outputs": ["evidence_table", "narrative_synthesis"]},
    "reporting_guideline": "PRISMA 2020",
}


def create_review_workspace(path: str | Path, title: str, review_type: str = "systematic_literature_review") -> Path:
    root = Path(path)
    dirs = ["data/raw", "data/normalized", "data/screening", "data/extraction", "documents", "outputs", "protocol"]
    for item in dirs:
        (root / item).mkdir(parents=True, exist_ok=True)
    protocol = DEFAULT_PROTOCOL.copy()
    protocol["project"] = {"title": title, "review_type": review_type, "version": "0.1"}
    normalized_type = review_type.casefold().replace("-", "_").replace(" ", "_")
    protocol["reporting_guideline"] = {
        "systematic_literature_review": "PRISMA 2020",
        "scoping_review": "PRISMA-ScR",
        "integrative_review": "Journal-specific guidance; document the selected method",
        "narrative_review": "Journal-specific guidance; document the search and selection approach",
    }.get(normalized_type, "Specify the appropriate reporting guideline")
    write_yaml(protocol, root / "protocol" / "review_protocol.yml")
    (root / "documents" / "review_manuscript_outline.md").write_text(
        review_manuscript_outline(title, review_type), encoding="utf-8"
    )
    (root / "README.md").write_text(
        f"# {title}\n\nReview workspace created by SahityaLab.\n\n"
        "Keep raw exports unchanged in `data/raw/`. Record every search, screening decision, "
        "exclusion reason, and protocol amendment.\n",
        encoding="utf-8",
    )
    return root


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    if not isinstance(protocol, dict):
        return ["Protocol must be a YAML mapping/object."]
    issues: list[str] = []
    if not protocol.get("project", {}).get("title"):
        issues.append("Project title is missing.")
    if not protocol.get("research_questions"):
        issues.append("Add at least one research question.")
    eligibility = protocol.get("eligibility", {})
    if not eligibility.get("inclusion"):
        issues.append("Define inclusion criteria before screening.")
    if not eligibility.get("exclusion"):
        issues.append("Define exclusion criteria before screening.")
    if not protocol.get("sources"):
        issues.append("List the bibliographic databases or other information sources.")
    return issues
