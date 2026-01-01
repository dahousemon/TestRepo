'use client';

import Link from 'next/link';
import { Peak } from '@/types/peak';
import { formatElevation, getDifficultyColor, cn } from '@/lib/utils';
import { PeakImage } from './PeakImage';

interface PeakCardProps {
  peak: Peak;
  showRank?: boolean;
}

export function PeakCard({ peak, showRank = true }: PeakCardProps) {
  return (
    <Link href={`/peaks/${peak.slug}`}>
      <article className="group bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md hover:border-blue-300 transition-all duration-200">
        <div className="relative h-48 bg-gray-100">
          <PeakImage
            src={peak.imageUrl}
            alt={peak.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          {showRank && (
            <div className="absolute top-2 left-2 bg-black/70 text-white text-sm font-bold px-2 py-1 rounded">
              #{peak.rank}
            </div>
          )}
          <div className="absolute top-2 right-2">
            <span className={cn(
              'text-xs font-medium px-2 py-1 rounded',
              peak.category === 'fourteener'
                ? 'bg-amber-500 text-white'
                : 'bg-sky-500 text-white'
            )}>
              {peak.category === 'fourteener' ? '14er' : '13er'}
            </span>
          </div>
        </div>

        <div className="p-4">
          <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition-colors">
            {peak.name}
          </h3>

          <div className="mt-2 flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">
              {formatElevation(peak.elevation)}
            </span>
            <span className={cn(
              'text-xs font-medium px-2 py-1 rounded',
              getDifficultyColor(peak.difficulty)
            )}>
              {peak.difficulty}
            </span>
          </div>

          <div className="mt-2 text-sm text-gray-500">
            {peak.range}
          </div>

          <div className="mt-2 text-xs text-gray-400">
            Prominence: {formatElevation(peak.prominence)}
          </div>
        </div>
      </article>
    </Link>
  );
}
