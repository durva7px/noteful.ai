"""Turn an uploaded file into LangChain Documents, one per page or slide where possible."""

import re
from pathlib import Path

import docx2txt
from langchain_core.documents import Document
from pptx import Presentation
from pypdf import PdfReader

SUPPORTED_TYPES = {".pdf", ".pptx", ".docx", ".txt", ".md"}


class UnsupportedFileType(ValueError):
    pass


def _clean(text: str) -> str:
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _load_pdf(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    return [
        Document(page_content=page.extract_text() or "", metadata={"page": number})
        for number, page in enumerate(reader.pages, start=1)
    ]


def _shape_text(shape) -> list[str]:
    parts: list[str] = []
    if shape.has_text_frame:
        parts.append(shape.text_frame.text)
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    if shape.shape_type == 6:  # group
        for sub in shape.shapes:
            parts.extend(_shape_text(sub))
    return parts


def _load_pptx(path: Path) -> list[Document]:
    docs = []
    for number, slide in enumerate(Presentation(str(path)).slides, start=1):
        parts: list[str] = []
        for shape in slide.shapes:
            parts.extend(_shape_text(shape))
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text
            if notes.strip():
                parts.append(f"Speaker notes: {notes}")
        docs.append(Document(page_content="\n".join(parts), metadata={"slide": number}))
    return docs


def _load_docx(path: Path) -> list[Document]:
    return [Document(page_content=docx2txt.process(str(path)))]


def _load_text(path: Path) -> list[Document]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return [Document(page_content=raw.decode(encoding))]
        except UnicodeDecodeError:
            continue
    return []


_LOADERS = {
    ".pdf": _load_pdf,
    ".pptx": _load_pptx,
    ".docx": _load_docx,
    ".txt": _load_text,
    ".md": _load_text,
}


def load_file(path: Path) -> list[Document]:
    """Load and clean a file, dropping pages or slides with no text."""
    suffix = path.suffix.lower()
    loader = _LOADERS.get(suffix)
    if loader is None:
        raise UnsupportedFileType(f"Unsupported file type: {suffix}")
    docs = []
    for doc in loader(path):
        doc.page_content = _clean(doc.page_content)
        if doc.page_content:
            docs.append(doc)
    return docs
