# DevFlow roadmap

DevFlow v1.0 covers the complete MVP journey: create an account, connect a
laptop, capture Git activity, browse project timelines, and read AI-generated
memories.

These are the agreed follow-ups after v1.0.

## v1.x

- [ ] **Scheduled summaries** — daily and weekly AI summaries generated
      automatically by a Render cron job instead of only on demand.
- [ ] **Project ↔ repository management UI** — link multiple repositories to one
      project, move repos between projects, and merge duplicate projects.

## v2

- [ ] **PNG app icons and push notifications** — fully installable PWA with
      generated icon sizes and opted-in activity reminders.
- [ ] **Audit logs** — record device key creation/revocation and event ingestion
      decisions for account security.
- [ ] **Agent tests and CI** — unit tests for hook installation/capture and a CI
      workflow that runs backend tests, agent tests, `svelte-check`, and the
      frontend build on every pull request.
