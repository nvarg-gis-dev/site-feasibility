import numpy as np
import pytest

from app.services.terrain import cut_fill, elevation_stats, slope_degrees


def test_cut_fill_balanced():
    dem = np.array([[52.0, 52.0], [48.0, 48.0]])
    result = cut_fill(dem, cell_size=10, platform_elev=50)
    assert result["cut_m3"] == pytest.approx(400)
    assert result["fill_m3"] == pytest.approx(400)
    assert result["net_m3"] == pytest.approx(0)


def test_cut_fill_all_cut():
    dem = np.array([[55.0, 55.0], [55.0, 55.0]])
    result = cut_fill(dem, cell_size=10, platform_elev=50)
    assert result["cut_m3"] == pytest.approx(2000)
    assert result["fill_m3"] == pytest.approx(0)
    assert result["net_m3"] == pytest.approx(2000)


def test_cut_fill_ignores_nan():
    dem = np.array([[52.0, 52.0], [48.0, np.nan]])
    result = cut_fill(dem, cell_size=10, platform_elev=50)
    assert result["cut_m3"] == pytest.approx(400)
    assert result["fill_m3"] == pytest.approx(200)
    assert result["net_m3"] == pytest.approx(200)


def test_slope_flat_is_zero():
    dem = np.full((3, 3), 25.0)
    slope = slope_degrees(dem, cell_size=10)
    assert np.allclose(slope, 0.0)


def test_slope_45_degrees():
    dem = np.array([
        [0.0, 10.0, 20.0],
        [0.0, 10.0, 20.0],
        [0.0, 10.0, 20.0],
    ])
    slope = slope_degrees(dem, cell_size=10)
    assert np.allclose(slope, 45.0)


def test_elevation_stats():
    dem = np.array([[10.0, 20.0], [30.0, np.nan]])
    stats = elevation_stats(dem)
    assert stats["min"] == pytest.approx(10)
    assert stats["max"] == pytest.approx(30)
    assert stats["mean"] == pytest.approx(20)