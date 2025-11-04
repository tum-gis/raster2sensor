"""
Logging configuration and utilities for raster2sensor.

This module provides a centralized logging configuration with support for:
- Console and file logging
- Rich formatting for enhanced console output
- Configurable log levels
- Structured logging for geospatial processing tasks
"""

import logging
import logging.handlers
import sys
import inspect
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

try:
    from rich import print as rich_print
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.traceback import install
    RICH_AVAILABLE = True
except ImportError:
    rich_print = None
    Console = None
    RichHandler = None
    install = None
    RICH_AVAILABLE = False

# Ensure we always have print available
print = print  # Built-in print function


class Raster2SensorLogger:
    """
    A comprehensive logging class for the raster2sensor package.

    Provides centralized logging configuration with support for both
    console and file logging, with optional rich formatting.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger if not already initialized."""
        if not self._initialized:
            # Initialize console with safer settings for Windows
            if RICH_AVAILABLE and Console:
                try:
                    # Try to create console with safer width/height settings
                    self.console = Console(
                        # Limit width to prevent buffer issues
                        width=min(120, 80),
                        height=min(50, 30),  # Limit height
                        force_terminal=False,  # Let Rich detect terminal capabilities
                        legacy_windows=True   # Better Windows compatibility
                    )
                except Exception:
                    # Fallback to None if Rich console creation fails
                    self.console = None
            else:
                self.console = None

            self._loggers = {}
            self._log_dir = None
            self._setup_rich_traceback()
            Raster2SensorLogger._initialized = True

    def _setup_rich_traceback(self):
        """Setup rich traceback handling if available."""
        if RICH_AVAILABLE and install and self.console:
            install(show_locals=True, console=self.console)

    def configure_logging(
        self,
        level: Union[str, int] = logging.INFO,
        log_dir: Optional[Union[str, Path]] = None,
        log_filename: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        use_rich: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_string: Optional[str] = None,
        suppress_third_party_debug: bool = True
    ) -> None:
        """
        Configure the global logging settings.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (defaults to ./logs)
            log_filename: Log file name (defaults to raster2sensor_YYYY-MM-DD.log)
            enable_file_logging: Whether to enable file logging
            enable_console_logging: Whether to enable console logging
            use_rich: Whether to use rich formatting for console output
            max_file_size: Maximum size of log files before rotation
            backup_count: Number of backup files to keep
            format_string: Custom format string for file logging
            suppress_third_party_debug: Whether to suppress DEBUG logs from third-party libraries
        """
        # Convert string level to int if necessary
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        # Setup log directory
        if log_dir is None:
            log_dir = Path('./logs')
        else:
            log_dir = Path(log_dir)

        self._log_dir = log_dir

        if enable_file_logging:
            log_dir.mkdir(exist_ok=True)

        # Setup log filename
        if log_filename is None:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            log_filename = f'raster2sensor_{timestamp}.log'

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Setup formatters
        if format_string is None:
            format_string = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(funcName)s:%(lineno)d - %(message)s'
            )

        file_formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup file logging
        if enable_file_logging:
            log_file = log_dir / log_filename
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # Setup console logging
        if enable_console_logging:
            if use_rich and RICH_AVAILABLE and RichHandler and self.console:
                try:
                    console_handler = RichHandler(
                        console=self.console,
                        show_time=True,
                        show_path=True,
                        rich_tracebacks=True,
                        tracebacks_show_locals=True
                    )
                    console_handler.setLevel(level)
                    root_logger.addHandler(console_handler)
                except Exception:
                    # Fallback to standard console handler if Rich fails
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(level)
                    console_formatter = logging.Formatter(
                        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        datefmt='%H:%M:%S'
                    )
                    console_handler.setFormatter(console_formatter)
                    root_logger.addHandler(console_handler)
            else:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)

        # Suppress noisy third-party debug logs if requested
        if suppress_third_party_debug:
            # Convert level to int if it's a string for comparison
            level_int = level if isinstance(
                level, int) else getattr(logging, level.upper())

            if level_int <= logging.DEBUG:
                # List of third-party loggers that are typically too verbose at DEBUG level
                noisy_loggers = [
                    'urllib3.connectionpool',
                    'requests.packages.urllib3.connectionpool',
                    'urllib3',
                    'requests',
                    'matplotlib',
                    'PIL',
                    'fiona',
                    'rasterio',
                    'boto3',
                    'botocore',
                    's3transfer'
                ]

                for logger_name in noisy_loggers:
                    third_party_logger = logging.getLogger(logger_name)
                    # Suppress DEBUG messages
                    third_party_logger.setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for the given name.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def log_processing_start(self, process_name: str, **kwargs) -> None:
        """
        Log the start of a processing operation.

        Args:
            process_name: Name of the processing operation
            **kwargs: Additional context information
        """
        logger = self.get_logger('raster2sensor.processing')
        context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
        message = f"Starting {process_name}"
        if context:
            message += f" | {context}"
        logger.info(message)

    def log_processing_complete(self, process_name: str, duration: Optional[float] = None, **kwargs) -> None:
        """
        Log the completion of a processing operation.

        Args:
            process_name: Name of the processing operation
            duration: Processing duration in seconds
            **kwargs: Additional context information
        """
        logger = self.get_logger('raster2sensor.processing')
        context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
        message = f"Completed {process_name}"
        if duration is not None:
            message += f" | Duration: {duration:.2f}s"
        if context:
            message += f" | {context}"
        logger.info(message)

    def log_spatial_operation(self, operation: str, input_data: str, output_data: Optional[str] = None, **kwargs) -> None:
        """
        Log spatial data operations.

        Args:
            operation: Type of spatial operation
            input_data: Input data description
            output_data: Output data description
            **kwargs: Additional context information
        """
        logger = self.get_logger('raster2sensor.spatial')
        message = f"{operation} | Input: {input_data}"
        if output_data:
            message += f" | Output: {output_data}"

        context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
        if context:
            message += f" | {context}"

        logger.info(message)

    def log_api_request(self, method: str, url: str, status_code: Optional[int] = None, **kwargs) -> None:
        """
        Log API requests and responses.

        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            **kwargs: Additional context information
        """
        logger = self.get_logger('raster2sensor.api')
        message = f"{method.upper()} {url}"
        if status_code:
            message += f" | Status: {status_code}"

        context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
        if context:
            message += f" | {context}"

        if status_code and status_code >= 400:
            logger.error(message)
        else:
            logger.info(message)

    def log_error(self, error: Exception, context: Optional[str] = None, **kwargs) -> None:
        """
        Log errors with context information.

        Args:
            error: Exception that occurred
            context: Additional context description
            **kwargs: Additional context information
        """
        logger = self.get_logger('raster2sensor.error')
        message = f"{type(error).__name__}: {str(error)}"
        if context:
            message = f"{context} | {message}"

        extra_context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
        if extra_context:
            message += f" | {extra_context}"

        logger.error(message, exc_info=True)

    def set_level(self, level: Union[str, int]) -> None:
        """
        Set the logging level for all handlers.

        Args:
            level: New logging level
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers:
            handler.setLevel(level)

    def get_log_files(self) -> list:
        """
        Get list of current log files.

        Returns:
            List of log file paths
        """
        if self._log_dir and self._log_dir.exists():
            return list(self._log_dir.glob('*.log*'))
        return []

    def cleanup_old_logs(self, max_age_days: int = 30) -> None:
        """
        Clean up old log files.

        Args:
            max_age_days: Maximum age of log files to keep
        """
        if not self._log_dir or not self._log_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for log_file in self._log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.get_logger('raster2sensor.maintenance').info(
                        f"Removed old log file: {log_file.name}"
                    )
                except OSError as e:
                    self.get_logger('raster2sensor.maintenance').error(
                        f"Failed to remove log file {log_file.name}: {e}"
                    )


# Global logger instance
logger_instance = Raster2SensorLogger()

# Convenience functions


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to calling module name)

    Returns:
        Logger instance
    """
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'raster2sensor')
        else:
            name = 'raster2sensor'

    # Ensure name is not None at this point
    assert name is not None, "Logger name should not be None"
    return logger_instance.get_logger(name)


def configure_logging(**kwargs) -> None:
    """Configure global logging settings."""
    logger_instance.configure_logging(**kwargs)


def log_processing_start(process_name: str, **kwargs) -> None:
    """Log the start of a processing operation."""
    logger_instance.log_processing_start(process_name, **kwargs)


def log_processing_complete(process_name: str, duration: Optional[float] = None, **kwargs) -> None:
    """Log the completion of a processing operation."""
    logger_instance.log_processing_complete(process_name, duration, **kwargs)


def log_spatial_operation(operation: str, input_data: str, output_data: Optional[str] = None, **kwargs) -> None:
    """Log spatial data operations."""
    logger_instance.log_spatial_operation(
        operation, input_data, output_data, **kwargs)


def log_api_request(method: str, url: str, status_code: Optional[int] = None, **kwargs) -> None:
    """Log API requests and responses."""
    logger_instance.log_api_request(method, url, status_code, **kwargs)


def log_error(error: Exception, context: Optional[str] = None, **kwargs) -> None:
    """Log errors with context information."""
    logger_instance.log_error(error, context, **kwargs)


def set_log_level(level: Union[str, int]) -> None:
    """Set the logging level."""
    logger_instance.set_level(level)


def cleanup_old_logs(max_age_days: int = 30) -> None:
    """Clean up old log files."""
    logger_instance.cleanup_old_logs(max_age_days)


def log_and_print(message: str, level: str = 'info', rich_format: Optional[str] = None, logger_instance: Optional[logging.Logger] = None, **kwargs):
    """
    Log a message and optionally print it with rich formatting.

    Args:
        message: Clean message for logging
        level: Log level (info, warning, error, debug, critical)
        rich_format: Rich-formatted version for console output
        logger_instance: Logger to use (default: get package logger)
        **kwargs: Additional context for logging

    Raises:
        ValueError: If level is not a valid log level
    """
    # Validate log level
    valid_levels = {'debug', 'info', 'warning', 'error', 'critical'}
    level_lower = level.lower()
    if level_lower not in valid_levels:
        raise ValueError(
            f"Invalid log level '{level}'. Must be one of: {', '.join(sorted(valid_levels))}")

    if logger_instance is None:
        logger_instance = get_logger('raster2sensor')

    # Create a LogRecord manually to set the correct caller information
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_frame = frame.f_back
        caller_filename = caller_frame.f_code.co_filename
        caller_function = caller_frame.f_code.co_name
        caller_lineno = caller_frame.f_lineno

        # Create the message with context
        if kwargs:
            context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
            full_message = f"{message} | {context}"
        else:
            full_message = message

        # Create a custom LogRecord with caller information
        record = logger_instance.makeRecord(
            logger_instance.name,
            getattr(logging, level_lower.upper()),
            caller_filename,
            caller_lineno,
            full_message,
            args=(),
            exc_info=None,
            func=caller_function
        )
        logger_instance.handle(record)
    else:
        # Fallback to normal logging if frame inspection fails
        log_func = getattr(logger_instance, level_lower)
        if kwargs:
            context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
            log_func(f"{message} | {context}")
        else:
            log_func(message)

    # Print rich-formatted version if provided
    if rich_format:
        try:
            if RICH_AVAILABLE and rich_print:
                rich_print(rich_format)
            else:
                print(rich_format)
        except Exception:
            # Fallback to plain text if Rich printing fails
            print(message)
    else:
        # Use simple print without Rich markup to avoid console buffer issues
        try:
            # Simple console output without rich formatting for non-rich environments
            if RICH_AVAILABLE and rich_print:
                level_colors = {
                    'debug': 'dim',
                    'info': 'cyan',
                    'warning': 'yellow',
                    'error': 'red',
                    'critical': 'bold red'
                }
                color = level_colors.get(level_lower, 'white')
                rich_print(f'[{color}]{message}[/{color}]')
            else:
                # Plain print for non-rich environments
                print(f'{level_lower.upper()}: {message}')
        except Exception:
            # Ultimate fallback to plain print
            print(message)


def log_and_raise(
    message: str,
    exception_type: type = ValueError,
    logger_instance: Optional[logging.Logger] = None,
    **kwargs
) -> None:
    """
    Log an error message and raise an exception.

    This utility function standardizes the common pattern of logging an error
    and then raising an exception with the same or related message.

    Args:
        message: Error message to log and use in exception
        exception_type: Type of exception to raise (default: ValueError)
        logger_instance: Logger to use (default: get package logger)
        **kwargs: Additional context for logging

    Raises:
        exception_type: The specified exception type with the message

    Example:
        log_and_raise("Invalid input data", ValueError, param="value")
        # Logs: "Invalid input data | param=value"
        # Raises: ValueError("Invalid input data")
    """
    if logger_instance is None:
        logger_instance = get_logger('raster2sensor')

    # Create a LogRecord manually to set the correct caller information
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_frame = frame.f_back
        caller_filename = caller_frame.f_code.co_filename
        caller_function = caller_frame.f_code.co_name
        caller_lineno = caller_frame.f_lineno

        # Create the message with context
        if kwargs:
            context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
            full_message = f"{message} | {context}"
        else:
            full_message = message

        # Create a custom LogRecord with caller information
        record = logger_instance.makeRecord(
            logger_instance.name,
            logging.ERROR,
            caller_filename,
            caller_lineno,
            full_message,
            args=(),
            exc_info=None,
            func=caller_function
        )
        logger_instance.handle(record)
    else:
        # Fallback to normal logging if frame inspection fails
        if kwargs:
            context = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
            logger_instance.error(f"{message} | {context}")
        else:
            logger_instance.error(message)

    # Raise the exception
    raise exception_type(message)


# Default logger for backward compatibility
LOGGER = get_logger('raster2sensor')
