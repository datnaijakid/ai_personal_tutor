from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import json

from app.services.pdf_extractor import extract_text_from_pdf


router = APIRouter()


UPLOAD_DIR = Path("uploads")
EXTRACTED_DIR = Path("extracted")

UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACTED_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    pdf_path = UPLOAD_DIR / file.filename

    with open(pdf_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    pages = extract_text_from_pdf(str(pdf_path))

    extracted_data = {
        "filename": file.filename,
        "page_count": len(pages),
        "pages": pages,
    }

    json_filename = Path(file.filename).stem + ".json"
    json_path = EXTRACTED_DIR / json_filename

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(
            extracted_data,
            json_file,
            ensure_ascii=False,
            indent=2
        )

    return {
        "message": "PDF uploaded and text extracted successfully.",
        "filename": file.filename,
        "page_count": len(pages),
        "extracted_file": str(json_path),
    }