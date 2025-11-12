"""
Image Processing Module for Raster2Sensor

This module handles the processing of raster images for vegetation indices calculation,
replicating and enhancing the functionality from the demo module.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from osgeo import gdal
from raster2sensor.utils import timeit
from raster2sensor.plots import Plots
from raster2sensor.ogcapiprocesses import OGCAPIProcesses
from raster2sensor.spatialtools import read_raster, clip_raster, encode_raster_to_base64
from raster2sensor.config_parser import Config, RasterImage, VegetationIndex
from raster2sensor.logging import get_logger


logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single raster image"""
    raster_path: str
    timestamp: str
    process_name: str
    success: bool
    error_message: Optional[str] = None


class ImageProcessor:
    """Main class for processing raster images with vegetation indices"""

    def __init__(self,
                 pygeoapi_url: str,
                 trial_id: str,
                 raster_images: List[RasterImage],
                 vegetation_indices: List[VegetationIndex],
                 sensorthingsapi_url: str):
        """
        Initialize the ImageProcessor with individual parameters

        Args:
            pygeoapi_url: URL for the PyGeoAPI service
            trial_id: Trial identifier to fetch plots for
            raster_images: List of raster images to process
            vegetation_indices: List of vegetation indices to calculate
            sensorthingsapi_url: SensorThings API URL
        """
        self.pygeoapi_url = pygeoapi_url
        self.trial_id = trial_id
        self.raster_images = raster_images
        self.vegetation_indices = vegetation_indices
        self.sensorthingsapi_url = sensorthingsapi_url

        if not self.pygeoapi_url:
            raise ValueError("pygeoapi_url must be provided")

        if not self.trial_id:
            raise ValueError("trial_id must be provided")

        self.ogc_api_processes = OGCAPIProcesses(self.pygeoapi_url)
        logger.info(
            f"Initialized ImageProcessor with PyGeoAPI URL: {self.pygeoapi_url}")
        logger.info(f"Trial ID: {self.trial_id}")
        logger.info(f"Images to process: {len(self.raster_images)}")
        logger.info(f"Vegetation indices: {len(self.vegetation_indices)}")

    @timeit
    def process_images(self) -> List[ProcessingResult]:
        """
        Process multiple raster images with multiple vegetation indices using stored parameters

        Returns:
            List of ProcessingResult objects
        """
        results = []
        # sensorthingsapi_url = self.sensorthingsapi_url
        # trial_id = self.trial_id
        # raster_images = self.raster_images
        # vegetation_indices = self.vegetation_indices

        # Load plots once for all processing
        logger.info(f"Fetching plots for trial: {self.trial_id}")
        try:
            plots_geojson = Plots.fetch_plots_geojson(
                self.sensorthingsapi_url, self.trial_id)
            plots_ds = gdal.OpenEx(json.dumps(plots_geojson))
            plots_layer = plots_ds.GetLayer()
        except Exception as e:
            logger.error(
                f"Failed to fetch plots for trial {self.trial_id}: {e}")
            raise

        # Process each raster image
        for raster_image in self.raster_images:
            logger.info(f"Processing raster image: {raster_image.path}")

            # Validate raster image exists
            if not Path(raster_image.path).exists():
                error_msg = f"Raster image path does not exist: {raster_image.path}"
                logger.error(error_msg)
                for vi in self.vegetation_indices:
                    results.append(ProcessingResult(
                        raster_path=raster_image.path,
                        timestamp=raster_image.timestamp,
                        process_name=vi.process,
                        success=False,
                        error_message=error_msg
                    ))
                continue

            # Load and clip raster
            try:
                raster_ds = read_raster(raster_image.path)
                clipped_raster_ds = clip_raster(raster_ds, plots_layer)
                encoded_raster_ds = encode_raster_to_base64(clipped_raster_ds)
                logger.debug(
                    f"Encoded raster memory size: {sys.getsizeof(encoded_raster_ds)} bytes")
            except Exception as e:
                error_msg = f"Failed to load/clip raster {raster_image.path}: {e}"
                logger.error(error_msg)
                for vi in self.vegetation_indices:
                    results.append(ProcessingResult(
                        raster_path=raster_image.path,
                        timestamp=raster_image.timestamp,
                        process_name=vi.process,
                        success=False,
                        error_message=error_msg
                    ))
                continue

            # Process each vegetation index for this raster
            for vegetation_index in self.vegetation_indices:
                result = self._process_single_index(
                    raster_image,
                    vegetation_index,
                    encoded_raster_ds,
                    plots_geojson
                )
                results.append(result)

        return results

    def _process_single_index(self,
                              raster_image: RasterImage,
                              vegetation_index: VegetationIndex,
                              encoded_raster_ds: str,
                              plots_geojson: Dict[str, Any]) -> ProcessingResult:
        """
        Process a single vegetation index for a single raster image

        Args:
            raster_image: The raster image being processed
            vegetation_index: The vegetation index to calculate
            encoded_raster_ds: Base64 encoded raster data
            plots_geojson: GeoJSON data for plots

        Returns:
            ProcessingResult object
        """
        try:
            logger.info(
                f"Calculating {vegetation_index.name} for {Path(raster_image.path).name}")

            # Prepare inputs for the vegetation index process
            raster_indices_inputs = {
                "input_value_raster": encoded_raster_ds,
                **vegetation_index.bands
            }

            # Execute the vegetation index process
            raster_indices_output = self.ogc_api_processes.execute_process(
                vegetation_index.process, raster_indices_inputs)

            if raster_indices_output is None:
                error_msg = f"Error executing process: {vegetation_index.process}"
                logger.error(error_msg)
                return ProcessingResult(
                    raster_path=raster_image.path,
                    timestamp=raster_image.timestamp,
                    process_name=vegetation_index.process,
                    success=False,
                    error_message=error_msg
                )

            # Prepare inputs for zonal statistics
            zonal_stats_inputs = {
                "input_zone_polygon": json.dumps(plots_geojson),
                "input_value_raster": raster_indices_output['value'],
                "raster_data": raster_indices_output['id']
            }

            # Execute zonal statistics
            zonal_stats = self.ogc_api_processes.execute_process(
                'zonal-stats', zonal_stats_inputs)

            if zonal_stats is None:
                error_msg = "Error executing zonal statistics"
                logger.error(error_msg)
                return ProcessingResult(
                    raster_path=raster_image.path,
                    timestamp=raster_image.timestamp,
                    process_name=vegetation_index.process,
                    success=False,
                    error_message=error_msg
                )

            # Create observations
            Plots.create_observations(
                self.sensorthingsapi_url, zonal_stats, raster_image.timestamp)

            success_msg = f"Successfully processed {vegetation_index.name} for {Path(raster_image.path).name}"
            logger.info(success_msg)

            return ProcessingResult(
                raster_path=raster_image.path,
                timestamp=raster_image.timestamp,
                process_name=vegetation_index.process,
                success=True
            )

        except Exception as e:
            error_msg = f"Error processing {vegetation_index.name} for {Path(raster_image.path).name}: {e}"
            logger.error(error_msg)
            return ProcessingResult(
                raster_path=raster_image.path,
                timestamp=raster_image.timestamp,
                process_name=vegetation_index.process,
                success=False,
                error_message=error_msg
            )

    def process(self) -> List[ProcessingResult]:
        """
        Process images using the parameters provided during initialization

        Returns:
            List of ProcessingResult objects
        """
        if not self.trial_id:
            raise ValueError("trial_id must be provided during initialization")

        return self.process_images()

    @staticmethod
    def log_results_summary(results: List[ProcessingResult]) -> None:
        """
        Print a summary of processing results

        Args:
            results: List of ProcessingResult objects
        """
        total_processes = len(results)
        successful_processes = sum(1 for r in results if r.success)
        failed_processes = total_processes - successful_processes

        logger.info("Processing Summary:")
        logger.info(f"Total processes: {total_processes}")
        logger.info(f"Successful: {successful_processes}")
        logger.info(f"Failed: {failed_processes}")

        if failed_processes > 0:
            logger.error("Failed processes:")
            for result in results:
                if not result.success:
                    logger.error(
                        f"  • {Path(result.raster_path).name} - {result.process_name}: {result.error_message}")

        if successful_processes == total_processes:
            logger.info("All processes completed successfully!")
        elif successful_processes > 0:
            logger.warning(
                f"Some processes completed successfully, but {failed_processes} failed.")
        else:
            logger.error("All processes failed!")


def process_images_from_config_file(config: Config) -> List[ProcessingResult]:
    """
    Convenience function to process images directly from a configuration object

    Args:
        config: Config object containing all processing parameters

    Returns:
        List of ProcessingResult objects
    """

    # Create processor with individual parameters from config
    processor = ImageProcessor(
        pygeoapi_url=config.pygeoapi_url,
        trial_id=config.trial_id,
        raster_images=config.raster_images,
        vegetation_indices=config.vegetation_indices,
        sensorthingsapi_url=config.sensorthingsapi_url
    )
    results = processor.process()

    # Log summary
    ImageProcessor.log_results_summary(results)

    return results
