//
//  ColorTheme.swift
//  Colorado Peaks Explorer
//
//  Colorado-inspired color theme for the app
//

import SwiftUI

struct ColorTheme {
    // Primary colors inspired by Colorado landscapes
    static let skyBlue = Color(red: 0.53, green: 0.81, blue: 0.92)           // Light sky blue
    static let mountainBlue = Color(red: 0.25, green: 0.41, blue: 0.88)     // Deep mountain blue
    static let forestGreen = Color(red: 0.13, green: 0.55, blue: 0.13)      // Forest green
    static let rockGray = Color(red: 0.50, green: 0.50, blue: 0.50)         // Mountain rock gray
    static let snowWhite = Color(red: 0.96, green: 0.96, blue: 0.96)        // Snow white
    static let sunsetOrange = Color(red: 1.0, green: 0.55, blue: 0.0)       // Colorado sunset
    static let aspenGold = Color(red: 0.85, green: 0.65, blue: 0.13)        // Aspen gold

    // Semantic colors
    static let primary = mountainBlue
    static let secondary = forestGreen
    static let accent = sunsetOrange
    static let background = snowWhite
    static let cardBackground = Color.white

    // Text colors
    static let textPrimary = Color.primary
    static let textSecondary = Color.secondary

    // Gradient backgrounds
    static let headerGradient = LinearGradient(
        colors: [skyBlue, mountainBlue],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardGradient = LinearGradient(
        colors: [Color.white, snowWhite],
        startPoint: .top,
        endPoint: .bottom
    )
}

// Extension for custom styling
extension View {
    func coloradoCardStyle() -> some View {
        self
            .background(ColorTheme.cardBackground)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
    }

    func coloradoButtonStyle() -> some View {
        self
            .padding()
            .background(ColorTheme.primary)
            .foregroundColor(.white)
            .cornerRadius(10)
    }
}
