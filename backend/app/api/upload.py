import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.chunker import chunk_pages
from app.services.pdf_processor import extract_text_from_pdf
from app.services.vector_store import VectorStore

router = APIRouter()

UPLOAD_DIR = Path("uploads")
EXTRACTED_DIR = Path("extracted")
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    course_id: str = Form(..., min_length=1),
):
    filename = file.filename or ""

    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()

    if len(contents) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF files must be 25 MB or smaller.",
        )

    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    stored_filename = f"{uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / stored_filename
    processed_path = EXTRACTED_DIR / f"{file_path.stem}.json"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_bytes(contents)
        pages = extract_text_from_pdf(file_path)
        chunks = chunk_pages(pages)

        processed_document = {
            "course_id": course_id,
            "original_filename": Path(filename).name,
            "stored_filename": stored_filename,
            "stored_pdf_path": str(file_path),
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "page_count": len(pages),
            "pages": pages,
            "chunk_count": len(chunks),
            "chunks": chunks,
        }
        processed_path.write_text(
            json.dumps(processed_document, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        vector_store = VectorStore(collection_name="pdf_chunks")
        try:
            vector_store.add_chunks(
                [
                    {
                        "id": f"{stored_filename}_chunk_{chunk.get('chunk_number', index + 1)}",
                        "text": chunk["text"],
                        "page_number": chunk["page_number"],
                        "document_id": stored_filename,
                        "document": processed_document["original_filename"],
                        "course_id": course_id,
                        "chunk_number": chunk.get("chunk_number", index + 1),
                        "start_char": chunk.get("start_char", 0),
                        "end_char": chunk.get("end_char", 0),
                    }
                    for index, chunk in enumerate(chunks)
                ]
            )
        finally:
            vector_store.close()
    except Exception as error:
        file_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be processed as a PDF.",
        ) from error

    return {
        "filename": processed_document["original_filename"],
        "course_id": course_id,
        "stored_filename": stored_filename,
        "page_count": processed_document["page_count"],
        "chunk_count": processed_document["chunk_count"],
        "processed_file": str(processed_path),
        "message": "PDF uploaded and processed successfully.",
    }
