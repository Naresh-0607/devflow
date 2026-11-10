# API reference

Base URL: `http://localhost:8000/api/v1` (dev) · interactive docs at `/docs`.

## Auth (Bearer access token)

| Method | Path             | Description                          |
| ------ | ---------------- | ------------------------------------ |
| POST   | `/auth/register` | Create account, returns user + tokens|
| POST   | `/auth/login`    | Sign in, returns user + tokens       |
| POST   | `/auth/refresh`  | Rotate refresh token                 |
| POST   | `/auth/logout`   | Revoke a refresh token               |
| GET    | `/auth/me`       | Current user                         |

## Devices (Bearer)

| Method | Path               | Description                               |
| ------ | ------------------ | ----------------------------------------- |
| GET    | `/devices`         | List connected devices                    |
| POST   | `/devices`         | Create API key (plaintext returned once)  |
| GET    | `/devices/me`      | Agent ping / key validation (`X-API-Key`) |
| DELETE | `/devices/{id}`    | Revoke a device                           |

## Events

| Method | Path      | Auth     | Description                        |
| ------ | --------- | -------- | ---------------------------------- |
| POST   | `/events` | API key  | Ingest a Git event                 |
| GET    | `/events` | Bearer   | Activity feed (`project_id`, paging)|

Event types: `repository_created`, `branch_change`, `commit`, `push`.

Ingestion is rate limited per API key (default 120 events/minute). Over-limit
requests return `429` with a `Retry-After` header. Configure with
`EVENT_RATE_LIMIT_PER_MINUTE` (set `0` to disable).

## Projects (Bearer)

| Method | Path                | Description                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/projects`         | All projects with activity stats         |
| POST   | `/projects`         | Create manually                          |
| GET    | `/projects/{id}`    | Detail: repos, timeline, memories, count |
| PATCH  | `/projects/{id}`    | Rename, describe, change status          |
| DELETE | `/projects/{id}`    | Delete project + history                 |

Statuses: `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`.

## AI summaries (Bearer)

| Method | Path                          | Description                         |
| ------ | ----------------------------- | ----------------------------------- |
| GET    | `/insights`                   | Summary feed + project list (API kept for compatibility; the UI uses `/chat`) |
| GET    | `/projects/{id}/summaries`    | Summary history for a project       |
| POST   | `/projects/{id}/summaries`    | Generate `DAILY`/`WEEKLY`/`PROJECT` |

## Chat (Bearer)

`POST /chat` answers questions about the calling user's own Git activity.

```json
{
  "message": "What was I working on yesterday?",
  "history": [{ "role": "user", "content": "Hi" }],
  "timezone": "Asia/Kolkata",
  "stream": true
}
```

- `history` is optional (max 30 messages); `timezone` must be an IANA name.
- `stream: true` returns `text/event-stream` frames: `token`, `tool`, `done`,
  `error`. The default is a JSON `{ answer, tools_used }`.
- The model can only call fixed read-only tools, all scoped to the
  authenticated user: `list_projects`, `get_project`, `get_timeline`,
  `search_events`, `get_summaries`, `get_stats`. Result sizes are capped and
  the model never receives SQL access.
- Commit messages and event payloads are treated as untrusted data. If nothing
  matches, the answer is exactly `I don't see that in your activity.`
- Without a `GROQ_API_KEY` the endpoint uses a deterministic keyword fallback
  over the same tools.
- Rate limited per user (default 20 requests/minute). Configure with
  `CHAT_RATE_LIMIT_PER_MINUTE`; over-limit requests return `429` and
  `Retry-After`.

## Dashboard (Bearer)

`GET /dashboard` → active/total projects, total events, last active project,
recent activity and the latest summary. One call powers the whole dashboard.

## System

`GET /health` → status, version and whether the AI layer is enabled. The
frontend pings it once per session to wake a sleeping Render instance.

Responses include `Server-Timing: app;dur=…`; JSON responses above 500 bytes are
gzip-compressed (SSE streams are not).
