import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

export function formatElevation(feet: number): string {
  return `${feet.toLocaleString()} ft`;
}

export function formatCoordinates(lat: number, lng: number): string {
  return `${lat.toFixed(4)}°, ${lng.toFixed(4)}°`;
}

export function getDifficultyColor(difficulty: string): string {
  switch (difficulty) {
    case 'Class 1':
      return 'bg-green-100 text-green-800';
    case 'Class 2':
      return 'bg-blue-100 text-blue-800';
    case 'Class 3':
      return 'bg-yellow-100 text-yellow-800';
    case 'Class 4':
      return 'bg-orange-100 text-orange-800';
    case 'Class 5':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getDifficultyDescription(difficulty: string): string {
  switch (difficulty) {
    case 'Class 1':
      return 'Hiking on a trail. No technical skills required.';
    case 'Class 2':
      return 'Simple scrambling with possible use of hands.';
    case 'Class 3':
      return 'Scrambling with increased exposure. Handholds necessary.';
    case 'Class 4':
      return 'Simple climbing with exposure. A rope is often used.';
    case 'Class 5':
      return 'Technical rock climbing. Rope and protection required.';
    default:
      return 'Unknown difficulty level.';
  }
}

export function getGoogleMapsUrl(lat: number, lng: number): string {
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
}
