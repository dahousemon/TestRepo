//
//  RouteOptimizerViewModel.swift
//  ColoradoPeaksExplorer
//
//  Created by Claude Code
//  View model for managing route optimization state
//

import Foundation
import Combine

class RouteOptimizerViewModel: ObservableObject {
    @Published var availablePeaks: [Peak] = []
    @Published var selectedPeaks: Set<String> = [] // Set of peak IDs
    @Published var optimizationResult: RouteOptimizationResult?
    @Published var isOptimizing: Bool = false
    @Published var returnToStart: Bool = false
    @Published var sortOption: SortOption = .bySelection

    private let peakDataService: PeakDataService
    private var cancellables = Set<AnyCancellable>()

    enum SortOption: String, CaseIterable {
        case bySelection = "Selection Order"
        case byElevation = "Elevation"
        case byName = "Name"
        case byOptimized = "Optimized Route"
    }

    init(peakDataService: PeakDataService = PeakDataService.shared) {
        self.peakDataService = peakDataService

        // Subscribe to peak data updates
        peakDataService.$peaks
            .assign(to: &$availablePeaks)
    }

    // MARK: - Peak Selection

    func togglePeakSelection(_ peak: Peak) {
        if selectedPeaks.contains(peak.id) {
            selectedPeaks.remove(peak.id)
        } else {
            selectedPeaks.insert(peak.id)
        }
        // Clear optimization when selection changes
        if sortOption == .byOptimized {
            optimizationResult = nil
        }
    }

    func selectAll() {
        selectedPeaks = Set(availablePeaks.map { $0.id })
    }

    func clearSelection() {
        selectedPeaks.removeAll()
        optimizationResult = nil
    }

    func selectFourteeners() {
        selectedPeaks = Set(availablePeaks.filter { $0.elevation >= 14000 }.map { $0.id })
    }

    func selectRange(_ range: String) {
        selectedPeaks = Set(availablePeaks.filter { $0.range == range }.map { $0.id })
    }

    // MARK: - Route Optimization

    func optimizeRoute() {
        guard !selectedPeaks.isEmpty else { return }

        isOptimizing = true

        // Perform optimization on background thread
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }

            let selectedPeakObjects = self.availablePeaks.filter { self.selectedPeaks.contains($0.id) }

            let result = TravelingSalesmanSolver.optimizeRoute(
                peaks: selectedPeakObjects,
                returnToStart: self.returnToStart
            )

            // Update on main thread
            DispatchQueue.main.async {
                self.optimizationResult = result
                self.isOptimizing = false
            }
        }
    }

    // MARK: - Computed Properties

    var selectedPeakObjects: [Peak] {
        let peaks = availablePeaks.filter { selectedPeaks.contains($0.id) }

        switch sortOption {
        case .bySelection:
            return peaks
        case .byElevation:
            return peaks.sorted { $0.elevation > $1.elevation }
        case .byName:
            return peaks.sorted { $0.name < $1.name }
        case .byOptimized:
            return optimizationResult?.orderedPeaks ?? peaks
        }
    }

    var selectedCount: Int {
        selectedPeaks.count
    }

    var hasOptimization: Bool {
        optimizationResult != nil
    }

    // MARK: - Available Ranges

    var availableRanges: [String] {
        let ranges = Set(availablePeaks.map { $0.range })
        return ranges.sorted()
    }
}
