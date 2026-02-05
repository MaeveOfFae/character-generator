"""Logging configuration for Blueprint UI."""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    log_to_console: bool = True,
) -> None:
    """Set up logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_to_console: Whether to log to console
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotate log files at 10MB, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)