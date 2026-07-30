"""
Application Entry Point

Responsibility:
    Creates and configures the FastAPI application.
"""

from fastapi import FastAPI

from src.api.routers import health
from src.config.settings import get_settings
from src.core.logger import configure_logging
from src.middleware.logging import LoggingMiddleware
from sqlalchemy import text
from src.db.database import engine
from src.api.routers.auth import router as auth_router


configure_logging()

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(LoggingMiddleware)
app.include_router(health.router)
app.include_router(auth_router)

@app.get("/")
def root():
    """
    Root endpoint to verify the application is running.
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
