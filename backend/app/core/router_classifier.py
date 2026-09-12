"""
Predictive routing classifier.

v1 is rule-based (keyword + heuristic scoring) so the pipeline works without
any training data. It's written so `predict()` is the only function the rest
of the app depends on -- swap the internals for a trained sklearn/DistilBERT
classifier later without touching the API layer.
"""
import re

CODE_HINTS = re.compile(r"\b(code|function|bug|error|python|javascript|api|debug|script|algorithm|sql)\b", re.I)
CREATIVE_HINTS = re.compile(r"\b(story|poem|write a|creative|imagine|brainstorm|slogan|essay)\b", re.I)
REASONING_HINTS = re.compile(r"\b(why|explain|analyze|compare|reason|prove|logic|trade-?off)\b", re.I)

MODELS = {
    "fast_cheap": {"name": "claude-haiku-4-5", "cost_per_1k": 0.001, "avg_latency_ms": 400},
    "balanced": {"name": "claude-sonnet-5", "cost_per_1k": 0.003, "avg_latency_ms": 900},
    "premium": {"name": "claude-opus-5", "cost_per_1k": 0.015, "avg_latency_ms": 1600},
}


def predict(query: str, priority: str = "balanced") -> tuple[str, str, dict]:
    """Returns (model_key, reason, model_info)."""
    length = len(query.split())

    if priority == "cost":
        key, reason = "fast_cheap", "user prioritized cost"
    elif priority == "quality":
        key, reason = "premium", "user prioritized quality"
    elif REASONING_HINTS.search(query) or length > 60:
        key, reason = "premium", "complex reasoning or long query detected"
    elif CODE_HINTS.search(query):
        key, reason = "balanced", "code-related query detected"
    elif CREATIVE_HINTS.search(query):
        key, reason = "balanced", "creative writing query detected"
    elif length < 12:
        key, reason = "fast_cheap", "short, routine query"
    else:
        key, reason = "balanced", "default balanced routing"

    return key, reason, MODELS[key]
