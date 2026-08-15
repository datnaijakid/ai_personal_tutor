from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.courses import router as courses_router


app = FastAPI()


# Allow the Next.js frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Backend is running!"
    }


app.include_router(health_router)
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(courses_router)
