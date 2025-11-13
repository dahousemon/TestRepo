# Colorado Peaks Explorer

A native iOS app built with Swift and SwiftUI that provides comprehensive information on 200 of Colorado's highest mountain peaks (all 53 fourteeners + 147 thirteeners), plus 14 curated Front Range peaks visible from Denver.

![iOS](https://img.shields.io/badge/iOS-15.0%2B-blue)
![Swift](https://img.shields.io/badge/Swift-5.5%2B-orange)
![SwiftUI](https://img.shields.io/badge/SwiftUI-3.0%2B-green)

## Features

### Core Features
- **Comprehensive Peak Database**: Information on 200 of Colorado's highest peaks (all 53 fourteeners + 147 thirteeners)
- **Front Range Peaks**: 14 curated peaks visible from Denver with viewing information
- **Offline Access**: Full functionality after initial data load with local caching
- **Peak Details**:
  - Elevation, prominence, and coordinates
  - Mountain range and location
  - Hiking difficulty (Class ratings)
  - Fun facts and trivia
  - High-quality peak images
- **Google Maps Integration**: Direct links to peak locations in Google Maps
- **Advanced Search**: Filter peaks by name, range, or elevation
- **Multiple Sort Options**: Sort by elevation, alphabetical, or prominence
- **Category Filtering**: Filter by Top 200 or Front Range peaks
- **Colorado-Inspired UI**: Beautiful design with colors inspired by Colorado's landscapes
- **Accessibility**: Full VoiceOver support and dynamic text sizing

### Technical Features
- Native iOS app (iOS 15+)
- Built with Swift and SwiftUI
- Efficient image caching for fast loading
- Data persistence with UserDefaults
- 30-day cache refresh mechanism
- Smooth performance with 200+ entries
- Error handling with fallback to cached data

## Screenshots

*Home Screen with Peak List*
- Searchable list of all peaks
- Category filters (All, Top 200, Front Range)
- Sort options (Elevation, Name, Prominence)
- Beautiful peak thumbnails

*Peak Detail Screen*
- Large peak image
- Comprehensive peak information
- Fun facts and trivia
- Google Maps integration
- Front Range viewing information (if applicable)

## Installation & Setup

### Requirements
- macOS 12.0+ with Xcode 13.0+
- iOS 15.0+ (for running the app)
- iPhone or iPad device/simulator

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/colorado-peaks-explorer.git
   cd colorado-peaks-explorer
   ```

2. **Open in Xcode**
   ```bash
   open ColoradoPeaksExplorer/ColoradoPeaksExplorer.xcodeproj
   ```

   If you don't have an Xcode project file yet, create one:
   - Open Xcode
   - Select "Create a new Xcode project"
   - Choose "iOS" → "App"
   - Product Name: `ColoradoPeaksExplorer`
   - Interface: SwiftUI
   - Language: Swift
   - Organization Identifier: `com.yourname`
   - Click "Next" and select the `ColoradoPeaksExplorer` folder

3. **Add Files to Project**

   Drag and drop the following folders into your Xcode project:
   - `Models/` (Peak.swift, ColorTheme.swift)
   - `Views/` (HomeView.swift, PeakDetailView.swift)
   - `Services/` (PeakDataService.swift, ImageCache.swift)
   - `Resources/` (peaks_data.json)
   - `SupportingFiles/` (Info.plist)
   - `ColoradoPeaksExplorerApp.swift` (main app file)

   **Important**: When adding `peaks_data.json`, make sure "Copy items if needed" and "Add to targets: ColoradoPeaksExplorer" are both checked.

4. **Configure the Project**

   In Xcode:
   - Select the project in the navigator
   - Select the "ColoradoPeaksExplorer" target
   - Go to "Signing & Capabilities"
   - Select your Team
   - Xcode will automatically manage signing

5. **Configure Info.plist**

   The Info.plist is already configured, but ensure it's set as the project's Info.plist:
   - Select the project → target → "Build Settings"
   - Search for "Info.plist File"
   - Set to: `ColoradoPeaksExplorer/SupportingFiles/Info.plist`

6. **Build and Run**
   - Select a simulator or connected device
   - Press `Cmd + R` or click the "Run" button
   - The app will build and launch

### Project Structure

```
ColoradoPeaksExplorer/
├── ColoradoPeaksExplorer/
│   ├── ColoradoPeaksExplorerApp.swift    # Main app entry point
│   ├── Models/
│   │   ├── Peak.swift                     # Peak data model
│   │   └── ColorTheme.swift               # UI color theme
│   ├── Views/
│   │   ├── HomeView.swift                 # Home screen
│   │   └── PeakDetailView.swift           # Detail screen
│   ├── Services/
│   │   ├── PeakDataService.swift          # Data fetching & caching
│   │   └── ImageCache.swift               # Image loading & caching
│   ├── Resources/
│   │   └── peaks_data.json                # Peak database
│   └── SupportingFiles/
│       └── Info.plist                     # App configuration
└── README.md                               # This file
```

## Usage Guide

### Home Screen

**Search Peaks**
- Tap the search bar at the top
- Type peak name, range, or elevation
- Results filter in real-time

**Filter by Category**
- Tap "All Peaks" to see everything
- Tap "Top 200" to see Colorado's highest peaks
- Tap "Front Range" to see peaks visible from Denver

**Sort Peaks**
- Use the segmented control to sort by:
  - **Elevation**: Highest to lowest (default)
  - **Name**: Alphabetical A-Z
  - **Prominence**: Most prominent first

**View Peak Details**
- Tap any peak row to see full details

**Refresh Data**
- Tap the refresh button (↻) in the top-right corner
- Data automatically refreshes every 30 days

### Peak Detail Screen

**View Information**
- Scroll to see all peak details
- Elevation, prominence, and coordinates
- Hiking difficulty rating
- Fun facts and trivia
- Peak image

**Open in Maps**
- Tap "Open in Google Maps" button
- Opens Google Maps (or Maps app) with peak coordinates
- View terrain, satellite imagery, and directions

**Front Range Peaks**
- Additional information for Denver-visible peaks
- Direction from Denver (e.g., Northwest)
- Distance from Denver (in miles)

### Accessibility

**VoiceOver Support**
- All UI elements are properly labeled
- Navigate using VoiceOver gestures
- Peak information is read clearly

**Dynamic Text**
- Supports system text size settings
- Go to Settings → Accessibility → Display & Text Size
- Adjust text size as needed

**High Contrast**
- App uses accessible color contrasts
- Colorado-inspired colors meet WCAG standards

## Data Sources

### Peak Data Sources
The peak information was compiled from reliable sources including:

- **Top 200 Peaks**:
  - climb13ers.com/colorado-13ers/top-200
  - Wikipedia's list of Colorado mountain peaks
  - Peakbagger.com

- **Front Range Peaks**:
  - FOX31 Denver article on peaks visible from Denver
  - PeakVisor Front Range information
  - Reddit discussions and local sources

- **Peak Details**:
  - 14ers.com for difficulty ratings and routes
  - SummitPost.org for peak information
  - AllTrails.com for hiking details
  - Colorado.com for fun facts
  - USGS for coordinates and elevation data

- **Images**:
  - Wikimedia Commons (public domain)
  - USGS imagery
  - Public domain sources

### Data Accuracy
All elevation and coordinate data has been cross-referenced with USGS sources. Fun facts have been verified from multiple reliable sources. If you notice any inaccuracies, please open an issue.

## Peak Categories

### Top 200 Highest Peaks
Contains exactly 200 of Colorado's highest peaks: all 53 fourteeners (peaks over 14,000 ft) plus 147 of the highest thirteeners, ranked by elevation from Mount Elbert (14,433 ft) down to Vermillion Peak (13,504 ft).

**Notable Peaks**:
- Mount Elbert (14,433 ft) - Highest in Colorado
- Mount Massive (14,421 ft) - Second highest
- All 53 Colorado fourteeners
- Highest thirteeners

### Front Range Peaks Visible from Denver
Contains exactly 14 curated peaks that are visible from Denver on clear days, based on verified sources including FOX31 Denver and PeakVisor.

**Notable Peaks**:
- Longs Peak (14,259 ft) - Northwest view
- Mount Blue Sky (14,264 ft) - Most prominent
- Pikes Peak (14,115 ft) - South view
- Grays & Torreys Peaks - I-70 corridor
- Indian Peaks (Arapaho, Apache, Navajo)

## Technical Details

### Data Management
- **Initial Load**: Fetches from bundled JSON on first launch
- **Caching**: Stores data locally using UserDefaults
- **Refresh**: Automatically refreshes every 30 days if online
- **Offline Mode**: Full functionality without internet after first load
- **Image Caching**: NSCache with 50MB limit, 100 image capacity

### Performance
- Efficient list rendering for 200+ peaks
- Lazy image loading with caching
- Optimized search and filter algorithms
- Smooth scrolling and transitions

### Error Handling
- Graceful fallback to cached data on errors
- User-friendly error messages
- Retry functionality
- Validates JSON structure on load

## Assumptions & Limitations

### Assumptions
1. **Peak Selection**: The "200 highest" includes all 53 fourteeners plus thirteeners. The exact 200th peak is approximately 13,500-13,600 ft.

2. **Denver Visibility**: Front Range peaks marked as "visible from Denver" are based on reliable sources but visibility depends on weather, air quality, and viewing location.

3. **Difficulty Ratings**: Class ratings are general guidelines. Conditions vary by season, weather, and route.

4. **Image URLs**: Images are from public sources. Some URLs may change over time. The app includes fallback placeholder images.

5. **Data Updates**: The 30-day refresh is for future API integration. Currently uses bundled JSON.

### Limitations
1. **Static Data**: Peak elevations and data are based on current USGS measurements. No real-time updates.

2. **Image Availability**: Not all peaks have high-quality public domain images. Generic placeholders are used when needed.

3. **Maps Integration**: Requires Google Maps or Apple Maps app for full functionality.

4. **iOS Only**: This is an iOS-only app. No Android, web, or macOS versions.

5. **Internet Required**: Initial launch requires internet to load images. Subsequent uses work offline.

## Future Enhancements

Potential features for future versions:
- Weather integration for current conditions
- Trail information and route details
- User accounts and favorite peaks
- Completed peaks tracking
- Photo sharing capability
- Augmented Reality peak identification
- Offline maps integration
- Push notifications for weather alerts
- Community features (comments, ratings)
- Expanded database (all 13ers, 12ers, etc.)

## Building for Release

### Create IPA File

1. **Archive the App**
   - In Xcode, select "Any iOS Device" as the target
   - Go to Product → Archive
   - Wait for the archive to complete

2. **Export IPA**
   - In the Organizer window that opens:
   - Select your archive
   - Click "Distribute App"
   - Choose "Ad Hoc" or "App Store" distribution
   - Follow the prompts to export the IPA file

3. **TestFlight (Optional)**
   - For beta testing, upload to App Store Connect
   - Invite testers via TestFlight
   - Get feedback before public release

4. **App Store Submission**
   - Create app in App Store Connect
   - Upload via Xcode or Transporter
   - Submit for review

## Troubleshooting

### Common Issues

**Issue**: App crashes on launch
- **Solution**: Ensure `peaks_data.json` is added to the app target

**Issue**: Images not loading
- **Solution**: Check internet connection on first launch. Images cache after first load.

**Issue**: "No peaks found"
- **Solution**: Verify JSON file is properly formatted and in the Resources folder

**Issue**: Google Maps not opening
- **Solution**: Ensure Google Maps or Apple Maps is installed on your device

**Issue**: Build errors in Xcode
- **Solution**: Clean build folder (Cmd+Shift+K), then rebuild

**Issue**: Data not updating
- **Solution**: Delete and reinstall app to clear cache, or wait for 30-day refresh

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Areas for contribution:
- Additional peak data and fun facts
- UI/UX improvements
- Bug fixes
- Performance optimizations
- Additional features

## License

This project is provided as-is for educational and personal use. Peak data is compiled from public sources. Image credits go to their respective owners (Wikimedia Commons, USGS, etc.).

## Credits

**Data Sources**:
- climb13ers.com
- 14ers.com
- SummitPost.org
- Peakbagger.com
- USGS
- Wikipedia

**Images**:
- Wikimedia Commons contributors
- USGS imagery database

**Inspiration**:
- Colorado's incredible mountain landscapes
- The hiking and climbing community

## Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Email: [your-email@example.com]

---

**Enjoy exploring Colorado's peaks!** 🏔️

*Note: This app is not affiliated with any official Colorado state organization. Always check current conditions and your abilities before attempting any peak.*
