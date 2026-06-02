"""
logger.py — Tiny wrapper around the stdlib logging module so the rest of the
codebase imports a configured logger without having to set handlers itself.
"""

from __future__ import annotations
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a clean console formatter. Idempotent."""
    root = logging.getLogger()
    if root.handlers:
        # Already configured by an earlier call; just set the level.
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
