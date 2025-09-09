import os
from dotenv import load_dotenv, find_dotenv
from string import Template
from uavstats.sensorthingsapi import UnitOfMeasurement, Datastream
load_dotenv(find_dotenv())


GEOSERVER_URL = os.getenv('GEOSERVER_URL')
GEOSERVER_USER = os.getenv('GEOSERVER_USER')
GEOSERVER_PASSWORD = os.getenv('GEOSERVER_PASSWORD')

# DATA DIRECTORIES & FILES
GIS_DATA_DIR = './gis_data'
if not os.path.exists(GIS_DATA_DIR):
    os.makedirs(GIS_DATA_DIR)

VARI_GEO_TIFF = os.path.join(GIS_DATA_DIR, 'VARI.tif')
PARCELS_GEOJSON = os.path.join(GIS_DATA_DIR, 'parcels.geojson')
OUTPUT_JSON = os.path.join(GIS_DATA_DIR, 'output.json')


# LAND PARCELS
LAND_PARCELS_FILE = os.path.join(GIS_DATA_DIR, 'parcels_wgs84.geojson')
TREATMENT_PARCELS_ID_FIELD = os.getenv('TREATMENT_PARCELS_ID_FIELD')
PROJECT_ID = os.getenv('PROJECT_ID')

# SENSOR THINGS API
SENSOR_THINGS_API_URL = os.getenv('SENSOR_THINGS_API_URL')
# DATASTREAMS: list[Datastream] = [{
#     'name': Template('NDVI - Treatment Parcel $treatment_parcel_id'),
#     'description': Template('NDVI for Treatment Parcel $treatment_parcel_id'),
#     'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
#     'Sensor': 1,
#     'ObservedProperty': 1,
#     'unitOfMeasurement': UnitOfMeasurement(
#         name='',
#         symbol='',
#         definition='Normalized Difference Vegetation Index'
#     ),
#     'properties': {
#         'raster_data': 'NDVI',
#         'spectral_index': {
#             'name': 'NDVI',
#             'formula': '(NIR - Red) / (NIR + Red)',
#             # 'bands': {                # Wavelengths and bandwidths for the bands are dependent on the sensor
#             #     'NIR': {
#             #         'wavelength': '850–880 nm',
#             #         'bandwidth': '30 nm',
#             #     },
#             #     'RED': {
#             #         'wavelength': '640–670 nm',
#             #         'bandwidth': '30 nm',
#             #     }
#             # }
#         }
#     }
# },
#     {
#     'name': Template('NDRE - Treatment Parcel $treatment_parcel_id'),
#     'description': Template('NDRE for Treatment Parcel $treatment_parcel_id'),
#     'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
#     'Sensor': 1,
#     'ObservedProperty': 2,
#     'unitOfMeasurement': UnitOfMeasurement(
#         name='',
#         symbol='',
#         definition='Normalized Difference Red Edge Index'
#     ),
#     'properties': {
#         'raster_data': 'NDRE',
#         'spectral_index': {
#             'name': 'NDRE',
#             'formula': '(NIR - RedEdge) / (NIR + RedEdge)',
#         }
#     }
# },

# ]

DATASTREAMS: list[Datastream] = [
    Datastream(
        name='NDVI -  Plot {plot_id}',
        description='Normalized Difference Vegetation Index (NDVI) for Plot ID: {plot_id}',
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
        name='NDRE - Plot {plot_id}',
        description='Normalized Difference Red Edge Index (NDRE) for Plot ID: {plot_id}',
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
    )
]

ADDITIONAL_DATASTREAMS: list[Datastream] = [
    Datastream(
        name='GNDVI - Plot {plot_id}',
        description='Green Normalized Difference Vegetation Index (GNDVI) for Plot ID: {plot_id}',
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
        name='SAVI - Plot {plot_id}',
        description='Soil Adjusted Vegetation Index (SAVI) for Plot ID: {plot_id}',
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
        name='CIRedEdge - Plot {plot_id}',
        description='Chlorophyll Index (CIRedEdge) for Plot ID: {plot_id}',
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
        name='MCARI - Plot {plot_id}',
        description='Modified Chlorophyll Absorption in Reflectance Index (MCARI) for Plot ID: {plot_id}',
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


# PYGEOAPI
PYGEOAPI_URL = os.getenv('PYGEOAPI_URL')
# TEST_GEOTIFF = os.path.join(GIS_DATA_DIR, 'vari2.tif')
# TEST_GEOTIFF = os.path.join(GIS_DATA_DIR, 'dop20_rgb.tif')
TEST_GEOTIFF = os.path.join(
    GIS_DATA_DIR, 'DOP_AD24_TD_D4_V2_M600-Tetracam_3cm_UTM32.tif')
