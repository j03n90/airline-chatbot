from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.rag.ingest import CODES, build_indexes

_indexes: dict[str, faiss.Index] = {}
_docs: dict[str, list[dict]] = {}
_model: SentenceTransformer | None = None


def indexes_ready(index_dir: Path | None = None) -> bool:
    index_dir = Path(index_dir or settings.index_dir)
    return all((index_dir / f"{code}.faiss").exists() and (index_dir / f"{code}.json").exists() for code in CODES)


def ensure_indexes() -> None:
    if not indexes_ready():
        build_indexes()
    load_indexes()


def load_indexes(index_dir: Path | None = None) -> None:
    global _model
    index_dir = Path(index_dir or settings.index_dir)
    for code in CODES:
        _indexes[code] = faiss.read_index(str(index_dir / f"{code}.faiss"))
        _docs[code] = json.loads((index_dir / f"{code}.json").read_text(encoding="utf-8"))
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)


def _encode(query: str) -> np.ndarray:
    if _model is None:
        ensure_indexes()
    vec = _model.encode([query], normalize_embeddings=True, convert_to_numpy=True)
    return np.asarray(vec, dtype="float32")


def retrieve(
    query: str,
    airline: Optional[str] = None,
    k: int = 4,
    extra_context: Optional[str] = None,
) -> list[dict]:
    if not _indexes:
        ensure_indexes()
    q = query
    if extra_context:
        q = f"{query}\nContext: {extra_context}"
    vec = _encode(q)
    codes = [airline] if airline in _indexes else list(CODES)
    hits: list[dict] = []
    for code in codes:
        scores, idxs = _indexes[code].search(vec, min(k, _indexes[code].ntotal))
        for score, i in zip(scores[0], idxs[0]):
            if i < 0:
                continue
            doc = dict(_docs[code][i])
            doc["score"] = float(score)
            hits.append(doc)
    hits.sort(key=lambda h: h["score"], reverse=True)
    if airline:
        return hits[:k]
    grouped = []
    seen = set()
    for h in hits:
        key = h["airline_code"]
        count = sum(1 for g in grouped if g["airline_code"] == key)
        if count < k:
            grouped.append(h)
            seen.add(key)
    return grouped
