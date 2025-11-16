//
//  RouteDetailView.swift
//  ColoradoPeaksExplorer
//
//  Created by Claude Code
//  Detailed visualization of an optimized route
//

import SwiftUI

struct RouteDetailView: View {
    let result: RouteOptimizationResult

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Summary Statistics
                summaryCard

                // Route Map Preview
                mapPreviewCard

                // Segment-by-Segment Breakdown
                segmentsList

                // Elevation Profile
                elevationProfileCard
            }
            .padding()
        }
        .navigationTitle("Route Details")
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Summary Card

    private var summaryCard: some View {
        VStack(spacing: 16) {
            Text("Route Summary")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 20) {
                StatBox(
                    icon: "mountain.2.fill",
                    value: "\(result.orderedPeaks.count)",
                    label: "Peaks"
                )

                StatBox(
                    icon: "point.topleft.down.curvedto.point.bottomright.up",
                    value: String(format: "%.1f", result.totalDistance),
                    label: "Miles"
                )

                StatBox(
                    icon: "arrow.up.forward",
                    value: "\(result.totalElevationGain.formatted())",
                    label: "Ft Gain"
                )
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "cpu")
                    Text("Algorithm:")
                    Spacer()
                    Text(result.algorithm)
                        .fontWeight(.medium)
                }
                .font(.subheadline)

                HStack {
                    Image(systemName: "clock")
                    Text("Computed in:")
                    Spacer()
                    Text(String(format: "%.3f seconds", result.computationTime))
                        .fontWeight(.medium)
                }
                .font(.subheadline)
            }
            .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 5, x: 0, y: 2)
    }

    // MARK: - Map Preview

    private var mapPreviewCard: some View {
        VStack(spacing: 12) {
            Text("Route Map")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            Button(action: openInGoogleMaps) {
                VStack(spacing: 12) {
                    Image(systemName: "map.fill")
                        .font(.system(size: 48))
                        .foregroundColor(.blue)

                    Text("Open Full Route in Google Maps")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text("View the complete route with turn-by-turn directions")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue.opacity(0.1))
                .cornerRadius(12)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 5, x: 0, y: 2)
    }

    // MARK: - Segments List

    private var segmentsList: some View {
        VStack(spacing: 12) {
            Text("Route Segments")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            ForEach(Array(result.routeSegments.enumerated()), id: \.offset) { index, segment in
                SegmentRow(
                    number: index + 1,
                    segment: segment,
                    isLast: index == result.routeSegments.count - 1
                )
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 5, x: 0, y: 2)
    }

    // MARK: - Elevation Profile

    private var elevationProfileCard: some View {
        VStack(spacing: 12) {
            Text("Elevation Profile")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Simple bar chart showing elevation changes
            VStack(spacing: 8) {
                ForEach(Array(result.orderedPeaks.enumerated()), id: \.element.id) { index, peak in
                    HStack {
                        Text("\(index + 1)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .frame(width: 30)

                        Text(peak.name)
                            .font(.caption)
                            .lineLimit(1)
                            .frame(width: 120, alignment: .leading)

                        GeometryReader { geometry in
                            ZStack(alignment: .leading) {
                                Rectangle()
                                    .fill(Color.gray.opacity(0.2))

                                Rectangle()
                                    .fill(elevationColor(for: peak.elevation))
                                    .frame(width: elevationBarWidth(for: peak.elevation, maxWidth: geometry.size.width))
                            }
                        }
                        .frame(height: 20)

                        Text("\(peak.elevation.formatted())")
                            .font(.caption)
                            .fontWeight(.medium)
                            .frame(width: 60, alignment: .trailing)
                    }
                }
            }

            HStack {
                Spacer()
                Text("Elevation in feet")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 5, x: 0, y: 2)
    }

    // MARK: - Helper Methods

    private func openInGoogleMaps() {
        let waypoints = result.orderedPeaks.map { "\($0.latitude),\($0.longitude)" }.joined(separator: "|")
        let urlString = "https://www.google.com/maps/dir/?api=1&waypoints=\(waypoints)&travelmode=driving"

        if let url = URL(string: urlString) {
            UIApplication.shared.open(url)
        }
    }

    private func elevationBarWidth(for elevation: Int, maxWidth: CGFloat) -> CGFloat {
        let minElevation = result.orderedPeaks.map { $0.elevation }.min() ?? 0
        let maxElevation = result.orderedPeaks.map { $0.elevation }.max() ?? 14433

        let normalized = Double(elevation - minElevation) / Double(maxElevation - minElevation)
        return maxWidth * CGFloat(normalized)
    }

    private func elevationColor(for elevation: Int) -> Color {
        if elevation >= 14000 {
            return .red
        } else if elevation >= 13500 {
            return .orange
        } else if elevation >= 13000 {
            return .blue
        } else {
            return .green
        }
    }
}

// MARK: - Supporting Views

struct StatBox: View {
    let icon: String
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)

            Text(value)
                .font(.title3)
                .fontWeight(.bold)

            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

struct SegmentRow: View {
    let number: Int
    let segment: RouteSegment
    let isLast: Bool

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                // Segment number
                ZStack {
                    Circle()
                        .fill(Color.blue)
                        .frame(width: 32, height: 32)

                    Text("\(number)")
                        .font(.subheadline)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(segment.from.name)
                            .font(.subheadline)
                            .fontWeight(.medium)

                        Text("→")
                            .foregroundColor(.secondary)

                        Text(segment.to.name)
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }

                    HStack(spacing: 12) {
                        Label(String(format: "%.1f mi", segment.distance), systemImage: "arrow.right")
                            .font(.caption)

                        if segment.elevationChange != 0 {
                            Label(
                                "\(abs(segment.elevationChange).formatted()) ft",
                                systemImage: segment.elevationChange > 0 ? "arrow.up" : "arrow.down"
                            )
                            .font(.caption)
                            .foregroundColor(segment.elevationChange > 0 ? .green : .red)
                        }
                    }
                }

                Spacer()
            }

            if !isLast {
                Divider()
            }
        }
    }
}

// MARK: - Preview

struct RouteDetailView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            RouteDetailView(result: RouteOptimizationResult(
                orderedPeaks: [],
                totalDistance: 100.5,
                totalElevationGain: 15000,
                routeSegments: [],
                algorithm: "Nearest Neighbor + 2-Opt",
                computationTime: 0.123
            ))
        }
    }
}
