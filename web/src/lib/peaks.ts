import { Peak, PeakFilters, PeakSort, DifficultyClass, PeakCategory } from '@/types/peak';
import peaksJson from '@/data/peaks_data.json';
import { slugify } from './utils';

interface RawPeak {
  id: string;
  name: string;
  elevation: number;
  range: string;
  latitude: number;
  longitude: number;
  prominence: number;
  difficulty: string;
  funFact: string;
  imageUrl: string;
  category: string;
}

interface PeaksData {
  top200Peaks: RawPeak[];
  frontRangePeaks: RawPeak[];
}

// Transform raw data to typed peaks
function transformPeaks(data: PeaksData): Peak[] {
  const allPeaks = data.top200Peaks.map((p, index) => ({
    ...p,
    slug: slugify(p.name),
    difficulty: p.difficulty as DifficultyClass,
    category: (p.elevation >= 14000 ? 'fourteener' : 'thirteener') as PeakCategory,
    rank: index + 1,
  }));

  return allPeaks;
}

// Cache transformed peaks
let cachedPeaks: Peak[] | null = null;

export function getAllPeaks(): Peak[] {
  if (!cachedPeaks) {
    cachedPeaks = transformPeaks(peaksJson as PeaksData);
  }
  return cachedPeaks;
}

export function getPeakBySlug(slug: string): Peak | undefined {
  return getAllPeaks().find(p => p.slug === slug);
}

export function getPeakById(id: string): Peak | undefined {
  return getAllPeaks().find(p => p.id === id);
}

export function getUniqueRanges(): string[] {
  const ranges = new Set(getAllPeaks().map(p => p.range));
  return Array.from(ranges).sort();
}

// Calculate distance between two coordinates in miles using Haversine formula
export function calculateDistance(
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number {
  const R = 3959; // Earth radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export function filterPeaks(peaks: Peak[], filters: PeakFilters): Peak[] {
  return peaks.filter(peak => {
    // Search filter
    if (filters.search) {
      const search = filters.search.toLowerCase();
      const matchesName = peak.name.toLowerCase().includes(search);
      const matchesRange = peak.range.toLowerCase().includes(search);
      if (!matchesName && !matchesRange) return false;
    }

    // Range filter
    if (filters.range && peak.range !== filters.range) return false;

    // Difficulty filter
    if (filters.difficulty && peak.difficulty !== filters.difficulty) return false;

    // Category filter
    if (filters.category && peak.category !== filters.category) return false;

    // Elevation range
    if (filters.minElevation && peak.elevation < filters.minElevation) return false;
    if (filters.maxElevation && peak.elevation > filters.maxElevation) return false;

    // Distance filter (Near Me)
    if (filters.maxDistance && filters.userLocation) {
      const distance = calculateDistance(
        filters.userLocation.latitude,
        filters.userLocation.longitude,
        peak.latitude,
        peak.longitude
      );
      if (distance > filters.maxDistance) return false;
    }

    return true;
  });
}

// Get peaks sorted by distance from a location
export function getPeaksByDistance(
  peaks: Peak[],
  userLat: number,
  userLon: number
): (Peak & { distance: number })[] {
  return peaks.map(peak => ({
    ...peak,
    distance: calculateDistance(userLat, userLon, peak.latitude, peak.longitude)
  })).sort((a, b) => a.distance - b.distance);
}

const difficultyOrder: Record<string, number> = {
  'Class 1': 1,
  'Class 2': 2,
  'Class 3': 3,
  'Class 4': 4,
  'Class 5': 5,
};

export function sortPeaks(peaks: Peak[], sort: PeakSort): Peak[] {
  const sorted = [...peaks];

  sorted.sort((a, b) => {
    let comparison = 0;

    switch (sort.field) {
      case 'elevation':
        comparison = a.elevation - b.elevation;
        break;
      case 'name':
        comparison = a.name.localeCompare(b.name);
        break;
      case 'prominence':
        comparison = a.prominence - b.prominence;
        break;
      case 'difficulty':
        comparison = difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        break;
    }

    return sort.order === 'asc' ? comparison : -comparison;
  });

  return sorted;
}

export function getNearbyPeaks(peak: Peak, radiusMiles: number = 10): Peak[] {
  const allPeaks = getAllPeaks();

  return allPeaks.filter(p => {
    if (p.id === peak.id) return false;

    // Haversine formula simplified for nearby peaks
    const lat1 = peak.latitude * Math.PI / 180;
    const lat2 = p.latitude * Math.PI / 180;
    const dLat = (p.latitude - peak.latitude) * Math.PI / 180;
    const dLon = (p.longitude - peak.longitude) * Math.PI / 180;

    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = 3959 * c; // Earth radius in miles

    return distance <= radiusMiles;
  }).slice(0, 5);
}

export function getStats() {
  const peaks = getAllPeaks();
  const fourteeners = peaks.filter(p => p.category === 'fourteener');
  const thirteeners = peaks.filter(p => p.category === 'thirteener');

  return {
    totalPeaks: peaks.length,
    fourteeners: fourteeners.length,
    thirteeners: thirteeners.length,
    highestPeak: peaks[0],
    totalRanges: getUniqueRanges().length,
  };
}
