#!/usr/bin/env python
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
import geopandas as gpd
from rich import print
from rich.console import Console
from rich.traceback import install
from uavstats import config
from uavstats.utils import clear, get_file_extension, create_sensorthingsapi_thing, fetch_sensorthingsapi
from uavstats.sensorthingsapi import Thing, Location, Datastream


install(show_locals=True)
console = Console()


@dataclass
class Parcels:
    '''Land Parcels Data Class
    Args:
        file_path (Path): Path to Land Parcels File
        id_field (str): Parcels ID Field
        project_id (str): Project ID
    '''
    file_path: Path
    id_field: str
    project_id: str

    def __post_init__(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not found')
        self.file_extension = get_file_extension(self.file_path)

    def read_file(self) -> gpd.GeoDataFrame:
        '''Reads Land Parcels File'''
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def create_sensorthings_things(self):
        '''Create SensorThingsAPI Things for the Land Parcels
            - Each parcel is a Thing
            - Each parcel has a Location
            - [Optional] Each parcel has one or many Datastreams
        '''
        for feature in self.read_file().iterfeatures(drop_id=True):
            if self.id_field not in feature['properties']:
                raise KeyError(
                    f"Parcel ID field '{self.id_field}' does not exist in feature properties")
            parcel_id = feature['properties'][self.id_field]
            geometry = feature['geometry']
            parcel_thing = Thing(
                name=f'Land Parcel - {parcel_id}',
                description=f'Land Parcel - {parcel_id}',
                properties={
                    'project_id': self.project_id,
                    'parcel_id': parcel_id
                },
                Locations=[
                    Location(
                        name=f'Location of Parcel - {parcel_id}',
                        description=f'Polygon Geometry for Parcel - {
                            parcel_id}',
                        encodingType='application/geo+json',
                        location=geometry
                    )
                ],
                Datastreams=[
                    # Loop through the Datastreams in the config file
                    Datastream(
                        name=ds['name'].substitute(parcel_id=parcel_id),
                        description=ds['description'].substitute(
                            parcel_id=parcel_id),
                        observationType=ds['observationType'],
                        unitOfMeasurement=ds['unitOfMeasurement'],
                        Sensor={"@iot.id": ds['Sensor']},
                        ObservedProperty={"@iot.id": ds['ObservedProperty']}
                    ) for ds in config.DATASTREAMS
                ]
            )

            parcel_thing_json = json.dumps(
                asdict(parcel_thing), indent=2, ensure_ascii=True)
            # print(parcel_thing_json)
            things_url = f"{config.SENSOR_THINGS_API_URL}/Things"
            create_sensorthingsapi_thing(
                things_url, parcel_thing_json)

    @staticmethod
    def fetch_parcels_geojson(project_id: str) -> dict:
        '''Fetch Parcels GeoJSON from SensorThingsAPI
        Args:
            project_id (str): Project ID
        Returns:
            parcels_geojson (dict): Parcels GeoJSON
        '''
        parcels_url = f"{config.SENSOR_THINGS_API_URL}/Things?$filter=properties/project_id eq '{
            project_id}'&$expand=Locations($select=location)"
        parcels_data = fetch_sensorthingsapi(parcels_url)
        # convert the fetched data to a GeoJSON
        parcels_geojson = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': parcel['Locations'][0]['location'],
                    'properties': {
                        'iot_id': parcel['@iot.id'],
                        'parcel_id': parcel['properties']['parcel_id'],
                        'project_id': parcel['properties']['project_id'],
                        'name': parcel['name'],
                    }
                } for parcel in parcels_data
            ]}
        # !DEGUG: write the GeoJSON to a file
        with open(config.PARCELS_GEOJSON, 'w') as f:
            json.dump(parcels_geojson, f, indent=2)
        return parcels_geojson


if __name__ == "__main__":
    clear()
    parcels = Parcels(
        file_path=config.LAND_PARCELS_FILE,
        id_field=config.LAND_PARCELS_ID_FIELD,
        project_id=config.PROJECT_ID
    )
    features = parcels.read_file()
    print(features)
    # parcels.create_sensorthings_things()
    parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)
    # print(parcels_geojson)
