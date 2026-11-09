# SāhityaLab

**A reproducible research workbench for literature reviews, bibliometrics, manuscript feedback, and journal responses.**

SāhityaLab (साहित्य — *sāhitya*, literature or scholarly writing) brings common research workflows into one composable Python toolkit. It helps researchers move from a documented review protocol and bibliographic exports to screening, evidence synthesis, bibliometric exploration, supervisor-feedback triage, and a traceable response-to-reviewers document.

> **Researcher remains in control.** SāhityaLab assists with organising evidence, surfacing patterns, and drafting. It does not decide study eligibility, invent references, verify claims automatically, or replace methodological judgement. All AI-generated suggestions must be checked against the underlying sources.

[![CI](https://github.com/Kronnork/SahityaLab/actions/workflows/ci.yml/badge.svg)](https://github.com/Kronnork/SahityaLab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Why SāhityaLab?

Research workflows often span disconnected tools and files: database exports, screening spreadsheets, evidence tables, bibliometric tools, Word comments, LaTeX sources, reviewer letters, and manuscript revisions. The result is duplicated effort and weak traceability between feedback, evidence, and the final paper.

SāhityaLab provides a common data model and CLI around these activities. It preserves raw source files, records decisions explicitly, exports interoperable formats, and keeps the human researcher responsible for every consequential decision.

## Capability map

| Workstream | What it supports | Output |
|---|---|---|
| Review design | Reproducible review workspace, protocol, research questions, eligibility criteria, sources and extraction fields | YAML protocol and project structure |
| Bibliographic ingestion | CSV, JSON, BibTeX, PubMed MEDLINE and OpenAlex imports; normalised article records | JSON records and import manifest |
| Deduplication and screening | DOI/title deduplication, rule-based *suggestions*, reviewer reconciliation | Duplicate log and screening register |
| Evidence synthesis | Study-characteristics/evidence table, configurable extraction fields and descriptive coverage profile | CSV, JSON and optional XLSX |
| PRISMA support | Explicit flow-count consistency checks and checklist tracker | PRISMA JSON/CSV data |
| Bibliometrics | PyBibX hand-off and isolated integration boundary | PyBibX input manifest and exported analyses |
| Supervisor feedback | Word `.docx` comments with anchors, legacy `.doc` conversion, LaTeX annotations and source locations | Structured feedback register |
| Journal responses | Reviewer-comment register, response/action/location fields, completeness checks | Response matrix in CSV/JSON/Markdown |
| AI assistance | Optional provider adapter for structured analysis and draft suggestions | JSON suggestions with provenance and review warnings |

## Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         SāhityaLab CLI / Python API               │
├───────────────────────┬────────────────────────┬─────────────────┤
│ Review workflow       │ Manuscript feedback    │ Journal workflow│
│ protocol              │ DOCX / DOC / LaTeX     │ response matrix │
│ import + deduplicate  │ text + comment anchors │ completeness    │
│ screening + adjudicate│ classify + prioritise  │ export          │
│ evidence + PRISMA     │ action register        │                 │
├───────────────────────┴────────────────────────┴─────────────────┤
│ Common models, provenance, validation, CSV / JSON / YAML exports  │
├──────────────────────────────────────────────────────────────────┤
│ Optional integrations: PyBibX | OpenAI-compatible AI | LibreOffice│
└──────────────────────────────────────────────────────────────────┘
```

The core workflow is designed to be useful without an AI key or a running external service. Optional integrations are imported only when selected.

## Installation

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

Install optional integrations as needed:

```bash
pip install -e '.[bibliometrics]'  # PyBibX integration
pip install -e '.[latex]'          # Better LaTeX-to-text conversion
pip install -e '.[bibtex]'         # Full BibTeX parser
pip install -e '.[ai]'             # OpenAI API client
pip install -e '.[excel]'          # Excel exports
pip install -e '.[all,dev]'        # Everything + development tools
```

Legacy Word `.doc` conversion requires LibreOffice (`soffice`) available on `PATH`. Native `.docx` extraction does not require Microsoft Word. LaTeX comment extraction uses SāhityaLab's documented comment conventions and works without the optional LaTeX parser; the parser improves plain-text conversion.

## Quick start

### 1. Create a review project

```bash
sahitya review init ./my-review \
  --title "Artificial Intelligence in FinTech: A Systematic Literature Review" \
  --review-type systematic_literature_review
```

This creates `protocol/review_protocol.yml`, a review manuscript outline tailored to the review type, and folders for raw data, normalised data, screening, extraction, documents and outputs. Edit the protocol and outline before running a review. Add research questions, sources, date ranges, exact search strings, inclusion/exclusion criteria, reviewer roles, extraction fields and synthesis plans.

### 2. Import database exports

```bash
sahitya records import data/scopus.csv --output outputs/records.json
sahitya records import data/wos.bib --output outputs/wos_records.json
```

Supported inputs: `.csv`, `.json`, `.bib`, `.bibtex` and PubMed MEDLINE `.txt`. OpenAlex API JSON (including inverted-index abstracts), common Scopus/WoS CSV exports and standard BibTeX fields are mapped to the common article model. CSV/JSON field names are mapped conservatively; inspect the imported metadata before using it in a review. Keep the original downloaded files unchanged in `data/raw/` and record the database, search date, query, filters and export options in the protocol/search log.

### 3. Deduplicate, screen and prepare evidence

```bash
sahitya records deduplicate outputs/records.json \
  --records-output outputs/unique_records.json \
  --duplicates-output outputs/duplicates.csv

sahitya records screen outputs/unique_records.json \
  --include-terms "artificial intelligence;machine learning;fintech" \
  --exclude-terms "editorial;book review" \
  --output outputs/screening_suggestions.json

# After reviewers update their decision fields in the register
sahitya records reconcile outputs/reviewer_decisions.json \
  --output outputs/reviewer_reconciliation.json

sahitya records evidence outputs/unique_records.json \
  --output outputs/evidence_table.csv

# Optional Excel workbook output
sahitya records evidence outputs/unique_records.json \
  --output outputs/evidence_table.xlsx
```

Rule-based screening deliberately assigns `uncertain` or `pending` suggestions; it never silently excludes a record. Human reviewers must make and record the actual inclusion decision and reasons. Use independent reviewer decisions and adjudication where required by the review design.

### 4. Check PRISMA flow counts

```bash
sahitya review prisma-check counts.json --output outputs/prisma_check.json
```

Example `counts.json`:

```json
{
  "identified": 1200,
  "duplicates_removed": 200,
  "screened": 1000,
  "records_excluded": 700,
  "full_text_sought": 300,
  "full_text_not_retrieved": 10,
  "full_text_assessed": 290,
  "full_text_excluded": 210,
  "included": 80
}
```

The checker tests arithmetic consistency; it does not certify that the counts are methodologically correct. Complete the checklist and record where each item is reported.

### 5. Run bibliometric exploration with PyBibX

```bash
pip install -e '.[bibliometrics]'
sahitya bibliometrics prepare data/scopus.csv data/wos.bib \
  --output-dir outputs/bibliometrics

# Launch the PyBibX interactive workbench
sahitya bibliometrics launch
```

PyBibX documents `pybibx.web_app()` to launch its local interface and `pybibx.web_stop()` to stop it. SāhityaLab provides CLI wrappers for both commands. The `prepare` command writes a reproducible input manifest and normalises supported records; it does not itself claim that a bibliometric analysis has run. Select the preserved source exports in the PyBibX workbench and archive its outputs alongside the manifest. See [PyBibX](https://github.com/valdecy/pybibx) for capabilities, accepted source formats and examples.

Potential bibliometric analyses include annual scientific production, most relevant sources/authors/documents, keyword co-occurrence, co-authorship and collaboration networks, co-citation, bibliographic coupling, thematic maps and topic evolution. The appropriate analysis depends on data completeness, export source and research question; interpret network and impact indicators cautiously.

### 6. Investigate supervisor comments in a manuscript

```bash
sahitya manuscript inspect manuscript.docx --output-dir outputs/supervisor_review
sahitya manuscript inspect draft.tex --output-dir outputs/latex_review

# Legacy .doc is converted via LibreOffice, if installed
sahitya manuscript inspect legacy-draft.doc --output-dir outputs/legacy_review
```

The command extracts text and comments, classifies feedback into working categories, suggests an action prompt and creates a structured register. Word comments retain author/date/comment ID and selected-text anchors where present. LaTeX comments retain file and line number.

### 7. Prepare a journal response matrix

Create a JSON array/object or CSV register with reviewer comments. JSON example:

```json
[
  {
    "reviewer": "Reviewer 1",
    "comment": "The theoretical contribution is not sufficiently distinguished from prior work.",
    "manuscript_location": "Introduction, paragraphs 4–6",
    "response": "",
    "action_taken": "",
    "topic": "theoretical contribution"
  }
]
```

Then:

```bash
sahitya journal matrix reviewer_comments.json --output-dir outputs/journal_response
sahitya journal validate outputs/journal_response/response_matrix.json
```

Each comment has an ID, reviewer, comment, severity/topic, response, action taken, manuscript location and status. Validation flags blank responses, actions or locations. It does not assume that an item is addressed simply because a response has been written; verify the revised manuscript and location before changing status.

## Document feedback formats

### Microsoft Word (`.docx`)

SāhityaLab reads the WordprocessingML package directly to recover native comments, comment metadata and marked text ranges. It also extracts paragraph/table text for contextual review. It is not a Word rendering engine: advanced layout, tracked-change semantics, footnotes, embedded objects and every possible comment-thread variant are not fully represented.

### Legacy Word (`.doc`)

`.doc` is converted to `.docx` using LibreOffice in headless mode, then processed by the same extractor. Conversion fidelity depends on the source document and LibreOffice version. The original is not modified.

### LaTeX (`.tex`, `.latex`)

Use explicit, machine-readable conventions in source comments:

```latex
% supervisor: Please make the research gap explicit.
% reviewer[major]: Clarify the sampling strategy.
% TODO[supervisor]: Add a robustness check and report the result.
```

SāhityaLab records file and line number. Normal LaTeX comments that do not use a recognised convention are ignored as review items. For collaborative review systems that store comments outside `.tex` files, export comments into a structured JSON/CSV file and map them to the common feedback model in your workflow.

### PDF

PDF text can be extracted for context, but PDF annotations are not currently extracted as supervisor comments. Convert or export feedback to DOCX/structured data where comment-level traceability is required.

## Feedback categories

The built-in deterministic classifier suggests one of the following categories:

- Theoretical contribution and novelty
- Literature coverage and positioning
- Methodology and protocol
- Analysis and results
- Discussion and implications
- Research design and scope
- Structure and clarity
- Language and presentation
- Unclassified

Severity is a suggestion (`critical`, `major`, `minor`, `editorial`, `unknown`) inferred from explicit language patterns. Inspect and revise it manually. Do not treat automatic classification as a judgement about the academic importance of a comment.

## Optional AI assistance

AI integration is intentionally opt-in. Configure an API key in the environment; never commit secrets:

```bash
export OPENAI_API_KEY="..."
export SAHITYALAB_AI_MODEL="gpt-4.1-mini"
```

The `ai` extra installs the OpenAI client. AI calls are **never automatic**; they happen only when you invoke one of the `sahitya ai` commands. The current adapter supports two bounded workflows:

```bash
# Analyse a supervisor's comments in a DOCX, DOC, LaTeX, PDF, TXT or Markdown manuscript
sahitya ai analyse-feedback manuscript.docx --output outputs/ai_feedback_analysis.json

# Draft point-by-point response options against a revised manuscript
sahitya ai draft-responses revised_manuscript.docx \
  --comments reviewer_comments.json \
  --author-context author_context.txt \
  --output outputs/ai_response_drafts.json
```

The feedback analysis groups concerns, interprets likely intent, suggests evidence or analysis to consider, and highlights patterns across comments. The response drafter distinguishes edits supported by the supplied revised manuscript from proposed edits and items that still require author verification. It does not write into or modify the manuscript. Output is structured JSON with provider/model metadata and explicit human-review flags. Manuscript text sent to the provider is capped at 60,000 characters by default; truncation is recorded in the output. Reviewer comments and optional author context are included in the request. Treat the entire supplied context as potentially sensitive.

Before invoking an AI command, check institutional, publisher and funder policies; remove confidential or identifying details unless authorised; and verify every citation, quotation, number, claim and suggested edit against the original sources. Never accept AI-generated references without independently confirming they exist and support the claim. Do not upload unpublished manuscripts or reviewer reports to a third party without permission. The AI assistant is a drafting aid, not an academic evaluator or authorial decision-maker.

## Python API

The package can be embedded in notebooks or research automation:

```python
from sahityalab.review.importers import load_records
from sahityalab.review.screening import deduplicate, screen_rule_based
from sahityalab.review.evidence import evidence_table, descriptive_profile
from sahityalab.documents.extract import extract_document
from sahityalab.documents.feedback import process_comments

records = load_records("scopus_export.csv")
unique, duplicate_log = deduplicate(records)
suggestions = screen_rule_based(
    unique,
    include_terms=["artificial intelligence", "machine learning"],
    exclude_terms=["editorial"],
)
profile = descriptive_profile(unique)
rows = evidence_table(unique)

manuscript_text, supervisor_comments = extract_document("manuscript.docx")
feedback_register = process_comments(supervisor_comments)
```

All domain objects are Pydantic models and can be serialised with `model_dump(mode="json")`.

## CLI reference

```text
sahitya --help
sahitya review init PATH --title TITLE [--review-type TYPE]
sahitya review validate PROTOCOL.yml
sahitya review prisma-check COUNTS.json --output FILE
sahitya records import FILE --output FILE
sahitya records deduplicate FILE --records-output FILE --duplicates-output FILE
sahitya records screen FILE --include-terms TERMS --exclude-terms TERMS --output FILE
sahitya records reconcile FILE --output FILE
sahitya records evidence FILE --output FILE
sahitya manuscript inspect FILE --output-dir DIR
sahitya journal matrix JSON_OR_CSV --output-dir DIR
sahitya journal validate FILE
sahitya ai analyse-feedback MANUSCRIPT --output FILE
sahitya ai draft-responses MANUSCRIPT --comments FILE --output FILE
sahitya bibliometrics prepare FILE... --output-dir DIR
sahitya bibliometrics launch
sahitya bibliometrics stop
```

Run `--help` on any command for the current option set.

## Project structure

```text
SahityaLab/
├── README.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── docs/
├── examples/
├── tests/
└── src/sahityalab/
    ├── models.py
    ├── io.py
    ├── review/          # protocols, imports, screening, evidence, PRISMA, outlines
    ├── bibliometrics/   # PyBibX adapter and launch/stop commands
    ├── documents/       # DOCX/DOC/LaTeX extraction and feedback triage
    ├── journal/         # response matrix and validation
    └── cli.py
```

## Quality and testing

```bash
pip install -e '.[dev]'
pytest
ruff check .
```

Tests use small synthetic records/documents and do not require API keys, paid databases or PyBibX. Optional-dependency integration tests can be added to your CI environment.

## Reproducibility and responsible use

- Preserve original database exports and manuscript versions; write outputs to separate folders.
- Record search dates, exact database queries, coverage periods, filters, export settings and protocol changes.
- Keep DOI/title duplicate logs; inspect potential duplicates because title matching is not infallible.
- Keep reviewer-level decisions separate; resolve disagreements according to the stated protocol.
- Record reasons for every full-text exclusion.
- Distinguish extracted evidence, author interpretation and AI-generated suggestions.
- Avoid presenting bibliometric indicators as direct measures of research quality.
- Report tools and AI use in accordance with journal, institution and funder guidance.
- Keep reviewer comments and unpublished manuscripts confidential.

## Roadmap

- [x] Common article, screening and feedback models
- [x] Review workspace and protocol validation
- [x] CSV, JSON and BibTeX import
- [x] DOI/title deduplication and reviewer decision reconciliation
- [x] Evidence table and descriptive profile
- [x] PRISMA flow arithmetic and checklist scaffold
- [x] PyBibX integration boundary and reproducible manifest
- [x] DOCX comment extraction with selected-text anchors
- [x] Optional DOC-to-DOCX conversion and LaTeX comment conventions
- [x] Journal response matrix and completeness validation
- [x] Explicit OpenAI-backed supervisor-comment analysis and response drafting
- [ ] Direct connectors for bibliographic databases and reference managers
- [ ] Full PRISMA diagram rendering and configurable review templates
- [ ] Richer `.docx` tracked-change and threaded-comment handling
- [ ] PDF annotation extraction
- [ ] Pluggable local and hosted LLM providers with evaluation harness
- [ ] GUI/notebook interface and collaborative multi-reviewer workspace

## License

SāhityaLab is released under the **MIT License**. See [LICENSE](LICENSE). Optional third-party packages and external services remain subject to their own licenses and terms.

## Acknowledgements

- [PyBibX](https://github.com/valdecy/pybibx) for bibliometric and scientometric analysis capabilities.
- The Python scientific and document-processing ecosystem, including pandas, Pydantic, python-docx, pypdf and PyYAML.

---

**SāhityaLab is a research-assistance toolkit, not a substitute for scholarly judgement, peer review, database licensing, or reporting standards.**
