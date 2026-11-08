from pathlib import Path

from devflow_agent.git import git_dir, hooks_dir, repo_root

MANAGED_MARKER = "Managed by DevFlow"

HOOK_EVENTS = {
    "post-commit": ("commit", False),
    "post-checkout": ("branch-change", True),
    "pre-push": ("push", False),
}

SCRIPT_TEMPLATE = """#!/bin/sh
# {marker}. Reinstall with: devflow install-hooks
# Never blocks Git: every path exits 0.
run_devflow() {{
  if command -v devflow >/dev/null 2>&1; then
    devflow "$@" >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m devflow_agent "$@" >/dev/null 2>&1
  elif command -v python >/dev/null 2>&1; then
    python -m devflow_agent "$@" >/dev/null 2>&1
  fi
}}
run_devflow capture {event}{args}
if [ -x "$0.pre-devflow" ]; then
  "$0.pre-devflow" "$@" >/dev/null 2>&1 || true
fi
exit 0
"""


def is_managed(path: Path) -> bool:
    try:
        return MANAGED_MARKER in path.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        return False


def install_hooks(path: Path | str = ".") -> tuple[Path, bool, list[str]]:
    """Install hooks. Returns (repo_root, first_link, installed_hook_names)."""
    root = repo_root(path)
    target_dir = hooks_dir(root)
    target_dir.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for hook_name, (event, pass_args) in HOOK_EVENTS.items():
        target = target_dir / hook_name
        if target.exists() and not is_managed(target):
            backup = target_dir / f"{hook_name}.pre-devflow"
            if not backup.exists():
                target.rename(backup)

        script = SCRIPT_TEMPLATE.format(
            marker=MANAGED_MARKER,
            event=event,
            args=' "$@"' if pass_args else "",
        )
        target.write_text(script, encoding="utf-8", newline="\n")
        try:
            target.chmod(0o755)
        except OSError:
            pass
        installed.append(hook_name)

    marker_path = git_dir(root) / "devflow-linked"
    first_link = not marker_path.exists()
    if first_link:
        marker_path.write_text("linked\n", encoding="utf-8")

    return root, first_link, installed


def uninstall_hooks(path: Path | str = ".") -> list[str]:
    root = repo_root(path)
    target_dir = hooks_dir(root)
    removed: list[str] = []
    for hook_name in HOOK_EVENTS:
        target = target_dir / hook_name
        if target.exists() and is_managed(target):
            target.unlink()
            removed.append(hook_name)
            backup = target_dir / f"{hook_name}.pre-devflow"
            if backup.exists():
                backup.rename(target)
    return removed
