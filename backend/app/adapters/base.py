import time
import httpx

from app.config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"  # OpenAI-compatible
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _mock_answer(model: str, prompt: str) -> str:
    return (
        f"[demo mode -- no API key configured for {model}]\n\n"
        f"This is a placeholder response so the full pipeline can be tested "
        f"end to end. Add GEMINI_API_KEY / GROQ_API_KEY (both free) to "
        f"backend/.env to get real model responses.\n\n"
        f"Your (compressed) prompt was: \"{prompt[:200]}\""
    )


async def _openai_compatible(url: str, key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
            json={
                "model": model,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def call_groq(model: str, prompt: str) -> str:
    if not settings.groq_api_key:
        return _mock_answer(model, prompt)
    return await _openai_compatible(GROQ_URL, settings.groq_api_key, model, prompt)


async def call_openai(model: str, prompt: str) -> str:
    if not settings.openai_api_key:
        return _mock_answer(model, prompt)
    return await _openai_compatible(OPENAI_URL, settings.openai_api_key, model, prompt)


async def call_gemini(model: str, prompt: str) -> str:
    if not settings.gemini_api_key:
        return _mock_answer(model, prompt)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GEMINI_URL.format(model=model),
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


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


def _provider_for(model_name: str):
    if model_name.startswith("gemini"):
        return call_gemini
    if model_name.startswith("claude"):
        return call_anthropic
    if model_name.startswith("gpt") or model_name.startswith("o1"):
        return call_openai
    return call_groq  # llama / mixtral / gemma / qwen etc. are served by Groq


async def call_model(model_name: str, prompt: str) -> tuple[str, int]:
    """Returns (answer_text, latency_ms)."""
    start = time.perf_counter()
    answer = await _provider_for(model_name)(model_name, prompt)
    return answer, int((time.perf_counter() - start) * 1000)


async def call_with_failover(
    primary: str, fallbacks: list[str], prompt: str
) -> tuple[str, int, str, bool]:
    """
    Try `primary`; if the provider errors (rate limit, outage, bad key),
    try each fallback in order. Returns (answer, latency_ms, model_used,
    failed_over).
    """
    last_error: Exception | None = None
    for i, name in enumerate([primary, *fallbacks]):
        try:
            answer, latency = await call_model(name, prompt)
            return answer, latency, name, i > 0
        except Exception as exc:  # noqa: BLE001 - any provider failure triggers failover
            last_error = exc
    raise RuntimeError(f"All providers failed: {last_error}")
