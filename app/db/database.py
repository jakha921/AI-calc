from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings


def _normalize_echo(value):
    """
    Normalize DEBUG/env value into SQLAlchemy echo flag.
    Supports bool and "true/false" strings. Other values disable echo to
    avoid KeyError on unexpected log-level strings.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on", "debug"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return False


echo_flag = _normalize_echo(settings.DEBUG)

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=echo_flag,
    future=True,
)

# Sync engine for migrations and scripts
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=echo_flag,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
