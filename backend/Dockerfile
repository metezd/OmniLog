# Backend image for production (FastAPI + Uvicorn).
# Build context: the backend/ folder.  docker build -t omnilog-backend ./backend
# The Python version is the one of the CI (3.11). The Debian release is named, so a new Debian
# release does not change the image unless this file changes.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The application does not run as root. The group and the user have the same fixed id (10001),
# so a file has the same owner on every host. The user has no home folder and no login shell.
RUN groupadd --system --gid 10001 omnilog \
    && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin omnilog

# The dependencies come first, so this layer is reused when only the code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

# The code belongs to root. The application user can read it but cannot change it.
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# Migrations are not run here. The compose file runs `alembic upgrade head` in a separate step.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]