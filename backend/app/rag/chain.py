"""Retrieval + generation: retrieve chunks, number them, and stream Claude's answer."""

from typing import AsyncIterator, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from app.config import get_settings
from app.rag.prompts import NO_CONTEXT, QA_PROMPT
from app.rag.vectorstore import MissingApiKey, get_vectorstore


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Source(BaseModel):
    n: int
    doc_id: str
    filename: str
    page: int | None = None
    slide: int | None = None
    score: float
    text: str


def retrieve(question: str, doc_ids: list[str] | None) -> list[tuple[Document, float]]:
    settings = get_settings()
    search_filter = {"doc_id": {"$in": doc_ids}} if doc_ids else None
    results = get_vectorstore().similarity_search_with_score(
        question, k=settings.retrieval_k, filter=search_filter
    )
    return [(doc, score) for doc, score in results if score >= settings.score_threshold]


def to_sources(results: list[tuple[Document, float]]) -> list[Source]:
    sources = []
    for n, (doc, score) in enumerate(results, start=1):
        meta = doc.metadata
        sources.append(
            Source(
                n=n,
                doc_id=meta.get("doc_id", ""),
                filename=meta.get("filename", "unknown"),
                page=int(meta["page"]) if "page" in meta else None,
                slide=int(meta["slide"]) if "slide" in meta else None,
                score=round(score, 3),
                text=doc.page_content,
            )
        )
    return sources


def format_context(sources: list[Source]) -> str:
    if not sources:
        return NO_CONTEXT
    blocks = []
    for s in sources:
        where = f", page {s.page}" if s.page else f", slide {s.slide}" if s.slide else ""
        blocks.append(f"[{s.n}] {s.filename}{where}\n{s.text}")
    return "\n\n".join(blocks)


def to_messages(history: list[ChatTurn]) -> list[BaseMessage]:
    turns = history[-get_settings().history_turns :]
    return [HumanMessage(t.content) if t.role == "user" else AIMessage(t.content) for t in turns]


def get_llm() -> ChatAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise MissingApiKey("ANTHROPIC_API_KEY is not set in backend/.env")
    return ChatAnthropic(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        output_config={"effort": settings.llm_effort},
        api_key=settings.anthropic_api_key,
    )


def stream_answer(question: str, history: list[ChatTurn], sources: list[Source]) -> AsyncIterator[str]:
    chain = QA_PROMPT | get_llm() | StrOutputParser()
    return chain.astream(
        {"context": format_context(sources), "history": to_messages(history), "question": question}
    )
