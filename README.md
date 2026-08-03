# AI Personal Tutor

AI Personal Tutor is an early-stage web application for uploading a PDF textbook to a local FastAPI service. The current experience is focused on a secure, validated upload flow; it does not yet provide tutoring, PDF reading, accounts, or persistent database storage.

## Current functionality

- A Next.js web page at `http://localhost:3000` for selecting and uploading one textbook PDF.
- Client-side checks for the file extension, MIME type, 25 MB size limit, and the PDF `%PDF-` header, so users receive immediate feedback.
- A FastAPI upload endpoint that repeats all validation. Server validation is authoritative, so a bypassed or modified browser request is still rejected.
- Clear UI feedback for uploads, validation failures, and server-provided errors.
- Successful uploads are stored using a generated filename under `backend/uploads/`, alongside a JSON metadata file containing the original filename, stored filename, content type, and size.
- A health endpoint for confirming that the API is running.

## Project structure

```
backend/                 FastAPI service
  app/main.py            API application and CORS configuration
  app/api/upload.py      PDF validation and local storage endpoint
  app/api/health.py      Health-check endpoint
  uploads/               Locally stored uploads and metadata (runtime data)
frontend/                Next.js application
  app/page.tsx           Home page
  components/PDFUploader.tsx
                          Upload form and client-side validation
```

## Requirements

- Python 3.10+ with `pip`
- Node.js 20.9+ and npm

## Run locally

Start the backend in one terminal:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
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

`NEXT_PUBLIC_API_URL` is exposed to the browser, so it must only contain a public API URL—never a secret or API key. Restart the Next.js development server after changing it.

## Upload rules

The `POST /upload` endpoint accepts a multipart form field named `file`. A file must:

- have a `.pdf` filename extension;
- use `application/pdf` or `application/x-pdf` as its MIME type;
- be 25 MB or smaller; and
- begin with the PDF signature `%PDF-`.

Files that fail the type or signature checks return `400`; files over the size limit return `413`. A successful response includes the original filename, generated storage filename, and confirmation message.

## API routes

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Returns a backend-running message. |
| `GET` | `/health` | Returns `{ "status": "OK" }`. |
| `POST` | `/upload` | Validates and saves one PDF received in the `file` field. |

## Verification

Run the frontend linter:

```powershell
cd frontend
npm run lint
```

## Current limitations

- Uploaded files remain on the local filesystem; there is no database, cloud storage, user ownership model, or cleanup job.
- CORS is configured for the local Next.js origin (`http://localhost:3000`).
- The application currently ends after a successful upload—tutoring, text extraction, and document management are not implemented yet.
