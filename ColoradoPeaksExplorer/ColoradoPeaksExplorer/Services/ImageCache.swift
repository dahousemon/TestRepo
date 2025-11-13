//
//  ImageCache.swift
//  Colorado Peaks Explorer
//
//  Image loading and caching service
//

import SwiftUI
import Combine

class ImageCache {
    static let shared = ImageCache()
    private var cache = NSCache<NSString, UIImage>()

    private init() {
        cache.countLimit = 100 // Cache up to 100 images
        cache.totalCostLimit = 50 * 1024 * 1024 // 50 MB limit
    }

    func get(forKey key: String) -> UIImage? {
        return cache.object(forKey: key as NSString)
    }

    func set(_ image: UIImage, forKey key: String) {
        cache.setObject(image, forKey: key as NSString)
    }
}

class ImageLoader: ObservableObject {
    @Published var image: UIImage?
    @Published var isLoading = false

    private var cancellable: AnyCancellable?
    private let url: URL
    private let cache = ImageCache.shared

    init(url: URL) {
        self.url = url
    }

    deinit {
        cancellable?.cancel()
    }

    func load() {
        // Check cache first
        let cacheKey = url.absoluteString
        if let cachedImage = cache.get(forKey: cacheKey) {
            self.image = cachedImage
            return
        }

        isLoading = true

        cancellable = URLSession.shared.dataTaskPublisher(for: url)
            .map { UIImage(data: $0.data) }
            .replaceError(with: nil)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] downloadedImage in
                guard let self = self else { return }
                self.isLoading = false

                if let downloadedImage = downloadedImage {
                    self.cache.set(downloadedImage, forKey: cacheKey)
                    self.image = downloadedImage
                }
            }
    }

    func cancel() {
        cancellable?.cancel()
    }
}

/// Async image view with caching
struct CachedAsyncImage: View {
    @StateObject private var loader: ImageLoader
    let placeholder: Image

    init(url: URL, placeholder: Image = Image(systemName: "photo")) {
        _loader = StateObject(wrappedValue: ImageLoader(url: url))
        self.placeholder = placeholder
    }

    var body: some View {
        Group {
            if let image = loader.image {
                Image(uiImage: image)
                    .resizable()
            } else {
                ZStack {
                    ColorTheme.rockGray.opacity(0.1)

                    if loader.isLoading {
                        ProgressView()
                    } else {
                        placeholder
                            .resizable()
                            .scaledToFit()
                            .foregroundColor(ColorTheme.rockGray)
                            .padding(40)
                    }
                }
            }
        }
        .onAppear {
            loader.load()
        }
        .onDisappear {
            loader.cancel()
        }
    }
}
