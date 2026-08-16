from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.database import get_database


router = APIRouter()


class ConversationRenameRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)


@router.get("/conversations")
async def list_conversations(course_id: str = Query(..., min_length=1)):
    return {"conversations": get_database().list_conversations(course_id)}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, course_id: str = Query(..., min_length=1)):
    messages = get_database().get_conversation(conversation_id, course_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"conversation_id": conversation_id, "messages": messages}


@router.patch("/conversations/{conversation_id}")
async def rename_conversation(conversation_id: str, payload: ConversationRenameRequest):
    if not get_database().rename_conversation(conversation_id, payload.course_id, payload.title):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"conversation_id": conversation_id, "title": payload.title.strip()}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, course_id: str = Query(..., min_length=1)):
    if not get_database().delete_conversation(conversation_id, course_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"deleted": True}
