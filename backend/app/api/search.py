from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.vector_store import VectorStore

router = APIRouter()

vector_store = VectorStore()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)
    document_id: str | None = None
    course_id: str | None = None


@router.post("/search")
async def search_documents(payload: SearchRequest):
    results = vector_store.search(
        query=payload.query,
        top_k=payload.top_k,
        document_id=payload.document_id,
        course_id=payload.course_id,
    )

    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "document_id": payload.document_id,
        "course_id": payload.course_id,
        "results": results,
    }
