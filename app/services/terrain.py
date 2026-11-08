import numpy as np


def elevation_stats(dem: np.ndarray) -> dict:
    """Min, max and mean elevation, ignoring NaN cells (outside the parcel)."""
    return {
        "min": float(np.nanmin(dem)),
        "max": float(np.nanmax(dem)),
        "mean": float(np.nanmean(dem)),
    }


def slope_degrees(dem: np.ndarray, cell_size: float) -> np.ndarray:
    """Slope of each cell in degrees. cell_size is in meters.

    Not NaN-safe: np.gradient's finite-difference stencil spreads NaN to
    every neighbor of a NaN cell, not just the cell itself. Callers should
    reduce the result with nanmean/nanmax instead of mean/max.
    """
    dz_dy, dz_dx = np.gradient(dem, cell_size)
    rise = np.sqrt(dz_dx**2 + dz_dy**2)
    return np.degrees(np.arctan(rise))


def cut_fill(dem: np.ndarray, cell_size: float, platform_elev: float) -> dict:
    """Cut and fill volumes (m3) to level the terrain to a flat platform."""
    cell_area = cell_size**2
    diff = dem - platform_elev

    cut = np.nansum(np.where(diff > 0, diff, 0)) * cell_area
    fill = np.nansum(np.where(diff < 0, -diff, 0)) * cell_area

    return {
        "cut_m3": float(cut),
        "fill_m3": float(fill),
        "net_m3": float(cut - fill),
    }