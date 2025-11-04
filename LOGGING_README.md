# Raster2Sensor Logging System

The `raster2sensor.logging` module provides a comprehensive logging solution designed specifically for geospatial processing applications. It offers structured logging with support for both console and file output, with optional rich formatting for enhanced readability.

## Features

- **Centralized Configuration**: Single point to configure all logging settings
- **Rich Console Output**: Beautiful console logging with syntax highlighting (when `rich` is available)
- **File Logging**: Automatic log rotation and organized file output
- **Structured Logging**: Specialized logging methods for different operation types
- **Singleton Pattern**: Ensures consistent logging configuration across modules
- **Type Safety**: Full type annotations for better IDE support

## Quick Start

### Basic Setup

```python
from raster2sensor.logging import configure_logging, get_logger

# Configure logging
configure_logging(
    level="INFO",
    log_dir="./logs",
    enable_file_logging=True,
    enable_console_logging=True,
    use_rich=True  # Enhanced console output
)

# Get a logger for your module
logger = get_logger(__name__)
logger.info("Hello from raster2sensor!")
```

### Specialized Logging Methods

#### Processing Operations

```python
from raster2sensor.logging import log_processing_start, log_processing_complete
import time

# Log start of processing
start_time = time.time()
log_processing_start(
    "Zonal Statistics",
    input_raster="VARI.tif",
    input_vector="parcels.geojson"
)

# ... do processing ...

# Log completion with timing
duration = time.time() - start_time
log_processing_complete(
    "Zonal Statistics",
    duration=duration,
    output_features=150
)
```

#### Spatial Operations

```python
from raster2sensor.logging import log_spatial_operation

log_spatial_operation(
    "Raster Clipping",
    input_data="VARI.tif (3000x2000 pixels)",
    output_data="VARI_clipped.tif (1500x1000 pixels)",
    clip_extent="EPSG:4326"
)
```

#### API Requests

```python
from raster2sensor.logging import log_api_request

log_api_request(
    "POST",
    "https://api.sensorthings.org/v1.0/Observations",
    status_code=201,
    response_time=0.342
)
```

#### Error Handling

```python
from raster2sensor.logging import log_error

try:
    # Some operation that might fail
    process_raster("missing_file.tif")
except FileNotFoundError as e:
    log_error(
        e,
        context="Loading input raster",
        expected_path="./gis_data/missing_file.tif"
    )
```

## Configuration Options

### `configure_logging()` Parameters

| Parameter                | Type        | Default    | Description                                           |
| ------------------------ | ----------- | ---------- | ----------------------------------------------------- |
| `level`                  | `str\|int`  | `INFO`     | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `log_dir`                | `str\|Path` | `"./logs"` | Directory for log files                               |
| `log_filename`           | `str`       | `None`     | Custom log filename (auto-generated if None)          |
| `enable_file_logging`    | `bool`      | `True`     | Enable file output                                    |
| `enable_console_logging` | `bool`      | `True`     | Enable console output                                 |
| `use_rich`               | `bool`      | `True`     | Use rich formatting for console                       |
| `max_file_size`          | `int`       | `10MB`     | Maximum log file size before rotation                 |
| `backup_count`           | `int`       | `5`        | Number of backup files to keep                        |
| `format_string`          | `str`       | `None`     | Custom format string for file logs                    |

### Example Advanced Configuration

```python
from raster2sensor.logging import configure_logging

configure_logging(
    level="DEBUG",
    log_dir="./my_logs",
    log_filename="custom_raster2sensor.log",
    enable_file_logging=True,
    enable_console_logging=True,
    use_rich=True,
    max_file_size=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    format_string="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
```

## Integration with Existing Code

### Backward Compatibility

The logging module provides a default `LOGGER` instance for backward compatibility:

```python
from raster2sensor.logging import LOGGER

LOGGER.info("This works with existing code!")
```

### Migration from Standard Logging

Replace existing logging code:

```python
# Old way
import logging
LOGGER = logging.getLogger(__name__)

# New way
from raster2sensor.logging import get_logger
LOGGER = get_logger(__name__)
```

## Log File Management

### Automatic Cleanup

```python
from raster2sensor.logging import cleanup_old_logs

# Remove log files older than 30 days
cleanup_old_logs(max_age_days=30)
```

### List Log Files

```python
from raster2sensor.logging import logger_instance

log_files = logger_instance.get_log_files()
for log_file in log_files:
    print(f"Log file: {log_file}")
```

## Best Practices

1. **Configure Early**: Call `configure_logging()` at the start of your application
2. **Use Module Loggers**: Always use `get_logger(__name__)` for module-specific loggers
3. **Structured Context**: Include relevant context in your log messages using kwargs
4. **Appropriate Levels**: Use appropriate log levels (DEBUG for development, INFO for normal operation)
5. **Error Context**: Always include context when logging errors

## Example Usage

See `example_logging.py` for a complete demonstration of all features.

## Dependencies

- **Required**: Standard library only (`logging`, `pathlib`, `datetime`)
- **Optional**: `rich` (for enhanced console output)

If `rich` is not installed, the logger will gracefully fall back to standard console formatting.

## Thread Safety

The logging system is thread-safe and can be used safely in multi-threaded applications. The singleton pattern ensures consistent configuration across all threads.
