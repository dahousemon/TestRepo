'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { getAllPeaks, getUniqueRanges, filterPeaks } from '@/lib/peaks';
import { PeakFilters, Peak } from '@/types/peak';
import { formatElevation, getDifficultyColor, cn } from '@/lib/utils';

// Dynamically import MapView to avoid SSR issues with Mapbox
const MapView = dynamic(() => import('@/components/MapView').then(mod => mod.MapView), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">Loading map...</p>
      </div>
    </div>
  ),
});

export default function MapPage() {
  const [filters, setFilters] = useState<PeakFilters>({});
  const [selectedPeak, setSelectedPeak] = useState<Peak | null>(null);

  const allPeaks = useMemo(() => getAllPeaks(), []);
  const ranges = useMemo(() => getUniqueRanges(), []);

  const filteredPeaks = useMemo(() => {
    return filterPeaks(allPeaks, filters);
  }, [allPeaks, filters]);

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col lg:flex-row">
      {/* Sidebar */}
      <aside className="w-full lg:w-80 bg-white border-b lg:border-b-0 lg:border-r border-gray-200 p-4 overflow-y-auto flex-shrink-0">
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
              <span className="text-gray-800">Fourteener (14,000+ ft)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-sky-500"></div>
              <span className="text-gray-800">Thirteener (13,000+ ft)</span>
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

        {/* Peak list */}
        <div className="border-t border-gray-200 pt-4 mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Peak List</h3>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {filteredPeaks.slice(0, 20).map((peak) => (
              <button
                key={peak.id}
                onClick={() => setSelectedPeak(peak)}
                className={cn(
                  'w-full text-left px-2 py-1.5 rounded text-sm transition-colors',
                  selectedPeak?.id === peak.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'hover:bg-gray-50 text-gray-700'
                )}
              >
                <div className="font-medium truncate">{peak.name}</div>
                <div className="text-xs text-gray-500">{formatElevation(peak.elevation)}</div>
              </button>
            ))}
            {filteredPeaks.length > 20 && (
              <p className="text-xs text-gray-500 text-center py-2">
                +{filteredPeaks.length - 20} more peaks
              </p>
            )}
          </div>
        </div>
      </aside>

      {/* Map area */}
      <div className="flex-1 min-h-[400px] lg:min-h-0">
        <MapView
          peaks={filteredPeaks}
          selectedPeak={selectedPeak}
          onPeakSelect={setSelectedPeak}
        />
      </div>
    </div>
  );
}
