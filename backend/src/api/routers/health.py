"""
Health APIs

Responsibility:
    Health endpoints for the application.
"""

from fastapi import APIRouter
from sqlalchemy import text

from src.db.database import engine

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/db")
async def database_health():
    """
    Verify database connectivity.
    """

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return {"status": "Database Connected"}