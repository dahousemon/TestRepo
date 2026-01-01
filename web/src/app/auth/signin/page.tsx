import Link from 'next/link';

export default function SignInPage() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-6xl mb-6">🔐</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Sign In Coming Soon
        </h1>
        <p className="text-gray-600 mb-8">
          User authentication will be available soon.
          For now, explore the peaks without signing in!
        </p>
        <Link
          href="/"
          className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Explore Peaks
        </Link>
      </div>
    </div>
  );
}
