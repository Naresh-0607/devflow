import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url_async,
    echo=settings.sql_echo,
    pool_pre_ping=True,
    connect_args=settings.database_connect_args,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Prepare the schema for local development.

    Production uses Alembic exclusively (``alembic upgrade head`` runs before the
    API starts), so we never create tables implicitly there. SQLite development
    keeps the zero-setup ``create_all`` behaviour.
    """
    from app import models  # noqa: F401  (register metadata)

    if settings.environment == "production":
        logger.info("Production startup: schema is managed by Alembic migrations")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
