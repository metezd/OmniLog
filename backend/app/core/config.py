import os

from dotenv import load_dotenv

# Load variables from a local .env file (ignored by git) if it exists
load_dotenv(override=os.getenv("SECRET_KEY") != "test-secret-key-at-least-32-characters-long")


def _require(name: str) -> str:
    """Return an environment variable or fail fast with a clear message."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# PostgreSQL connection string, e.g.
# postgresql+psycopg2://omnilog:omnilog@localhost:5432/omnilog
DATABASE_URL = _require("DATABASE_URL")

# Secret used to sign JWT tokens. It has no default on purpose: a public
# default value would let anyone forge tokens. Generate one with:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = _require("SECRET_KEY")
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters long")

# Comma separated list of allowed frontend origins for CORS.
# Whitespace is trimmed and empty entries (e.g. a trailing comma) are ignored.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
# The API sends cookies and credentials, so a wildcard origin would let any website call it as
# the logged-in user. Fail at start-up instead of running with an open CORS policy.
if "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must list explicit origins. A wildcard (*) is not allowed.")

# How long a login token stays valid, in minutes
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "90"))

# - External catalog (US-08)
# IGDB (games) uses Twitch OAuth client credentials. Leave both empty to turn game search off.
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID", "").strip()
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET", "").strip()

# TMDB (series and movies). Either the v4 "API Read Access Token" or the v3 API key.
# Leave empty to turn series and movie search off.
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Redis holds the search cache. If Redis is down, an in-process cache is used instead.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# How long a search result stays cached, in seconds (default: 1 hour)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# How long the seasons and episodes of a series stay cached, in seconds (default: 24 hours).
# They change rarely, so this is longer than the search cache (US-09).
DETAILS_CACHE_TTL_SECONDS = int(os.getenv("DETAILS_CACHE_TTL_SECONDS", "86400"))

# Calls to IGDB and TMDB: read timeout, retries for timeouts, 429 and 5xx, and the first
# wait between retries (doubles after each retry). Set the wait to 0 in tests.
EXTERNAL_API_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_API_TIMEOUT_SECONDS", "8"))
EXTERNAL_API_MAX_RETRIES = int(os.getenv("EXTERNAL_API_MAX_RETRIES", "3"))
EXTERNAL_API_BACKOFF_SECONDS = float(os.getenv("EXTERNAL_API_BACKOFF_SECONDS", "0.5"))

# OpenAI integration (AI-powered embeddings and spoiler detection).
# Leave OPENAI_API_KEY empty to disable OpenAI-backed features.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
SPOILER_MODEL = os.getenv("SPOILER_MODEL", "gpt-4o-mini").strip()
SPOILER_THRESHOLD = float(os.getenv("SPOILER_THRESHOLD", "0.5"))
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "8"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
