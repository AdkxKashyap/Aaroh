"""
Database Configuration

Responsibility:
    Creates the SQLAlchemy engine.

Used By:
    Entire application.
"""

from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import get_settings

settings = get_settings()
"""
FastAPI is asynchronous. An async engine allows database operations to be awaited instead of blocking the server
"""
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)
