import { notFound } from 'next/navigation';
import Link from 'next/link';
import { Metadata } from 'next';
import { getAllPeaks, getPeakBySlug, getNearbyPeaks } from '@/lib/peaks';
import { formatElevation, formatCoordinates, getDifficultyColor, getDifficultyDescription, getGoogleMapsUrl, cn } from '@/lib/utils';
import { PeakImage } from '@/components/PeakImage';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const peaks = getAllPeaks();
  return peaks.map((peak) => ({
    slug: peak.slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const peak = getPeakBySlug(slug);

  if (!peak) {
    return { title: 'Peak Not Found - Colorado 200' };
  }

  return {
    title: `${peak.name} - Colorado 200`,
    description: `${peak.name} is a ${peak.elevation.toLocaleString()} ft peak in the ${peak.range}. ${peak.funFact}`,
    openGraph: {
      title: peak.name,
      description: `Elevation: ${peak.elevation.toLocaleString()} ft | ${peak.range}`,
      images: [peak.imageUrl],
    },
  };
}

export default async function PeakDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const peak = getPeakBySlug(slug);

  if (!peak) {
    notFound();
  }

  const nearbyPeaks = getNearbyPeaks(peak, 15);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <ol className="flex items-center space-x-2 text-sm text-gray-500">
          <li>
            <Link href="/" className="hover:text-gray-700">Peaks</Link>
          </li>
          <li>/</li>
          <li className="text-gray-900 font-medium">{peak.name}</li>
        </ol>
      </nav>

      {/* Hero image */}
      <div className="relative h-64 md:h-96 rounded-xl overflow-hidden mb-8">
        <PeakImage
          src={peak.imageUrl}
          alt={peak.name}
          fill
          className="object-cover"
          priority
          sizes="(max-width: 1200px) 100vw, 1200px"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <span className="bg-black/50 px-3 py-1 rounded-full text-sm font-medium">
              #{peak.rank}
            </span>
            <span className={cn(
              'px-3 py-1 rounded-full text-sm font-medium',
              peak.category === 'fourteener' ? 'bg-amber-500' : 'bg-sky-500'
            )}>
              {peak.category === 'fourteener' ? 'Fourteener' : 'Thirteener'}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold">{peak.name}</h1>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-500 mb-1">Elevation</div>
              <div className="text-xl font-bold text-gray-900">{formatElevation(peak.elevation)}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-500 mb-1">Prominence</div>
              <div className="text-xl font-bold text-gray-900">{formatElevation(peak.prominence)}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-500 mb-1">Difficulty</div>
              <div className={cn('text-lg font-bold px-2 py-0.5 rounded inline-block', getDifficultyColor(peak.difficulty))}>
                {peak.difficulty}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-500 mb-1">Mountain Range</div>
              <div className="text-lg font-semibold text-gray-900">{peak.range}</div>
            </div>
          </div>

          {/* Fun fact */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">Did You Know?</h2>
            <p className="text-blue-800">{peak.funFact}</p>
          </div>

          {/* Difficulty description */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Difficulty Rating</h2>
            <div className={cn('inline-block px-3 py-1 rounded-lg text-sm font-medium mb-3', getDifficultyColor(peak.difficulty))}>
              {peak.difficulty}
            </div>
            <p className="text-gray-600">{getDifficultyDescription(peak.difficulty)}</p>
          </div>

          {/* Coordinates */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Location</h2>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <div className="text-sm text-gray-500 mb-1">Coordinates</div>
                <div className="font-mono text-gray-900">{formatCoordinates(peak.latitude, peak.longitude)}</div>
              </div>
              <a
                href={getGoogleMapsUrl(peak.latitude, peak.longitude)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Open in Google Maps
              </a>
            </div>
          </div>
        </div>

        {/* Right column - Actions & Nearby */}
        <div className="space-y-6">
          {/* Actions card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Track Your Summit</h2>
            <button className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors mb-3">
              Mark as Summited
            </button>
            <p className="text-sm text-gray-500 text-center">
              Sign in to track your summit history
            </p>
          </div>

          {/* Nearby peaks */}
          {nearbyPeaks.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Nearby Peaks</h2>
              <div className="space-y-3">
                {nearbyPeaks.map((nearby) => (
                  <Link
                    key={nearby.id}
                    href={`/peaks/${nearby.slug}`}
                    className="block p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <div className="font-medium text-gray-900">{nearby.name}</div>
                    <div className="text-sm text-gray-500">{formatElevation(nearby.elevation)}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Back link */}
      <div className="mt-12">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to all peaks
        </Link>
      </div>
    </div>
  );
}
