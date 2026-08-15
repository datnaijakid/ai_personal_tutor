from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.database import get_database

router = APIRouter(prefix="/courses", tags=["courses"])


class CoursePayload(BaseModel):
    course_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""


@router.get("")
async def list_courses():
    return {"courses": get_database().list_courses()}


@router.post("")
async def save_course(payload: CoursePayload):
    get_database().create_course(payload.course_id, payload.name.strip(), payload.description)
    return {"course_id": payload.course_id, "name": payload.name.strip()}


@router.patch("/{course_id}")
async def rename_course(course_id: str, payload: CoursePayload):
    get_database().create_course(course_id, payload.name.strip(), payload.description)
    return {"course_id": course_id, "name": payload.name.strip()}
