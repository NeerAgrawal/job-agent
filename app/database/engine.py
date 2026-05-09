"""Database engine setup."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# Create async engine with SQLite async driver
database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
engine = create_async_engine(
    database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=False,
)

# Metadata for migrations
metadata = MetaData()
