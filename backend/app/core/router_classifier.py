"""
Predictive routing classifier.

Uses a trained TF-IDF + logistic regression model (from train_classifier.py)
when one exists, otherwise a rule-based router (keywords + length), so the
pipeline works from day one with zero training data. `predict()` is the only
function the rest of the app depends on.
"""
import re
from pathlib import Path

import joblib

from app.config import settings

_MODEL_PATH = Path(__file__).parent / "trained_router.joblib"
_trained = None
if _MODEL_PATH.exists():
    try:
        _trained = joblib.load(_MODEL_PATH)
    except Exception:  # corrupt/incompatible file -> fall back to rules
        _trained = None

CODE_HINTS = re.compile(r"\b(code|function|bug|error|python|javascript|api|debug|script|algorithm|sql)\b", re.I)
CREATIVE_HINTS = re.compile(r"\b(story|poem|write a|creative|imagine|brainstorm|slogan|essay)\b", re.I)
REASONING_HINTS = re.compile(r"\b(why|explain|analyze|compare|reason|prove|logic|trade-?off)\b", re.I)

# Model names come from settings (.env). cost_per_1k is a *notional* list-price
# estimate used for the dashboard's savings math -- the free tiers bill $0.
MODELS = {
    "fast_cheap": {"name": settings.fast_model, "cost_per_1k": 0.0001, "avg_latency_ms": 350},
    "balanced": {"name": settings.balanced_model, "cost_per_1k": 0.0005, "avg_latency_ms": 800},
    "premium": {"name": settings.premium_model, "cost_per_1k": 0.002, "avg_latency_ms": 1200},
}


def fallbacks_for(model_key: str) -> list[str]:
    """Other tiers' models, tried in order if the chosen model's provider fails."""
    return [info["name"] for key, info in MODELS.items() if key != model_key]


def predict(query: str, priority: str = "balanced") -> tuple[str, str, dict]:
    """Returns (model_key, reason, model_info)."""
    length = len(query.split())

    # an explicit cost/quality choice from the user always beats the learned router
    if priority == "balanced" and _trained is not None:
        name_to_key = {info["name"]: key for key, info in MODELS.items()}
        predicted = _trained.predict([query])[0]
        if predicted in name_to_key:  # skip if that model is no longer a configured tier
            key = name_to_key[predicted]
            return key, "predicted by trained classifier", MODELS[key]

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
