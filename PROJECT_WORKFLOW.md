# Professor DOTU: Complete Beginner's Guide

This document explains what this project does, how its pieces communicate, what happens when a person uses it, where information is kept, and how to run and develop it. It is written for someone who is new to web development.

## 1. What this project is

Professor DOTU is a study helper for PDF course material. A student creates a course in the browser, uploads one or more textbook PDFs to that course, then asks questions about the material.

The app does **not** normally read an entire textbook every time a question is asked. Instead, it prepares the PDF once at upload time. It breaks the text into small pieces, converts the pieces to numbers that represent their meaning, and saves those numbers in a searchable local database. Later, it searches for the few pieces most related to the student's question and uses them to form an answer.

This approach is called **RAG**, short for *retrieval-augmented generation*:

```text
Student question
       ↓
Find relevant textbook passages (retrieval)
       ↓
Give those passages to an AI model (generation)
       ↓
Answer with page references
```

The project has two applications that run together:

| Part | Folder | Job |
| --- | --- | --- |
| Frontend | `frontend/` | The website the student sees and clicks. |
| Backend | `backend/` | The Python service that validates PDFs, searches the textbook, and produces answers. |

Think of the frontend as the receptionist and the backend as the library worker. The receptionist accepts requests from the student. The library worker stores books, finds relevant pages, and sends a result back.

## 2. Basic words you will see

- **Browser**: Chrome, Edge, Firefox, and similar programs that display websites.
- **Frontend**: Code that runs in the browser and draws the screen.
- **Backend/API**: Code that runs on a server and handles data and logic. An API is a set of URLs the frontend can call.
- **Request**: A message sent from one program to another, such as “upload this PDF” or “answer this question.”
- **Response**: The reply to a request.
- **JSON**: A common plain-text format for structured data. It looks like `{ "name": "Biology" }`.
- **Database**: Software that stores information so it can be retrieved later.
- **Embedding**: A long list of numbers representing the approximate meaning of text. Text with similar meanings tends to have embeddings close together.
- **Vector database**: A database designed to find embeddings that are close to another embedding.
- **LLM**: Large language model; the AI that writes a natural-language answer.
- **Local-first**: Most of this project's storage and optional AI model run on the same computer as the app, rather than automatically sending files to a cloud service.

## 3. Technology used

### Frontend: Next.js, React, TypeScript

The frontend is a Next.js 16 application. Next.js uses React to build pages from components. TypeScript is JavaScript with additional checks that catch many mistakes before the app runs.

The important frontend files are:

| File | Purpose |
| --- | --- |
| `frontend/app/page.tsx` | Main page; manages the course tabs, selected course, course names, file list, and chat history while the page is open. |
| `frontend/components/PDFUploader.tsx` | File picker, browser-side PDF checks, and upload request. |
| `frontend/components/ChatWidget.tsx` | Chat screen, message list, and chat request. |
| `frontend/next.config.ts` | In local development, forwards `/upload`, `/chat`, and `/search` website requests to the backend. |
| `frontend/.env.local.example` | Example configuration for telling the frontend where the backend is. |

### Backend: Python and FastAPI

The backend is a Python application using FastAPI. FastAPI turns Python functions into web endpoints such as `POST /upload`.

The important backend files are:

| File | Purpose |
| --- | --- |
| `backend/app/main.py` | Creates the FastAPI application, enables local browser access, and registers API routes. |
| `backend/app/api/upload.py` | Checks and processes uploaded PDFs. |
| `backend/app/api/chat.py` | Receives course-scoped chat questions. |
| `backend/app/api/search.py` | Provides raw semantic-search results. |
| `backend/app/rag.py` | Coordinates search, relevance checking, sources, and answer generation. |
| `backend/app/services/pdf_processor.py` | Extracts readable text from a PDF one page at a time. |
| `backend/app/services/chunker.py` | Divides long page text into overlapping chunks. |
| `backend/app/services/embeddings.py` | Loads and uses the embedding model. |
| `backend/app/services/vector_store.py` | Saves and searches chunks in ChromaDB. |
| `backend/app/services/local_llm.py` | Talks to the optional local Ollama AI model. |

### Supporting tools

- **PyMuPDF (`fitz`)** reads text from ordinary, machine-readable PDFs.
- **sentence-transformers** runs `all-MiniLM-L6-v2`, the local embedding model.
- **ChromaDB** is the vector database.
- **Ollama** is optional software for running an LLM locally. The configured model is `qwen2.5:7b-instruct`.

## 4. Starting the project on your computer

Open two PowerShell windows. One runs the backend and one runs the frontend.

### Backend terminal

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

What these commands mean:

1. `cd backend` moves into the backend folder.
2. `python -m venv venv` creates an isolated Python environment. It avoids mixing this project's packages with other projects' packages.
3. `Activate.ps1` makes PowerShell use that isolated environment.
4. `pip install -r requirements.txt` downloads the Python packages listed by the project.
5. `uvicorn ...` starts the FastAPI web server on port 8000.

The backend is then available at `http://127.0.0.1:8000`. Visiting `/health` gives a small confirmation response.

### Frontend terminal

```powershell
cd frontend
npm install
npm run dev
```

`npm install` downloads JavaScript packages. `npm run dev` starts the development website, normally at `http://localhost:3000`.

Open that address in a browser. Keep both terminals running while using the app.

### Optional AI-answer terminal

Without Ollama, the app still finds relevant PDF text. It returns the best matching passage rather than a polished tutoring answer.

To enable generated answers, install Ollama, then run:

```powershell
ollama pull qwen2.5:7b-instruct
ollama serve
```

The model download can be several gigabytes. Ollama must run on the same machine as this backend unless you deliberately change the configured Ollama address.

## 5. What happens on the screen

### Courses

The main page begins with one course, `Untitled course`. The student can rename it or add additional courses.

Each course has:

- an ID: a unique computer-friendly value such as `first-course` or a generated UUID;
- a name: the label the student sees, such as “Biology 101”;
- a list of files shown in the sidebar; and
- a list of chat messages shown in its chat panel.

The **course ID**, not the visible name, is what keeps searches separated. Names can be changed without moving or confusing the stored PDF chunks.

At the moment, course names, displayed files, and displayed chat messages live in browser memory. They remain while the page stays open, but they do not survive a browser refresh. The PDFs and searchable chunks do remain on disk. Saving course information permanently is a future database feature.

### Uploading a PDF

When the student picks PDFs, the frontend performs quick checks before uploading:

1. The filename must end in `.pdf`.
2. The browser-reported type must be a PDF type.
3. The file must be no larger than 25 MB.
4. The first five bytes must be `%PDF-`, the standard PDF signature.

The browser then sends a `POST /upload` request. A `POST` request means “send data to the server and ask it to do something.” It contains two multipart form fields:

```text
file      = the actual PDF bytes
course_id = the active course's hidden unique ID
```

The backend repeats the safety checks. Rechecking is important because a person can bypass browser checks or call the backend directly.

## 6. The PDF-processing workflow, step by step

Here is the complete path for one accepted PDF.

```text
1. Student selects a PDF in the browser.
2. Frontend validates it and sends the PDF + active course ID to POST /upload.
3. Backend validates it again.
4. Backend gives the stored file a random UUID filename.
5. Backend saves the original PDF in backend/uploads/.
6. PyMuPDF extracts text page by page.
7. The chunker splits each page into smaller overlapping passages.
8. Backend saves a JSON record in backend/extracted/.
9. The embedding model turns each passage into numbers.
10. ChromaDB saves the numbers, passage text, and metadata in backend/chroma_db/.
11. Backend returns a success response to the browser.
12. Frontend adds the original filename to the visible course file list.
```

### Random filenames

The uploaded file is not stored under the original name. Instead, it is stored with a random UUID, for example:

```text
Original name: Introduction to Biology.pdf
Stored name:   78d4d0a1b67f4e12af01b2c3d4e5f678.pdf
```

This prevents two files with the same name from overwriting one another. The original readable name is preserved as metadata and used in sources shown to the student.

### Page extraction

`pdf_processor.py` opens the PDF and asks PyMuPDF for text on every page. Its output is conceptually like:

```json
[
  { "page_number": 1, "text": "Chapter one introduces cells..." },
  { "page_number": 2, "text": "Cells have membranes..." }
]
```

An image-only scanned PDF may have no selectable text. This project does not currently perform OCR (optical character recognition), so those PDFs may produce little or no useful searchable content.

### Chunking

Textbooks are too large to treat as a single item. The chunker uses chunks of about 500 characters with a 100-character overlap.

```text
Page text:    [---------------------------- long page ----------------------------]
Chunk 1:      [---------- 500 characters ----------]
Chunk 2:                         [---------- 500 characters ----------]
                                  ^ overlap preserves context
```

The overlap prevents an important idea at the edge of one chunk from being entirely separated from the beginning of the next chunk.

Each chunk keeps useful metadata: its source document, page number, chunk number, character start/end positions, document ID, and course ID.

### Embeddings and ChromaDB

The embedding model converts every chunk's text into a numeric vector. The exact numbers are not meant for people to read. They let the computer compare meaning, not merely exact words.

For example, “cash generated by operations” can be considered related to “operating cash flow” even if the words are not identical.

ChromaDB saves:

```text
Chunk ID        → unique ID for this stored passage
Document text   → actual passage from the PDF
Embedding       → the passage's meaning as numbers
Metadata        → course ID, document name, page number, and related details
```

New PDFs call `add_chunks`; they do not delete earlier PDFs. This is what makes multiple courses and multiple PDFs usable together.

## 7. How a chat question becomes an answer

Suppose the student is viewing Biology and asks, “What is photosynthesis?”

```text
1. ChatWidget reads the typed question.
2. It sends POST /chat with:
      { "question": "What is photosynthesis?", "course_id": "biology-id" }
3. FastAPI checks both fields are non-empty.
4. rag.py calls the vector store search.
5. The search embeds the question into numbers using the same embedding model.
6. ChromaDB finds up to five closest stored chunks.
7. ChromaDB is filtered by course_id = biology-id.
8. rag.py removes weak matches using a relevance threshold of 0.40.
9. rag.py removes duplicate text and collects document/page source labels.
10. If Ollama is available, it receives the question plus the matching passages.
11. Ollama is instructed to use only that supplied textbook context.
12. The backend sends { answer, sources } to the frontend.
13. The frontend displays the assistant answer and page sources.
```

The course filter is essential. Even if an Accounting PDF has a chunk that happens to look semantically close, a Biology chat request cannot retrieve it because its `course_id` does not match.

### Relevance guardrail

Vector databases always return the nearest available passages, even if none is actually a good answer. `rag.py` therefore requires a similarity score of at least `0.40` for chat. If no chunk reaches that score, the app says it could not find relevant material rather than pretending to know.

### When Ollama is unavailable

The app checks the local Ollama server at `http://localhost:11434/api/tags`. If it cannot connect, it does not crash. It returns the first relevant textbook passage with its source instead. This is a deliberate fallback.

### Source labels

Sources appear in a readable format like:

```text
Introduction to Biology.pdf (Page 42)
```

They show the student where the retrieved material came from. They are labels at present, not yet clickable PDF links.

## 8. The API endpoints

The backend exposes these URLs:

| Method and path | What it does |
| --- | --- |
| `GET /` | Returns a simple “backend is running” message. |
| `GET /health` | Returns `{ "status": "OK" }`; useful for checking that the backend is alive. |
| `POST /upload` | Accepts one PDF plus a required course ID; saves, extracts, chunks, embeds, and indexes it. |
| `POST /search` | Returns raw matching chunks; useful for debugging or future UI features. |
| `POST /chat` | Accepts a required question and course ID; returns an answer and sources. |

`/search` accepts a JSON body such as:

```json
{
  "query": "How does photosynthesis work?",
  "top_k": 5,
  "course_id": "biology-id",
  "document_id": null
}
```

`course_id` limits results to a course. `document_id` can further limit the search to one uploaded PDF. If both are given, both filters must match.

## 9. Where data is stored

When the backend is started from the `backend` folder, its runtime data is stored here:

| Location | Contains |
| --- | --- |
| `backend/uploads/` | Original uploaded PDF files under random filenames. |
| `backend/extracted/` | JSON records with extracted pages and chunks. |
| `backend/chroma_db/` | ChromaDB's local vector index. |

These folders are ignored by Git. That means `git commit` will not upload a student's PDFs or the generated index to GitHub.

Deleting all three folders' contents resets the document library. Deleting only the PDFs is not enough: ChromaDB could still retain searchable chunk data. Deleting only ChromaDB means PDFs remain stored but are no longer searchable until reprocessed.

The repository root also has `chroma_db/` ignored because running the backend from a different working directory can create the vector database there. Consistently starting the backend from `backend/` avoids this confusion.

## 10. Frontend-to-backend addresses

In the standard local setup, the frontend runs on port 3000 and the backend runs on port 8000.

```text
Browser → http://localhost:3000
             ↓
          Next.js frontend
             ↓
Backend → http://127.0.0.1:8000
```

For local requests without a custom API URL, Next.js rewrites `/upload`, `/chat`, and `/search` to the FastAPI backend.

For a separate or deployed backend, copy the example file:

```powershell
cd frontend
Copy-Item .env.local.example .env.local
```

Then set:

```dotenv
NEXT_PUBLIC_API_URL=https://your-backend.example.com
```

`NEXT_PUBLIC_API_URL` is visible to every browser user. It must contain only a public address, never passwords, private keys, or API keys.

## 11. Testing and checks

### Backend tests

The backend tests live in `backend/tests/`.

- `test_pdf_processing.py` checks PDF text extraction, chunk overlap, invalid chunk settings, and upload processing.
- `test_vector_store.py` checks adding/searching chunks, course filtering, chat sources, local-LLM behavior, and irrelevant-result behavior.

Run them after activating the backend virtual environment:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Frontend checks

```powershell
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

- Lint checks for common code-quality problems.
- TypeScript checking catches incompatible props and values.
- The production build checks whether Next.js can prepare a deployable version.

## 12. Important current limitations

This is a solid local prototype, but it is not yet a finished multi-user service.

1. Course names, displayed file lists, and chat history are browser memory only. Refreshing the page clears that UI state.
2. There are no user accounts. Anyone who can use the same backend shares its document index.
3. There is no permanent relational database for courses, users, messages, or document records.
4. There is no delete-one-document endpoint or UI yet.
5. Scanned/image-only PDFs need OCR support.
6. The local Ollama option needs adequate disk space, memory, and hardware.
7. Sources are text labels, not clickable links to an exact PDF page.
8. No production authentication, rate limiting, file scanning, backups, privacy policy, or data-deletion workflow has been added yet.

## 13. What to improve next

A sensible development order is:

1. Add persistent course, document, and chat records in a database.
2. Add document management: list from the backend, delete one document, and remove its chunks from ChromaDB.
3. Make sources open the PDF at the cited page.
4. Add study actions: chapter summary, flashcards, quiz generation, and weak-topic tracking.
5. Add OCR for scanned PDFs.
6. Add login/accounts and make every database/vector query owned by the signed-in user.
7. Add production security and deployment configuration.

## 14. Publishing choices

### Website first

The easiest first public release is a hosted website. Users only need a browser. A deployed version needs a hosted frontend, hosted FastAPI backend, persistent file storage, a database, and an AI strategy.

For public use, you would usually replace or supplement the local Ollama model with a managed LLM API or your own properly hosted model server. Do not expose a machine running a local development server directly to the public internet.

### Windows executable later

A Windows `.exe` could package the frontend in a desktop wrapper such as Tauri or Electron. It could use the hosted backend, or a more difficult offline mode could bundle Python, ChromaDB, the embedding model, and optional Ollama support.

The offline route offers privacy but creates a much larger installer and more complicated updates. Building the website first is usually the simpler path.

## 15. A short mental model to remember

```text
Frontend: “What did the student click or type?”
Backend:  “Validate it and do the work.”
PDF tool: “Turn PDF pages into text.”
Chunker:  “Split text into useful passages.”
Embeddings:“Turn meanings into numbers.”
ChromaDB: “Find passages with similar meanings.”
RAG:      “Use those passages to answer safely.”
Ollama:   “Write the answer in tutor-like language.”
```

If something goes wrong, use that sequence to locate the area: upload problem, extraction problem, indexing/search problem, or answer-generation problem.
