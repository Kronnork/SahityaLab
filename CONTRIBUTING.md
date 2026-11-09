# Contributing

Thank you for considering a contribution to SāhityaLab.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[all,dev]'
```

## Before submitting

1. Add or update tests for behaviour changes, including optional dependency boundaries where relevant.
2. Run `pytest` and `ruff check .`.
3. Keep deterministic research-processing steps separate from AI calls.
4. Preserve source provenance and never silently convert a human decision into an automated decision.
5. Update the README or workflow documentation when a command or supported format changes.
6. Do not include real unpublished manuscripts, reviewer reports, API keys or personal data in tests or examples.

## Design principles

- Human review remains mandatory for inclusion decisions, interpretation and manuscript changes.
- Raw exports and source manuscripts are never modified in place.
- Optional integrations must fail with clear installation guidance.
- AI-generated material must be identifiable as a suggestion and must not fabricate citations, findings or edits.
- Prefer interoperable JSON, CSV, YAML and Markdown outputs.
