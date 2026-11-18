from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.chapters import router as chapters_router
from app.api.journal import router as journal_router
from app.api.recommendations import router as recommendations_router
from app.api.stats import router as stats_router
from app.api import lists
from app.core.errors import register_exception_handlers
from app.api.library import router as library_router
from app.api.media import router as media_router
from app.core import cache
from app.core.config import CORS_ORIGINS
from app.core.database import get_db

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
app.include_router(catalog_router)
app.include_router(library_router)
app.include_router(chapters_router)
app.include_router(journal_router)
app.include_router(recommendations_router)
app.include_router(stats_router)
app.include_router(lists.router)


@app.get("/")
def read_root():
    return {"message": "OmniLog Backend is working!"}


@app.get("/health")
def health_check():
    """Liveness: the process answers. Use this for the health check of the host (Docker, Render)."""
    return {"status": "healthy"}


@app.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness: the parts that the API needs. Use this for an uptime monitor, not for restarts.

    The database is required. Redis is optional, because the API works without it (NFR-04), so
    Redis down only shows as "down" and the answer stays 200. No error details are returned.
    """
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "down"
    ready = database == "ok"
    body = {
        "status": "ready" if ready else "unavailable",
        "database": database,
        "cache": "ok" if cache.is_available() else "down",
    }
    return JSONResponse(body, status_code=200 if ready else 503)
