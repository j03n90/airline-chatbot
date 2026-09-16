from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.assistant import router as assistant_router
from backend.api.mock import router as mock_router
from backend.config import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        from backend.rag.retrieve import ensure_indexes

        ensure_indexes()
    except Exception as exc:
        print(f"FAISS index not ready at startup: {exc}")
    yield


app = FastAPI(title="Airline Service Assistant", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mock_router)
app.include_router(assistant_router)

dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


@app.get("/api/meta")
def meta():
    return {
        "name": "airline-service-assistant",
        "llm": settings.deepseek_model,
        "embedding": settings.embedding_model,
        "package_manager": "uv",
    }
