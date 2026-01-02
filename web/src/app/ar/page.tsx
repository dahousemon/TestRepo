'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { getAllPeaks, calculateDistance } from '@/lib/peaks';
import { Peak } from '@/types/peak';
import Link from 'next/link';

export default function ARPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [nearbyPeaks, setNearbyPeaks] = useState<Peak[]>([]);
  const [arReady, setArReady] = useState(false);
  const [scriptsLoaded, setScriptsLoaded] = useState(false);
  const arContainerRef = useRef<HTMLDivElement>(null);

  const getMarkerColor = useCallback((peak: Peak) => {
    return peak.category === 'fourteener' ? '#f59e0b' : '#0ea5e9';
  }, []);

  // Load AR.js and A-Frame scripts
  useEffect(() => {
    const loadScripts = async () => {
      // Check if already loaded
      if (document.querySelector('script[src*="aframe"]')) {
        setScriptsLoaded(true);
        return;
      }

      try {
        // Load A-Frame first
        const aframeScript = document.createElement('script');
        aframeScript.src = 'https://aframe.io/releases/1.4.0/aframe.min.js';
        aframeScript.async = true;

        await new Promise<void>((resolve, reject) => {
          aframeScript.onload = () => resolve();
          aframeScript.onerror = () => reject(new Error('Failed to load A-Frame'));
          document.head.appendChild(aframeScript);
        });

        // Then load AR.js
        const arjsScript = document.createElement('script');
        arjsScript.src = 'https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js';
        arjsScript.async = true;

        await new Promise<void>((resolve, reject) => {
          arjsScript.onload = () => resolve();
          arjsScript.onerror = () => reject(new Error('Failed to load AR.js'));
          document.head.appendChild(arjsScript);
        });

        setScriptsLoaded(true);
      } catch {
        setError('Failed to load AR libraries. Please try again.');
        setIsLoading(false);
      }
    };

    loadScripts();
  }, []);

  // Get user location
  useEffect(() => {
    if (!scriptsLoaded) return;

    // Check for geolocation support and request position
    const getLocation = () => {
      if (!navigator.geolocation) {
        return Promise.reject(new Error('Geolocation is not supported by your browser'));
      }

      return new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        });
      });
    };

    getLocation()
      .then((position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ lat: latitude, lng: longitude });

        // Get peaks within 100 miles
        const allPeaks = getAllPeaks();
        const nearby = allPeaks
          .map(peak => ({
            ...peak,
            distance: calculateDistance(latitude, longitude, peak.latitude, peak.longitude)
          }))
          .filter(peak => peak.distance <= 100)
          .sort((a, b) => a.distance - b.distance)
          .slice(0, 50); // Limit to 50 nearest peaks for performance

        setNearbyPeaks(nearby);
        setIsLoading(false);

        // Small delay to ensure A-Frame is fully initialized
        setTimeout(() => setArReady(true), 1000);
      })
      .catch((err: Error) => {
        setError(`Location error: ${err.message}. Please enable location services.`);
        setIsLoading(false);
      });
  }, [scriptsLoaded]);

  // Build AR scene dynamically
  useEffect(() => {
    if (!arReady || !arContainerRef.current || nearbyPeaks.length === 0) return;

    // Create A-Frame scene dynamically
    const scene = document.createElement('a-scene');
    scene.setAttribute('embedded', '');
    scene.setAttribute('arjs', 'sourceType: webcam; debugUIEnabled: false;');
    scene.setAttribute('vr-mode-ui', 'enabled: false');
    scene.setAttribute('renderer', 'antialias: true; alpha: true');

    // Create camera
    const camera = document.createElement('a-camera');
    camera.setAttribute('gps-camera', 'simulateLatitude: 0; simulateLongitude: 0;');
    camera.setAttribute('rotation-reader', '');
    scene.appendChild(camera);

    // Create entities for each peak
    nearbyPeaks.forEach((peak) => {
      const entity = document.createElement('a-entity');
      entity.setAttribute('gps-entity-place', `latitude: ${peak.latitude}; longitude: ${peak.longitude};`);
      entity.setAttribute('look-at', '[gps-camera]');
      entity.setAttribute('scale', '15 15 15');

      // Marker cone
      const marker = document.createElement('a-entity');
      marker.setAttribute('geometry', 'primitive: cone; radiusBottom: 0.5; radiusTop: 0; height: 1');
      marker.setAttribute('material', `color: ${getMarkerColor(peak)}; opacity: 0.9`);
      entity.appendChild(marker);

      // Text label
      const text = document.createElement('a-text');
      text.setAttribute('value', `${peak.name}\n${peak.elevation.toLocaleString()} ft`);
      text.setAttribute('color', 'white');
      text.setAttribute('align', 'center');
      text.setAttribute('scale', '0.5 0.5 0.5');
      text.setAttribute('position', '0 1.5 0');
      entity.appendChild(text);

      scene.appendChild(entity);
    });

    const container = arContainerRef.current;
    container.appendChild(scene);

    // Cleanup
    return () => {
      if (container && scene.parentNode === container) {
        container.removeChild(scene);
      }
    };
  }, [arReady, nearbyPeaks, getMarkerColor]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg p-6 max-w-md text-center">
          <div className="text-4xl mb-4">📍</div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">AR View Unavailable</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link href="/" className="text-blue-600 hover:underline">
            ← Back to Peaks
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin w-12 h-12 border-4 border-white border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-lg">Initializing AR...</p>
          <p className="text-sm text-gray-400 mt-2">Please allow camera and location access</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ar-container" style={{ position: 'fixed', inset: 0 }}>
      {/* AR Scene container */}
      <div ref={arContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* UI Overlay */}
      <div className="fixed top-0 left-0 right-0 z-50 p-4 pointer-events-none">
        <div className="flex items-center justify-between">
          <Link
            href="/map"
            className="pointer-events-auto bg-black/70 text-white px-4 py-2 rounded-full text-sm font-medium backdrop-blur-sm"
          >
            ← Exit AR
          </Link>
          <div className="bg-black/70 text-white px-4 py-2 rounded-full text-sm backdrop-blur-sm">
            {nearbyPeaks.length} peaks nearby
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="fixed bottom-4 left-4 right-4 z-50 pointer-events-none">
        <div className="bg-black/70 backdrop-blur-sm rounded-lg p-4 text-white max-w-sm mx-auto">
          <h3 className="font-semibold mb-2 text-center">Point your camera at the mountains</h3>
          <div className="flex justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
              <span>Fourteener</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-sky-500 rounded-full"></div>
              <span>Thirteener</span>
            </div>
          </div>
          {userLocation && (
            <p className="text-xs text-gray-400 text-center mt-2">
              Your location: {userLocation.lat.toFixed(4)}°, {userLocation.lng.toFixed(4)}°
            </p>
          )}
        </div>
      </div>

      {/* Instructions modal for first-time users */}
      {arReady && nearbyPeaks.length === 0 && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md text-center">
            <div className="text-4xl mb-4">🏔️</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">No Peaks Nearby</h2>
            <p className="text-gray-600 mb-4">
              You need to be within 100 miles of Colorado&apos;s peaks to use AR view.
            </p>
            <Link
              href="/map"
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
            >
              View Map Instead
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
