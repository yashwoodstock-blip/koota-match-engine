"""Database session and connection management."""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment or default to local async SQLite
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./koota.db"

# If URL is standard postgresql:// convert to postgresql+asyncpg:// for async SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Async engine
engine_kwargs = {"echo": False, "future": True}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize tables in database."""
    from app.models import Base
    from app.db.migrate_profile_updates import run_profile_update_migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_profile_update_migrations()
