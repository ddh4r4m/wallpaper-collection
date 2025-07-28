# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a comprehensive wallpaper repository serving high-quality wallpapers via GitHub Raw Files and Media URLs. It provides a structured collection of 2,737+ wallpapers across 22 categories, with complete JSON APIs and pagination for mobile application consumption. Features automated Pinterest scraping, AI quality assessment, and full API generation pipeline.

## Essential Development Commands

### Repository Management
```bash
# **PRIMARY SCRAPING TOOL** - Interactive Pinterest scraper with full automation
python scripts/pinterest_api_scraper.py
# Prompts for: Pinterest URL, category, quantity
# Automatically: scrapes, downloads, processes, generates APIs & pagination

# Alternative: Run API generation after manual image additions
python tools/build_api.py
# Generates complete API structure and pagination for all categories

# Legacy crawl commands (deprecated - use pinterest_api_scraper.py instead)
python scripts/crawl_images.py --category nature --source unsplash --limit 100
python scripts/review_images.py --input crawl_cache/ --output review_system/
python scripts/process_approved.py --input review_system/approved/ --category nature
```

### Image Processing
```bash
# Batch resize images for mobile optimization
python scripts/optimize_images.py --target-width 1080 --target-height 1920 --quality 85

# Generate thumbnails for all wallpapers
python scripts/generate_thumbnails.py --size 400x600 --quality 80

# Validate image formats and sizes
python scripts/validate_images.py

# AI image quality assessment
python scripts/review_images.py --input crawl_cache/ --metrics brisque,sharpness,content

# Process manually reviewed images
python scripts/process_approved.py --input review_system/manual_review/approved/ --category gaming
```

### Index Generation
```bash
# Update master index.json
python scripts/generate_index.py --update-master

# Generate category-specific indexes
python scripts/generate_index.py --category abstract

# Validate JSON structure
python scripts/validate_json.py
```

## Repository Structure

### CRITICAL: WallCraft API Structure (ALWAYS USE THIS STRUCTURE)
```
wallpaper-collection/
├── README.md                     # Repository documentation
├── API.md                        # WallCraft API documentation
├── requirements.txt              # Python dependencies
├── collection/                   # **MAIN WALLPAPER COLLECTION** (ALWAYS USE THIS)
│   ├── api/
│   │   └── v1/                   # API endpoints for mobile app
│   │       ├── all.json          # All wallpapers across categories
│   │       ├── abstract.json     # Abstract category endpoint
│   │       ├── nature.json       # Nature category endpoint
│   │       ├── gradient.json     # Gradient category endpoint
│   │       └── ... (category endpoints)
│   ├── wallpapers/               # **PRIMARY WALLPAPER STORAGE**
│   │   ├── abstract/             # Sequential naming: 001.jpg, 002.jpg, etc.
│   │   ├── nature/
│   │   ├── gradient/
│   │   └── ... (20+ category folders)
│   └── thumbnails/               # **PRIMARY THUMBNAIL STORAGE**
│       ├── abstract/             # Matching sequential naming
│       ├── nature/
│       ├── gradient/
│       └── ... (matching structure)
├── wallpapers/                   # **DEPRECATED - DO NOT USE**
│   └── ... (old structure)
├── thumbnails/                   # **DEPRECATED - DO NOT USE**
│   └── ... (old structure)
├── categories/                   # **DEPRECATED - DO NOT USE**
│   └── ... (old JSON structure)
├── review_system/                # AI quality assessment (temp storage)
│   ├── approved/                 # Auto-approved images
│   ├── rejected/                 # Auto-rejected images
│   └── manual_review/            # Requires human review
├── crawl_cache/                  # Temporary download cache
│   ├── unsplash/
│   ├── pexels/
│   ├── pinterest/
│   └── wallhaven/
└── scripts/                      # Management automation
    ├── crawl_images.py          # Multi-source image crawler
    ├── pinterest_scraper.py     # Pinterest-specific scraper
    ├── review_images.py         # AI quality assessment
    ├── process_approved.py      # Handle approved images
    ├── batch_processor.py       # Orchestrate entire pipeline
    ├── upload_batch.py          # Batch upload processor
    ├── generate_index.py        # JSON index generator
    ├── optimize_images.py       # Image optimization
    └── compress_images.py       # Image compression
```

### **CRITICAL: API Generation Requirements**
**⚠️ MANDATORY STEP WHEN ADDING NEW CATEGORIES:**

When new wallpapers are added to a category, you MUST update the API generation script:

```bash
# Edit tools/build_api.py to add the new category
# Line ~41: Add category to valid_categories set
# Line ~72: Add category description to category_descriptions dict
# Then run: python tools/build_api.py
```

**Example: Adding "patterns" category:**
```python
# In tools/build_api.py:
self.valid_categories = {
    'abstract', 'nature', ..., 'patterns'  # Add here
}

self.category_descriptions = {
    'abstract': 'Abstract patterns...',
    'patterns': 'Geometric patterns, repeating designs...'  # Add here
}
```

### **IMPORTANT DIRECTORY RULES**
1. **ALWAYS use `collection/wallpapers/{category}/` for wallpaper storage**
2. **ALWAYS use `collection/thumbnails/{category}/` for thumbnail storage**
3. **APIs auto-generated at `collection/api/v1/{category}.json` and `collection/api/v1/{category}/pages/{page}.json`**
4. **NEVER use the root `wallpapers/` or `thumbnails/` directories** (these are deprecated)
5. **Sequential naming**: 001.jpg, 002.jpg, 003.jpg (3-digit padding)
6. **GitHub Media URLs**: Use `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/...`

### Image Naming Convention (WallCraft API)
- **Format**: `{number}.{extension}` (sequential numbering within category folders)
- **Examples**: `001.jpg`, `002.jpg`, `003.jpg` (NOT `abstract_001.jpg`)
- **Rules**: 3-digit zero-padded numbers, stored in category-specific folders
- **Path Structure**: `collection/wallpapers/{category}/{number}.jpg`
- **API ID Format**: `{category}_{number}` (e.g., `gradient_001`, `abstract_045`)

## Wallpaper Categories

### Core Categories (High User Retention)
- **abstract** - Geometric patterns, fluid art, minimalist designs (257 images)
- **nature** - Landscapes, mountains, forests, oceans, wildlife (310 images) 
- **space** - Galaxies, nebulae, planets, astronauts, cosmic scenes (125 images)
- **minimal** - Clean designs, simple patterns, monochromatic themes (71 images)
- **cyberpunk** - Neon cities, futuristic themes, sci-fi aesthetics (84 images)
- **ai** - AI-generated artwork, futuristic themes, digital art (83 images)
- **4k** - Ultra high-resolution wallpapers across categories (200 images)

### Gaming & Entertainment
- **gaming** - Video game screenshots, concept art, characters (83 images)
- **anime** - Anime characters, Studio Ghibli, manga art (133 images)
- **movies** - Film posters, movie scenes, cinematic art (83 images)
- **music** - Album covers, music visualizations, instruments (83 images)

### Lifestyle & Interests
- **cars** - Sports cars, classic cars, automotive photography (83 images)
- **sports** - Football, basketball, extreme sports, fitness (115 images)
- **technology** - Gadgets, circuits, futuristic tech, AI themes (83 images)
- **architecture** - Buildings, bridges, modern/classic structures (275 images)
- **art** - Digital art, paintings, illustrations, creative designs (83 images)
- **animals** - Wildlife, pets, nature photography (84 images)

### Mood & Aesthetic
- **dark** - Dark themes, gothic, mysterious atmospheres (83 images)
- **neon** - Neon lights, synthwave, retro-futuristic vibes (83 images)
- **pastel** - Soft colors, kawaii, gentle aesthetics (71 images)
- **vintage** - Retro designs, old-school aesthetics (100 images)
- **gradient** - Color transitions, smooth blends, abstract flows (145 images)
- **patterns** - Geometric patterns, repeating designs, textures (81 images)

### Seasonal & Special
- **seasonal** - Holiday themes, seasonal changes, celebrations (83 images)

### Current Collection Statistics (2025-07-28)
- **Total Categories**: 24 active categories
- **Total Wallpapers**: 2,737 high-quality images
- **Total Thumbnails**: 2,737 optimized thumbnails  
- **API Coverage**: 100% (all categories have complete APIs)
- **Pagination Coverage**: 100% (all categories have paginated endpoints)

### Category Selection Strategy
Categories chosen based on:
- High user engagement and retention rates
- Diverse aesthetic preferences  
- Popular search trends in wallpaper apps
- Broad appeal across different demographics
- Pinterest scraping effectiveness and image quality

## JSON Schema

### Master Index (index.json)
```json
{
  "version": "1.0.0",
  "lastUpdated": "2024-01-15T10:30:00Z",
  "totalWallpapers": 1250,
  "categories": [
    {
      "id": "abstract",
      "name": "Abstract",
      "count": 320,
      "description": "Abstract AI-generated patterns and shapes"
    }
  ],
  "featured": [
    {
      "id": "abstract_001",
      "category": "abstract",
      "filename": "abstract_001.jpg",
      "title": "Geometric Flow",
      "width": 1080,
      "height": 1920,
      "fileSize": 245760,
      "hash": "abc123def456",
      "prompt": "geometric abstract flowing patterns in blue and purple",
      "tags": ["geometric", "flowing", "blue", "purple"],
      "downloadUrl": "https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/abstract/abstract_001.jpg",
      "thumbnailUrl": "https://raw.githubusercontent.com/username/wallpaper-collection/main/thumbnails/abstract/abstract_001.jpg",
      "createdAt": "2024-01-10T14:20:00Z"
    }
  ]
}
```

### Category Index (categories/{category}.json)
```json
{
  "category": "abstract",
  "name": "Abstract",
  "description": "Abstract AI-generated patterns and shapes",
  "count": 320,
  "lastUpdated": "2024-01-15T10:30:00Z",
  "wallpapers": [
    {
      "id": "abstract_001",
      "filename": "abstract_001.jpg",
      "title": "Geometric Flow",
      "width": 1080,
      "height": 1920,
      "fileSize": 245760,
      "downloadUrl": "https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/abstract/abstract_001.jpg",
      "thumbnailUrl": "https://raw.githubusercontent.com/username/wallpaper-collection/main/thumbnails/abstract/abstract_001.jpg"
    }
  ]
}
```

## Image Optimization Guidelines

### Image Specifications
- **Format**: JPEG for photos, PNG for graphics with transparency
- **Max Resolution**: 1080x1920 for mobile optimization
- **Quality**: 85% for main images, 80% for thumbnails
- **File Size**: <500KB for main images, <100KB for thumbnails
- **Aspect Ratio**: Mobile-optimized (portrait/square preferred)

### Thumbnail Specifications
- **Size**: 400x600 pixels maximum
- **Quality**: 80% JPEG compression
- **Format**: Always JPEG for consistency
- **Naming**: Same as main image filename

## Multi-Source Image Crawling System

### Supported Sources
- **Unsplash API** - High-quality photography, nature, architecture, lifestyle
- **Pexels API** - Diverse categories, good for sports, technology, cars
- **Pixabay** - Large variety, excellent for abstract, digital art, vintage
- **Wallhaven** - Gaming, anime, technology, cyberpunk focused
- **Pinterest** - Excellent for gradients, abstract patterns, design inspiration
- **Custom scrapers** - Specialized sites with ToS compliance

### Crawling Features
- Category-optimized source selection
- API rate limiting and quota management
- Duplicate detection across sources
- Metadata extraction and enhancement
- Automatic retry and error handling
- Progress tracking and logging

### Source-Category Mapping
```python
# Optimal sources for each category
SOURCE_MAPPING = {
    'nature': ['unsplash', 'pexels', 'pixabay'],
    'gaming': ['wallhaven', 'custom_scrapers'],
    'anime': ['wallhaven', 'custom_scrapers'],
    'cars': ['pexels', 'unsplash'],
    'sports': ['pexels', 'unsplash'],
    'technology': ['unsplash', 'pexels', 'wallhaven'],
    'space': ['unsplash', 'pexels', 'pixabay'],
    'abstract': ['pixabay', 'unsplash', 'pexels'],
    'gradient': ['pinterest', 'unsplash', 'pixabay'],  # Pinterest excellent for gradients
    'architecture': ['unsplash', 'pexels'],
    'art': ['pixabay', 'unsplash']
}
```

## AI Quality Assessment System

### Quality Metrics
- **Technical Quality**: Sharpness, resolution, noise levels, compression artifacts
- **Aesthetic Quality**: Composition, color balance, visual appeal, artistic merit
- **Content Appropriateness**: Safe content, no watermarks, mobile-suitable aspect ratios
- **Mobile Optimization**: Portrait/landscape suitability, readability on small screens

### AI Assessment Tools
- **BRISQUE** - Blind/Referenceless Image Spatial Quality Evaluator
- **OpenCV metrics** - Sharpness detection, blur assessment, contrast analysis
- **Custom scoring** - Trained on wallpaper preferences and user feedback
- **Content filtering** - NSFW detection, watermark identification, logo removal

### Review Categories
- **Auto-approved** - High-quality images meeting all criteria (>8.0/10 score)
- **Auto-rejected** - Poor quality, inappropriate content (<4.0/10 score)
- **Manual review** - Borderline cases requiring human judgment (4.0-8.0 score)

### Assessment Pipeline
1. **Technical Analysis**: Resolution, sharpness, noise, file format validation
2. **Content Analysis**: Subject detection, appropriateness filtering, watermark detection
3. **Aesthetic Scoring**: Composition analysis, color harmony, visual appeal
4. **Mobile Optimization**: Aspect ratio analysis, readability assessment
5. **Final Classification**: Auto-approve, auto-reject, or flag for manual review

## Automation Scripts

### **PRIMARY TOOL**: Pinterest API Scraper (pinterest_api_scraper.py) ⭐
```bash
# Interactive Pinterest scraper with complete automation
python scripts/pinterest_api_scraper.py

# User prompts:
# 📌 Pinterest URL (search/board/user): https://pinterest.com/search/pins/?q=abstract%20gradient
# 📂 Category name: gradient  
# 🔢 Number of images: 25

# Automatic process:
# 1. ✅ Scrapes Pinterest with advanced scrolling
# 2. ✅ Downloads high-resolution images (800x1200+ min)
# 3. ✅ Creates sequential filenames (001.jpg, 002.jpg, etc.)
# 4. ✅ Generates thumbnails automatically
# 5. ✅ Places in proper collection structure
# 6. ✅ Runs API generation script (tools/build_api.py)
# 7. ✅ Creates complete pagination system
# 8. ✅ Ready for mobile app consumption immediately!

# Features:
# - Selenium-based with intelligent scrolling
# - High-resolution filtering and validation
# - Duplicate detection and prevention
# - Automatic thumbnail generation (400x600)
# - Complete API integration
# - GitHub Media URL structure
# - Comprehensive error handling and logging
```

### **SECONDARY TOOL**: API Generator (tools/build_api.py)
```bash
# Generate APIs after manual image additions
python tools/build_api.py

# Features:
# - Scans all category directories
# - Generates complete JSON APIs
# - Creates pagination (15 items per page)
# - Updates master API endpoints
# - Handles all 24+ categories automatically
```

### Legacy Tools (Mostly Deprecated)
```bash
# Legacy crawlers - use pinterest_api_scraper.py instead
python scripts/crawl_images.py --category nature --source unsplash --limit 100
python scripts/review_images.py --input crawl_cache/ --output review_system/
python scripts/process_approved.py --input review_system/approved/ --category nature
python scripts/batch_processor.py --categories nature,gaming,anime --sources unsplash,wallhaven

# Still useful for specific tasks:
python scripts/optimize_images.py --target-width 1080 --quality 85
python scripts/generate_thumbnails.py --size 400x600 --quality 80
```

## API Endpoints

### WallCraft API Access (GitHub Raw URLs)
- **Base URL**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/`
- **Category API**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/{category}.json`
- **All Categories**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json`
- **Wallpaper Image**: `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/{category}/{number}.jpg`
- **Thumbnail**: `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/{category}/{number}.jpg`

### Pagination System (100% COMPLETE) ✅
**Complete pagination support with 15 items per page across ALL categories:**

#### Pagination Structure:
- **Main API**: `{category}.json` (complete category data)
- **Paginated API**: `{category}/pages/{page}.json` (15 items per page)

#### Example URLs:
```bash
# Main category API (all items)
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract.json

# Paginated endpoints
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract/pages/1.json
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature/pages/1.json
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/gradient/pages/1.json
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/patterns/pages/1.json
```

#### Pagination Metadata:
```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2025-07-28T22:38:03.579947",
    "category": "gradient",
    "page": 1,
    "per_page": 15,
    "total_pages": 10,
    "total_count": 145,
    "count_on_page": 15,
    "has_next": true,
    "has_prev": false,
    "next_page_url": "/api/v1/gradient/pages/2.json",
    "prev_page_url": null
  }
}
```

#### Complete Pagination Coverage (All 24 Categories):
- **Large Collections (15+ pages)**:
  - architecture: 19 pages (275 images)
  - nature: 21 pages (310 images)  
  - abstract: 18 pages (257 images)
  - 4k: 14 pages (200 images)
  - all: 178 pages (2,737 total images)

- **Medium Collections (8-12 pages)**:
  - gradient: 10 pages (145 images)
  - anime: 9 pages (133 images)
  - space: 9 pages (125 images)
  - sports: 8 pages (115 images)
  - vintage: 7 pages (100 images)

- **Standard Collections (6 pages)**:
  - animals, art, cars, cyberpunk, dark, gaming, neon, seasonal, technology: 6 pages each (83-84 images)

- **Compact Collections (5-6 pages)**:
  - patterns: 6 pages (81 images)
  - minimal: 5 pages (71 images)
  - pastel: 5 pages (71 images)

**Status**: ✅ **100% Complete** - All categories have full pagination support!

### Deprecated URLs (DO NOT USE)
- **Old Raw URLs**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/...`
- **Old Categories**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/categories/{category}.json`

### GitHub API Access
- **Contents API**: `https://api.github.com/repos/ddh4r4m/wallpaper-collection/contents/wallpapers/{category}`
- **Repository Info**: `https://api.github.com/repos/ddh4r4m/wallpaper-collection`

## Development Workflow

### Adding New Wallpapers (RECOMMENDED METHOD)
1. **PRIMARY METHOD**: Use the Pinterest API Scraper
   ```bash
   python scripts/pinterest_api_scraper.py
   # Interactive prompts for URL, category, quantity
   # Automatically handles everything: download, processing, APIs, pagination
   ```

2. **ALTERNATIVE**: Manual addition + API generation
   - Place images in `collection/wallpapers/{category}/` with sequential naming (001.jpg, 002.jpg, etc.)
   - Run `python tools/build_api.py` to generate all APIs and pagination
   - Script automatically creates thumbnails and complete API structure

### Updating Metadata
1. Modify category descriptions in `scripts/generate_index.py`
2. Run `python scripts/generate_index.py --update-all`
3. Commit changes to repository

### Image Optimization
1. Run `python scripts/optimize_images.py --target-width 1080 --quality 85`
2. Verify optimized images meet size requirements
3. Update thumbnails if needed

## Quality Assurance

### Image Validation
- **Format**: Only JPEG/PNG allowed
- **Size**: Must be mobile-optimized (max 1080x1920)
- **Quality**: High enough for display, small enough for fast loading
- **Naming**: Must follow convention exactly

### JSON Validation
- **Structure**: Must match schema exactly
- **URLs**: All download/thumbnail URLs must be accessible
- **Metadata**: Complete and accurate information required
- **Timestamps**: ISO 8601 format required

### Performance Requirements
- **Load Time**: Images should load within 2 seconds on 4G
- **File Size**: Main images <500KB, thumbnails <100KB
- **CDN Delivery**: GitHub Raw Files provides global CDN
- **Caching**: Images cached by browsers automatically

## Repository Settings

### GitHub Configuration
- **Visibility**: Public (required for raw.githubusercontent.com access)
- **Branch**: Use `main` branch for production
- **Releases**: Tag versions for major updates
- **Issues**: Enable for bug reports and feature requests

### Access Control
- **Raw Files**: Publicly accessible via GitHub CDN
- **API**: Rate limited but publicly accessible
- **Repository**: Public read access, controlled write access

This repository serves as a scalable, free hosting solution for wallpaper collections with automated Pinterest scraping, complete API generation, and mobile app consumption.

## Recent Major Updates (2025-07-28)
- ✅ **Pinterest API Scraper**: Complete automation from URL to mobile-ready APIs
- ✅ **Full Pagination**: 100% coverage across all 24 categories  
- ✅ **New Categories**: Added patterns (81 images), enhanced nature/space/ai
- ✅ **2,737 Total Images**: Largest collection update with complete API coverage
- ✅ **GitHub Media URLs**: Optimized for CDN delivery and mobile performance

**Next Steps for Development:**
1. Use `python scripts/pinterest_api_scraper.py` for new image additions
2. All APIs and pagination auto-generate - no manual intervention needed
3. Collection ready for immediate mobile app integration