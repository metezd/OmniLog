import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
from app.core.errors import register_exception_handlers
from app.api.library import router as library_router
from app.api.media import router as media_router
from app.core import cache
from app.core.body_limit import BodySizeLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.config import CORS_ORIGINS, ENABLE_DOCS
from app.core import database
from app.core.database import get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Stop at once with a clear message when the local PostgreSQL is not running (#371)
    database.check_database(database.engine)
    # Say once at the start why the cache is not Redis (#422). The API works without it (NFR-04),
    # so this is only a warning, but the search cache and the rate limits stay in this process.
    redis_state = cache.status()
    if redis_state == "not_configured":
        logger.warning("REDIS_URL is empty. The cache and the rate limits use the memory of this process.")
    elif redis_state == "down":
        logger.warning(
            "Redis at %s does not answer. The cache and the rate limits use the memory of this process.",
            cache.redis_target(),
        )
    yield


app = FastAPI(
    lifespan=lifespan,
    title="OmniLog API",
    description="Video Game & TV Series Tracking API",
    version="0.8.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)

# The body size limit runs inside the security headers, so its 413 and 400 answers get them too
# (#302). The security headers are on every answer, also on an unhandled error (#220, #304).
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Catalog search and title details can be large JSON answers (a series with all its seasons and
# episodes). Answers of at least 1000 bytes are compressed when the client accepts gzip (#250).
# Small answers stay plain, because the compression would cost more than it saves.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# The token is sent in the Authorization header and the API sets no cookie, so a browser needs no
# credentials mode. Only the methods of the API and the headers that a client sends are allowed
# (#394). A preflight that asks for anything else gets no Access-Control-Allow-* answer.
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
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
        "cache": cache.status(),
    }
    return JSONResponse(body, status_code=200 if ready else 503)
