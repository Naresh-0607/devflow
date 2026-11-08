# DevFlow

> Developers forget what they worked on. DevFlow remembers.

DevFlow is an AI-powered developer memory system. It captures Git activity from your
local repositories through lightweight Git hooks, stores a searchable timeline in the
cloud, and turns that timeline into human-readable summaries.

## Monorepo layout

| Path        | Description                                              |
| ----------- | -------------------------------------------------------- |
| `backend/`  | FastAPI API, auth, event ingestion, AI summary layer     |
| `frontend/` | SvelteKit PWA (dashboard, projects, insights, settings)  |
| `agent/`    | Local event-driven agent + Git hook installer            |
| `docs/`     | Architecture and API notes                               |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

The backend defaults to a local SQLite database. Set `DATABASE_URL` to a Neon
Postgres URL for production.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### 3. Local agent

```bash
cd agent
pip install -e .
devflow login --key dvf_live_xxx --endpoint http://localhost:8000
cd path/to/your/repo
devflow install-hooks
```

From then on every commit, checkout/switch and push is captured automatically.
Use `devflow status` to check the connection.

## Core flow

```
git commit / checkout / push
        ↓
Git hook → devflow agent → POST /api/v1/events (API key auth)
        ↓
FastAPI → Neon/SQLite → project + repository timeline
        ↓
LiteLLM (Groq) → AI summaries
        ↓
SvelteKit PWA (phone) → "Here's what you were building."
```

## What is implemented

- [x] Email/password auth with Argon2id, JWT access tokens and rotating refresh tokens
- [x] Device API keys (`dvf_live_…`), one-time reveal and revocation
- [x] Event ingestion for `repository_created`, `branch_change`, `commit`, `push`
- [x] Automatic project/repository creation and project start dates
- [x] Dashboard, projects, project timeline, AI insights and settings pages
- [x] Mobile-first responsive PWA with offline shell and install manifest
- [x] LiteLLM/Groq summaries with a deterministic offline fallback
- [x] Local agent with non-blocking `post-commit`, `post-checkout`, `pre-push` hooks
- [x] Backend test suite (`8 passed`) and verified end-to-end Git hook flow

## Next steps

- Alembic migrations instead of `create_all` for production schema changes
- Background summary generation (daily/weekly) via a Render cron job
- Global Git hooks path + auto-tracking newly initialised repositories
- Project ↔ repository management UI (link multiple repos to one project)
- PNG app icons and push notifications for a fully installable PWA
- Rate limiting and audit logs for the event ingestion API

