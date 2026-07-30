"""
Centralized Logging Configuration

Responsibility:
    Configures the application's logger.

Used By:
    Entire application.

Why:
    Ensures all logs have a consistent structure and format.
"""

import logging
import sys

import structlog


def configure_logging() -> None:
    """Configure application-wide structured logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


logger = structlog.get_logger()
