import json
import os
import sys
from pathlib import Path

DEFAULT_ENDPOINT = "http://localhost:8000"


def config_dir() -> Path:
    override = os.environ.get("DEVFLOW_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".devflow"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = config_path()
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def clear_config() -> None:
    path = config_path()
    if path.exists():
        path.unlink()


def default_device_name() -> str:
    import socket

    return socket.gethostname() or "unknown-device"


def require_config() -> dict:
    config = load_config()
    if not config.get("api_key"):
        print("DevFlow is not connected yet. Run: devflow login --key dvf_live_...")
        raise SystemExit(2)
    return config


def endpoint_of(config: dict) -> str:
    return (config.get("endpoint") or DEFAULT_ENDPOINT).rstrip("/")


def warn(message: str) -> None:
    print(f"devflow: {message}", file=sys.stderr)
