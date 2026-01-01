'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

interface SummitButtonProps {
  peakId: string;
  peakName: string;
  isSummited: boolean;
  compact?: boolean;
}

export function SummitButton({ peakId, peakName, isSummited, compact = true }: SummitButtonProps) {
  const { data: session } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [summited, setSummited] = useState(isSummited);

  const handleToggleSummit = async () => {
    if (!session) {
      router.push('/auth/signin?callbackUrl=' + encodeURIComponent(window.location.pathname));
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/summits', {
        method: summited ? 'DELETE' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peakId }),
      });

      if (response.ok) {
        setSummited(!summited);
        router.refresh();
      } else {
        const error = await response.json();
        alert(error.message || 'Failed to update summit');
      }
    } catch {
      alert('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handleToggleSummit}
        disabled={loading}
        className={`p-2 rounded-lg transition-colors ${
          summited
            ? 'bg-green-100 text-green-700 hover:bg-green-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        } disabled:opacity-50`}
        title={summited ? `Remove ${peakName} summit` : `Mark ${peakName} as summited`}
      >
        {loading ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : summited ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleToggleSummit}
      disabled={loading}
      className={`w-full py-3 rounded-lg font-medium transition-colors ${
        summited
          ? 'bg-green-600 text-white hover:bg-green-700'
          : 'bg-blue-600 text-white hover:bg-blue-700'
      } disabled:opacity-50`}
    >
      {loading
        ? 'Please wait...'
        : summited
          ? '✓ Summited'
          : 'Mark as Summited'}
    </button>
  );
}
