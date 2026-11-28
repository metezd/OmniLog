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

def _whole_number(name: str, default: int, minimum: int) -> int:
    """A whole number setting of at least `minimum`. A wrong value stops the start with its name."""
    text = os.getenv(name, str(default)).strip()
    try:
        value = int(text)
    except ValueError:
        raise RuntimeError(f"{name} must be a whole number, got {text!r}") from None
    if value < minimum:
        raise RuntimeError(f"{name} must be {minimum} or more, got {value}")
    return value


# The connection pool of the API (#432). The endpoints run in a thread pool of 40 threads, so more
# requests than connections can wait here. A request that finds no free connection within
# DB_POOL_TIMEOUT seconds gets 503. DB_STATEMENT_TIMEOUT_MS stops one SQL statement of the API that
# runs longer (0 turns it off); the migrations have no such limit.
DB_POOL_SIZE = _whole_number("DB_POOL_SIZE", 5, 1)
DB_MAX_OVERFLOW = _whole_number("DB_MAX_OVERFLOW", 10, 0)
DB_POOL_TIMEOUT = _whole_number("DB_POOL_TIMEOUT", 10, 1)
DB_STATEMENT_TIMEOUT_MS = _whole_number("DB_STATEMENT_TIMEOUT_MS", 15000, 0)

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
# Only these websites may call the API from a browser. A wildcard would let any website read the
# answers. Fail at start-up instead of running with an open CORS policy.
if "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must list explicit origins. A wildcard (*) is not allowed.")

# Show the API documentation (/docs, /redoc and /openapi.json). Off by default (#394), so a start
# without this setting does not make the full list of endpoints public. Set ENABLE_DOCS=true in
# backend/.env for development.
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").strip().lower() in ("1", "true", "yes", "on")

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

# A key that the frontend and the backend share (#301). The frontend sends it with the browser
# address in X-Client-IP, so the login and register limits count the browser and not the
# frontend. Without the right key the backend ignores X-Client-IP. Empty turns this off.
FRONTEND_PROXY_SECRET = os.getenv("FRONTEND_PROXY_SECRET", "").strip()
if FRONTEND_PROXY_SECRET and len(FRONTEND_PROXY_SECRET) < 32:
    raise RuntimeError("FRONTEND_PROXY_SECRET must be at least 32 characters long, or empty.")

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

# Redis can be a managed service such as Upstash. Use its connection string, for example
# rediss://default:<token>@<name>.upstash.io:6379 (the double s turns TLS on). A managed Redis is
# farther away than a local one, so the timeout of one Redis call can be raised here (seconds).
REDIS_SOCKET_TIMEOUT_SECONDS = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "0.5"))
if REDIS_SOCKET_TIMEOUT_SECONDS <= 0:
    raise RuntimeError("REDIS_SOCKET_TIMEOUT_SECONDS must be more than 0.")

# How long a search result stays cached, in seconds (default: 1 hour)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Negative cache: how long an empty answer from IGDB or TMDB (no search results, or an id that
# the service does not know) stays cached, in seconds (default: 5 minutes). It is short on
# purpose, because a title can appear at the source soon after. 0 turns the negative cache off.
NEGATIVE_CACHE_TTL_SECONDS = int(os.getenv("NEGATIVE_CACHE_TTL_SECONDS", "300"))
if NEGATIVE_CACHE_TTL_SECONDS < 0:
    raise RuntimeError("NEGATIVE_CACHE_TTL_SECONDS must be 0 or more.")

# Database cache (L2): a title whose details were loaded less than this many days ago is served
# from PostgreSQL (media_items.last_synced) without a call to IGDB or TMDB, even when Redis (L1)
# has lost the entry. Default: 7 days. 0 turns it off, so every cache miss calls the outside API.
DB_CACHE_TTL_DAYS = float(os.getenv("DB_CACHE_TTL_DAYS", "7"))
if DB_CACHE_TTL_DAYS < 0:
    raise RuntimeError("DB_CACHE_TTL_DAYS must be 0 or more.")

# How long the seasons and episodes of a series stay cached, in seconds (default: 24 hours).
# They change rarely, so this is longer than the search cache (US-09).
DETAILS_CACHE_TTL_SECONDS = int(os.getenv("DETAILS_CACHE_TTL_SECONDS", "86400"))

# Calls to IGDB and TMDB: read timeout, retries for timeouts, 429 and 5xx, and the first
# wait between retries (doubles after each retry). Set the wait to 0 in tests.
EXTERNAL_API_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_API_TIMEOUT_SECONDS", "8"))
EXTERNAL_API_MAX_RETRIES = int(os.getenv("EXTERNAL_API_MAX_RETRIES", "3"))
EXTERNAL_API_BACKOFF_SECONDS = float(os.getenv("EXTERNAL_API_BACKOFF_SECONDS", "0.5"))
# When all tries of a call to IGDB, TMDB or a keyless source got no answer (timeouts, no
# connection), that host is not called again for this many seconds, and the saved data is used
# (#428). 0 turns the pause off.
EXTERNAL_API_COOLDOWN_SECONDS = max(float(os.getenv("EXTERNAL_API_COOLDOWN_SECONDS", "60")), 0.0)

# Outgoing limit for IGDB: the most requests per second that this backend process sends to it.
# IGDB allows 4 per second for one Twitch application and answers 429 above that. A call that
# would have to wait more than a few seconds fails at once, so the caller uses the saved copy. 0
# turns the limit off. The limit counts per process, so give each process its share when the
# backend runs more than one.
IGDB_MAX_REQUESTS_PER_SECOND = float(os.getenv("IGDB_MAX_REQUESTS_PER_SECOND", "3"))
if IGDB_MAX_REQUESTS_PER_SECOND < 0:
    raise RuntimeError("IGDB_MAX_REQUESTS_PER_SECOND must be 0 or more.")

# - Rate limits (#217)
# Each limit is "<count>/<period>", where the period is second, minute, hour or day. Login and
# register are counted per client address, search, review, details and recommendations per user. RATE_LIMIT_ENABLED=false
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
# Failed logins of one account, from any address (#391). See docs/deployment.md, section 9.1.
RATE_LIMIT_LOGIN_ACCOUNT = _rate_limit("RATE_LIMIT_LOGIN_ACCOUNT", "20/hour")
RATE_LIMIT_REGISTER = _rate_limit("RATE_LIMIT_REGISTER", "5/hour")
# A second register limit per address for a whole day, so a slow search for registered emails
# gets 20 answers a day and not 120 (#395). See docs/deployment.md, section 9.2.
RATE_LIMIT_REGISTER_DAY = _rate_limit("RATE_LIMIT_REGISTER_DAY", "20/day")
RATE_LIMIT_SEARCH = _rate_limit("RATE_LIMIT_SEARCH", "30/minute")
RATE_LIMIT_REVIEW = _rate_limit("RATE_LIMIT_REVIEW", "20/minute")
# Opening a title that was not loaded yet calls IGDB or TMDB, and OpenAI for its embedding (#390)
RATE_LIMIT_DETAILS = _rate_limit("RATE_LIMIT_DETAILS", "60/minute")
# Each recommendation call averages the liked embeddings and runs a vector search (#396)
RATE_LIMIT_RECOMMENDATIONS = _rate_limit("RATE_LIMIT_RECOMMENDATIONS", "30/minute")
# All writes of one user that have no limit of their own: the library, the chapters and the lists
# (#431). Most of them also add a diary row, so without a limit one account could fill the database.
RATE_LIMIT_WRITES = _rate_limit("RATE_LIMIT_WRITES", "120/minute")

# OpenAI integration (AI-powered embeddings and spoiler detection).
# Leave OPENAI_API_KEY empty to disable OpenAI-backed features.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
SPOILER_MODEL = os.getenv("SPOILER_MODEL", "gpt-4o-mini").strip()
SPOILER_THRESHOLD = float(os.getenv("SPOILER_THRESHOLD", "0.5"))
# Who checks a review for spoilers (#397). "openai" sends the review text to OpenAI when
# OPENAI_API_KEY is set. "local" keeps every review inside the system and uses the local patterns,
# also when the key is set for the embeddings of titles.
SPOILER_PROVIDER = os.getenv("SPOILER_PROVIDER", "openai").strip().lower() or "openai"
if SPOILER_PROVIDER not in ("local", "openai"):
    raise RuntimeError("SPOILER_PROVIDER must be local or openai.")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "8"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
# After a failed OpenAI call, the next calls fail at once for this many seconds instead of waiting
# for OpenAI again (#382). 0 turns the pause off.
OPENAI_COOLDOWN_SECONDS = max(float(os.getenv("OPENAI_COOLDOWN_SECONDS", "60")), 0.0)
# Threads for the work that runs after the answer: embeddings and the OpenAI spoiler check (#382)
BACKGROUND_WORKERS = max(int(os.getenv("BACKGROUND_WORKERS", "2")), 1)
