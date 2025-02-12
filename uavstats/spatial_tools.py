import os
import json
import matplotlib.pyplot as plt
from osgeo import ogr, gdal, osr


def read_raster(file_path) -> gdal.Dataset:
    """Reads a GeoTIFF file and returns a dataset

    Args:
        file_path (str): Path to the GeoTIFF file
    """
    ds = gdal.Open(file_path)
    return ds


def crop_raster(raster_dataset: gdal.Dataset, polygon_layer: ogr.Layer) -> gdal.Dataset:
    """_summary_

    Args:
        raster_dataset (gdal.Dataset): Raster dataset
        polygon_layer (ogr.Layer): Polygon layer

    Returns:
        gdal.Dataset: Cropped raster dataset
    """
    # Crop a raster using a polygon in GeoJSON format
    # Open the raster dataset
    raster = raster_dataset

    # Get the extent of the polygon
    polygon_extent = polygon_layer.GetExtent()
    # Get the extent of the raster
    gt = raster.GetGeoTransform()
    width = raster.RasterXSize
    height = raster.RasterYSize
    raster_extent = (gt[0], gt[3] + height * gt[5],
                     gt[0] + width * gt[1], gt[3])
    # Get the intersection of the two extents
    intersection = [max(polygon_extent[0], raster_extent[0]), max(polygon_extent[1], raster_extent[1]),
                    min(polygon_extent[2], raster_extent[2]), min(polygon_extent[3], raster_extent[3])]
    # Get the intersection coordinates
    xmin, ymin, xmax, ymax = intersection
    # Get the geotransform of the raster
    geotransform = raster.GetGeoTransform()
    # Get the resolution of the raster
    xres = geotransform[1]
    yres = geotransform[5]
    # Calculate the number of columns and rows
    cols = int((xmax - xmin) / xres)
    rows = int(abs((ymax - ymin) / yres))  # ! Changed to absolute value
    # Create a new raster dataset
    driver = gdal.GetDriverByName('MEM')
    output = driver.Create('', cols, rows, 1, gdal.GDT_Float32)
    # Set the geotransform
    output.SetGeoTransform((xmin, xres, 0, ymax, 0, yres))
    # Set the projection
    output.SetProjection(raster.GetProjection())
    # Get number of bands
    num_bands = raster.RasterCount
    # Loop through all bands
    for band_num in range(1, num_bands + 1):
        # Read the raster data for each band
        band = raster.GetRasterBand(band_num)
        data = band.ReadAsArray(int(
            (xmin - raster_extent[0]) / xres), int((ymax - raster_extent[3]) / yres), cols, rows)
        # Write the raster data to corresponding band
        output_band = output.GetRasterBand(band_num)
        output_band.WriteArray(data)
    # Return the new raster dataset
    return output


def plot_raster(raster_dataset: gdal.Dataset):
    """Plots a raster dataset

    Args:
        raster_dataset (gdal.Dataset): Raster dataset
    """
    # Get the raster array
    raster_array = raster_dataset.ReadAsArray()
    # Plot the raster array
    plt.imshow(raster_array)
    plt.show()


def write_raster(raster_dataset: gdal.Dataset, output_file: str):
    """Writes a raster dataset to a file

    Args:
        raster_dataset (gdal.Dataset): Raster dataset
        output_file (str): Output file path
    """
    # Get the driver
    driver = gdal.GetDriverByName('GTiff')
    # Create the output raster
    output_raster = driver.CreateCopy(output_file, raster_dataset)
    # Close the output raster
    output_raster = None
