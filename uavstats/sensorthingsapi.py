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
    properties: Dict[str, object] = None


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
    Sensor: int
    ObservedProperty: int
    properties: Dict[str, object] = None


@dataclass
class Thing:
    name: str
    description: str
    properties: Dict[str, object]
    Locations: List[Location]
    Datastreams: List[Datastream]


# Example usage:
thing = Thing(
    name="Land Parcel - 1",
    description="Land Parcel - 1",
    properties={
        "parcel_id": 1,
        "project_id": "FAIRagro UC6"
    },
    Locations=[
        Location(
            name="Location of Parcel - 1",
            description="Polygon Geometry for Parcel - 1",
            encodingType="application/geo+json",
            location={
                "type": "Polygon",
                "coordinates": [[[10.628838331813736, 49.20751413114618], [10.628818955886832, 49.2075186951713], [10.628851463185999, 49.20757793906097], [10.6288708391328, 49.20757337503022], [10.628838331813736, 49.20751413114618]]]
            }
        )
    ],
    Datastreams=[
        Datastream(
            name="NDVI - 1",
            description="NDVI Zonal Stats for Parcel 1",
            observationType="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
            unitOfMeasurement=UnitOfMeasurement(
                name="NDVI",
                symbol="NDVI",
                definition="Normalized Difference Vegetation Index"
            ),
            Sensor={"@iot.id": 1},
            ObservedProperty={"@iot.id": 1}
        ),
        Datastream(
            name="VARI",
            description="VARI Zonal Stats for Parcel 1",
            observationType="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
            unitOfMeasurement=UnitOfMeasurement(
                name="VARI",
                symbol="VARI",
                definition="Visible Atmospherically Resistant Index"
            ),
            Sensor={"@iot.id": 1},
            ObservedProperty={"@iot.id": 2}
        )
    ]
)

# print(asdict(thing))
