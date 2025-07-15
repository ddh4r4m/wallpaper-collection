# WallCraft API Documentation

[![Total Wallpapers](https://img.shields.io/badge/Wallpapers-1491-blue)](https://github.com/ddh4r4m/wallpaper-collection)
[![Categories](https://img.shields.io/badge/Categories-20-green)](https://github.com/ddh4r4m/wallpaper-collection)
[![API Status](https://img.shields.io/badge/API-Live-success)](https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json)

Complete API documentation for fetching high-quality wallpapers from the WallCraft collection. **No API keys required** - start using immediately!

## 🚀 Quick Start

### Test the API
```bash
# Get collection overview
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json

# Get nature wallpapers  
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json

# Download a wallpaper
curl -o nature_wallpaper.jpg "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg"
```

## 🔗 API Endpoints

### Base URL
```
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/
```

### Core Endpoints

| Endpoint | Description | Response Type |
|----------|-------------|---------------|
| `index.json` | Master collection index | JSON |
| `categories/{category}.json` | Category wallpapers | JSON |
| `wallpapers/{category}/{filename}` | High-res wallpaper | JPEG |
| `thumbnails/{category}/{filename}` | Thumbnail (300×533) | JPEG |
| `collection_statistics.txt` | Human-readable stats | Text |

### Available Categories
```
abstract, nature, space, minimal, cyberpunk, gaming, anime, movies, music, 
cars, sports, technology, architecture, art, dark, neon, pastel, vintage, 
gradient, seasonal
```

## 📊 Collection Statistics

- **Total Wallpapers**: 1,491
- **Categories**: 20 
- **Resolution**: 1080×1920 (Mobile Portrait)
- **Format**: JPEG, High Quality
- **Average File Size**: ~500KB
- **Total Collection Size**: 1.9GB

### Top Categories by Count

| Category | Count | Description |
|----------|-------|-------------|
| **Nature** | 284 | Landscapes, mountains, forests, oceans |
| **Architecture** | 275 | Buildings, structures, urban photography |
| **Abstract** | 217 | Artistic patterns, geometric designs |
| **Space** | 86 | Galaxies, nebulae, cosmic scenes |
| **Seasonal** | 85 | Holiday and seasonal themes |
| **Dark** | 80 | Dark themes, gothic aesthetics |
| **Neon** | 78 | Neon lights, electric themes |
| **Gaming** | 76 | Game screenshots, concept art |

## 📄 API Response Formats

### Master Index (`index.json`)

Complete collection metadata with categories and featured wallpapers.

```json
{
  "version": "2.0.0",
  "lastUpdated": "2025-07-15T16:50:05.934492Z",
  "totalWallpapers": 1491,
  "categories": [
    {
      "id": "nature",
      "name": "Nature", 
      "count": 284,
      "description": "Natural landscapes, mountains, forests, oceans, wildlife, and botanical photography"
    }
  ],
  "featured": [
    {
      "id": "nature_001",
      "source": "unsplash_nature_bulk",
      "category": "nature",
      "title": "High-Quality Nature Wallpaper 1",
      "description": "High-quality nature wallpaper from Unsplash: a lush green forest filled with lots of trees",
      "width": 1080,
      "height": 1920,
      "photographer": "Unsplash Contributor",
      "tags": ["nature", "wallpaper", "hd", "high resolution", "mobile"],
      "download_url": "https://images.unsplash.com/photo-1649700142623-07fe807400fc?w=1080&h=1920&fit=crop&crop=center&q=85",
      "thumbnail_url": "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/nature/nature_001.jpg",
      "file_size": 712992,
      "filename": "nature_001.jpg"
    }
  ],
  "statistics": {
    "totalCategories": 20,
    "averagePerCategory": 74.5,
    "totalFileSize": 1869230832,
    "generatedAt": "2025-07-15T16:50:05.934492Z"
  }
}
```

### Category Index (`categories/{category}.json`)

All wallpapers in a specific category with complete metadata.

```json
{
  "category": "nature",
  "name": "Nature",
  "description": "Natural landscapes, mountains, forests, oceans, wildlife, and botanical photography",
  "count": 284,
  "lastUpdated": "2025-07-15T16:50:05.935Z", 
  "wallpapers": [
    {
      "id": "nature_001",
      "source": "unsplash_nature_bulk",
      "category": "nature",
      "title": "High-Quality Nature Wallpaper 1",
      "description": "High-quality nature wallpaper from Unsplash: a lush green forest filled with lots of trees",
      "width": 1080,
      "height": 1920,
      "photographer": "Unsplash Contributor",
      "tags": ["nature", "landscape", "mountain", "forest", "ocean"],
      "download_url": "https://images.unsplash.com/photo-1649700142623-07fe807400fc?w=1080&h=1920&fit=crop&crop=center&q=85",
      "original_url": "https://images.unsplash.com/photo-1649700142623-07fe807400fc?fm=jpg&q=60&w=3000",
      "alt_text": "a lush green forest filled with lots of trees",
      "scraped_at": "2025-07-14T22:02:39.746584Z",
      "filename": "nature_001.jpg",
      "thumbnail_url": "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/nature/nature_001.jpg",
      "file_size": 712992,
      "file_modified": "2025-07-14T22:02:39.746202Z"
    }
  ]
}
```

## 💻 Integration Examples

### JavaScript/TypeScript

#### Fetch Random Wallpaper from Category
```javascript
async function getRandomWallpaper(category = 'nature') {
  const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
  const data = await response.json();
  const randomIndex = Math.floor(Math.random() * data.wallpapers.length);
  return data.wallpapers[randomIndex];
}

// Usage
getRandomWallpaper('space').then(wallpaper => {
  console.log('Random wallpaper:', wallpaper.title);
  document.getElementById('wallpaper').src = wallpaper.thumbnail_url;
});
```

#### React Hook
```jsx
import { useState, useEffect } from 'react';

function useWallpapers(category) {
  const [wallpapers, setWallpapers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchWallpapers() {
      try {
        const response = await fetch(
          `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`
        );
        const data = await response.json();
        setWallpapers(data.wallpapers);
      } catch (error) {
        console.error('Error fetching wallpapers:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchWallpapers();
  }, [category]);

  return { wallpapers, loading };
}

// Component usage
function WallpaperGallery() {
  const { wallpapers, loading } = useWallpapers('abstract');
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="grid grid-cols-2 gap-4">
      {wallpapers.map(wallpaper => (
        <img 
          key={wallpaper.id}
          src={wallpaper.thumbnail_url}
          alt={wallpaper.title}
          className="rounded-lg"
        />
      ))}
    </div>
  );
}
```

### Python

#### Fetch and Download Wallpapers
```python
import requests
import random
from pathlib import Path

def get_wallpapers(category='nature'):
    """Fetch wallpapers from a specific category"""
    url = f'https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/{category}.json'
    response = requests.get(url)
    return response.json()['wallpapers']

def download_random_wallpaper(category='nature', save_path='wallpaper.jpg'):
    """Download a random wallpaper from category"""
    wallpapers = get_wallpapers(category)
    wallpaper = random.choice(wallpapers)
    
    # Use GitHub raw URL for better reliability
    image_url = f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/{category}/{wallpaper['filename']}"
    
    response = requests.get(image_url)
    with open(save_path, 'wb') as f:
        f.write(response.content)
    
    print(f"Downloaded: {wallpaper['title']}")
    return wallpaper

# Usage
wallpaper = download_random_wallpaper('neon', 'neon_wallpaper.jpg')
```

#### Search Across Categories
```python
def search_wallpapers(query, categories=['nature', 'abstract', 'space']):
    """Search for wallpapers by title or tags"""
    results = []
    
    for category in categories:
        wallpapers = get_wallpapers(category)
        
        matches = [
            wallpaper for wallpaper in wallpapers
            if query.lower() in wallpaper['title'].lower() or
               any(query.lower() in tag.lower() for tag in wallpaper['tags'])
        ]
        
        results.extend(matches)
    
    return results

# Usage
mountain_wallpapers = search_wallpapers('mountain', ['nature', 'abstract'])
print(f"Found {len(mountain_wallpapers)} mountain wallpapers")
```

### Swift (iOS)

#### Wallpaper Model and Service
```swift
import Foundation

struct Wallpaper: Codable {
    let id: String
    let title: String
    let description: String
    let category: String
    let thumbnailUrl: String
    let downloadUrl: String
    let tags: [String]
    let photographer: String
    let fileSize: Int
    
    enum CodingKeys: String, CodingKey {
        case id, title, description, category, tags, photographer
        case thumbnailUrl = "thumbnail_url"
        case downloadUrl = "download_url"
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

class WallpaperService {
    private let baseURL = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main"
    
    func fetchWallpapers(category: String) async throws -> [Wallpaper] {
        let url = URL(string: "\(baseURL)/categories/\(category).json")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try JSONDecoder().decode(CategoryResponse.self, from: data)
        return response.wallpapers
    }
    
    func downloadWallpaper(_ wallpaper: Wallpaper) async throws -> Data {
        let imageURL = URL(string: "\(baseURL)/wallpapers/\(wallpaper.category)/\(wallpaper.id).jpg")!
        let (data, _) = try await URLSession.shared.data(from: imageURL)
        return data
    }
}

// Usage in SwiftUI
import SwiftUI

struct WallpaperView: View {
    @State private var wallpapers: [Wallpaper] = []
    @State private var isLoading = true
    private let service = WallpaperService()
    
    var body: some View {
        NavigationView {
            if isLoading {
                ProgressView("Loading wallpapers...")
            } else {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2)) {
                    ForEach(wallpapers, id: \.id) { wallpaper in
                        AsyncImage(url: URL(string: wallpaper.thumbnailUrl)) { image in
                            image
                                .resizable()
                                .aspectRatio(9/16, contentMode: .fit)
                                .cornerRadius(12)
                        } placeholder: {
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color.gray.opacity(0.3))
                                .aspectRatio(9/16, contentMode: .fit)
                        }
                    }
                }
                .padding()
            }
        }
        .task {
            await loadWallpapers()
        }
    }
    
    private func loadWallpapers() async {
        do {
            wallpapers = try await service.fetchWallpapers(category: "nature")
            isLoading = false
        } catch {
            print("Error loading wallpapers: \(error)")
        }
    }
}
```

### Kotlin (Android)

#### Data Classes and Service
```kotlin
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*

@Serializable
data class Wallpaper(
    val id: String,
    val title: String,
    val description: String,
    val category: String,
    @SerialName("thumbnail_url") val thumbnailUrl: String,
    @SerialName("download_url") val downloadUrl: String,
    val tags: List<String>,
    val photographer: String,
    @SerialName("file_size") val fileSize: Int
)

@Serializable
data class CategoryResponse(
    val category: String,
    val name: String,
    val description: String,
    val count: Int,
    val wallpapers: List<Wallpaper>
)

class WallpaperService {
    private val client = HttpClient {
        install(ContentNegotiation) {
            json()
        }
    }
    
    private val baseUrl = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main"
    
    suspend fun getWallpapers(category: String): List<Wallpaper> {
        return try {
            val response: CategoryResponse = client.get("$baseUrl/categories/$category.json").body()
            response.wallpapers
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    suspend fun downloadWallpaper(wallpaper: Wallpaper): ByteArray? {
        return try {
            val imageUrl = "$baseUrl/wallpapers/${wallpaper.category}/${wallpaper.id}.jpg"
            client.get(imageUrl).body()
        } catch (e: Exception) {
            null
        }
    }
}

// Jetpack Compose Usage
@Composable
fun WallpaperGrid(category: String = "nature") {
    var wallpapers by remember { mutableStateOf<List<Wallpaper>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    val service = remember { WallpaperService() }
    
    LaunchedEffect(category) {
        wallpapers = service.getWallpapers(category)
        isLoading = false
    }
    
    if (isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            CircularProgressIndicator()
        }
    } else {
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(wallpapers) { wallpaper ->
                AsyncImage(
                    model = wallpaper.thumbnailUrl,
                    contentDescription = wallpaper.title,
                    modifier = Modifier
                        .aspectRatio(9f / 16f)
                        .clip(RoundedCornerShape(12.dp)),
                    contentScale = ContentScale.Crop
                )
            }
        }
    }
}
```

### Flutter/Dart

#### Complete Flutter Integration
```dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class Wallpaper {
  final String id;
  final String title;
  final String description;
  final String category;
  final String thumbnailUrl;
  final String downloadUrl;
  final List<String> tags;
  final String photographer;
  final int fileSize;

  Wallpaper({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    required this.thumbnailUrl,
    required this.downloadUrl,
    required this.tags,
    required this.photographer,
    required this.fileSize,
  });

  factory Wallpaper.fromJson(Map<String, dynamic> json) {
    return Wallpaper(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      category: json['category'],
      thumbnailUrl: json['thumbnail_url'],
      downloadUrl: json['download_url'],
      tags: List<String>.from(json['tags']),
      photographer: json['photographer'],
      fileSize: json['file_size'],
    );
  }
}

class WallpaperService {
  static const String baseUrl = 'https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main';
  
  static Future<List<Wallpaper>> getWallpapers(String category) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/categories/$category.json'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> wallpapersJson = data['wallpapers'];
        return wallpapersJson.map((json) => Wallpaper.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching wallpapers: $e');
      return [];
    }
  }
}

class WallpaperGrid extends StatefulWidget {
  final String category;
  
  const WallpaperGrid({Key? key, this.category = 'nature'}) : super(key: key);

  @override
  _WallpaperGridState createState() => _WallpaperGridState();
}

class _WallpaperGridState extends State<WallpaperGrid> {
  List<Wallpaper> wallpapers = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadWallpapers();
  }

  Future<void> loadWallpapers() async {
    final fetchedWallpapers = await WallpaperService.getWallpapers(widget.category);
    setState(() {
      wallpapers = fetchedWallpapers;
      isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 9 / 16,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: wallpapers.length,
      itemBuilder: (context, index) {
        final wallpaper = wallpapers[index];
        return ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.network(
            wallpaper.thumbnailUrl,
            fit: BoxFit.cover,
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return Container(
                color: Colors.grey[300],
                child: const Center(child: CircularProgressIndicator()),
              );
            },
          ),
        );
      },
    );
  }
}

// Usage in main app
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WallCraft Gallery',
      home: Scaffold(
        appBar: AppBar(title: Text('Nature Wallpapers')),
        body: WallpaperGrid(category: 'nature'),
      ),
    );
  }
}
```

## 🔧 Advanced Features

### Caching Strategy
```javascript
class WallpaperCache {
  constructor(maxAge = 5 * 60 * 1000) { // 5 minutes
    this.cache = new Map();
    this.maxAge = maxAge;
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
const wallpapers = await cache.get('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json');
```

### Progressive Loading
```javascript
function loadWallpaperProgressively(wallpaper) {
  const img = new Image();
  
  // Load thumbnail first
  img.src = wallpaper.thumbnail_url;
  img.onload = () => {
    document.getElementById('wallpaper').src = img.src;
    
    // Load full resolution in background
    const fullImg = new Image();
    fullImg.onload = () => {
      document.getElementById('wallpaper').src = fullImg.src;
    };
    fullImg.src = `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/${wallpaper.category}/${wallpaper.filename}`;
  };
}
```

### Batch Loading Multiple Categories
```javascript
async function loadMultipleCategories(categories) {
  const promises = categories.map(category =>
    fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`)
      .then(response => response.json())
  );
  
  const results = await Promise.all(promises);
  
  return results.reduce((acc, data) => {
    acc[data.category] = data.wallpapers;
    return acc;
  }, {});
}

// Usage
const allWallpapers = await loadMultipleCategories(['nature', 'abstract', 'space']);
```

## 📈 Performance Best Practices

### 1. Use Thumbnails First
- Always load thumbnails initially for fast UX
- Load full resolution only when needed
- Implement progressive loading for smooth transitions

### 2. Implement Caching
- Cache API responses for 5-10 minutes
- Use browser cache for images
- Implement offline fallback with cached data

### 3. Lazy Loading
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});
```

### 4. Error Handling
```javascript
async function fetchWithRetry(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

## 🎯 Use Cases

### Mobile Apps
- **Wallpaper Apps**: Direct integration with categories
- **Meditation Apps**: Nature and minimal categories
- **Gaming Apps**: Gaming and cyberpunk categories
- **Art Apps**: Abstract and art categories

### Web Applications  
- **Portfolio Sites**: Architecture and art categories
- **Landing Pages**: Abstract and minimal for backgrounds
- **Dashboard Apps**: Dark themes for professional look
- **Blog Headers**: Category-specific imagery

### Desktop Applications
- **System Wallpapers**: All categories for variety
- **Screensavers**: Space and nature for ambient display
- **Design Tools**: Abstract patterns for creative work

## 🔄 API Updates

The collection is actively maintained and updated:

- **Automatic Updates**: New wallpapers added regularly
- **Quality Control**: All images pass quality assessment
- **Index Updates**: Statistics updated with each addition
- **No Breaking Changes**: API structure remains stable

## 🛠️ Troubleshooting

### Common Issues

1. **CORS Errors**: Use GitHub raw URLs, not github.com URLs
2. **404 Errors**: Check category name spelling and case
3. **Slow Loading**: Use thumbnails first, implement caching
4. **Rate Limiting**: GitHub raw has high limits, but implement retry logic

### Debug Examples
```javascript
// Check if API is accessible
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json')
  .then(response => {
    console.log('API Status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Total wallpapers:', data.totalWallpapers);
  })
  .catch(error => {
    console.error('API Error:', error);
  });
```

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: This API guide covers all endpoints
- **Examples**: Check the `/docs` folder for more integration examples

---

**Ready to integrate beautiful wallpapers into your app? Start with a simple API call and build from there!**

```javascript
// Your wallpaper journey starts here 🚀
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json')
  .then(response => response.json())
  .then(data => console.log(`${data.totalWallpapers} wallpapers ready to use!`));
```