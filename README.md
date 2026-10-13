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
backend/              FastAPI service - compression, caching, routing, logging, API (+ Dockerfile)
frontend/             Next.js app - chat interface + analytics dashboard (+ Dockerfile)
docker-compose.yml    runs db (PostgreSQL, persistent volume) + backend + frontend
.env.example          settings for Docker Compose (copy to .env)
```

## Run with Docker (lab systems)

Needs Docker with Compose v2 (`docker compose version` should print a version) and internet access for the first build.

```bash
git clone https://github.com/manishaagangadevi/llm-router.git
cd llm-router
cp .env.example .env        # Windows: copy .env.example .env
docker compose up --build
```

Then open:

| What | URL |
|------|-----|
| App (chat) | http://localhost:3000 |
| Dashboard | http://localhost:3000/dashboard |
| API docs | http://localhost:8000/docs |

This starts three containers: `db` (PostgreSQL 16), `backend` (FastAPI) and `frontend` (Next.js). The backend waits for the database to be healthy before starting.

**Persistent storage.** Request logs live in the Docker volume `llm-router_pgdata`, so they survive `docker compose stop`, `docker compose down`, restarts and rebuilds. Only `docker compose down -v` deletes the data.

**API keys are optional.** Without keys the app runs in demo mode and returns placeholder answers, so every feature (compression, routing, logging, dashboard, feedback) can still be demonstrated. For real answers put `GEMINI_API_KEY` and/or `GROQ_API_KEY` in `.env` (never commit `.env`), then run `docker compose up -d --build backend`. The lab network must allow `generativelanguage.googleapis.com` and `api.groq.com`.

**Good to know**
- Do not change `POSTGRES_PASSWORD` after the first start: the volume keeps the old password. To reset, run `docker compose down -v` (this erases the data).
- Ports 3000 and 8000 must be free on the machine.
- To open the app from a different PC than the one running Docker, set `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` in `.env` to that machine's address, then rebuild with `docker compose up --build`.
- The semantic cache is held in memory and starts empty after every backend restart.
- `train_classifier.py` saves the trained router inside the backend container. `docker compose restart backend` keeps it, but `docker compose down` or a rebuild removes it, so re-run the training afterwards.
- Run the training in Docker with `docker compose exec backend python train_classifier.py`, then `docker compose restart backend`.

## Running without Docker (development)

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
- [x] Docker Compose setup: frontend, backend and PostgreSQL with a persistent volume
- [ ] Public hosting (optional)
