#!/usr/bin/env python
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
import geopandas as gpd
from rich import print
from rich.console import Console
from rich.traceback import install
from uavstats import config
from uavstats.utils import clear, get_file_extension, create_sensorthingsapi_entity, fetch_sensorthingsapi
from uavstats.sensorthingsapi import Thing, Location, Datastream


install(show_locals=True)


@dataclass
class DatastreamAppend(Datastream):
    Thing: Optional[dict[str, int]] = None


@dataclass
class Parcels:
    '''Land Parcels Data Class
    Args:
        file_path (Path): Path to Land Parcels File
        trial_id (str): Field Trial ID
        plot_id_field (str): Plot ID Field
        treatment_id_field (str): Treatment ID Field
        year (int): Year
    '''
    file_path: Path
    trial_id: str
    plot_id_field: str
    treatment_id_field: str
    year: int = field(default_factory=lambda: (datetime.now().year))

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
            if self.plot_id_field not in feature['properties']:
                raise KeyError(
                    f"Treatment Plot ID field '{self.plot_id_field}' does not exist in feature properties")
            plot_id = feature['properties'][self.plot_id_field]
            # If not treatment_id_field, treatment_id is blank
            treatment_id = feature['properties'].get(
                self.treatment_id_field, '') if self.treatment_id_field else ''
            geometry = feature['geometry']
            parcel_thing = Thing(
                name=f'Treatment Plot - {plot_id}',
                description=f'Treatment Plot - {plot_id}',
                properties={
                    'trial_id': self.trial_id,
                    'plot_id': plot_id,
                    'treatment_id': treatment_id,
                    'year': self.year,

                },
                Locations=[
                    Location(
                        name=f'Location of Plot - {plot_id}',
                        description=f'Polygon Geometry for Plot - {plot_id}',
                        encodingType='application/geo+json',
                        location={"type": "Feature",
                                  "geometry": geometry,
                                  "properties": {
                                      'trial_id': self.trial_id,
                                      'plot_id': plot_id,
                                      'treatment_id': treatment_id,
                                      'year': self.year
                                  }, },

                    )
                ],
                Datastreams=[
                    # Loop through the Datastreams in the config file
                    Datastream(name=ds.name.format(
                        plot_id=plot_id),
                        description=ds.description.format(
                            plot_id=plot_id),
                        observationType=ds.observationType,
                        unitOfMeasurement=ds.unitOfMeasurement,
                        Sensor=ds.Sensor,
                        ObservedProperty=ds.ObservedProperty,
                        properties=ds.properties
                    ) for ds in config.DATASTREAMS
                ]
            )

            parcel_thing_dict = asdict(parcel_thing)
            # print(json.dumps(parcel_thing_dict, indent=2, ensure_ascii=True))
            things_url = f"{config.SENSOR_THINGS_API_URL}/Things"

            create_sensorthingsapi_entity(
                things_url, parcel_thing_dict)
        print('[green]SensorThingsAPI Things created successfully')

    @staticmethod
    def fetch_parcels_geojson(trial_id: str) -> dict:
        '''Fetch Parcels GeoJSON from SensorThingsAPI
        Args:
            trial_id (str): Trial ID (Location-Year)
        Returns:
            parcels_geojson (dict): Parcels GeoJSON
        '''
        parcels_url = f"{config.SENSOR_THINGS_API_URL}/Things?$filter=properties/trial_id eq '{
            trial_id}'&$expand=Locations($select=location)"
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
                        'trial_id': parcel['properties']['trial_id'],
                        'plot_id': parcel['properties']['plot_id'],
                        'treatment_id': parcel['properties']['treatment_id'],
                        'year': parcel['properties']['year']
                    }
                } for parcel in parcels_data
            ]}
        # !DEGUG: write the GeoJSON to a file
        with open(config.PARCELS_GEOJSON, 'w') as f:
            json.dump(parcels_geojson, f, indent=2)
        return parcels_geojson

    def add_datastreams(self, trial_id, datastreams: list[Datastream]):
        # !TODO Create additional datastreams for each existing parcel
        """Create additional Datastreams for each existing parcel
        Fetch existing parcels from the SensorThingsAPI and create additional Datastreams for each parcel
        Args:
            datastreams (list[Datastream]): List of Datastreams
        """
        # Fetch all things where trial_id matches

        things = fetch_sensorthingsapi(
            f"{config.SENSOR_THINGS_API_URL}/Things?$filter=startswith(properties/trial_id,%27{trial_id}%27)")
        print(
            f"[cyan]Fetched {len(things)} things for trial id: '{trial_id}'")
        # Loop through the fetched things
        post_datastreams = []
        for thing in things:
            # Create a new Datastream for each thing
            for ds in datastreams:
                new_datastream = DatastreamAppend(
                    name=ds.name.format(
                        plot_id=thing['properties']['plot_id']),
                    description=ds.description.format(
                        plot_id=thing['properties']['plot_id']),
                    observationType=ds.observationType,
                    unitOfMeasurement=ds.unitOfMeasurement,
                    Sensor=ds.Sensor,
                    ObservedProperty=ds.ObservedProperty,
                    properties=ds.properties,
                    # Associate with the Thing
                    Thing={"@iot.id": thing['@iot.id']}
                )

                batch_request = {
                    "id": len(post_datastreams)+1,
                    "method": "post",
                    "url": "Datastreams",
                    "body": asdict(new_datastream)
                }
                post_datastreams.append(batch_request)

                # datastream_json = json.dumps(
                #     asdict(new_datastream), indent=2, ensure_ascii=True)
                # datastreams_url = f"{config.SENSOR_THINGS_API_URL}/Datastreams"
                # create_sensorthingsapi_entity(datastreams_url, datastream_json)
        print(
            f"[cyan]Creating {len(post_datastreams)} new datastreams for field trial '{trial_id}'")
        batch_url = f"{config.SENSOR_THINGS_API_URL}/$batch"
        # Post the datastreams to the SensorThingsAPI
        response = create_sensorthingsapi_entity(
            batch_url, json.dumps({'requests': post_datastreams}))
        if response != 200:
            print(f"[red]Failed to create datastreams: {response.text}")
            return

        print(
            f"[green]Successfully created {len(post_datastreams)} new datastreams for field trial '{trial_id}'")

    @staticmethod
    def create_observations(zonal_stats: dict, flight_timestamp: str):
        """Create Observations for each parcel
        Args:
            zonal_stats (dict): Zonal Statistics
            flight_timestamp (str): Flight Timestamp in local timezone
        """
        result_time = zonal_stats.get('result_time')
        value = zonal_stats.get('value')
        if value is not None:
            zonal_stats_features = value.get('features')
        else:
            raise ValueError("zonal_stats['value'] is missing or None")
        raster_data = zonal_stats.get('raster_data')
        if raster_data is not None:
            raster_data = raster_data.lower()
        else:
            raise ValueError("zonal_stats['raster_data'] is missing or None")
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
                           "median": feature['properties']['median']},
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
    if config.TREATMENT_PARCELS_ID_FIELD is None:
        raise ValueError("TREATMENT_PARCELS_ID_FIELD must be set in config")
    if config.PROJECT_ID is None:
        raise ValueError("PROJECT_ID must be set in config")
    parcels = Parcels(
        file_path=Path(config.LAND_PARCELS_FILE),
        trial_id='Goetheweg-2024',
        plot_id_field=config.TREATMENT_PARCELS_ID_FIELD,
        treatment_id_field=config.PROJECT_ID,
        year=2024
    )
    # features = parcels.read_file()
    # print(features)
    # parcels_geojson = Parcels.fetch_parcels_geojson(config.PROJECT_ID)
    # print(parcels_geojson)
    # parcels.create_sensorthings_things()
    # parcels.add_datastreams(
    #     trial_id='FAIRagro UC6',
    #     datastreams=config.ADDITIONAL_DATASTREAMS
    # )
