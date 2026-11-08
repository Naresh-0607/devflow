import argparse
import shutil
import subprocess
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
from devflow_agent.hooks import (
    install_hooks,
    install_template_hooks,
    linked_marker,
    mark_linked,
    template_status,
    uninstall_hooks,
    uninstall_template_hooks,
)

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


def _repository_payload(info: dict) -> dict:
    return {
        "name": info["name"],
        "local_identifier": info["local_identifier"],
        "remote_url": info["remote_url"],
    }


def _send_repository_created(config: dict, info: dict, source: str) -> None:
    send_event(
        config,
        {
            "event_type": "repository_created",
            "repository": _repository_payload(info),
            "payload": {"source": source},
        },
    )


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
            _send_repository_created(config, info, "hooks-install")
            mark_linked(root)
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

    # Hooks installed through the global template (or manually) register the
    # project on their first captured event, so `install-hooks` is optional.
    if not linked_marker(root).exists():
        try:
            _send_repository_created(config, info, "auto-link")
            mark_linked(root)
        except AgentError as exc:
            warn(f"could not auto-link repository: {exc}")

    try:
        send_event(
            config,
            {
                "event_type": event_type,
                "repository": _repository_payload(info),
                "payload": payload,
            },
        )
    except AgentError as exc:
        warn(f"event not delivered: {exc}")
        return 1
    return 0


def cmd_record_init(args: argparse.Namespace) -> int:
    """Record a freshly initialised repository immediately (used by git init)."""
    config = require_config()
    try:
        root, first_link, installed = install_hooks(args.repo)
    except NotARepository as exc:
        warn(str(exc))
        return 1

    if first_link or not linked_marker(root).exists():
        info = repository_info(root)
        try:
            _send_repository_created(config, info, "git-init")
            mark_linked(root)
        except AgentError as exc:
            warn(f"repository initialised, but DevFlow could not record it: {exc}")
            return 1
        if not args.quiet:
            print(f"DevFlow is now tracking '{info['name']}'.")
    elif not args.quiet:
        print(f"DevFlow is already tracking '{root}'.")
    return 0


def cmd_auto_track(args: argparse.Namespace) -> int:
    if args.status:
        status = template_status()
        if status["enabled"]:
            print(f"Auto-track: enabled (hooks template: {status['path']})")
        elif status["path"]:
            print(f"Auto-track: partially configured at {status['path']} (run devflow auto-track)")
        else:
            print("Auto-track: disabled")
        return 0

    if args.disable:
        target, unset = uninstall_template_hooks()
        if target is None:
            print("Auto-track was already disabled.")
        else:
            print(f"Removed DevFlow hooks from {target}.")
            if unset:
                print("Cleared global init.templateDir.")
        return 0

    target, config_changed = install_template_hooks()
    print("Auto-track enabled: new repositories created with 'git init' get DevFlow hooks.")
    print(f"Hooks template: {target}")
    if config_changed:
        print(f"Set global init.templateDir -> {target.as_posix()}")
    print("Existing repos still need: devflow install-hooks")
    return 0


PROFILE_BEGIN = "# >>> DevFlow git init capture >>>"
PROFILE_END = "# <<< DevFlow git init capture <<<"


def _profile_snippet() -> str:
    # An absolute interpreter path keeps this working without the agent venv
    # being active in every PowerShell session.
    python = Path(sys.executable).as_posix()
    return f"""{PROFILE_BEGIN}
# Records DevFlow projects the moment `git init` creates a repository.
$DevFlowGit = (Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1)
if ($DevFlowGit) {{
    function git {{
        & $DevFlowGit.Source @args
        $devflowExit = $LASTEXITCODE
        if ($devflowExit -eq 0 -and $args.Count -ge 1 -and $args[0] -eq 'init') {{
            $target = if ($args.Count -ge 2 -and -not $args[1].StartsWith('-')) {{ $args[1] }} else {{ '.' }}
            & "{python}" -m devflow_agent record-init --repo $target --quiet *> $null
        }}
        $global:LASTEXITCODE = $devflowExit
    }}
}}
{PROFILE_END}
"""


def _powershell_profiles() -> list[Path]:
    """Return the CurrentUserAllHosts profile path for every installed PowerShell."""
    shells = [shell for shell in ("powershell", "pwsh") if shutil.which(shell)]
    profiles: list[Path] = []
    for shell in shells:
        try:
            result = subprocess.run(
                [shell, "-NoProfile", "-Command", "$PROFILE.CurrentUserAllHosts"],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        path = result.stdout.strip()
        if not path:
            continue
        candidate = Path(path)
        if candidate not in profiles:
            profiles.append(candidate)
    return profiles


def _strip_block(text: str) -> str:
    start = text.find(PROFILE_BEGIN)
    end = text.find(PROFILE_END)
    if start != -1 and end != -1:
        text = text[:start] + text[end + len(PROFILE_END):]
    return text.rstrip()


def cmd_shell_integration(args: argparse.Namespace) -> int:
    snippet = _profile_snippet()
    if args.print_only or not (args.install or args.uninstall):
        print(snippet)
        print("# Add the block above to your PowerShell profile (or run --install).")
        return 0

    profiles = _powershell_profiles()
    if not profiles:
        warn("could not locate a PowerShell profile")
        return 1

    for profile in profiles:
        profile.parent.mkdir(parents=True, exist_ok=True)
        existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
        cleaned = _strip_block(existing)

        if args.uninstall:
            profile.write_text((cleaned + "\n") if cleaned else "", encoding="utf-8")
            print(f"Removed DevFlow git integration from {profile}")
        else:
            updated = (cleaned + "\n\n" if cleaned else "") + snippet
            profile.write_text(updated, encoding="utf-8")
            print(f"Installed DevFlow git integration in {profile}")

    action = "Removed" if args.uninstall else "Installed"
    print(f"{action}. Open a new PowerShell window for changes to take effect.")
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

    record_init = subparsers.add_parser(
        "record-init", help="Record a repository created with `git init` right away"
    )
    record_init.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    record_init.add_argument("--quiet", action="store_true", help="Suppress output")
    record_init.set_defaults(func=cmd_record_init)

    auto = subparsers.add_parser(
        "auto-track", help="Automatically track every new repository created with git init"
    )
    auto.add_argument("--disable", action="store_true", help="Stop auto-tracking new repositories")
    auto.add_argument("--status", action="store_true", help="Show auto-track configuration")
    auto.set_defaults(func=cmd_auto_track)

    shell = subparsers.add_parser(
        "shell-integration", help="Record `git init` immediately via your PowerShell profile"
    )
    shell.add_argument("--install", action="store_true", help="Add the wrapper to your PowerShell profile")
    shell.add_argument("--uninstall", action="store_true", help="Remove the wrapper from your profile")
    shell.add_argument("--print", dest="print_only", action="store_true", help="Print the snippet only")
    shell.set_defaults(func=cmd_shell_integration)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
