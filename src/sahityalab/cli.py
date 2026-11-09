"""Command-line interface for the SāhityaLab research workbench."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print

from .bibliometrics.pybibx_adapter import launch_pybibx_webapp, prepare_inputs, stop_pybibx_webapp
from .documents.extract import extract_document
from .documents.feedback import feedback_summary, process_comments
from .io import load_yaml, write_json
from .journal.responses import create_response_workspace, load_journal_comments, validate_responses
from .review.evidence import descriptive_profile, evidence_table
from .review.importers import load_records
from .review.prisma import prisma_flow
from .review.project import create_review_workspace, validate_protocol
from .review.screening import deduplicate, screen_rule_based

app = typer.Typer(help="SāhityaLab: a reproducible workbench for scholarly research workflows.", no_args_is_help=True)
review_app = typer.Typer(help="Review design and reporting utilities.", no_args_is_help=True)
records_app = typer.Typer(help="Bibliographic record import and review utilities.", no_args_is_help=True)
manuscript_app = typer.Typer(help="Manuscript and supervisor-feedback utilities.", no_args_is_help=True)
journal_app = typer.Typer(help="Journal response-to-reviewers utilities.", no_args_is_help=True)
biblio_app = typer.Typer(help="Bibliometric analysis integration utilities.", no_args_is_help=True)
app.add_typer(review_app, name="review")
app.add_typer(records_app, name="records")
app.add_typer(manuscript_app, name="manuscript")
app.add_typer(journal_app, name="journal")
app.add_typer(biblio_app, name="bibliometrics")


def _terms(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


@review_app.command("init")
def review_init(path: Path, title: str = typer.Option(..., "--title"), review_type: str = typer.Option("systematic_literature_review", "--review-type")) -> None:
    create_review_workspace(path, title, review_type)
    print(f"[green]Created review workspace:[/green] {path.resolve()}")


@review_app.command("validate")
def review_validate(protocol: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    issues = validate_protocol(load_yaml(protocol))
    if issues:
        for issue in issues:
            print(f"[yellow]• {issue}[/yellow]")
        raise typer.Exit(1)
    print("[green]Protocol has the minimum required fields.[/green]")


@review_app.command("prisma-check")
def review_prisma_check(counts_file: Path, output: Path = typer.Option(..., "--output", "-o")) -> None:
    result = prisma_flow(json.loads(counts_file.read_text(encoding="utf-8")))
    write_json(result, output)
    print(json.dumps(result, indent=2))
    if not result["internally_consistent"]:
        raise typer.Exit(1)


@records_app.command("import")
def records_import(file: Path, output: Path = typer.Option(..., "--output", "-o")) -> None:
    items = load_records(file)
    write_json([item.model_dump(mode="json") for item in items], output)
    print(f"[green]Imported {len(items)} records[/green] → {output}")


def _read_articles(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    from .models import Article
    return [Article.model_validate(x) for x in raw]


@records_app.command("deduplicate")
def records_deduplicate(file: Path, records_output: Path = typer.Option(..., "--records-output"), duplicates_output: Path = typer.Option(..., "--duplicates-output")) -> None:
    kept, duplicates = deduplicate(_read_articles(file))
    write_json([item.model_dump(mode="json") for item in kept], records_output)
    import pandas as pd
    duplicates_output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(duplicates, columns=["duplicate_id", "kept_id", "title"]).to_csv(duplicates_output, index=False)
    print(f"Kept {len(kept)} records; identified {len(duplicates)} potential duplicates.")


@records_app.command("screen")
def records_screen(file: Path, include_terms: Optional[str] = typer.Option(None, "--include-terms"), exclude_terms: Optional[str] = typer.Option(None, "--exclude-terms"), output: Path = typer.Option(..., "--output", "-o")) -> None:
    decisions = screen_rule_based(_read_articles(file), _terms(include_terms), _terms(exclude_terms))
    write_json([item.model_dump(mode="json") for item in decisions], output)
    print(f"Created {len(decisions)} suggested screening decisions → {output}")


@records_app.command("evidence")
def records_evidence(file: Path, output: Path = typer.Option(..., "--output", "-o")) -> None:
    articles = _read_articles(file)
    rows = evidence_table(articles)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".json":
        write_json(rows, output)
    else:
        import pandas as pd
        pd.DataFrame(rows).to_csv(output, index=False, encoding="utf-8-sig")
    write_json(descriptive_profile(articles), output.with_name(f"{output.stem}_profile.json"))
    print(f"[green]Evidence table written:[/green] {output}")


@manuscript_app.command("inspect")
def manuscript_inspect(file: Path, output_dir: Path = typer.Option(..., "--output-dir", "-o")) -> None:
    text, comments = extract_document(file)
    comments = process_comments(comments)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manuscript_text.txt").write_text(text, encoding="utf-8")
    write_json([item.model_dump(mode="json") for item in comments], output_dir / "feedback_register.json")
    import pandas as pd
    pd.DataFrame([item.model_dump(mode="json") for item in comments]).to_csv(output_dir / "feedback_register.csv", index=False, encoding="utf-8-sig")
    write_json(feedback_summary(comments), output_dir / "feedback_summary.json")
    print(f"Extracted manuscript text and {len(comments)} comments → {output_dir}")


@journal_app.command("matrix")
def journal_matrix(file: Path, output_dir: Path = typer.Option(..., "--output-dir", "-o")) -> None:
    create_response_workspace(file, output_dir)
    print(f"[green]Response workspace created:[/green] {output_dir}")


@journal_app.command("validate")
def journal_validate(file: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    comments = load_journal_comments(file)
    result = validate_responses(comments)
    print(json.dumps(result, indent=2))
    if result["incomplete_comments"]:
        raise typer.Exit(1)


@biblio_app.command("prepare")
def bibliometrics_prepare(files: list[Path], output_dir: Path = typer.Option(..., "--output-dir", "-o")) -> None:
    manifest = prepare_inputs(files)
    manifest["engine"] = "pybibx"
    manifest["note"] = "Use original exports with the PyBibX workbench; manifest preparation is not analysis execution."
    write_json(manifest, output_dir / "pybibx_run_manifest.json")
    print(f"Prepared {manifest['records_imported_by_sahityalab']} records for PyBibX → {output_dir}")


@biblio_app.command("launch")
def bibliometrics_launch() -> None:
    launch_pybibx_webapp()


@biblio_app.command("stop")
def bibliometrics_stop() -> None:
    stop_pybibx_webapp()


@ai_app.command("analyse-feedback")
def ai_analyse_feedback(file: Path, output: Path = typer.Option(..., "--output", "-o")) -> None:
    from .ai.assistant import OpenAIResearchAssistant
    text, comments = extract_document(file)
    result = OpenAIResearchAssistant().analyse_supervisor_comments(text, process_comments(comments))
    write_json(result, output)
    print(f"[green]AI feedback analysis written:[/green] {output}; human verification required")


@ai_app.command("draft-responses")
def ai_draft_responses(manuscript: Path, comments_file: Path = typer.Option(..., "--comments", exists=True), output: Path = typer.Option(..., "--output", "-o"), author_context_file: Optional[Path] = typer.Option(None, "--author-context", exists=True)) -> None:
    from .ai.assistant import OpenAIResearchAssistant
    manuscript_text, _ = extract_document(manuscript)
    comments = load_journal_comments(comments_file)
    author_context = author_context_file.read_text(encoding="utf-8") if author_context_file else ""
    result = OpenAIResearchAssistant().draft_journal_responses(manuscript_text, comments, author_context)
    write_json(result, output)
    print(f"[green]AI response drafts written:[/green] {output}; human verification required")


ai_app = typer.Typer(help="Explicitly invoked, optional AI-assisted research tasks.", no_args_is_help=True)
app.add_typer(ai_app, name="ai")


if __name__ == "__main__":
    app()
