

import logging
import logging.config
import os
from pathlib import Path


def init_logging():
    """Initialize logging configuration for the indiaml project."""
    # Find the logging.conf file relative to the project root
    current_dir = Path(__file__).parent.parent.parent  # Go up to indiaml/ directory
    config_path = current_dir / 'logging.conf'
    
    if not config_path.exists():
        # Fallback to basic logging if config file not found
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z'
        )
        logging.warning(f"Logging config file not found at {config_path}. Using basic configuration.")
        return
    
    try:
        # Configure logging from file
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
        logging.info("Logging configuration loaded successfully")
    except Exception as e:
        # Fallback to basic logging if config loading fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z'
        )
        logging.error(f"Failed to load logging configuration: {e}. Using basic configuration.")


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name. If None, uses the calling module's name.
        
    Returns:
        Logger instance
        
    Usage:
        # In any module:
        from indiaml.config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("This is an info message")
    """
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'indiaml')
    
    return logging.getLogger(name)


# Initialize logging when module is imported
init_logging()

# Default logger for this module
logger = get_logger(__name__)
