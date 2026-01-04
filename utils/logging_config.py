import logging
import sys
from pathlib import Path
from typing import Dict, Any

import structlog


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup structured logging for the application"""

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logs directory if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Root logger configuration
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set specific logger levels
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


class ContextLogger:
    """Helper class for adding context to log messages"""

    def __init__(self, logger_name: str):
        self.logger = structlog.get_logger(logger_name)
        self._context: Dict[str, Any] = {}

    def bind(self, **kwargs) -> "ContextLogger":
        """Add context to the logger"""
        new_logger = ContextLogger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **{**self._context, **kwargs})

    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, **{**self._context, **kwargs})

    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **{**self._context, **kwargs})

    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, **{**self._context, **kwargs})

    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self.logger.critical(message, **{**self._context, **kwargs})


def get_logger(name: str) -> ContextLogger:
    """Get a context logger for the given name"""
    return ContextLogger(name)
