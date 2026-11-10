# Performance notes (v1.1)

This document records what was measured, what changed, and the remaining
infrastructure costs (cold starts, region) that code cannot remove.

## Method

- Harness: in-process FastAPI app over `httpx.ASGITransport` (no network), one
  warm-up request then 10 measured requests per endpoint.
- Fixture: one user, 5 projects, 60 Git events per project, one stored summary.
- Report: median of three runs. The machine was heavily loaded during the
  re-measurement, so the same-session v1.0 numbers are the useful comparison.
  The original v1.0 numbers were captured on a quieter machine and are kept for
  history.
- Frontend route timing is logged to the browser console as
  `[devflow] route /path settled in Nms` after every client navigation.

### Original baseline (before any v1.1 changes)

| Endpoint                         | avg    | p95    |
| -------------------------------- | ------ | ------ |
| `GET /health`                    | 0.3 ms | 0.4 ms |
| `GET /api/v1/dashboard`          | 11.4   | 13.5   |
| `GET /api/v1/projects`           | 10.9   | 11.5   |
| `GET /api/v1/projects/{id}`      | 10.2   | 13.7   |
| `GET /api/v1/insights`           | 13.8   | 16.6   |
| `GET /api/v1/events?limit=50`    | 5.6    | 6.7    |

### Same-session comparison (median of 3 runs, same machine)

| Endpoint                      | v1.0 avg | v1.1 avg | Change |
| ----------------------------- | -------- | -------- | ------ |
| `GET /health`                 | 1.4 ms   | 1.0 ms   | ~0     |
| `GET /api/v1/dashboard`       | 52.8 ms  | 44.4 ms  | −16%   |
| `GET /api/v1/projects`        | 58.0 ms  | 18.6 ms  | −68%   |
| `GET /api/v1/projects/{id}`   | 47.2 ms  | 36.8 ms  | −22%   |
| `GET /api/v1/insights`        | 67.9 ms  | 21.2 ms  | −69%   |
| `GET /api/v1/events?limit=50` | 31.9 ms  | 27.0 ms  | −15%   |
| `POST /api/v1/chat` (offline) | —        | 36.3 ms  | new    |

The variance between runs is large on Windows (for example dashboard ranged
from 7.6 ms to 45.9 ms), which is why the table uses medians and a same-session
baseline rather than the quieter original run.

## Backend changes

- **N+1 removal.** `project_metrics_bulk()` answers last activity, event count
  and repository count for many projects with two grouped queries. Projects,
  insights and dashboard no longer issue three queries per project.
- **Indexes.** `git_events(repository_id, created_at)`,
  `repositories(project_id)`, `projects(user_id, status)` and
  `ai_summaries(project_id, created_at)`, applied by
  `20261110_0002_performance_indexes.py` (the first two already existed in the
  initial migration).
- **One dashboard call.** `GET /api/v1/dashboard` returns the hero project,
  stats, recent activity and latest summary together, so the dashboard no
  longer fans out to three endpoints.
- **Bounded timelines.** Project detail/events return at most 50 recent events;
  `GET /events` also supports `limit`/`offset`.
- **Compression.** JSON responses above 500 bytes are gzip-compressed. SSE chat
  streams are explicitly exempt so tokens are not buffered.
- **Cheap timing.** Request timing is a pure-ASGI middleware that adds
  `Server-Timing: app;dur=…` and logs `METHOD route -> status Nms` without
  spawning a task group per request.
- **Auth refresh.** The client only calls `/auth/refresh` after a `401`, and
  concurrent refreshes share one in-flight request. A valid access token is
  reused directly, so there is no extra request before each API call.

## Frontend changes

- The app is client-rendered (`ssr = false`); authenticated data lives behind
  localStorage tokens, so server rendering would only ship a shell.
- Route `load` functions return cached data **immediately** and a `fresh`
  promise. Navigation is never blocked on the network.
- Stale-while-revalidate cache per user (`dvf_cache:<user>:<path>`) for
  dashboard, projects and project detail. Mutations invalidate the user's
  cached paths.
- `data-sveltekit-preload-data="hover"` (set globally and on nav links) starts
  route loads on hover/touch before the click lands.
- Skeletons render immediately; fresh data swaps in when it arrives.
- Dashboard makes one request instead of three.
- The markdown renderer is a 1.6 kB dynamic chunk loaded only after the first
  answer completes.

### Bundle check (`npm run build`)

| Asset                                  | Size    | gzip   |
| -------------------------------------- | ------- | ------ |
| shared CSS                             | 53.6 kB | 9.5 kB |
| SvelteKit client runtime               | 44.2 kB | 17.1 kB|
| Svelte runtime chunk                   | 42.7 kB | 15.7 kB|
| largest route chunk (project detail)   | 14.0 kB | 3.9 kB |
| chat route chunk                       | 8.7 kB  | 2.8 kB |
| markdown (lazy)                        | 1.6 kB  | 0.8 kB |
| service worker                         | 2.6 kB  | 1.0 kB |

The two ~43 kB chunks are SvelteKit/Svelte runtime code shared by every route,
not app code. The service worker pre-caches the app shell and hashed assets,
uses network-first for navigations and never caches `/api/`.

## Cold starts and region

- Render free instances sleep. `wakeBackend()` fires a one-time `/health` ping
  per browser session while the shell paints, so a sleeping instance starts
  earlier. This does not remove the first-visit latency.
- To remove cold starts entirely, use a paid Render instance **or** point an
  external pinger (UptimeRobot, every 5 minutes) at `/health`. Both are
  infrastructure settings; no code change is required.
- Use Neon's **pooled** connection string (the `-pooler` host). The current
  `DATABASE_URL` already does this.
- Render and Neon should be in the same region. For Chennai, use
  **Singapore** (`aws-ap-southeast-1` on Neon, `singapore` on Render). The
  blueprint in `render.yaml` now requests Singapore; if the API service already
  exists in another region, recreate it, then create/restore the Neon project
  in Singapore and update `DATABASE_URL`.
