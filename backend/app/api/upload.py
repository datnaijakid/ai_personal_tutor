import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    filename = file.filename or ""

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

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    metadata = {
        "original_filename": Path(filename).name,
        "stored_filename": stored_filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
    }
    metadata_path = UPLOAD_DIR / f"{file_path.stem}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "filename": metadata["original_filename"],
        "stored_filename": stored_filename,
        "message": "PDF uploaded successfully"
    }
