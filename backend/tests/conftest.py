import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_devflow.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GROQ_API_KEY", "")

import httpx
import pytest_asyncio

from app.database import Base, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def register(client, email="dev@example.com", password="supersecret"):
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
