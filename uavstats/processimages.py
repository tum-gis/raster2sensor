import json
from osgeo import gdal
from rich import print
from uavstats import config
from uavstats.utils import fetch_data, clear
from uavstats.parcels import Parcels
from uavstats.ogcapiprocesses import OGCAPIProcesses
from uavstats.processes import zonal_statistics, calculate_ndvi
from uavstats.spatial_tools import read_raster, clip_raster, plot_raster, write_raster, encode_raster_to_base64, decode_base64_to_raster
import sys


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

    # !Load raster file
    raster = read_geotiff(test_geotiff_path)
    # Serialize the raster array to JSON
    raster_array_json = json.dumps(raster['array'].tolist())

    # !Load Parcels
    parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)
    # Read the parcels GeoJSON in gdal
    parcels_ds = gdal.OpenEx(json.dumps(parcels_geojson))
    parcels_layer = parcels_ds.GetLayer()

    # !Clip Raster Image
    raster_ds = read_raster(test_geotiff_path)
    # plot_raster(raster_ds)
    cropped_raster_ds = clip_raster(raster_ds, parcels_layer)
    # plot_raster(cropped_raster_ds)
    # write_raster(cropped_raster_ds, "./gis_data/cropped.tif")

    # !Prepare inputs for the process
    encoded_raster_ds = encode_raster_to_base64(cropped_raster_ds)
    # Compare actual memory size of the encoded raster vs the original raster
    original_raster_size = sys.getsizeof(raster['array'])
    encoded_raster_size = sys.getsizeof(encoded_raster_ds)
    # print(f"Original raster memory size: {original_raster_size} bytes")
    # print(f"Encoded raster memory size: {encoded_raster_size} bytes")

    # # !Execute Process -> TEST
    # # Calculate NDVI
    # ndvi_raster_ds = calculate_ndvi(encoded_raster_ds, 1, 2)
    # output = decode_base64_to_raster(ndvi_raster_ds)
    # write_raster(output, "./gis_data/ndvi.tif")
    # plot_raster(output)

    # # Zonal Statistics
    # zonal_stats = zonal_statistics(
    #     json.dumps(parcels_geojson), encoded_raster_ds)
    # print(zonal_stats)

    # !Execute Process -> PYGEOAPI
    # inputs = {
    #     "input_zone_polygon": json.dumps(parcels_geojson),
    #     # Ensure the base64 is a string
    #     "input_value_raster": encoded_raster_ds
    # }
    # # Execute the process
    # output = ogc_api_processes.execute_process(process_id, inputs)
    # print(output)
    # # Write to geojson file
    # with open('./gis_data/test.geojson', 'w') as f:
    #     json.dump(output['value'], f, indent=2)
    # NDVI
    inputs = {
        "input_value_raster": encoded_raster_ds,
        "red_band": 1,
        "nir_band": 2
    }
    # Execute the process
    output = ogc_api_processes.execute_process('ndvi', inputs)
    plot_raster(decode_base64_to_raster(output['value']))


main()
