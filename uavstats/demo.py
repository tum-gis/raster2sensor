import json
from osgeo import gdal
from dataclasses import dataclass, asdict
from rich import print
from uavstats import config
from uavstats.utils import fetch_data, clear, timeit
from uavstats.parcels import Parcels
from uavstats.ogcapiprocesses import OGCAPIProcesses
from uavstats.processes import zonal_statistics, calculate_ndvi
from uavstats.spatial_tools import read_raster, clip_raster, plot_raster, write_raster, encode_raster_to_base64, decode_base64_to_raster
import sys


@dataclass
class RasterImage:
    path: str
    timestamp: str


@timeit
def main(raster_images: list[RasterImage], process: str, bands: dict):

    parcels = Parcels(
        file_path=config.LAND_PARCELS_FILE,
        land_parcel_id='1',
        field_trial_id='FAIRagro UC6',
        treatment_parcel_id_field=config.TREATMENT_PARCELS_ID_FIELD,
        project_id=config.PROJECT_ID
    )

    ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)

    # *Load Parcels
    parcels_geojson = parcels.fetch_parcels_geojson(config.PROJECT_ID)
    parcels_ds = gdal.OpenEx(json.dumps(parcels_geojson))
    parcels_layer = parcels_ds.GetLayer()

    for raster_image in raster_images:
        # *Load raster file
        raster_ds = read_raster(raster_image.get('path'))

        # *Clip Raster Image
        clipped_raster_ds = clip_raster(raster_ds, parcels_layer)

        # *Prepare inputs for the process
        encoded_raster_ds = encode_raster_to_base64(clipped_raster_ds)
        print(
            f"Encoded raster memory size: {sys.getsizeof(encoded_raster_ds)} bytes")
        raster_indices_inputs = {
            "input_value_raster": encoded_raster_ds, **bands}

        # *Execute the process
        raster_indices_output = ogc_api_processes.execute_process(
            process, raster_indices_inputs)
        if raster_indices_output is None:
            print(f"[red]Error executing process: {process}")
            sys.exit(1)
        zonal_stats_inputs = {
            "input_zone_polygon": json.dumps(parcels_geojson),
            "input_value_raster": raster_indices_output['value'],
            "raster_data": raster_indices_output['id']

        }
        zonal_stats = ogc_api_processes.execute_process(
            'zonal-stats', zonal_stats_inputs)

        if zonal_stats is None:
            print("[red]Error executing zonal statistics")
            sys.exit(1)
        # *Create Observations
        parcels.create_observations(zonal_stats, raster_image.get('timestamp'))


if __name__ == '__main__':
    clear()
    raster_images = [
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_20240306_TD_D1_Rangacker_MCA_4cm_UTM32.tif",
            "timestamp": "2024-03-06T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_AD24_TD_20240405_D2_MCA_V2_3cm_UTM32.tif",
            "timestamp": "2024-04-05T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_20240522_AD24_TD_V2_MCA_3cm_UTM32.tif",
            "timestamp": "2024-05-22T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_AD24_TD_D4_V2_M600-Tetracam_3cm_UTM32.tif",
            "timestamp": "2024-05-23T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_AD24_TD_D5_V2_M600_MS_TTC_3cm_UTM32.tif",
            "timestamp": "2024-06-11T09:00:00+01:00"
        },
        # {
        #     "path": "D:\\GISDATA\\FAIRagro_Data\\Tetracam_MS_Images\\DOP_AD24_TD_D6_V2_MS_M600_TTC_3cm_UTM32.tif",
        #     "timestamp": "2024-06-25T09:00:00+01:00"
        # }
    ]
    ndvi_bands = {
        "red_band": 2,
        "nir_band": 5
    }

    ndre_bands = {
        "red_edge_band": 3,
        "nir_band": 5
    }

    # main(raster_images, 'ndvi', ndvi_bands)
    # main(raster_images, 'ndre', ndre_bands)
