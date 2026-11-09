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

sketchElement.addEventListener("arcgisCreate", (event) => {
  const { state, graphic } = event.detail;

  // A new drawing replaces the previous one: at most one polygon exists.
  if (state === "start") {
    if (parcelGraphic) {
      parcelLayer.remove(parcelGraphic);
    }
    parcelGraphic = null;
    parcelPolygon = null;
  }

  if (state === "complete" && graphic) {
    parcelGraphic = graphic;
    parcelPolygon = toGeoJSON(graphic.geometry as Polygon);
    // Temporary until step 5 sends this to the API.
    console.log("Parcel GeoJSON:", parcelPolygon);
  }
});

await mapElement.goTo(coverageGraphic);
