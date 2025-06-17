#!/usr/bin/env python
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import geopandas as gpd
from rich import print
from rich.console import Console
from rich.traceback import install
from uavstats import config
from uavstats.utils import clear, get_file_extension, create_sensorthingsapi_entity, fetch_sensorthingsapi
from uavstats.sensorthingsapi import Thing, Location, Datastream


install(show_locals=True)


@dataclass
class Parcels:
    '''Land Parcels Data Class
    Args:
        file_path (Path): Path to Land Parcels File
        land_parcel_id (str): Land Parcel ID
        field_trial_id (str): Field Trial ID
        treatment_parcel_id_field (str): Parcels ID Field
        project_id (str): Project ID
        year (str): Year
    '''
    file_path: Path
    land_parcel_id: str
    field_trial_id: str
    treatment_parcel_id_field: str
    project_id: str
    year: str = str(datetime.now().year)

    def __post_init__(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not found')
        self.file_extension = get_file_extension(self.file_path)

    def read_file(self) -> gpd.GeoDataFrame:
        '''Reads Land Parcels File'''
        # TODO Check if the file exists, and if it is a valid shapefile or GeoJSON, raise an error if not
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def create_sensorthings_things(self):
        '''Create SensorThingsAPI Things for the Land Parcels
            - Each parcel is a Thing
            - Each parcel has a Location
            - [Optional] Each parcel has one or many Datastreams
        '''
        print('[cyan]Creating SensorThingsAPI Things...')
        for feature in self.read_file().iterfeatures(drop_id=True):
            if self.treatment_parcel_id_field not in feature['properties']:
                raise KeyError(
                    f"Treatment Parcel ID field '{self.treatment_parcel_id_field}' does not exist in feature properties")
            treatment_parcel_id = feature['properties'][self.treatment_parcel_id_field]
            geometry = feature['geometry']
            parcel_thing = Thing(
                name=f'Treatment Parcel - {treatment_parcel_id}',
                description=f'Treatment Parcel - {treatment_parcel_id}',
                properties={
                    'land_parcel_id': self.land_parcel_id,
                    'field_trial_id': self.field_trial_id,
                    'treatment_parcel_id': treatment_parcel_id,
                    'project_id': self.project_id,
                    'year': self.year,

                },
                Locations=[
                    Location(
                        name=f'Location of Treatment Parcel - {
                            treatment_parcel_id}',
                        description=f'Polygon Geometry for Treatment Parcel - {
                            treatment_parcel_id}',
                        encodingType='application/geo+json',
                        location={"type": "Feature",
                                  "geometry": geometry,
                                  "properties": {'land_parcel_id': self.land_parcel_id,
                                                 'field_trial_id': self.field_trial_id,
                                                 'treatment_parcel_id': treatment_parcel_id,
                                                 'year': self.year
                                                 }, },

                    )
                ],
                Datastreams=[
                    # Loop through the Datastreams in the config file
                    Datastream(
                        name=ds['name'].substitute(
                            treatment_parcel_id=treatment_parcel_id),
                        description=ds['description'].substitute(
                            treatment_parcel_id=treatment_parcel_id),
                        observationType=ds.get('observationType'),
                        unitOfMeasurement=ds.get('unitOfMeasurement'),
                        Sensor={"@iot.id": ds.get('Sensor')},
                        ObservedProperty={
                            "@iot.id": ds.get('ObservedProperty')},
                        properties=ds.get('properties', None)
                    ) for ds in config.DATASTREAMS
                ]
            )

            parcel_thing_json = json.dumps(
                asdict(parcel_thing), indent=2, ensure_ascii=True)
            # print(parcel_thing_json)
            things_url = f"{config.SENSOR_THINGS_API_URL}/Things"
            create_sensorthingsapi_entity(
                things_url, parcel_thing_json)
        print('[green]SensorThingsAPI Things created successfully')

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
                    'geometry': parcel['Locations'][0]['location']['geometry'],
                    'properties': {
                        'iot_id': parcel['@iot.id'],
                        'name': parcel['name'],
                        'land_parcel_id': parcel['properties']['land_parcel_id'],
                        'field_trial_id': parcel['properties']['field_trial_id'],
                        'treatment_parcel_id': parcel['properties']['treatment_parcel_id'],
                        'project_id': parcel['properties']['project_id'],
                        'year': parcel['properties']['year']
                    }
                } for parcel in parcels_data
            ]}
        # !DEGUG: write the GeoJSON to a file
        with open(config.PARCELS_GEOJSON, 'w') as f:
            json.dump(parcels_geojson, f, indent=2)
        return parcels_geojson

    def create_additional_datastreams(self, datastreams: list[Datastream]):
        # !TODO Create additional datastreams for each existing parcel
        """Create additional Datastreams for each existing parcel
        Fetch existing parcels from the SensorThingsAPI and create additional Datastreams for each parcel
        Args:
            datastreams (list[Datastream]): List of Datastreams
        """
        pass

    def create_observations(self, zonal_stats: dict, flight_timestamp: str):
        """Create Observations for each parcel
        Args:
            zonal_stats (dict): Zonal Statistics
            flight_timestamp (str): Flight Timestamp in local timezone
        """
        result_time = zonal_stats.get('result_time')
        zonal_stats_features = (zonal_stats.get('value')).get('features')
        raster_data = (zonal_stats.get('raster_data')).lower()
        # flight_timestamp = datetime.strptime(flight_timestamp, '%Y-%m-%d')

        # Fetch Things + Datastreams
        things = fetch_sensorthingsapi(
            f"{config.SENSOR_THINGS_API_URL}/Things?$expand=Datastreams")

        # Match Datastreams with Zonal Stats
        observations = []
        for feature in zonal_stats_features:
            iot_id = feature['properties']['iot_id']
            # Find the target thing and datastream
            target_thing = [
                thing for thing in things if thing['@iot.id'] == iot_id]
            target_datastream = [datastream for datastream in target_thing[0]['Datastreams'] if (
                datastream['properties']['raster_data']).lower() == raster_data]
            # print(f"[cyan]Zonal Stats Polygon:")
            # print(feature)
            # print(f"[cyan]Target Thing:")
            # print(target_thing[0])
            # print(f"[cyan]Target Datastream:")
            # print(target_datastream[0])

            # # Europe/Berlin timezone for the flight date
            # flight_timestamp = flight_timestamp.replace(
            #     tzinfo=timezone(timedelta(hours=1)))
            observation = {
                "phenomenonTime": flight_timestamp,
                "resultTime": result_time,
                "result": {"mean": feature['properties']['mean'],
                           "min": feature['properties']['min'],
                           "max": feature['properties']['max'],
                           "stddev": feature['properties']['stddev'],
                           "median": "feature['properties']['median']"},
                "Datastream": {"@iot.id": target_datastream[0]['@iot.id']},

            }

            observations.append(observation)

        batch_request = [{'id': i, 'method': 'post', 'url': 'Observations', 'body': observation}
                         for i, observation in enumerate(observations)]
        # Post the observation to the SensorThings API
        create_sensorthingsapi_entity(
            f'{config.SENSOR_THINGS_API_URL}/$batch', json.dumps({'requests': batch_request}))

        #                 # Post the observation to the SensorThings API
        #                 observations_url = f"{config.SENSOR_THINGS_API_URL}/Observations"
        #                 create_sensorthingsapi_entity(
        #                     observations_url, json.dumps(observation))
        #                 print(
        #                     f"Observation created for datastream {target_datastream['@iot.id']}")


if __name__ == "__main__":
    clear()
    parcels = Parcels(
        file_path=config.LAND_PARCELS_FILE,
        land_parcel_id='1',
        field_trial_id='FAIRagro UC6',
        treatment_parcel_id_field=config.TREATMENT_PARCELS_ID_FIELD,
        project_id=config.PROJECT_ID
    )
    features = parcels.read_file()
    # print(features)
    # parcels.create_sensorthings_things()
    # parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)
    # print(parcels_geojson)
