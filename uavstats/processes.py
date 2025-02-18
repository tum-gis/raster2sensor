# https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#calculate-zonal-statistics
# https://github.com/ECCC-MSC/msc-pygeoapi/blob/master/msc_pygeoapi/process/weather/extract_raster.py
import logging
import json
from rich import print
from osgeo import gdal, ogr
import numpy
from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
from uavstats.spatial_tools import read_raster, clip_raster, plot_raster, write_raster, encode_raster_to_base64, decode_base64_to_raster

ogr.UseExceptions()
LOGGER = logging.getLogger(__name__)

#: Process metadata and description
PROCESS_METADATA = {
    'version': '1.0.0',
    'id': 'zonal-stats',
    'title': {
        'en': 'Zonal Statistics',
    },
    'description': {
        'en': 'Raster zonal statistics calculation',
    },
    'keywords': ['zonal statistics', 'raster', 'vector'],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://example.org/process',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'input_value_raster': {
            'title': 'Raster',
            'description': 'Raster file as values',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['raster', 'value']
        },
        'input_zone_polygon': {
            'title': 'Zones',
            'description': 'Shape file as zones',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['vector', 'zones']
        }
    },
    'outputs': {
        'statsValue': {
            'title': 'Zonal Statistics Ouputs',
            'description': 'Statistical summary: Average, Mean, Medain, Standard Deviation, Variance',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            },
            'output': {
                'formats': [{
                    'mimeType': 'application/json'
                }]
            }
        }
    },
}


def zonal_statistics(input_zone_polygon: str, input_value_raster: str, stats: list[str] = ["mean", "min", "max", "sum"]) -> dict:
    """
    Computes zonal statistics for each polygon feature in the vector dataset.

    Args:
        input_zone_polygon (str): GeoJSON string
        input_value_raster (str): Base64 encoded raster
        stats (list): List of statistics to compute
    """
    # Open raster and vector datasets
    raster_ds = decode_base64_to_raster(input_value_raster)
    vector_ds = gdal.OpenEx(input_zone_polygon)
    vector_layer = vector_ds.GetLayer()

    # Get raster geotransform and metadata
    # https://gdal.org/en/stable/tutorials/geotransforms_tut.html
    transform = raster_ds.GetGeoTransform()
    pixel_width, pixel_height = abs(transform[1]), abs(transform[5])

    # Create an in-memory raster for rasterization
    rasterized = gdal.GetDriverByName('MEM').Create(
        '', raster_ds.RasterXSize, raster_ds.RasterYSize, 1, gdal.GDT_Byte)
    rasterized.SetGeoTransform(transform)
    rasterized.SetProjection(raster_ds.GetProjection())

    # Read the original raster data
    band = raster_ds.GetRasterBand(1)
    raster_data = band.ReadAsArray()

    # Store results for each polygon
    results = {'type': 'FeatureCollection', 'features': []}

    # Loop through each polygon feature
    for feat in range(vector_layer.GetFeatureCount()):
        # Rasterize the current polygon feature
        feature = vector_layer.GetFeature(feat)
        rasterized.GetRasterBand(1).Fill(0)  # Reset the mask
        # Create layer with the current feature
        vector_layer.SetAttributeFilter(f"FID = {feature.GetFID()}")
        gdal.RasterizeLayer(rasterized, [1], vector_layer, burn_values=[
                            1], )

        # Read rasterized polygon mask
        mask_data = rasterized.GetRasterBand(1).ReadAsArray()

        # Extract valid pixels inside the polygon
        valid_pixels = raster_data[mask_data == 1]

        # Compute statistics for the polygon

        polygon_stats = {
            "FID": feature.GetFID(),
            "name": feature.GetField('name'),
            "iot_id": feature.GetField('iot_id'),
            "mean": float(numpy.mean(valid_pixels)) if valid_pixels.size > 0 else None,
            "min": float(numpy.min(valid_pixels)) if valid_pixels.size > 0 else None,
            "max": float(numpy.max(valid_pixels)) if valid_pixels.size > 0 else None,
            "sum": float(numpy.sum(valid_pixels)) if valid_pixels.size > 0 else None,
            "count": int(valid_pixels.size),
        }
        enriched_features = {
            'type': 'Feature',
            'geometry': json.loads(feature.GetGeometryRef().ExportToJson()),
            'properties': polygon_stats
        }

        results['features'].append(enriched_features)

    # Cleanup
    raster_ds, vector_ds, rasterized = None, None, None
    return results


def calculate_ndvi(input_value_raster: str, red_band: int, nir_band: int) -> str:
    # TODO: Validate that this is working correctly
    """Calculate NDVI from a raster dataset

    Args:
        input_value_raster (str): Base64 encoded raster
        red_band (int): Red band index
        nir_band (int): Near-infrared band index

    Returns:
        output raster (str): NDVI values as a base64 encoded raster
    """
    # Decode the base64 raster
    raster_ds = decode_base64_to_raster(input_value_raster)
    # Get the red and NIR bands
    red_band = raster_ds.GetRasterBand(
        red_band).ReadAsArray().astype(numpy.float64)
    nir_band = raster_ds.GetRasterBand(
        nir_band).ReadAsArray().astype(numpy.float64)
    # # Read the band data
    # red_data = red_band.ReadAsArray().astype(numpy.float32)
    # nir_data = nir_band.ReadAsArray().astype(numpy.float32)
    # Calculate NDVI
    with numpy.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_band - red_band) / (nir_band + red_band)
        ndvi[ndvi == numpy.inf] = numpy.nan
        ndvi = numpy.nan_to_num(ndvi, nan=-999)

    # Create NDVI raster
    driver = gdal.GetDriverByName('MEM')
    ndvi_ds = driver.Create('', raster_ds.RasterXSize,
                            raster_ds.RasterYSize, 1, gdal.GDT_Float32)
    ndvi_ds.SetGeoTransform(raster_ds.GetGeoTransform())
    ndvi_ds.SetProjection(raster_ds.GetProjection())
    ndvi_band = ndvi_ds.GetRasterBand(1)
    ndvi_band.WriteArray(ndvi)
    ndvi_band.SetNoDataValue(-999)

    # Cleanup
    raster_ds = None
    red_band, nir_band = None, None
    return encode_raster_to_base64(ndvi_ds)
