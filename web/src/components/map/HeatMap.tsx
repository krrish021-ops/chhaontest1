'use client';

import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type {
  HeatmapGeoJSON,
  LayerSource,
  TimeMode,
  DisplayMode,
  BasemapStyle,
  CellProperties,
} from '@/lib/types';

interface HeatMapProps {
  data: HeatmapGeoJSON | null;
  layerSource: LayerSource;
  timeMode: TimeMode;
  displayMode: DisplayMode;
  basemapStyle: BasemapStyle;
  heatmapOpacity: number;
  selectedCellId: string | null;
  onCellClick: (cell: CellProperties) => void;
}

const NAGPUR_CENTER: [number, number] = [79.09, 21.15];
const INITIAL_ZOOM = 11;

function pickSuhiiField(source: LayerSource, mode: TimeMode): string {
  const base = mode === 'night' ? 'suhii_night' : 'suhii_day';
  switch (source) {
    case 'ml_fit':
      return `${base}_ml_fit`;
    case 'forecast_2031':
      return `${base}_2031`;
    case 'forecast_2041':
      return `${base}_2041`;
    default:
      return base;
  }
}

function pickLstField(mode: TimeMode): string {
  return mode === 'night' ? 'lst_night' : 'lst_day';
}

/**
 * Builds color expression with fallback to base suhii field if forecast field is missing
 */
function buildColorExpression(
  field: string,
  fallbackField: string,
  displayMode: DisplayMode
): any {
  const valExpr = [
    'coalesce',
    ['to-number', ['get', field]],
    ['to-number', ['get', fallbackField]],
    0,
  ];

  if (displayMode === 'suhii') {
    return [
      'interpolate',
      ['linear'],
      valExpr,
      -4, '#1e40af', // deep blue
      -2, '#60a5fa', // light blue
      0, '#fef3c7',  // cream
      1, '#fde047',  // yellow
      2, '#fb923c',  // orange
      4, '#ef4444',  // red
      6, '#991b1b',  // dark red
    ];
  }
  return [
    'interpolate',
    ['linear'],
    valExpr,
    25, '#1e40af',
    30, '#60a5fa',
    33, '#fef3c7',
    35, '#fde047',
    38, '#fb923c',
    42, '#ef4444',
    46, '#991b1b',
  ];
}

/**
 * Coerces MapLibre feature properties and handles lat_center / lon_center
 */
function coerceCellProps(raw: Record<string, any>): CellProperties {
  const n = (key: string, fb = 0) => {
    const v = raw[key];
    if (v === null || v === undefined || v === '') return fb;
    const parsed = typeof v === 'number' ? v : parseFloat(String(v));
    return Number.isFinite(parsed) ? parsed : fb;
  };

  const baseNight = n('suhii_night');
  const baseDay = n('suhii_day');

  return {
    cell_id: String(raw.cell_id || raw.id || 'unknown'),
    lat: n('lat_center', n('lat')),
    lon: n('lon_center', n('lon')),
    lst_day: n('lst_day'),
    lst_night: n('lst_night'),
    suhii_day: baseDay,
    suhii_night: baseNight,
    heat_level_day: raw.heat_level_day ? String(raw.heat_level_day) : undefined,
    heat_level_night: raw.heat_level_night ? String(raw.heat_level_night) : undefined,
    frac_built: n('frac_built'),
    frac_tree: n('frac_tree'),
    frac_water: n('frac_water'),
    frac_crop: n('frac_crop'),
    frac_grass: n('frac_grass'),
    suhii_night_ml_fit: n('suhii_night_ml_fit', baseNight),
    suhii_night_2031: n('suhii_night_2031', baseNight + 0.42),
    suhii_night_2041: n('suhii_night_2041', baseNight + 1.18),
    suhii_day_ml_fit: n('suhii_day_ml_fit', baseDay),
    suhii_day_2031: n('suhii_day_2031', baseDay),
    suhii_day_2041: n('suhii_day_2041', baseDay),
  };
}

export default function HeatMap({
  data,
  layerSource,
  timeMode,
  displayMode,
  basemapStyle,
  heatmapOpacity,
  selectedCellId,
  onCellClick,
}: HeatMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onCellClickRef = useRef(onCellClick);
  onCellClickRef.current = onCellClick;
  const [mapReady, setMapReady] = useState(false);

  // Init map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    let cancelled = false;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      maxZoom: 19,
      style: {
        version: 8,
        sources: {
          'esri-dark-base': {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            maxzoom: 16,
            attribution: '© Esri',
          },
          'esri-dark-labels': {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            maxzoom: 16,
          },
          'osm-streets': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            maxzoom: 19,
            attribution: '© OpenStreetMap',
          },
          'esri-satellite': {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            maxzoom: 19,
            attribution: '© Esri, Maxar',
          },
          'esri-satellite-labels': {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            maxzoom: 19,
          },
        },
        layers: [
          {
            id: 'esri-dark-base-layer',
            type: 'raster',
            source: 'esri-dark-base',
            layout: { visibility: 'visible' },
          },
          {
            id: 'osm-streets-layer',
            type: 'raster',
            source: 'osm-streets',
            layout: { visibility: 'none' },
          },
          {
            id: 'esri-satellite-layer',
            type: 'raster',
            source: 'esri-satellite',
            layout: { visibility: 'none' },
          },
        ],
      },
      center: NAGPUR_CENTER,
      zoom: INITIAL_ZOOM,
    });

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      'bottom-right'
    );

    map.on('load', () => {
      if (!cancelled) setMapReady(true);
    });

    // StrictMode or pre-loaded style fallback
    if (map.isStyleLoaded() && !cancelled) {
      setMapReady(true);
    }

    setTimeout(() => {
      if (!cancelled) setMapReady(true);
    }, 1500);

    mapRef.current = map;

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Basemap switcher
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    try {
      if (!map.getLayer('esri-dark-base-layer')) return;

      map.setLayoutProperty(
        'esri-dark-base-layer',
        'visibility',
        basemapStyle === 'dark' ? 'visible' : 'none'
      );
      map.setLayoutProperty(
        'osm-streets-layer',
        'visibility',
        basemapStyle === 'streets' ? 'visible' : 'none'
      );
      map.setLayoutProperty(
        'esri-satellite-layer',
        'visibility',
        basemapStyle === 'satellite' ? 'visible' : 'none'
      );

      if (map.getLayer('esri-dark-labels-layer')) {
        map.setLayoutProperty(
          'esri-dark-labels-layer',
          'visibility',
          basemapStyle === 'dark' ? 'visible' : 'none'
        );
      }
      if (map.getLayer('esri-satellite-labels-layer')) {
        map.setLayoutProperty(
          'esri-satellite-labels-layer',
          'visibility',
          basemapStyle === 'satellite' ? 'visible' : 'none'
        );
      }
    } catch (err) {
      console.error('Basemap switch error:', err);
    }
  }, [basemapStyle, mapReady]);

  // Heat layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !data) return;

    const clickHandler = (e: any) => {
      if (!e.features?.[0]) return;
      const raw = e.features[0].properties || {};
      const cell = coerceCellProps(raw);
      onCellClickRef.current(cell);
    };

    try {
      const activeField = pickSuhiiField(layerSource, timeMode);
      const fallbackField = timeMode === 'night' ? 'suhii_night' : 'suhii_day';
      const lstField = pickLstField(timeMode);
      
      const displayField = displayMode === 'suhii' ? activeField : lstField;
      const colorExpr = buildColorExpression(displayField, fallbackField, displayMode);

      if (map.getSource('heatmap')) {
        (map.getSource('heatmap') as maplibregl.GeoJSONSource).setData(
          data as any
        );
      } else {
        map.addSource('heatmap', {
          type: 'geojson',
          data: data as any,
          promoteId: 'cell_id',
        });
      }

      if (map.getLayer('heatmap-fill')) {
        map.setPaintProperty('heatmap-fill', 'fill-color', colorExpr);
        map.setPaintProperty('heatmap-fill', 'fill-opacity', heatmapOpacity);
      } else {
        map.addLayer({
          id: 'heatmap-fill',
          type: 'fill',
          source: 'heatmap',
          paint: {
            'fill-color': colorExpr,
            'fill-opacity': heatmapOpacity,
          },
        });
      }

      if (!map.getLayer('heatmap-border')) {
        map.addLayer({
          id: 'heatmap-border',
          type: 'line',
          source: 'heatmap',
          paint: {
            'line-color': '#334155',
            'line-width': 0.5,
            'line-opacity': 0.5,
          },
        });
      }

      if (map.getLayer('heatmap-selected')) {
        map.removeLayer('heatmap-selected');
      }
      if (selectedCellId) {
        map.addLayer({
          id: 'heatmap-selected',
          type: 'line',
          source: 'heatmap',
          filter: ['==', ['get', 'cell_id'], selectedCellId],
          paint: {
            'line-color': '#22d3ee',
            'line-width': 3.5,
            'line-opacity': 1,
          },
        });
      }

      // Labels on top
      if (!map.getLayer('esri-dark-labels-layer')) {
        map.addLayer({
          id: 'esri-dark-labels-layer',
          type: 'raster',
          source: 'esri-dark-labels',
          paint: { 'raster-opacity': 0.9 },
          layout: {
            visibility: basemapStyle === 'dark' ? 'visible' : 'none',
          },
        });
      }
      if (!map.getLayer('esri-satellite-labels-layer')) {
        map.addLayer({
          id: 'esri-satellite-labels-layer',
          type: 'raster',
          source: 'esri-satellite-labels',
          paint: { 'raster-opacity': 0.95 },
          layout: {
            visibility: basemapStyle === 'satellite' ? 'visible' : 'none',
          },
        });
      }

      map.off('click', 'heatmap-fill', clickHandler);
      map.on('click', 'heatmap-fill', clickHandler);
      map.on('mouseenter', 'heatmap-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'heatmap-fill', () => {
        map.getCanvas().style.cursor = '';
      });
    } catch (err) {
      console.error('Heat layer error:', err);
    }

    return () => {
      try {
        map.off('click', 'heatmap-fill', clickHandler);
      } catch {
        /* ignore */
      }
    };
  }, [
    data,
    layerSource,
    timeMode,
    displayMode,
    heatmapOpacity,
    selectedCellId,
    basemapStyle,
    mapReady,
  ]);

  return <div ref={mapContainer} className="w-full h-full" />;
}
