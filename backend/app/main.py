import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import init_db
from app.rag.vectorstore import MissingApiKey
from app.routers import chat, documents

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    get_settings().upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Noteful API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents.router)
app.include_router(chat.router)


@app.exception_handler(MissingApiKey)
async def missing_key_handler(_: Request, exc: MissingApiKey):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "pinecone_configured": bool(settings.pinecone_api_key),
        "llm_configured": bool(settings.anthropic_api_key),
        "llm_model": settings.llm_model,
    }
