import os

from dotenv import load_dotenv

# Load variables from a local .env file (ignored by git) if it exists
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
