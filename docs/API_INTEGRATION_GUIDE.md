# WallCraft API Integration Guide

Complete guide for integrating the WallCraft wallpaper collection into your applications.

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Integration Examples](#integration-examples)
3. [Image URLs and Formats](#image-urls-and-formats)
4. [Search and Filtering](#search-and-filtering)
5. [Performance Best Practices](#performance-best-practices)
6. [Mobile App Integration](#mobile-app-integration)
7. [Rate Limiting and Caching](#rate-limiting-and-caching)
8. [Error Handling](#error-handling)

## 🚀 Getting Started

### Base URL
```
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/
```

### Quick Test
```bash
# Test API availability
curl -I https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json

# Get collection overview
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json | jq '.totalWallpapers'

# Get nature wallpapers
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json | jq '.count'
```

## 💻 Integration Examples

### JavaScript/TypeScript

#### Fetch All Categories
```javascript
async function getCategories() {
  const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json');
  const data = await response.json();
  return data.categories;
}

// Usage
getCategories().then(categories => {
  categories.forEach(category => {
    console.log(`${category.name}: ${category.count} wallpapers`);
  });
});
```

#### Get Random Wallpaper from Category
```javascript
async function getRandomWallpaper(category) {
  const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
  const data = await response.json();
  const randomIndex = Math.floor(Math.random() * data.wallpapers.length);
  return data.wallpapers[randomIndex];
}

// Usage
getRandomWallpaper('nature').then(wallpaper => {
  console.log('Random nature wallpaper:', wallpaper.title);
  console.log('Download URL:', wallpaper.download_url);
});
```

#### React Hook Example
```jsx
import { useState, useEffect } from 'react';

function useWallpapers(category) {
  const [wallpapers, setWallpapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchWallpapers() {
      try {
        setLoading(true);
        const response = await fetch(
          `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`
        );
        const data = await response.json();
        setWallpapers(data.wallpapers);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchWallpapers();
  }, [category]);

  return { wallpapers, loading, error };
}

// Component usage
function WallpaperGallery({ category }) {
  const { wallpapers, loading, error } = useWallpapers(category);

  if (loading) return <div>Loading wallpapers...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="gallery">
      {wallpapers.map(wallpaper => (
        <img
          key={wallpaper.id}
          src={wallpaper.thumbnail_url}
          alt={wallpaper.alt_text}
          onClick={() => window.open(wallpaper.download_url)}
        />
      ))}
    </div>
  );
}
```

#### Advanced Wallpaper Manager
```javascript
class WallpaperAPI {
  constructor() {
    this.baseURL = 'https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/';
    this.cache = new Map();
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes
  }

  async request(endpoint) {
    const url = this.baseURL + endpoint;
    const cached = this.cache.get(url);
    
    if (cached && Date.now() - cached.timestamp < this.cacheDuration) {
      return cached.data;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.cache.set(url, { data, timestamp: Date.now() });
    return data;
  }

  async getIndex() {
    return this.request('index.json');
  }

  async getCategory(category) {
    return this.request(`categories/${category}.json`);
  }

  async searchWallpapers(query, categories = null) {
    const results = [];
    const searchCategories = categories || await this.getAvailableCategories();

    for (const category of searchCategories) {
      const categoryData = await this.getCategory(category);
      const matches = categoryData.wallpapers.filter(wallpaper =>
        wallpaper.title.toLowerCase().includes(query.toLowerCase()) ||
        wallpaper.description.toLowerCase().includes(query.toLowerCase()) ||
        wallpaper.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
      );
      results.push(...matches);
    }

    return results;
  }

  async getAvailableCategories() {
    const index = await this.getIndex();
    return index.categories.map(cat => cat.id);
  }

  async getRandomWallpapers(count = 10, category = null) {
    if (category) {
      const categoryData = await this.getCategory(category);
      return this.shuffleArray(categoryData.wallpapers).slice(0, count);
    } else {
      const index = await this.getIndex();
      return this.shuffleArray(index.featured).slice(0, count);
    }
  }

  shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  async downloadWallpaper(wallpaper, filename = null) {
    const response = await fetch(wallpaper.download_url);
    const blob = await response.blob();
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || wallpaper.filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}

// Usage
const api = new WallpaperAPI();

// Get random wallpapers
api.getRandomWallpapers(5, 'nature').then(wallpapers => {
  wallpapers.forEach(w => console.log(w.title));
});

// Search for wallpapers
api.searchWallpapers('mountain').then(results => {
  console.log(`Found ${results.length} mountain wallpapers`);
});
```

### Python

#### Basic API Client
```python
import requests
import random
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta

class WallpaperAPI:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/"
        self.session = requests.Session()
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    def _get_cached_or_fetch(self, endpoint: str) -> Dict:
        """Get data from cache or fetch from API"""
        url = self.base_url + endpoint
        
        if url in self.cache:
            data, timestamp = self.cache[url]
            if datetime.now() - timestamp < self.cache_duration:
                return data
        
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        
        self.cache[url] = (data, datetime.now())
        return data
    
    def get_categories(self) -> List[Dict]:
        """Get all available categories"""
        index = self._get_cached_or_fetch("index.json")
        return index['categories']
    
    def get_category_wallpapers(self, category: str) -> Dict:
        """Get all wallpapers from a specific category"""
        return self._get_cached_or_fetch(f"categories/{category}.json")
    
    def get_random_wallpaper(self, category: Optional[str] = None) -> Dict:
        """Get a random wallpaper, optionally from specific category"""
        if category:
            data = self.get_category_wallpapers(category)
            return random.choice(data['wallpapers'])
        else:
            index = self._get_cached_or_fetch("index.json")
            return random.choice(index['featured'])
    
    def search_wallpapers(self, query: str, categories: Optional[List[str]] = None) -> List[Dict]:
        """Search wallpapers by query across categories"""
        results = []
        search_categories = categories or [cat['id'] for cat in self.get_categories()]
        
        query_lower = query.lower()
        
        for category in search_categories:
            try:
                data = self.get_category_wallpapers(category)
                matches = [
                    wallpaper for wallpaper in data['wallpapers']
                    if (query_lower in wallpaper['title'].lower() or
                        query_lower in wallpaper['description'].lower() or
                        any(query_lower in tag.lower() for tag in wallpaper['tags']))
                ]
                results.extend(matches)
            except Exception as e:
                print(f"Error searching category {category}: {e}")
        
        return results
    
    def download_wallpaper(self, wallpaper: Dict, filepath: str) -> None:
        """Download wallpaper to local file"""
        url = wallpaper.get('download_url')
        if not url:
            # Fallback to repository URL
            url = f"{self.base_url}wallpapers/{wallpaper['category']}/{wallpaper['filename']}"
        
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def get_wallpapers_by_tags(self, tags: List[str], category: Optional[str] = None) -> List[Dict]:
        """Get wallpapers that match any of the specified tags"""
        if category:
            categories = [category]
        else:
            categories = [cat['id'] for cat in self.get_categories()]
        
        results = []
        tags_lower = [tag.lower() for tag in tags]
        
        for cat in categories:
            try:
                data = self.get_category_wallpapers(cat)
                matches = [
                    wallpaper for wallpaper in data['wallpapers']
                    if any(any(tag_lower in wallpaper_tag.lower() for wallpaper_tag in wallpaper['tags']) 
                          for tag_lower in tags_lower)
                ]
                results.extend(matches)
            except Exception as e:
                print(f"Error filtering category {cat}: {e}")
        
        return results

# Usage examples
api = WallpaperAPI()

# Get all categories
categories = api.get_categories()
print("Available categories:")
for cat in categories:
    print(f"  {cat['name']}: {cat['count']} wallpapers")

# Get random nature wallpaper
nature_wallpaper = api.get_random_wallpaper('nature')
print(f"\nRandom nature wallpaper: {nature_wallpaper['title']}")

# Search for mountain wallpapers
mountain_wallpapers = api.search_wallpapers('mountain')
print(f"\nFound {len(mountain_wallpapers)} mountain wallpapers")

# Get wallpapers with specific tags
dark_wallpapers = api.get_wallpapers_by_tags(['dark', 'moody'], 'abstract')
print(f"Found {len(dark_wallpapers)} dark abstract wallpapers")

# Download wallpaper
api.download_wallpaper(nature_wallpaper, 'wallpaper.jpg')
print("Wallpaper downloaded!")
```

#### Django Integration
```python
# models.py
from django.db import models
import requests
from datetime import datetime

class WallpaperCategory(models.Model):
    name = models.CharField(max_length=100)
    category_id = models.CharField(max_length=50, unique=True)
    count = models.IntegerField()
    description = models.TextField()
    last_updated = models.DateTimeField()
    
    def get_wallpapers(self):
        """Fetch wallpapers from API"""
        url = f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/{self.category_id}.json"
        response = requests.get(url)
        return response.json()['wallpapers']
    
    class Meta:
        ordering = ['name']

class FavoriteWallpaper(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    wallpaper_id = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'wallpaper_id']

# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import requests

@cache_page(60 * 5)  # Cache for 5 minutes
def wallpaper_gallery(request, category=None):
    base_url = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/"
    
    if category:
        response = requests.get(f"{base_url}categories/{category}.json")
        wallpapers = response.json()['wallpapers']
        title = f"{category.title()} Wallpapers"
    else:
        response = requests.get(f"{base_url}index.json")
        wallpapers = response.json()['featured']
        title = "Featured Wallpapers"
    
    return render(request, 'gallery.html', {
        'wallpapers': wallpapers,
        'title': title,
        'category': category
    })

def api_wallpapers(request, category):
    """API endpoint for wallpapers"""
    cache_key = f"wallpapers_{category}"
    wallpapers = cache.get(cache_key)
    
    if not wallpapers:
        base_url = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/"
        response = requests.get(f"{base_url}categories/{category}.json")
        wallpapers = response.json()
        cache.set(cache_key, wallpapers, 60 * 5)  # Cache for 5 minutes
    
    return JsonResponse(wallpapers)

def api_search(request):
    """Search wallpapers across categories"""
    query = request.GET.get('q', '')
    categories = request.GET.get('categories', '').split(',') if request.GET.get('categories') else None
    
    if not query:
        return JsonResponse({'error': 'Query parameter required'}, status=400)
    
    # Implementation would search across categories
    # This is a simplified version
    results = []
    return JsonResponse({'results': results, 'query': query})

# templates/gallery.html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        .gallery { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
            gap: 10px; 
            padding: 20px;
        }
        .wallpaper { 
            aspect-ratio: 9/16; 
            border-radius: 8px; 
            overflow: hidden; 
            cursor: pointer;
        }
        .wallpaper img { 
            width: 100%; 
            height: 100%; 
            object-fit: cover; 
        }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="gallery">
        {% for wallpaper in wallpapers %}
        <div class="wallpaper" onclick="openWallpaper('{{ wallpaper.download_url }}')">
            <img src="{{ wallpaper.thumbnail_url }}" alt="{{ wallpaper.title }}" loading="lazy">
        </div>
        {% endfor %}
    </div>

    <script>
        function openWallpaper(url) {
            window.open(url, '_blank');
        }
    </script>
</body>
</html>
```

### Swift (iOS)

```swift
import Foundation
import UIKit
import Combine

// MARK: - Data Models
struct Wallpaper: Codable {
    let id: String
    let title: String
    let description: String
    let width: Int
    let height: Int
    let tags: [String]
    let downloadURL: String
    let thumbnailURL: String
    let fileSize: Int
    let filename: String
    
    enum CodingKeys: String, CodingKey {
        case id, title, description, width, height, tags, filename
        case downloadURL = "download_url"
        case thumbnailURL = "thumbnail_url"
        case fileSize = "file_size"
    }
}

struct CategoryResponse: Codable {
    let category: String
    let name: String
    let description: String
    let count: Int
    let wallpapers: [Wallpaper]
}

struct IndexResponse: Codable {
    let version: String
    let totalWallpapers: Int
    let categories: [Category]
    let featured: [Wallpaper]
    
    enum CodingKeys: String, CodingKey {
        case version, categories, featured
        case totalWallpapers = "totalWallpapers"
    }
}

struct Category: Codable {
    let id: String
    let name: String
    let count: Int
    let description: String
}

// MARK: - API Service
class WallpaperAPIService: ObservableObject {
    static let shared = WallpaperAPIService()
    private let baseURL = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/"
    private let session = URLSession.shared
    private var cancellables = Set<AnyCancellable>()
    
    // Cache
    private var cache: [String: (data: Any, timestamp: Date)] = [:]
    private let cacheExpiration: TimeInterval = 300 // 5 minutes
    
    private init() {}
    
    // MARK: - Generic Request Method
    private func request<T: Codable>(_ endpoint: String, type: T.Type) -> AnyPublisher<T, Error> {
        guard let url = URL(string: baseURL + endpoint) else {
            return Fail(error: URLError(.badURL))
                .eraseToAnyPublisher()
        }
        
        // Check cache
        if let cached = cache[endpoint],
           Date().timeIntervalSince(cached.timestamp) < cacheExpiration,
           let data = cached.data as? T {
            return Just(data)
                .setFailureType(to: Error.self)
                .eraseToAnyPublisher()
        }
        
        return session.dataTaskPublisher(for: url)
            .map(\.data)
            .decode(type: T.self, decoder: JSONDecoder())
            .handleEvents(receiveOutput: { [weak self] data in
                self?.cache[endpoint] = (data, Date())
            })
            .eraseToAnyPublisher()
    }
    
    // MARK: - API Methods
    func getIndex() -> AnyPublisher<IndexResponse, Error> {
        return request("index.json", type: IndexResponse.self)
    }
    
    func getCategory(_ category: String) -> AnyPublisher<CategoryResponse, Error> {
        return request("categories/\(category).json", type: CategoryResponse.self)
    }
    
    func searchWallpapers(query: String, in categories: [String]? = nil) -> AnyPublisher<[Wallpaper], Error> {
        let searchCategories = categories ?? ["nature", "abstract", "space", "architecture"]
        
        let publishers = searchCategories.map { category in
            getCategory(category)
                .map { response in
                    response.wallpapers.filter { wallpaper in
                        wallpaper.title.localizedCaseInsensitiveContains(query) ||
                        wallpaper.description.localizedCaseInsensitiveContains(query) ||
                        wallpaper.tags.contains { $0.localizedCaseInsensitiveContains(query) }
                    }
                }
                .catch { _ in Just([Wallpaper]()) }
        }
        
        return Publishers.MergeMany(publishers)
            .collect()
            .map { $0.flatMap { $0 } }
            .eraseToAnyPublisher()
    }
    
    func downloadImage(from url: String) -> AnyPublisher<UIImage, Error> {
        guard let imageURL = URL(string: url) else {
            return Fail(error: URLError(.badURL))
                .eraseToAnyPublisher()
        }
        
        return session.dataTaskPublisher(for: imageURL)
            .map(\.data)
            .tryMap { data in
                guard let image = UIImage(data: data) else {
                    throw URLError(.cannotDecodeContentData)
                }
                return image
            }
            .eraseToAnyPublisher()
    }
}

// MARK: - ViewModel
class WallpaperViewModel: ObservableObject {
    @Published var wallpapers: [Wallpaper] = []
    @Published var categories: [Category] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = WallpaperAPIService.shared
    private var cancellables = Set<AnyCancellable>()
    
    func loadCategories() {
        isLoading = true
        errorMessage = nil
        
        apiService.getIndex()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] response in
                    self?.categories = response.categories
                    self?.wallpapers = response.featured
                }
            )
            .store(in: &cancellables)
    }
    
    func loadWallpapers(for category: String) {
        isLoading = true
        errorMessage = nil
        
        apiService.getCategory(category)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] response in
                    self?.wallpapers = response.wallpapers
                }
            )
            .store(in: &cancellables)
    }
    
    func searchWallpapers(query: String) {
        guard !query.isEmpty else { return }
        
        isLoading = true
        errorMessage = nil
        
        apiService.searchWallpapers(query: query)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] wallpapers in
                    self?.wallpapers = wallpapers
                }
            )
            .store(in: &cancellables)
    }
}

// MARK: - SwiftUI Views
import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = WallpaperViewModel()
    @State private var selectedCategory: String?
    @State private var searchText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                SearchBar(text: $searchText, onSearchButtonClicked: {
                    viewModel.searchWallpapers(query: searchText)
                })
                
                if viewModel.isLoading {
                    ProgressView("Loading...")
                        .frame(maxHeight: .infinity)
                } else if let errorMessage = viewModel.errorMessage {
                    Text("Error: \(errorMessage)")
                        .foregroundColor(.red)
                        .padding()
                } else {
                    ScrollView {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 10) {
                            ForEach(viewModel.wallpapers, id: \.id) { wallpaper in
                                WallpaperCard(wallpaper: wallpaper)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("WallCraft")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu("Categories") {
                        ForEach(viewModel.categories, id: \.id) { category in
                            Button(category.name) {
                                selectedCategory = category.id
                                viewModel.loadWallpapers(for: category.id)
                            }
                        }
                    }
                }
            }
        }
        .onAppear {
            viewModel.loadCategories()
        }
    }
}

struct WallpaperCard: View {
    let wallpaper: Wallpaper
    @State private var image: UIImage?
    
    var body: some View {
        VStack(alignment: .leading) {
            AsyncImage(url: URL(string: wallpaper.thumbnailURL)) { image in
                image
                    .resizable()
                    .aspectRatio(9/16, contentMode: .fill)
            } placeholder: {
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
                    .aspectRatio(9/16, contentMode: .fill)
            }
            .clipShape(RoundedRectangle(cornerRadius: 8))
            
            VStack(alignment: .leading, spacing: 4) {
                Text(wallpaper.title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(2)
                
                HStack {
                    Text("\(wallpaper.width)×\(wallpaper.height)")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Button(action: {
                        // Download or set as wallpaper
                    }) {
                        Image(systemName: "arrow.down.circle")
                            .foregroundColor(.blue)
                    }
                }
            }
            .padding(.horizontal, 4)
        }
    }
}

struct SearchBar: UIViewRepresentable {
    @Binding var text: String
    var onSearchButtonClicked: () -> Void
    
    func makeUIView(context: Context) -> UISearchBar {
        let searchBar = UISearchBar()
        searchBar.delegate = context.coordinator
        searchBar.placeholder = "Search wallpapers..."
        searchBar.searchBarStyle = .minimal
        return searchBar
    }
    
    func updateUIView(_ uiView: UISearchBar, context: Context) {
        uiView.text = text
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UISearchBarDelegate {
        let parent: SearchBar
        
        init(_ parent: SearchBar) {
            self.parent = parent
        }
        
        func searchBar(_ searchBar: UISearchBar, textDidChange searchText: String) {
            parent.text = searchText
        }
        
        func searchBarSearchButtonClicked(_ searchBar: UISearchBar) {
            parent.onSearchButtonClicked()
            searchBar.resignFirstResponder()
        }
    }
}
```

### Kotlin (Android)

```kotlin
// Data classes
data class Wallpaper(
    val id: String,
    val title: String,
    val description: String,
    val width: Int,
    val height: Int,
    val tags: List<String>,
    @SerializedName("download_url") val downloadUrl: String,
    @SerializedName("thumbnail_url") val thumbnailUrl: String,
    @SerializedName("file_size") val fileSize: Int,
    val filename: String
)

data class CategoryResponse(
    val category: String,
    val name: String,
    val description: String,
    val count: Int,
    val wallpapers: List<Wallpaper>
)

data class IndexResponse(
    val version: String,
    val totalWallpapers: Int,
    val categories: List<Category>,
    val featured: List<Wallpaper>
)

data class Category(
    val id: String,
    val name: String,
    val count: Int,
    val description: String
)

// API Interface
interface WallpaperApiService {
    @GET("categories/{category}.json")
    suspend fun getWallpapers(@Path("category") category: String): CategoryResponse
    
    @GET("index.json")
    suspend fun getIndex(): IndexResponse
}

// Repository with caching
class WallpaperRepository @Inject constructor(
    private val apiService: WallpaperApiService,
    private val cacheManager: CacheManager
) {
    
    suspend fun getWallpapers(category: String): Result<List<Wallpaper>> {
        return try {
            // Check cache first
            cacheManager.getWallpapers(category)?.let { cached ->
                return Result.success(cached)
            }
            
            // Fetch from API
            val response = apiService.getWallpapers(category)
            cacheManager.cacheWallpapers(category, response.wallpapers)
            Result.success(response.wallpapers)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun searchWallpapers(
        query: String, 
        categories: List<String>? = null
    ): Result<List<Wallpaper>> {
        return try {
            val searchCategories = categories ?: listOf("nature", "abstract", "space", "architecture")
            val results = mutableListOf<Wallpaper>()
            
            searchCategories.forEach { category ->
                try {
                    val categoryWallpapers = getWallpapers(category).getOrNull() ?: emptyList()
                    val matches = categoryWallpapers.filter { wallpaper ->
                        wallpaper.title.contains(query, ignoreCase = true) ||
                        wallpaper.description.contains(query, ignoreCase = true) ||
                        wallpaper.tags.any { it.contains(query, ignoreCase = true) }
                    }
                    results.addAll(matches)
                } catch (e: Exception) {
                    // Continue with other categories
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

// Cache Manager
class CacheManager @Inject constructor(
    private val context: Context
) {
    private val cache = mutableMapOf<String, Pair<List<Wallpaper>, Long>>()
    private val cacheExpiration = 5 * 60 * 1000L // 5 minutes
    
    fun getWallpapers(category: String): List<Wallpaper>? {
        val cached = cache[category]
        return if (cached != null && System.currentTimeMillis() - cached.second < cacheExpiration) {
            cached.first
        } else {
            cache.remove(category)
            null
        }
    }
    
    fun cacheWallpapers(category: String, wallpapers: List<Wallpaper>) {
        cache[category] = Pair(wallpapers, System.currentTimeMillis())
    }
}

// ViewModel
class WallpaperViewModel @Inject constructor(
    private val repository: WallpaperRepository
) : ViewModel() {
    
    private val _wallpapers = MutableLiveData<List<Wallpaper>>()
    val wallpapers: LiveData<List<Wallpaper>> = _wallpapers
    
    private val _categories = MutableLiveData<List<Category>>()
    val categories: LiveData<List<Category>> = _categories
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    fun loadCategories() {
        viewModelScope.launch {
            _loading.value = true
            try {
                repository.getIndex().fold(
                    onSuccess = { response ->
                        _categories.value = response.categories
                        _wallpapers.value = response.featured
                    },
                    onFailure = { exception ->
                        _error.value = exception.message
                    }
                )
            } finally {
                _loading.value = false
            }
        }
    }
    
    fun loadWallpapers(category: String) {
        viewModelScope.launch {
            _loading.value = true
            repository.getWallpapers(category).fold(
                onSuccess = { _wallpapers.value = it },
                onFailure = { _error.value = it.message }
            )
            _loading.value = false
        }
    }
    
    fun searchWallpapers(query: String) {
        if (query.isBlank()) return
        
        viewModelScope.launch {
            _loading.value = true
            repository.searchWallpapers(query).fold(
                onSuccess = { _wallpapers.value = it },
                onFailure = { _error.value = it.message }
            )
            _loading.value = false
        }
    }
}

// Composable UI
@Composable
fun WallpaperScreen(
    viewModel: WallpaperViewModel = hiltViewModel()
) {
    val wallpapers by viewModel.wallpapers.observeAsState(emptyList())
    val categories by viewModel.categories.observeAsState(emptyList())
    val loading by viewModel.loading.observeAsState(false)
    val error by viewModel.error.observeAsState()
    
    var searchQuery by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf<String?>(null) }
    
    LaunchedEffect(Unit) {
        viewModel.loadCategories()
    }
    
    Column {
        // Search bar
        SearchBar(
            query = searchQuery,
            onQueryChange = { searchQuery = it },
            onSearch = { viewModel.searchWallpapers(searchQuery) }
        )
        
        // Categories
        LazyRow(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(categories) { category ->
                FilterChip(
                    onClick = {
                        selectedCategory = category.id
                        viewModel.loadWallpapers(category.id)
                    },
                    label = { Text("${category.name} (${category.count})") },
                    selected = selectedCategory == category.id
                )
            }
        }
        
        // Content
        when {
            loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            error != null -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Error: $error",
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
            else -> {
                WallpaperGrid(wallpapers = wallpapers)
            }
        }
    }
}

@Composable
fun WallpaperGrid(
    wallpapers: List<Wallpaper>,
    modifier: Modifier = Modifier
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        modifier = modifier.padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(wallpapers) { wallpaper ->
            WallpaperCard(
                wallpaper = wallpaper,
                onClick = { /* Handle click */ }
            )
        }
    }
}

@Composable
fun WallpaperCard(
    wallpaper: Wallpaper,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick() },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column {
            AsyncImage(
                model = wallpaper.thumbnailUrl,
                contentDescription = wallpaper.title,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(9f / 16f),
                contentScale = ContentScale.Crop,
                placeholder = painterResource(R.drawable.placeholder),
                error = painterResource(R.drawable.error_placeholder)
            )
            
            Column(
                modifier = Modifier.padding(8.dp)
            ) {
                Text(
                    text = wallpaper.title,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "${wallpaper.width}×${wallpaper.height}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    
                    IconButton(
                        onClick = { /* Download action */ }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Download,
                            contentDescription = "Download"
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        placeholder = { Text("Search wallpapers...") },
        leadingIcon = {
            Icon(
                imageVector = Icons.Default.Search,
                contentDescription = "Search"
            )
        },
        trailingIcon = {
            if (query.isNotEmpty()) {
                IconButton(onClick = { onQueryChange("") }) {
                    Icon(
                        imageVector = Icons.Default.Clear,
                        contentDescription = "Clear"
                    )
                }
            }
        },
        keyboardOptions = KeyboardOptions(
            imeAction = ImeAction.Search
        ),
        keyboardActions = KeyboardActions(
            onSearch = { onSearch() }
        ),
        singleLine = true
    )
}
```

## 🖼️ Image URLs and Formats

### High-Resolution Images
```
Pattern: https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/{category}/{filename}
Example: https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg

Specifications:
- Resolution: 1080×1920 (Mobile Portrait)
- Format: JPEG
- Quality: High (85-95%)
- File Size: 100KB - 2MB average
```

### Thumbnails
```
Pattern: https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/{category}/{filename}
Example: https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/nature/nature_001.jpg

Specifications:
- Resolution: 300×533 (Mobile Portrait)
- Format: JPEG
- Quality: Medium (70-80%)
- File Size: 20-80KB average
```

### External Sources (Unsplash)
Many wallpapers link directly to Unsplash's CDN for optimal performance:
```
Pattern: https://images.unsplash.com/photo-{id}?w=1080&h=1920&fit=crop&crop=center&q=85
Example: https://images.unsplash.com/photo-1649700142623-07fe807400fc?w=1080&h=1920&fit=crop&crop=center&q=85

Benefits:
- Global CDN distribution
- Optimized delivery
- Dynamic resizing
- WebP support (add &fm=webp)
```

## 🔍 Search and Filtering

### Filter by Tags
```javascript
async function searchByTags(category, tags) {
  const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
  const data = await response.json();
  
  return data.wallpapers.filter(wallpaper => 
    tags.some(tag => wallpaper.tags.includes(tag))
  );
}

// Usage
const darkWallpapers = await searchByTags('abstract', ['dark', 'moody']);
```

### Filter by Description
```javascript
function searchByKeyword(wallpapers, keyword) {
  return wallpapers.filter(wallpaper => 
    wallpaper.title.toLowerCase().includes(keyword.toLowerCase()) ||
    wallpaper.description.toLowerCase().includes(keyword.toLowerCase()) ||
    wallpaper.alt_text.toLowerCase().includes(keyword.toLowerCase())
  );
}
```

### Sort Options
```javascript
function sortWallpapers(wallpapers, sortBy) {
  switch (sortBy) {
    case 'newest':
      return wallpapers.sort((a, b) => new Date(b.scraped_at) - new Date(a.scraped_at));
    case 'largest':
      return wallpapers.sort((a, b) => b.file_size - a.file_size);
    case 'title':
      return wallpapers.sort((a, b) => a.title.localeCompare(b.title));
    default:
      return wallpapers;
  }
}
```

## 🚀 Performance Best Practices

### Caching Strategy
```javascript
class WallpaperCache {
  constructor() {
    this.cache = new Map();
    this.maxAge = 5 * 60 * 1000; // 5 minutes
  }
  
  async get(url) {
    const cached = this.cache.get(url);
    if (cached && Date.now() - cached.timestamp < this.maxAge) {
      return cached.data;
    }
    
    const response = await fetch(url);
    const data = await response.json();
    
    this.cache.set(url, {
      data,
      timestamp: Date.now()
    });
    
    return data;
  }
}

const cache = new WallpaperCache();
```

### Progressive Loading
```javascript
function createProgressiveImage(wallpaper) {
  const img = new Image();
  
  // Load thumbnail first
  img.src = wallpaper.thumbnail_url;
  img.onload = () => {
    // Display thumbnail immediately
    displayImage(img);
    
    // Then load high-res in background
    const highRes = new Image();
    highRes.src = wallpaper.download_url;
    highRes.onload = () => {
      // Replace with high-res when ready
      img.src = highRes.src;
    };
  };
  
  return img;
}
```

### Batch Loading
```javascript
async function loadWallpapersBatch(category, page = 1, limit = 20) {
  const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
  const data = await response.json();
  
  const start = (page - 1) * limit;
  const end = start + limit;
  
  return {
    wallpapers: data.wallpapers.slice(start, end),
    hasMore: end < data.wallpapers.length,
    total: data.wallpapers.length
  };
}
```

## 🔒 Rate Limiting and Usage Guidelines

### Recommended Limits
- **Requests per minute**: 60
- **Concurrent downloads**: 5
- **Cache duration**: 5-10 minutes for metadata
- **Thumbnail caching**: 1 hour
- **Full image caching**: 24 hours

### Implementation Example
```javascript
class RateLimiter {
  constructor(maxRequests = 60, windowMs = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = [];
  }
  
  async makeRequest(url) {
    const now = Date.now();
    
    // Remove old requests outside window
    this.requests = this.requests.filter(
      time => now - time < this.windowMs
    );
    
    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = Math.min(...this.requests);
      const waitTime = this.windowMs - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    this.requests.push(now);
    return fetch(url);
  }
}
```

## 🧪 Testing Your Integration

### Basic API Test
```bash
# Test master index
curl -I https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json

# Test category endpoint
curl -I https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json

# Test image download
curl -I https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg
```

### JavaScript Test Suite
```javascript
// Basic API tests
async function testAPI() {
  console.log('Testing WallCraft API...');
  
  // Test 1: Master index
  try {
    const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json');
    const data = await response.json();
    console.log('✅ Master index loaded:', data.totalWallpapers, 'wallpapers');
  } catch (error) {
    console.error('❌ Master index failed:', error);
  }
  
  // Test 2: Category endpoint
  try {
    const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json');
    const data = await response.json();
    console.log('✅ Nature category loaded:', data.count, 'wallpapers');
  } catch (error) {
    console.error('❌ Nature category failed:', error);
  }
  
  // Test 3: Image accessibility
  try {
    const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg', { method: 'HEAD' });
    console.log('✅ Image accessible:', response.status === 200);
  } catch (error) {
    console.error('❌ Image access failed:', error);
  }
}

testAPI();
```

## 📞 Support and Contributing

### Reporting Issues
- **Bug Reports**: [GitHub Issues](https://github.com/ddh4r4m/wallpaper-collection/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/ddh4r4m/wallpaper-collection/discussions)
- **API Questions**: Include your integration details and error messages

### Contributing
1. **New Categories**: Submit high-quality wallpaper suggestions
2. **Quality Improvements**: Report low-quality images for replacement
3. **API Enhancements**: Suggest new metadata fields or endpoints
4. **Documentation**: Help improve this documentation

### Attribution
When using this collection in your application:
```
Wallpapers provided by WallCraft Collection
https://github.com/ddh4r4m/wallpaper-collection
```

---

**Made with ❤️ for the developer community**