# Backend image for production (FastAPI + Uvicorn).
# Build context: the backend/ folder.  docker build -t omnilog-backend ./backend
# The CI reads the Python version from the FROM line below and runs the backend tests on it, so
# the version that we ship is the version that we test. Change it only here. The Debian release is
# named, so a new Debian release does not change the image unless this file changes.
FROM python:3.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The application does not run as root. The group and the user have the same fixed id (10001),
# so a file has the same owner on every host. The user has no home folder and no login shell.
RUN groupadd --system --gid 10001 omnilog \
    && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin omnilog

# The dependencies come first, so this layer is reused when only the code changes.
# requirements.txt is the lock file (see requirements.in): the exact versions that CI tested, and
# pip refuses a file whose hash is not in the lock.
COPY requirements.txt .
RUN pip install --require-hashes -r requirements.txt

# The code belongs to root. The application user can read it but cannot change it.
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# The rate limits count the address of the client (#217). Behind a proxy, uvicorn reads it from
# X-Forwarded-For, but only when the call comes from an address in FORWARDED_ALLOW_IPS. Nobody else
# can choose the address that is counted. docker-compose.prod.yml sets the addresses of the proxy
# and the frontend. Without a proxy, only the local host is trusted.
ENV FORWARDED_ALLOW_IPS=127.0.0.1

# Migrations are not run here. The compose file runs `alembic upgrade head` in a separate step.
# --no-server-header: the answers do not name uvicorn (penetration finding F7)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]