# syntax=docker/dockerfile:1

FROM node:20-bookworm-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/app/.cache/huggingface
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
COPY airline ./airline
COPY --from=frontend /src/frontend/dist ./frontend/dist
ARG DEEPSEEK_API_KEY
RUN test -n "$DEEPSEEK_API_KEY" || (echo "DEEPSEEK_API_KEY build-arg is required" && exit 1)
ENV DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
    DEEPSEEK_BASE_URL=https://api.deepseek.com \
    DEEPSEEK_MODEL=deepseek-chat
RUN uv run python -m backend.rag.ingest
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
