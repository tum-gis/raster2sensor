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
class Plots:
    '''Plots Data Class
    Args:
        file_path (Path): Path to Plots File
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
        '''Reads Land Plots File'''
        # TODO Check if the file exists, and if it is a valid shapefile or GeoJSON, raise an error if not
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def create_sensorthings_things(self):
        '''Create SensorThingsAPI Things for the Land Plots
            - Each parcel is a Thing
            - Each parcel has a Location
            - [Optional] Each parcel has one or many Datastreams
        '''
        print('[cyan]Creating SensorThingsAPI Things...')
        plot_things = []
        for feature in self.read_file().iterfeatures(drop_id=True):
            if self.plot_id_field not in feature['properties']:
                raise KeyError(
                    f"Plot ID field '{self.plot_id_field}' does not exist in feature properties")
            plot_id = feature['properties'][self.plot_id_field]
            # If not treatment_id_field, treatment_id is blank
            treatment_id = feature['properties'].get(
                self.treatment_id_field, '') if self.treatment_id_field else ''
            geometry = feature['geometry']
            plot_thing = Thing(
                name=f'Plot - {plot_id}',
                description=f'Plot: {plot_id}' + (
                    f' (Treatment: {treatment_id})' if treatment_id else f''),
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
            plot_things.append(asdict(plot_thing))

        batch_request = [{'id': i, 'method': 'post', 'url': 'Things', 'body': thing}
                         for i, thing in enumerate(plot_things)]
        create_sensorthingsapi_entity(
            f'{config.SENSOR_THINGS_API_URL}/$batch', {'requests': batch_request})
        print('[green]SensorThingsAPI Things created successfully')

    @staticmethod
    def fetch_plots_geojson(trial_id: str) -> dict:
        '''Fetch Plots GeoJSON from SensorThingsAPI
        Args:
            trial_id (str): Trial ID (Location-Year)
        Returns:
            plots_geojson (dict): Plots GeoJSON
        '''
        plots_url = f"{config.SENSOR_THINGS_API_URL}/Things?$filter=properties/trial_id eq '{trial_id}'&$expand=Locations($select=location)"
        plots_data = fetch_sensorthingsapi(plots_url)
        # convert the fetched data to a GeoJSON
        plots_geojson = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': plot['Locations'][0]['location']['geometry'],
                    'properties': {
                        'iot_id': plot.get('@iot.id'),
                        'name': plot.get('name'),
                        'trial_id': plot.get('properties', {}).get('trial_id'),
                        'plot_id': plot.get('properties', {}).get('plot_id'),
                        'treatment_id': plot.get('properties', {}).get('treatment_id'),
                        'year': plot.get('properties', {}).get('year')
                    }
                } for plot in plots_data
            ]}
        # !DEGUG: write the GeoJSON to a file
        with open(config.PARCELS_GEOJSON, 'w') as f:
            json.dump(plots_geojson, f, indent=2)
        return plots_geojson

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
            batch_url, {'requests': post_datastreams})
        if response.status_code != 200:
            print(f"[red]Failed to create datastreams: {response.status_code}")
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
            # Find the target Thing and Datastream
            target_thing = [
                thing for thing in things if thing['@iot.id'] == iot_id]
            target_datastream = []
            if target_thing:
                target_datastream = [datastream for datastream in target_thing[0]['Datastreams'] if (
                    datastream['properties']['raster_data']).lower() == raster_data]
            if not target_datastream:
                print(
                    f"[yellow]Datastream {raster_data} not found for iot_id {iot_id}[/yellow]")
                continue
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

        # Only proceed if observations length > 1
        if len(observations) < 1:
            print("[yellow]No observations to create[/yellow]")
            return
        batch_request = [{'id': i, 'method': 'post', 'url': 'Observations', 'body': observation}
                         for i, observation in enumerate(observations)]
        # Post the batched Observations to the SensorThings API
        create_sensorthingsapi_entity(
            f'{config.SENSOR_THINGS_API_URL}/$batch', {'requests': batch_request})

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
    plots = Plots(
        file_path=Path('gis_data\\plots_goetheweg-2024.geojson'),
        trial_id='Goetheweg-2024',
        plot_id_field='ID',
        treatment_id_field='',
        year=2024
    )
    # features = parcels.read_file()
    # print(features)
    # plots_geojson = Plots.fetch_parcels_geojson(config.PROJECT_ID)
    # print(plots_geojson)
    plots.create_sensorthings_things()
    # plots.add_datastreams(
    #     trial_id='Goetheweg-2024',
    #     datastreams=config.ADDITIONAL_DATASTREAMS
    # )
