import json
import numpy
from rich import print
from uavstats import config
from uavstats.utils import fetch_data, clear
from uavstats.parcels import Parcels
from uavstats.ogcprocesses import OGCAPIProcesses
from uavstats.zonalstats import execute_process
from uavstats.spatial_tools import read_raster, crop_raster, plot_raster, write_raster

from osgeo import ogr, gdal, osr


def read_geotiff(file_path):
    ds = gdal.Open(file_path)
    geotransform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    return {
        "dataset": ds,
        "array": arr,
        "geotransform": geotransform,
        "projection": projection
    }


def main():
    clear()
    test_geotiff_path = config.TEST_GEOTIFF
    ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)
    process_id = 'zonal-stats'

    #! Load raster file
    raster = read_geotiff(test_geotiff_path)
    # Serialize the raster array to JSON
    raster_array_json = json.dumps(raster['array'].tolist())

    #! Load Parcels
    parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)
    # Read the parcels GeoJSON in gdal
    parcels_ds = ogr.Open(config.PARCELS_GEOJSON)
    parcels_layer = parcels_ds.GetLayer()
    print(type(parcels_layer))
    print(parcels_layer.GetExtent())

    # Test Crop
    raster_ds = read_raster(test_geotiff_path)
    plot_raster(raster_ds)
    cropped_raster_ds = crop_raster(raster_ds, parcels_layer)
    plot_raster(cropped_raster_ds)
    write_raster(cropped_raster_ds, "./gis_data/cropped.tif")

    # ! Execute Process
    # process_inputs = {
    #     'input_value_raster': json.dumps(raster['array']),
    #     'input_zone_polygon': json.dumps(parcels_geojson)
    # }
    # ogc_process.execute_process(process_id, {"inputs": process_inputs})
    # print(raster['array'])
    # execute_process(json.dumps(parcels_geojson),
    #                 json.dumps(raster['array'].tolist()))


main()
