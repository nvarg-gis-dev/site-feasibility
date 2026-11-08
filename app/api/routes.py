import numpy as np
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    EarthworkRequest,
    EarthworkResponse,
    ElevationStats,
    PolygonGeoJSON,
    SlopeStats,
)
from app.services.dem import DemClip, PolygonOutsideDemError, clip_to_polygon
from app.services.terrain import cut_fill, elevation_stats, slope_degrees

router = APIRouter()


def _clip_or_422(polygon: PolygonGeoJSON) -> DemClip:
    try:
        return clip_to_polygon(polygon.model_dump())
    except PolygonOutsideDemError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/assessment", response_model=AssessmentResponse)
def assessment(request: AssessmentRequest) -> AssessmentResponse:
    clip = _clip_or_422(request.polygon)

    elevation = elevation_stats(clip.masked_dem)

    # Slope on the FULL dem (real neighbors everywhere), then reduce only
    # over the polygon's cells - masking before differentiating would spread
    # NaN into edge cells and could make a small polygon's slope all-NaN.
    full_slope = slope_degrees(clip.dem, clip.cell_size)
    slope_inside = np.where(clip.inside_mask, full_slope, np.nan)

    return AssessmentResponse(
        area_m2=clip.area_m2,
        elevation=ElevationStats(**elevation),
        slope=SlopeStats(
            mean_deg=float(np.nanmean(slope_inside)),
            max_deg=float(np.nanmax(slope_inside)),
        ),
    )


@router.post("/earthwork", response_model=EarthworkResponse)
def earthwork(request: EarthworkRequest) -> EarthworkResponse:
    clip = _clip_or_422(request.polygon)
    result = cut_fill(clip.masked_dem, clip.cell_size, request.platform_elev_m)
    est_cost_usd = (result["cut_m3"] + result["fill_m3"]) * request.unit_cost_usd
    return EarthworkResponse(**result, est_cost_usd=est_cost_usd)
