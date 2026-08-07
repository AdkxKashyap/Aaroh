"""
Application Entry Point

Responsibility:
    Creates and configures the FastAPI application.
"""

from fastapi import FastAPI

from src.api.routers.auth import router as auth_router
from src.api.routers.health import router as health_router
from src.api.routers.user import router as user_router
from src.config.settings import get_settings
from src.core.logger import configure_logging
from src.middleware.logging import LoggingMiddleware

configure_logging()

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(LoggingMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)


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
