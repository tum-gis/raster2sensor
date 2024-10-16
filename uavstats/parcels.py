#!/usr/bin/env python
import os
import sys
from pathlib import Path
from dataclasses import dataclass
import geopandas as gpd
from rich import print
from rich.console import Console
from rich.traceback import install
from uavstats import config
from uavstats.utils import clear, timeit, get_file_name, get_file_extension, get_files

install(show_locals=True)
console = Console()


@dataclass
class Parcels:
    '''Land Parcels Data Class'''
    file_path: Path
    id_field: str
    project_id: str

    def __post_init__(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not found')
        self.file_extension = get_file_extension(self.file_path)

    def read_file(self):
        '''Reads Land Parcels File'''
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def get_features(self):
        '''Get Features'''
        # return self.read_file().to_dict(orient='records')
        return self.read_file()

    def loop_features(self):
        '''Loop Features'''
        for feature in self.get_features().iterfeatures(drop_id=True):
            if self.id_field not in feature['properties']:
                raise KeyError(
                    f"Parcel ID '{self.id_field}' not found in feature properties")
            feature_id = feature['properties'][self.id_field]
            geometry = feature['geometry']
            print(f'[yellow] {feature_id}')
            print(feature)


if __name__ == "__main__":
    clear()
    parcels = Parcels(
        file_path=config.LAND_PARCELS_FILE,
        id_field=config.LAND_PARCELS_ID_FIELD,
        project_id=config.PROJECT_ID
    )
    # features = parcels.get_features()
    # print(features)
    parcels.loop_features()
