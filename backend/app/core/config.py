import os

from dotenv import load_dotenv

# Load variables from a local .env file (ignored by git) if it exists. A variable that is
# already set (shell, CI, Render, the test setup) keeps priority over the file.
load_dotenv()


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

# Show the API documentation (/docs, /redoc and /openapi.json). On by default for development.
# Turn it off in production, so the full list of endpoints is not public.
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").strip().lower() in ("1", "true", "yes", "on")

# Allow POST /media, which adds a title to the shared catalog (#218). Off by default, so the
# route answers 404: titles come from the catalog search. The tests turn it on to make fixtures.
ALLOW_MEDIA_CREATE = os.getenv("ALLOW_MEDIA_CREATE", "false").strip().lower() in ("1", "true", "yes", "on")

# How many proxies add an address to X-Forwarded-For in front of the backend (#251). The client
# address is read that many places from the right end of the header, because a client can write
# anything at the left end. 0 (default) uses the address that uvicorn gives, which is right for
# development and for the Docker setup (FORWARDED_ALLOW_IPS). render.yaml sets 2.
FORWARDED_TRUSTED_HOPS = int(os.getenv("FORWARDED_TRUSTED_HOPS", "0"))
if FORWARDED_TRUSTED_HOPS < 0:
    raise RuntimeError("FORWARDED_TRUSTED_HOPS must be 0 or more.")

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
# An empty value turns Redis off, so the in-process cache is used from the start (#251).
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()

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

# - Rate limits (#217)
# Each limit is "<count>/<period>", where the period is second, minute, hour or day. Login and
# register are counted per client address, search and review per user. RATE_LIMIT_ENABLED=false
# turns all of them off (the tests do this, and the rate limit tests turn them on again).
_RATE_LIMIT_PERIODS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}


def _rate_limit(name: str, default: str) -> tuple[int, int]:
    """Read a limit such as "10/minute" and return (count, period in seconds)."""
    text = os.getenv(name, default).strip().lower()
    count, _, period = text.partition("/")
    if not count.isdigit() or int(count) < 1 or period not in _RATE_LIMIT_PERIODS:
        raise RuntimeError(
            f"{name} must look like 10/minute (a count of 1 or more, then second, minute, hour or day)"
        )
    return int(count), _RATE_LIMIT_PERIODS[period]


RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")
RATE_LIMIT_LOGIN = _rate_limit("RATE_LIMIT_LOGIN", "10/minute")
RATE_LIMIT_REGISTER = _rate_limit("RATE_LIMIT_REGISTER", "5/hour")
RATE_LIMIT_SEARCH = _rate_limit("RATE_LIMIT_SEARCH", "30/minute")
RATE_LIMIT_REVIEW = _rate_limit("RATE_LIMIT_REVIEW", "20/minute")

# OpenAI integration (AI-powered embeddings and spoiler detection).
# Leave OPENAI_API_KEY empty to disable OpenAI-backed features.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
SPOILER_MODEL = os.getenv("SPOILER_MODEL", "gpt-4o-mini").strip()
SPOILER_THRESHOLD = float(os.getenv("SPOILER_THRESHOLD", "0.5"))
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "8"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
