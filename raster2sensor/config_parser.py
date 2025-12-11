"""
Configuration Parser for the raster2sensor package

This module handles parsing of configuration files that include:
- Datastreams configuration
- Raster images with timestamps
- Vegetation indices/processes with their band configurations
"""

import json
import yaml
from pathlib import Path
from typing import List, Union, Dict, Any
from dataclasses import dataclass
from raster2sensor.sensorthingsapi import Datastream, UnitOfMeasurement
from raster2sensor.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RasterImage:
    """Configuration for a raster image"""
    path: str
    timestamp: str


@dataclass
class VegetationIndex:
    """Configuration for a vegetation index process"""
    name: str
    process: str
    bands: Dict[str, int]


@dataclass
class Config:
    """Main configuration structure"""
    trial_id: str
    plot_id_field: str
    year: int
    sensorthingsapi_url: str
    pygeoapi_url: str
    ndvi_file: Path
    datastreams: List[Dict[str, Any]]
    raster_images: List[RasterImage]
    vegetation_indices: List[VegetationIndex]


class ConfigParser:
    """Parser for configuration files supporting YAML and JSON"""

    @staticmethod
    def load_config(config_path: Union[str, Path]) -> Config:
        """
        Load configuration from YAML or JSON file

        Args:
            config_path: Path to the configuration file

        Returns:
            Config object

        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the config format is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}")

        # Determine file format and load
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(
                        f"Invalid YAML format in {config_path}: {e}")
            elif config_path.suffix.lower() == '.json':
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON format in {config_path}: {e}")
            else:
                raise ValueError(
                    f"Unsupported file format: {config_path.suffix}. Use .yml, .yaml, or .json")

        return ConfigParser._parse_config(config_data)

    @staticmethod
    def _parse_config(config_data: Dict[str, Any]) -> Config:
        """Parse configuration data into Config object"""

        # Parse datastreams
        datastreams_data = config_data.get('datastreams', [])
        datastreams = []
        for ds_data in datastreams_data:
            # Convert to the format expected by existing datastream parser
            datastreams.append(ds_data)

        # Parse raster images
        raster_images_data = config_data.get('raster_images', [])
        raster_images = []
        for img_data in raster_images_data:
            raster_images.append(RasterImage(**img_data))

        # Parse vegetation indices
        vegetation_indices_data = config_data.get('vegetation_indices', [])
        vegetation_indices = []
        for vi_data in vegetation_indices_data:
            vegetation_indices.append(VegetationIndex(**vi_data))
        # Validate required fields
        required_fields = ['trial_id', 'plot_id_field',
                           'sensorthingsapi_url', 'pygeoapi_url']
        missing_fields = []

        for field in required_fields:
            if not config_data.get(field):
                missing_fields.append(field)

        if missing_fields:
            logger.error(
                f"Missing required configuration fields: {', '.join(missing_fields)}")
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}")

        return Config(
            # Use direct access after validation
            trial_id=config_data['trial_id'],
            plot_id_field=config_data['plot_id_field'],
            year=config_data.get('year', 2025),  # Default year to 2025
            ndvi_file=Path(config_data.get('ndvi_file', 'data/ndvi_data.csv')),
            sensorthingsapi_url=config_data['sensorthingsapi_url'],
            pygeoapi_url=config_data['pygeoapi_url'],
            datastreams=datastreams,
            raster_images=raster_images,
            vegetation_indices=vegetation_indices
        )

    @staticmethod
    def create_sample_config(output_path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Create a sample configuration file

        Args:
            output_path: Path where to save the sample config
            format: 'yaml' or 'json'
        """
        sample_config = {
            "sensorthingsapi_url": "http://localhost:8080/FROST-Server/v1.1",
            "pygeoapi_url": "http://localhost:5000/api",
            "trial_id": "MyTrial-2025",
            "plot_id_field": "ID",
            "ndvi_file": "data/ndvi_MyTrial-2025.csv",
            "year": 2025,
            "datastreams": [
                {
                    "name": "NDVI - Trial Plot {plot_id}",
                    "description": "Normalized Difference Vegetation Index (NDVI) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 1},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Normalized Difference Vegetation Index"
                    },
                    "properties": {
                        "raster_data": "NDVI",
                        "spectral_index": {
                            "name": "NDVI",
                            "formula": "(NIR - Red) / (NIR + Red)"
                        }
                    }
                },
                {
                    "name": "NDRE - Trial Plot {plot_id}",
                    "description": "Normalized Difference Red Edge Index (NDRE) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 2},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Normalized Difference Red Edge Index"
                    },
                    "properties": {
                        "raster_data": "NDRE",
                        "spectral_index": {
                            "name": "NDRE",
                            "formula": "(NIR - RedEdge) / (NIR + RedEdge)"
                        }
                    }
                }
            ],
            "raster_images": [
                {
                    "path": "data/DOP_20240306_TD_D1_Rangacker_MCA_4cm_UTM32.tif",
                    "timestamp": "2024-03-06T09:00:00+01:00"
                },
                {
                    "path": "data/DOP_AD24_TD_20240405_D2_MCA_V2_3cm_UTM32.tif",
                    "timestamp": "2024-04-05T09:00:00+01:00"
                }
            ],
            "vegetation_indices": [
                {
                    "name": "NDVI",
                    "process": "ndvi",
                    "bands": {
                        "red_band": 2,
                        "nir_band": 5
                    }
                },
                {
                    "name": "NDRE",
                    "process": "ndre",
                    "bands": {
                        "red_edge_band": 3,
                        "nir_band": 5
                    }
                }

            ]
        }

        output_path = Path(output_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(sample_config, f, default_flow_style=False,
                          indent=2, sort_keys=False)
            else:
                json.dump(sample_config, f, indent=2)

        logger.info(f"Sample configuration created: {output_path}")


def load_datastreams_from_config(config_path: Union[str, Path]) -> List[Datastream]:
    """
    Load datastreams from configuration file

    Args:
        config_path: Path to the configuration file

    Returns:
        List of Datastream objects
    """
    config = ConfigParser.load_config(config_path)

    datastreams = []
    for ds_data in config.datastreams:
        # Create UnitOfMeasurement object
        uom_data = ds_data.get('unitOfMeasurement', {})
        unit_of_measurement = UnitOfMeasurement(
            name=uom_data.get('name', ''),
            symbol=uom_data.get('symbol', ''),
            definition=uom_data.get('definition', '')
        )

        # Create Datastream object using the correct field names that match config_parser
        datastream = Datastream(
            name=ds_data.get('name', ''),
            description=ds_data.get('description', ''),
            observationType=ds_data.get('observationType', ''),
            unitOfMeasurement=unit_of_measurement,
            Sensor=ds_data.get('Sensor', {}),
            ObservedProperty=ds_data.get('ObservedProperty', {}),
            properties=ds_data.get('properties', {})
        )

        datastreams.append(datastream)

    return datastreams


# Legacy compatibility - these classes are kept for backward compatibility
# but they just redirect to the new classes
class DatastreamConfigParser(ConfigParser):
    """Legacy class name - redirects to ConfigParser for backward compatibility"""
    pass


class UnifiedConfigParser(ConfigParser):
    """Legacy class name - redirects to ConfigParser for backward compatibility"""
    pass


class UnifiedConfig(Config):
    """Legacy class name - redirects to Config for backward compatibility"""
    pass


def load_datastreams_from_unified_config(config_path: Union[str, Path]) -> List[Datastream]:
    """Legacy function name - redirects to load_datastreams_from_config for backward compatibility"""
    return load_datastreams_from_config(config_path)
