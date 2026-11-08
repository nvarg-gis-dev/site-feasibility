# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Site feasibility API: user sends a parcel polygon; API returns terrain stats,
slope, and cut/fill volumes and cost for a target platform elevation.
Stack: FastAPI, NumPy, rasterio, pytest, Docker, GitHub Actions.
Viewer (later): Vite + TypeScript + ArcGIS Maps SDK for JavaScript.

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

CI (`.github/workflows/ci.yml`) runs on push/PR to `main`: install `requirements.txt`, then `pytest -v`. There is no separate lint step configured.

## Architecture

FastAPI service for evaluating land-development/site feasibility (terrain analysis on raster elevation data). Currently early-stage/skeleton:

- `app/main.py` — FastAPI app instance and route registration. Routes are currently defined directly on `app` (see `/health`); as the API grows, expect routers to move under `app/api/`.
- `app/services/` — pure computation logic, decoupled from the web layer. e.g. `terrain.py` operates on a DEM (digital elevation model) passed as a 2D `numpy` array:
  - `elevation_stats(dem)` — min/max/mean elevation, NaN-safe (NaN marks cells outside the parcel boundary).
  - `slope_degrees(dem, cell_size)` — per-cell slope in degrees via `np.gradient`; `cell_size` is the raster resolution in meters.
  - `cut_fill(dem, cell_size, platform_elev)` — cut/fill earthwork volumes (m³) to level a DEM to a flat platform elevation.
- `app/models/` —