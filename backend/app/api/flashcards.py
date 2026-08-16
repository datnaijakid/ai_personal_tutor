from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag import build_flashcard


router = APIRouter()


class FlashcardRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    topic: str | None = Field(default=None, max_length=240)


class FlashcardResponse(BaseModel):
    front: str
    back: str
    source: dict


@router.post("/flashcards", response_model=FlashcardResponse)
async def flashcards_endpoint(payload: FlashcardRequest):
    """Create one flashcard from retrieved course material only."""
    result = build_flashcard(payload.course_id, payload.topic)
    if result is None:
        raise HTTPException(status_code=422, detail="No suitable textbook material was found. Upload a PDF or use a different chapter/topic.")
    if result == "LLM_UNAVAILABLE":
        raise HTTPException(status_code=503, detail="Flashcards require Ollama to be running with the configured model.")
    return FlashcardResponse(**result)
