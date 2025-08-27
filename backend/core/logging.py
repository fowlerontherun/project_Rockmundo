"""Minimal logging helpers for the backend.

These utilities provide a JSON based log formatter and convenience
functions to configure and retrieve loggers.  They are intentionally
light‑weight but fully functional so that other modules can rely on
``core.logging`` without pulling in heavy dependencies.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format log records as a JSON object."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger to emit structured JSON logs."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with *name*."""

    return logging.getLogger(name)


__all__ = ["JsonFormatter", "setup_logging", "get_logger"]
