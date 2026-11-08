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

## Projects (Bearer)

| Method | Path                | Description                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/projects`         | All projects with activity stats         |
| POST   | `/projects`         | Create manually                          |
| GET    | `/projects/{id}`    | Detail: repos, timeline, latest memory   |
| PATCH  | `/projects/{id}`    | Rename, describe, change status          |
| DELETE | `/projects/{id}`    | Delete project + history                 |

Statuses: `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`.

## AI insights (Bearer)

| Method | Path                          | Description                         |
| ------ | ----------------------------- | ----------------------------------- |
| GET    | `/insights`                   | Summary feed + project list         |
| GET    | `/projects/{id}/summaries`    | Summary history for a project       |
| POST   | `/projects/{id}/summaries`    | Generate `DAILY`/`WEEKLY`/`PROJECT` |

## Dashboard (Bearer)

`GET /dashboard` → active/total projects, total events, last active project,
recent activity and the latest summary.

## System

`GET /health` → status, version and whether the AI layer is enabled.
