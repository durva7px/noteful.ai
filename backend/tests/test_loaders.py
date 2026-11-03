from pathlib import Path

import pytest
from langchain_core.documents import Document

from app.rag.chain import format_context, to_sources
from app.rag.ingest import split_documents
from app.rag.loaders import UnsupportedFileType, load_file


def test_pdf_one_document_per_page(sample_files):
    docs = load_file(sample_files["pdf"])
    assert [d.metadata["page"] for d in docs] == [1, 2]
    assert "Calvin cycle" in docs[1].page_content


def test_pptx_one_document_per_slide_with_notes(sample_files):
    docs = load_file(sample_files["pptx"])
    assert [d.metadata["slide"] for d in docs] == [1, 2]
    assert "Newton's Laws" in docs[0].page_content
    assert "Speaker notes: Mention inertia" in docs[0].page_content
    assert "F = ma" in docs[1].page_content


def test_docx_and_markdown(sample_files):
    assert "Mitochondria" in load_file(sample_files["docx"])[0].page_content
    assert "Energy cannot be created" in load_file(sample_files["md"])[0].page_content


def test_unsupported_type(tmp_path: Path):
    path = tmp_path / "old.ppt"
    path.write_bytes(b"x")
    with pytest.raises(UnsupportedFileType):
        load_file(path)


def test_split_keeps_metadata_and_numbers_chunks():
    docs = [Document(page_content="word " * 600, metadata={"page": 3})]
    chunks = split_documents(docs, "abc", "notes.pdf", "pdf")
    assert len(chunks) > 1
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert all(c.metadata["page"] == 3 and c.metadata["doc_id"] == "abc" for c in chunks)
    assert all(len(c.page_content) <= 1000 for c in chunks)


def test_context_is_numbered_with_locations():
    results = [
        (Document(page_content="Alpha", metadata={"doc_id": "a", "filename": "a.pdf", "page": 2.0}), 0.8),
        (Document(page_content="Beta", metadata={"doc_id": "b", "filename": "b.pptx", "slide": 4.0}), 0.6),
    ]
    context = format_context(to_sources(results))
    assert "[1] a.pdf, page 2\nAlpha" in context
    assert "[2] b.pptx, slide 4\nBeta" in context
