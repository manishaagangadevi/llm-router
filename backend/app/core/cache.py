"""
Semantic cache, v1.

Uses normalized string similarity as a stand-in for embedding similarity so
the project runs with zero extra infra out of the box. Swap `_similarity`
for cosine similarity over embeddings (FAISS/Chroma) once that's wired up --
the public `get`/`set` interface stays the same either way.
"""
from difflib import SequenceMatcher

_STORE: list[dict] = []
SIMILARITY_THRESHOLD = 0.92


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def get(query: str) -> dict | None:
    for entry in _STORE:
        if _similarity(entry["query"], query) >= SIMILARITY_THRESHOLD:
            return entry
    return None


def set(query: str, answer: str, model_used: str) -> None:
    _STORE.append({"query": query, "answer": answer, "model_used": model_used})
    if len(_STORE) > 500:
        _STORE.pop(0)
