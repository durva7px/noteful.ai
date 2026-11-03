import uuid
from datetime import datetime, timezone
from typing import Iterator

from sqlmodel import Field, Session, SQLModel, create_engine

from app.config import get_settings


class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    filename: str
    file_type: str
    stored_path: str
    status: str = "processing"  # processing | ready | failed
    chunk_count: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
