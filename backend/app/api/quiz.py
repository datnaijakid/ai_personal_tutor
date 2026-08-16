from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag import build_quiz_questions


router = APIRouter()


class QuizRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    topic: str | None = Field(default=None, max_length=240)
    question_count: int = Field(default=1, ge=1, le=10)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_option: int
    explanation: str
    source: dict


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]


@router.post("/quiz", response_model=QuizResponse)
async def quiz_endpoint(payload: QuizRequest):
    """Create one multiple-choice question from retrieved course material only."""
    result = build_quiz_questions(payload.course_id, payload.topic, payload.question_count)
    if result is None:
        raise HTTPException(
            status_code=422,
            detail="No suitable textbook material was found for this quiz yet. Upload a PDF first.",
        )
    if result == "LLM_UNAVAILABLE":
        raise HTTPException(
            status_code=503,
            detail="Quiz mode requires Ollama to be running with the configured model.",
        )
    return QuizResponse(questions=result)
