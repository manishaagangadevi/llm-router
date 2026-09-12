from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas import QueryRequest, QueryResponse, LogEntry
from app.db import init_db, get_session, RequestLog
from app.core import compressor, cache
from app.core.router_classifier import predict
from app.adapters.base import call_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="LLM Router API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest, session: AsyncSession = Depends(get_session)):
    compressed_text, original_tokens, compressed_tokens = compressor.compress(req.query)
    tokens_saved_pct = round(
        100 * (original_tokens - compressed_tokens) / max(original_tokens, 1), 1
    )

    cached = cache.get(compressed_text)
    if cached:
        log = RequestLog(
            query_preview=req.query[:200],
            model_used=cached["model_used"],
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            tokens_saved_pct=tokens_saved_pct,
            latency_ms=5,
            estimated_cost_usd=0.0,
            cache_hit=True,
            routing_reason="semantic cache hit",
        )
        session.add(log)
        await session.commit()
        return QueryResponse(
            answer=cached["answer"],
            model_used=cached["model_used"],
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            tokens_saved_pct=tokens_saved_pct,
            cache_hit=True,
            latency_ms=5,
            estimated_cost_usd=0.0,
            routing_reason="semantic cache hit",
        )

    model_key, reason, model_info = predict(compressed_text, req.priority)
    answer, latency_ms = await call_model(model_info["name"], compressed_text)
    estimated_cost = round((compressed_tokens / 1000) * model_info["cost_per_1k"], 6)

    cache.set(compressed_text, answer, model_info["name"])

    log = RequestLog(
        query_preview=req.query[:200],
        model_used=model_info["name"],
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        tokens_saved_pct=tokens_saved_pct,
        latency_ms=latency_ms,
        estimated_cost_usd=estimated_cost,
        cache_hit=False,
        routing_reason=reason,
    )
    session.add(log)
    await session.commit()

    return QueryResponse(
        answer=answer,
        model_used=model_info["name"],
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        tokens_saved_pct=tokens_saved_pct,
        cache_hit=False,
        latency_ms=latency_ms,
        estimated_cost_usd=estimated_cost,
        routing_reason=reason,
    )


@app.get("/api/logs", response_model=list[LogEntry])
async def get_logs(limit: int = 50, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RequestLog).order_by(RequestLog.id.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [
        LogEntry(
            id=r.id,
            query_preview=r.query_preview,
            model_used=r.model_used,
            tokens_saved_pct=r.tokens_saved_pct,
            latency_ms=r.latency_ms,
            estimated_cost_usd=r.estimated_cost_usd,
            cache_hit=r.cache_hit,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@app.get("/api/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    total = await session.scalar(select(func.count(RequestLog.id))) or 0
    cache_hits = await session.scalar(
        select(func.count(RequestLog.id)).where(RequestLog.cache_hit == True)  # noqa: E712
    ) or 0
    total_cost = await session.scalar(select(func.sum(RequestLog.estimated_cost_usd))) or 0.0
    avg_tokens_saved = await session.scalar(select(func.avg(RequestLog.tokens_saved_pct))) or 0.0

    model_counts_result = await session.execute(
        select(RequestLog.model_used, func.count(RequestLog.id)).group_by(RequestLog.model_used)
    )
    model_distribution = {row[0]: row[1] for row in model_counts_result.all()}

    baseline_cost = total * 0.015  # if every request had hit the premium model
    cost_saved = max(round(baseline_cost - total_cost, 4), 0.0)

    return {
        "total_requests": total,
        "cache_hit_rate_pct": round(100 * cache_hits / max(total, 1), 1),
        "total_cost_usd": round(total_cost, 4),
        "estimated_cost_saved_usd": cost_saved,
        "avg_tokens_saved_pct": round(avg_tokens_saved, 1),
        "model_distribution": model_distribution,
        "generated_at": datetime.utcnow().isoformat(),
    }
