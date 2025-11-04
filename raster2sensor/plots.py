#!/usr/bin/env python
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
import geopandas as gpd
from raster2sensor import config
from raster2sensor.utils import clear, get_file_extension, create_sensorthingsapi_entity, fetch_sensorthingsapi
from raster2sensor.sensorthingsapi import Thing, Location, Datastream
from raster2sensor.logging import get_logger, log_and_print, log_and_raise

logger = get_logger(__name__)


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
        '''Reads Plots File'''
        if not os.path.isfile(self.file_path):
            log_and_raise(
                message=f'{self.file_path} not found', exception_type=FileNotFoundError
            )
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def create_sensorthings_things(self):
        '''Create SensorThingsAPI Things for the Plots
            - Each plot is a Thing
            - Each plot has a Location
            - [Optional] Each plot has one or many Datastreams
        '''
        log_and_print(
            "Creating SensorThingsAPI Things",
            level='info')

        plot_things = []
        for feature in self.read_file().iterfeatures(drop_id=True):
            if self.plot_id_field not in feature['properties']:
                error_msg = f"Plot ID field '{self.plot_id_field}' does not exist in feature properties"
                log_and_print(
                    message=error_msg,
                    level='error'
                )
                raise KeyError(
                    f"Plot ID field '{self.plot_id_field}' does not exist in feature properties")
            plot_id = feature['properties'][self.plot_id_field]
            # If not treatment_id_field, treatment_id is blank
            treatment_id = feature['properties'].get(
                self.treatment_id_field, '') if self.treatment_id_field else ''
            geometry = feature['geometry']
            plot_thing = Thing(
                name=f'Trial Plot - {self.trial_id}-{plot_id} ',
                description=f'Agricultural trial plot {plot_id} belonging to trial {self.trial_id}',
                properties={
                    'trial_id': self.trial_id,
                    'plot_id': plot_id,
                    **({"treatment_id": treatment_id} if treatment_id else {}),
                    'year': self.year,

                },

                Locations=[
                    Location(
                        name=f'Location of Trial Plot - {self.trial_id}-{plot_id}',
                        description=f'Polygon Geometry for Trial Plot - {self.trial_id}-{plot_id}',
                        encodingType='application/geo+json',
                        location={"type": "Feature",
                                  "geometry": geometry,
                                  },
                        properties={
                            'trial_id': self.trial_id,
                            'plot_id': plot_id,
                        }

                    )
                ],
                Datastreams=[
                    # Loop through the Datastreams in the config file
                    Datastream(name=ds.name.format(
                        plot_id=f'{self.trial_id}-{plot_id}'),
                        description=ds.description.format(
                            plot_id=f'{self.trial_id}-{plot_id}'),
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

        # Log clean message for audit trail
        success_msg = f'{len(plot_things)} SensorThingsAPI Things created successfully for trial id: {self.trial_id}'
        log_and_print(
            success_msg,
            level='info'
        )

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
        if not plots_data:
            error_msg = f"No plots found for trial id: '{trial_id}'"
            log_and_print(
                message=error_msg,
                level='error'
            )
            raise ValueError(error_msg)
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

        # If logger.level is DEBUG write the GeoJSON to a file:
        log_and_print(
            f"Writing plots GeoJSON to {config.PARCELS_GEOJSON}", level='info'
        )
        if logger.level == logging.DEBUG:
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
        # Loop through the fetched things
        post_datastreams = []
        for thing in things:
            # Create a new Datastream for each thing
            for ds in datastreams:
                new_datastream = DatastreamAppend(
                    name=ds.name.format(
                        plot_id=f"{thing['properties']['trial_id']}-{thing['properties']['plot_id']}"),
                    description=ds.description.format(
                        plot_id=f"{thing['properties']['trial_id']}-{thing['properties']['plot_id']}"),
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
        log_and_print(
            f"Creating {len(post_datastreams)} new datastreams for field trial '{trial_id}'",
            level='info'
        )
        batch_url = f"{config.SENSOR_THINGS_API_URL}/$batch"

        try:
            # Post the datastreams to the SensorThingsAPI
            response = create_sensorthingsapi_entity(
                batch_url, {'requests': post_datastreams})
            # Raises HTTPError for 4xx/5xx status codes
            response.raise_for_status()
        except Exception as e:
            # Handle both HTTP errors and other exceptions
            error_msg = f"Error creating datastreams for trial '{trial_id}': {str(e)}"
            log_and_print(
                message=error_msg,
                level='error'
            )
            raise

        log_and_print(
            message=f"Successfully created {len(post_datastreams)} new datastreams for field trial '{trial_id}'",
            level='info'
        )

    @staticmethod
    def create_observations(zonal_stats: dict, flight_timestamp: str):
        """Create Observations for each parcel
        Args:
            zonal_stats (dict): Zonal Statistics
            flight_timestamp (str): Flight Timestamp in local timezone

        Raises:
            ValueError: If required data is missing or invalid
            KeyError: If expected keys are not found in zonal_stats
        """
        things = []
        # Validate input parameters
        if not isinstance(zonal_stats, dict):
            log_and_raise(message="zonal_stats must be a dictionary",
                          exception_type=ValueError)

        if not flight_timestamp:
            log_and_raise(message="flight_timestamp cannot be empty",
                          exception_type=ValueError)

        # Extract and validate required fields
        result_time = zonal_stats.get('result_time')
        if not result_time:
            log_and_raise(
                message="Missing 'result_time' in zonal_stats", exception_type=ValueError)

        value = zonal_stats.get('value')
        if not value:
            log_and_raise(message="Missing 'value' in zonal_stats",
                          exception_type=ValueError)

        if not isinstance(value, dict):
            raise ValueError("zonal_stats['value'] must be a dictionary")

        zonal_stats_features = value.get('features')

        if not zonal_stats_features:
            log_and_raise(
                message="Missing 'features' in zonal_stats['value']", exception_type=ValueError)

        raster_data = zonal_stats.get('raster_data')
        if not raster_data:
            log_and_raise(
                message="Missing 'raster_data' in zonal_stats", exception_type=ValueError)
        if not isinstance(raster_data, str):
            raise ValueError("raster_data must be a string")
        raster_data = raster_data.lower()
        # flight_timestamp = datetime.strptime(flight_timestamp, '%Y-%m-%d')

        # Fetch Things + Datastreams
        try:
            things = fetch_sensorthingsapi(
                f"{config.SENSOR_THINGS_API_URL}/Things?$expand=Datastreams")
            if not things:
                error_msg = "No things found in SensorThings API"
                log_and_raise(message=error_msg, exception_type=RuntimeError)
        except Exception as e:
            error_msg = f"Failed to fetch things from SensorThings API: {str(e)}"
            log_and_raise(message=error_msg, exception_type=RuntimeError)

        # Match Datastreams with Zonal Stats
        observations = []
        missing_datastreams = []

        if not isinstance(zonal_stats_features, list):
            raise ValueError("zonal_stats['value']['features'] must be a list")

        for feature in zonal_stats_features:
            iot_id = None  # Initialize to handle error logging
            try:
                # Validate feature structure
                if 'properties' not in feature:
                    logger.warning(f"Feature missing 'properties': {feature}")
                    continue

                if 'iot_id' not in feature['properties']:
                    logger.warning(
                        f"Feature missing 'iot_id' in properties: {feature['properties']}")
                    continue

                iot_id = feature['properties']['iot_id']

                # Find the target Thing and Datastream
                target_thing = [
                    thing for thing in things if thing.get('@iot.id') == iot_id]

                if not target_thing:
                    logger.warning(f"Thing with iot_id {iot_id} not found")
                    continue

                target_datastream = []
                if target_thing and target_thing[0].get('Datastreams'):
                    target_datastream = [
                        datastream for datastream in target_thing[0]['Datastreams']
                        if datastream.get('properties', {}).get('raster_data', '').lower() == raster_data
                    ]

                if not target_datastream:
                    missing_info = f"iot_id: {iot_id}, raster_data: {raster_data}"
                    if missing_info not in missing_datastreams:
                        missing_datastreams.append(missing_info)
                    continue

                # Validate required statistics in feature properties
                required_stats = ['mean', 'min', 'max', 'stddev', 'median']
                missing_stats = [
                    stat for stat in required_stats if stat not in feature['properties']]

                if missing_stats:
                    logger.warning(
                        f"Feature {iot_id} missing statistics: {missing_stats}")
                    continue

                observation = {
                    "phenomenonTime": flight_timestamp,
                    "resultTime": result_time,
                    "result": {
                        "mean": feature['properties']['mean'],
                        "min": feature['properties']['min'],
                        "max": feature['properties']['max'],
                        "stddev": feature['properties']['stddev'],
                        "median": feature['properties']['median']
                    },
                    "Datastream": {"@iot.id": target_datastream[0]['@iot.id']},
                }
                observations.append(observation)

            except Exception as e:
                logger.error(f"Error processing feature {iot_id}: {str(e)}")
                continue

        # Log summary of missing datastreams
        if missing_datastreams:
            warning_msg = f"Datastreams not found for {len(missing_datastreams)} features"
            log_and_print(message=warning_msg, level='warning',
                          )

        # Only proceed if observations length > 0
        if len(observations) < 1:
            warning_msg = "No valid observations to create"
            log_and_print(message=warning_msg, level='warning',
                          )
            return

        info_msg = f"Creating {len(observations)} observations"
        log_and_print(message=info_msg, level='info',
                      )
        batch_request = [{'id': i, 'method': 'post', 'url': 'Observations', 'body': observation}
                         for i, observation in enumerate(observations)]

        try:
            # Post the batched Observations to the SensorThings API
            create_sensorthingsapi_entity(
                f'{config.SENSOR_THINGS_API_URL}/$batch', {'requests': batch_request})
            info_msg = f"Successfully created {len(observations)} observations"
            log_and_print(message=info_msg, level='info',
                          )
        except Exception as e:
            error_msg = f"Failed to create observations: {str(e)}"
            log_and_print(message=error_msg, level='error',
                          )
            raise


if __name__ == "__main__":
    clear()
    # ----- Geotheweg-2024 -----
    plots = Plots(
        file_path=Path('gis_data\\plots_goetheweg-2024.geojson'),
        trial_id='Goetheweg-2024',
        plot_id_field='ID',
        treatment_id_field='',
        year=2024
    )
    # plots.create_sensorthings_things()
    # plots.add_datastreams(
    #     trial_id='Goetheweg-2024',
    #     datastreams=config.ADDITIONAL_DATASTREAMS
    # )

    # ----- Ochsenwasen-2025 -----
    plots = Plots(
        file_path=Path('gis_data\\plots_ochsenwasen-2025.geojson'),
        trial_id='Ochsenwasen-2025',
        plot_id_field='plot_id',
        treatment_id_field='treat_id',
        year=2025
    )
    # plots.create_sensorthings_things()
    plots.fetch_plots_geojson('Ochsenwasen-2025')
