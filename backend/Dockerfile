# Backend image for production (FastAPI + Uvicorn).
# Build context: the backend/ folder.  docker build -t omnilog-backend ./backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The dependencies come first, so this layer is reused when only the code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

# The application does not run as root
RUN useradd --system --uid 10001 --no-create-home omnilog
USER 10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# Migrations are not run here. The compose file runs `alembic upgrade head` in a separate step.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
