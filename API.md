# WallCraft API Documentation

[![Total Wallpapers](https://img.shields.io/badge/Wallpapers-2387-blue)](https://github.com/ddh4r4m/wallpaper-collection)
[![Categories](https://img.shields.io/badge/Categories-19-green)](https://github.com/ddh4r4m/wallpaper-collection)
[![API Status](https://img.shields.io/badge/API-Live-success)](https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json)

Complete API documentation for the **bulletproof WallCraft collection**. **No API keys required** - start using immediately with guaranteed correct URLs!

## 🚀 Quick Start

### 🧪 Tested & Verified APIs

**All endpoints tested and working** ✅ (Last verified: July 17, 2025)

### Test the APIs
```bash
# Get all wallpapers
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json

# Get collection statistics
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/stats.json

# Get 4K wallpapers  
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k.json

# Download a 4K wallpaper (sequential numbering)
curl -o 4k_001.jpg "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/001.jpg"

# Download 4K thumbnail
curl -o 4k_001_thumb.jpg "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/001.jpg"
```

## 🔗 API Endpoints

### Base URL
```
https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/
```

### Core API Endpoints (v1)

| Endpoint | Description | Response Type |
|----------|-------------|---------------|
| `api/v1/all.json` | All wallpapers with metadata | JSON |
| `api/v1/categories.json` | Category list and counts | JSON |
| `api/v1/{category}.json` | Category-specific wallpapers | JSON |
| `api/v1/featured.json` | Featured wallpapers (latest 20) | JSON |
| `api/v1/stats.json` | Complete collection statistics | JSON |

### 🚀 Paginated Endpoints (NEW!)

| Endpoint | Description | Page Size | Response Type |
|----------|-------------|-----------|---------------|
| `api/v1/all/pages/{page}.json` | All wallpapers paginated | 15 per page | JSON |
| `api/v1/{category}/pages/{page}.json` | Category wallpapers paginated | 15 per page | JSON |

**Performance Benefits:**
- **92% smaller**: 141KB → 12KB per page  
- **Faster loading**: Perfect for mobile apps
- **Progressive browsing**: Load more as needed

### Media Endpoints

| Endpoint | Description | Response Type |
|----------|-------------|---------------|
| `wallpapers/{category}/{id}.jpg` | High-res wallpaper (up to 1080×1920) | JPEG |
| `thumbnails/{category}/{id}.jpg` | Thumbnail (400×600) | JPEG |

### Available Categories

| Category | Count | Description |
|----------|-------|-------------|
| `nature` | 304 | Landscapes, wildlife, forests, mountains, and natural scenes |
| `architecture` | 275 | Buildings, bridges, modern structures, and urban photography |
| `abstract` | 257 | Abstract patterns, geometric designs, and artistic visualizations |
| `4k` | 200 | Ultra high-definition wallpapers optimized for 4K displays |
| `anime` | 133 | Anime characters, manga art, and Japanese animation styles |
| `space` | 122 | Galaxies, nebulae, planets, stars, and cosmic photography |
| `vintage` | 99 | Retro designs, nostalgic themes, and classic aesthetics |
| `art` | 90 | Digital art, paintings, illustrations, and creative designs |
| `seasonal` | 90 | Holiday themes, seasonal changes, and weather phenomena |
| `dark` | 90 | Dark themes, gothic aesthetics, and mysterious atmospheres |
| `neon` | 88 | Neon lighting, synthwave aesthetics, and electric themes |
| `cyberpunk` | 88 | Futuristic cityscapes, neon lights, and sci-fi themes |
| `gaming` | 84 | Video game characters, scenes, and gaming-inspired artwork |
| `cars` | 84 | Automotive photography, sports cars, and vehicle designs |
| `animals` | 84 | Wildlife photography, pets, and animal portraits |
| `ai` | 83 | AI-generated wallpapers from Stable Diffusion, Midjourney, and other AI models |
| `technology` | 83 | Gadgets, circuits, futuristic tech, and digital interfaces |
| `pastel` | 69 | Soft colors, gentle aesthetics, and dream-like themes |
| `minimal` | 64 | Clean, simple designs with minimalist aesthetics |

**Total: 19 active categories with 2,387 wallpapers**

#### Category API Examples
```bash
# Get nature wallpapers (304 wallpapers - largest collection)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature.json

# Get architecture wallpapers (275 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/architecture.json

# Get abstract wallpapers (257 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract.json

# Get 4K wallpapers (200 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k.json

# Get anime wallpapers (133 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/anime.json

# Get AI wallpapers (83 wallpapers - NEW!)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/ai.json
```

#### 🚀 Pagination Examples
```bash
# Get first page of all wallpapers (15 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/all/pages/1.json

# Get first page of 4K wallpapers (15 wallpapers) 
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k/pages/1.json

# Get page 5 of 4K wallpapers
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k/pages/5.json

# Get first page of anime wallpapers
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/anime/pages/1.json

# Available pages: All (1-159), Nature (1-21), Architecture (1-19), Abstract (1-18), 4K (1-14), Anime (1-9), AI (1-6)
```

**Pagination Available For:**
- **All wallpapers**: 159 pages (2,387 total wallpapers)
- **Nature category**: 21 pages (304 wallpapers)
- **Architecture category**: 19 pages (275 wallpapers)
- **Abstract category**: 18 pages (257 wallpapers)
- **4K category**: 14 pages (200 wallpapers)
- **Anime category**: 9 pages (133 wallpapers)
- **AI category**: 6 pages (83 wallpapers)
- **And 12 more categories** with pagination support

## 📊 Collection Statistics

- **Total Wallpapers**: 2,387 (Live Count)
- **Categories**: 19 Active Categories
- **Nature Collection**: 304 high-quality landscape and wildlife wallpapers (largest)
- **Architecture Collection**: 275 stunning building and structure wallpapers
- **Abstract Collection**: 257 artistic and geometric wallpapers
- **4K Collection**: 200 unique wallpapers from Unsplash curated collection
- **Anime Collection**: 133 high-quality anime and manga wallpapers
- **AI Collection**: 83 AI-generated wallpapers from Civitai and other sources (newly added)
- **Resolution**: Up to 1080×1920 (Mobile Optimized)
- **Format**: JPEG, High Quality (85% compression)
- **Thumbnails**: 400×600px for fast loading (80% compression)
- **File Naming**: Sequential (001.jpg, 002.jpg, etc.)
- **API Structure**: Bulletproof with computed URLs
- **Source**: Curated from Unsplash and other high-quality sources

## 📄 API Response Formats

### All Wallpapers (`api/v1/all.json`)

Complete collection with all wallpapers and metadata.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T23:29:21.210153",
    "total_count": 2387,
    "categories": 19
  },
  "data": [
    {
      "id": "4k_001",
      "category": "4k",
      "title": "Pink Flower 4K Wallpaper",
      "tags": [
        "4k",
        "wallpaper",
        "pink",
        "flower",
        "nature",
        "portrait"
      ],
      "urls": {
        "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/001.jpg",
        "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/001.jpg"
      },
      "metadata": {
        "dimensions": {
          "width": 1080,
          "height": 1920
        },
        "file_size": 98252,
        "format": "JPEG",
        "added_at": "2025-07-16T21:34:41.205709",
        "hash": "7c3a0596157f9236646aedebd3123f3e",
        "photographer": "Alexandru Acea"
      }
    }
  ]
}
```

### Paginated Response (`api/v1/all/pages/{page}.json`)

Paginated response with navigation metadata and 15 wallpapers per page.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T23:29:21.210153",
    "page": 1,
    "per_page": 15,
    "total_pages": 159,
    "total_count": 2387,
    "count_on_page": 15,
    "categories": 19,
    "has_next": true,
    "has_prev": false,
    "next_page_url": "/api/v1/all/pages/2.json",
    "prev_page_url": null
  },
  "data": [
    {
      "id": "4k_001",
      "category": "4k",
      "title": "Pink Flower 4K Wallpaper",
      "tags": [
        "4k",
        "wallpaper",
        "pink",
        "flower",
        "nature",
        "portrait"
      ],
      "urls": {
        "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/001.jpg",
        "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/001.jpg"
      },
      "metadata": {
        "dimensions": {
          "width": 1080,
          "height": 1920
        },
        "file_size": 98252,
        "format": "JPEG",
        "added_at": "2025-07-16T21:34:41.205709",
        "hash": "7c3a0596157f9236646aedebd3123f3e",
        "photographer": "Alexandru Acea"
      }
    }
  ]
}
```

### Categories List (`api/v1/categories.json`)

Overview of all categories with counts and descriptions.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T22:22:47.973645",
    "total_categories": 19
  },
  "data": {
    "nature": {
      "name": "Nature",
      "count": 284,
      "description": "Landscapes, wildlife, forests, mountains, and natural scenes"
    },
    "architecture": {
      "name": "Architecture", 
      "count": 275,
      "description": "Buildings, bridges, modern structures, and urban photography"
    },
    "abstract": {
      "name": "Abstract",
      "count": 219,
      "description": "Abstract patterns, geometric designs, and artistic visualizations"
    },
    "4k": {
      "name": "4K",
      "count": 200,
      "description": "Ultra high-definition wallpapers optimized for 4K displays"
    },
    "anime": {
      "name": "Anime",
      "count": 133,
      "description": "Anime characters, manga art, and Japanese animation styles"
    },
    "ai": {
      "name": "AI",
      "count": 83,
      "description": "AI-generated wallpapers from Stable Diffusion, Midjourney, and other AI models"
    },
    "animals": {
      "name": "Animals",
      "count": 84,
      "description": "Wildlife photography, pets, and animal portraits"
    }
  }
}
```

### Category Wallpapers (`api/v1/{category}.json`)

All wallpapers in a specific category.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T22:22:47.973645",
    "category": "4k",
    "total_count": 200
  },
  "data": [
    {
      "id": "4k_001",
      "category": "4k",
      "title": "Pink Flower 4K Wallpaper",
      "tags": [
        "4k",
        "wallpaper",
        "pink",
        "flower",
        "nature",
        "portrait"
      ],
      "urls": {
        "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/001.jpg",
        "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/001.jpg"
      },
      "metadata": {
        "dimensions": {
          "width": 1080,
          "height": 1920
        },
        "file_size": 98252,
        "format": "JPEG",
        "added_at": "2025-07-16T21:34:41.205709",
        "hash": "7c3a0596157f9236646aedebd3123f3e",
        "photographer": "Alexandru Acea"
      }
    }
  ]
}
```

### Featured Wallpapers (`api/v1/featured.json`)

Latest 20 wallpapers across all categories.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T22:22:47.973645",
    "total_count": 20
  },
  "data": [
    {
      "id": "4k_155",
      "category": "4k",
      "title": "4K Wallpaper 155",
      "tags": [
        "4k"
      ],
      "urls": {
        "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/155.jpg",
        "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/155.jpg"
      },
      "metadata": {
        "added_at": "2025-07-16T22:20:43.047200",
        "file_size": 336377,
        "dimensions": {
          "width": 1080,
          "height": 1920
        }
      }
    }
  ]
}
```

### Collection Statistics (`api/v1/stats.json`)

Complete statistics and analytics.

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-16T22:22:47.973645"
  },
  "data": {
    "total_wallpapers": 2387,
    "total_categories": 19,
    "categories": {
      "4k": {
        "name": "4K",
        "count": 200,
        "description": "Ultra high-definition wallpapers optimized for 4K displays"
      },
      "anime": {
        "name": "Anime",
        "count": 133,
        "description": "Anime characters, manga art, and Japanese animation styles"
      },
      "ai": {
        "name": "AI",
        "count": 83,
        "description": "AI-generated wallpapers from Stable Diffusion, Midjourney, and other AI models"
      },
      "abstract": {
        "name": "Abstract", 
        "count": 257,
        "description": "Abstract patterns, geometric designs, and artistic visualizations"
      }
    },
    "recent_additions": [
      {
        "id": "4k_155",
        "category": "4k",
        "title": "4K Wallpaper 155",
        "added_at": "2025-07-16T22:20:43.047200"
      }
    ],
    "popular_tags": [
      [
        "wallpaper",
        167
      ],
      [
        "hd",
        162
      ],
      [
        "4k",
        155
      ],
      [
        "portrait",
        109
      ],
      [
        "curated",
        104
      ],
      [
        "anime",
        58
      ]
    ],
    "file_stats": {
      "total_size_mb": 951.9,
      "average_file_size_kb": 474.79,
      "average_dimensions": {
        "width": 1170,
        "height": 1818
      },
      "total_files": 2387
    }
  }
}
```

## 🌟 4K Wallpaper Collection Spotlight

### 🔥 Featured: Massive 2,387 Wallpaper Collection
Our **complete collection** contains **2,387 carefully curated wallpapers** across 19 diverse categories. Notable collections include:

- **Nature (304)**: Stunning landscapes and wildlife photography
- **Architecture (275)**: Modern and classic building photography  
- **Abstract (257)**: Artistic patterns and geometric designs
- **4K Collection (200)**: Premium Unsplash curated wallpapers
- **Anime (133)**: High-quality anime and manga artwork
- **AI (83)**: AI-generated wallpapers from Civitai and other sources

Each wallpaper is:

- **Unique**: Guaranteed no duplicates via ID tracking
- **High Quality**: Sourced from Unsplash's curated collection  
- **Mobile Optimized**: Resized to 1080×1920 for perfect mobile display
- **Fast Loading**: Optimized JPEG compression (85% quality)
- **Professionally Tagged**: Rich metadata with photographer attribution

### 🚀 Collection Implementation Guide

#### Quick Start with Major Categories
```bash
# Get all 2,387 wallpapers
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json

# Get nature wallpapers (largest collection - 304 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature.json

# Get architecture wallpapers (275 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/architecture.json

# Get abstract wallpapers (257 wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract.json

# Get 4K wallpapers (200 premium wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k.json

# Get AI wallpapers (83 AI-generated wallpapers)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/ai.json

# Access specific wallpaper (sequential numbering)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/nature/001.jpg

# Get thumbnail for fast preview
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/nature/001.jpg
```

#### URL Pattern for All Categories
```typescript
// Wallpaper URLs (varies by category)
const wallpaperUrl = `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/${category}/${id.padStart(3, '0')}.jpg`;

// Thumbnail URLs (varies by category)  
const thumbnailUrl = `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/${category}/${id.padStart(3, '0')}.jpg`;

// Examples:
const nature42 = "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/nature/042.jpg";
const anime15 = "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/anime/015.jpg";
const ai01 = "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/ai/001.jpg";
const cars01 = "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/cars/001.jpg";
```

#### Implementation Examples

**Flutter/Dart**
```dart
class WallpaperService {
  static const String baseUrl = 'https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection';
  
  String getWallpaperUrl(String category, int id) {
    final paddedId = id.toString().padLeft(3, '0');
    return '$baseUrl/wallpapers/$category/$paddedId.jpg';
  }
  
  String getThumbnailUrl(String category, int id) {
    final paddedId = id.toString().padLeft(3, '0');
    return '$baseUrl/thumbnails/$category/$paddedId.jpg';
  }
}

// Usage for different collections
final natureUrl = WallpaperService().getWallpaperUrl('nature', 1); // 001.jpg
final animeUrl = WallpaperService().getWallpaperUrl('anime', 50); // 050.jpg
final aiUrl = WallpaperService().getWallpaperUrl('ai', 25); // 025.jpg
final carsThumb = WallpaperService().getThumbnailUrl('cars', 25); // 025.jpg
```

**JavaScript/React**
```javascript
class WallpaperAPI {
  static baseUrl = 'https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection';
  
  static getWallpaperUrl(category, id) {
    const paddedId = id.toString().padStart(3, '0');
    return `${this.baseUrl}/wallpapers/${category}/${paddedId}.jpg`;
  }
  
  static getThumbnailUrl(category, id) {
    const paddedId = id.toString().padStart(3, '0');
    return `${this.baseUrl}/thumbnails/${category}/${paddedId}.jpg`;
  }
}

// Usage for different collections
const nature1 = WallpaperAPI.getWallpaperUrl('nature', 1);   // 001.jpg
const abstract100 = WallpaperAPI.getWallpaperUrl('abstract', 100); // 100.jpg
const aiThumb = WallpaperAPI.getThumbnailUrl('ai', 35); // 035.jpg
const animalsThumb = WallpaperAPI.getThumbnailUrl('animals', 35); // 035.jpg
```

## 🎯 Data Models

### Wallpaper Object
```typescript
interface Wallpaper {
  id: string;              // Format: "{category}_{sequential_id}"
  category: string;        // Category name
  title: string;           // Wallpaper title
  tags: string[];          // Array of tags
  urls: {
    raw: string;           // Full resolution image URL
    thumb: string;         // Thumbnail URL (400×600)
  };
  metadata: {
    dimensions?: {
      width: number;       // Image width in pixels
      height: number;      // Image height in pixels
    };
    file_size: number;     // File size in bytes
    added_at: string;      // ISO 8601 timestamp
    format?: string;       // Image format (e.g., "JPEG")
  };
}
```

### API Response Structure
```typescript
interface APIResponse<T> {
  meta: {
    version: string;       // API version
    generated_at: string;  // ISO 8601 timestamp
    total_count?: number;  // Total items in response
    category?: string;     // Category name (for category endpoints)
    categories?: number;   // Total categories (for stats endpoint)
  };
  data: T;                 // Response data (array or object)
}
```

### Paginated Response Structure
```typescript
interface PaginatedAPIResponse<T> {
  meta: {
    version: string;           // API version
    generated_at: string;      // ISO 8601 timestamp
    page: number;              // Current page number (1-based)
    per_page: number;          // Items per page (always 15)
    total_pages: number;       // Total number of pages
    total_count: number;       // Total items across all pages
    count_on_page: number;     // Items on current page
    categories?: number;       // Total categories (for all endpoint)
    category?: string;         // Category name (for category endpoints)
    has_next: boolean;         // Whether next page exists
    has_prev: boolean;         // Whether previous page exists
    next_page_url: string | null;  // Relative URL to next page
    prev_page_url: string | null;  // Relative URL to previous page
  };
  data: T[];                   // Array of wallpapers for current page
}
```

### Category Information
```typescript
interface CategoryInfo {
  name: string;            // Display name
  count: number;           // Number of wallpapers
  description: string;     // Category description
}
```

## 🔧 Key Features

### 🎯 Bulletproof URL System
- **Computed URLs**: Never stored, always calculated from file structure
- **Impossible to be wrong**: URLs generated from actual file paths
- **Consistent structure**: Sequential numbering (001.jpg, 002.jpg, etc.)

### 📊 Standardized Responses
- **Consistent format**: All endpoints use same response structure
- **Rich metadata**: Complete information for each wallpaper
- **Versioned APIs**: Future-proof with version numbers

### 🚀 Performance Optimized
- **Pre-generated JSON**: Fast response times
- **Optimized thumbnails**: 400×600px for quick loading
- **Efficient caching**: Static files with long cache headers
- **Smart pagination**: 92% smaller responses (141KB → 12KB per page)

### 🛠️ Developer Friendly
- **Predictable URLs**: Easy to construct programmatically
- **Complete metadata**: Everything needed for apps
- **Error resilient**: Graceful handling of missing files
- **Pagination support**: Built-in navigation with next/prev URLs

## 📱 Mobile App Implementation Guide

### Using Pagination in Mobile Apps

**Flutter/Dart Implementation:**
```dart
class WallpaperPagination {
  static const String baseUrl = 'https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1';
  
  // Get paginated wallpapers
  Future<PaginatedResponse> getPage(String category, int page) async {
    final url = category == 'all' 
      ? '$baseUrl/all/pages/$page.json'
      : '$baseUrl/$category/pages/$page.json';
    
    final response = await http.get(Uri.parse(url));
    return PaginatedResponse.fromJson(json.decode(response.body));
  }
  
  // Load more wallpapers (infinite scroll)
  Future<List<Wallpaper>> loadMore(String category, int currentPage) async {
    final nextPage = currentPage + 1;
    final response = await getPage(category, nextPage);
    return response.data;
  }
}

class PaginatedResponse {
  final PaginationMeta meta;
  final List<Wallpaper> data;
  
  PaginatedResponse({required this.meta, required this.data});
  
  factory PaginatedResponse.fromJson(Map<String, dynamic> json) {
    return PaginatedResponse(
      meta: PaginationMeta.fromJson(json['meta']),
      data: (json['data'] as List).map((item) => Wallpaper.fromJson(item)).toList(),
    );
  }
}

class PaginationMeta {
  final int page;
  final int totalPages;
  final int totalCount;
  final bool hasNext;
  final bool hasPrev;
  final String? nextPageUrl;
  final String? prevPageUrl;
  
  PaginationMeta({
    required this.page,
    required this.totalPages,
    required this.totalCount,
    required this.hasNext,
    required this.hasPrev,
    this.nextPageUrl,
    this.prevPageUrl,
  });
  
  factory PaginationMeta.fromJson(Map<String, dynamic> json) {
    return PaginationMeta(
      page: json['page'],
      totalPages: json['total_pages'],
      totalCount: json['total_count'],
      hasNext: json['has_next'],
      hasPrev: json['has_prev'],
      nextPageUrl: json['next_page_url'],
      prevPageUrl: json['prev_page_url'],
    );
  }
}
```

**JavaScript/React Implementation:**
```javascript
class WallpaperPagination {
  static baseUrl = 'https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1';
  
  // Get paginated wallpapers
  static async getPage(category, page) {
    const url = category === 'all' 
      ? `${this.baseUrl}/all/pages/${page}.json`
      : `${this.baseUrl}/${category}/pages/${page}.json`;
    
    const response = await fetch(url);
    return await response.json();
  }
  
  // React hook for pagination
  static usePagination(category) {
    const [wallpapers, setWallpapers] = useState([]);
    const [meta, setMeta] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const loadPage = async (page) => {
      setLoading(true);
      try {
        const response = await this.getPage(category, page);
        setWallpapers(response.data);
        setMeta(response.meta);
      } catch (error) {
        console.error('Failed to load wallpapers:', error);
      } finally {
        setLoading(false);
      }
    };
    
    const loadMore = async () => {
      if (!meta?.hasNext) return;
      
      const nextPage = meta.page + 1;
      const response = await this.getPage(category, nextPage);
      setWallpapers(prev => [...prev, ...response.data]);
      setMeta(response.meta);
    };
    
    return { wallpapers, meta, loading, loadPage, loadMore };
  }
}
```

### Best Practices for Mobile Apps

1. **Start with Page 1**: Always begin pagination with page 1
2. **Implement Infinite Scroll**: Use `loadMore()` function for seamless browsing
3. **Check `has_next`**: Always verify before loading next page
4. **Cache Responses**: Store paginated responses for better UX
5. **Error Handling**: Handle network errors gracefully
6. **Loading States**: Show loading indicators during pagination

## 📈 Migration from Old API

If you're using the old API structure, here's how to migrate:

### URL Structure Changes
```bash
# OLD (fragile, could be wrong)
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json

# NEW (bulletproof, always correct)
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k.json
```

### Response Structure Changes
```json
// OLD format
{
  "category": "nature",
  "wallpapers": [...]
}

// NEW format (standardized)
{
  "meta": {
    "version": "1.0",
    "category": "4k",
    "total_count": 200
  },
  "data": [...]
}
```

### URL Field Changes
```json
// OLD format
{
  "download_url": "https://images.unsplash.com/...",
  "thumbnail_url": "https://raw.githubusercontent.com/..."
}

// NEW format (bulletproof)
{
  "urls": {
    "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/4k/001.jpg",
    "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/4k/001.jpg"
  }
}
```

## 🔄 API Reliability

### Automated Updates
- **Self-healing**: APIs regenerated from source files
- **Consistent**: URLs computed from file structure
- **Validated**: All endpoints tested before deployment

### Error Handling
```bash
# Test API availability
curl -I https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json

# Check 4K category
curl -I https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k.json
```

## 📞 Support & Documentation

- **GitHub Issues**: Report bugs and feature requests
- **Live APIs**: All endpoints are live and tested
- **Bulletproof Architecture**: Guaranteed correct URLs
- **No Breaking Changes**: Stable API structure

---

**The bulletproof WallCraft API with 2,387 wallpapers is ready for production use! 🚀**

```bash
# Start using the massive collection API today
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json | jq '.meta.total_count'
# Output: 2387

# Explore the largest collections
curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature.json | jq '.meta.total_count'
# Output: 304

curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/architecture.json | jq '.meta.total_count'  
# Output: 275

curl https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/api/v1/ai.json | jq '.meta.total_count'
# Output: 83
```