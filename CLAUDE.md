# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a wallpaper repository serving AI-generated wallpapers via GitHub Raw Files. It provides a structured collection of high-quality wallpapers organized by categories, with JSON metadata for easy consumption by mobile applications.

## Essential Development Commands

### Repository Management
```bash
# Initialize repository structure with all categories
mkdir -p wallpapers/{abstract,nature,space,minimal,cyberpunk,gaming,anime,movies,music,cars,sports,technology,architecture,art,dark,neon,pastel,vintage,gradient,seasonal}
mkdir -p thumbnails/{abstract,nature,space,minimal,cyberpunk,gaming,anime,movies,music,cars,sports,technology,architecture,art,dark,neon,pastel,vintage,gradient,seasonal}
mkdir -p categories
mkdir -p scripts
mkdir -p review_system/{approved,rejected,manual_review}
mkdir -p crawl_cache

# Crawl images from multiple sources
python scripts/crawl_images.py --category nature --source unsplash --limit 100
python scripts/crawl_images.py --category gaming --source wallhaven --limit 50

# Run AI quality assessment on crawled images
python scripts/review_images.py --input crawl_cache/ --output review_system/

# Process approved images
python scripts/process_approved.py --input review_system/approved/ --category nature

# Generate/update JSON indexes
python scripts/generate_index.py

# Batch process entire pipeline
python scripts/batch_processor.py --categories nature,gaming,anime --sources unsplash,wallhaven
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

### **IMPORTANT DIRECTORY RULES**
1. **ALWAYS use `collection/wallpapers/{category}/` for wallpaper storage**
2. **ALWAYS use `collection/thumbnails/{category}/` for thumbnail storage**
3. **ALWAYS use `collection/api/v1/{category}.json` for API endpoints**
4. **NEVER use the root `wallpapers/` or `thumbnails/` directories** (these are deprecated)
5. **Sequential naming**: 001.jpg, 002.jpg, 003.jpg (3-digit padding)
6. **GitHub Media URLs**: Use `https://media.githubusercontent.com/media/username/repo/main/collection/...`

### Image Naming Convention (WallCraft API)
- **Format**: `{number}.{extension}` (sequential numbering within category folders)
- **Examples**: `001.jpg`, `002.jpg`, `003.jpg` (NOT `abstract_001.jpg`)
- **Rules**: 3-digit zero-padded numbers, stored in category-specific folders
- **Path Structure**: `collection/wallpapers/{category}/{number}.jpg`
- **API ID Format**: `{category}_{number}` (e.g., `gradient_001`, `abstract_045`)

## Wallpaper Categories

### Core Categories (High User Retention)
- **abstract** - Geometric patterns, fluid art, minimalist designs, mathematical visualizations
- **nature** - Landscapes, mountains, forests, oceans, wildlife, botanical photography
- **space** - Galaxies, nebulae, planets, astronauts, cosmic scenes, stellar photography
- **minimal** - Clean designs, simple patterns, monochromatic themes, zen aesthetics
- **cyberpunk** - Neon cities, futuristic themes, sci-fi aesthetics, digital dystopia

### Gaming & Entertainment
- **gaming** - Video game screenshots, concept art, characters, gaming environments
- **anime** - Anime characters, Studio Ghibli, manga art, Japanese animation
- **movies** - Film posters, movie scenes, cinematic art, movie characters
- **music** - Album covers, music visualizations, instruments, concert photography

### Lifestyle & Interests
- **cars** - Sports cars, classic cars, automotive photography, racing scenes
- **sports** - Football, basketball, extreme sports, fitness, athletic photography
- **technology** - Gadgets, circuits, futuristic tech, AI themes, digital interfaces
- **architecture** - Buildings, bridges, modern/classic structures, urban photography
- **art** - Digital art, paintings, illustrations, creative designs, artistic photography

### Mood & Aesthetic
- **dark** - Dark themes, gothic, mysterious atmospheres, low-light photography
- **neon** - Neon lights, synthwave, retro-futuristic vibes, electric aesthetics
- **pastel** - Soft colors, kawaii, gentle aesthetics, dream-like themes
- **vintage** - Retro designs, old-school aesthetics, nostalgic themes
- **gradient** - Color transitions, smooth blends, modern gradients, abstract flows

### Seasonal & Special
- **seasonal** - Holiday themes, seasonal changes, celebrations, weather phenomena

### Category Selection Strategy
Categories chosen based on:
- High user engagement and retention rates
- Diverse aesthetic preferences
- Popular search trends in wallpaper apps
- Broad appeal across different demographics
- Seasonal and trending content opportunities

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

### Image Crawler (crawl_images.py)
```bash
# Crawl from specific source and category
python scripts/crawl_images.py --category nature --source unsplash --limit 100

# Crawl from multiple sources
python scripts/crawl_images.py --category gaming --sources wallhaven,custom --limit 50

# Features:
# - Multi-source API integration
# - Rate limiting and quota management
# - Duplicate detection and filtering
# - Metadata extraction
# - Progress tracking and logging
```

### AI Quality Reviewer (review_images.py)
```bash
# Review crawled images with AI assessment
python scripts/review_images.py --input crawl_cache/ --output review_system/

# Review specific metrics
python scripts/review_images.py --input crawl_cache/ --metrics brisque,sharpness,content

# Features:
# - Multi-metric quality assessment
# - Automated approval/rejection
# - Manual review flagging
# - Detailed scoring reports
# - Batch processing capability
```

### Approved Image Processor (process_approved.py)
```bash
# Process approved images for specific category
python scripts/process_approved.py --input review_system/approved/ --category nature

# Process manually approved images
python scripts/process_approved.py --input review_system/manual_review/approved/ --category gaming

# Features:
# - Mobile optimization (resize, compress)
# - Thumbnail generation
# - Metadata enhancement
# - File organization
# - Index updates
```

### Batch Processor (batch_processor.py)
```bash
# Run complete pipeline for multiple categories
python scripts/batch_processor.py --categories nature,gaming,anime --sources unsplash,wallhaven

# Features:
# - End-to-end automation
# - Multi-category processing
# - Source optimization
# - Progress monitoring
# - Error handling and recovery
```

### Upload Batch Script (upload_batch.py)
```bash
# Process and upload new wallpapers
python scripts/upload_batch.py --folder ./new_wallpapers --category abstract

# Features:
# - Automatic image optimization
# - Thumbnail generation
# - Metadata extraction
# - JSON index updates
# - File naming standardization
```

## API Endpoints

### WallCraft API Access (GitHub Raw URLs)
- **Base URL**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/`
- **Category API**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/{category}.json`
- **All Categories**: `https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/all.json`
- **Wallpaper Image**: `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/{category}/{number}.jpg`
- **Thumbnail**: `https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/{category}/{number}.jpg`

### Pagination System (FULLY IMPLEMENTED)
**Complete pagination support with 15 items per page:**

#### Pagination Structure:
- **Main API**: `{category}.json` (complete category data)
- **Paginated API**: `{category}/pages/{page}.json` (15 items per page)

#### Example URLs:
```bash
# Main category API (all items)
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract.json

# Paginated endpoints
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/abstract/pages/1.json
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/4k/pages/1.json
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/api/v1/nature/pages/1.json
```

#### Pagination Metadata:
```json
{
  "meta": {
    "version": "1.0",
    "category": "abstract",
    "page": 1,
    "per_page": 15,
    "total_pages": 18,
    "total_count": 257,
    "count_on_page": 15,
    "has_next": true,
    "has_prev": false,
    "next_page_url": "/api/v1/abstract/pages/2.json",
    "prev_page_url": null
  }
}
```

#### Categories with Full Pagination:
- **Large Collections (10+ pages)**:
  - abstract: 18 pages (257 items)
  - architecture: 19 pages (275 items)
  - nature: 21 pages (305+ items)
  - 4k: 14 pages (200 items)
  - all: 162 pages (entire collection)

- **Medium Collections (5-9 pages)**:
  - ai: 8 pages
  - anime: 9 pages
  - space: 9 pages

- **Small Collections (2-6 pages)**:
  - animals: 6 pages
  - art: 6 pages
  - cars: 6 pages
  - cyberpunk: 6 pages
  - dark: 6 pages
  - gaming: 6 pages
  - minimal: 5 pages
  - neon: 6 pages
  - pastel: 5 pages
  - seasonal: 6 pages
  - technology: 6 pages
  - vintage: 7 pages

#### Missing Pagination (To Be Generated):
- gradient (149 items - needs ~10 pages)
- sports (needs pagination)
- movies (needs pagination)
- music (needs pagination)

### Deprecated URLs (DO NOT USE)
- **Old Raw URLs**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/...`
- **Old Categories**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/categories/{category}.json`

### GitHub API Access
- **Contents API**: `https://api.github.com/repos/ddh4r4m/wallpaper-collection/contents/wallpapers/{category}`
- **Repository Info**: `https://api.github.com/repos/ddh4r4m/wallpaper-collection`

## Development Workflow

### Adding New Wallpapers (WallCraft API Structure)
1. **ALWAYS use collection structure**: Place images in `collection/wallpapers/{category}/`
2. **Sequential naming**: Use 001.jpg, 002.jpg, 003.jpg format (3-digit padding)
3. Run `python scripts/upload_batch.py --folder ./new_images --category {category}`
4. Script automatically:
   - Places files in `collection/wallpapers/{category}/` with sequential naming
   - Creates thumbnails in `collection/thumbnails/{category}/`
   - Updates API endpoint at `collection/api/v1/{category}.json`
   - Uses GitHub Media URLs for mobile app consumption
   - Validates directory structure before processing

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

This repository serves as a scalable, free hosting solution for wallpaper collections with automated processing and JSON API for mobile app consumption.