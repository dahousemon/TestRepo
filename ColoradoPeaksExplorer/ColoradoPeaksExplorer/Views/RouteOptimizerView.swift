//
//  RouteOptimizerView.swift
//  ColoradoPeaksExplorer
//
//  Created by Claude Code
//  UI for selecting peaks and optimizing travel routes using TSP solver
//

import SwiftUI

struct RouteOptimizerView: View {
    @StateObject private var viewModel = RouteOptimizerViewModel()
    @State private var showingQuickSelect = false

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Stats Header
                if viewModel.selectedCount > 0 {
                    statsHeader
                }

                // Peak Selection List
                peakSelectionList

                // Optimization Controls
                if viewModel.selectedCount >= 2 {
                    optimizationControls
                }
            }
            .navigationTitle("Route Optimizer")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    quickSelectButton
                }
            }
            .sheet(isPresented: $showingQuickSelect) {
                quickSelectSheet
            }
        }
    }

    // MARK: - Stats Header

    private var statsHeader: some View {
        VStack(spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(viewModel.selectedCount) peaks selected")
                        .font(.headline)

                    if let result = viewModel.optimizationResult {
                        Text("Total: \(String(format: "%.1f", result.totalDistance)) mi • \(result.totalElevationGain.formatted()) ft gain")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                if viewModel.selectedCount > 0 {
                    Button(action: viewModel.clearSelection) {
                        Text("Clear")
                            .font(.subheadline)
                            .foregroundColor(.red)
                    }
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 12)

            // Sort Picker
            if viewModel.selectedCount > 0 {
                Picker("Sort By", selection: $viewModel.sortOption) {
                    ForEach(RouteOptimizerViewModel.SortOption.allCases, id: \.self) { option in
                        Text(option.rawValue).tag(option)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .padding(.bottom, 8)
            }
        }
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - Peak Selection List

    private var peakSelectionList: some View {
        List {
            if viewModel.selectedCount > 0 {
                Section(header: Text("Selected Peaks")) {
                    ForEach(Array(viewModel.selectedPeakObjects.enumerated()), id: \.element.id) { index, peak in
                        PeakSelectionRow(
                            peak: peak,
                            isSelected: true,
                            routeIndex: viewModel.sortOption == .byOptimized ? index + 1 : nil,
                            nextSegment: getSegment(for: index)
                        ) {
                            viewModel.togglePeakSelection(peak)
                        }
                    }
                }
            }

            Section(header: Text("Available Peaks")) {
                ForEach(viewModel.availablePeaks.filter { !viewModel.selectedPeaks.contains($0.id) }) { peak in
                    PeakSelectionRow(
                        peak: peak,
                        isSelected: false,
                        routeIndex: nil,
                        nextSegment: nil
                    ) {
                        viewModel.togglePeakSelection(peak)
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
    }

    // MARK: - Optimization Controls

    private var optimizationControls: some View {
        VStack(spacing: 12) {
            Toggle("Return to start", isOn: $viewModel.returnToStart)
                .padding(.horizontal)

            Button(action: {
                viewModel.optimizeRoute()
            }) {
                HStack {
                    if viewModel.isOptimizing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Image(systemName: "map")
                    }

                    Text(viewModel.isOptimizing ? "Optimizing..." : "Optimize Route")
                        .fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(viewModel.isOptimizing ? Color.gray : Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .disabled(viewModel.isOptimizing || viewModel.selectedCount < 2)
            .padding(.horizontal)

            if let result = viewModel.optimizationResult {
                VStack(spacing: 8) {
                    NavigationLink(destination: RouteDetailView(result: result)) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Route optimized using \(result.algorithm)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                Text("Computed in \(String(format: "%.3f", result.computationTime))s")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }

                            Spacer()

                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.blue)
                        }
                        .padding(.horizontal)
                    }

                    Text("Tap to view detailed route visualization")
                        .font(.caption2)
                        .foregroundColor(.blue)
                }
            }
        }
        .padding(.vertical, 12)
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - Quick Select

    private var quickSelectButton: some View {
        Button(action: { showingQuickSelect = true }) {
            Image(systemName: "line.3.horizontal.decrease.circle")
        }
    }

    private var quickSelectSheet: some View {
        NavigationView {
            List {
                Section {
                    Button("Select All Peaks") {
                        viewModel.selectAll()
                        showingQuickSelect = false
                    }

                    Button("All Fourteeners (14,000+ ft)") {
                        viewModel.selectFourteeners()
                        showingQuickSelect = false
                    }
                }

                Section(header: Text("By Mountain Range")) {
                    ForEach(viewModel.availableRanges, id: \.self) { range in
                        Button(range) {
                            viewModel.selectRange(range)
                            showingQuickSelect = false
                        }
                    }
                }

                Section {
                    Button("Clear Selection") {
                        viewModel.clearSelection()
                        showingQuickSelect = false
                    }
                    .foregroundColor(.red)
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Quick Select")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        showingQuickSelect = false
                    }
                }
            }
        }
    }

    // MARK: - Helper Methods

    private func getSegment(for index: Int) -> RouteSegment? {
        guard viewModel.sortOption == .byOptimized,
              let result = viewModel.optimizationResult,
              index < result.routeSegments.count else {
            return nil
        }
        return result.routeSegments[index]
    }
}

// MARK: - Peak Selection Row

struct PeakSelectionRow: View {
    let peak: Peak
    let isSelected: Bool
    let routeIndex: Int?
    let nextSegment: RouteSegment?
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            HStack(spacing: 12) {
                // Selection indicator / Route number
                if let index = routeIndex {
                    ZStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 32, height: 32)

                        Text("\(index)")
                            .font(.system(.subheadline, design: .rounded))
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                    }
                } else {
                    Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                        .foregroundColor(isSelected ? .blue : .gray)
                        .font(.title3)
                }

                // Peak info
                VStack(alignment: .leading, spacing: 4) {
                    Text(peak.name)
                        .font(.headline)
                        .foregroundColor(.primary)

                    HStack {
                        Text("\(peak.elevation.formatted()) ft")
                            .font(.subheadline)

                        Text("•")

                        Text(peak.range)
                            .font(.subheadline)
                    }
                    .foregroundColor(.secondary)

                    // Route segment info
                    if let segment = nextSegment {
                        HStack(spacing: 6) {
                            Image(systemName: "arrow.right")
                                .font(.caption2)

                            Text("\(String(format: "%.1f", segment.distance)) mi")

                            if segment.elevationChange != 0 {
                                Image(systemName: segment.elevationChange > 0 ? "arrow.up.right" : "arrow.down.right")
                                    .font(.caption2)

                                Text("\(abs(segment.elevationChange).formatted()) ft")
                            }

                            Text("→ \(segment.to.name)")
                                .lineLimit(1)
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                }

                Spacer()
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

struct RouteOptimizerView_Previews: PreviewProvider {
    static var previews: some View {
        RouteOptimizerView()
    }
}
