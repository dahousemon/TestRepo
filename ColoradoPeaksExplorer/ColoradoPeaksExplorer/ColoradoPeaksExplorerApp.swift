//
//  ColoradoPeaksExplorerApp.swift
//  Colorado Peaks Explorer
//
//  Main app entry point
//

import SwiftUI

@main
struct ColoradoPeaksExplorerApp: App {
    @StateObject private var peakDataService = PeakDataService()

    var body: some Scene {
        WindowGroup {
            TabView {
                HomeView()
                    .environmentObject(peakDataService)
                    .tabItem {
                        Label("Peaks", systemImage: "mountain.2.fill")
                    }

                RouteOptimizerView()
                    .environmentObject(peakDataService)
                    .tabItem {
                        Label("Route Optimizer", systemImage: "map.fill")
                    }
            }
        }
    }
}
