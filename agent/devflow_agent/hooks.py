import sys
from pathlib import Path

from devflow_agent.config import config_dir
from devflow_agent.git import git_dir, hooks_dir, repo_root, run_git

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
  elif [ -x "{python}" ]; then
    "{python}" -m devflow_agent "$@" >/dev/null 2>&1
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

TEMPLATE_DIR_NAME = "git-template"


def template_dir() -> Path:
    """Where DevFlow keeps the global `git init` hook template."""
    return config_dir() / TEMPLATE_DIR_NAME


def template_hooks_dir() -> Path:
    return template_dir() / "hooks"


def is_managed(path: Path) -> bool:
    try:
        return MANAGED_MARKER in path.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        return False


def linked_marker(root: Path) -> Path:
    return git_dir(root) / "devflow-linked"


def mark_linked(root: Path) -> None:
    linked_marker(root).write_text("linked\n", encoding="utf-8")


def _render_hook(event: str, pass_args: bool) -> str:
    return SCRIPT_TEMPLATE.format(
        marker=MANAGED_MARKER,
        event=event,
        args=' "$@"' if pass_args else "",
        python=Path(sys.executable).as_posix(),
    )


def _write_hook(target: Path, event: str, pass_args: bool, backup: bool) -> None:
    if target.exists() and not is_managed(target) and backup:
        saved = target.with_name(f"{target.name}.pre-devflow")
        if not saved.exists():
            target.rename(saved)
    target.write_text(_render_hook(event, pass_args), encoding="utf-8", newline="\n")
    try:
        target.chmod(0o755)
    except OSError:
        pass


def install_hooks(path: Path | str = ".") -> tuple[Path, bool, list[str]]:
    """Install hooks. Returns (repo_root, first_link, installed_hook_names)."""
    root = repo_root(path)
    target_dir = hooks_dir(root)
    target_dir.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for hook_name, (event, pass_args) in HOOK_EVENTS.items():
        _write_hook(target_dir / hook_name, event, pass_args, backup=True)
        installed.append(hook_name)

    return root, not linked_marker(root).exists(), installed


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


# ---------- Global template (auto-track every new repo) ----------


def _global_template_setting() -> str | None:
    value = run_git(["config", "--global", "--get", "init.templateDir"], Path.home())
    return value or None


def _resolve_template_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.home() / path
    return path


def install_template_hooks() -> tuple[Path, bool]:
    """Copy hooks into the global Git init template.

    Returns (template directory, whether the global config was changed).
    If the user already has a custom ``init.templateDir``, DevFlow adds its
    hooks there instead of replacing the setting.
    """
    existing = _global_template_setting()
    config_changed = False

    if existing:
        target = _resolve_template_path(existing)
    else:
        target = template_dir()
        config_changed = True

    hooks = target / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    for hook_name, (event, pass_args) in HOOK_EVENTS.items():
        _write_hook(hooks / hook_name, event, pass_args, backup=False)

    if config_changed:
        run_git(
            ["config", "--global", "init.templateDir", target.as_posix()],
            Path.home(),
        )

    return target, config_changed


def uninstall_template_hooks() -> tuple[Path | None, bool]:
    """Remove DevFlow hooks from the template and unset our init.templateDir."""
    existing = _global_template_setting()
    if not existing:
        return None, False

    target = _resolve_template_path(existing)
    hooks = target / "hooks"
    for hook_name in HOOK_EVENTS:
        candidate = hooks / hook_name
        if candidate.exists() and is_managed(candidate):
            candidate.unlink()

    if target.resolve() == template_dir().resolve():
        run_git(["config", "--global", "--unset", "init.templateDir"], Path.home())
        return target, True
    return target, False


def template_status() -> dict:
    existing = _global_template_setting()
    if not existing:
        return {"enabled": False, "path": None, "managed": False}
    target = _resolve_template_path(existing)
    managed = all(
        (target / "hooks" / name).exists() and is_managed(target / "hooks" / name)
        for name in HOOK_EVENTS
    )
    return {"enabled": managed, "path": target, "managed": managed}
