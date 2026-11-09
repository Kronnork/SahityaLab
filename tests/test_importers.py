import json
from pathlib import Path

from sahityalab.review.importers import load_records


def test_csv_import_maps_common_fields(tmp_path: Path):
    file = tmp_path / "export.csv"
    file.write_text('Title,Authors,Year,DOI,Abstract\n"A study","Smith, J; Doe, A",2024,10.1234/test,"An abstract"\n', encoding="utf-8")
    records = load_records(file)
    assert len(records) == 1
    assert records[0].title == "A study"
    assert records[0].year == 2024
    assert records[0].doi == "10.1234/test"


def test_json_import(tmp_path: Path):
    file = tmp_path / "export.json"
    file.write_text(json.dumps({"results": [{"title": "Paper", "publication year": "2022"}]}), encoding="utf-8")
    assert load_records(file)[0].year == 2022


def test_openalex_json_mapping(tmp_path: Path):
    file = tmp_path / "openalex.json"
    payload = {"results": [{"id": "https://openalex.org/W1", "display_name": "An OpenAlex paper", "publication_year": 2023,
        "doi": "https://doi.org/10.1000/xyz", "authorships": [{"author": {"display_name": "Jane Researcher"}}],
        "abstract_inverted_index": {"Research": [0], "matters.": [1]}, "primary_location": {"source": {"display_name": "Journal of Tests"}}}]}
    file.write_text(json.dumps(payload), encoding="utf-8")
    article = load_records(file)[0]
    assert article.title == "An OpenAlex paper"
    assert article.authors == ["Jane Researcher"]
    assert article.abstract == "Research matters."
    assert article.doi == "10.1000/xyz"
    assert article.journal == "Journal of Tests"


def test_pubmed_medline_import(tmp_path: Path):
    file = tmp_path / "pubmed.txt"
    file.write_text("PMID- 12345\nTI  - A PubMed article\nAU  - Doe J\nFAU - Doe, Jane\nDP  - 2021 Jan\nJT  - Journal Example\nAID - 10.5555/demo [doi]\nAB  - First sentence.\n      Second sentence.\n\n", encoding="utf-8")
    article = load_records(file)[0]
    assert article.title == "A PubMed article"
    assert article.authors == ["Doe, Jane"]
    assert article.year == 2021
    assert article.doi == "10.5555/demo"
    assert "Second sentence" in article.abstract


def test_imported_record_ids_are_deterministic(tmp_path: Path):
    file = tmp_path / "stable.csv"
    file.write_text('Title,Year\n"A reproducible record",2024\n', encoding="utf-8")
    assert load_records(file)[0].id == load_records(file)[0].id
