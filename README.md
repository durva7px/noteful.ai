# Noteful

A local RAG study assistant. Upload PDFs, PowerPoint decks and notes, then ask questions and get answers grounded in your material, with citations to the page or slide.

- **Frontend:** Next.js 15, Tailwind CSS (`frontend/`)
- **Backend:** FastAPI + LangChain (`backend/`)
- **Vector DB and embeddings:** Pinecone serverless index with hosted `llama-text-embed-v2`
- **LLM:** Claude Sonnet 5.5 via `langchain-anthropic`

## Setup

You need Python 3.12, Node 20+, [uv](https://docs.astral.sh/uv/) (or plain `pip`), a [Pinecone](https://app.pinecone.io) API key, and an [Anthropic](https://console.anthropic.com) API key.

### Backend

```bash
cd backend
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
cp .env.example .env   # then fill in PINECONE_API_KEY and ANTHROPIC_API_KEY
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

The Pinecone index `noteful` (1024 dims, cosine) is created automatically on the first upload. API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000.

## How it works

1. **Upload:** `POST /api/documents` saves the file and records it in SQLite. A background task then loads it (one document per PDF page or slide, including speaker notes), splits it into 1,000-character chunks with 150 overlap, embeds them with Pinecone, and upserts them with ids `{doc_id}#{chunk}`.
2. **Ask:** `POST /api/chat` retrieves the top 6 chunks (optionally limited to selected documents), numbers them as context, and streams Claude's answer as server-sent events: `sources`, then `token` events, then `done`.
3. **Cite:** the UI turns `[n]` markers into chips that open the source passage.

Supported types: `.pdf`, `.pptx`, `.docx`, `.txt`, `.md`, up to 25 MB each. Scanned PDFs (no text layer) and legacy `.ppt` / `.doc` files are not supported.

## Configuration

All settings live in `backend/app/config.py` and can be overridden in `backend/.env`: `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_K`, `SCORE_THRESHOLD`, `LLM_MODEL`, `PINECONE_INDEX`, `PINECONE_REGION`, and more.

## Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest
```

The tests run offline. They generate sample PDF, PPTX and DOCX files and check the loaders, chunking, context formatting, and the API's behaviour when keys are missing.
