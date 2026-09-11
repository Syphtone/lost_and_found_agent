"""Embedding interface for RAG.

This module is the ONLY place that knows which embedding model is used and how
it is loaded. The rest of the app (services, MCP tools, the agent) depends only
on the functions exposed here — `embed_text`, `embed_texts`, and
`embedding_dim` — so the embedding model can be swapped without touching
retrieval, storage, or agent logic.

Backend: a local sentence-transformers model (default
`all-MiniLM-L6-v2`, 384-dim), loaded lazily and cached for the process. No
network call is required when the model is already in the local HF cache.
"""

from __future__ import annotations

import os

# Force local-cache-only loading. The embedding model is already present in the
# local Hugging Face cache; this prevents any network probe to the HF Hub at
# load time (which is both slow and blocked in this environment) and enforces
# our "no download" rule. Set before importing sentence_transformers.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the sentence-transformers model once per process (lazy)."""
    return SentenceTransformer(settings.embedding_model)


def embedding_dim() -> int:
    """Return the embedding vector dimension (must match the pgvector column).

    Configured value is authoritative; we do not force a model load just to
    read the dimension.
    """
    return settings.embedding_dim


def embed_text(text: str) -> list[float]:
    """Embed a single string into a plain list[float] (pgvector-friendly)."""
    vector = _get_model().encode(
        text,
        normalize_embeddings=True,  # cosine-ready unit vectors
        convert_to_numpy=True,
    )
    return vector.astype("float32").tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings. Returns one list[float] per input."""
    if not texts:
        return []
    vectors = _get_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [v.astype("float32").tolist() for v in vectors]
