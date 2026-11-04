"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { INDIAN_CITIES, IndianCityEntry } from "@/lib/indianCities";

export type ThermalLayerKey = "observed" | "normalized" | "forecast_2031" | "forecast_2041";

interface HeatMapProps {
  geojsonData: any;
  selectedCellId: string | null;
  onSelectCellId: (cellId: string | null) => void;
  activeLayer: ThermalLayerKey;
  opacity: number;
  basemap: "dark" | "streets";
  center: [number, number];
  zoom: number;
  focusedCity: IndianCityEntry | null;
  onSelectCityPin?: (city: IndianCityEntry) => void;
  filterMode?: "all" | "hotspots" | "cool";
}

const BASEMAP_STYLES: Record<string, string> = {
  dark: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  streets: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
};

const COLOR_STOPS: [number, string][] = [
  [-2.0, "#1d4ed8"],
  [-0.5, "#0284c7"],
  [0.5, "#0d9488"],
  [1.5, "#65a30d"],
  [2.5, "#eab308"],
  [3.5, "#f97316"],
  [4.5, "#dc2626"],
  [6.0, "#7f1d1d"],
];

export function getLayerFieldName(layer: ThermalLayerKey): string {
  switch (layer) {
    case "normalized":
      return "suhii_night_normalized";
    case "forecast_2031":
      return "suhii_night_2031";
    case "forecast_2041":
      return "suhii_night_2041";
    default:
      return "suhii_night";
  }
}

export function getLayerDisplayTitle(layer: ThermalLayerKey): string {
  switch (layer) {
    case "normalized":
      return "2024 Weather-Adjusted (ERA5)";
    case "forecast_2031":
      return "2031 BAU Projection";
    case "forecast_2041":
      return "2041 BAU Projection";
    default:
      return "2024 Observed Satellite (MODIS)";
  }
}

export default function HeatMap({
  geojsonData,
  selectedCellId,
  onSelectCellId,
  activeLayer,
  opacity,
  basemap,
  center,
  zoom,
  focusedCity,
  onSelectCityPin,
  filterMode = "all",
}: HeatMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const activeLayerRef = useRef<ThermalLayerKey>(activeLayer);
  activeLayerRef.current = activeLayer;

  const [mapReady, setMapReady] = useState(false);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAP_STYLES[basemap] || BASEMAP_STYLES.dark,
      center,
      zoom,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "bottom-left");
    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: "300px",
    });
    map.on("load", () => setMapReady(true));
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Fly when city center/zoom changes
  useEffect(() => {
    if (!mapRef.current || !center) return;
    mapRef.current.flyTo({ center, zoom, duration: 1100, essential: true });
  }, [center[0], center[1], zoom]);

  // Fly to searched/selected Indian city
  useEffect(() => {
    if (!mapRef.current || !focusedCity) return;
    mapRef.current.flyTo({
      center: [focusedCity.lon, focusedCity.lat],
      zoom: Math.max(mapRef.current.getZoom(), 7.2),
      duration: 1200,
      essential: true,
    });
  }, [focusedCity]);

  // Switch basemap
  useEffect(() => {
    if (!mapRef.current) return;
    setMapReady(false);
    mapRef.current.setStyle(BASEMAP_STYLES[basemap] || BASEMAP_STYLES.dark);
    mapRef.current.once("styledata", () => setMapReady(true));
  }, [basemap]);

  // Build or update GeoJSON source & layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !geojsonData) return;

    const field = getLayerFieldName(activeLayer);
    const firstSymbolId = (map.getStyle()?.layers || []).find((l) => l.type === "symbol")?.id;

    ["heat-highlight", "heat-outline", "heat-fill"].forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (map.getSource("heat-source")) map.removeSource("heat-source");

    map.addSource("heat-source", {
      type: "geojson",
      data: geojsonData,
    });

    const colorExpr: any = [
      "case",
      ["==", ["get", field], null],
      "rgba(0,0,0,0)",
      [
        "interpolate",
        ["linear"],
        ["coalesce", ["to-number", ["get", field]], 0],
        ...COLOR_STOPS.flat(),
      ],
    ];

    let layerFilter: any = ["!=", ["get", field], null];
    if (filterMode === "hotspots") {
      layerFilter = [">=", ["to-number", ["get", field]], 2.5];
    } else if (filterMode === "cool") {
      layerFilter = ["<=", ["to-number", ["get", field]], 0.5];
    }

    map.addLayer(
      {
        id: "heat-fill",
        type: "fill",
        source: "heat-source",
        filter: layerFilter,
        paint: {
          "fill-color": colorExpr,
          "fill-opacity": opacity,
        },
      },
      firstSymbolId
    );

    map.addLayer(
      {
        id: "heat-outline",
        type: "line",
        source: "heat-source",
        filter: layerFilter,
        paint: {
          "line-color": "#1e293b",
          "line-width": 0.5,
          "line-opacity": 0.25,
        },
      },
      firstSymbolId
    );

    map.addLayer(
      {
        id: "heat-highlight",
        type: "line",
        source: "heat-source",
        paint: {
          "line-color": "#f97316",
          "line-width": 3,
        },
        filter: ["==", ["get", "cell_id"], selectedCellId || ""],
      },
      firstSymbolId
    );

    const onMove = (e: any) => {
      if (!e.features?.length) return;
      map.getCanvas().style.cursor = "pointer";
      const pr = e.features[0].properties;
      const curField = getLayerFieldName(activeLayerRef.current);
      const val = pr[curField];
      const suhiiStr =
        val !== undefined && val !== null && val !== "null"
          ? `${Number(val) >= 0 ? "+" : ""}${Number(val).toFixed(2)} °C`
          : "No data";
      const lstDay =
        pr.lst_day !== undefined && pr.lst_day !== null && pr.lst_day !== "null"
          ? `${Number(pr.lst_day).toFixed(1)} °C`
          : "—";

      popupRef.current
        ?.setLngLat(e.lngLat)
        .setHTML(
          `<div style="background:#0f172a;color:#f8fafc;padding:10px 12px;border-radius:6px;border:1px solid #334155;font-family:system-ui,sans-serif;font-size:12px;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
            <div style="font-weight:600;font-size:12.5px;color:#f8fafc;margin-bottom:2px;">${pr.location_name || pr.cell_id}</div>
            <div style="font-size:10.5px;color:#94a3b8;margin-bottom:8px;">Zone ${pr.cell_id} · ${getLayerDisplayTitle(activeLayerRef.current)}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;border-top:1px solid #1e293b;padding-top:6px;">
              <div>
                <div style="font-size:10px;color:#94a3b8;">Night Heat Island</div>
                <div style="font-weight:700;color:#fb923c;font-family:monospace;">${suhiiStr}</div>
              </div>
              <div>
                <div style="font-size:10px;color:#94a3b8;">Day Surface Temp</div>
                <div style="font-weight:700;color:#f8fafc;font-family:monospace;">${lstDay}</div>
              </div>
            </div>
          </div>`
        )
        .addTo(map);
    };

    const onLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };

    const onClick = (e: any) => {
      if (!e.features?.length) return;
      const cid = e.features[0].properties?.cell_id;
      if (cid) onSelectCellId(String(cid));
    };

    map.on("mousemove", "heat-fill", onMove);
    map.on("mouseleave", "heat-fill", onLeave);
    map.on("click", "heat-fill", onClick);

    return () => {
      if (!map.getStyle()) return;
      map.off("mousemove", "heat-fill", onMove);
      map.off("mouseleave", "heat-fill", onLeave);
      map.off("click", "heat-fill", onClick);
    };
  }, [mapReady, geojsonData, activeLayer, filterMode]);

  // Update opacity
  useEffect(() => {
    const map = mapRef.current;
    if (map && mapReady && map.getLayer("heat-fill")) {
      map.setPaintProperty("heat-fill", "fill-opacity", opacity);
    }
  }, [opacity, mapReady]);

  // Update selected cell outline
  useEffect(() => {
    const map = mapRef.current;
    if (map && mapReady && map.getLayer("heat-highlight")) {
      map.setFilter("heat-highlight", ["==", ["get", "cell_id"], selectedCellId || ""]);
    }
  }, [selectedCellId, mapReady]);

  // Render clean, understated city reference markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const majorHubs = new Set([
      "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Ahmedabad",
      "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow", "Bhopal",
      "Indore", "Nagpur", "Patna", "Surat", "Raipur", "Ranchi",
      "Bhubaneswar", "Chandigarh", "Guwahati", "Kochi", "Visakhapatnam", "Srinagar",
    ]);

    const pins = INDIAN_CITIES.filter(
      (c) => majorHubs.has(c.name) || (focusedCity && c.name === focusedCity.name)
    );
    if (focusedCity && !pins.some((x) => x.name === focusedCity.name)) {
      pins.push(focusedCity);
    }

    pins.forEach((city) => {
      const isFocused = focusedCity?.name === city.name;
      const el = document.createElement("div");
      el.style.cursor = "pointer";
      el.innerHTML = `<div style="
        display:flex;align-items:center;gap:5px;
        padding:${isFocused ? "4px 9px" : "2px 6px"};
        border-radius:4px;
        background:${isFocused ? "#0f172a" : "rgba(15,23,42,0.82)"};
        color:#f8fafc;
        border:${isFocused ? "1.5px solid #f97316" : "1px solid rgba(148,163,184,0.4)"};
        font-family:system-ui,sans-serif;
        font-size:${isFocused ? "11.5px" : "10px"};
        font-weight:600;
        letter-spacing:0.01em;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        white-space:nowrap;
      ">
        <span style="width:5px;height:5px;border-radius:50%;background:${isFocused ? "#f97316" : "#cbd5e1"};display:inline-block;"></span>
        <span>${city.name}</span>
      </div>`;
      el.onclick = (ev) => {
        ev.stopPropagation();
        if (onSelectCityPin) onSelectCityPin(city);
      };
      markersRef.current.push(
        new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([city.lon, city.lat])
          .addTo(map)
      );
    });
  }, [mapReady, focusedCity, geojsonData]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
