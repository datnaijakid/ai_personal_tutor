from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.chunker import chunk_pages
from app.services.pdf_processor import extract_text_from_pdf
from app.services.database import get_database
from app.services.vector_store import VectorStore

router = APIRouter()

UPLOAD_DIR = Path("uploads")
EXTRACTED_DIR = Path("extracted")
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), course_id: str = Form(..., min_length=1)):
    """Store and index one PDF without changing previously indexed documents."""
    filename = file.filename or ""
    normalized_course_id = course_id.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    if not normalized_course_id:
        raise HTTPException(status_code=400, detail="A course ID is required.")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="PDF files must be 25 MB or smaller.")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    # This UUID identifies this upload, even when a chapter is uploaded again
    # under the same filename or to a different course.
    document_id = uuid4().hex
    stored_filename = f"{document_id}.pdf"
    file_path = UPLOAD_DIR / stored_filename
    processed_path = EXTRACTED_DIR / f"{document_id}.json"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    database = get_database()
    database.create_document(document_id, normalized_course_id, Path(filename).name, stored_filename, str(processed_path))

    try:
        database.set_document_status(document_id, "processing")
        file_path.write_bytes(contents)
        pages = extract_text_from_pdf(file_path)
        raw_chunks = chunk_pages(pages)
        chunks = [
            {
                "id": f"{document_id}:chunk:{chunk.get('chunk_number', index + 1)}",
                "document_id": document_id,
                "document_name": Path(filename).name,
                "course_id": normalized_course_id,
                "page_number": chunk["page_number"],
                "chunk_number": chunk.get("chunk_number", index + 1),
                "text": chunk["text"],
            }
            for index, chunk in enumerate(raw_chunks)
        ]
        processed_document = {
            "document_id": document_id,
            "course_id": normalized_course_id,
            "original_filename": Path(filename).name,
            "stored_filename": stored_filename,
            "stored_pdf_path": str(file_path),
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "page_count": len(pages),
            "pages": pages,
            "chunk_count": len(chunks),
            "chunks": [
                {key: chunk[key] for key in ("document_id", "document_name", "course_id", "page_number", "chunk_number", "text")}
                for chunk in chunks
            ],
        }
        processed_path.write_text(json.dumps(processed_document, ensure_ascii=False, indent=2), encoding="utf-8")

        vector_store = VectorStore(collection_name="pdf_chunks")
        try:
            # add() is intentionally additive: no collection delete/rebuild occurs.
            vector_store.add_chunks(chunks)
        finally:
            vector_store.close()
        database.set_document_status(document_id, "completed")
    except Exception as error:
        database.set_document_status(document_id, "failed")
        file_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file could not be processed as a PDF.") from error

    return {
        "filename": processed_document["original_filename"],
        "document_id": document_id,
        "course_id": normalized_course_id,
        "stored_filename": stored_filename,
        "page_count": processed_document["page_count"],
        "chunk_count": processed_document["chunk_count"],
        "processed_file": str(processed_path),
        "message": "PDF uploaded and processed successfully.",
    }
