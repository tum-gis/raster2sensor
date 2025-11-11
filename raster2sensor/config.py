""" #FIXME: 
DEPRECATED!
Configuration module for Raster2Sensor application.
"""

import os
from dotenv import load_dotenv, find_dotenv
from raster2sensor.sensorthingsapi import UnitOfMeasurement, Datastream
load_dotenv(find_dotenv())


# DATA DIRECTORIES & FILES
DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
PLOTS_GEOJSON = os.path.join(DATA_DIR, 'plots.geojson')

# SENSOR THINGS API
SENSOR_THINGS_API_URL = os.getenv('SENSOR_THINGS_API_URL')

# PYGEOAPI
PYGEOAPI_URL = os.getenv('PYGEOAPI_URL')

# SAMPLE DATASTREAMS CONFIGURATION
# To be provided as a YAML or JSON file, see example in datastreams.yml
DATASTREAMS: list[Datastream] = [
    Datastream(
        name='NDVI -  Trial Plot {plot_id}',
        description='Normalized Difference Vegetation Index (NDVI) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 1},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Normalized Difference Vegetation Index'
        ),
        properties={
            'raster_data': 'NDVI',
            'spectral_index': {
                'name': 'NDVI',
                'formula': '(NIR - Red) / (NIR + Red)',
            }
        }
    ),
    Datastream(
        name='NDRE - Trial Plot {plot_id}',
        description='Normalized Difference Red Edge Index (NDRE) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 2},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Normalized Difference Red Edge Index'
        ),
        properties={
            'raster_data': 'NDRE',
            'spectral_index': {
                'name': 'NDRE',
                'formula': '(NIR - RedEdge) / (NIR + RedEdge)',
            }
        }
    ),
    Datastream(
        name='GNDVI - Trial Plot {plot_id}',
        description='Green Normalized Difference Vegetation Index (GNDVI) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 3},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Green Normalized Difference Vegetation Index'
        ),
        properties={
            'raster_data': 'GNDVI',
            'spectral_index': {
                'name': 'GNDVI',
                'formula': '(NIR - Green) / (NIR + Green)',
            }
        }
    ),
    Datastream(
        name='SAVI - Trial Plot {plot_id}',
        description='Soil Adjusted Vegetation Index (SAVI) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 4},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Soil Adjusted Vegetation Index'
        ),
        properties={
            'raster_data': 'SAVI',
            'spectral_index': {
                'name': 'SAVI',
                'formula': '((NIR - Red) / (NIR + Red + L)) * (1 + L). where L is a soil brightness correction factor (typically 0.5)',
            }
        }
    ),
    Datastream(
        name='CIRedEdge - Trial Plot {plot_id}',
        description='Chlorophyll Index (CIRedEdge) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 5},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Chlorophyll Index (CIRedEdge)'
        ),
        properties={
            'raster_data': 'CIRedEdge',
            'spectral_index': {
                'name': 'CIRedEdge',
                'formula': '(NIR / RedEdge) -1',
            }
        }
    ),
    Datastream(
        name='MCARI - Trial Plot {plot_id}',
        description='Modified Chlorophyll Absorption in Reflectance Index (MCARI) for Trial Plot {plot_id}',
        observationType='http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
        Sensor={"@iot.id": 1},
        ObservedProperty={"@iot.id": 6},
        unitOfMeasurement=UnitOfMeasurement(
            name='',
            symbol='',
            definition='Modified Chlorophyll Absorption in Reflectance Index (MCARI)'
        ),
        properties={
            'raster_data': 'MCARI',
            'spectral_index': {
                'name': 'MCARI',
                'formula': '((NIR - RED) - 0.2 *(NIR - GREEN)) * (NIR / RED)',
            }
        }
    )
]
