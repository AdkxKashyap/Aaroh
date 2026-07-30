"""
Application Entry Point

Responsibility:
    Creates and configures the FastAPI application.
"""

from fastapi import FastAPI

from src.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


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