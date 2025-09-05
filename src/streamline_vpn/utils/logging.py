"""
Logging Utilities
=================

Logging configuration and utilities for StreamlineVPN.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional, Dict, Any


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """Setup logging configuration for StreamlineVPN.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Custom format string
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": format_string,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "streamline_vpn": {
                "level": level,
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": level,
            "handlers": ["console"]
        }
    }
    
    # Add file handler if specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "detailed",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        config["loggers"]["streamline_vpn"]["handlers"].append("file")
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"streamline_vpn.{name}")


def log_performance(func_name: str, duration: float, **kwargs) -> None:
    """Log performance metrics.
    
    Args:
        func_name: Function name
        duration: Execution duration in seconds
        **kwargs: Additional metrics to log
    """
    logger = get_logger("performance")
    metrics = {
        "function": func_name,
        "duration": duration,
        **kwargs
    }
    logger.info(f"Performance: {metrics}")


def log_error(error: Exception, context: str = "", **kwargs) -> None:
    """Log error with context.
    
    Args:
        error: Exception instance
        context: Error context
        **kwargs: Additional context
    """
    logger = get_logger("error")
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        **kwargs
    }
    logger.error(f"Error occurred: {error_info}", exc_info=True)
