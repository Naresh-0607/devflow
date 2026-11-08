from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

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
    """Create tables for the MVP. Swap for Alembic migrations before public launch."""
    from app import models  # noqa: F401  (register metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
