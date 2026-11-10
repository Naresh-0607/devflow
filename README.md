# DevFlow

> Developers forget what they worked on. DevFlow remembers.

DevFlow is an AI-powered developer memory system. It captures Git activity from your
local repositories through lightweight Git hooks, stores a searchable timeline in the
cloud, and turns that timeline into human-readable summaries.

## Monorepo layout

| Path        | Description                                              |
| ----------- | -------------------------------------------------------- |
| `backend/`  | FastAPI API, auth, event ingestion, AI summary layer     |
| `frontend/` | SvelteKit PWA (dashboard, projects, chat, settings)      |
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

The backend defaults to a local SQLite database (tables are created
automatically in development). Set `DATABASE_URL` to a Neon Postgres URL for
production; production schema changes are applied with `alembic upgrade head`
(Render runs it automatically before starting the API).

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

# optional: track every new repo created with `git init`
devflow auto-track                 # hooks template for all future repos
devflow shell-integration --install  # PowerShell: record `git init` instantly

cd path/to/your/repo
devflow install-hooks              # or: devflow record-init
```

From then on every commit, checkout/switch and push is captured automatically.
Repositories created after `devflow auto-track` are linked on their first Git
event, and `git init` is recorded immediately when shell integration is enabled.
Use `devflow status` to check the connection.

## Core flow

```
git commit / checkout / push
        ↓
Git hook → devflow agent → POST /api/v1/events (API key auth)
        ↓
FastAPI → Neon/SQLite → project + repository timeline
        ↓
LiteLLM (Groq) → AI summaries + database-backed chat
        ↓
SvelteKit PWA (phone) → "Here's what you were building."
```

## What is implemented

- [x] Email/password auth with Argon2id, JWT access tokens and rotating refresh tokens
- [x] Device API keys (`dvf_live_…`), one-time reveal and revocation
- [x] Event ingestion for `repository_created`, `branch_change`, `commit`, `push`
- [x] Automatic project/repository creation and project start dates
- [x] Dashboard with a "Continue where you left off" hero, projects, vertical timeline and settings pages
- [x] "Ask DevFlow" chat backed by fixed, user-scoped read-only tools (no SQL from the model)
- [x] Mobile-first responsive PWA with offline shell, install manifest and light/dark themes
- [x] LiteLLM/Groq summaries and chat with a deterministic offline fallback
- [x] Local agent with non-blocking `post-commit`, `post-checkout`, `pre-push` hooks
- [x] Global Git hooks template + auto-tracking of newly initialised repositories (`git init`)
- [x] Alembic migrations for production schema changes
- [x] Per-API-key event rate limiting and per-user chat rate limiting
- [x] Frontend caching/preloading, gzip, health ping and measured performance (see [docs/performance.md](docs/performance.md))
- [x] Backend test suite (`15 passed`) and verified end-to-end Git hook flow

## Next steps

See [ROADMAP.md](ROADMAP.md) for the remaining v1.x work:

