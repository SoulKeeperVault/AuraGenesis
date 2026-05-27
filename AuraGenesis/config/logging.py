"""Structured logging configuration for AuraGenesis.

Provides consistent, observable logging across all consciousness modules.
"""
import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the entire Aura system."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from heavy libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for any module."""
    return logging.getLogger(f"aura.{name}")
