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

## Record `git init` automatically

Git has no `init` hook, so DevFlow offers two complementary mechanisms.

**1. Auto-track every new repository (recommended):**

```bash
devflow auto-track          # enable
devflow auto-track --status
devflow auto-track --disable
```

This installs DevFlow hooks into the global Git template and sets
`init.templateDir`, so every `git init` (and `git clone`) gets hooks automatically.
If you already have a custom `init.templateDir`, DevFlow adds its hooks there
instead of overwriting your setting.

**2. Record the repository at the moment `git init` runs (PowerShell):**

```powershell
devflow shell-integration --install   # adds a small `git` wrapper to $PROFILE
devflow shell-integration --uninstall # remove it
devflow shell-integration --print     # print the snippet only
```

Open a new PowerShell window afterwards. From then on `git init` calls
`devflow record-init`, which installs hooks and sends `repository_created`
immediately — the project appears in the dashboard before your first commit.

**Repos created without either mechanism** are auto-linked on their first
captured event (the agent sends `repository_created` + the event).

You can also record any existing repo immediately:

```bash
devflow record-init                 # current directory
devflow record-init --repo C:\path\to\repo
```

## What gets captured

| Git action           | Hook / trigger     | Event type           |
| -------------------- | ------------------ | -------------------- |
| `git init`           | shell integration  | `repository_created` |
| first captured event | auto-link          | `repository_created` |
| `devflow install-hooks` | —               | `repository_created` |
| `git commit`         | post-commit        | `commit`             |
| `git checkout/switch`| post-checkout      | `branch_change`      |
| `git push`           | pre-push           | `push`               |

Hooks always exit `0`, so DevFlow can never block or fail a Git command.

## Commands

```text
devflow login --key dvf_live_... [--endpoint URL] [--name NAME]
devflow status
devflow logout
devflow install-hooks [--repo PATH]
devflow uninstall-hooks [--repo PATH]
devflow record-init [--repo PATH] [--quiet]
devflow auto-track [--status | --disable]
devflow shell-integration [--install | --uninstall | --print]
devflow --version
```

## Config

Stored in `~/.devflow/config.json` (mode restricted where supported):

```json
{
  "api_key": "dvf_live_...",
  "endpoint": "http://localhost:8000",
  "device_name": "Naresh-laptop"
}
```
