import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.datastructures import Headers, MutableHeaders

from app import __version__
from app.config import settings
from app.database import init_db
from app.routers import auth, chat, dashboard, devices, events, insights, projects

logger = logging.getLogger("devflow.requests")


class SelectiveGZipMiddleware(GZipMiddleware):
    """Compress JSON responses but never buffer an SSE stream."""

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if "text/event-stream" in headers.get("accept", ""):
                return await self.app(scope, receive, send)
            if scope.get("path", "").endswith("/chat"):
                return await self.app(scope, receive, send)
        return await super().__call__(scope, receive, send)


class TimingMiddleware:
    """Pure-ASGI timing: no extra task per request, streaming stays intact."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        started = time.perf_counter()
        status = 500

        async def send_wrapper(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                elapsed_ms = (time.perf_counter() - started) * 1000
                headers = MutableHeaders(scope=message)
                headers.append("Server-Timing", f"app;dur={elapsed_ms:.1f}")
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                elapsed_ms = (time.perf_counter() - started) * 1000
                route = scope.get("route")
                path = getattr(route, "path", scope.get("path", ""))
                logger.info(
                    "%s %s -> %s %.1fms",
                    scope.get("method", ""),
                    path,
                    status,
                    elapsed_ms,
                )

        await self.app(scope, receive, send_wrapper)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="AI-powered developer memory: Git activity in, development memory out.",
    lifespan=lifespan,
)

app.add_middleware(SelectiveGZipMiddleware, minimum_size=500)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = settings.api_v1_prefix
app.include_router(auth.router, prefix=api)
app.include_router(devices.router, prefix=api)
app.include_router(events.router, prefix=api)
app.include_router(projects.router, prefix=api)
app.include_router(insights.router, prefix=api)
app.include_router(chat.router, prefix=api)
app.include_router(dashboard.router, prefix=api)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "ai": "enabled" if settings.ai_enabled else "fallback"}
