import subprocess
from pathlib import Path


class NotARepository(RuntimeError):
    pass


def run_git(args: list[str], cwd: Path | str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repo_root(path: Path | str = ".") -> Path:
    output = run_git(["rev-parse", "--show-toplevel"], path)
    if not output:
        raise NotARepository(f"{path} is not inside a Git repository")
    return Path(output)


def current_branch(root: Path) -> str | None:
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if not branch or branch == "HEAD":
        return None
    return branch


def remote_url(root: Path) -> str | None:
    return run_git(["remote", "get-url", "origin"], root)


def repository_info(path: Path | str = ".") -> dict:
    root = repo_root(path)
    return {
        "name": root.name,
        "local_identifier": str(root),
        "remote_url": remote_url(root),
        "root": root,
        "branch": current_branch(root),
    }


def head_commit(root: Path) -> dict:
    raw = run_git(["log", "-1", "--format=%H%x00%s%x00%an%x00%aI"], root)
    if not raw:
        return {}
    parts = raw.split("\x00")
    if len(parts) < 4:
        return {}
    sha, message, author, committed_at = parts
    return {"sha": sha, "message": message, "author": author, "committed_at": committed_at}


def git_dir(root: Path) -> Path:
    raw = run_git(["rev-parse", "--git-dir"], root)
    if not raw:
        raise NotARepository(f"Cannot resolve .git directory for {root}")
    path = Path(raw)
    return path if path.is_absolute() else root / path


def hooks_dir(root: Path) -> Path:
    raw = run_git(["rev-parse", "--git-path", "hooks"], root)
    path = Path(raw) if raw else git_dir(root) / "hooks"
    return path if path.is_absolute() else root / path
