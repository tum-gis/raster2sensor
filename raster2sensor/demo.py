import json
from osgeo import gdal
from dataclasses import dataclass, asdict
from rich import print
from raster2sensor import config
from raster2sensor.utils import fetch_data, clear, timeit
from raster2sensor.plots import Plots
from raster2sensor.ogcapiprocesses import OGCAPIProcesses
from raster2sensor.processes import zonal_statistics, calculate_ndvi
from raster2sensor.spatial_tools import read_raster, clip_raster, plot_raster, write_raster, encode_raster_to_base64, decode_base64_to_raster
import sys
from pathlib import Path


@dataclass
class RasterImage:
    path: str
    timestamp: str


@timeit
def main(trial_id: str, raster_images: list[RasterImage], process: str, bands: dict):
    if config.PYGEOAPI_URL is None:
        raise ValueError(
            "PYGEOAPI_URL must be set in the config and cannot be None.")
    ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)

    # *Load Plots
    plots_geojson = Plots.fetch_plots_geojson(trial_id)
    plots_ds = gdal.OpenEx(json.dumps(plots_geojson))
    plots_layer = plots_ds.GetLayer()

    for raster_image in raster_images:
        # *Load raster file
        # if raster_image.path does not exist, raise error
        if not Path(raster_image.path).exists():
            print(
                f"[red]Raster image path does not exist: {raster_image.path}")
            sys.exit(1)
        raster_ds = read_raster(raster_image.path)  # type: ignore

        # *Clip Raster Image
        clipped_raster_ds = clip_raster(raster_ds, plots_layer)

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
            "input_zone_polygon": json.dumps(plots_geojson),
            "input_value_raster": raster_indices_output['value'],
            "raster_data": raster_indices_output['id']

        }
        zonal_stats = ogc_api_processes.execute_process(
            'zonal-stats', zonal_stats_inputs)

        if zonal_stats is None:
            print("[red]Error executing zonal statistics")
            sys.exit(1)
        # *Create Observations
        Plots.create_observations(
            zonal_stats, raster_image.timestamp)  # type: ignore
        print(
            f"[green]Successfully processed raster image: {raster_image.path}[/green]")


if __name__ == '__main__':
    clear()
    raster_images = [
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\UAV Images\\2024\\Tetracam_MS_Images\\DOP_20240306_TD_D1_Rangacker_MCA_4cm_UTM32.tif",
            "timestamp": "2024-03-06T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\UAV Images\\2024\\Tetracam_MS_Images\\DOP_AD24_TD_20240405_D2_MCA_V2_3cm_UTM32.tif",
            "timestamp": "2024-04-05T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\UAV Images\\2024\\Tetracam_MS_Images\\DOP_20240522_AD24_TD_V2_MCA_3cm_UTM32.tif",
            "timestamp": "2024-05-22T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\UAV Images\\2024\\Tetracam_MS_Images\\DOP_AD24_TD_D4_V2_M600-Tetracam_3cm_UTM32.tif",
            "timestamp": "2024-05-23T09:00:00+01:00"
        },
        {
            "path": "D:\\GISDATA\\FAIRagro_Data\\UAV Images\\2024\\Tetracam_MS_Images\\DOP_AD24_TD_D5_V2_M600_MS_TTC_3cm_UTM32.tif",
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
    cirededge_bands = {
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

    raster_image_objs = [RasterImage(**img) for img in raster_images]

    main('Goetheweg-2024', raster_image_objs, 'ndvi', ndvi_bands)
    main('Goetheweg-2024', raster_image_objs, 'ndre', ndre_bands)
    main('Goetheweg-2024', raster_image_objs, 'cirededge', cirededge_bands)
    main('Goetheweg-2024', raster_image_objs, 'gndvi', gndvi_bands)
    main('Goetheweg-2024', raster_image_objs, 'savi', savi_bands)
    # main(raster_image_objs, 'mcari', mcari_bands)  # ! BUG verify calculation
    print("[green]Process completed successfully![/green]")
