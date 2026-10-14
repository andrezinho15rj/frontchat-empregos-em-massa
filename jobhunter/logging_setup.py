"""Logging estruturado em arquivo rotativo + console."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from . import app_paths

_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    global _configured
    logger = logging.getLogger("jobhunter")
    if _configured:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        fh = RotatingFileHandler(
            app_paths.logs_dir() / "jobhunter.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:  # pragma: no cover - nunca deixar o log derrubar o app
        pass

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.propagate = False
    _configured = True
    return logger


def get_logger(name: str = "jobhunter") -> logging.Logger:
    if not name.startswith("jobhunter"):
        name = f"jobhunter.{name}"
    return logging.getLogger(name)
