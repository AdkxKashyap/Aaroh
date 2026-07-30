"""
Application Entry Point

Responsibility:
    Creates the FastAPI application.

Why this file exists:
    This is the starting point of our backend application.
    Every incoming HTTP request enters through this application.

Current Scope:
    Only creates the application and exposes a health endpoint.
"""

from fastapi import FastAPI

app = FastAPI(
    title="School Operations Agent",
    version="1.0.0",
)


@app.get("/")
def root():
    """
    Root endpoint used to verify that the application is running.
    """
    return {
        "message": "Aaroh Agent Backend is running."
    }