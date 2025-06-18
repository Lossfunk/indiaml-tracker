"""
Example demonstrating how to use the logging system in the indiaml project.
"""

from indiaml.config.logging_config import get_logger

# Method 1: Get logger with module name (recommended)
logger = get_logger(__name__)

# Method 2: Get logger with custom name
custom_logger = get_logger("indiaml.custom")

# Method 3: Get logger without specifying name (uses calling module's name)
auto_logger = get_logger()


def example_function():
    """Example function demonstrating different log levels."""
    logger.debug("This is a debug message - useful for detailed diagnostics")
    logger.info("This is an info message - general information about program execution")
    logger.warning("This is a warning message - something unexpected happened but the program continues")
    logger.error("This is an error message - a serious problem occurred")
    
    try:
        # Simulate an error
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.exception("Exception occurred with full traceback")
        logger.error(f"Error without traceback: {e}")


def pipeline_example():
    """Example of logging in a pipeline context."""
    pipeline_logger = get_logger("indiaml.pipeline.example")
    
    pipeline_logger.info("Starting data processing pipeline")
    pipeline_logger.info("Processing 1000 records")
    pipeline_logger.warning("Found 5 records with missing data")
    pipeline_logger.info("Pipeline completed successfully")


def analytics_example():
    """Example of logging in analytics context."""
    analytics_logger = get_logger("indiaml.analytics.example")
    
    analytics_logger.info("Starting analytics computation")
    analytics_logger.debug("Loading configuration parameters")
    analytics_logger.info("Computed statistics for 500 papers")
    analytics_logger.info("Analytics completed")


if __name__ == "__main__":
    print("Running logging examples...")
    print("Check the console output for colored logs and 'indiaml.log' file for file logs")
    print("-" * 60)
    
    example_function()
    print("-" * 60)
    
    pipeline_example()
    print("-" * 60)
    
    analytics_example()
    print("-" * 60)
    
    print("Logging examples completed!")
