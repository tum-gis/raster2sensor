# tests/test_uavstats.py

from typer.testing import CliRunner
from dataclasses import asdict
from uavstats.sensorthingsapi import Thing, Location, UnitOfMeasurement, Datastream

runner = CliRunner()

test_case = {
    "name": "Kitchen",
    "description": "The Kitchen in my house",
    "properties": {
        "oven": True,
        "heatingPlates": 4
    },
    "Locations": [
        {
            "name": "Location of the kitchen",
            "description": "This is where the kitchen is",
            "encodingType": "application/geo+json",
            "location": {
                "type": "Point",
                "coordinates": [8.438889, 44.27253]
            }
        }
    ],
    "Datastreams": [
        {
            "name": "Temperature in the Kitchen",
            "description": "The temperature in the kitchen, measured by the sensor next to the window",
            "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
            "unitOfMeasurement": {
                "name": "Degree Celsius",
                "symbol": "°C",
                "definition": "ucum:Cel"
            },
            "Sensor": {"@iot.id": 5},
            "ObservedProperty": {"@iot.id": 1}
        }, {
            "name": "Humidity in the Kitchen",
            "description": "The relative humidity in the kitchen, measured by the sensor next to the window",
            "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
            "unitOfMeasurement": {
                "name": "Percent",
                "symbol": "%",
                "definition": "ucum:%"
            },
            "Sensor": {"@iot.id": 5},
            "ObservedProperty": {"@iot.id": 1}
        }
    ]
}


def test_version():
    # Example usage:
    thing = Thing(
        name="Kitchen",
        description="The Kitchen in my house",
        properties={"oven": True, "heatingPlates": 4},
        Locations=[
            Location(
                name="Location of the kitchen",
                description="This is where the kitchen is",
                encodingType="application/geo+json",
                location={"type": "Point", "coordinates": [8.438889, 44.27253]}
            )
        ],
        Datastreams=[
            Datastream(
                name="Temperature in the Kitchen",
                description="The temperature in the kitchen, measured by the sensor next to the window",
                observationType="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                unitOfMeasurement=UnitOfMeasurement(
                    name="Degree Celsius",
                    symbol="°C",
                    definition="ucum:Cel"
                ),
                Sensor={"@iot.id": 5},
                ObservedProperty={"@iot.id": 1}
            ),
            Datastream(
                name="Humidity in the Kitchen",
                description="The relative humidity in the kitchen, measured by the sensor next to the window",
                observationType="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                unitOfMeasurement=UnitOfMeasurement(
                    name="Percent",
                    symbol="%",
                    definition="ucum:%"
                ),
                Sensor={"@iot.id": 5},
                ObservedProperty={"@iot.id": 1}
            )
        ]
    )
    assert asdict(thing) == test_case
