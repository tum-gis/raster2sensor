import json
import numpy
from rich import print
from uavstats import config
from uavstats.utils import fetch_data, clear
from uavstats.plots import Plots
from uavstats.ogcapiprocesses import OGCAPIProcesses
from uavstats.processes import execute_process

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
    ogc_process = OGCAPIProcesses(config.PYGEOAPI_URL)
    process_id = 'zonal-stats'
    # ogc_process.fetch_processes()
    # ogc_process.describe_process(process_id)

    #! Load raster file
    # with rasterio.open(test_geotiff_path) as src:
    #     with MemoryFile() as memfile:
    #         with memfile.open(**src.profile) as mem:
    #             mem.write(src.read())
    #             raster = mem.read()
    # dataset = gdal.Open(test_geotiff_path)
    # band = dataset.GetRasterBand(1)
    # raster = dataset.ReadAsArray().tolist()
    # array = band.ReadAsArray().tolist()
    raster = read_geotiff(test_geotiff_path)
    # print(raster['array'].tolist())
    # print(gdal_array.LoadFile(test_geotiff_path))

    #! Get Parcels
    parcels = Parcels(
        file_path=config.LAND_PARCELS_FILE,
        land_parcel_id='1',
        field_trial_id='FAIRagro UC6',
        treatment_parcel_id_field=config.TREATMENT_PARCELS_ID_FIELD,
        project_id=config.PROJECT_ID
    )
    parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)

    # ! Execute Process
    # process_inputs = {
    #     'input_value_raster': json.dumps(raster['array']),
    #     'input_zone_polygon': json.dumps(parcels_geojson)
    # }
    # ogc_process.execute_process(process_id, {"inputs": process_inputs})
    # print(raster['array'])
    execute_process(json.dumps(parcels_geojson),
                    json.dumps(raster['array'].tolist()))

    # # # ! REVERSE GeoTIFF
    # # Read numpy array as raster
    # print('[blue] original array')
    # print(raster['array'])

    # # OGC API Input
    # load_json = json.loads(json.dumps(raster['array'].tolist()))
    # input_value_raster = numpy.array(load_json)
    # print('[blue] recreated json array')
    # print(input_value_raster)

    # # TEST whether the array is the same as the original
    # print('[yellow] array comparison')
    # print(numpy.array_equal(raster['array'], input_value_raster))
    # new_raster = gdal.GetDriverByName('MEM').Create(
    #     '', input_value_raster.shape[1], input_value_raster.shape[0], 1, gdal.GDT_Float32)
    # new_raster.GetRasterBand(1).WriteArray(input_value_raster)
    # new_raster.SetGeoTransform(raster['geotransform'])
    # new_raster.SetProjection(raster['projection'])
    # print('[green] raster array')
    # print(new_raster)
    # # Read raster as arrays
    # print()
    # print(raster['dataset'].GetProjection())

    # srs = osr.SpatialReference()
    # srs.ImportFromEPSG(4326)
    # new_raster.SetProjection(srs.ExportToWkt())
    # print()
    # print(new_raster.GetProjection())


main()
