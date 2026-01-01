export interface Peak {
  id: string;
  name: string;
  slug: string;
  elevation: number;
  range: string;
  latitude: number;
  longitude: number;
  prominence: number;
  difficulty: DifficultyClass;
  funFact: string;
  imageUrl: string;
  category: PeakCategory;
  rank: number;
}

export type DifficultyClass = 'Class 1' | 'Class 2' | 'Class 3' | 'Class 4' | 'Class 5';

export type PeakCategory = 'fourteener' | 'thirteener';

export type SortField = 'elevation' | 'name' | 'prominence' | 'difficulty';
export type SortOrder = 'asc' | 'desc';

export interface PeakFilters {
  search?: string;
  range?: string;
  difficulty?: DifficultyClass;
  category?: PeakCategory;
  minElevation?: number;
  maxElevation?: number;
}

export interface PeakSort {
  field: SortField;
  order: SortOrder;
}

export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
  createdAt: Date;
}

export interface Summit {
  id: string;
  odlerId: string;
  peakId: string;
  summitDate?: Date;
  notes?: string;
  createdAt: Date;
}

export interface UserStats {
  totalSummited: number;
  fourteenersSummited: number;
  thirteenersSummited: number;
  totalElevationGained: number;
  percentComplete: number;
}
