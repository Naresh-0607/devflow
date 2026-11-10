# Architecture

## Principles

1. **Event-driven, not surveillance-driven.** The agent wakes on Git events only. No
   polling, keystroke logging, screen time or mouse tracking.
2. **The AI never sees a repository.** It receives compact, human-readable event lines.
3. **Memory is durable.** Every Git event is stored before it is summarised.
4. **The agent must never block Git.** Hooks always exit `0`.

## Components

```
 Phone / Browser (SvelteKit PWA, Cloudflare Pages)
        │  Bearer JWT (access + rotating refresh)
        ▼
 FastAPI (Render)
        │
   ┌────┴─────────┐
   ▼              ▼
 Neon Postgres   LiteLLM → Groq
        ▲
        │  HTTPS + X-API-Key
        │
 Local agent (Python)
        │
 Git hooks: post-commit · post-checkout · pre-push
```

## Data model

| Table            | Purpose                                                |
| ---------------- | ------------------------------------------------------ |
| `users`          | Account, Argon2id password hash                        |
| `devices`        | One row per machine; SHA-256 hash of `dvf_live_…` key  |
| `refresh_tokens` | Rotating refresh tokens (hashed, revocable)            |
| `projects`       | A memory space; status + start date                    |
| `repositories`   | Git repos linked to a project by `local_identifier`    |
| `git_events`     | Immutable event log with JSON payload                  |
| `ai_summaries`   | Generated DAILY / WEEKLY / PROJECT memories            |

A project is created automatically the first time an event arrives from a new
repository (named after the repository). Projects can also be created manually.

## Event ingestion

```
POST /api/v1/events
X-API-Key: dvf_live_…
{
  "event_type": "commit",
  "repository": {
    "name": "jarvis",
    "local_identifier": "/home/dev/jarvis",
    "remote_url": "https://github.com/dev/jarvis"
  },
  "payload": { "sha": "...", "message": "...", "branch": "voice-v2" }
}
```

The backend resolves the repository by `(user, local_identifier)`, creates the
project/repository on first contact, stores the event and updates project
activity. `repository_created` also sets the project start date.

## Catching `git init`

Git fires no hook when a repository is created, so the agent uses three layers:

1. **Global template hooks** — `devflow auto-track` writes the
   `post-commit`/`post-checkout`/`pre-push` hooks into `~/.devflow/git-template`
   and sets `init.templateDir`. Every `git init`/`git clone` inherits them.
2. **PowerShell integration** — `devflow shell-integration --install` adds a
   small `git` wrapper to `$PROFILE` that calls `devflow record-init` right after
   a successful `git init`, so the project is recorded immediately (the wrapper
   uses an absolute Python path and works without the venv active).
3. **Auto-link** — the first captured event from any unregistered repository
   sends `repository_created` followed by the event, so `install-hooks` is
   optional.

Hooks and the wrapper always exit `0`; DevFlow can never break a Git command.

## Authentication

- **Users:** email + password. Passwords hashed with Argon2id. Access JWT (30 min)
  and rotating refresh token (30 days, hash stored in DB, revoked on use).
- **Agent:** long-lived API key `dvf_live_<random>`. Only the SHA-256 hash is stored.
  The plaintext key is returned once at creation. Revoking a device invalidates it.

## Scheduling / summaries

For the MVP, summaries are generated on demand from the Insights page (or
`POST /projects/{id}/summaries`). The AI layer uses LiteLLM with Groq; if no
`GROQ_API_KEY` is configured, a deterministic local summary is produced so the
product still works offline.

## Production notes

- Production schema changes are managed by Alembic. Render runs
  `alembic upgrade head` before starting the API; `create_all` only runs in
  non-production environments.
- Configure `CORS_ORIGINS` to the deployed frontend origin.
- Set a strong `SECRET_KEY` (32+ random bytes).
- Deploy the frontend with `@sveltejs/adapter-cloudflare` and set `VITE_API_URL`.
- Run the backend on Render with the Neon `DATABASE_URL` (auto-normalised to
  `postgresql+asyncpg://`).
- New repositories are tracked automatically via the global `init.templateDir`
  template (`devflow auto-track`); existing repositories need a one-time
  `devflow install-hooks` or `devflow record-init`.
