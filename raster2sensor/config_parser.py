"""
Configuration Parser for Raster2Sensor

This module handles parsing of configuration files that include:
- Datastreams configuration
- Raster images with timestamps
- Vegetation indices/processes with their band configurations
"""

import json
import yaml
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass, asdict
from raster2sensor.sensorthingsapi import Datastream, UnitOfMeasurement


@dataclass
class RasterImage:
    """Configuration for a raster image"""
    path: str
    timestamp: str
    description: Optional[str] = None


@dataclass
class VegetationIndex:
    """Configuration for a vegetation index process"""
    name: str
    process: str
    bands: Dict[str, int]
    description: Optional[str] = None


@dataclass
class Config:
    """Main configuration structure"""
    datastreams: List[Dict[str, Any]]
    raster_images: List[RasterImage]
    vegetation_indices: List[VegetationIndex]
    trial_id: Optional[str] = None
    plot_id_field: Optional[str] = None
    year: Optional[int] = None


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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Determine file format and load
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML format in {config_path}: {e}")
            elif config_path.suffix.lower() == '.json':
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format in {config_path}: {e}")
            else:
                raise ValueError(f"Unsupported file format: {config_path.suffix}. Use .yml, .yaml, or .json")
        
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
        
        return Config(
            datastreams=datastreams,
            raster_images=raster_images,
            vegetation_indices=vegetation_indices,
            trial_id=config_data.get('trial_id'),
            plot_id_field=config_data.get('plot_id_field'),
            year=config_data.get('year')
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
            "trial_id": "Goetheweg-2024",
            "plot_id_field": "ID",
            "year": 2024,
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
                },
                {
                    "name": "GNDVI - Trial Plot {plot_id}",
                    "description": "Green Normalized Difference Vegetation Index (GNDVI) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 3},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Green Normalized Difference Vegetation Index"
                    },
                    "properties": {
                        "raster_data": "GNDVI",
                        "spectral_index": {
                            "name": "GNDVI",
                            "formula": "(NIR - Green) / (NIR + Green)"
                        }
                    }
                },
                {
                    "name": "SAVI - Trial Plot {plot_id}",
                    "description": "Soil Adjusted Vegetation Index (SAVI) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 4},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Soil Adjusted Vegetation Index"
                    },
                    "properties": {
                        "raster_data": "SAVI",
                        "spectral_index": {
                            "name": "SAVI",
                            "formula": "(NIR - Red) / (NIR + Red + L) * (1 + L)"
                        }
                    }
                },
                {
                    "name": "CIRedEdge - Trial Plot {plot_id}",
                    "description": "Chlorophyll Index Red Edge (CIRedEdge) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 5},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Chlorophyll Index Red Edge"
                    },
                    "properties": {
                        "raster_data": "CIRedEdge",
                        "spectral_index": {
                            "name": "CIRedEdge",
                            "formula": "(NIR / RedEdge) - 1"
                        }
                    }
                },
                {
                    "name": "MCARI - Trial Plot {plot_id}",
                    "description": "Modified Chlorophyll Absorption Ratio Index (MCARI) for Trial Plot {plot_id}",
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "Sensor": {"@iot.id": 1},
                    "ObservedProperty": {"@iot.id": 6},
                    "unitOfMeasurement": {
                        "name": "",
                        "symbol": "",
                        "definition": "Modified Chlorophyll Absorption Ratio Index"
                    },
                    "properties": {
                        "raster_data": "MCARI",
                        "spectral_index": {
                            "name": "MCARI",
                            "formula": "[(RedEdge - Red) - 0.2 * (RedEdge - Green)] * (RedEdge / Red)"
                        }
                    }
                }
            ],
            "raster_images": [
                {
                    "path": "data/DOP_20240306_TD_D1_Rangacker_MCA_4cm_UTM32.tif",
                    "timestamp": "2024-03-06T09:00:00+01:00",
                    "description": "UAV Image from March 6, 2024"
                },
                {
                    "path": "data/DOP_AD24_TD_20240405_D2_MCA_V2_3cm_UTM32.tif",
                    "timestamp": "2024-04-05T09:00:00+01:00",
                    "description": "UAV Image from April 5, 2024"
                }
            ],
            "vegetation_indices": [
                {
                    "name": "NDVI",
                    "process": "ndvi",
                    "bands": {
                        "red_band": 2,
                        "nir_band": 5
                    },
                    "description": "Normalized Difference Vegetation Index"
                },
                {
                    "name": "NDRE",
                    "process": "ndre",
                    "bands": {
                        "red_edge_band": 3,
                        "nir_band": 5
                    },
                    "description": "Normalized Difference Red Edge Index"
                },
                {
                    "name": "GNDVI",
                    "process": "gndvi",
                    "bands": {
                        "green_band": 1,
                        "nir_band": 5
                    },
                    "description": "Green Normalized Difference Vegetation Index"
                },
                {
                    "name": "SAVI",
                    "process": "savi",
                    "bands": {
                        "red_band": 2,
                        "nir_band": 5
                    },
                    "description": "Soil Adjusted Vegetation Index"
                },
                {
                    "name": "CIRedEdge",
                    "process": "cirededge",
                    "bands": {
                        "red_edge_band": 3,
                        "nir_band": 5
                    },
                    "description": "Chlorophyll Index Red Edge"
                },
                {
                    "name": "MCARI",
                    "process": "mcari",
                    "bands": {
                        "red_band": 2,
                        "green_band": 1,
                        "nir_band": 5
                    },
                    "description": "Modified Chlorophyll Absorption Ratio Index"
                }
            ]
        }
        
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(sample_config, f, default_flow_style=False, indent=2, sort_keys=False)
            else:
                json.dump(sample_config, f, indent=2)
        
        print(f"Sample configuration created: {output_path}")


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
            Sensor=ds_data.get('Sensor', {}),  # Capitalized to match config_parser
            ObservedProperty=ds_data.get('ObservedProperty', {}),  # Capitalized to match config_parser
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