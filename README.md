# router

A predictive multi-LLM router. It compresses incoming prompts, predicts which
model should handle each one, calls it, and logs cost/latency/token savings
without exposing any of that machinery to the end user by default.

## Why

Calling a single premium model for every request is expensive and often
unnecessary a large share of real-world queries are routine and are handled
identically by a cheaper, faster model. This project is a small, self-hosted
version of the routing layer that production systems (LiteLLM, Not Diamond,
OpenRouter) provide commercially: a gateway that sits between an app and
several LLM providers, and decides per-request which one to call.

## How it works

1. **Compress** - strip filler/politeness phrasing from the incoming prompt
   to cut token count before anything else happens.
2. **Cache** - check a semantic cache for a near-duplicate prior query; return
   instantly on a hit, skipping inference entirely.
3. **Route** - a classifier predicts which single model should handle this
   query, based on task type, complexity, and a user-set cost/quality/speed
   priority. Only that one model is called (not all of them).
4. **Log** - every request is logged: model used, tokens saved, latency,
   estimated cost, and cache hit/miss.
5. **Reveal on demand** - the chat UI shows a clean single answer by default;
   an optional "routing details" toggle reveals the reasoning per response.
   A separate dashboard shows aggregate stats: cost saved, model
   distribution, cache hit rate.

## Structure

```
backend/    FastAPI service - compression, caching, routing, logging, API
frontend/   Next.js app - chat interface + analytics dashboard
```

## Running locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # then add your free keys (see below)
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Free API keys

| Provider | Where | Used for |
|----------|-------|----------|
| Gemini   | aistudio.google.com | balanced tier |
| Groq     | console.groq.com    | fast + premium tiers (Llama models) |

Both have free tiers (check their pages for current limits). OpenAI and
Anthropic adapters are also included and activate if you add keys. A provider
with no key runs in demo mode and returns placeholder text, so the whole
pipeline (compression → routing → logging → dashboard) works without any keys.
Which model serves each tier is set in `.env` (`FAST_MODEL`, `BALANCED_MODEL`,
`PREMIUM_MODEL`), so a retired model is a config change, not a code change.

### Training the router

Rate answers with the ▲ / ▼ buttons in the chat. Once there are at least 15
thumbs-up examples for two or more models, run `python train_classifier.py`
in `backend/` and restart the server. Until then routing is rule-based.

## Status / roadmap

- [x] Prompt compression, rule-based routing, request logging, dashboard
- [x] Gemini, Groq, OpenAI and Anthropic adapters with automatic failover
- [x] Vector semantic cache (hashing vectors + cosine similarity; strict threshold, near-duplicate queries only)
- [x] Feedback buttons and a training script for a learned router
- [ ] True embedding-based cache (bag-of-words cannot separate "capital of France" from "capital of Germany")
- [ ] Deploy: frontend on Vercel, backend on Render, database on Supabase
