# syntax=docker/dockerfile:1
#
# Backend image: FastAPI under uvicorn. Alembic, the migrations and the seed
# script ship in the same image, so schema changes and seeding run from the
# exact code that serves requests rather than from whatever is checked out
# on the host:
#
#   docker compose --profile app run --rm backend alembic upgrade head
#   docker compose --profile app run --rm backend python scripts/seed.py

FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# A venv rather than a bare site-packages, so the runtime stage copies one
# directory and inherits nothing else from the build.
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system quiz && useradd --system --gid quiz --no-create-home quiz

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY seeds ./seeds

USER quiz

EXPOSE 8000

# The slim image has no curl; the interpreter is already here.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
