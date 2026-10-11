"""
Trains the routing classifier from rated requests.

Usage (from the backend folder):
    python train_classifier.py

Learns only from requests that received a thumbs-UP: the query is the input
and the model that handled it well is the label. Thumbs-down requests are
excluded -- training on them under the same label would teach the router to
send similar queries to the model that just failed.

Needs >= MIN_PER_CLASS rated examples for at least two models. Until then
the app keeps using the rule-based router, so running this early is safe.
"""
import asyncio
import sys
from collections import Counter
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select  # noqa: E402
from app.db import async_session, RequestLog  # noqa: E402

MODEL_PATH = Path(__file__).parent / "app" / "core" / "trained_router.joblib"
MIN_PER_CLASS = 15


async def load_examples():
    async with async_session() as session:
        result = await session.execute(select(RequestLog).where(RequestLog.feedback == 1))
        rows = result.scalars().all()
    return [r.query_preview for r in rows], [r.model_used for r in rows]


def main():
    texts, labels = asyncio.run(load_examples())
    counts = Counter(labels)
    print(f"Thumbs-up examples: {len(texts)} -> {dict(counts)}")

    ready = [m for m, n in counts.items() if n >= MIN_PER_CLASS]
    if len(ready) < 2:
        print(
            f"Not enough data yet: need >= {MIN_PER_CLASS} thumbs-up examples for at "
            f"least 2 different models. Keep using the app and rating answers; "
            f"routing stays rule-based until then."
        )
        return

    keep = [i for i, label in enumerate(labels) if label in ready]
    texts = [texts[i] for i in keep]
    labels = [labels[i] for i in keep]

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=2000)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(texts, labels)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Trained on {len(texts)} examples across {ready}. Saved to {MODEL_PATH}")
    print("Restart the backend to load it.")


if __name__ == "__main__":
    main()
