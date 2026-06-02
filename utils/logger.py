"""
logger.py — Centralized logging setup.
"""

from __future__ import annotations
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
"""Configure root logger with a clean console formatter. Idempotent."""
root = logging.getLogger()
if root.handlers:
    # Already configured (e.g. on reload); just adjust level.
    root.setLevel(level)
    return

root.setLevel(level)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level)
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
handler.setFormatter(formatter)
root.addHandler(handler)

# Quiet noisy third-party loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
