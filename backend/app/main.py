from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.journal import router as journal_router
from app.api.library import router as library_router
from app.api.media import router as media_router
from app.core.config import CORS_ORIGINS
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="OmniLog API",
    description="Video Game & TV Series Tracking API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(media_router)
app.include_router(library_router)
app.include_router(journal_router)


@app.get("/")
def read_root():
    return {"message": "OmniLog Backend is working!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}