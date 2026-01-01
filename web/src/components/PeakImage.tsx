'use client';

import { useState } from 'react';
import Image from 'next/image';

interface PeakImageProps {
  src: string;
  alt: string;
  fill?: boolean;
  priority?: boolean;
  className?: string;
  sizes?: string;
}

export function PeakImage({ src, alt, fill, priority, className, sizes }: PeakImageProps) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  // Generate a gradient based on the alt text for consistent fallback colors
  const getGradient = (text: string) => {
    const hash = text.split('').reduce((a, b) => ((a << 5) - a) + b.charCodeAt(0), 0);
    const hue1 = Math.abs(hash) % 360;
    const hue2 = (hue1 + 40) % 360;
    return `linear-gradient(135deg, hsl(${hue1}, 60%, 40%) 0%, hsl(${hue2}, 70%, 30%) 100%)`;
  };

  if (error) {
    return (
      <div
        className={`flex items-center justify-center ${className || ''}`}
        style={{
          background: getGradient(alt),
          position: fill ? 'absolute' : 'relative',
          inset: fill ? 0 : undefined,
          width: fill ? undefined : '100%',
          height: fill ? undefined : '100%',
        }}
      >
        <div className="text-center text-white p-4">
          <svg
            className="w-12 h-12 mx-auto mb-2 opacity-80"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M5 3l14 9-14 9V3z M12 2L2 22h20L12 2z"
            />
          </svg>
          <span className="text-sm font-medium opacity-90">{alt}</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {loading && (
        <div
          className="absolute inset-0 animate-pulse"
          style={{ background: getGradient(alt) }}
        />
      )}
      <Image
        src={src}
        alt={alt}
        fill={fill}
        priority={priority}
        className={className}
        sizes={sizes}
        onError={() => setError(true)}
        onLoad={() => setLoading(false)}
      />
    </>
  );
}
