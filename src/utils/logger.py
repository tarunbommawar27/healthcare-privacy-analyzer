"""Logging configuration for the application"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_file: str = "logs/analyzer.log", level: str = "INFO"):
    """
    Configure application logger with file and console output

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Remove default logger
    logger.remove()

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Add console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level
    )

    # Add file handler with rotation
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level
    )

    return logger


def get_logger():
    """Get the configured logger instance"""
    return logger
