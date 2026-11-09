# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Site feasibility API: user sends a parcel polygon; API returns terrain stats,
slope, and cut/fill volumes and cost for a target platform elevation.
Stack: FastAPI, NumPy, rasterio, pytest, Docker, GitHub Actions.
Viewer (`web/`): Vite + TypeScript + ArcGIS map components 5.x.

## Rules

- I must be able to explain every line in a job interview. Keep code simple,
  no clever tricks, no unnecessary abstractions.
- Small changes, one feature at a time. Explain what you changed and why.
- Do not commit or push. I make the commits and PRs myself.
- Do not overwrite existing files without showing me what will be removed.
- Pure terrain math lives in app/services/terrain.py with known-answer tests.
- No database for now (PostGIS comes later).
- Code, comments and docs in English.

## Commands

Run commands from the repo root with the project's virtualenv active (`.venv`).

- Install deps: `pip install -r requirements.txt`
- Run all tests: `pytest -v`
- Run a single test file: `pytest tests/test_terrain.py -v`
- Run a single test: `pytest tests/test_terrain.py::test_cut_fill_balanced -v`
- Run the API locally: `uvicorn app.main:app --reload`
- Run via Docker: `docker compose up --build` (serves on `http://localhost:8000`)

Viewer commands run from `web/` (start the API first):

- Install deps: `npm install`
- Run the viewer: `npm run dev` (serves on `http://localhost:5173`, the only origin the API's CORS allows)
- Type-check and build: `npm run build`

CI (`.github/workflows/ci.yml`) runs on push to `main` and on pull requests, with two jobs: `test` (install `requirements.txt`, then `pytest -v`) and `web` (Node 26, from `web/`: `npm ci`, then `npm run build`). There is no separate lint step configured.

## Architecture

FastAPI service for evaluating land-development/site feasibility (terrain analysis on raster elevation data), with a browser viewer:

- `app/main.py` — FastAPI app instance, CORS for the viewer's dev origin, the `/health` route, and inclusion of the API router.
- `app/api/routes.py` — `POST /assessment` and `POST /earthwork`; returns 422 if the polygon is not fully inside the DEM.
- `app/models/schemas.py` — pydantic request/response models and GeoJSON polygon validation (`PolygonGeoJSON`).
- `app/services/` — computation logic, decoupled from the web layer:
  - `dem.py` — `clip_to_polygon(polygon)` reprojects a lon/lat GeoJSON polygon to the DEM's CRS, raises `PolygonOutsideDemError` if it is not fully inside the DEM, and returns a `DemClip` (full DEM, NaN-masked DEM, inside mask, cell size, area). `data/sample_dem.tif` is loaded once and cached.
  - `terrain.py` — pure math on a DEM (digital elevation model) passed as a 2D `numpy` array:
    - `elevation_stats(dem)` — min/max/mean elevation, NaN-safe (NaN marks cells outside the parcel boundary).
    - `slope_degrees(dem, cell_size)` — per-cell slope in degrees via `np.gradient`; `cell_size` is the raster resolution in meters.
    - `cut_fill(dem, cell_size, platform_elev)` — cut/fill earthwork volumes (m³) to level a DEM to a flat platform elevation.
- `web/` — browser viewer. `index.html` holds the map, sketch and panel markup; `src/main.ts` holds the logic (draw one polygon, call `POST /assessment` and `POST /earthwork`, show the results). UI comes from map components (`@arcgis/map-components`), and `@arcgis/core` is used only for non-UI classes.
