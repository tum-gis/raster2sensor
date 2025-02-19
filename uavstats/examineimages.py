import os
from osgeo import gdal
from rich import print


def clear():
    '''Clears Console'''
    os.system('cls' if os.name == 'nt' else 'clear')


def main(image_path):
    # Open the multispectral raster
    dataset = gdal.Open(image_path)

    # Get number of bands
    num_bands = dataset.RasterCount
    print(f"Number of Bands: {num_bands}")

    # List band descriptions
    for i in range(1, num_bands + 1):
        band = dataset.GetRasterBand(i)
        print(f"Band {i}: Data Type = {gdal.GetDataTypeName(band.DataType)}")


if __name__ == "__main__":
    clear()
    main("gis_data/dop20_rgb.tif")
