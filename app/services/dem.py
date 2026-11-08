from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import array_bounds
from rasterio.warp import transform_geom
from shapely.geometry import box, shape

DEM_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_dem.tif"


class PolygonOutsideDemError(ValueError):
    """Raised when a polygon is not fully inside the DEM coverage area."""


@dataclass
class DemClip:
    dem: np.ndarray  # full DEM - slope needs real neighbors at the parcel edge
    masked_dem: np.ndarray  # DEM with NaN outside the polygon - for elevation/cut_fill
    inside_mask: np.ndarray  # boolean, True = inside the polygon
    cell_size: float
    area_m2: float


@lru_cache(maxsize=1)
def _load_dem():
    with rasterio.open(DEM_PATH) as ds:
        return ds.read(1), ds.transform, ds.crs


def clip_to_polygon(polygon: dict) -> DemClip:
    # _load_dem()'s array is cached and shared across requests; nothing below
    # mutates it in place (np.where always allocates a new array), so sharing
    # it by reference as `dem` is safe.
    dem, transform, crs = _load_dem()

    geom_utm = transform_geom("EPSG:4326", crs, polygon)
    poly = shape(geom_utm)

    raster_box = box(*array_bounds(*dem.shape, transform))
    if not raster_box.contains(poly):
        raise PolygonOutsideDemError("Polygon must be fully inside the DEM coverage area.")

    inside = geometry_mask([geom_utm], out_shape=dem.shape, transform=transform, invert=True)
    masked_dem = np.where(inside, dem, np.nan)

    return DemClip(
        dem=dem,
        masked_dem=masked_dem,
        inside_mask=inside,
        cell_size=abs(transform.a),
        area_m2=poly.area,
    )
