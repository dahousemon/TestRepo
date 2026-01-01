'use client';

interface SummitButtonProps {
  peakId: string;
  peakName: string;
  isSummited?: boolean;
  compact?: boolean;
}

export function SummitButton({ peakName, compact = true }: SummitButtonProps) {
  const handleClick = () => {
    alert(`Summit tracking for ${peakName} coming soon!`);
  };

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className="p-2 rounded-lg transition-colors bg-gray-100 text-gray-600 hover:bg-gray-200"
        title={`Mark ${peakName} as summited (coming soon)`}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      className="w-full py-3 rounded-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700"
    >
      Mark as Summited
    </button>
  );
}
