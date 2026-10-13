import asyncio
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_preview: Mapped[str] = mapped_column(String(200))
    model_used: Mapped[str] = mapped_column(String(50))
    original_tokens: Mapped[int] = mapped_column(Integer)
    compressed_tokens: Mapped[int] = mapped_column(Integer)
    tokens_saved_pct: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[int] = mapped_column(Integer)
    estimated_cost_usd: Mapped[float] = mapped_column(Float)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    routing_reason: Mapped[str] = mapped_column(String(200), default="")
    feedback: Mapped[int | None] = mapped_column(Integer, nullable=True)  # +1 good, -1 bad
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db(retries: int = 30, delay_s: float = 2.0):
    """
    Create tables. Retries because in Docker the backend can start a few
    seconds before Postgres accepts connections.
    """
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception as exc:  # noqa: BLE001
            if attempt == retries:
                raise
            print(f"[db] not ready (attempt {attempt}/{retries}): {type(exc).__name__}; retrying in {delay_s}s")
            await asyncio.sleep(delay_s)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
