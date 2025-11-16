//
//  TravelingSalesmanSolver.swift
//  ColoradoPeaksExplorer
//
//  Created by Claude Code
//  Implements traveling salesman problem solver for optimizing peak routes
//

import Foundation

/// Result of a TSP optimization
struct RouteOptimizationResult {
    let orderedPeaks: [Peak]
    let totalDistance: Double // in miles
    let totalElevationGain: Int // in feet
    let routeSegments: [RouteSegment]
    let algorithm: String
    let computationTime: TimeInterval
}

/// Represents a segment between two peaks
struct RouteSegment {
    let from: Peak
    let to: Peak
    let distance: Double // in miles
    let elevationChange: Int // in feet (can be negative)
}

/// Service for solving the traveling salesman problem for peak routes
class TravelingSalesmanSolver {

    // MARK: - Distance Calculation

    /// Calculate the great circle distance between two coordinates using the Haversine formula
    /// - Parameters:
    ///   - lat1: Latitude of first point in degrees
    ///   - lon1: Longitude of first point in degrees
    ///   - lat2: Latitude of second point in degrees
    ///   - lon2: Longitude of second point in degrees
    /// - Returns: Distance in miles
    static func haversineDistance(lat1: Double, lon1: Double, lat2: Double, lon2: Double) -> Double {
        let earthRadiusMiles = 3958.8 // Earth's radius in miles

        // Convert degrees to radians
        let lat1Rad = lat1 * .pi / 180
        let lon1Rad = lon1 * .pi / 180
        let lat2Rad = lat2 * .pi / 180
        let lon2Rad = lon2 * .pi / 180

        // Haversine formula
        let dLat = lat2Rad - lat1Rad
        let dLon = lon2Rad - lon1Rad

        let a = sin(dLat / 2) * sin(dLat / 2) +
                cos(lat1Rad) * cos(lat2Rad) *
                sin(dLon / 2) * sin(dLon / 2)

        let c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earthRadiusMiles * c
    }

    /// Calculate distance between two peaks
    static func distance(from peak1: Peak, to peak2: Peak) -> Double {
        return haversineDistance(
            lat1: peak1.latitude,
            lon1: peak1.longitude,
            lat2: peak2.latitude,
            lon2: peak2.longitude
        )
    }

    /// Build a distance matrix for a set of peaks
    private static func buildDistanceMatrix(peaks: [Peak]) -> [[Double]] {
        let n = peaks.count
        var matrix = Array(repeating: Array(repeating: 0.0, count: n), count: n)

        for i in 0..<n {
            for j in 0..<n where i != j {
                matrix[i][j] = distance(from: peaks[i], to: peaks[j])
            }
        }

        return matrix
    }

    // MARK: - TSP Algorithms

    /// Solve TSP using nearest neighbor heuristic followed by 2-opt optimization
    /// - Parameters:
    ///   - peaks: Array of peaks to visit
    ///   - startPeak: Optional starting peak (if nil, uses first peak)
    ///   - returnToStart: Whether the route should return to the starting peak
    /// - Returns: Optimized route result
    static func optimizeRoute(
        peaks: [Peak],
        startPeak: Peak? = nil,
        returnToStart: Bool = false
    ) -> RouteOptimizationResult {
        let startTime = Date()

        guard peaks.count >= 2 else {
            // Handle edge case: less than 2 peaks
            return RouteOptimizationResult(
                orderedPeaks: peaks,
                totalDistance: 0,
                totalElevationGain: 0,
                routeSegments: [],
                algorithm: "No optimization needed",
                computationTime: 0
            )
        }

        // Step 1: Get initial route using nearest neighbor
        var route = nearestNeighborRoute(peaks: peaks, startPeak: startPeak)

        // Step 2: Optimize using 2-opt
        route = twoOptOptimization(route: route)

        // Step 3: Add return to start if requested
        if returnToStart && route.count > 1 {
            route.append(route[0])
        }

        // Step 4: Calculate route statistics
        let segments = calculateRouteSegments(route: route)
        let totalDistance = segments.reduce(0) { $0 + $1.distance }
        let totalElevationGain = calculateTotalElevationGain(segments: segments)

        let computationTime = Date().timeIntervalSince(startTime)

        return RouteOptimizationResult(
            orderedPeaks: route,
            totalDistance: totalDistance,
            totalElevationGain: totalElevationGain,
            routeSegments: segments,
            algorithm: "Nearest Neighbor + 2-Opt",
            computationTime: computationTime
        )
    }

    /// Nearest neighbor heuristic: Start at a peak and always go to the nearest unvisited peak
    private static func nearestNeighborRoute(peaks: [Peak], startPeak: Peak?) -> [Peak] {
        var unvisited = peaks
        var route: [Peak] = []

        // Determine starting peak
        let start = startPeak ?? peaks[0]
        guard let startIndex = unvisited.firstIndex(where: { $0.id == start.id }) else {
            return peaks
        }

        route.append(unvisited.remove(at: startIndex))

        // Build route by always selecting nearest unvisited peak
        while !unvisited.isEmpty {
            let current = route.last!
            var nearestIndex = 0
            var nearestDistance = Double.infinity

            for (index, peak) in unvisited.enumerated() {
                let dist = distance(from: current, to: peak)
                if dist < nearestDistance {
                    nearestDistance = dist
                    nearestIndex = index
                }
            }

            route.append(unvisited.remove(at: nearestIndex))
        }

        return route
    }

    /// 2-opt optimization: Iteratively improve the route by reversing segments
    private static func twoOptOptimization(route: [Peak]) -> [Peak] {
        guard route.count >= 4 else { return route }

        var optimizedRoute = route
        var improved = true
        var iterations = 0
        let maxIterations = 1000 // Prevent infinite loops

        while improved && iterations < maxIterations {
            improved = false
            iterations += 1

            for i in 0..<(optimizedRoute.count - 1) {
                for j in (i + 2)..<optimizedRoute.count {
                    // Skip if j is the last index and i is 0 (for non-circular routes)
                    if i == 0 && j == optimizedRoute.count - 1 {
                        continue
                    }

                    let delta = twoOptDelta(route: optimizedRoute, i: i, j: j)

                    if delta < -0.001 { // Improvement found (with small epsilon for floating point)
                        optimizedRoute = twoOptReverse(route: optimizedRoute, i: i, j: j)
                        improved = true
                    }
                }
            }
        }

        return optimizedRoute
    }

    /// Calculate the change in total distance if we reverse the segment between i and j
    private static func twoOptDelta(route: [Peak], i: Int, j: Int) -> Double {
        let a = route[i]
        let b = route[i + 1]
        let c = route[j]
        let d = j + 1 < route.count ? route[j + 1] : route[0]

        let currentDistance = distance(from: a, to: b) + distance(from: c, to: d)
        let newDistance = distance(from: a, to: c) + distance(from: b, to: d)

        return newDistance - currentDistance
    }

    /// Reverse the segment of the route between i+1 and j
    private static func twoOptReverse(route: [Peak], i: Int, j: Int) -> [Peak] {
        var newRoute = route
        var left = i + 1
        var right = j

        while left < right {
            newRoute.swapAt(left, right)
            left += 1
            right -= 1
        }

        return newRoute
    }

    // MARK: - Route Analysis

    /// Calculate route segments with distances and elevation changes
    private static func calculateRouteSegments(route: [Peak]) -> [RouteSegment] {
        guard route.count >= 2 else { return [] }

        var segments: [RouteSegment] = []

        for i in 0..<(route.count - 1) {
            let from = route[i]
            let to = route[i + 1]
            let dist = distance(from: from, to: to)
            let elevChange = to.elevation - from.elevation

            segments.append(RouteSegment(
                from: from,
                to: to,
                distance: dist,
                elevationChange: elevChange
            ))
        }

        return segments
    }

    /// Calculate total elevation gain (only counting uphill segments)
    private static func calculateTotalElevationGain(segments: [RouteSegment]) -> Int {
        return segments.reduce(0) { total, segment in
            total + max(0, segment.elevationChange)
        }
    }

    // MARK: - Convenience Methods

    /// Find the optimal route for a specific mountain range
    static func optimizeRouteForRange(
        range: String,
        allPeaks: [Peak],
        returnToStart: Bool = false
    ) -> RouteOptimizationResult {
        let peaksInRange = allPeaks.filter { $0.range == range }
        return optimizeRoute(peaks: peaksInRange, returnToStart: returnToStart)
    }

    /// Find optimal route for all fourteeners
    static func optimizeFourteenersRoute(
        allPeaks: [Peak],
        returnToStart: Bool = false
    ) -> RouteOptimizationResult {
        let fourteeners = allPeaks.filter { $0.elevation >= 14000 }
        return optimizeRoute(peaks: fourteeners, returnToStart: returnToStart)
    }
}
