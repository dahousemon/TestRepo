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
            HomeView()
                .environmentObject(peakDataService)
        }
    }
}
