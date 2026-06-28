"""Structured JSON logging via structlog."""

from __future__ import annotations

import logging
import sys
from typing import TextIO

import structlog

from config import get_settings


def configure_logging(stream: TextIO | None = None) -> None:
    # `stream` lets callers force logs onto a specific channel. The MCP stdio server
    # passes stderr, because stdout there is the JSON-RPC protocol channel and must
    # stay clean. Default (None) keeps the prior behavior for the HTTP service.
    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=level, stream=stream)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=stream or sys.stdout),
        cache_logger_on_first_use=True,
    )
