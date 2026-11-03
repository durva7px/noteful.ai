"""Ingestion pipeline: load -> clean -> split -> embed -> upsert."""

import logging
import time
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import Session

from app.config import get_settings
from app.db import Document as DocumentRow
from app.db import engine
from app.rag.loaders import load_file
from app.rag.vectorstore import get_vectorstore, namespace_vector_count

logger = logging.getLogger(__name__)

INDEX_WAIT_SECONDS = 20


def split_documents(docs: list[Document], doc_id: str, filename: str, file_type: str) -> list[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata.update(
            {"doc_id": doc_id, "filename": filename, "file_type": file_type, "chunk_index": i}
        )
    return chunks


def _wait_until_indexed(expected_count: int) -> None:
    """Pinecone is eventually consistent; wait until new vectors are queryable."""
    deadline = time.monotonic() + INDEX_WAIT_SECONDS
    while time.monotonic() < deadline:
        if namespace_vector_count() >= expected_count:
            return
        time.sleep(1)
    logger.warning("Timed out waiting for Pinecone to index %s vectors", expected_count)


def ingest_document(doc_id: str) -> None:
    """Background task: index one uploaded file and record the outcome."""
    with Session(engine) as session:
        row = session.get(DocumentRow, doc_id)
        if row is None:
            return
        try:
            docs = load_file(Path(row.stored_path))
            if not docs:
                raise ValueError("No extractable text found (the file may be scanned or image-only).")
            chunks = split_documents(docs, row.id, row.filename, row.file_type)
            store = get_vectorstore()
            before = namespace_vector_count()
            store.add_documents(chunks, ids=[f"{row.id}#{c.metadata['chunk_index']}" for c in chunks])
            _wait_until_indexed(before + len(chunks))
            row.status, row.chunk_count, row.error = "ready", len(chunks), None
        except Exception as exc:  # surface any failure to the UI instead of leaving "processing"
            logger.exception("Ingestion failed for %s", doc_id)
            row.status, row.error = "failed", str(exc)
        session.add(row)
        session.commit()
