from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PolygonGeoJSON(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]  # rings of [lon, lat]; holes unchecked

    @field_validator("coordinates")
    @classmethod
    def check_exterior_ring(cls, value: list[list[list[float]]]) -> list[list[list[float]]]:
        if not value or len(value[0]) < 4:
            raise ValueError("Polygon exterior ring must have at least 4 positions")
        return value


class ElevationStats(BaseModel):
    min: float
    max: float
    mean: float


class SlopeStats(BaseModel):
    mean_deg: float
    max_deg: float


class AssessmentRequest(BaseModel):
    polygon: PolygonGeoJSON


class AssessmentResponse(BaseModel):
    area_m2: float
    elevation: ElevationStats
    slope: SlopeStats


class EarthworkRequest(BaseModel):
    polygon: PolygonGeoJSON
    platform_elev_m: float
    unit_cost_usd: float = Field(ge=0)


class EarthworkResponse(BaseModel):
    cut_m3: float
    fill_m3: float
    net_m3: float
    est_cost_usd: float
