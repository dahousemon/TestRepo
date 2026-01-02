'use client';

import { useState, useMemo } from 'react';
import { SearchBar, FilterPanel, PeakList } from '@/components';
import { getAllPeaks, getUniqueRanges, filterPeaks, sortPeaks, getStats } from '@/lib/peaks';
import { PeakFilters, PeakSort } from '@/types/peak';

export default function HomePage() {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<PeakFilters>({});
  const [sort, setSort] = useState<PeakSort>({ field: 'elevation', order: 'desc' });

  const allPeaks = useMemo(() => getAllPeaks(), []);
  const ranges = useMemo(() => getUniqueRanges(), []);
  const stats = useMemo(() => getStats(), []);

  const filteredPeaks = useMemo(() => {
    const withSearch = filterPeaks(allPeaks, { ...filters, search });
    return sortPeaks(withSearch, sort);
  }, [allPeaks, filters, search, sort]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero section */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-white mb-4">
          Colorado&apos;s <span className="text-blue-400">200</span> Highest Peaks
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Explore all {stats.fourteeners} fourteeners and {stats.thirteeners} thirteeners.
          From Mount Elbert at {stats.highestPeak?.elevation.toLocaleString()} ft to the rugged wilderness of Colorado&apos;s high country.
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
          <div className="text-3xl font-bold text-gray-900">{stats.totalPeaks}</div>
          <div className="text-sm text-gray-500">Total Peaks</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
          <div className="text-3xl font-bold text-amber-600">{stats.fourteeners}</div>
          <div className="text-sm text-gray-500">Fourteeners</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
          <div className="text-3xl font-bold text-sky-600">{stats.thirteeners}</div>
          <div className="text-sm text-gray-500">Thirteeners</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
          <div className="text-3xl font-bold text-gray-900">{stats.totalRanges}</div>
          <div className="text-sm text-gray-500">Mountain Ranges</div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search by peak name or mountain range..."
          className="max-w-xl mx-auto"
        />
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters sidebar */}
        <aside className="lg:col-span-1">
          <FilterPanel
            filters={filters}
            sort={sort}
            ranges={ranges}
            onFiltersChange={setFilters}
            onSortChange={setSort}
            resultCount={filteredPeaks.length}
          />
        </aside>

        {/* Peak list */}
        <div className="lg:col-span-3">
          <PeakList peaks={filteredPeaks} />
        </div>
      </div>
    </div>
  );
}
