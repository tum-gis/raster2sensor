#!/usr/bin/env python
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
import sys
from typing import Optional
import geopandas as gpd
from raster2sensor import config
from raster2sensor.utils import clear, get_file_extension, create_sensorthingsapi_entity, fetch_sensorthingsapi
from raster2sensor.sensorthingsapi import Thing, Location, Datastream
from raster2sensor.spatialtools import convert_geometry_to_geojson
from raster2sensor.logging import get_logger

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
        datastreams (list[Datastream]): Datastreams to use for creating Things
    '''
    file_path: Path
    trial_id: str
    plot_id_field: str
    treatment_id_field: str
    year: int = field(default_factory=lambda: (datetime.now().year))
    datastreams: list[Datastream] = field(default_factory=list)

    def __post_init__(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not found')
        self.file_extension = get_file_extension(self.file_path)

    def read_file(self) -> gpd.GeoDataFrame:
        '''Reads Plots File'''
        if not os.path.isfile(self.file_path):
            error_msg = f'{self.file_path} not found'
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        driver = 'ESRI Shapefile' if self.file_extension == '.shp' else 'GeoJSON'
        return gpd.read_file(self.file_path, driver=driver)

    def create_sensorthings_things(self):
        '''Create SensorThingsAPI Things for the Plots
            - Each plot is a Thing
            - Each plot has a Location
            - [Optional] Each plot has one or many Datastreams
        '''
        logger.info(
            "Creating SensorThingsAPI Things"
        )

        plot_things = []
        for feature in self.read_file().iterfeatures(drop_id=True):
            # logger.debug(feature)
            # breakpoint()
            if self.plot_id_field not in feature['properties']:
                error_msg = f"Plot ID field '{self.plot_id_field}' does not exist in feature properties"
                logger.error(error_msg)
                raise KeyError(error_msg)
            plot_id = feature['properties'][self.plot_id_field]
            # If not treatment_id_field, treatment_id is blank
            treatment_id = feature['properties'].get(
                self.treatment_id_field, '') if self.treatment_id_field else ''
            geometry = feature['geometry']
            # Convert geometry to proper GeoJSON format (tuples to lists)
            geojson_geometry = convert_geometry_to_geojson(geometry)
            # logger.debug(geojson_geometry)
            # breakpoint()
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
                    # Loop through the provided datastreams
                    Datastream(name=ds.name.format(
                        plot_id=f'{self.trial_id}-{plot_id}'),
                        description=ds.description.format(
                            plot_id=f'{self.trial_id}-{plot_id}'),
                        observationType=ds.observationType,
                        unitOfMeasurement=ds.unitOfMeasurement,
                        Sensor=ds.Sensor,
                        ObservedProperty=ds.ObservedProperty,
                        properties=ds.properties
                    ) for ds in self.datastreams
                ]
            )
            plot_things.append(asdict(plot_thing))
        # logger.debug(plot_things)
        batch_request = [{'id': i, 'method': 'post', 'url': 'Things', 'body': thing}
                         for i, thing in enumerate(plot_things)]
        create_sensorthingsapi_entity(
            f'{config.SENSOR_THINGS_API_URL}/$batch', {'requests': batch_request})

        # Log clean message for audit trail
        success_msg = f'{len(plot_things)} SensorThingsAPI Things created successfully for trial id: {self.trial_id}'
        logger.info(success_msg)

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
            # log_and_raise(
            #     message=error_msg,
            #     exception_type=ValueError,
            #     # level='error'
            # )
            logger.error(error_msg)
            sys.exit(1)
        else:
            logger.info(
                f"Fetched {len(plots_data)} plots for trial id: '{trial_id}'")
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
        if logger.level <= logging.DEBUG:
            logger.debug(
                f"Writing plots GeoJSON to {config.PLOTS_GEOJSON}"
            )
            with open(config.PLOTS_GEOJSON, 'w') as f:
                json.dump(plots_geojson, f, indent=2)
        return plots_geojson

    @staticmethod
    def add_datastreams(trial_id, datastreams: list[Datastream]):
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
        logger.info(
            f"Creating {len(post_datastreams)} new datastreams for field trial '{trial_id}'"
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
            logger.error(error_msg)
            raise

        logger.info(
            f"Successfully created {len(post_datastreams)} new datastreams for field trial '{trial_id}'"
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
            error_msg = "zonal_stats must be a dictionary"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not flight_timestamp:
            error_msg = "flight_timestamp cannot be empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Extract and validate required fields
        result_time = zonal_stats.get('result_time')
        if not result_time:
            error_msg = "Missing 'result_time' in zonal_stats"
            logger.error(error_msg)
            raise ValueError(error_msg)

        value = zonal_stats.get('value')
        if not value:
            error_msg = "Missing 'value' in zonal_stats"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not isinstance(value, dict):
            error_msg = "zonal_stats['value'] must be a dictionary"
            logger.error(error_msg)
            raise ValueError(error_msg)

        zonal_stats_features = value.get('features')

        if not zonal_stats_features:
            error_msg = "Missing 'features' in zonal_stats['value']"
            logger.error(error_msg)
            raise ValueError(error_msg)

        raster_data = zonal_stats.get('raster_data')
        if not raster_data:
            error_msg = "Missing 'raster_data' in zonal_stats"
            logger.error(error_msg)
            raise ValueError(error_msg)
        if not isinstance(raster_data, str):
            error_msg = "raster_data must be a string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        raster_data = raster_data.lower()
        # flight_timestamp = datetime.strptime(flight_timestamp, '%Y-%m-%d')

        # Fetch Things + Datastreams
        try:
            things = fetch_sensorthingsapi(
                f"{config.SENSOR_THINGS_API_URL}/Things?$expand=Datastreams")
            if not things:
                error_msg = "No things found in SensorThings API"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Failed to fetch things from SensorThings API: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

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
            logger.warning(warning_msg)

        # Only proceed if observations length > 0
        if len(observations) < 1:
            warning_msg = "No valid observations to create"
            logger.warning(warning_msg)
            return

        info_msg = f"Creating {len(observations)} observations"
        logger.info(info_msg)
        batch_request = [{'id': i, 'method': 'post', 'url': 'Observations', 'body': observation}
                         for i, observation in enumerate(observations)]

        try:
            # Post the batched Observations to the SensorThings API
            create_sensorthingsapi_entity(
                f'{config.SENSOR_THINGS_API_URL}/$batch', {'requests': batch_request})
            info_msg = f"Successfully created {len(observations)} observations"
            logger.info(info_msg)
        except Exception as e:
            error_msg = f"Failed to create observations: {str(e)}"
            logger.error(error_msg)
            raise


if __name__ == "__main__":
    clear()
    # # ----- Geotheweg-2024 -----
    # plots = Plots(
    #     file_path=Path('data\\plots_goetheweg-2024.geojson'),
    #     trial_id='Goetheweg-2024',
    #     plot_id_field='ID',
    #     treatment_id_field='',
    #     year=2024,
    #     datastreams=config.DATASTREAMS
    # )
    # plots.create_sensorthings_things()
    # plots.add_datastreams(
    #     trial_id='Goetheweg-2024',
    #     datastreams=config.ADDITIONAL_DATASTREAMS
    # )

    # ----- Ochsenwasen-2025 -----
    plots = Plots(
        file_path=Path('data\\plots_ochsenwasen-2025.geojson'),
        trial_id='Ochsenwasen-2025',
        plot_id_field='plot_id',
        treatment_id_field='treat_id',
        year=2025,
        datastreams=config.DATASTREAMS
    )
    plots.create_sensorthings_things()
    # plots.fetch_plots_geojson('Ochsenwasen-2025')
