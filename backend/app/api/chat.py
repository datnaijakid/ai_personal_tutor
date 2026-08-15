from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag import build_answer
from app.services.database import get_database

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    course_id: str = Field(..., min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    database = get_database()
    try:
        conversation_id = database.get_or_create_conversation(
            payload.course_id, payload.conversation_id
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    database.add_message(conversation_id, "user", payload.question)
    result = build_answer(payload.question, top_k=5, course_id=payload.course_id)
    database.add_message(conversation_id, "assistant", result["answer"])
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        conversation_id=conversation_id,
    )
