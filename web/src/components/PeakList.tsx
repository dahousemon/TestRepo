'use client';

import { Peak } from '@/types/peak';
import { PeakCard } from './PeakCard';

interface PeakListProps {
  peaks: Peak[];
  loading?: boolean;
}

export function PeakList({ peaks, loading = false }: PeakListProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden animate-pulse">
            <div className="h-48 bg-gray-200" />
            <div className="p-4 space-y-3">
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-8 bg-gray-200 rounded w-1/2" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (peaks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">🏔️</div>
        <h3 className="text-lg font-medium text-gray-900">No peaks found</h3>
        <p className="text-gray-500 mt-1">Try adjusting your filters or search terms.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {peaks.map((peak) => (
        <PeakCard key={peak.id} peak={peak} />
      ))}
    </div>
  );
}
