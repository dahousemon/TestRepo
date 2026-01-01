'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Peak } from '@/types/peak';
import { formatElevation } from '@/lib/utils';

interface MapViewProps {
  peaks: Peak[];
  selectedPeak: Peak | null;
  onPeakSelect: (peak: Peak | null) => void;
  mapboxToken?: string;
}

export function MapView({ peaks, selectedPeak, onPeakSelect, mapboxToken }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);
  const popup = useRef<mapboxgl.Popup | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Use provided token or fall back to env variable or default
    const token = mapboxToken || process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.eyJ1IjoiZGFob3VzZW1vbiIsImEiOiJjbWp2cjNjc2s1dWpnM2dvd2J2aWFydjF6In0.aRFLfwOeldJyfjPvwNhRaw';

    if (!token) {
      return;
    }

    mapboxgl.accessToken = token;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/outdoors-v12',
      center: [-105.7821, 39.5501], // Colorado center
      zoom: 6.5,
      pitch: 45,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');
    map.current.addControl(
      new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      'top-right'
    );

    map.current.on('load', () => {
      setMapReady(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [mapboxToken]);

  // Add markers when map is ready and peaks change
  useEffect(() => {
    if (!map.current || !mapReady) return;

    // Clear existing markers
    markers.current.forEach(marker => marker.remove());
    markers.current = [];

    // Add new markers
    peaks.forEach((peak) => {
      const el = document.createElement('div');
      el.className = 'peak-marker';
      el.style.cssText = `
        width: 24px;
        height: 24px;
        background-color: ${peak.category === 'fourteener' ? '#f59e0b' : '#0ea5e9'};
        border: 2px solid white;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        transition: transform 0.2s;
      `;

      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.2)';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
      });

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([peak.longitude, peak.latitude])
        .addTo(map.current!);

      el.addEventListener('click', () => {
        onPeakSelect(peak);

        // Show popup
        if (popup.current) {
          popup.current.remove();
        }

        popup.current = new mapboxgl.Popup({
          offset: 25,
          closeButton: true,
          closeOnClick: false,
        })
          .setLngLat([peak.longitude, peak.latitude])
          .setHTML(`
            <div style="padding: 8px; min-width: 180px;">
              <h3 style="margin: 0 0 8px 0; font-weight: 600; font-size: 14px;">${peak.name}</h3>
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                <strong>Elevation:</strong> ${formatElevation(peak.elevation)}
              </p>
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                <strong>Range:</strong> ${peak.range}
              </p>
              <p style="margin: 0 0 8px 0; font-size: 12px; color: #666;">
                <strong>Difficulty:</strong> ${peak.difficulty}
              </p>
              <a href="/peaks/${peak.slug}" style="color: #2563eb; font-size: 12px; text-decoration: none;">
                View Details →
              </a>
            </div>
          `)
          .addTo(map.current!);
      });

      markers.current.push(marker);
    });

    // Fit bounds to show all peaks
    if (peaks.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      peaks.forEach(peak => {
        bounds.extend([peak.longitude, peak.latitude]);
      });
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 10 });
    }
  }, [peaks, mapReady, onPeakSelect]);

  // Fly to selected peak
  useEffect(() => {
    if (!map.current || !selectedPeak || !mapReady) return;

    map.current.flyTo({
      center: [selectedPeak.longitude, selectedPeak.latitude],
      zoom: 12,
      pitch: 60,
      duration: 2000,
    });
  }, [selectedPeak, mapReady]);

  // Token is now always available via hardcoded fallback

  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}
