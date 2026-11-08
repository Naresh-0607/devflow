import argparse
import sys
from pathlib import Path

from devflow_agent import __version__
from devflow_agent.client import AgentError, ping, send_event
from devflow_agent.config import (
    DEFAULT_ENDPOINT,
    clear_config,
    default_device_name,
    endpoint_of,
    load_config,
    require_config,
    save_config,
    warn,
)
from devflow_agent.git import NotARepository, current_branch, head_commit, repository_info
from devflow_agent.hooks import install_hooks, uninstall_hooks

EVENT_MAP = {
    "commit": "commit",
    "branch-change": "branch_change",
    "push": "push",
    "repository-created": "repository_created",
}


def _short_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    # Raw SHAs are not useful as branch names.
    if len(ref) >= 40 and all(ch in "0123456789abcdef" for ch in ref.lower()):
        return None
    return ref


def _build_payload(event: str, root: Path, hook_args: list[str]) -> dict:
    branch = current_branch(root)
    if event == "commit":
        return {**head_commit(root), "branch": branch}
    if event == "branch-change":
        old_ref = hook_args[0] if len(hook_args) > 0 else None
        new_ref = hook_args[1] if len(hook_args) > 1 else None
        return {
            "from_branch": _short_ref(old_ref) if old_ref and old_ref.startswith("refs/") else None,
            "to_branch": _short_ref(new_ref) if new_ref and new_ref.startswith("refs/") else branch,
            "branch": branch,
        }
    if event == "push":
        return {"branch": branch, "remote": "origin"}
    return {}


def cmd_login(args: argparse.Namespace) -> int:
    existing = load_config()
    config = {
        **existing,
        "api_key": args.key.strip(),
        "endpoint": (args.endpoint or existing.get("endpoint") or DEFAULT_ENDPOINT).rstrip("/"),
        "device_name": args.name or existing.get("device_name") or default_device_name(),
    }
    save_config(config)
    print(f"Saved DevFlow credentials in ~/.devflow/config.json (endpoint: {config['endpoint']})")
    try:
        me = ping(config)
        print(f"Connected as device '{me.get('name', config['device_name'])}'.")
    except AgentError as exc:
        warn(f"credentials saved but verification failed: {exc}")
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    clear_config()
    print("DevFlow credentials removed from this machine.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config()
    if not config.get("api_key"):
        print("Not connected. Run: devflow login --key dvf_live_...")
        return 1
    masked = config["api_key"][:16] + "..." if len(config["api_key"]) > 16 else "***"
    print(f"Endpoint : {endpoint_of(config)}")
    print(f"API key  : {masked}")
    print(f"Device   : {config.get('device_name', 'unknown')}")
    try:
        me = ping(config)
    except AgentError as exc:
        print(f"Status   : unreachable ({exc})")
        return 1
    print(f"Status   : connected (device id {me.get('id')})")
    return 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    config = require_config()
    try:
        root, first_link, installed = install_hooks(args.repo)
    except NotARepository as exc:
        warn(str(exc))
        return 1

    print(f"Installed DevFlow hooks in {root}: {', '.join(installed)}")
    if first_link:
        info = repository_info(root)
        try:
            send_event(
                config,
                {
                    "event_type": "repository_created",
                    "repository": {
                        "name": info["name"],
                        "local_identifier": info["local_identifier"],
                        "remote_url": info["remote_url"],
                    },
                    "payload": {"source": "hooks-install"},
                },
            )
            print(f"Linked repository '{info['name']}' and recorded its start date.")
        except AgentError as exc:
            warn(f"repository linked locally, but start event failed: {exc}")
    print("Git activity is now captured automatically. Code away.")
    return 0


def cmd_uninstall_hooks(args: argparse.Namespace) -> int:
    try:
        removed = uninstall_hooks(args.repo)
    except NotARepository as exc:
        warn(str(exc))
        return 1
    print("Removed DevFlow hooks" + (f": {', '.join(removed)}" if removed else " (none found)."))
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    config = load_config()
    if not config.get("api_key"):
        warn("not connected; run 'devflow login' first")
        return 2
    try:
        info = repository_info(args.repo)
        root = info["root"]
    except NotARepository as exc:
        warn(str(exc))
        return 1

    event_type = EVENT_MAP[args.event]
    payload = _build_payload(args.event, root, args.hook_args)
    try:
        send_event(
            config,
            {
                "event_type": event_type,
                "repository": {
                    "name": info["name"],
                    "local_identifier": info["local_identifier"],
                    "remote_url": info["remote_url"],
                },
                "payload": payload,
            },
        )
    except AgentError as exc:
        warn(f"event not delivered: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devflow",
        description="DevFlow local agent: capture Git activity, remember your work.",
    )
    parser.add_argument("--version", action="version", version=f"devflow-agent {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Connect this machine using an API key")
    login.add_argument("--key", required=True, help="API key from DevFlow settings (dvf_live_...)")
    login.add_argument("--endpoint", default=None, help=f"Backend URL (default {DEFAULT_ENDPOINT})")
    login.add_argument("--name", default=None, help="Device name shown in DevFlow")
    login.set_defaults(func=cmd_login)

    logout = subparsers.add_parser("logout", help="Remove credentials from this machine")
    logout.set_defaults(func=cmd_logout)

    status = subparsers.add_parser("status", help="Check the connection to DevFlow")
    status.set_defaults(func=cmd_status)

    install = subparsers.add_parser("install-hooks", help="Track a repository via Git hooks")
    install.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    install.set_defaults(func=cmd_install_hooks)

    uninstall = subparsers.add_parser("uninstall-hooks", help="Stop tracking a repository")
    uninstall.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    uninstall.set_defaults(func=cmd_uninstall_hooks)

    capture = subparsers.add_parser("capture", help=argparse.SUPPRESS)
    capture.add_argument("event", choices=list(EVENT_MAP.keys()))
    capture.add_argument("hook_args", nargs="*")
    capture.add_argument("--repo", default=".")
    capture.set_defaults(func=cmd_capture)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
