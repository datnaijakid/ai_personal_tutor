from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.database import get_database
from app.services.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


class RenameDocumentRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)


def _document_or_404(document_id: str, course_id: str) -> dict[str, str]:
    document = get_database().get_document(document_id)
    if not document or document["course_id"] != course_id:
        raise HTTPException(status_code=404, detail="Document not found in this course.")
    return document


def _index_document(document: dict[str, str]) -> None:
    processed_path = Path(document["processed_path"])
    payload = json.loads(processed_path.read_text(encoding="utf-8"))
    chunks = [
        {
            "id": f"{document['document_id']}:chunk:{chunk['chunk_number']}",
            "document_id": document["document_id"],
            "document_name": document["filename"],
            "course_id": document["course_id"],
            "page_number": chunk["page_number"],
            "chunk_number": chunk["chunk_number"],
            "text": chunk["text"],
        }
        for chunk in payload["chunks"]
    ]
    store = VectorStore()
    try:
        store.delete_document(document["document_id"], document["course_id"])
        store.add_chunks(chunks)
    finally:
        store.close()


@router.get("")
async def list_documents(course_id: str = Query(..., min_length=1)):
    return {"documents": get_database().list_documents(course_id)}


@router.patch("/{document_id}")
async def rename_document(document_id: str, payload: RenameDocumentRequest):
    document = _document_or_404(document_id, payload.course_id)
    filename = Path(payload.filename).name.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="A document name is required.")
    database = get_database()
    database.rename_document(document_id, payload.course_id, filename)
    document["filename"] = filename
    try:
        database.set_document_status(document_id, "processing")
        _index_document(document)
        database.set_document_status(document_id, "completed")
    except Exception as error:
        database.set_document_status(document_id, "failed")
        raise HTTPException(status_code=400, detail="The document could not be renamed and synchronized.") from error
    return database.get_document(document_id)


@router.post("/{document_id}/reindex")
async def reindex_document(document_id: str, course_id: str = Query(..., min_length=1)):
    document = _document_or_404(document_id, course_id)
    database = get_database()
    try:
        database.set_document_status(document_id, "processing")
        _index_document(document)
        database.set_document_status(document_id, "completed")
    except Exception as error:
        database.set_document_status(document_id, "failed")
        raise HTTPException(status_code=400, detail="The document could not be re-indexed.") from error
    return database.get_document(document_id)


@router.delete("/{document_id}")
async def delete_document(document_id: str, course_id: str = Query(..., min_length=1)):
    document = _document_or_404(document_id, course_id)
    store = VectorStore()
    try:
        store.delete_document(document_id, course_id)
    finally:
        store.close()
    get_database().delete_document(document_id, course_id)
    for path in (Path(document["processed_path"]), Path("uploads") / document["stored_filename"]):
        path.unlink(missing_ok=True)
    return {"deleted": True, "document_id": document_id}


@router.get("/{document_id}/file")
async def document_file(document_id: str, course_id: str = Query(..., min_length=1)):
    document = _document_or_404(document_id, course_id)
    path = Path("uploads") / document["stored_filename"]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored PDF not found.")
    # Omit a filename so browsers render the PDF inline for citation previews.
    return FileResponse(path, media_type="application/pdf")
