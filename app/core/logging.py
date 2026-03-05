"""
Structured logging for BSC Website Bot.
Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
"""
import logging
import sys


_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _configure_root_logger() -> None:
    """Configure the root logger once at startup."""
    if logging.root.handlers:
        return  # already configured

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)


_configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (uses the root configuration)."""
    return logging.getLogger(name)
