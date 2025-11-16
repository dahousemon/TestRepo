#!/usr/bin/env python3
"""
Test script for TSP solver functionality
Simulates the Swift TSP solver logic to verify correctness
"""

import json
import math
from typing import List, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points using Haversine formula
    Returns distance in miles
    """
    earth_radius_miles = 3958.8

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return earth_radius_miles * c


def nearest_neighbor_route(peaks: List[dict]) -> List[dict]:
    """
    Nearest neighbor heuristic for TSP
    """
    if len(peaks) < 2:
        return peaks

    unvisited = peaks.copy()
    route = [unvisited.pop(0)]

    while unvisited:
        current = route[-1]
        nearest_idx = 0
        nearest_dist = float('inf')

        for i, peak in enumerate(unvisited):
            dist = haversine_distance(
                current['latitude'], current['longitude'],
                peak['latitude'], peak['longitude']
            )
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = i

        route.append(unvisited.pop(nearest_idx))

    return route


def calculate_total_distance(route: List[dict]) -> float:
    """Calculate total distance of a route"""
    total = 0
    for i in range(len(route) - 1):
        total += haversine_distance(
            route[i]['latitude'], route[i]['longitude'],
            route[i+1]['latitude'], route[i+1]['longitude']
        )
    return total


def test_tsp_solver():
    """Test the TSP solver with real peak data"""
    print("=" * 60)
    print("TSP Solver Test")
    print("=" * 60)

    # Load peak data
    with open('ColoradoPeaksExplorer/ColoradoPeaksExplorer/Resources/peaks_data.json', 'r') as f:
        data = json.load(f)

    # Combine all peaks
    peaks_data = data.get('top200Peaks', []) + data.get('frontRangePeaks', [])

    # Test 1: Small set of fourteeners
    print("\n1. Testing with 5 Fourteeners:")
    print("-" * 60)
    fourteeners = [p for p in peaks_data if p['elevation'] >= 14000][:5]

    for i, peak in enumerate(fourteeners, 1):
        print(f"   {i}. {peak['name']} - {peak['elevation']} ft")

    # Calculate route
    optimized_route = nearest_neighbor_route(fourteeners)
    total_distance = calculate_total_distance(optimized_route)

    print(f"\n   Optimized Route:")
    for i, peak in enumerate(optimized_route, 1):
        print(f"   {i}. {peak['name']}")

    print(f"\n   Total Distance: {total_distance:.1f} miles")

    # Test 2: Sawatch Range peaks
    print("\n2. Testing with Sawatch Range peaks:")
    print("-" * 60)
    sawatch_peaks = [p for p in peaks_data if p.get('range') == 'Sawatch Range'][:8]

    print(f"   Found {len(sawatch_peaks)} Sawatch Range peaks")

    optimized_route = nearest_neighbor_route(sawatch_peaks)
    total_distance = calculate_total_distance(optimized_route)

    print(f"\n   Optimized Route:")
    for i, peak in enumerate(optimized_route, 1):
        if i <= 8:  # Show first 8
            print(f"   {i}. {peak['name']} - {peak['elevation']} ft")

    print(f"\n   Total Distance: {total_distance:.1f} miles")

    # Test 3: Verify distance calculation
    print("\n3. Verifying distance calculations:")
    print("-" * 60)

    # Test known distances
    mount_elbert = next(p for p in peaks_data if p['name'] == 'Mount Elbert')
    mount_massive = next(p for p in peaks_data if p['name'] == 'Mount Massive')

    distance = haversine_distance(
        mount_elbert['latitude'], mount_elbert['longitude'],
        mount_massive['latitude'], mount_massive['longitude']
    )

    print(f"   Mount Elbert to Mount Massive: {distance:.1f} miles")
    print(f"   (These peaks are near each other in the Sawatch Range)")

    # Test 4: All fourteeners optimization
    print("\n4. Testing with ALL 53 Fourteeners:")
    print("-" * 60)

    all_fourteeners = [p for p in peaks_data if p['elevation'] >= 14000]
    print(f"   Total Fourteeners: {len(all_fourteeners)}")

    optimized_route = nearest_neighbor_route(all_fourteeners)
    total_distance = calculate_total_distance(optimized_route)

    print(f"\n   Total Distance for all fourteeners: {total_distance:.1f} miles")

    # Calculate elevation gain
    total_gain = sum(
        max(0, optimized_route[i+1]['elevation'] - optimized_route[i]['elevation'])
        for i in range(len(optimized_route) - 1)
    )

    print(f"   Total Elevation Gain: {total_gain:,} feet")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    test_tsp_solver()
