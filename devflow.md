# DevFlow - Complete Product Blueprint (0% to 100%)

# Executive Summary

DevFlow is an AI-powered developer memory system.

Its purpose is simple:

> Developers forget what they worked on. DevFlow remembers.

Instead of focusing on commit statistics or project management, DevFlow converts Git activity into a searchable timeline, project memory, and AI-generated development summaries.

---

# Problem Statement

Developers often:

- Work across multiple repositories.
- Create many branches.
- Make dozens of commits.
- Switch between projects frequently.
- Forget what they were building.

Current tools show Git data.

DevFlow explains development progress.

---

# Product Vision

Open DevFlow from a phone and instantly know:

- What project you're working on.
- When it started.
- Recent development activity.
- Current focus area.
- AI-generated summaries.
- Historical timeline.

Core principle:

> You code. DevFlow remembers.

---

# Technology Stack

## Frontend

- SvelteKit
- TypeScript
- Tailwind CSS
- Progressive Web App (PWA)
- Cloudflare Pages

## Backend

- FastAPI
- Python
- Render

## Database

- Neon PostgreSQL

## AI Layer

- LiteLLM
- Groq

## Local Agent

- Python
- Git Hooks
- Local Configuration Storage

---

# High Level Architecture

```text
 Phone / Browser
        │
        ▼
 Cloudflare Pages
  (SvelteKit PWA)
        │
        ▼
 FastAPI Backend
      (Render)
        │
   ┌────┴─────┐
   │          │
   ▼          ▼
Neon DB    AI Layer
            Groq

        ▲
        │
        │ HTTPS
        │
 Local DevFlow Agent
        │
        ▼
 Local Git Repositories
```

---

# Local Agent Design

The agent is event-driven.

It does NOT:

- Continuously scan repositories.
- Track keyboard activity.
- Track mouse activity.
- Measure active screen time.

The agent wakes only when important Git events occur.

Tracked events:

- git init
- git checkout
- git switch
- git commit
- git push

Workflow:

```text
Git Event
    ↓
Agent Triggered
    ↓
Collect Metadata
    ↓
Send To Backend
    ↓
Sleep
```

---

# Authentication Architecture

## User Authentication

- Register
- Login
- Refresh Tokens
- Logout

Password hashing:

- Argon2id

## Agent Authentication

User generates API Key.

Example:

```text
dvf_live_xxxxxxxxx
```

Agent setup flow:

```text
Website
   ↓
Generate API Key
   ↓
Agent Login
   ↓
Paste Key
   ↓
Device Registered
```

---

# Database Schema

## users

```sql
id
email
password_hash
created_at
updated_at
```

## devices

```sql
id
user_id
name
api_key_hash
last_seen
created_at
```

## projects

```sql
id
user_id
name
description
status
started_at
completed_at
created_at
updated_at
```

Status values:

- ACTIVE
- PAUSED
- COMPLETED
- ARCHIVED

## repositories

```sql
id
project_id
name
remote_url
local_identifier
created_at
```

## git_events

```sql
id
repository_id
event_type
payload_json
created_at
```

## ai_summaries

```sql
id
project_id
summary
summary_type
created_at
```

---

# Event Types

## Repository Created

```text
git init
```

Purpose:

- Determine project start date.

## Branch Change

```text
git checkout
git switch
```

Purpose:

- Track focus changes.

## Commit

```text
git commit
```

Purpose:

- Capture completed development activity.

## Push

```text
git push
```

Purpose:

- Mark activity published remotely.

---

# AI Layer Responsibilities

The AI never receives an entire repository.

Input:

```json
{
  "project":"Jarvis",
  "events":[
    "checkout voice-v2",
    "commit websocket routing",
    "commit microphone fixes",
    "push voice-v2"
  ]
}
```

Output:

```text
Work continued on the voice system.
Main focus was websocket routing and microphone reliability.
The project appears to be progressing toward a complete voice pipeline.
```

---

# Frontend Pages

## Dashboard

Displays:

- Active Projects
- Recent Activity
- Latest AI Summary
- Last Active Project

## Projects

Displays:

- All projects
- Status
- Start date
- Last activity

## Project Details

Displays:

- Timeline
- Branch activity
- Commit history
- AI summaries

## AI Insights

Displays:

- Daily summaries
- Weekly summaries
- Project memories

## Settings

Displays:

- Account settings
- API keys
- Connected devices

---

# Mobile Experience

Primary screen:

```text
Jarvis

Started:
67 days ago

Last Activity:
Yesterday

Recent Work:
- Created voice-v2 branch
- Added websocket routing
- Fixed microphone issues

Current Focus:
Voice System
```

---

# Core User Journey

1. User creates account.
2. User generates API key.
3. User installs agent.
4. User links laptop.
5. User starts coding.
6. Git events are captured.
7. Backend stores activity.
8. AI generates summaries.
9. User opens phone.
10. DevFlow explains recent work.

---

# Non-Goals

DevFlow is NOT:

- Jira
- Trello
- GitHub replacement
- Time tracker
- Employee monitoring software
- Screen activity tracker

---

# MVP Success Criteria

A user should be able to:

- Create an account.
- Connect a laptop.
- Track Git events.
- View project timelines.
- Read AI-generated summaries.
- See when projects started.
- Remember what they were building.

If those goals are met, Version 1 is successful.

---

# Final Product Statement

DevFlow is a personal AI-powered developer memory platform that captures Git activity from local repositories, builds a searchable development timeline, generates intelligent summaries, and helps developers instantly remember what they were building from any device.
