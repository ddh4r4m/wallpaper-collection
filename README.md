# WallCraft - High-Quality Wallpaper Collection API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Total Wallpapers](https://img.shields.io/badge/Wallpapers-2387-blue)](https://github.com/ddh4r4m/wallpaper-collection)
[![Categories](https://img.shields.io/badge/Categories-19-green)](https://github.com/ddh4r4m/wallpaper-collection)
[![Size](https://img.shields.io/badge/Collection%20Size-1.0GB-orange)](https://github.com/ddh4r4m/wallpaper-collection)

A comprehensive, high-quality wallpaper collection with a RESTful JSON API. Perfect for mobile apps, web applications, and desktop software requiring beautiful wallpapers across multiple categories.

## 🚀 Quick Start

### Get Collection Overview
```bash
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/stats.json
```

### Get Category Wallpapers
```bash
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature.json
```

### Download a Wallpaper
```bash
curl -o wallpaper.jpg "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/nature/001.jpg"
```

## 📖 Complete API Documentation

👉 **[View Complete API Documentation](./API.md)** - Comprehensive integration guide with examples for all platforms

The API.md file includes:
- **Complete endpoint documentation** with response formats
- **Integration examples** for JavaScript, Python, Swift, Kotlin, Flutter  
- **Performance best practices** and caching strategies
- **Error handling** and troubleshooting guide
- **Ready-to-use code** for mobile and web apps

## 📊 Collection Stats

- **Total Wallpapers**: 2,387
- **Categories**: 19
- **Resolution**: Up to 1080×1920 (Mobile Optimized)
- **Format**: JPEG, High Quality (85% compression)
- **Total Size**: 1.0GB
- **Sources**: Unsplash, Civitai, Reddit, Curated Collections

### Category Breakdown

| Category | Count | Percentage | Description |
|----------|--------|------------|-------------|
| **Nature** | 304 | 12.7% | Landscapes, wildlife, forests, mountains |
| **Architecture** | 275 | 11.5% | Buildings, structures, urban photography |
| **Abstract** | 257 | 10.8% | Artistic patterns, geometric designs |
| **4K** | 200 | 8.4% | Ultra high-definition wallpapers |
| **Anime** | 133 | 5.6% | Anime characters, manga art |
| **Space** | 122 | 5.1% | Galaxies, nebulae, cosmic scenes |
| **Vintage** | 99 | 4.1% | Retro designs, nostalgic themes |
| **Art** | 90 | 3.8% | Digital art, paintings, illustrations |
| **Seasonal** | 90 | 3.8% | Holiday themes, seasonal changes |
| **Dark** | 90 | 3.8% | Dark themes, gothic aesthetics |
| **Neon** | 88 | 3.7% | Neon lighting, synthwave aesthetics |
| **Cyberpunk** | 88 | 3.7% | Neon cities, futuristic themes |
| **Gaming** | 84 | 3.5% | Video game characters, scenes |
| **Cars** | 84 | 3.5% | Automotive photography, sports cars |
| **Animals** | 84 | 3.5% | Wildlife photography, pets |
| **AI** | 83 | 3.5% | AI-generated wallpapers |
| **Technology** | 83 | 3.5% | Gadgets, circuits, digital interfaces |
| **Pastel** | 69 | 2.9% | Soft colors, gentle aesthetics |
| **Minimal** | 64 | 2.7% | Clean, simple designs |

## 🔌 API Endpoints

### Base URL
```
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/
```

### Main Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `all.json` | All wallpapers with metadata | Complete collection |
| `categories.json` | Category list and counts | All categories overview |
| `{category}.json` | Category-specific wallpapers | All wallpapers in category |
| `featured.json` | Featured wallpapers (latest 20) | Curated selection |
| `stats.json` | Complete collection statistics | Detailed analytics |
| `{category}/pages/{page}.json` | Paginated category results | 15 wallpapers per page |

### Image Endpoints
| Endpoint | Description | Response |
|----------|-------------|----------|
| `wallpapers/{category}/{id}.jpg` | High-res wallpaper (up to 1080×1920) | JPEG image |
| `thumbnails/{category}/{id}.jpg` | Thumbnail (400×600) | JPEG thumbnail |

### Available Categories
```
4k, abstract, ai, animals, anime, architecture, art, cars, cyberpunk, 
dark, gaming, minimal, nature, neon, pastel, seasonal, space, 
technology, vintage
```

## 📄 API Response Formats

### Statistics Response (`stats.json`)
```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-19T12:26:57.111378"
  },
  "data": {
    "total_wallpapers": 2387,
    "total_categories": 19,
    "categories": {
      "nature": {
        "name": "Nature",
        "count": 304,
        "description": "Landscapes, wildlife, forests, mountains, and natural scenes"
      },
      "ai": {
        "name": "AI",
        "count": 83,
        "description": "AI-generated wallpapers from Stable Diffusion, Midjourney, and other AI models"
      }
    },
    "file_stats": {
      "total_size_mb": 1018.95,
      "average_file_size_kb": 437.12,
      "total_files": 2387
    }
  }
}
```

### Category Response (`{category}.json`)
```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-19T12:26:57.111378",
    "category": "nature",
    "total_count": 304
  },
  "data": [
    {
      "id": "nature_001",
      "category": "nature",
      "title": "Nature Wallpaper 001",
      "tags": ["nature", "hd", "mobile", "wallpaper"],
      "urls": {
        "raw": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/nature/001.jpg",
        "thumb": "https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/nature/001.jpg"
      },
      "metadata": {
        "dimensions": {
          "width": 1080,
          "height": 1920
        },
        "file_size": 245760,
        "format": "JPEG",
        "added_at": "2025-07-16T21:34:41.205709",
        "hash": "7c3a0596157f9236646aedebd3123f3e"
      }
    }
  ]
}
```

## 🔧 Modern API Features

### Pagination Support
```bash
# Get paginated results (15 items per page)
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/all/pages/1.json
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature/pages/1.json
```

### Bulletproof URL System
- **Computed URLs**: Never stored, always calculated from file structure
- **Impossible to be wrong**: URLs generated from actual file paths
- **Sequential numbering**: Consistent 001.jpg, 002.jpg format
- **GitHub LFS**: Large files handled efficiently

## 📈 Performance Characteristics

### API Response Times
- **JSON APIs**: < 100ms (pre-generated static files)
- **Image Loading**: < 500ms (GitHub CDN)
- **Pagination**: 92% smaller responses (12KB vs 141KB)
- **Cache Headers**: Long-term browser caching

### File Specifications
- **Wallpapers**: Up to 1080×1920, <500KB average
- **Thumbnails**: 400×600, <100KB average
- **Metadata**: <2KB per wallpaper
- **Total Collection**: ~1GB (2,387 wallpapers)

## 🎯 Production Features

- ✅ **2,387 wallpapers** across 19 diverse categories
- ✅ **Multiple sources**: Unsplash, Civitai, Reddit communities
- ✅ **AI-generated content**: 83 AI wallpapers from Stable Diffusion
- ✅ **Mobile optimized**: Perfect for portrait displays
- ✅ **Rich metadata**: Complete information for apps
- ✅ **Bulletproof URLs**: Self-healing API system
- ✅ **Pagination support**: Efficient data loading
- ✅ **Zero-cost hosting**: GitHub Raw Files + LFS

## 📞 Support

For issues and feature requests, please check:
1. The comprehensive `CLAUDE.md` documentation
2. Script help: `python scripts/script_name.py --help`
3. Log files for debugging information

## 🔄 Usage Examples

### Mobile App Integration
```javascript
// Get all wallpapers
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json')
  .then(response => response.json())
  .then(data => console.log(data.meta.total_count)); // 2387

// Get nature wallpapers
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature.json')
  .then(response => response.json())
  .then(data => data.data.forEach(wallpaper => {
    console.log(wallpaper.urls.raw); // Direct image URL
  }));
```

This system provides a professional-grade wallpaper collection with automated quality control, diverse content sources, and comprehensive processing pipeline - perfect for mobile app integration!