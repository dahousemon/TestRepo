'use client';

import { DifficultyClass, PeakCategory, PeakFilters, PeakSort, SortField, SortOrder } from '@/types/peak';
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

export function FilterPanel({
  filters,
  sort,
  ranges,
  onFiltersChange,
  onSortChange,
  resultCount,
}: FilterPanelProps) {
  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = !!(filters.range || filters.difficulty || filters.category);

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
