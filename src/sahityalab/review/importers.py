"""Import bibliographic exports into a common article representation."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ..models import Article


def _first(row: dict[str, Any], *keys: str) -> Any:
    normalized = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in row.items()}
    for key in keys:
        value = normalized.get(re.sub(r"[^a-z0-9]", "", key.lower()))
        if value not in (None, "", [], "nan"):
            return value
    return None


def _split_people(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).replace(";", "|").replace(" and ", "|")
    return [x.strip() for x in text.split("|") if x.strip()]


def article_from_mapping(row: dict[str, Any], source: str | None = None) -> Article:
    year = _first(row, "year", "publication year", "publication_year", "py")
    try:
        year = int(str(year)[:4]) if year else None
    except ValueError:
        year = None
    keywords_value = _first(row, "author keywords", "keywords", "DE", "ID")
    if isinstance(keywords_value, list) and keywords_value and isinstance(keywords_value[0], dict):
        keywords_value = [item.get("display_name", item.get("name", "")) for item in keywords_value]
    keywords = _split_people(keywords_value)
    abstract = _first(row, "abstract", "description")
    if not abstract:
        inverted = _first(row, "abstract_inverted_index")
        if isinstance(inverted, dict):
            positions = [(position, word) for word, indexes in inverted.items() for position in indexes]
            abstract = " ".join(word for _, word in sorted(positions))
    authors_value = _first(row, "authors", "author", "author full names", "AU", "creator")
    if not authors_value:
        authorships = _first(row, "authorships")
        if isinstance(authorships, list):
            authors_value = [item.get("author", {}).get("display_name", "") for item in authorships if isinstance(item, dict)]
    journal_value = _first(row, "source title", "journal", "publication name", "SO")
    if not journal_value:
        primary = _first(row, "primary_location") or _first(row, "host_venue")
        if isinstance(primary, dict):
            source_obj = primary.get("source", primary)
            if isinstance(source_obj, dict):
                journal_value = source_obj.get("display_name") or source_obj.get("name")
    ids_obj = _first(row, "ids")
    doi_value = _first(row, "doi", "digital object identifier")
    if not doi_value and isinstance(ids_obj, dict):
        doi_value = ids_obj.get("doi")
    doi_value = str(doi_value or "").strip()
    doi_value = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi_value, flags=re.I)
    doi_value = re.sub(r"^doi:\s*", "", doi_value, flags=re.I).rstrip(" .;,")
    title = str(_first(row, "title", "document title", "article title", "display_name") or "Untitled record").strip()
    stable_source = source or "unspecified"
    identity_payload = json.dumps({"source": stable_source, "record": row}, sort_keys=True, ensure_ascii=False, default=str)
    stable_id = "rec_" + hashlib.sha256(identity_payload.encode("utf-8")).hexdigest()[:20]
    return Article(id=stable_id, title=title, authors=_split_people(authors_value), year=year,
                   abstract=str(abstract or ""), doi=doi_value or None, journal=str(journal_value or "") or None,
                   source_database=source, keywords=keywords,
                   url=str(_first(row, "url", "link", "document url", "id") or "") or None, raw=row)


def load_csv(path: str | Path, source: str | None = None) -> list[Article]:
    p = Path(path)
    with p.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        return [article_from_mapping(row, source or p.stem) for row in csv.DictReader(handle, dialect=dialect)]


def load_json(path: str | Path, source: str | None = None) -> list[Article]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("results", data.get("data", [data]))
    if not isinstance(data, list):
        raise ValueError("JSON export must contain a list of records or a 'results'/'data' list.")
    return [article_from_mapping(row, source or Path(path).stem) for row in data if isinstance(row, dict)]


def load_bibtex(path: str | Path, source: str | None = None) -> list[Article]:
    """Load BibTeX using bibtexparser when installed; support a conservative fallback."""
    p = Path(path)
    try:
        import bibtexparser  # type: ignore[import-not-found]
        with p.open(encoding="utf-8") as handle:
            db = bibtexparser.load(handle)
        return [article_from_mapping(entry, source or p.stem) for entry in db.entries]
    except ImportError:
        text = p.read_text(encoding="utf-8")
        entries: list[dict[str, str]] = []
        for block in re.split(r"@\w+\s*\{", text)[1:]:
            fields = dict(re.findall(r"([\w-]+)\s*=\s*[\{\"](.*?)[\}\"]\s*[,\n]", block, re.S))
            if fields:
                fields["title"] = fields.get("title", "").replace("\n", " ")
                entries.append(fields)
        if not entries:
            raise RuntimeError("Install the BibTeX extra: pip install 'sahityalab[bibtex]'") from None
        return [article_from_mapping(row, source or p.stem) for row in entries]


def load_pubmed_txt(path: str | Path, source: str | None = None) -> list[Article]:
    """Parse a basic PubMed MEDLINE text export (tag/value records)."""
    p = Path(path)
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    last_tag: str | None = None
    for line in p.read_text(encoding="utf-8-sig").splitlines() + [""]:
        if not line.strip():
            if current:
                records.append(current)
                current = {}
            last_tag = None
            continue
        if len(line) >= 6 and line[4:6] == "- ":
            tag, value = line[:4].strip(), line[6:].strip()
            if tag in {"AU", "FAU", "AD"}:
                current.setdefault(tag, []).append(value)
            elif tag in current and isinstance(current[tag], list):
                current[tag].append(value)
            else:
                current[tag] = value
            last_tag = tag
        elif last_tag:
            previous = current.get(last_tag)
            if isinstance(previous, list):
                previous[-1] = f"{previous[-1]} {line.strip()}".strip()
            else:
                current[last_tag] = f"{previous or ''} {line.strip()}".strip()
    articles = []
    for record in records:
        articles.append(Article(title=str(record.get("TI") or record.get("BTI") or "Untitled record"),
            authors=[str(x) for x in record.get("FAU", record.get("AU", []))], year=_parse_year(record.get("DP")),
            abstract=str(record.get("AB") or ""), doi=_extract_doi(record.get("AID", [])),
            journal=str(record.get("JT") or record.get("TA") or "") or None,
            source_database=source or p.stem, raw=record))
    return articles


def _parse_year(value: Any) -> int | None:
    match = re.search(r"\b(19|20)\d{2}\b", str(value or ""))
    return int(match.group(0)) if match else None


def _extract_doi(value: Any) -> str | None:
    values = value if isinstance(value, list) else [value]
    for item in values:
        match = re.search(r"10\.\d{4,9}/[^\s]+", str(item or ""), re.I)
        if match:
            return match.group(0).rstrip(".;")
    return None


def load_records(path: str | Path, source: str | None = None) -> list[Article]:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return load_csv(path, source)
    if suffix == ".json":
        return load_json(path, source)
    if suffix == ".txt":
        return load_pubmed_txt(path, source)
    if suffix in {".bib", ".bibtex"}:
        return load_bibtex(path, source)
    raise ValueError(f"Unsupported bibliographic format: {suffix}. Supported: CSV, JSON, BibTeX and PubMed MEDLINE TXT.")
