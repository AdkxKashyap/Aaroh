"""
Health APIs

Responsibility:
    Exposes health endpoints for monitoring.
"""

from fastapi import APIRouter
from sqlalchemy import text

from src.db.database import engine

router = APIRouter(
    tags=["Health"],
)


@router.get("/health")
async def health():
    """
    Basic application health check.
    """
    return {"status": "UP"}


@router.get("/live")
async def liveness():
    """
    Indicates the application process is alive.
    """
    return {"status": "ALIVE"}


@router.get("/ready")
async def readiness():
    """
    Verifies the application is ready to serve traffic.
    Checks database connectivity.
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        return {"status": "READY"}

    except Exception as ex:
        return {
            "status": "NOT_READY",
            "error": str(ex),
        }


@router.get("/health/db")
async def database_health():
    """
    Verifies database connectivity.
    """
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return {"status": "Database Connected"}
