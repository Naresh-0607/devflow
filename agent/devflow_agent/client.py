import json
import urllib.error
import urllib.request

from devflow_agent.config import endpoint_of


class AgentError(RuntimeError):
    pass


def _request(config: dict, method: str, path: str, body: dict | None = None) -> dict:
    url = f"{endpoint_of(config)}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": config.get("api_key", ""),
            "User-Agent": "devflow-agent/0.1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AgentError(f"HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AgentError(f"cannot reach DevFlow at {url}: {exc}") from exc


def send_event(config: dict, event: dict) -> dict:
    return _request(config, "POST", "/api/v1/events", event)


def ping(config: dict) -> dict:
    return _request(config, "GET", "/api/v1/devices/me")
