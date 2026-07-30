"""
Request Logging Middleware

Responsibility:
    Logs every incoming request and outgoing response.

Why:
    Provides request tracing and latency monitoring.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs request details."""

    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
