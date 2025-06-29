"""
Comprehensive logging configuration with colorlog support for IndiaML project.

This module provides elaborate logging capabilities with:
- Colored console output using colorlog
- File logging with rotation
- Performance monitoring
- Context-aware logging
- Multiple log levels and formatters
"""

import logging
import logging.handlers
import os
import sys
import time
import functools
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
import colorlog


class PerformanceLogger:
    """Logger for performance monitoring and timing operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.timers[operation] = time.time()
        self.logger.debug(f"⏱️  Started timing operation: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and log the duration."""
        if operation not in self.timers:
            self.logger.warning(f"⚠️  Timer for operation '{operation}' was not started")
            return 0.0
        
        duration = time.time() - self.timers[operation]
        del self.timers[operation]
        
        if duration < 0.1:
            self.logger.debug(f"⚡ Operation '{operation}' completed in {duration:.3f}s")
        elif duration < 1.0:
            self.logger.info(f"🚀 Operation '{operation}' completed in {duration:.3f}s")
        elif duration < 10.0:
            self.logger.info(f"⏰ Operation '{operation}' completed in {duration:.2f}s")
        else:
            self.logger.warning(f"🐌 Slow operation '{operation}' completed in {duration:.2f}s")
        
        return duration
    
    def time_operation(self, operation: str):
        """Decorator to time function execution."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.start_timer(operation)
                try:
                    result = func(*args, **kwargs)
                    self.end_timer(operation)
                    return result
                except Exception as e:
                    self.end_timer(operation)
                    self.logger.error(f"❌ Operation '{operation}' failed: {e}")
                    raise
            return wrapper
        return decorator


class ContextLogger:
    """Logger that maintains context information across operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs) -> None:
        """Set context variables for logging."""
        self.context.update(kwargs)
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.debug(f"🔧 Context updated: {context_str}")
    
    def clear_context(self) -> None:
        """Clear all context variables."""
        self.context.clear()
        self.logger.debug("🧹 Context cleared")
    
    def log_with_context(self, level: int, message: str, **extra_context) -> None:
        """Log a message with current context."""
        full_context = {**self.context, **extra_context}
        if full_context:
            context_str = " | ".join(f"{k}={v}" for k, v in full_context.items())
            message = f"[{context_str}] {message}"
        self.logger.log(level, message)
    
    def debug(self, message: str, **context) -> None:
        self.log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context) -> None:
        self.log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context) -> None:
        self.log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context) -> None:
        self.log_with_context(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context) -> None:
        self.log_with_context(logging.CRITICAL, message, **context)


class ElaborateLogger:
    """Main logger class with comprehensive logging capabilities."""
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create main logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handlers()
        
        # Create specialized loggers
        self.performance = PerformanceLogger(self.logger)
        self.context = ContextLogger(self.logger)
        
        # Log initialization
        self.logger.info(f"🚀 Logger '{name}' initialized with elaborate logging")
        self.logger.info(f"📁 Log directory: {self.log_dir.absolute()}")
    
    def _setup_console_handler(self) -> None:
        """Setup colored console handler."""
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Elaborate color formatter
        color_formatter = colorlog.ColoredFormatter(
            fmt=(
                "%(log_color)s%(asctime)s %(levelname)-8s "
                "%(name)s:%(lineno)d %(reset)s%(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        
        console_handler.setFormatter(color_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handlers(self) -> None:
        """Setup file handlers with rotation."""
        # Main log file with rotation
        main_log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed file formatter
        file_formatter = logging.Formatter(
            fmt=(
                "%(asctime)s.%(msecs)03d [%(levelname)-8s] "
                "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error-only log file
        error_log_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # Performance log file
        perf_log_file = self.log_dir / f"{self.name}_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        
        # Performance-specific formatter
        perf_formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        perf_handler.setFormatter(perf_formatter)
        
        # Add filter to only log performance messages
        perf_handler.addFilter(lambda record: "⏱️" in record.getMessage() or 
                              "⚡" in record.getMessage() or 
                              "🚀" in record.getMessage() or 
                              "⏰" in record.getMessage() or 
                              "🐌" in record.getMessage())
        
        self.logger.addHandler(perf_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional context."""
        self._log_with_emoji(logging.DEBUG, "🔍", message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional context."""
        self._log_with_emoji(logging.INFO, "ℹ️", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional context."""
        self._log_with_emoji(logging.WARNING, "⚠️", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional context."""
        self._log_with_emoji(logging.ERROR, "❌", message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with optional context."""
        self._log_with_emoji(logging.CRITICAL, "🚨", message, **kwargs)
    
    def success(self, message: str, **kwargs) -> None:
        """Log success message."""
        self._log_with_emoji(logging.INFO, "✅", message, **kwargs)
    
    def progress(self, message: str, **kwargs) -> None:
        """Log progress message."""
        self._log_with_emoji(logging.INFO, "🔄", message, **kwargs)
    
    def start_operation(self, operation: str, **context) -> None:
        """Log the start of an operation."""
        self.context.set_context(**context)
        self._log_with_emoji(logging.INFO, "🚀", f"Starting operation: {operation}")
        self.performance.start_timer(operation)
    
    def end_operation(self, operation: str, success: bool = True) -> None:
        """Log the end of an operation."""
        duration = self.performance.end_timer(operation)
        emoji = "✅" if success else "❌"
        status = "completed successfully" if success else "failed"
        self._log_with_emoji(logging.INFO, emoji, f"Operation '{operation}' {status}")
        self.context.clear_context()
    
    def log_data_stats(self, data_name: str, count: int, **stats) -> None:
        """Log data statistics."""
        stats_str = ", ".join(f"{k}={v}" for k, v in stats.items())
        message = f"Data '{data_name}': {count} items"
        if stats_str:
            message += f" ({stats_str})"
        self._log_with_emoji(logging.INFO, "📊", message)
    
    def log_api_call(self, api_name: str, endpoint: str, status_code: int = None, 
                     duration: float = None) -> None:
        """Log API call information."""
        message = f"API call to {api_name}: {endpoint}"
        if status_code:
            message += f" (status: {status_code})"
        if duration:
            message += f" (duration: {duration:.3f}s)"
        
        emoji = "🌐"
        if status_code:
            if 200 <= status_code < 300:
                emoji = "✅"
            elif 400 <= status_code < 500:
                emoji = "⚠️"
            elif status_code >= 500:
                emoji = "❌"
        
        level = logging.INFO
        if status_code and status_code >= 400:
            level = logging.ERROR
        
        self._log_with_emoji(level, emoji, message)
    
    def log_file_operation(self, operation: str, file_path: str, 
                          size: int = None, success: bool = True) -> None:
        """Log file operation."""
        message = f"File {operation}: {file_path}"
        if size:
            message += f" ({size} bytes)"
        
        emoji = "📁" if success else "❌"
        level = logging.INFO if success else logging.ERROR
        self._log_with_emoji(level, emoji, message)
    
    def log_exception(self, exc: Exception, context: str = None) -> None:
        """Log exception with full traceback."""
        message = f"Exception occurred"
        if context:
            message += f" in {context}"
        message += f": {type(exc).__name__}: {exc}"
        
        self.logger.exception(f"❌ {message}")
    
    def _log_with_emoji(self, level: int, emoji: str, message: str, **kwargs) -> None:
        """Internal method to log with emoji and optional context."""
        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"[{context_str}] {message}"
        
        self.logger.log(level, f"{emoji} {message}")


# Global logger instances
_loggers: Dict[str, ElaborateLogger] = {}


def get_logger(name: str, log_dir: Optional[str] = None) -> ElaborateLogger:
    """Get or create a logger instance."""
    if name not in _loggers:
        _loggers[name] = ElaborateLogger(name, log_dir)
    return _loggers[name]


def setup_project_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Setup logging for the entire project."""
    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Create main project logger
    main_logger = get_logger("indiaml", log_dir)
    main_logger.info("🎯 Project logging initialized")
    main_logger.info(f"📊 Log level set to: {level}")
    main_logger.info(f"📁 Logs will be written to: {Path(log_dir).absolute()}")


# Decorators for easy logging
def log_function_calls(logger_name: str = None):
    """Decorator to log function entry and exit."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Log function entry
            args_str = ", ".join([str(arg)[:50] for arg in args[:3]])  # First 3 args, truncated
            kwargs_str = ", ".join([f"{k}={str(v)[:50]}" for k, v in list(kwargs.items())[:3]])
            params = ", ".join(filter(None, [args_str, kwargs_str]))
            if len(params) > 100:
                params = params[:100] + "..."
            
            logger.debug(f"Entering function: {func_name}({params})")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Function {func_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


def log_async_function_calls(logger_name: str = None):
    """Decorator to log async function entry and exit."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Log function entry
            args_str = ", ".join([str(arg)[:50] for arg in args[:3]])
            kwargs_str = ", ".join([f"{k}={str(v)[:50]}" for k, v in list(kwargs.items())[:3]])
            params = ", ".join(filter(None, [args_str, kwargs_str]))
            if len(params) > 100:
                params = params[:100] + "..."
            
            logger.debug(f"Entering async function: {func_name}({params})")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Async function {func_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Async function {func_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator
