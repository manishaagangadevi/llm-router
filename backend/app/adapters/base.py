import time
import httpx

from app.config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


async def call_anthropic(model: str, prompt: str) -> str:
    if not settings.anthropic_api_key:
        return _mock_answer(model, prompt)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(block.get("text", "") for block in data.get("content", []))


def _mock_answer(model: str, prompt: str) -> str:
    return (
        f"[demo mode -- no API key configured for {model}]\n\n"
        f"This is a placeholder response so you can test the full pipeline "
        f"end to end. Add ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY "
        f"to backend/.env to get real model responses.\n\n"
        f"Your (compressed) prompt was: \"{prompt[:200]}\""
    )


async def call_model(model_name: str, prompt: str) -> tuple[str, int]:
    """Returns (answer_text, latency_ms). Routes by model name prefix."""
    start = time.perf_counter()

    if model_name.startswith("claude"):
        answer = await call_anthropic(model_name, prompt)
    else:
        answer = _mock_answer(model_name, prompt)

    latency_ms = int((time.perf_counter() - start) * 1000)
    return answer, latency_ms
