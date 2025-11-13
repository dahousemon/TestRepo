//
//  PeakDataService.swift
//  Colorado Peaks Explorer
//
//  Service for fetching, caching, and managing peak data
//

import Foundation
import Combine

class PeakDataService: ObservableObject {
    @Published var peaks: [Peak] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let cacheKey = "cachedPeaksData"
    private let cacheTimestampKey = "cachedPeaksTimestamp"
    private let cacheDuration: TimeInterval = 30 * 24 * 60 * 60 // 30 days in seconds

    private var cancellables = Set<AnyCancellable>()

    init() {
        loadPeaks()
    }

    /// Load peaks from cache or fetch from source
    func loadPeaks() {
        isLoading = true

        // Try to load from cache first
        if let cachedPeaks = loadFromCache(), !shouldRefreshCache() {
            self.peaks = cachedPeaks
            self.isLoading = false
            return
        }

        // Fetch from bundled JSON file (simulating API fetch)
        fetchPeaksFromBundle()
    }

    /// Fetch peaks from bundled JSON file
    private func fetchPeaksFromBundle() {
        guard let url = Bundle.main.url(forResource: "peaks_data", withExtension: "json") else {
            errorMessage = "Could not find peaks_data.json in bundle"
            isLoading = false
            return
        }

        do {
            let data = try Data(contentsOf: url)
            let peaksData = try JSONDecoder().decode(PeaksData.self, from: data)

            // Combine all peaks and sort by elevation (highest first)
            let allPeaks = peaksData.allPeaks.sorted { $0.elevation > $1.elevation }

            self.peaks = allPeaks
            saveToCache(allPeaks)
            isLoading = false
        } catch {
            errorMessage = "Error loading peaks: \(error.localizedDescription)"
            isLoading = false

            // Try to use cached data as fallback
            if let cachedPeaks = loadFromCache() {
                self.peaks = cachedPeaks
                errorMessage = "Using cached data due to loading error"
            }
        }
    }

    /// Save peaks to cache
    private func saveToCache(_ peaks: [Peak]) {
        do {
            let data = try JSONEncoder().encode(peaks)
            UserDefaults.standard.set(data, forKey: cacheKey)
            UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: cacheTimestampKey)
        } catch {
            print("Error saving peaks to cache: \(error)")
        }
    }

    /// Load peaks from cache
    private func loadFromCache() -> [Peak]? {
        guard let data = UserDefaults.standard.data(forKey: cacheKey) else {
            return nil
        }

        do {
            let peaks = try JSONDecoder().decode([Peak].self, from: data)
            return peaks
        } catch {
            print("Error loading peaks from cache: \(error)")
            return nil
        }
    }

    /// Check if cache should be refreshed (older than 30 days)
    private func shouldRefreshCache() -> Bool {
        let cachedTimestamp = UserDefaults.standard.double(forKey: cacheTimestampKey)
        let currentTimestamp = Date().timeIntervalSince1970

        return (currentTimestamp - cachedTimestamp) > cacheDuration
    }

    /// Force refresh data
    func refreshData() {
        fetchPeaksFromBundle()
    }

    /// Get peaks by category
    func peaks(for category: PeakCategory) -> [Peak] {
        return peaks.filter { $0.category == category }
            .sorted { $0.elevation > $1.elevation }
    }

    /// Get top N peaks
    func topPeaks(count: Int) -> [Peak] {
        return Array(peaks.prefix(count))
    }

    /// Search peaks by name
    func searchPeaks(query: String) -> [Peak] {
        if query.isEmpty {
            return peaks
        }

        return peaks.filter { peak in
            peak.name.localizedCaseInsensitiveContains(query) ||
            peak.range.localizedCaseInsensitiveContains(query)
        }
    }

    /// Filter peaks by elevation range
    func filterPeaks(minElevation: Int, maxElevation: Int) -> [Peak] {
        return peaks.filter { peak in
            peak.elevation >= minElevation && peak.elevation <= maxElevation
        }
    }
}
