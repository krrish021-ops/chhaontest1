"use client";

import React, { useEffect, useRef } from "react";
import maplibre, { Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { LayerSource, BasemapStyle } from "@/lib/types";

interface HeatMapProps {
  geojsonData: any;
  layerSource: LayerSource;
  basemapStyle: BasemapStyle;
  opacity: number;
  selectedCellId: string | null;
  onSelectCell: (cellId: string) => void;
}

const BASEMAP_URLS: Record<BasemapStyle, string> = {
  dark: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  streets: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
};

export function HeatMap({
  geojsonData,
  layerSource,
  basemapStyle,
  opacity,
  selectedCellId,
  onSelectCell,
}: HeatMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const hoveredIdRef = useRef<string | null>(null);

  const getPropKey = (source: LayerSource): string => {
    switch (source) {
      case "observed":
        return "suhii_night_normalized";
      case "ml_fit":
        return "suhii_night_ml";
      case "forecast_2031":
        return "suhii_night_2031";
      case "forecast_2041":
        return "suhii_night_2041";
      default:
        return "suhii_night";
    }
  };

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibre.Map({
      container: mapContainerRef.current,
      style: BASEMAP_URLS[basemapStyle],
      center: [79.0888, 21.1458],
      zoom: 11,
      pitch: 0,
    });

    map.addControl(new maplibre.NavigationControl(), "top-left");

    map.on("load", () => {
      mapRef.current = map;
      if (geojsonData) {
        renderMapContent(map, geojsonData, layerSource, opacity, selectedCellId);
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 2. Basemap Style Change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.setStyle(BASEMAP_URLS[basemapStyle]);
    map.once("styledata", () => {
      if (geojsonData) {
        renderMapContent(map, geojsonData, layerSource, opacity, selectedCellId);
      }
    });
  }, [basemapStyle]);

  // 3. Render Layers whenever Data, LayerSource, or Opacity changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const executeRender = () => {
      if (geojsonData && map.isStyleLoaded()) {
        renderMapContent(map, geojsonData, layerSource, opacity, selectedCellId);
        fitBoundsToGeoJSON(map, geojsonData);
      }
    };

    if (map.isStyleLoaded()) {
      executeRender();
    } else {
      map.once("styledata", executeRender);
    }
  }, [geojsonData, layerSource, opacity]);

  // 4. Highlight Selected Cell
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer("chhaon-highlight")) {
      map.setFilter("chhaon-highlight", [
        "==",
        ["to-string", ["get", "cell_id"]],
        selectedCellId?.toString() || "",
      ]);
    }
    if (map.getLayer("chhaon-highlight-glow")) {
      map.setFilter("chhaon-highlight-glow", [
        "==",
        ["to-string", ["get", "cell_id"]],
        selectedCellId?.toString() || "",
      ]);
    }
  }, [selectedCellId]);

  // Main Render Helper
  const renderMapContent = (
    map: MapLibreMap,
    data: any,
    source: LayerSource,
    layerOpacity: number,
    selectedId: string | null
  ) => {
    if (!data || !data.features || data.features.length === 0) return;

    const propKey = getPropKey(source);

    // Clean up existing layers/sources
    [
      "chhaon-highlight-glow",
      "chhaon-highlight",
      "chhaon-heat-line",
      "chhaon-heat-fill",
    ].forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (map.getSource("chhaon-grid")) map.removeSource("chhaon-grid");

    map.addSource("chhaon-grid", {
      type: "geojson",
      data: data,
      promoteId: "cell_id",
    });

    // Color ramp — -999 sentinel for null/missing data
    const colorExpression: any = [
      "interpolate",
      ["linear"],
      ["coalesce", ["get", propKey], ["get", "suhii_night"], -999],
      -999, "#1e293b", // No data — dark neutral (invisible on dark basemap)
      -4.0, "#1e3a8a", // Deep cool
      -2.0, "#2563eb", // Cool
      -0.5, "#38bdf8", // Mild cool
       0.0, "#5eead4", // Neutral
       1.0, "#fbbf24", // Warm
       2.0, "#f59e0b", // Hot
       3.0, "#ea580c", // Very hot
       4.0, "#dc2626", // Critical
       5.5, "#991b1b", // Extreme
       7.0, "#450a0a", // Max
    ];

    map.addLayer({
      id: "chhaon-heat-fill",
      type: "fill",
      source: "chhaon-grid",
      paint: {
        "fill-color": colorExpression,
        "fill-opacity": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          Math.min(layerOpacity + 0.12, 1),
          layerOpacity,
        ],
      },
    });

    map.addLayer({
      id: "chhaon-heat-line",
      type: "line",
      source: "chhaon-grid",
      paint: {
        "line-color": "#0f172a",
        "line-width": 0.4,
        "line-opacity": 0.35,
      },
    });

    map.addLayer({
      id: "chhaon-highlight-glow",
      type: "line",
      source: "chhaon-grid",
      paint: {
        "line-color": "#fb923c",
        "line-width": 9,
        "line-opacity": 0.25,
        "line-blur": 4,
      },
      filter: ["==", ["to-string", ["get", "cell_id"]], selectedId?.toString() || ""],
    });

    map.addLayer({
      id: "chhaon-highlight",
      type: "line",
      source: "chhaon-grid",
      paint: {
        "line-color": "#fdba74",
        "line-width": 2.5,
        "line-opacity": 1.0,
      },
      filter: ["==", ["to-string", ["get", "cell_id"]], selectedId?.toString() || ""],
    });

    const popup = new maplibre.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      className: "chhaon-popup",
    });

    map.off("mousemove", "chhaon-heat-fill");
    map.off("mouseleave", "chhaon-heat-fill");
    map.off("click", "chhaon-heat-fill");

    map.on("mousemove", "chhaon-heat-fill", (e) => {
      map.getCanvas().style.cursor = "pointer";

      if (e.features && e.features[0]) {
        const feat  = e.features[0];
        const props = feat.properties || {};
        const cellId = props.cell_id || "Cell";

        // Null-safe value — show "No data" instead of 0
        const val    = props[propKey] ?? props.suhii_night ?? null;
        const valNum = val !== null ? Number(val) : null;

        // Feature-state hover glow
        if (hoveredIdRef.current !== null && hoveredIdRef.current !== cellId) {
          map.setFeatureState(
            { source: "chhaon-grid", id: hoveredIdRef.current },
            { hover: false }
          );
        }
        map.setFeatureState({ source: "chhaon-grid", id: cellId }, { hover: true });
        hoveredIdRef.current = cellId;

        const valColor =
          valNum === null
            ? "#94a3b8"
            : valNum >= 3
            ? "#f87171"
            : valNum >= 1
            ? "#fbbf24"
            : "#5eead4";

        const valDisplay =
          valNum === null
            ? '<span style="color:#94a3b8">No data</span>'
            : `${valNum >= 0 ? "+" : ""}${valNum.toFixed(2)}°C`;

        popup
          .setLngLat(e.lngLat)
          .setHTML(
            `<div style="font-family:'Inter',sans-serif;font-size:12px;padding:8px 10px;background:#0f172a;color:#e2e8f0;border-radius:8px;border:1px solid #334155;box-shadow:0 8px 24px rgba(0,0,0,0.5);">
              <div style="font-weight:600;margin-bottom:4px;color:#f8fafc;letter-spacing:0.02em;">Cell ${cellId}</div>
              <div style="color:#94a3b8;font-size:11px;">Night SUHII Anomaly</div>
              <div style="font-weight:700;font-size:15px;color:${valColor};">${valDisplay}</div>
            </div>`
          )
          .addTo(map);
      }
    });

    map.on("mouseleave", "chhaon-heat-fill", () => {
      map.getCanvas().style.cursor = "";
      popup.remove();
      if (hoveredIdRef.current !== null) {
        map.setFeatureState(
          { source: "chhaon-grid", id: hoveredIdRef.current },
          { hover: false }
        );
        hoveredIdRef.current = null;
      }
    });

    map.on("click", "chhaon-heat-fill", (e) => {
      if (e.features && e.features[0]) {
        const cellId = e.features[0].properties?.cell_id;
        if (cellId) onSelectCell(cellId.toString());
      }
    });
  };

  // Auto-zoom to city boundaries
  const fitBoundsToGeoJSON = (map: MapLibreMap, data: any) => {
    if (!data || !data.features || data.features.length === 0) return;

    let minX = 180, minY = 90, maxX = -180, maxY = -90;

    data.features.forEach((feat: any) => {
      const geom = feat.geometry;
      if (!geom) return;

      const processCoords = (coords: any[]) => {
        coords.forEach((coord: any) => {
          if (typeof coord[0] === "number" && typeof coord[1] === "number") {
            if (coord[0] < minX) minX = coord[0];
            if (coord[0] > maxX) maxX = coord[0];
            if (coord[1] < minY) minY = coord[1];
            if (coord[1] > maxY) maxY = coord[1];
          } else if (Array.isArray(coord)) {
            processCoords(coord);
          }
        });
      };

      if (geom.coordinates) processCoords(geom.coordinates);
    });

    if (minX < maxX && minY < maxY) {
      map.fitBounds(
        [[minX, minY], [maxX, maxY]],
        { padding: 60, maxZoom: 14, duration: 1200 }
      );
    }
  };

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}

export default HeatMap;
