"""Extract manuscript text and review comments from common manuscript formats."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ..models import SupervisorComment


def _context(text: str, anchor: str | None, width: int = 220) -> str | None:
    if not anchor:
        return None
    index = text.find(anchor)
    if index < 0:
        return None
    return text[max(0, index - width): min(len(text), index + len(anchor) + width)].strip()


def extract_docx(path: str | Path) -> tuple[str, list[SupervisorComment]]:
    from docx import Document
    from lxml import etree
    p = Path(path)
    document = Document(str(p))
    parts = [para.text for para in document.paragraphs if para.text.strip()]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    body_text = "\n".join(parts)
    comments = []
    with zipfile.ZipFile(p) as archive:
        names = set(archive.namelist())
        if "word/comments.xml" not in names:
            return body_text, comments
        comments_root = etree.fromstring(archive.read("word/comments.xml"))
        document_root = etree.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        comment_map = {}
        for node in comments_root.xpath(".//w:comment", namespaces=ns):
            cid = node.get("{%s}id" % ns["w"], "")
            comment_map[cid] = {"author": node.get("{%s}author" % ns["w"]), "date": node.get("{%s}date" % ns["w"]), "text": "".join(node.xpath(".//w:t/text()", namespaces=ns)).strip()}
        anchors: dict[str, list[str]] = {cid: [] for cid in comment_map}
        for paragraph in document_root.xpath(".//w:p", namespaces=ns):
            active: set[str] = set()
            selected: dict[str, list[str]] = {}
            for child in paragraph.iter():
                local = etree.QName(child).localname
                cid = child.get("{%s}id" % ns["w"], "")
                if local == "commentRangeStart":
                    active.add(cid)
                    selected.setdefault(cid, [])
                elif local == "commentRangeEnd":
                    active.discard(cid)
                elif local == "t":
                    for current in active:
                        selected.setdefault(current, []).append(child.text or "")
            for cid, chunks in selected.items():
                anchors.setdefault(cid, []).append("".join(chunks).strip())
        for cid, item in comment_map.items():
            anchor = " ".join(x for x in anchors.get(cid, []) if x) or None
            comments.append(SupervisorComment(source_file=str(p), source_format="docx", author=item["author"], date=item["date"], text=item["text"], anchor_text=anchor, context=_context(body_text, anchor), location=f"Word comment id {cid}", metadata={"comment_id": cid}))
    return body_text, comments


def convert_legacy_doc(path: str | Path) -> Path:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        raise RuntimeError("Legacy .doc conversion requires LibreOffice (soffice) on PATH.")
    source = Path(path).resolve()
    temp_dir = Path(tempfile.mkdtemp(prefix="sahityalab_doc_"))
    proc = subprocess.run([executable, "--headless", "--convert-to", "docx", "--outdir", str(temp_dir), str(source)], capture_output=True, text=True, check=False)
    converted = temp_dir / f"{source.stem}.docx"
    if proc.returncode != 0 or not converted.exists():
        raise RuntimeError(f"LibreOffice conversion failed: {proc.stderr or proc.stdout}")
    return converted


def extract_doc(path: str | Path) -> tuple[str, list[SupervisorComment]]:
    converted = convert_legacy_doc(path)
    try:
        text, comments = extract_docx(converted)
        for comment in comments:
            comment.source_file = str(path)
            comment.source_format = "doc"
        return text, comments
    finally:
        shutil.rmtree(converted.parent, ignore_errors=True)


def extract_latex(path: str | Path) -> tuple[str, list[SupervisorComment]]:
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    try:
        from pylatexenc.latex2text import LatexNodes2Text
        plain = LatexNodes2Text().latex_to_text(source)
    except ImportError:
        plain = re.sub(r"(?<!\\)%.*", "", source)
        plain = re.sub(r"\\(cite|ref|label|begin|end)\s*\{[^}]*\}", " ", plain)
        plain = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^]]*\])?", " ", plain)
        plain = re.sub(r"[{}]", " ", plain)
    comments = []
    patterns = [
        re.compile(r"^\s*%\s*(?:supervisor|advisor|adviser|reviewer)\s*(?:\[(?P<severity>[^]]+)\])?\s*:\s*(?P<text>.+)$", re.I),
        re.compile(r"^\s*%\s*TODO\[(?P<author>[^]]+)\]\s*:\s*(?P<text>.+)$", re.I),
    ]
    for line_no, line in enumerate(source.splitlines(), 1):
        match = next((patt.match(line) for patt in patterns if patt.match(line)), None)
        if match:
            groups = match.groupdict()
            severity = (groups.get("severity") or "").casefold()
            comments.append(SupervisorComment(source_file=str(p), source_format="latex", author=groups.get("author") or "supervisor", text=(groups.get("text") or "").strip(), location=f"{p.name}:{line_no}", severity=severity if severity in {"critical", "major", "minor", "editorial"} else "unknown", metadata={"line": line_no, "source_line": line}))
    return plain, comments


def extract_pdf(path: str | Path) -> tuple[str, list[SupervisorComment]]:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages), []


def extract_document(path: str | Path) -> tuple[str, list[SupervisorComment]]:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return extract_docx(path)
    if suffix == ".doc":
        return extract_doc(path)
    if suffix in {".tex", ".latex"}:
        return extract_latex(path)
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix in {".txt", ".md"}:
        return Path(path).read_text(encoding="utf-8"), []
    raise ValueError(f"Unsupported manuscript format: {suffix}")
