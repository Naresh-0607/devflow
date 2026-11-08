# DevFlow Agent

Event-driven local agent for DevFlow. It wakes up only when Git events happen —
no polling, no keystroke tracking, no screen time measurement.

## Install

```bash
cd agent
pip install -e .
```

## Connect

Generate an API key in DevFlow → Settings → Connected devices, then:

```bash
devflow login --key dvf_live_xxx --endpoint http://localhost:8000
devflow status
```

## Track a repository

```bash
cd path/to/repo
devflow install-hooks
```

This installs `post-commit`, `post-checkout` and `pre-push` hooks (previous hooks
are preserved and still run). The first install also records the repository start
date so DevFlow knows when the project began.

## What gets captured

| Git action           | Hook          | Event type           |
| -------------------- | ------------- | -------------------- |
| `git commit`         | post-commit   | `commit`             |
| `git checkout/switch`| post-checkout | `branch_change`      |
| `git push`           | pre-push      | `push`               |
| first hook install   | —             | `repository_created` |

Hooks always exit `0`, so DevFlow can never block or fail a Git command.

## Config

Stored in `~/.devflow/config.json` (mode restricted where supported):

```json
{
  "api_key": "dvf_live_...",
  "endpoint": "http://localhost:8000",
  "device_name": "Naresh-laptop"
}
```
