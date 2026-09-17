# Airline Service Assistant

Conversational assistant for three fictional airlines (Suntrail Air, Northstar Air, Bluehaven Airways). One Docker image, two HTTP surfaces:

- `/api/assistant/*`  customer assistant (DeepSeek + LangGraph + FAISS)
- `/api/mock/*`  mock booking bench used to seed and inspect test data

Python dependencies are managed **only with [uv](https://docs.astral.sh/uv/)**. Do not use `pip install`.

---

## DeepSeek API key / Docker

This project talks to DeepSeek (`deepseek-chat`). **The git repository does not contain an API key.**

1. Copy `.env.example` to `.env`.
2. Put your key in `.env`:

```
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

`.env` is gitignored. `.dockerignore` also excludes it, so the key is never copied in as a source file.

### Interviewer: how to run the image

Build injects the key via `--build-arg` (required; an empty arg fails the build). After that, `docker run` does not need `-e`:

```bash
set -a && source .env && set +a
docker build --build-arg DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" -t airline-assistant .
docker run -p 8080:8080 airline-assistant
```

Open http://127.0.0.1:8080

If you prefer not to bake the key into the image:

```bash
docker run -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" -p 8080:8080 airline-assistant
```

Embeddings / FAISS indexes are built **during `docker build`** with the local open-source model `sentence-transformers/all-MiniLM-L6-v2`. Runtime retrieval does not call DeepSeek for embeddings.

---

## Local run (no Docker)

```bash
uv sync --group dev
uv run python -m backend.rag.ingest
uv run uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

Frontend (optional hot reload):

```bash
cd frontend && npm install && npm run dev
```

Vite proxies `/api` to port 8080. For the single-process demo, build the UI and let FastAPI serve `frontend/dist`:

```bash
cd frontend && npm install && npm run build
uv run uvicorn backend.app:app --port 8080
```

---

## Tests

Layered gates; run them in this order. Default suite does **not** need to be marked `eval`  assistant tests assert quotes/reason codes and use DeepSeek only when composing prose.

```bash
uv run pytest tests/policy tests/mock tests/agent tests/rag   # no chat model required for policy/mock/rag
uv run pytest                                                # full suite including assistant API
```

---

## What to click in the UI

The main view is the chat. Open **Mock Lab** with the info button or the right-edge **Lab** handle. Presets come from `GET /api/mock/presets` (same ids as `tests/`). Load a case, then send from chat; keep Lab open to watch bookings update.

Recommended path:

1. **STA Standard mixed-route change = USD 85** - Send the prefilled message - expect a quote of **USD 85**, booking still `scheduled` - type `Yes, confirm.` - booking becomes `changed`.
2. **BHA Basic cannot change** - expect `not_permitted`, itinerary unchanged.
3. **Unknown airline must not merge rules** - expect a per-airline answer, not one fake global fee.
4. **PNR + surname is not enough** - expect identity rejection.
5. **Partly flown refund -> desk** - expect handoff.
6. **Custom / blank** - paste your own seed JSON to debug.

---

## API sketch

Mock: `POST /api/mock/sessions/{id}/load`, `load-preset`, `lookup`, `quote-change`, `quote-cancel`, `confirm`, clock, bookings.

Assistant: `GET /api/assistant/health`, `POST /api/assistant/sessions`, `POST /api/assistant/chat` (JSON if `Accept: application/json`, otherwise SSE), `GET .../trace`. Sessions are LangGraph threads (`thread_id` = `session_id`) checkpointed to sqlite (`data/checkpoints.sqlite` by default; tests use in-memory).
