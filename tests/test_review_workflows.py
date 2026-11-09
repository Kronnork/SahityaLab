from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from lxml import etree

from sahityalab.ai.assistant import AIUnavailable, OpenAIResearchAssistant
from sahityalab.documents.extract import extract_docx, extract_latex
from sahityalab.documents.feedback import process_comments
from sahityalab.journal.responses import validate_responses
from sahityalab.models import Article, Decision, JournalComment, ScreeningDecision, SupervisorComment
from sahityalab.review.prisma import prisma_flow
from sahityalab.review.project import create_review_workspace
from sahityalab.review.screening import deduplicate, reconcile_reviewers


def test_deduplicate_prefers_doi_and_title():
    items = [Article(title="A Paper", doi="10.1/abc"), Article(title="Different title", doi="10.1/ABC"), Article(title="A Paper")]
    kept, duplicates = deduplicate(items)
    assert len(kept) == 1
    assert len(duplicates) == 2


def test_screening_reconciliation_flags_conflict():
    decisions = [ScreeningDecision(article_id="a", reviewer="one", decision=Decision.INCLUDE), ScreeningDecision(article_id="a", reviewer="two", decision=Decision.EXCLUDE)]
    result = reconcile_reviewers(decisions)["a"]
    assert result["requires_adjudication"] is True
    assert result["consensus"] == "conflict"


def test_prisma_flow_consistent():
    result = prisma_flow({"identified": 100, "duplicates_removed": 10, "screened": 90, "records_excluded": 50,
        "full_text_sought": 40, "full_text_not_retrieved": 5, "full_text_assessed": 35, "full_text_excluded": 20, "included": 15})
    assert result["internally_consistent"]


def test_supervisor_feedback_classification():
    comment = SupervisorComment(source_file="draft.docx", source_format="docx", text="Please clarify the theoretical contribution and novelty.")
    result = process_comments([comment])[0]
    assert result.category == "theoretical_contribution"
    assert result.suggested_action


def test_latex_supervisor_comment(tmp_path: Path):
    source = tmp_path / "paper.tex"
    source.write_text("\\section{Introduction}\n% supervisor: Clarify the research gap.\nThis is text.\n", encoding="utf-8")
    text, comments = extract_latex(source)
    assert "Introduction" in text
    assert len(comments) == 1
    assert comments[0].metadata["line"] == 2


def test_journal_response_validation():
    comments = [JournalComment(reviewer="R1", comment="Please explain.")]
    result = validate_responses(comments)
    assert result["incomplete_comments"] == 1
    assert set(result["issues"][0]["missing"]) == {"response", "action_taken", "manuscript_location"}


def test_review_workspace_contains_outline(tmp_path: Path):
    root = create_review_workspace(tmp_path / "workspace", "A scoping review", "scoping_review")
    outline = (root / "documents" / "review_manuscript_outline.md").read_text(encoding="utf-8")
    assert "Data charting" in outline
    assert "Study selection" in outline


def test_docx_comment_text_and_anchor(tmp_path: Path):
    source = tmp_path / "base.docx"
    document = Document()
    document.add_paragraph("Please strengthen this theoretical contribution.")
    document.save(source)
    ns_uri = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ns = {"w": ns_uri}
    temporary = tmp_path / "with_comment.docx"
    with ZipFile(source) as original, ZipFile(temporary, "w", ZIP_DEFLATED) as updated:
        for name in original.namelist():
            data = original.read(name)
            if name == "word/document.xml":
                root = etree.fromstring(data)
                p = root.xpath(".//w:body/w:p", namespaces=ns)[0]
                run = p.xpath(".//w:r[w:t]", namespaces=ns)[0]
                start = etree.Element(f"{{{ns_uri}}}commentRangeStart")
                start.set(f"{{{ns_uri}}}id", "7")
                end = etree.Element(f"{{{ns_uri}}}commentRangeEnd")
                end.set(f"{{{ns_uri}}}id", "7")
                pos = p.index(run)
                p.insert(pos, start)
                p.insert(pos + 2, end)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")
            updated.writestr(name, data)
        comments = etree.Element(f"{{{ns_uri}}}comments", nsmap={"w": ns_uri})
        comment = etree.SubElement(comments, f"{{{ns_uri}}}comment")
        comment.set(f"{{{ns_uri}}}id", "7")
        comment.set(f"{{{ns_uri}}}author", "Supervisor")
        comment.set(f"{{{ns_uri}}}date", "2026-11-09T10:00:00Z")
        cp = etree.SubElement(comment, f"{{{ns_uri}}}p")
        cr = etree.SubElement(cp, f"{{{ns_uri}}}r")
        ct = etree.SubElement(cr, f"{{{ns_uri}}}t")
        ct.text = "Please provide a sharper theoretical argument."
        updated.writestr("word/comments.xml", etree.tostring(comments, xml_declaration=True, encoding="UTF-8", standalone="yes"))
    text, comments_out = extract_docx(temporary)
    assert "theoretical contribution" in text
    assert len(comments_out) == 1
    assert comments_out[0].author == "Supervisor"
    assert comments_out[0].anchor_text == "Please strengthen this theoretical contribution."


def test_ai_assistant_requires_explicit_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        OpenAIResearchAssistant()
    except AIUnavailable as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("AI assistant must require explicit credentials")


def test_review_workspace_chooses_scoping_reporting_guideline(tmp_path: Path):
    from sahityalab.io import load_yaml
    root = create_review_workspace(tmp_path / "scoping", "Map a field", "scoping_review")
    protocol = load_yaml(root / "protocol" / "review_protocol.yml")
    assert protocol["reporting_guideline"] == "PRISMA-ScR"


def test_journal_csv_import_round_trip(tmp_path: Path):
    from sahityalab.journal.responses import load_journal_comments
    source = tmp_path / "comments.csv"
    source.write_text('reviewer,comment,response,action_taken,manuscript_location,evidence_needed\nReviewer 1,"Clarify the theory.",Response,Revised,Section 2,"New source; conceptual definition"\n', encoding="utf-8")
    comments = load_journal_comments(source)
    assert comments[0].reviewer == "Reviewer 1"
    assert comments[0].evidence_needed == ["New source", "conceptual definition"]
