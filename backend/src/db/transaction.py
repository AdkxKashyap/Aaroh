from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

_TRANSACTION_DEPTH_KEY = "service_transaction_depth"

"""
Transactional context manager for SQLAlchemy AsyncSession.

Usage:
    async with transactional(session):
        # perform database operations
"""


@asynccontextmanager
async def transactional(session: AsyncSession) -> AsyncIterator[None]:
    depth = session.info.get(_TRANSACTION_DEPTH_KEY, 0)

    if depth > 0:
        session.info[_TRANSACTION_DEPTH_KEY] = depth + 1
        try:
            yield
        finally:
            session.info[_TRANSACTION_DEPTH_KEY] -= 1
            if session.info[_TRANSACTION_DEPTH_KEY] == 0:
                session.info.pop(_TRANSACTION_DEPTH_KEY, None)
        return

    session.info[_TRANSACTION_DEPTH_KEY] = 1

    try:
        yield
        await session.commit()
    except Exception:
        if session.in_transaction():
            await session.rollback()
        raise
    finally:
        session.info.pop(_TRANSACTION_DEPTH_KEY, None)
