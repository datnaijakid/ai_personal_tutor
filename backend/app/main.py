from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.upload import router as upload_router

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Backend is running!"
    }


app.include_router(health_router)
app.include_router(upload_router)