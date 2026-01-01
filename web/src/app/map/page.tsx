'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { getAllPeaks, getUniqueRanges, filterPeaks } from '@/lib/peaks';
import { PeakFilters, Peak } from '@/types/peak';
import { formatElevation, getDifficultyColor, cn } from '@/lib/utils';

export default function MapPage() {
  const [filters, setFilters] = useState<PeakFilters>({});
  const [selectedPeak, setSelectedPeak] = useState<Peak | null>(null);

  const allPeaks = useMemo(() => getAllPeaks(), []);
  const ranges = useMemo(() => getUniqueRanges(), []);

  const filteredPeaks = useMemo(() => {
    return filterPeaks(allPeaks, filters);
  }, [allPeaks, filters]);

  // Calculate map bounds
  const bounds = useMemo(() => {
    if (filteredPeaks.length === 0) return { minLat: 37, maxLat: 41, minLng: -109, maxLng: -102 };

    return {
      minLat: Math.min(...filteredPeaks.map(p => p.latitude)),
      maxLat: Math.max(...filteredPeaks.map(p => p.latitude)),
      minLng: Math.min(...filteredPeaks.map(p => p.longitude)),
      maxLng: Math.max(...filteredPeaks.map(p => p.longitude)),
    };
  }, [filteredPeaks]);

  // Transform coordinates to SVG positions
  const getPosition = (lat: number, lng: number) => {
    const padding = 0.5;
    const x = ((lng - (bounds.minLng - padding)) / ((bounds.maxLng + padding) - (bounds.minLng - padding))) * 100;
    const y = 100 - ((lat - (bounds.minLat - padding)) / ((bounds.maxLat + padding) - (bounds.minLat - padding))) * 100;
    return { x, y };
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col lg:flex-row">
      {/* Sidebar */}
      <aside className="w-full lg:w-80 bg-white border-b lg:border-b-0 lg:border-r border-gray-200 p-4 overflow-y-auto">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Peak Map</h1>

        {/* Filters */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Category</label>
            <div className="flex gap-2">
              <button
                onClick={() => setFilters({ ...filters, category: undefined })}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg border transition-colors flex-1',
                  !filters.category ? 'bg-blue-50 border-blue-300 text-blue-700' : 'bg-white border-gray-300'
                )}
              >
                All
              </button>
              <button
                onClick={() => setFilters({ ...filters, category: 'fourteener' })}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg border transition-colors flex-1',
                  filters.category === 'fourteener' ? 'bg-amber-50 border-amber-300 text-amber-700' : 'bg-white border-gray-300'
                )}
              >
                14ers
              </button>
              <button
                onClick={() => setFilters({ ...filters, category: 'thirteener' })}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg border transition-colors flex-1',
                  filters.category === 'thirteener' ? 'bg-sky-50 border-sky-300 text-sky-700' : 'bg-white border-gray-300'
                )}
              >
                13ers
              </button>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Range</label>
            <select
              value={filters.range || ''}
              onChange={(e) => setFilters({ ...filters, range: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Ranges</option>
              {ranges.map((range) => (
                <option key={range} value={range}>{range}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="text-sm text-gray-600">
            Showing <span className="font-semibold text-gray-900">{filteredPeaks.length}</span> peaks
          </div>
        </div>

        {/* Legend */}
        <div className="border-t border-gray-200 pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Legend</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span>Fourteener (14,000+ ft)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-sky-500"></div>
              <span>Thirteener (13,000+ ft)</span>
            </div>
          </div>
        </div>

        {/* Selected peak info */}
        {selectedPeak && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <h3 className="font-semibold text-gray-900 mb-2">{selectedPeak.name}</h3>
            <div className="space-y-1 text-sm text-gray-600 mb-3">
              <div>Elevation: {formatElevation(selectedPeak.elevation)}</div>
              <div>Range: {selectedPeak.range}</div>
              <div className={cn('inline-block px-2 py-0.5 rounded text-xs', getDifficultyColor(selectedPeak.difficulty))}>
                {selectedPeak.difficulty}
              </div>
            </div>
            <Link
              href={`/peaks/${selectedPeak.slug}`}
              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              View Details
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        )}
      </aside>

      {/* Map area */}
      <div className="flex-1 bg-gray-100 relative">
        {/* SVG Map placeholder */}
        <svg
          viewBox="0 0 100 100"
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Background */}
          <rect width="100" height="100" fill="#e5e7eb" />

          {/* Grid lines */}
          {[0, 20, 40, 60, 80, 100].map((pos) => (
            <g key={pos}>
              <line x1={pos} y1="0" x2={pos} y2="100" stroke="#d1d5db" strokeWidth="0.2" />
              <line x1="0" y1={pos} x2="100" y2={pos} stroke="#d1d5db" strokeWidth="0.2" />
            </g>
          ))}

          {/* Peak markers */}
          {filteredPeaks.map((peak) => {
            const { x, y } = getPosition(peak.latitude, peak.longitude);
            const isSelected = selectedPeak?.id === peak.id;
            const color = peak.category === 'fourteener' ? '#f59e0b' : '#0ea5e9';

            return (
              <g key={peak.id}>
                <circle
                  cx={x}
                  cy={y}
                  r={isSelected ? 2 : 1.2}
                  fill={color}
                  stroke={isSelected ? '#1f2937' : 'white'}
                  strokeWidth={isSelected ? 0.4 : 0.2}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setSelectedPeak(peak)}
                />
                {isSelected && (
                  <text
                    x={x}
                    y={y - 3}
                    textAnchor="middle"
                    fontSize="2"
                    fill="#1f2937"
                    fontWeight="bold"
                  >
                    {peak.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Map instructions overlay */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg px-4 py-2 text-sm text-gray-600 shadow-sm">
          Click a peak marker to see details. For full interactive map, integrate Mapbox or Google Maps.
        </div>
      </div>
    </div>
  );
}
