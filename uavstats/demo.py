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
from pathlib import Path


@dataclass
class RasterImage:
    path: str
    timestamp: str


@timeit
def main(raster_images: list[RasterImage], process: str, bands: dict):
    parcels = Parcels(
        file_path=Path(config.LAND_PARCELS_FILE),
        land_parcel_id='1',
        field_trial_id='FAIRagro UC6',
        treatment_parcel_id_field=config.TREATMENT_PARCELS_ID_FIELD if config.TREATMENT_PARCELS_ID_FIELD is not None else "",
        project_id=config.PROJECT_ID if config.PROJECT_ID is not None else ""
    )

    if config.PYGEOAPI_URL is None:
        raise ValueError(
            "PYGEOAPI_URL must be set in the config and cannot be None.")
    ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)

    # *Load Parcels
    parcels_geojson = parcels.fetch_parcels_geojson(
        config.PROJECT_ID if config.PROJECT_ID is not None else "")
    parcels_ds = gdal.OpenEx(json.dumps(parcels_geojson))
    parcels_layer = parcels_ds.GetLayer()

    for raster_image in raster_images:
        # *Load raster file
        raster_ds = read_raster(raster_image.get('path'))  # type: ignore

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
        parcels.create_observations(
            zonal_stats, raster_image.get('timestamp'))  # type: ignore


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
    cired_edge_bands = {
        "red_edge_band": 3,
        "nir_band": 5
    }
    gndvi_bands = {
        "green_band": 1,
        "nir_band": 5
    }
    savi_bands = {
        "red_band": 2,
        "nir_band": 5
    }
    mcari_bands = {
        "red_band": 2,
        "green_band": 1,
        "nir_band": 5
    }

    # main(raster_images, 'ndvi', ndvi_bands)
    # main(raster_images, 'ndre', ndre_bands)
    # main(raster_images, 'cired-edge', cired_edge_bands) #! BUG Processing: list out of range
    main(raster_images, 'gndvi', gndvi_bands)
    main(raster_images, 'savi', savi_bands)
    main(raster_images, 'mcari', mcari_bands)  # ! BUG verify calculation
    print("[green]Process completed successfully![/green]")
