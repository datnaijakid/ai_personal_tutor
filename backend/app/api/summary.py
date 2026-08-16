from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag import build_chapter_summary


router = APIRouter()


class SummaryRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1, max_length=240)


class SummaryResponse(BaseModel):
    title: str
    points: list[str]
    sources: list[dict]


@router.post("/summary", response_model=SummaryResponse)
async def summary_endpoint(payload: SummaryRequest):
    result = build_chapter_summary(payload.course_id, payload.topic)
    if result is None:
        raise HTTPException(status_code=422, detail="No matching textbook material was found for that chapter or topic.")
    if result == "LLM_UNAVAILABLE":
        raise HTTPException(status_code=503, detail="Summaries require Ollama to be running with the configured model.")
    return SummaryResponse(**result)
