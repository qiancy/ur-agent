"""
Logging configuration for Uni-Resource Agent.

All logs are written to the output/ directory with daily rotation.
"""
import logging
import os
import sys
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

def setup_logging(name: str = "unires", level: int = logging.INFO) -> logging.Logger:
    """Configure logging with console and file handlers."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler (daily log file)
    log_file = os.path.join(OUTPUT_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_{name}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


def get_logger(module: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return logging.getLogger(f"unires.{module}")
