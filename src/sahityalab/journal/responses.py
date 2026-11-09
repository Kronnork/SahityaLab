"""Create and validate traceable point-by-point journal response matrices."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from collections.abc import Iterable
from typing import Any

import pandas as pd

from ..io import write_json
from ..models import JournalComment


def load_journal_comments(path: str | Path) -> list[JournalComment]:
    """Load journal comments from JSON or CSV reviewer registers."""
    source = Path(path)
    if source.suffix.casefold() == ".csv":
        with source.open(encoding="utf-8-sig", newline="") as handle:
            raw: Any = list(csv.DictReader(handle))
    else:
        raw = json.loads(source.read_text(encoding="utf-8-sig"))
        if isinstance(raw, dict):
            raw = raw.get("comments", [])
    if not isinstance(raw, list):
        raise ValueError("Journal comments must be a JSON array/object or a CSV register.")
    comments: list[JournalComment] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("comment"):
            continue
        values = dict(item)
        evidence = values.get("evidence_needed", [])
        if isinstance(evidence, str):
            values["evidence_needed"] = [part.strip() for part in evidence.split(";") if part.strip()]
        comments.append(JournalComment.model_validate(values))
    return comments


def response_rows(comments: Iterable[JournalComment]) -> list[dict[str, Any]]:
    """Flatten comments into a stable table-friendly representation."""
    rows = []
    for number, item in enumerate(comments, 1):
        rows.append({
            "id": item.id,
            "number": number,
            "reviewer": item.reviewer,
            "topic": item.topic,
            "severity": item.severity.value,
            "comment": item.comment,
            "response": item.response,
            "action_taken": item.action_taken,
            "manuscript_location": item.manuscript_location,
            "status": item.status.value,
            "evidence_needed": "; ".join(item.evidence_needed),
        })
    return rows


def validate_responses(comments: Iterable[JournalComment]) -> dict[str, Any]:
    """Report completeness gaps without asserting that a response is adequate."""
    items = list(comments)
    issues = []
    for index, item in enumerate(items, 1):
        missing = [name for name, value in (
            ("response", item.response),
            ("action_taken", item.action_taken),
            ("manuscript_location", item.manuscript_location),
        ) if not value.strip()]
        if missing:
            issues.append({"id": item.id, "number": index, "reviewer": item.reviewer, "missing": missing})
    return {
        "total_comments": len(items),
        "complete_comments": len(items) - len(issues),
        "incomplete_comments": len(issues),
        "issues": issues,
        "validation_note": "Completeness only; academic adequacy and manuscript changes require human verification.",
    }


def create_response_workspace(input_path: str | Path, output_dir: str | Path) -> Path:
    """Create JSON, CSV, Markdown and completeness report for a reviewer letter."""
    comments = load_journal_comments(input_path)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    rows = response_rows(comments)
    write_json([item.model_dump(mode="json") for item in comments], root / "response_matrix.json")
    pd.DataFrame(rows).to_csv(root / "response_matrix.csv", index=False, encoding="utf-8-sig")
    validation = validate_responses(comments)
    write_json(validation, root / "validation.json")
    lines = ["# Response to Reviewers", "", "Complete one response per reviewer comment. Verify each change in the revised manuscript.", ""]
    for row in rows:
        lines.extend([
            f"## {row['reviewer']} · Comment {row['number']}", "",
            f"**Comment**: {row['comment']}", "",
            f"**Response**: {row['response'] or '[Draft response here]'}", "",
            f"**Action taken**: {row['action_taken'] or '[Describe the manuscript change]'}", "",
            f"**Manuscript location**: {row['manuscript_location'] or '[Section, page, paragraph, table or figure]'}", "",
            f"**Status**: {row['status']}", "",
        ])
    (root / "response_to_reviewers.md").write_text("\n".join(lines), encoding="utf-8")
    return root
