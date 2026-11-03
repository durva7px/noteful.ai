import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.rag.chain import ChatTurn, retrieve, stream_answer, to_sources

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = []
    doc_ids: list[str] | None = None


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest):
    async def events():
        try:
            results = await run_in_threadpool(retrieve, req.question, req.doc_ids)
            sources = to_sources(results)
            yield sse("sources", [s.model_dump() for s in sources])
            async for token in stream_answer(req.question, req.history, sources):
                yield sse("token", token)
            yield sse("done", {})
        except Exception as exc:  # report to the client; the stream has already started
            logger.exception("Chat failed")
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
