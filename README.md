# AI Personal Tutor (Professor DOTU)

A local-first PDF learning assistant. Upload a textbook PDF, and the app extracts its text, chunks the content, embeds those chunks with a local sentence-transformers model, and stores the vectors in a persistent ChromaDB collection for semantic search. You can then ask questions through a chat interface branded as **Professor DOTU**, which retrieves the most relevant passages and builds an answer.

## Features

- **PDF upload** with client-side and server-side validation (extension, MIME type, 25 MB size limit, `%PDF-` header).
- **Text extraction** page by page via PyMuPDF.
- **Chunking** into overlapping segments with configurable chunk size and overlap.
- **Embeddings** computed locally with the `all-MiniLM-L6-v2` sentence-transformers model.
- **Persistent vector store** using ChromaDB (`pdf_chunks` collection) for semantic similarity search.
- **RAG chat** (`Professor DOTU`) that retrieves relevant chunks and optionally generates an answer with a local Ollama LLM (falls back to a context summary when no LLM is available).
- **Semantic search API** returning ranked chunks with metadata (document, page, score).
- **Next.js frontend** with a clean, responsive two-panel layout (upload left, chat right).

## Tech stack

| Layer          | Technology                                       |
| -------------- | ------------------------------------------------ |
| Backend        | Python 3.10+, FastAPI, Uvicorn                   |
| PDF processing | PyMuPDF                                          |
| Embeddings     | sentence-transformers (`all-MiniLM-L6-v2`)       |
| Vector store   | ChromaDB (persistent, cosine space)              |
| Optional LLM   | Ollama (`qwen2.5:7b-instruct`)                   |
| Frontend       | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + CORS config
│   │   ├── rag.py                  # RAG retrieval + answer builder
│   │   ├── api/
│   │   │   ├── health.py           # GET /health
│   │   │   ├── upload.py           # POST /upload (validate, store, extract, index)
│   │   │   ├── search.py           # POST /search (semantic search)
│   │   │   └── chat.py             # POST /chat (RAG chat)
│   │   └── services/
│   │       ├── pdf_processor.py    # PDF text extraction
│   │       ├── chunker.py          # Overlapping chunk generation
│   │       ├── embeddings.py       # Sentence-transformers embedding service
│   │       ├── vector_store.py     # ChromaDB persistence + query wrapper
│   │       └── local_llm.py        # Optional Ollama client
│   ├── uploads/                    # Stored original PDF files (gitignored)
│   ├── extracted/                  # Processed JSON per upload (gitignored)
│   ├── chroma_db/                  # Persistent ChromaDB storage (gitignored)
│   ├── requirements.txt
│   └── tests/
│       ├── test_pdf_processing.py
│       └── test_vector_store.py
└── frontend/
    ├── app/
    │   ├── layout.tsx
    │   └── page.tsx                # Main upload + chat page
    ├── components/
    │   ├── PDFUploader.tsx         # Upload UI + browser validation
    │   └── ChatWidget.tsx          # Chat UI + backend /chat integration
    ├── next.config.ts              # API rewrites for /upload, /chat, /search
    └── package.json
```

## Requirements

- Python 3.10+ with `pip`
- Node.js 20.9+ and npm

## Run locally

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend runs at `http://127.0.0.1:8000`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`.

> **Using a separate backend, Docker, VM, or deployed site?** Before starting the frontend, create its local configuration file from the committed template:
>
> ```powershell
> Copy-Item .env.local.example .env.local
> ```
>
> Then set `NEXT_PUBLIC_API_URL` in `.env.local` to the public or network-reachable URL of the FastAPI backend. `.env.local` is intentionally ignored by Git because deployments may use different addresses; `.env.local.example` is included in the repository as the required setup template.

### 3. Open the app

Open `http://localhost:3000`, upload a textbook PDF, then ask Professor DOTU questions about it.

### Frontend API URL

For the standard local setup, no `.env.local` file is required: the frontend uses its `/chat`, `/upload`, and `/search` rewrites, which target the backend at `http://127.0.0.1:8000`.

When the frontend must reach a backend at a different address, create `frontend/.env.local` from the tracked template:

```powershell
cd frontend
Copy-Item .env.local.example .env.local
```

Then update the value as needed:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_URL` is exposed to the browser, so it must only contain a public URL — never a secret or API key. Restart the Next.js dev server after changing it.

### Optional: local LLM (Ollama)

The `/chat` endpoint uses a local Ollama model when available and otherwise falls back to showing relevant excerpts from the uploaded PDF. This fallback is expected behaviour, but it means the app is not generating a tutor-style answer yet.

To enable AI-generated answers, install [Ollama](https://ollama.com/) on the **same machine that runs the FastAPI backend**, then run:

```powershell
ollama pull qwen2.5:7b-instruct
ollama serve
```

In a second terminal, confirm that Ollama and the model are available:

```powershell
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

`ollama list` must include `qwen2.5:7b-instruct`, and the API command must return a response. Start the FastAPI backend only after Ollama is available, or restart the backend after starting Ollama.

#### Ollama troubleshooting

If chat responses begin with `Based on the uploaded material:` and list PDF text, the backend could not generate an answer. Check the following:

- Run `ollama serve` and keep it running while the backend is running.
- Run `ollama pull qwen2.5:7b-instruct` if `ollama list` does not show the model.
- Ensure port `11434` is not blocked by a local firewall.
- If the backend runs in Docker, a VM, or a remote server, `localhost:11434` refers to that backend environment, **not** your own computer. Run Ollama in the same environment or change the Ollama base URL in `backend/app/services/local_llm.py` to an address reachable from the backend.

The default model and Ollama address (`http://localhost:11434`) are currently configured in `backend/app/services/local_llm.py`.

## API routes

| Method | Route     | Description                                                       |
| ------ | --------- | ----------------------------------------------------------------- |
| `GET`  | `/`       | Returns a backend-running message.                                |
| `GET`  | `/health` | Returns `{ "status": "OK" }`.                                     |
| `POST` | `/upload` | Validates, stores, extracts, chunks, embeds, and indexes one PDF. |
| `POST` | `/search` | Returns the most similar stored chunks to a text query.           |
| `POST` | `/chat`   | Retrieves relevant chunks and returns an answer with sources.     |

### Upload rules

`POST /upload` accepts a multipart form field named `file`. A file must:

- have a `.pdf` filename extension;
- use `application/pdf` or `application/x-pdf` as its MIME type;
- be 25 MB or smaller; and
- begin with the PDF signature `%PDF-`.

Files that fail the type or signature checks return `400`; files over the size limit return `413`. A successful response includes the original filename, generated storage filename, page count, chunk count, and confirmation message.

### Search API

`POST /search` accepts a JSON body:

```json
{
  "query": "What is photosynthesis?",
  "top_k": 5,
  "document_id": null
}
```

- `query` is required.
- `top_k` is optional and defaults to `5` (accepted range `1–25`).
- `document_id` is optional and limits results to a single stored document.

The response includes the query, results, and metadata such as `document_id`, `page_number`, `chunk_number`, and `score` for each hit.

### Chat API

`POST /chat` accepts a JSON body:

```json
{
  "question": "Explain the conceptual framework."
}
```

The response includes an `answer` and a list of `sources` (document + page references).
For chat, the app only includes sources whose semantic-similarity score meets the built-in relevance threshold. Questions that are not covered by the uploaded material return a no-match response with no sources.

## Processing pipeline

```text
PDF
  ↓
Extraction (PyMuPDF, page by page)
  ↓
Chunks (overlapping, JSON-serializable)
  ↓
Embedding Model (all-MiniLM-L6-v2)
  ↓
Vectors
  ↓
ChromaDB (pdf_chunks)
  ↓
Semantic Search / RAG Chat
```

## Verification

### Backend tests

```powershell
cd backend
.\venv\Scripts\python -m unittest discover -s tests -v
```

### Frontend lint

```powershell
cd frontend
npm run lint
```

## Current limitations

- Uploaded files remain on the local filesystem; there is no database-backed user model or cleanup job yet.
- CORS is configured for the local Next.js origin (`http://localhost:3000`).
- Richer tutoring features and multi-document management are not implemented yet.
