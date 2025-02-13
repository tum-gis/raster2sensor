# https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#calculate-zonal-statistics
# https://github.com/ECCC-MSC/msc-pygeoapi/blob/master/msc_pygeoapi/process/weather/extract_raster.py
import json
import logging
from rich import print
from osgeo import gdal, osr, ogr
# import gdal
# import osr
# import ogr
import numpy
from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
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


def zonal_stats(feat, input_zone_polygon, input_value_raster):
    # Read numpy array as raster
    load_json = json.loads(input_value_raster)
    input_value_raster = numpy.array(load_json)
    print(input_value_raster)
    raster = gdal.GetDriverByName('MEM').Create(
        '', input_value_raster.shape[1], input_value_raster.shape[0], 1, gdal.GDT_Float32)
    raster.GetRasterBand(1).WriteArray(input_value_raster)

    # Set geotransform (example values - adjust as needed)
    geotransform = (10.626763017, 2.802632411067409e-06, 0.0,
                    49.208020635, 0.0, -1.7604186046400793e-06)
    raster.SetGeoTransform(geotransform)

    # Set projection (example using WGS 84 - EPSG:4326)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    raster.SetProjection(srs.ExportToWkt())
    print(raster)

    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()

    # Get raster georeference info
    transform = raster.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    # Reproject vector geometry to same projection as raster
    sourceSR = lyr.GetSpatialRef()
    targetSR = osr.SpatialReference()
    targetSR.ImportFromWkt(raster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
    feat = lyr.GetNextFeature()
    geom = feat.GetGeometryRef()
    geom.Transform(coordTrans)

    # Get extent of feat
    geom = feat.GetGeometryRef()
    if (geom.GetGeometryName() == 'MULTIPOLYGON'):
        count = 0
        pointsX = []
        pointsY = []
        for polygon in geom:
            geomInner = geom.GetGeometryRef(count)
            ring = geomInner.GetGeometryRef(0)
            numpoints = ring.GetPointCount()
            for p in range(numpoints):
                lon, lat, z = ring.GetPoint(p)
                pointsX.append(lon)
                pointsY.append(lat)
            count += 1
    elif (geom.GetGeometryName() == 'POLYGON'):
        ring = geom.GetGeometryRef(0)
        numpoints = ring.GetPointCount()
        pointsX = []
        pointsY = []
        for p in range(numpoints):
            lon, lat, z = ring.GetPoint(p)
            pointsX.append(lon)
            pointsY.append(lat)

    else:
        msg = "ERROR: Geometry needs to be either Polygon or Multipolygon"
        LOGGER.error(msg)
        raise ProcessorExecuteError(msg)

    xmin = min(pointsX)
    xmax = max(pointsX)
    ymin = min(pointsY)
    ymax = max(pointsY)

    # Specify offset and rows and columns to read
    xoff = int((xmin - xOrigin)/pixelWidth)
    yoff = int((yOrigin - ymax)/pixelWidth)
    xcount = int((xmax - xmin)/pixelWidth)+1
    ycount = int((ymax - ymin)/pixelWidth)+1

    # Create memory target raster
    target_ds = gdal.GetDriverByName('MEM').Create(
        '', xcount, ycount, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform((
        xmin, pixelWidth, 0,
        ymax, 0, pixelHeight,
    ))

    # Create for target raster the same projection as for the value raster
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(raster.GetProjectionRef())
    target_ds.SetProjection(raster_srs.ExportToWkt())

    # Rasterize zone polygon to raster
    gdal.RasterizeLayer(target_ds, [1], lyr, burn_values=[1])

    # Read raster as arrays
    banddataraster = raster.GetRasterBand(1)
    print(banddataraster)
    breakpoint()
    dataraster = banddataraster.ReadAsArray(
        xoff, yoff, xcount, ycount).astype(numpy.float64)
    # dataraster = banddataraster.ReadAsArray().astype(numpy.float64)
    bandmask = target_ds.GetRasterBand(1)
    datamask = bandmask.ReadAsArray(0, 0, xcount, ycount).astype(numpy.float64)

    # Mask zone of raster
    zoneraster = numpy.ma.masked_array(dataraster, numpy.logical_not(datamask))

    # Calculate statistics of zonal raster
    return numpy.average(zoneraster), numpy.mean(zoneraster), numpy.median(zoneraster), numpy.std(zoneraster), numpy.var(zoneraster)


def loop_zonal_stats(input_zone_polygon, input_value_raster):
    # print(input_zone_polygon)
    # print(input_value_raster)

    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()
    featList = range(lyr.GetFeatureCount())
    statDict = {}

    for FID in featList:
        feat = lyr.GetFeature(FID)
        meanValue = zonal_stats(feat, input_zone_polygon, input_value_raster)
        statDict[FID] = meanValue
    return statDict


def execute_process(input_zone_polygon, input_value_raster):
    return loop_zonal_stats(input_zone_polygon, input_value_raster)
