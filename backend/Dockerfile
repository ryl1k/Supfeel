# Build context: repository root (the agent reads ../knowledge-base).
#   docker build -f backend/Dockerfile -t supfeel-api .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/backend/.venv

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
COPY knowledge-base /app/knowledge-base

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PORT=8000 \
    LLM_MODE=live

EXPOSE 8000
CMD ["sh", "-c", "python -m app.boot && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
