from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rag import build_answer

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    result = build_answer(payload.question, top_k=5)
    return ChatResponse(answer=result["answer"], sources=result["sources"])
