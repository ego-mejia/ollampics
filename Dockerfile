# Multi-stage build: frontend assets, then Python backend that serves them.
#
# IMPORTANT: This container does NOT include Ollama. Ollama must run on the
# host (or another container). The default OLLAMA_HOST below points to
# `host.docker.internal` which works on Mac/Windows Docker Desktop. On Linux,
# use `--add-host=host.docker.internal:host-gateway` or set OLLAMA_HOST to
# your host's LAN IP.
#
# powermetrics-based watt measurement does NOT work inside a container.
# That feature is opt-in anyway — leave POWERMETRICS_ENABLED=0 in the container.

# --- Stage 1: build the frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend ---
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

COPY src/ ./src/
COPY tasks/ ./tasks/
RUN uv sync --frozen

COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV OLLYMPICS_OLLAMA_HOST=http://host.docker.internal:11434 \
    OLLYMPICS_DB_URL=sqlite:////data/ollympics.db \
    OLLYMPICS_ENABLE_WATTS=false

VOLUME ["/data"]
EXPOSE 8000

CMD ["sh", "-c", "uv run oly db init && uv run oly serve --host 0.0.0.0 --port 8000"]
