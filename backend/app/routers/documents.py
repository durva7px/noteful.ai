from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import get_settings
from app.db import Document, get_session
from app.rag.ingest import ingest_document
from app.rag.loaders import SUPPORTED_TYPES
from app.rag.vectorstore import delete_document_vectors

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    error: str | None
    created_at: datetime


@router.post("", response_model=list[DocumentOut], status_code=202)
async def upload_documents(
    files: list[UploadFile],
    background: BackgroundTasks,
    session: Session = Depends(get_session),
):
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    # Validate everything first so a bad file doesn't leave a partial batch behind.
    payloads = []
    for file in files:
        name = Path(file.filename or "").name
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_TYPES:
            raise HTTPException(400, f"{name}: unsupported type. Use {', '.join(sorted(SUPPORTED_TYPES))}.")
        data = await file.read()
        if len(data) > max_bytes:
            raise HTTPException(413, f"{name}: larger than {settings.max_upload_mb} MB.")
        if not data:
            raise HTTPException(400, f"{name}: file is empty.")
        payloads.append((name, suffix, data))

    rows = []
    for name, suffix, data in payloads:
        row = Document(filename=name, file_type=suffix.lstrip("."), stored_path="")
        path = settings.upload_dir / f"{row.id}{suffix}"
        path.write_bytes(data)
        row.stored_path = str(path)
        session.add(row)
        rows.append(row)
    session.commit()

    for row in rows:
        session.refresh(row)
        background.add_task(ingest_document, row.id)
    return rows


@router.get("", response_model=list[DocumentOut])
def list_documents(session: Session = Depends(get_session)):
    return session.exec(select(Document).order_by(Document.created_at.desc())).all()


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, session: Session = Depends(get_session)):
    row = session.get(Document, doc_id)
    if row is None:
        raise HTTPException(404, "Document not found")
    if row.chunk_count:
        delete_document_vectors(doc_id)
    Path(row.stored_path).unlink(missing_ok=True)
    session.delete(row)
    session.commit()
    return Response(status_code=204)
