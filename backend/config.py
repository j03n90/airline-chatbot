import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


class Settings:
    api_key: str = os.getenv("API_KEY", "")
    base_url: str = os.getenv("BASE_URL", "https://api.deepseek.com")
    model: str = os.getenv("MODEL", "deepseek-chat")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    index_dir: Path = ROOT / "backend" / "rag" / "indexes"
    policy_dir: Path = ROOT / "airline" / "airline-policies"
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8080"))
    checkpoint_backend: str = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    checkpoint_sqlite_path: Path = Path(
        os.getenv("CHECKPOINT_SQLITE_PATH") or str(ROOT / "data" / "checkpoints.sqlite")
    )


settings = Settings()
