from app.services.rate_limit import event_rate_limiter
from tests.conftest import auth_headers, register


async def test_register_login_and_me(client):
    data = await register(client)
    assert data["user"]["email"] == "dev@example.com"
    assert data["tokens"]["access_token"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "dev@example.com", "password": "supersecret"},
    )
    assert login.status_code == 200

    me = await client.get("/api/v1/auth/me", headers=auth_headers(login.json()["tokens"]))
    assert me.status_code == 200
    assert me.json()["email"] == "dev@example.com"


async def test_duplicate_registration_rejected(client):
    await register(client)
    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": "dev@example.com", "password": "supersecret"},
    )
    assert duplicate.status_code == 409


async def test_refresh_rotation(client):
    data = await register(client)
    refresh_token = data["tokens"]["refresh_token"]

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != refresh_token

    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code == 401

    logout = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]}
    )
    assert logout.status_code == 204


async def test_agent_event_ingestion_creates_project(client):
    data = await register(client)
    headers = auth_headers(data["tokens"])

    device = await client.post(
        "/api/v1/devices", json={"name": "Workstation"}, headers=headers
    )
    assert device.status_code == 201
    api_key = device.json()["api_key"]
    assert api_key.startswith("dvf_live_")

    event = {
        "event_type": "commit",
        "repository": {
            "name": "jarvis",
            "local_identifier": "/home/dev/jarvis",
            "remote_url": "https://github.com/dev/jarvis",
        },
        "payload": {"message": "add websocket routing", "branch": "voice-v2"},
    }
    first = await client.post("/api/v1/events", json=event, headers={"X-API-Key": api_key})
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["created_project"] is True
    assert body["created_repository"] is True

    # Second event for the same repo reuses project/repository.
    second_event = {
        **event,
        "event_type": "push",
        "payload": {"branch": "voice-v2"},
    }
    second = await client.post(
        "/api/v1/events", json=second_event, headers={"X-API-Key": api_key}
    )
    assert second.status_code == 201
    assert second.json()["project_id"] == body["project_id"]
    assert second.json()["created_project"] is False

    projects = await client.get("/api/v1/projects", headers=headers)
    assert projects.status_code == 200
    assert len(projects.json()) == 1
    project = projects.json()[0]
    assert project["name"] == "jarvis"
    assert project["event_count"] == 2

    detail = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["recent_events"]) == 2
    assert detail.json()["repositories"][0]["remote_url"] == event["repository"]["remote_url"]


async def test_invalid_api_key_rejected(client):
    response = await client.post(
        "/api/v1/events",
        json={
            "event_type": "commit",
            "repository": {"name": "x", "local_identifier": "/x"},
            "payload": {},
        },
        headers={"X-API-Key": "not-a-real-key"},
    )
    assert response.status_code == 401


async def test_summary_and_dashboard(client):
    data = await register(client)
    headers = auth_headers(data["tokens"])
    device = await client.post("/api/v1/devices", json={"name": "Laptop"}, headers=headers)
    api_key = device.json()["api_key"]

    await client.post(
        "/api/v1/events",
        json={
            "event_type": "commit",
            "repository": {"name": "devflow", "local_identifier": "/dev/devflow"},
            "payload": {"message": "build the memory timeline", "branch": "main"},
        },
        headers={"X-API-Key": api_key},
    )
    projects = (await client.get("/api/v1/projects", headers=headers)).json()
    project_id = projects[0]["id"]

    summary = await client.post(
        f"/api/v1/projects/{project_id}/summaries",
        json={"summary_type": "PROJECT"},
        headers=headers,
    )
    assert summary.status_code == 201, summary.text
    assert "devflow" in summary.json()["summary"].lower()

    dashboard = await client.get("/api/v1/dashboard", headers=headers)
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["total_projects"] == 1
    assert payload["total_events"] == 1
    assert payload["latest_summary"] is not None
    assert payload["last_active_project"]["id"] == project_id

    insights = await client.get("/api/v1/insights", headers=headers)
    assert insights.status_code == 200
    assert len(insights.json()["summaries"]) == 1


async def test_projects_are_isolated_between_users(client):
    first = await register(client, email="one@example.com")
    second = await register(client, email="two@example.com")

    device = await client.post(
        "/api/v1/devices",
        json={"name": "Laptop"},
        headers=auth_headers(first["tokens"]),
    )
    api_key = device.json()["api_key"]
    created = await client.post(
        "/api/v1/events",
        json={
            "event_type": "commit",
            "repository": {"name": "secret", "local_identifier": "/secret"},
            "payload": {"message": "private work"},
        },
        headers={"X-API-Key": api_key},
    )
    assert created.status_code == 201

    other = await client.get("/api/v1/projects", headers=auth_headers(second["tokens"]))
    assert other.json() == []

    project_id = created.json()["project_id"]
    peek = await client.get(
        f"/api/v1/projects/{project_id}", headers=auth_headers(second["tokens"])
    )
    assert peek.status_code == 404


async def test_event_ingestion_is_rate_limited_per_api_key(client):
    data = await register(client)
    headers = auth_headers(data["tokens"])
    device = await client.post("/api/v1/devices", json={"name": "Laptop"}, headers=headers)
    api_key = device.json()["api_key"]

    event = {
        "event_type": "commit",
        "repository": {"name": "burst", "local_identifier": "/burst"},
        "payload": {"message": "first"},
    }

    original_limit = event_rate_limiter.limit
    event_rate_limiter.limit = 1
    event_rate_limiter.reset()
    try:
        first = await client.post("/api/v1/events", json=event, headers={"X-API-Key": api_key})
        assert first.status_code == 201

        second = await client.post(
            "/api/v1/events",
            json={**event, "payload": {"message": "second"}},
            headers={"X-API-Key": api_key},
        )
        assert second.status_code == 429
        assert second.headers["Retry-After"]
    finally:
        event_rate_limiter.limit = original_limit
        event_rate_limiter.reset()


async def test_device_revocation(client):
    data = await register(client)
    headers = auth_headers(data["tokens"])
    device = await client.post("/api/v1/devices", json={"name": "Old laptop"}, headers=headers)
    device_id = device.json()["id"]
    api_key = device.json()["api_key"]

    revoked = await client.delete(f"/api/v1/devices/{device_id}", headers=headers)
    assert revoked.status_code == 204

    rejected = await client.post(
        "/api/v1/events",
        json={
            "event_type": "commit",
            "repository": {"name": "x", "local_identifier": "/x"},
            "payload": {},
        },
        headers={"X-API-Key": api_key},
    )
    assert rejected.status_code == 401
