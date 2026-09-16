import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    index_dir: Path = ROOT / "backend" / "rag" / "indexes"
    policy_dir: Path = ROOT / "airline" / "airline-policies"
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8080"))


settings = Settings()
