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
        name='ndvi',
        symbol='ndvi',
        definition='Normalized Difference Vegetation Index'
    ),
    'properties': {
        'spectral_index': {
            'formula': '(NIR - Red) / (NIR + Red)',
            # 'bands': {                # Wavelengths and bandwidths for the bands are dependent on the sensor
            #     'NIR': {
            #         'wavelength': '850–880 nm',
            #         'bandwidth': '30 nm',
            #     },
            #     'RED': {
            #         'wavelength': '640–670 nm',
            #         'bandwidth': '30 nm',
            #     }
            # }
        }
    }
},
    {
    'name': Template('NDRE - Treatment Parcel $treatment_parcel_id'),
    'description': Template('NDRE Zonal Stats for Treatment Parcel $treatment_parcel_id'),
    'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement',
    'Sensor': 1,
    'ObservedProperty': 2,
    'unitOfMeasurement': UnitOfMeasurement(
        name='ndre',
        symbol='ndre',
        definition='Normalized Difference Red Edge Index'
    ),
    'properties': {
        'spectral_index': {
            'formula': '(NIR - RedEdge) / (NIR + RedEdge)',
        }
    }
},

]


# WPS REQUESTS
WPS_URL = Template(
    '${geoserver_url}/ows?service=WPS&version=1.0.0')
WPS_GET_CAPABILITIES_URL = Template(
    '${geoserver_url}/ows?service=WPS&version=1.0.0&request=GetCapabilities')


# PYGEOAPI
PYGEOAPI_URL = os.getenv('PYGEOAPI_URL')
# TEST_GEOTIFF = os.path.join(GIS_DATA_DIR, 'vari2.tif')
# TEST_GEOTIFF = os.path.join(GIS_DATA_DIR, 'dop20_rgb.tif')
TEST_GEOTIFF = os.path.join(
    GIS_DATA_DIR, 'DOP_AD24_TD_D4_V2_M600-Tetracam_3cm_UTM32.tif')
