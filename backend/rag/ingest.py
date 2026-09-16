from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.rag.corpus import CORPUS

CODES = ("STA", "NSA", "BHA")


def embedder() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def build_indexes(index_dir: Path | None = None, model: SentenceTransformer | None = None) -> Path:
    index_dir = Path(index_dir or settings.index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    model = model or embedder()
    for code in CODES:
        chunks = CORPUS[code]
        texts = [c["text"] for c in chunks]
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        vectors = np.asarray(vectors, dtype="float32")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(index_dir / f"{code}.faiss"))
        (index_dir / f"{code}.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    (index_dir / "meta.json").write_text(
        json.dumps({"embedding_model": settings.embedding_model, "airlines": list(CODES)}),
        encoding="utf-8",
    )
    return index_dir


def main() -> None:
    path = build_indexes()
    print(f"Wrote FAISS indexes to {path}")


if __name__ == "__main__":
    main()
