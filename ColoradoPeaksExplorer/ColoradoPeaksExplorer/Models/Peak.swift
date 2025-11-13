//
//  Peak.swift
//  Colorado Peaks Explorer
//
//  Data model representing a Colorado mountain peak
//

import Foundation

struct Peak: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let elevation: Int
    let range: String
    let latitude: Double
    let longitude: Double
    let prominence: Int
    let difficulty: String
    let funFact: String
    let imageUrl: String
    let category: PeakCategory

    // Front Range specific properties (optional)
    let visibleFromDenver: Bool?
    let direction: String?
    let distanceFromDenver: String?

    enum CodingKeys: String, CodingKey {
        case id, name, elevation, range, latitude, longitude
        case prominence, difficulty, funFact, imageUrl, category
        case visibleFromDenver, direction, distanceFromDenver
    }

    /// Google Maps URL for this peak
    var googleMapsUrl: URL? {
        let urlString = "https://www.google.com/maps/search/?api=1&query=\(latitude),\(longitude)"
        return URL(string: urlString)
    }

    /// Formatted elevation string
    var elevationString: String {
        return "\(elevation.formatted()) ft"
    }

    /// Formatted prominence string
    var prominenceString: String {
        return "\(prominence.formatted()) ft"
    }

    /// Formatted coordinates string
    var coordinatesString: String {
        return String(format: "%.4f°, %.4f°", latitude, longitude)
    }

    /// Returns if this is a fourteener
    var isFourteener: Bool {
        return elevation >= 14000
    }

    /// Returns if this is a thirteener
    var isThirteener: Bool {
        return elevation >= 13000 && elevation < 14000
    }

    /// Peak rank description
    var rankDescription: String {
        if isFourteener {
            return "Fourteener"
        } else if isThirteener {
            return "Thirteener"
        } else {
            return "Peak"
        }
    }
}

enum PeakCategory: String, Codable, CaseIterable {
    case top200 = "top200"
    case frontRange = "frontRange"

    var displayName: String {
        switch self {
        case .top200:
            return "Top 200 Highest Peaks"
        case .frontRange:
            return "Front Range Peaks Visible from Denver"
        }
    }
}

/// Response structure for JSON data
struct PeaksData: Codable {
    let top200Peaks: [Peak]
    let frontRangePeaks: [Peak]

    /// All peaks combined
    var allPeaks: [Peak] {
        return top200Peaks + frontRangePeaks
    }
}
