from dataclasses import dataclass

@dataclass
class WholeSampleValue:
    name: str
    value_units: str
    value: float
    source: "Datasource"

@dataclass
class PartsOfSampleValues:
    name_parts: str
    value_units: str
    values: dict
    source: "Datasource"
