//
//  HomeView.swift
//  Colorado Peaks Explorer
//
//  Main home screen with peak list and search
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var peakDataService: PeakDataService
    @State private var searchText = ""
    @State private var selectedCategory: PeakCategory? = nil
    @State private var sortOption: SortOption = .elevation

    enum SortOption: String, CaseIterable {
        case elevation = "Elevation"
        case alphabetical = "Name"
        case prominence = "Prominence"
    }

    var filteredAndSortedPeaks: [Peak] {
        var peaks = peakDataService.peaks

        // Filter by search text
        if !searchText.isEmpty {
            peaks = peaks.filter { peak in
                peak.name.localizedCaseInsensitiveContains(searchText) ||
                peak.range.localizedCaseInsensitiveContains(searchText) ||
                "\(peak.elevation)".contains(searchText)
            }
        }

        // Filter by category
        if let category = selectedCategory {
            peaks = peaks.filter { $0.category == category }
        }

        // Sort
        switch sortOption {
        case .elevation:
            peaks.sort { $0.elevation > $1.elevation }
        case .alphabetical:
            peaks.sort { $0.name < $1.name }
        case .prominence:
            peaks.sort { $0.prominence > $1.prominence }
        }

        return peaks
    }

    var body: some View {
        NavigationView {
            ZStack {
                ColorTheme.background.ignoresSafeArea()

                VStack(spacing: 0) {
                    // Header with gradient
                    headerView

                    // Category filter pills
                    categoryFilterView

                    // Sort options
                    sortOptionsView

                    // Peak list
                    if peakDataService.isLoading {
                        loadingView
                    } else if let errorMessage = peakDataService.errorMessage {
                        errorView(message: errorMessage)
                    } else {
                        peakListView
                    }
                }
            }
            .navigationBarHidden(true)
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    // MARK: - Subviews

    private var headerView: some View {
        VStack(spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Colorado Peaks")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.white)

                    Text("\(filteredAndSortedPeaks.count) Peaks")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.9))
                }

                Spacer()

                Button(action: {
                    peakDataService.refreshData()
                }) {
                    Image(systemName: "arrow.clockwise")
                        .font(.title2)
                        .foregroundColor(.white)
                        .padding(8)
                }
            }
            .padding(.horizontal)
            .padding(.top, 50)

            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.white.opacity(0.7))

                TextField("Search peaks or ranges...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .foregroundColor(.white)
                    .accessibilityLabel("Search peaks by name, range, or elevation")

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.white.opacity(0.7))
                    }
                }
            }
            .padding(12)
            .background(Color.white.opacity(0.2))
            .cornerRadius(10)
            .padding(.horizontal)
            .padding(.bottom, 16)
        }
        .background(ColorTheme.headerGradient)
    }

    private var categoryFilterView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                CategoryPill(
                    title: "All Peaks",
                    isSelected: selectedCategory == nil,
                    action: { selectedCategory = nil }
                )

                ForEach(PeakCategory.allCases, id: \.self) { category in
                    CategoryPill(
                        title: category == .top200 ? "Top 200" : "Front Range",
                        isSelected: selectedCategory == category,
                        action: { selectedCategory = category }
                    )
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 12)
        }
        .background(Color.white)
    }

    private var sortOptionsView: some View {
        HStack {
            Text("Sort by:")
                .font(.subheadline)
                .foregroundColor(ColorTheme.textSecondary)

            Picker("Sort", selection: $sortOption) {
                ForEach(SortOption.allCases, id: \.self) { option in
                    Text(option.rawValue).tag(option)
                }
            }
            .pickerStyle(SegmentedPickerStyle())
            .accessibilityLabel("Sort peaks by")

            Spacer()
        }
        .padding()
        .background(Color.white)
    }

    private var peakListView: some View {
        List {
            ForEach(filteredAndSortedPeaks) { peak in
                NavigationLink(destination: PeakDetailView(peak: peak)) {
                    PeakRowView(peak: peak)
                }
                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                .listRowSeparator(.hidden)
                .accessibilityElement(children: .combine)
                .accessibilityLabel("\(peak.name), elevation \(peak.elevationString)")
            }
        }
        .listStyle(PlainListStyle())
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading peaks...")
                .foregroundColor(ColorTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func errorView(message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(ColorTheme.sunsetOrange)

            Text(message)
                .foregroundColor(ColorTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding()

            Button(action: {
                peakDataService.refreshData()
            }) {
                Text("Retry")
                    .coloradoButtonStyle()
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

// MARK: - Supporting Views

struct CategoryPill: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .white : ColorTheme.primary)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? ColorTheme.primary : Color.clear)
                .cornerRadius(20)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(ColorTheme.primary, lineWidth: 1.5)
                )
        }
        .accessibilityLabel(title)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

struct PeakRowView: View {
    let peak: Peak

    var body: some View {
        HStack(spacing: 12) {
            // Peak image thumbnail
            if let imageUrl = URL(string: peak.imageUrl) {
                CachedAsyncImage(url: imageUrl)
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 80, height: 80)
                    .cornerRadius(8)
                    .clipped()
            } else {
                Image(systemName: "mountain.2.fill")
                    .font(.largeTitle)
                    .foregroundColor(ColorTheme.rockGray)
                    .frame(width: 80, height: 80)
                    .background(ColorTheme.rockGray.opacity(0.1))
                    .cornerRadius(8)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(peak.name)
                    .font(.headline)
                    .foregroundColor(ColorTheme.textPrimary)

                Text(peak.range)
                    .font(.subheadline)
                    .foregroundColor(ColorTheme.textSecondary)

                HStack(spacing: 8) {
                    Label(peak.elevationString, systemImage: "arrow.up")
                        .font(.caption)
                        .foregroundColor(ColorTheme.primary)

                    Text("•")
                        .foregroundColor(ColorTheme.rockGray)

                    Text(peak.difficulty)
                        .font(.caption)
                        .foregroundColor(ColorTheme.forestGreen)
                }

                if peak.isFourteener {
                    Text("14er")
                        .font(.caption2)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(ColorTheme.sunsetOrange)
                        .cornerRadius(4)
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(ColorTheme.rockGray.opacity(0.5))
        }
        .padding()
        .coloradoCardStyle()
    }
}

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        HomeView()
            .environmentObject(PeakDataService())
    }
}
