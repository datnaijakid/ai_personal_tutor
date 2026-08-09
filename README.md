# AI Personal Tutor

AI Personal Tutor is a local-first PDF learning assistant that uploads a document, extracts its text, chunks the content, embeds those chunks with a local sentence-transformers model, and stores the vectors in a persistent ChromaDB collection for semantic search.

## Current functionality

- A Next.js web page at `http://localhost:3000` for selecting and uploading one textbook PDF.
- A chat interface branded as Professor DOTU for asking questions after uploading a textbook.
- Client-side checks for the file extension, MIME type, 25 MB size limit, and the PDF `%PDF-` header, so users receive immediate feedback.
- A FastAPI upload endpoint that repeats all validation on the server before accepting the file.
- Clear UI feedback for uploads, validation failures, and server-provided errors.
- Successful uploads are stored using a generated filename under `backend/uploads/`.
- PDF text is extracted page by page, chunked into overlapping segments, and saved under `backend/extracted/` as a JSON document.
- Each chunk is embedded with a local sentence-transformers model and inserted into a persistent ChromaDB collection named `pdf_chunks`.
- A `POST /search` endpoint performs semantic similarity search over the stored chunks.
- A `POST /chat` endpoint receives questions from the frontend chat UI.
- A health endpoint confirms the API is running.

## Processing pipeline

```text
PDF
  ↓
Extraction
  ↓
Chunks
  ↓
Embedding Model
  ↓
Vectors
  ↓
ChromaDB (pdf_chunks)
```

## Project structure

```text
backend/
  app/
    main.py                 FastAPI app and CORS config
    api/
      health.py             Health endpoint
      upload.py             PDF validation, storage, extraction, and indexing
      search.py             Semantic search route
    services/
      pdf_processor.py      PDF text extraction
      chunker.py            Overlapping chunk generation
      embeddings.py         Sentence-transformers embedding service
      vector_store.py       ChromaDB persistence and query wrapper
  uploads/                  Stored original PDF uploads
  extracted/                Processed JSON output for each upload
  chroma_db/                Persistent local ChromaDB storage
  tests/
    test_pdf_processing.py
    test_vector_store.py
frontend/
  app/
    page.tsx                Main upload page and home layout
  components/
    PDFUploader.tsx         UI and browser validation for textbook upload
    ChatWidget.tsx          Chat UI and backend `/chat` integration
  next.config.ts            Frontend API rewrites for `/upload`, `/chat`, and `/search`
```

## Requirements

- Python 3.10+ with `pip`
- Node.js 20.9+ and npm

## Run locally

Activate the project venv in one terminal and start the backend:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend targets `http://localhost:8000` by default.

### Frontend API URL

To use an API running at a different URL, create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_URL` is exposed to the browser, so it must only contain a public API URL; never a secret or API key. Restart the Next.js development server after changing it.

## Upload rules

The `POST /upload` endpoint accepts a multipart form field named `file`. A file must:

- have a `.pdf` filename extension;
- use `application/pdf` or `application/x-pdf` as its MIME type;
- be 25 MB or smaller; and
- begin with the PDF signature `%PDF-`.

Files that fail the type or signature checks return `400`; files over the size limit return `413`. A successful response includes the original filename, generated storage filename, page count, chunk count, and confirmation message.

## Search API

The `POST /search` endpoint accepts a JSON body like:

```json
{
  "query": "What is photosynthesis?",
  "top_k": 5,
  "document_id": null
}
```

- `query` is required.
- `top_k` is optional and defaults to `5`.
- `document_id` is optional and limits results to a single stored document.

The response includes the query, results, and metadata such as `document_id`, `page_number`, and `chunk_number` for each hit.

## API routes

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Returns a backend-running message. |
| `GET` | `/health` | Returns `{ "status": "OK" }`. |
| `POST` | `/upload` | Validates, stores, extracts, chunks, embeds, and indexes one PDF. |
| `POST` | `/search` | Returns the most similar stored chunks to a text query. |

## Verification

Run the backend tests in the project venv:

```powershell
cd backend
.\venv\Scripts\python -m unittest discover -s tests -v
```

Run the frontend linter:

```powershell
cd frontend
npm run lint
```

## Current limitations

- Uploaded files remain on the local filesystem; there is no database-backed user model or cleanup job yet.
- CORS is configured for the local Next.js origin (`http://localhost:3000`).
- Tutoring logic, document management, and richer chat features are not implemented yet.
