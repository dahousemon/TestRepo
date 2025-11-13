# Colorado Peaks Explorer - Technical Setup Guide

This guide provides detailed technical instructions for setting up and building the Colorado Peaks Explorer iOS app.

## Prerequisites

### Required Software
- **macOS**: 12.0 (Monterey) or later
- **Xcode**: 13.0 or later
- **iOS Deployment Target**: iOS 15.0+
- **Swift**: 5.5+
- **Git**: For version control

### Required Knowledge
- Basic understanding of Xcode
- Familiarity with iOS development
- Understanding of Swift and SwiftUI (helpful but not required)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TestRepo
```

### 2. Create Xcode Project

Since this repository contains source files but not an `.xcodeproj` file, you need to create the Xcode project:

#### Option A: Using Xcode GUI

1. Open Xcode
2. Select **File → New → Project**
3. Choose **iOS** tab, then **App** template
4. Click **Next**
5. Configure the project:
   - **Product Name**: `ColoradoPeaksExplorer`
   - **Team**: Select your Apple Developer team
   - **Organization Identifier**: `com.yourname` (or your organization)
   - **Bundle Identifier**: Will auto-generate (e.g., `com.yourname.ColoradoPeaksExplorer`)
   - **Interface**: SwiftUI
   - **Language**: Swift
   - **Use Core Data**: Unchecked
   - **Include Tests**: Checked (optional)
6. Click **Next**
7. Save in the cloned repository folder as `ColoradoPeaksExplorer`

#### Option B: Using Existing Project Structure

If you want to preserve the existing folder structure:

1. Create a new Xcode project as above
2. Delete the auto-generated files (ContentView.swift, etc.)
3. Proceed to Step 3 below

### 3. Add Source Files to Project

You need to add all the source files to your Xcode project:

1. In Xcode, right-click on the `ColoradoPeaksExplorer` folder in the Project Navigator
2. Select **Add Files to "ColoradoPeaksExplorer"...**
3. Navigate to the repository folder
4. Add the following folders (make sure "Copy items if needed" is checked):
   - `ColoradoPeaksExplorer/Models/`
   - `ColoradoPeaksExplorer/Views/`
   - `ColoradoPeaksExplorer/Services/`
   - `ColoradoPeaksExplorer/Resources/`
   - `ColoradoPeaksExplorer/ColoradoPeaksExplorerApp.swift`

5. **Critical**: When adding `Resources/peaks_data.json`:
   - Ensure "Copy items if needed" is **checked**
   - Ensure "Add to targets: ColoradoPeaksExplorer" is **checked**
   - This makes the JSON file available to the app bundle

### 4. Configure Info.plist

1. In Project Navigator, select the project (top item)
2. Select the **ColoradoPeaksExplorer** target
3. Go to the **Info** tab
4. If using a custom Info.plist:
   - Go to **Build Settings** tab
   - Search for "Info.plist File"
   - Set path to: `ColoradoPeaksExplorer/SupportingFiles/Info.plist`

5. Ensure the following keys are present (or add them):
   - `LSApplicationQueriesSchemes`: Array with `comgooglemaps` and `maps`
   - This allows the app to open Google Maps

### 5. Configure Project Settings

#### General Settings
1. Select project → Target → **General** tab
2. Set **Deployment Target** to iOS 15.0
3. Set **Display Name** to "Colorado Peaks"
4. Configure **App Icons & Launch Screen** (optional, but recommended)

#### Signing & Capabilities
1. Go to **Signing & Capabilities** tab
2. **Automatically manage signing**: Checked
3. **Team**: Select your Apple Developer team
   - If you don't have a team, you can use a Personal Team (free)
   - Sign in with your Apple ID in Xcode → Preferences → Accounts

#### Build Settings (Optional but Recommended)
1. Go to **Build Settings** tab
2. Search for "Swift Language Version"
3. Ensure it's set to Swift 5.x
4. Search for "Enable Bitcode"
5. Set to **No** (not required for modern iOS apps)

### 6. Verify File Structure

Your Xcode project should now have this structure:

```
ColoradoPeaksExplorer (project)
└── ColoradoPeaksExplorer (group/folder)
    ├── ColoradoPeaksExplorerApp.swift
    ├── Models
    │   ├── Peak.swift
    │   └── ColorTheme.swift
    ├── Views
    │   ├── HomeView.swift
    │   └── PeakDetailView.swift
    ├── Services
    │   ├── PeakDataService.swift
    │   └── ImageCache.swift
    ├── Resources
    │   └── peaks_data.json  [IMPORTANT: Must be in bundle]
    └── SupportingFiles
        └── Info.plist
```

### 7. Verify peaks_data.json in Bundle

This is crucial! To verify:

1. Select the **ColoradoPeaksExplorer** target
2. Go to **Build Phases** tab
3. Expand **Copy Bundle Resources**
4. Verify that `peaks_data.json` is listed
5. If not, click **+** and add it

### 8. Build the Project

1. Select a simulator or connected device from the scheme selector
   - Recommended: iPhone 14 Pro or later simulator
   - Or connect a physical iPhone/iPad (iOS 15.0+)

2. Press **Cmd + B** to build
3. Fix any build errors (should be none if setup correctly)

4. Press **Cmd + R** to run
5. The app should launch successfully

## Troubleshooting Build Issues

### Issue: "No such module 'Foundation'"
**Solution**: Clean build folder (Cmd + Shift + K), then rebuild

### Issue: "peaks_data.json not found"
**Solution**:
1. Select peaks_data.json in Project Navigator
2. Open File Inspector (right sidebar)
3. Under "Target Membership", check "ColoradoPeaksExplorer"
4. Rebuild

### Issue: "Cannot find 'Peak' in scope"
**Solution**:
1. Ensure all Swift files are added to the project
2. Check that they're in the correct target membership
3. Clean and rebuild

### Issue: Code signing errors
**Solution**:
1. Go to Signing & Capabilities
2. Change Team to your Personal Team
3. If needed, change Bundle Identifier to something unique
4. Xcode will automatically fix provisioning

### Issue: Build succeeds but app crashes on launch
**Solution**:
1. Check that peaks_data.json is in the bundle (see step 7)
2. Verify JSON is valid (use a JSON validator)
3. Check Console output in Xcode for error messages

## Running on Physical Device

### Requirements
- iOS 15.0+ device
- USB cable
- Apple ID signed into Xcode

### Steps
1. Connect iPhone/iPad via USB
2. Trust the computer on your device
3. In Xcode, select your device from the scheme selector
4. Press Cmd + R to build and run
5. If prompted, go to Settings → General → VPN & Device Management on your iOS device
6. Trust your developer certificate
7. Return to the app and launch

## Testing

### Simulator Testing
Test on multiple simulators:
- iPhone SE (small screen)
- iPhone 14 Pro (standard size)
- iPhone 14 Pro Max (large screen)
- iPad Pro (tablet layout)

### Features to Test
- [ ] App launches successfully
- [ ] Peaks load and display
- [ ] Search functionality works
- [ ] Category filtering works
- [ ] Sort options work correctly
- [ ] Peak detail view opens
- [ ] Images load and cache
- [ ] Google Maps button opens Maps
- [ ] Offline mode works (after initial load)
- [ ] VoiceOver navigation works
- [ ] Dynamic text sizing works

### Performance Testing
- [ ] Smooth scrolling with 200+ peaks
- [ ] Fast search results
- [ ] Quick image loading (after cache)
- [ ] No memory leaks
- [ ] Efficient battery usage

## Creating Archive for Distribution

### For Ad Hoc Testing (TestFlight, etc.)

1. **Clean Project**
   ```
   Product → Clean Build Folder (Cmd + Shift + K)
   ```

2. **Archive**
   - Select "Any iOS Device" as destination
   - `Product → Archive`
   - Wait for archive to complete

3. **Organizer Window**
   - Automatically opens after archiving
   - Select the archive
   - Click **Distribute App**

4. **Choose Distribution Method**
   - **Ad Hoc**: For installing on specific devices
   - **Development**: For development devices
   - **App Store**: For App Store submission

5. **Export Options**
   - Select appropriate options
   - Click **Next** through the steps
   - Choose export location
   - Save the `.ipa` file

### For App Store Submission

1. **Create App in App Store Connect**
   - Go to appstoreconnect.apple.com
   - Click **+ App**
   - Fill in app information
   - Create app

2. **Archive in Xcode** (as above)

3. **Upload to App Store Connect**
   - In Organizer, select archive
   - Click **Distribute App**
   - Choose **App Store Connect**
   - Follow prompts to upload

4. **Submit for Review**
   - Go to App Store Connect
   - Select your app
   - Fill in all required information
   - Submit for review

## Customization

### Changing Bundle Identifier
1. Select project → Target → General
2. Change **Bundle Identifier** to your own (e.g., `com.yourname.ColoradoPeaksExplorer`)

### Changing App Name
1. Select project → Target → General
2. Change **Display Name**
3. Or edit Info.plist → `CFBundleDisplayName`

### Adding App Icon
1. Create icons in required sizes (use an icon generator tool)
2. In Assets.xcassets, select AppIcon
3. Drag and drop icons into appropriate slots
4. Required sizes: 1024x1024 (App Store), plus various sizes for devices

### Customizing Colors
Edit `ColoradoPeaksExplorer/Models/ColorTheme.swift`:
```swift
static let mountainBlue = Color(red: 0.25, green: 0.41, blue: 0.88)
// Change RGB values to customize colors
```

## Advanced Configuration

### Enabling Debug Logging
Add to `PeakDataService.swift`:
```swift
private let debugMode = true

func logDebug(_ message: String) {
    if debugMode {
        print("[DEBUG] \(message)")
    }
}
```

### Optimizing Images
To reduce app size:
1. Compress images before adding to JSON
2. Use WebP format (requires additional code)
3. Implement lazy loading (already included)

### Adding More Peaks
1. Edit `Resources/peaks_data.json`
2. Add peak objects to `top200Peaks` or `frontRangePeaks` arrays
3. Follow the existing JSON structure
4. Rebuild app

### Changing Cache Duration
Edit `PeakDataService.swift`:
```swift
private let cacheDuration: TimeInterval = 30 * 24 * 60 * 60 // 30 days
// Change to desired duration in seconds
```

## Development Tips

### SwiftUI Previews
Most views have preview code. To use:
1. Open a View file (e.g., HomeView.swift)
2. Press Cmd + Option + Enter to show preview
3. Click "Resume" if needed
4. Live preview appears on the right

### Debugging
- Set breakpoints by clicking line numbers
- Press Cmd + Y to enable/disable all breakpoints
- Use `print()` statements for quick debugging
- Check Xcode Console for errors

### Version Control
Recommended `.gitignore` entries:
```
# Xcode
*.xcworkspace
xcuserdata/
*.xcuserstate
*.xcuserdatad

# Build
build/
DerivedData/

# OS
.DS_Store
```

## Support

### Getting Help
- Check README.md for general usage
- Review Troubleshooting section above
- Check Xcode console for error messages
- Search Xcode documentation (Cmd + Shift + 0)

### Common Resources
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Swift.org](https://swift.org)
- [SwiftUI Documentation](https://developer.apple.com/xcode/swiftui/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/swiftui)

## Next Steps

After successful setup:
1. ✅ Run the app and test all features
2. ✅ Customize with your own data if desired
3. ✅ Test on multiple devices/simulators
4. ✅ Consider adding app icon and launch screen
5. ✅ Build for distribution
6. ✅ Submit to App Store (optional)

---

**Happy coding!** 🚀 If you encounter any issues not covered here, please open an issue on GitHub.
