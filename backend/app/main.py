from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import init_db
from app.routers import auth, dashboard, devices, events, insights, projects


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
app.include_router(dashboard.router, prefix=api)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "ai": "enabled" if settings.ai_enabled else "fallback"}
