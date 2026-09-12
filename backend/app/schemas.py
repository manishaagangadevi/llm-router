from pydantic import BaseModel, ConfigDict
from typing import Optional


class QueryRequest(BaseModel):
    query: str
    priority: Optional[str] = "balanced"  # "cost" | "quality" | "speed" | "balanced"


class QueryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    answer: str
    model_used: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved_pct: float
    cache_hit: bool
    latency_ms: int
    estimated_cost_usd: float
    routing_reason: str


class LogEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    query_preview: str
    model_used: str
    tokens_saved_pct: float
    latency_ms: int
    estimated_cost_usd: float
    cache_hit: bool
    created_at: str
