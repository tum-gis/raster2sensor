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
DATASTREAMS: list[Datastream] = [{
    'name': Template('NDVI - Treatment Parcel $treatment_parcel_id'),
    'description': Template('NDVI Zonal Stats for Treatment Parcel $treatment_parcel_id'),
    'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
    'Sensor': 1,
    'ObservedProperty': 1,
    'unitOfMeasurement': UnitOfMeasurement(
        name='NDVI',
        symbol='NDVI',
        definition='Normalized Difference Vegetation Index'
    ),
    'properties': {
        'index': {
            'formula': '(NIR - RED) / (NIR + RED)',
            'bands': {
                'NIR': {
                    'wavelength': '850–880 nm',
                    'bandwidth': '30 nm',
                },
                'RED': {
                    'wavelength': '640–670 nm',
                    'bandwidth': '30 nm',
                }
            }
        }
    }
},
    #     {
    #     'name': Template('VARI - $treatment_parcel_id'),
    #     'description': Template('VARI Zonal Stats for Parcel $treatment_parcel_id'),
    #     'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
    #     'Sensor': 1,
    #     'ObservedProperty': 2,
    #     'unitOfMeasurement': UnitOfMeasurement(
    #         name='VARI',
    #         symbol='VARI',
    #         definition='Visible Atmospherically Resistant Index'
    #     )
    # }
]


# WPS REQUESTS
WPS_URL = Template(
    '${geoserver_url}/ows?service=WPS&version=1.0.0')
WPS_GET_CAPABILITIES_URL = Template(
    '${geoserver_url}/ows?service=WPS&version=1.0.0&request=GetCapabilities')


# PYGEOAPI
PYGEOAPI_URL = os.getenv('PYGEOAPI_URL')
TEST_GEOTIFF = os.path.join(GIS_DATA_DIR, 'vari2.tif')
