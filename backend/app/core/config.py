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

# Secret used to sign JWT tokens (needed from Step 2 on)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

# Comma separated list of allowed frontend origins for CORS
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
