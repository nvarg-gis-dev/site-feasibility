import "./style.css";

// Registers the <arcgis-map> and <arcgis-zoom> custom elements used in index.html.
import "@arcgis/map-components/components/arcgis-map";
import "@arcgis/map-components/components/arcgis-zoom";

import Basemap from "@arcgis/core/Basemap";
import Graphic from "@arcgis/core/Graphic";
import Polygon from "@arcgis/core/geometry/Polygon";
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

const mapElement = document.querySelector("arcgis-map")!;

// An OpenStreetMap layer as the basemap: no ArcGIS API key needed.
mapElement.basemap = new Basemap({ baseLayers: [new OpenStreetMapLayer()] });

await mapElement.viewOnReady();

const coverageLayer = new GraphicsLayer({ title: "DEM coverage" });
coverageLayer.add(coverageGraphic);
mapElement.map?.add(coverageLayer);

await mapElement.goTo(coverageGraphic);
