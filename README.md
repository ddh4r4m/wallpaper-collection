# WallCraft - High-Quality Wallpaper Collection API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Total Wallpapers](https://img.shields.io/badge/Wallpapers-1244-blue)](https://github.com/ddh4r4m/wallpaper-collection)
[![Categories](https://img.shields.io/badge/Categories-20-green)](https://github.com/ddh4r4m/wallpaper-collection)
[![Size](https://img.shields.io/badge/Collection%20Size-1.9GB-orange)](https://github.com/ddh4r4m/wallpaper-collection)

A comprehensive, high-quality wallpaper collection with a RESTful JSON API. Perfect for mobile apps, web applications, and desktop software requiring beautiful wallpapers across multiple categories.

## 🚀 Quick Start

### Get Collection Overview
```bash
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json
```

### Get Category Wallpapers
```bash
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json
```

### Download a Wallpaper
```bash
curl -o wallpaper.jpg "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg"
```

## 📊 Collection Stats

- **Total Wallpapers**: 1,244
- **Categories**: 20
- **Resolution**: 1080×1920 (Mobile Portrait)
- **Format**: JPEG, High Quality
- **Total Size**: 1.9GB
- **Sources**: Unsplash, Wallhaven, Curated Collections

### Category Breakdown

| Category | Count | Percentage | Description |
|----------|--------|------------|-------------|
| **Nature** | 284 | 22.8% | Landscapes, forests, mountains, oceans |
| **Architecture** | 275 | 22.1% | Buildings, structures, urban photography |
| **Abstract** | 217 | 17.4% | Artistic patterns, geometric designs |
| **Space** | 86 | 6.9% | Galaxies, nebulae, cosmic scenes |
| **Gaming** | 76 | 6.1% | Game screenshots, concept art |
| **Dark** | 75 | 6.0% | Dark themes, gothic aesthetics |
| **Anime** | 58 | 4.7% | Anime characters, illustrations |
| **Art** | 47 | 3.8% | Digital art, paintings |
| **Minimal** | 46 | 3.7% | Clean, simple designs |
| **Cyberpunk** | 41 | 3.3% | Neon, futuristic themes |
| **Cars** | 29 | 2.3% | Automotive photography |
| **Technology** | 10 | 0.8% | Tech, circuits, digital themes |

## 🔌 API Endpoints

### Base URL
```
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/
```

### Main Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `index.json` | Master collection index | Complete collection metadata |
| `categories/{category}.json` | Category-specific wallpapers | All wallpapers in category |
| `wallpapers/{category}/{filename}` | High-res wallpaper image | JPEG image file |
| `thumbnails/{category}/{filename}` | Thumbnail (300×533) | JPEG thumbnail |
| `collection_statistics.txt` | Human-readable stats | Text statistics |

### Available Categories
```
abstract, nature, space, minimal, cyberpunk, gaming, anime, movies, music, 
cars, sports, technology, architecture, art, dark, neon, pastel, vintage, 
gradient, seasonal
```

## 📄 API Response Formats

### Master Index (`index.json`)
```json
{
  "version": "2.0.0",
  "lastUpdated": "2025-07-15T15:14:34.094342Z",
  "totalWallpapers": 1244,
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
    "averagePerCategory": 62.2,
    "totalFileSize": 1959966481,
    "generatedAt": "2025-07-15T15:14:34.279800Z"
  }
}
```

### Category Index (`categories/{category}.json`)
```json
{
  "category": "nature",
  "name": "Nature",
  "description": "Natural landscapes, mountains, forests, oceans, wildlife, and botanical photography",
  "count": 284,
  "lastUpdated": "2025-07-15T15:14:34.166220Z",
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
      "original_url": "https://images.unsplash.com/photo-1649700142623-07fe807400fc?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MjQ2fHxuYXR1cmUlMjBsYW5kc2NhcGV8ZW58MHx8MHx8fDA%3D",
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

## 🔧 Advanced Configuration

### Batch Processing Settings
```python
# In batch_processor.py
config = {
    'crawl_limit_per_category': 100,
    'quality_threshold': 6.0,
    'enable_cleanup': True,
    'update_indexes': True
}
```

### Quality Assessment Thresholds
```python
# In review_images.py
thresholds = {
    'auto_approve': 8.0,
    'auto_reject': 4.0,
    'min_resolution': (800, 600),
    'max_file_size': 10 * 1024 * 1024
}
```

## 📈 Performance Metrics

### Expected Processing Rates
- **Crawling**: 50-100 images per minute
- **Quality Assessment**: 200-500 images per minute
- **Image Processing**: 100-200 images per minute
- **Total Pipeline**: 20-50 images per minute (end-to-end)

### Storage Requirements
- **Original Images**: ~500KB average per image
- **Thumbnails**: ~100KB average per image
- **Metadata**: ~2KB average per image
- **Total**: ~600KB per processed wallpaper

## 🎯 Success Metrics

After full implementation:
- ✅ **20+ diverse categories** for maximum user engagement
- ✅ **Multi-source crawling** from 4+ APIs and custom scrapers
- ✅ **AI quality assessment** with 95%+ accuracy
- ✅ **Automated processing** with mobile optimization
- ✅ **Comprehensive metadata** for searchability
- ✅ **Scalable architecture** for thousands of images
- ✅ **Zero-cost hosting** via GitHub Raw Files

## 📞 Support

For issues and feature requests, please check:
1. The comprehensive `CLAUDE.md` documentation
2. Script help: `python scripts/script_name.py --help`
3. Log files for debugging information

## 🔄 Development Workflow

1. **Setup**: Run `python setup.py` to install dependencies
2. **Configure**: Set API keys in `.env` file
3. **Test**: Run individual scripts with small limits
4. **Scale**: Use batch processor for production runs
5. **Deploy**: Commit processed images to GitHub
6. **Monitor**: Check logs and statistics for issues

This system provides a professional-grade wallpaper collection with automated quality control, diverse content sources, and comprehensive processing pipeline - perfect for mobile app integration!