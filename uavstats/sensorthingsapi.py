#!/usr/bin/env python
from dataclasses import dataclass, asdict
from typing import List, Dict
from rich import print


@dataclass
class Location:
    name: str
    description: str
    encodingType: str
    location: Dict[str, object]


@dataclass
class UnitOfMeasurement:
    name: str
    symbol: str
    definition: str


@dataclass
class Datastream:
    name: str
    description: str
    observationType: str
    unitOfMeasurement: UnitOfMeasurement
    Sensor: Dict[str, int]
    ObservedProperty: Dict[str, int]


@dataclass
class Thing:
    name: str
    description: str
    properties: Dict[str, object]
    Locations: List[Location]
    Datastreams: List[Datastream]


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
            ObservedProperty={"@iot.id": 5}
        )
    ]
)

print(asdict(thing))
