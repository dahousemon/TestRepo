import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import { getUserStats, getUserSummits } from '@/lib/users';
import { getAllPeaks } from '@/lib/peaks';
import { formatElevation } from '@/lib/utils';
import Link from 'next/link';
import { SummitButton } from '@/components/SummitButton';

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect('/auth/signin?callbackUrl=/dashboard');
  }

  const stats = getUserStats(session.user.id);
  const summits = getUserSummits(session.user.id);
  const allPeaks = getAllPeaks();

  const summitedPeakIds = new Set(summits.map(s => s.peakId));
  const summitedPeaks = allPeaks.filter(p => summitedPeakIds.has(p.id));
  const remainingPeaks = allPeaks.filter(p => !summitedPeakIds.has(p.id)).slice(0, 6);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {session.user.name}!
        </h1>
        <p className="text-gray-600 mt-2">
          Track your progress climbing Colorado&apos;s 200 highest peaks.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
          <div className="text-4xl font-bold text-gray-900">{stats.totalSummited}</div>
          <div className="text-sm text-gray-500 mt-1">Peaks Summited</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
          <div className="text-4xl font-bold text-amber-600">{stats.fourteenersSummited}</div>
          <div className="text-sm text-gray-500 mt-1">Fourteeners</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
          <div className="text-4xl font-bold text-sky-600">{stats.thirteenersSummited}</div>
          <div className="text-sm text-gray-500 mt-1">Thirteeners</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
          <div className="text-4xl font-bold text-green-600">{stats.percentComplete}%</div>
          <div className="text-sm text-gray-500 mt-1">Complete</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center col-span-2 md:col-span-1">
          <div className="text-2xl font-bold text-gray-900">
            {(stats.totalElevationGained / 1000).toFixed(0)}k
          </div>
          <div className="text-sm text-gray-500 mt-1">Feet Climbed</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900">Overall Progress</h2>
          <span className="text-sm text-gray-500">
            {stats.totalSummited} of 200 peaks
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full transition-all duration-500"
            style={{ width: `${stats.percentComplete}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Summited Peaks */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Your Summits ({summitedPeaks.length})
            </h2>
          </div>

          {summitedPeaks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🏔️</div>
              <p>No summits yet. Start your journey!</p>
              <Link
                href="/"
                className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                Explore Peaks
              </Link>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {summitedPeaks.map((peak) => {
                const summit = summits.find(s => s.peakId === peak.id);
                return (
                  <Link
                    key={peak.id}
                    href={`/peaks/${peak.slug}`}
                    className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-colors"
                  >
                    <div>
                      <div className="font-medium text-gray-900">{peak.name}</div>
                      <div className="text-sm text-gray-500">
                        {formatElevation(peak.elevation)}
                        {summit?.summitDate && (
                          <span className="ml-2">
                            • Summited {new Date(summit.summitDate).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-green-600 text-xl">✓</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Suggested Next Peaks */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Suggested Next Peaks
          </h2>

          <div className="space-y-3">
            {remainingPeaks.map((peak) => (
              <div
                key={peak.id}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <Link href={`/peaks/${peak.slug}`} className="flex-1">
                  <div className="font-medium text-gray-900">{peak.name}</div>
                  <div className="text-sm text-gray-500">
                    {formatElevation(peak.elevation)} • {peak.difficulty}
                  </div>
                </Link>
                <SummitButton peakId={peak.id} peakName={peak.name} isSummited={false} />
              </div>
            ))}
          </div>

          <Link
            href="/"
            className="block mt-4 text-center text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View all peaks →
          </Link>
        </div>
      </div>
    </div>
  );
}
