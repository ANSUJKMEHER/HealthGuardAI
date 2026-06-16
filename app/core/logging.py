"""
HealthGuard AI — Structured Logging Configuration
Replaces all print() with structured JSON logging via structlog.
"""

import structlog
import logging
import sys

from app.config import settings


def setup_logging():
    """
    Configure structured logging for the entire application.

    In production: JSON output for log aggregation (Loki, CloudWatch, etc.)
    In development: Colored, human-readable console output.
    """

    # Choose processors based on environment
    if settings.is_production:
        # JSON output for production — parseable by log aggregation tools
        renderer = structlog.processors.JSONRenderer()
    else:
        # Pretty colored output for local development
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=35,
        )

    structlog.configure(
        processors=[
            # Add context
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # Stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Final rendering
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging to go through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    logger = structlog.get_logger()
    logger.info("logging_configured",
                mode="production" if settings.is_production else "development")
