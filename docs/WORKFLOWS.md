# Workflow notes

## Suggested systematic review sequence

1. Define questions, scope, eligibility criteria and planned synthesis before searching.
2. Record databases, query strings, run dates, limits, filters and export formats.
3. Keep original exports read-only in `data/raw/`.
4. Import and normalise exports; inspect unmapped fields and encoding before pooling sources.
5. Deduplicate using DOI and title; inspect the duplicate log because title matching is not infallible.
6. Run independent title/abstract screening. Rule matches are prioritisation hints only.
7. Retrieve and screen full texts; record one explicit reason for each exclusion.
8. Extract study characteristics and evidence into a pre-specified table.
9. Analyse only the included corpus. Separate descriptive bibliometrics from substantive synthesis.
10. Reconcile every reported count against the screening register and PRISMA flow.

## Suggested supervisor-comment sequence

1. Keep a dated, immutable copy of the reviewed manuscript.
2. Run `sahitya manuscript inspect` and inspect its output against the source document.
3. Confirm that anchors and locations identify the intended text; comment IDs are provenance, not globally stable identifiers.
4. Review category and severity suggestions; correct them as needed.
5. Assign an owner and action to each comment in the feedback register.
6. Make changes in a new manuscript version, not the source original.
7. Record the exact new section/page/paragraph/table/figure and explain what changed.
8. Resolve or explicitly defer every comment with a rationale.

## Suggested journal response sequence

1. Preserve the editor decision and each reviewer comment verbatim.
2. Split compound comments into independently answerable items while keeping a source reference to the original comment.
3. Respond in a respectful, evidence-led manner. Acknowledge the concern before explaining the change or reason for disagreement.
4. State the concrete action taken, not just that the manuscript was revised.
5. Identify precise manuscript locations using the journal's preferred version/page/line scheme.
6. Check the final response matrix against the final manuscript and ensure no response promises an edit that is absent from the submitted file.

## PyBibX integration boundary

SāhityaLab imports supported source exports into a common model and writes an explicit run manifest. Pass the preserved exports to the PyBibX workbench for its current analysis workflows. The adapter does not call undocumented PyBibX classes or invent a stable Python API across PyBibX versions. Record the installed PyBibX version, analysis options, input files and exported results with each study.
