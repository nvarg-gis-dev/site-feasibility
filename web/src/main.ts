import "./style.css";

// Registers the custom elements used in index.html.
import "@arcgis/map-components/components/arcgis-map";
import "@arcgis/map-components/components/arcgis-sketch";
import "@arcgis/map-components/components/arcgis-zoom";

import Basemap from "@arcgis/core/Basemap";
import Graphic from "@arcgis/core/Graphic";
import Polygon from "@arcgis/core/geometry/Polygon";
import { webMercatorToGeographic } from "@arcgis/core/geometry/support/webMercatorUtils";
import GraphicsLayer from "@arcgis/core/layers/GraphicsLayer";
import OpenStreetMapLayer from "@arcgis/core/layers/OpenStreetMapLayer";
import SimpleFillSymbol from "@arcgis/core/symbols/SimpleFillSymbol";

// Corners of data/sample_dem.tif in lon/lat. The DEM is a 3km x 3km square in
// UTM 17N; these are its four corners reprojected to WGS84 with
// rasterio.warp.transform. Update them if the sample DEM changes.
const DEM_COVERAGE = new Polygon({
  rings: [[
    [-79.62869, 8.91649],
    [-79.60141, 8.91639],
    [-79.60131, 8.94351],
    [-79.62859, 8.94361],
    [-79.62869, 8.91649], // close the ring
  ]],
  spatialReference: { wkid: 4326 },
});

const coverageGraphic = new Graphic({
  geometry: DEM_COVERAGE,
  symbol: new SimpleFillSymbol({
    color: [0, 0, 0, 0], // transparent fill: only the outline is drawn
    outline: { color: [220, 0, 0], width: 2 },
  }),
});

// The shape the API expects: PolygonGeoJSON in app/models/schemas.py.
interface PolygonGeoJSON {
  type: "Polygon";
  coordinates: number[][][];
}

// The map draws in Web Mercator; the API wants [lon, lat]. ArcGIS rings are
// already closed, as GeoJSON requires.
function toGeoJSON(geometry: Polygon): PolygonGeoJSON {
  const lonLat = webMercatorToGeographic(geometry) as Polygon;
  return { type: "Polygon", coordinates: lonLat.rings };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// The response shapes of the API: app/models/schemas.py.
interface AssessmentResponse {
  area_m2: number;
  elevation: { min: number; max: number; mean: number };
  slope: { mean_deg: number; max_deg: number };
}

interface EarthworkResponse {
  cut_m3: number;
  fill_m3: number;
  net_m3: number;
  est_cost_usd: number;
}

// FastAPI sends "detail" as a string for errors we raise ourselves, and as a
// list of objects for pydantic validation errors.
function errorMessage(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join("; ");
  }
  return "The request failed.";
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // A server crash may not return JSON, so fall back to an empty object.
    const data = await response.json().catch(() => ({}));
    throw new Error(errorMessage(data.detail));
  }
  return response.json();
}

function formatNumber(value: number, decimals: number): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

const mapElement = document.querySelector("arcgis-map")!;

// An OpenStreetMap layer as the basemap: no ArcGIS API key needed.
mapElement.basemap = new Basemap({ baseLayers: [new OpenStreetMapLayer()] });

await mapElement.viewOnReady();

const coverageLayer = new GraphicsLayer({ title: "DEM coverage" });
coverageLayer.add(coverageGraphic);
mapElement.map?.add(coverageLayer);

const parcelLayer = new GraphicsLayer({ title: "Parcel" });
mapElement.map?.add(parcelLayer);

const sketchElement = document.querySelector("arcgis-sketch")!;
sketchElement.layer = parcelLayer;

let parcelGraphic: Graphic | null = null;
let parcelPolygon: PolygonGeoJSON | null = null;

const platformElevInput = document.querySelector<HTMLInputElement>("#platform-elev")!;
const unitCostInput = document.querySelector<HTMLInputElement>("#unit-cost")!;
const runButton = document.querySelector<HTMLButtonElement>("#run")!;
const errorText = document.querySelector<HTMLParagraphElement>("#error")!;
const resultsTable = document.querySelector<HTMLTableElement>("#results")!;

function clearOutput(): void {
  errorText.textContent = "";
  resultsTable.replaceChildren();
}

function showResults(assessment: AssessmentResponse, earthwork: EarthworkResponse): void {
  const rows = [
    ["Area (m²)", formatNumber(assessment.area_m2, 0)],
    ["Area (ha)", formatNumber(assessment.area_m2 / 10_000, 2)],
    ["Elevation min (m)", formatNumber(assessment.elevation.min, 1)],
    ["Elevation mean (m)", formatNumber(assessment.elevation.mean, 1)],
    ["Elevation max (m)", formatNumber(assessment.elevation.max, 1)],
    ["Slope mean (°)", formatNumber(assessment.slope.mean_deg, 1)],
    ["Slope max (°)", formatNumber(assessment.slope.max_deg, 1)],
    ["Cut (m³)", formatNumber(earthwork.cut_m3, 0)],
    ["Fill (m³)", formatNumber(earthwork.fill_m3, 0)],
    ["Net, cut − fill (m³)", formatNumber(earthwork.net_m3, 0)],
    ["Estimated cost (USD)", formatNumber(earthwork.est_cost_usd, 0)],
  ];

  for (const [label, value] of rows) {
    const row = resultsTable.insertRow();
    row.insertCell().textContent = label;
    row.insertCell().textContent = value;
  }
}

runButton.addEventListener("click", async () => {
  clearOutput();
  runButton.disabled = true;

  try {
    const assessment = await postJson<AssessmentResponse>("/assessment", {
      polygon: parcelPolygon,
    });
    // valueAsNumber is NaN for an empty input. JSON turns that into null, so
    // the API rejects it and its message is shown like any other error.
    const earthwork = await postJson<EarthworkResponse>("/earthwork", {
      polygon: parcelPolygon,
      platform_elev_m: platformElevInput.valueAsNumber,
      unit_cost_usd: unitCostInput.valueAsNumber,
    });
    showResults(assessment, earthwork);
  } catch (error) {
    errorText.textContent = error instanceof Error ? error.message : String(error);
  } finally {
    // The user may have started a new drawing while the requests were running.
    runButton.disabled = parcelPolygon === null;
  }
});

sketchElement.addEventListener("arcgisCreate", (event) => {
  const { state, graphic } = event.detail;

  // A new drawing replaces the previous one: at most one polygon exists.
  if (state === "start") {
    if (parcelGraphic) {
      parcelLayer.remove(parcelGraphic);
    }
    parcelGraphic = null;
    parcelPolygon = null;
    runButton.disabled = true;
    clearOutput(); // the old results belong to the polygon just removed
  }

  if (state === "complete" && graphic) {
    parcelGraphic = graphic;
    parcelPolygon = toGeoJSON(graphic.geometry as Polygon);
    runButton.disabled = false;
  }
});

await mapElement.goTo(coverageGraphic);
