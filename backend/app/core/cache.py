"""
Semantic cache, v2.

Uses a HashingVectorizer (fixed-size bag-of-words hashing -- no training and
no model download) plus cosine similarity, so near-duplicate queries like
"capital of france?" and "what is the capital of France" hit the same entry
where exact-string matching would miss.

Known limit: bag-of-words cannot tell "capital of France" from "capital of
Germany" (cosine ~0.82), so the threshold is kept strict (near-identical
queries only) -- a wrong cached answer is worse than a cache miss. Real
embeddings are what unlock true semantic matching.

To upgrade to true semantic embeddings later: swap `_vectorize` for an
embeddings call (e.g. Gemini's free text-embedding endpoint or a local
sentence-transformers model), and swap the linear scan in `get` for
FAISS/Chroma once the cache grows large.
"""
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_VECTORIZER = HashingVectorizer(
    n_features=2**12, alternate_sign=False, norm="l2", ngram_range=(1, 2)
)
_STORE: list[dict] = []
SIMILARITY_THRESHOLD = 0.92  # deliberately strict, see note above
MAX_ENTRIES = 500


def _vectorize(text: str):
    return _VECTORIZER.transform([text.lower().strip()])


def get(query: str) -> dict | None:
    if not _STORE:
        return None

    query_vec = _vectorize(query)
    best_score, best_entry = 0.0, None
    for entry in _STORE:
        score = float(cosine_similarity(query_vec, entry["vector"])[0][0])
        if score > best_score:
            best_score, best_entry = score, entry

    return best_entry if best_score >= SIMILARITY_THRESHOLD else None


def set(query: str, answer: str, model_used: str) -> None:
    _STORE.append(
        {"query": query, "vector": _vectorize(query), "answer": answer, "model_used": model_used}
    )
    if len(_STORE) > MAX_ENTRIES:
        _STORE.pop(0)
