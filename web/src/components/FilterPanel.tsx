'use client';

import { useState } from 'react';
import { DifficultyClass, PeakCategory, PeakFilters, PeakSort, SortField } from '@/types/peak';
import { cn } from '@/lib/utils';

interface FilterPanelProps {
  filters: PeakFilters;
  sort: PeakSort;
  ranges: string[];
  onFiltersChange: (filters: PeakFilters) => void;
  onSortChange: (sort: PeakSort) => void;
  resultCount: number;
}

const difficulties: DifficultyClass[] = ['Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5'];
const categories: { value: PeakCategory | ''; label: string }[] = [
  { value: '', label: 'All Peaks' },
  { value: 'fourteener', label: 'Fourteeners (14ers)' },
  { value: 'thirteener', label: 'Thirteeners (13ers)' },
];

const sortOptions: { field: SortField; label: string }[] = [
  { field: 'elevation', label: 'Elevation' },
  { field: 'name', label: 'Name' },
  { field: 'prominence', label: 'Prominence' },
  { field: 'difficulty', label: 'Difficulty' },
];

const distanceOptions = [
  { value: 25, label: '25 mi' },
  { value: 50, label: '50 mi' },
  { value: 100, label: '100 mi' },
  { value: 200, label: '200 mi' },
];

export function FilterPanel({
  filters,
  sort,
  ranges,
  onFiltersChange,
  onSortChange,
  resultCount,
}: FilterPanelProps) {
  const [locationStatus, setLocationStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [locationError, setLocationError] = useState<string | null>(null);

  const handleClearFilters = () => {
    onFiltersChange({});
    setLocationStatus('idle');
    setLocationError(null);
  };

  const handleNearMe = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      setLocationStatus('error');
      return;
    }

    setLocationStatus('loading');
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationStatus('success');
        onFiltersChange({
          ...filters,
          userLocation: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
          maxDistance: filters.maxDistance || 100, // Default to 100 miles
        });
      },
      (error) => {
        setLocationStatus('error');
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location permission denied');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location unavailable');
            break;
          case error.TIMEOUT:
            setLocationError('Location request timed out');
            break;
          default:
            setLocationError('Failed to get location');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const handleClearLocation = () => {
    onFiltersChange({
      ...filters,
      userLocation: undefined,
      maxDistance: undefined,
    });
    setLocationStatus('idle');
    setLocationError(null);
  };

  const hasActiveFilters = !!(filters.range || filters.difficulty || filters.category || filters.userLocation);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-4">
      {/* Result count and clear */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">
          <span className="font-semibold text-gray-900">{resultCount}</span> peaks found
        </span>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Near Me */}
      <div>
        <label className="text-sm font-medium text-gray-700 mb-2 block">Near Me</label>
        {!filters.userLocation ? (
          <button
            onClick={handleNearMe}
            disabled={locationStatus === 'loading'}
            className={cn(
              'w-full px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors flex items-center justify-center gap-2',
              locationStatus === 'loading'
                ? 'bg-gray-100 border-gray-300 text-gray-500 cursor-wait'
                : 'bg-green-50 border-green-300 text-green-700 hover:bg-green-100'
            )}
          >
            {locationStatus === 'loading' ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Getting location...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Find peaks near me
              </>
            )}
          </button>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <span className="text-sm text-green-700 flex items-center gap-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Location enabled
              </span>
              <button
                onClick={handleClearLocation}
                className="text-sm text-green-600 hover:text-green-800 font-medium"
              >
                Clear
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {distanceOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => onFiltersChange({ ...filters, maxDistance: opt.value })}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                    filters.maxDistance === opt.value
                      ? 'bg-green-100 border-green-300 text-green-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {locationError && (
          <p className="mt-2 text-sm text-red-600">{locationError}</p>
        )}
      </div>

      {/* Sort */}
      <div className="flex flex-wrap gap-2">
        <label className="text-sm font-medium text-gray-700 w-full mb-1">Sort by</label>
        <div className="flex flex-wrap gap-2">
          {sortOptions.map((option) => (
            <button
              key={option.field}
              onClick={() => onSortChange({
                field: option.field,
                order: sort.field === option.field && sort.order === 'desc' ? 'asc' : 'desc'
              })}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                sort.field === option.field
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              )}
            >
              {option.label}
              {sort.field === option.field && (
                <span className="ml-1">{sort.order === 'desc' ? '↓' : '↑'}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Category filter */}
      <div>
        <label className="text-sm font-medium text-gray-700 mb-2 block">Category</label>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value || 'all'}
              onClick={() => onFiltersChange({ ...filters, category: cat.value || undefined })}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                (filters.category || '') === cat.value
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Range filter */}
      <div>
        <label className="text-sm font-medium text-gray-700 mb-2 block">Mountain Range</label>
        <select
          value={filters.range || ''}
          onChange={(e) => onFiltersChange({ ...filters, range: e.target.value || undefined })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Ranges</option>
          {ranges.map((range) => (
            <option key={range} value={range}>{range}</option>
          ))}
        </select>
      </div>

      {/* Difficulty filter */}
      <div>
        <label className="text-sm font-medium text-gray-700 mb-2 block">Difficulty</label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onFiltersChange({ ...filters, difficulty: undefined })}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg border transition-colors',
              !filters.difficulty
                ? 'bg-blue-50 border-blue-300 text-blue-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            All
          </button>
          {difficulties.map((diff) => (
            <button
              key={diff}
              onClick={() => onFiltersChange({ ...filters, difficulty: diff })}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                filters.difficulty === diff
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              )}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
