#!/usr/bin/env python3
"""
Example usage of the raster2sensor logging system.

This script demonstrates various logging features including:
- Basic logging setup
- Processing operation logging
- Spatial operation logging
- API request logging
- Error logging
"""

import time
from raster2sensor.logging import (
    configure_logging,
    get_logger,
    log_processing_start,
    log_processing_complete,
    log_spatial_operation,
    log_api_request,
    log_error
)


def example_processing_task():
    """Example of logging a processing task."""
    start_time = time.time()

    # Log start of processing
    log_processing_start(
        "Zonal Statistics Calculation",
        input_raster="VARI.tif",
        input_vector="parcels.geojson",
        processing_mode="mean"
    )

    # Simulate some processing
    logger = get_logger(__name__)
    logger.info("Processing raster data...")
    logger.debug("Loading raster bands...")
    logger.debug("Applying vector mask...")

    # Simulate processing time
    time.sleep(1)

    # Log completion
    duration = time.time() - start_time
    log_processing_complete(
        "Zonal Statistics Calculation",
        duration=duration,
        output_features=150,
        statistics_computed=["mean", "std", "min", "max"]
    )


def example_spatial_operations():
    """Example of logging spatial operations."""
    log_spatial_operation(
        "Raster Clipping",
        input_data="VARI.tif (3000x2000 pixels)",
        output_data="VARI_clipped.tif (1500x1000 pixels)",
        clip_extent="EPSG:4326",
        nodata_value=-9999
    )

    log_spatial_operation(
        "Vector Reprojection",
        input_data="parcels.geojson (EPSG:4326)",
        output_data="parcels_utm.geojson (EPSG:32633)",
        feature_count=150
    )


def example_api_logging():
    """Example of logging API requests."""
    # Successful API request
    log_api_request(
        "POST",
        "https://api.sensorthings.org/v1.0/Observations",
        status_code=201,
        response_time=0.342,
        data_points=150
    )

    # Failed API request
    log_api_request(
        "GET",
        "https://api.sensorthings.org/v1.0/Things/999",
        status_code=404,
        error="Thing not found"
    )


def example_error_logging():
    """Example of error logging."""
    try:
        # Simulate an error
        raise FileNotFoundError("VARI.tif not found in ./gis_data/")
    except FileNotFoundError as e:
        log_error(
            e,
            context="Loading input raster for zonal statistics",
            expected_path="./gis_data/VARI.tif",
            operation="file_io"
        )


def main():
    """Main function demonstrating logging usage."""
    print("🚀 Raster2Sensor Logging Example")
    print("=" * 40)

    # Configure logging with both console and file output
    configure_logging(
        level="DEBUG",
        log_dir="./logs",
        enable_file_logging=True,
        enable_console_logging=True,
        use_rich=True  # Use rich formatting if available
    )

    logger = get_logger(__name__)
    logger.info("Starting raster2sensor logging demonstration")

    print("\n📊 Processing Operations Example:")
    example_processing_task()

    print("\n🗺️  Spatial Operations Example:")
    example_spatial_operations()

    print("\n🌐 API Requests Example:")
    example_api_logging()

    print("\n❌ Error Logging Example:")
    example_error_logging()

    logger.info("Logging demonstration completed")
    print("\n✅ Check the ./logs/ directory for log files!")


if __name__ == "__main__":
    main()
