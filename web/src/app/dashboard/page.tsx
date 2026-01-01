import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
      <div className="text-6xl mb-6">🏔️</div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">
        Dashboard Coming Soon
      </h1>
      <p className="text-gray-600 mb-8 max-w-md mx-auto">
        User accounts and summit tracking will be available soon.
        For now, explore Colorado&apos;s 200 highest peaks!
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          href="/"
          className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Explore Peaks
        </Link>
        <Link
          href="/map"
          className="inline-flex items-center justify-center px-6 py-3 bg-white text-gray-700 rounded-lg font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          View Map
        </Link>
      </div>
    </div>
  );
}
