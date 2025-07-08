"""
Logging configuration for the Offenheitscrawler.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week"
) -> logger:
    """
    Set up the logger configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        rotation: Log file rotation size
        retention: Log file retention period
    
    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    return logger


def get_logger(name: str) -> logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
