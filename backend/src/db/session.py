"""
Database Session

Responsibility:
    Provides database sessions for every request.

Why:
    Ensures every request gets its own database session.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from src.db.database import engine

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    """

    async with SessionLocal() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()
