import os
import base64
from rich import print
from math import radians, cos
import matplotlib.pyplot as plt
from osgeo import ogr, gdal


def read_raster(file_path: str) -> gdal.Dataset:
    """Reads a GeoTIFF file and returns a dataset

    Args:
        file_path (str): Path to the GeoTIFF file
    """
    # Get name from file path
    print(f"[cyan] Processing Raster: {os.path.basename(file_path)}")
    ds = gdal.Open(file_path)
    return ds


def apply_buffer_to_extent(extent: tuple, buffer_distance_meters: int = 2) -> tuple:
    """Apply buffer to extent in meters

    Args:
        extent (tuple): Extent as (xmin, xmax, ymin, ymax)
        buffer_distance_meters (float): Buffer distance in meters

    Returns:
        tuple: Buffered extent as (xmin, xmax, ymin, ymax)
    """
    xmin, xmax, ymin, ymax = extent

    # Convert meters to degrees for latitude
    buffer_distance_lat = buffer_distance_meters / \
        111320  # 1 degree latitude ~ 111.32 km
    # Convert meters to degrees for longitude
    buffer_distance_lon = buffer_distance_meters / \
        (111320 * cos(radians((ymin + ymax) / 2)))

    xmin -= buffer_distance_lon
    xmax += buffer_distance_lon
    ymin -= buffer_distance_lat
    ymax += buffer_distance_lat

    return xmin, xmax, ymin, ymax


def clip_raster(raster_dataset: gdal.Dataset, polygon_layer: ogr.Layer) -> gdal.Dataset:
    """Clip a raster using a polygon

    Args:
        raster_dataset (gdal.Dataset): Raster dataset
        polygon_layer (ogr.Layer): Polygon layer

    Returns:
        gdal.Dataset: Cropped raster dataset
    """

    # Get the extent of the polygon
    polygon_extent = polygon_layer.GetExtent()

    # Apply buffer to polygon extent
    xmin, xmax, ymin, ymax = apply_buffer_to_extent(polygon_extent, 2)

    # Get raster projection
    raster_dataset_srs = raster_dataset.GetProjection()
    polygon_layer_srs = polygon_layer.GetSpatialRef()

    # TODO always reproject the rasters to match the vector CRS (4326)
    # Reproject raster if needed
    if polygon_layer_srs and polygon_layer_srs.ExportToWkt() != raster_dataset_srs:
        print("Reprojecting raster to match vector CRS...")
        reprojected_ds = gdal.Warp('', raster_dataset, format='MEM',
                                   dstSRS=polygon_layer_srs.ExportToWkt())
        raster_dataset = reprojected_ds

    clipped_ds = gdal.Translate("clipped_ds.tif", raster_dataset, projWin=[
                                xmin, ymax, xmax, ymin])

    # Close input datasets
    raster_dataset = None
    polygon_layer = None
    # TODO : Logger debug & error messages
    if clipped_ds:
        print("[green]✅ Clipping successful, returning GDAL dataset.")
    else:
        print("[red]❌ Clipping failed.")

    return clipped_ds  # Return in-memory GDAL dataset


def plot_raster(raster_dataset: gdal.Dataset):
    """Plots a raster dataset

    Args:
        raster_dataset (gdal.Dataset): Raster dataset
    """
    # Get the raster array
    if raster_dataset is None:
        print("❌ Invalid raster dataset.")
        return

    raster_array = raster_dataset.ReadAsArray()
    # TODO Handle multispectral images with more than 3 bands
    # Check if the raster is multiband
    if len(raster_array.shape) == 3:
        # Multiband image
        raster_array = raster_array.transpose(
            (1, 2, 0))  # Reorder dimensions for plotting
        plt.imshow(raster_array)
    else:
        # Single band image
        plt.imshow(raster_array, cmap='gray')

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
    output_raster = None


def encode_raster_to_base64(raster_dataset: gdal.Dataset) -> str:
    """Encodes a raster dataset to base64

    Args:
        raster_dataset (gdal.Dataset): Raster dataset

    Returns:
        str: Base64 encoded raster
    """
    # Retrieve the GeoTIFF driver
    mem_driver = gdal.GetDriverByName("GTiff")  # GeoTIFF format

    # Create an in-memory raster
    mem_driver.CreateCopy(
        '/vsimem/temp.tif', raster_dataset, options=["COMPRESS=LZW"])

    # Read the in-memory file into a byte stream
    mem_tiff = gdal.VSIFOpenL('/vsimem/temp.tif', 'rb')
    mem_tiff_stat = gdal.VSIStatL('/vsimem/temp.tif')
    mem_tiff_size = mem_tiff_stat.size
    mem_tiff_data = gdal.VSIFReadL(1, mem_tiff_size, mem_tiff)
    gdal.VSIFCloseL(mem_tiff)

    # Encode the in-memory file to base64
    base64_encoded = base64.b64encode(mem_tiff_data).decode('utf-8')

    return base64_encoded


def decode_base64_to_raster(base64_encoded: str) -> gdal.Dataset:
    """Decode a base64 encoded raster to a GDAL dataset
    """
    # Decode the base64 string
    decoded_data = base64.b64decode(base64_encoded.encode('utf-8'))

    # Write the decoded data to a temporary file using GDAL's virtual file system
    gdal.FileFromMemBuffer('/vsimem/temp.tif', decoded_data)

    # Open the temporary file as a GDAL dataset
    decoded_raster = gdal.Open('/vsimem/temp.tif')

    return decoded_raster
