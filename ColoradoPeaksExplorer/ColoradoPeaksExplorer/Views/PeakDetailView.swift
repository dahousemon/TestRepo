//
//  PeakDetailView.swift
//  Colorado Peaks Explorer
//
//  Detailed view for a single peak
//

import SwiftUI

struct PeakDetailView: View {
    let peak: Peak
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Header image
                headerImageView

                // Peak information
                VStack(spacing: 20) {
                    // Title section
                    titleSection

                    // Basic info cards
                    basicInfoSection

                    // Fun fact section
                    funFactSection

                    // Front Range specific info
                    if peak.category == .frontRange, let visibleFromDenver = peak.visibleFromDenver, visibleFromDenver {
                        frontRangeInfoSection
                    }

                    // Google Maps button
                    mapsButton

                    Spacer(minLength: 20)
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button(action: {
                    presentationMode.wrappedValue.dismiss()
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("Back")
                    }
                    .foregroundColor(ColorTheme.primary)
                }
            }
        }
    }

    // MARK: - Subviews

    private var headerImageView: some View {
        ZStack(alignment: .bottomLeading) {
            if let imageUrl = URL(string: peak.imageUrl) {
                CachedAsyncImage(url: imageUrl)
                    .aspectRatio(contentMode: .fill)
                    .frame(height: 300)
                    .clipped()
            } else {
                ColorTheme.rockGray.opacity(0.3)
                    .frame(height: 300)
                    .overlay(
                        Image(systemName: "mountain.2.fill")
                            .font(.system(size: 80))
                            .foregroundColor(.white.opacity(0.5))
                    )
            }

            // Gradient overlay
            LinearGradient(
                colors: [Color.clear, Color.black.opacity(0.6)],
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(height: 300)

            // Peak rank badge
            if peak.isFourteener {
                Text("14er")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(ColorTheme.sunsetOrange)
                    .cornerRadius(8)
                    .padding()
            }
        }
        .accessibilityLabel("Peak image")
    }

    private var titleSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(peak.name)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(ColorTheme.textPrimary)
                .accessibilityAddTraits(.isHeader)

            HStack {
                Image(systemName: "location.fill")
                    .foregroundColor(ColorTheme.secondary)
                Text(peak.range)
                    .font(.headline)
                    .foregroundColor(ColorTheme.textSecondary)
            }

            HStack(spacing: 4) {
                Text(peak.rankDescription)
                    .font(.subheadline)
                    .foregroundColor(ColorTheme.primary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(ColorTheme.primary.opacity(0.1))
                    .cornerRadius(6)

                Text(peak.difficulty)
                    .font(.subheadline)
                    .foregroundColor(ColorTheme.forestGreen)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(ColorTheme.forestGreen.opacity(0.1))
                    .cornerRadius(6)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var basicInfoSection: some View {
        VStack(spacing: 12) {
            InfoCard(
                icon: "arrow.up",
                title: "Elevation",
                value: peak.elevationString,
                color: ColorTheme.primary
            )

            InfoCard(
                icon: "chart.bar.fill",
                title: "Prominence",
                value: peak.prominenceString,
                color: ColorTheme.forestGreen
            )

            InfoCard(
                icon: "location.circle.fill",
                title: "Coordinates",
                value: peak.coordinatesString,
                color: ColorTheme.sunsetOrange
            )
        }
    }

    private var funFactSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "lightbulb.fill")
                    .foregroundColor(ColorTheme.aspenGold)
                Text("Fun Fact")
                    .font(.headline)
                    .foregroundColor(ColorTheme.textPrimary)
            }

            Text(peak.funFact)
                .font(.body)
                .foregroundColor(ColorTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(ColorTheme.aspenGold.opacity(0.1))
        .cornerRadius(12)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Fun fact: \(peak.funFact)")
    }

    private var frontRangeInfoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "eye.fill")
                    .foregroundColor(ColorTheme.skyBlue)
                Text("Visible from Denver")
                    .font(.headline)
                    .foregroundColor(ColorTheme.textPrimary)
            }

            if let direction = peak.direction {
                HStack {
                    Image(systemName: "compass.fill")
                        .foregroundColor(ColorTheme.primary)
                    Text("Direction: \(direction)")
                        .font(.body)
                        .foregroundColor(ColorTheme.textSecondary)
                }
            }

            if let distance = peak.distanceFromDenver {
                HStack {
                    Image(systemName: "ruler.fill")
                        .foregroundColor(ColorTheme.primary)
                    Text("Distance: \(distance)")
                        .font(.body)
                        .foregroundColor(ColorTheme.textSecondary)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(ColorTheme.skyBlue.opacity(0.1))
        .cornerRadius(12)
    }

    private var mapsButton: some View {
        Button(action: {
            if let url = peak.googleMapsUrl {
                UIApplication.shared.open(url)
            }
        }) {
            HStack {
                Image(systemName: "map.fill")
                    .font(.headline)
                Text("Open in Google Maps")
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(ColorTheme.primary)
            .cornerRadius(12)
        }
        .accessibilityLabel("Open peak location in Google Maps")
        .accessibilityHint("Opens Google Maps with this peak's coordinates")
    }
}

// MARK: - Supporting Views

struct InfoCard: View {
    let icon: String
    let title: String
    let value: String
    let color: Color

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .foregroundColor(ColorTheme.textSecondary)
                Text(value)
                    .font(.headline)
                    .foregroundColor(ColorTheme.textPrimary)
            }

            Spacer()
        }
        .padding()
        .coloradoCardStyle()
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title): \(value)")
    }
}

struct PeakDetailView_Previews: PreviewProvider {
    static var samplePeak = Peak(
        id: "1",
        name: "Mount Elbert",
        elevation: 14433,
        range: "Sawatch Range",
        latitude: 39.1178,
        longitude: -106.4454,
        prominence: 9093,
        difficulty: "Class 1",
        funFact: "Mount Elbert is the highest peak in Colorado and the entire Rocky Mountains.",
        imageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Mount_Elbert.jpg/800px-Mount_Elbert.jpg",
        category: .top200,
        visibleFromDenver: nil,
        direction: nil,
        distanceFromDenver: nil
    )

    static var previews: some View {
        NavigationView {
            PeakDetailView(peak: samplePeak)
        }
    }
}
