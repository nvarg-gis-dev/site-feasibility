"""Download a Copernicus GLO-30 DEM tile and save a 3km x 3km sample.

The sample covers a hilly patch of Panama Pacifico / Arraijan, west of the
Panama Canal, reprojected to UTM zone 17N (EPSG:32617) so cell sizes are in
meters. Used as realistic sample input for the terrain-analysis service.
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform
from rasterio.windows import from_bounds

# Public, unsigned Copernicus GLO-30 tile covering Panama City (8-9N, 80-79W).
TILE_URL = (
    "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/"
    "Copernicus_DSM_COG_10_N08_00_W080_00_DEM/"
    "Copernicus_DSM_COG_10_N08_00_W080_00_DEM.tif"
)

# Panama Pacifico / Arraijan area, west of the Panama Canal. Nudged inland
# from the Howard AFB coastline (~8.915N, -79.599W) to avoid open water.
AOI_CENTER_LON = -79.615
AOI_CENTER_LAT = 8.93

BOX_SIZE_M = 3000  # 3km x 3km sample
PIXEL_SIZE_M = 30  # matches native GLO-30 resolution
GRID_SIZE_PX = BOX_SIZE_M // PIXEL_SIZE_M  # 100

DST_CRS = "EPSG:32617"
OUTPUT_PATH = "data/sample_dem.tif"

SRC_NODATA_FALLBACK = -32767.0

# Read a larger window than the output box so reprojection has enough source
# pixels to resample from, even though the UTM grid isn't lon/lat-aligned.
WINDOW_MARGIN = 1.3

METERS_PER_DEGREE_LAT = 111_320


def main():
    half_box_m = (BOX_SIZE_M / 2) * WINDOW_MARGIN
    half_lat_deg = half_box_m / METERS_PER_DEGREE_LAT
    half_lon_deg = half_box_m / (
        METERS_PER_DEGREE_LAT * np.cos(np.radians(AOI_CENTER_LAT))
    )

    west = AOI_CENTER_LON - half_lon_deg
    east = AOI_CENTER_LON + half_lon_deg
    south = AOI_CENTER_LAT - half_lat_deg
    north = AOI_CENTER_LAT + half_lat_deg

    with rasterio.open(TILE_URL) as src:
        window = from_bounds(west, south, east, north, transform=src.transform)
        window = window.round_offsets().round_lengths()
        source_data = src.read(1, window=window)
        source_transform = src.window_transform(window)
        source_nodata = src.nodata if src.nodata is not None else SRC_NODATA_FALLBACK

    # Project the AOI center into UTM 17N so the output grid is centered on it.
    center_xs, center_ys = transform(
        "EPSG:4326", DST_CRS, [AOI_CENTER_LON], [AOI_CENTER_LAT]
    )
    center_x, center_y = center_xs[0], center_ys[0]

    west_utm = center_x - BOX_SIZE_M / 2
    north_utm = center_y + BOX_SIZE_M / 2
    dst_transform = from_origin(west_utm, north_utm, PIXEL_SIZE_M, PIXEL_SIZE_M)

    dst_array = np.full((GRID_SIZE_PX, GRID_SIZE_PX), np.nan, dtype="float32")

    reproject(
        source=source_data,
        destination=dst_array,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        src_nodata=source_nodata,
        dst_transform=dst_transform,
        dst_crs=DST_CRS,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )

    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "height": GRID_SIZE_PX,
        "width": GRID_SIZE_PX,
        "count": 1,
        "crs": DST_CRS,
        "transform": dst_transform,
        "nodata": np.nan,
        "compress": "lzw",
    }

    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.write(dst_array, 1)

    print(f"Saved {OUTPUT_PATH}")
    print(f"Shape: {dst_array.shape}, CRS: {DST_CRS}, resolution: {PIXEL_SIZE_M}m")
    print(
        f"Elevation min/max: {np.nanmin(dst_array):.1f}m / {np.nanmax(dst_array):.1f}m"
    )


if __name__ == "__main__":
    main()
