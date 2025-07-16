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

### File Organization
```
wallpaper-collection/
├── README.md                     # Repository documentation
├── index.json                    # Master index of all wallpapers
├── requirements.txt              # Python dependencies
├── categories/                   # Category-specific metadata (20+ files)
│   ├── abstract.json
│   ├── nature.json
│   ├── space.json
│   ├── gaming.json
│   ├── anime.json
│   ├── cars.json
│   ├── sports.json
│   └── ... (20+ category files)
├── wallpapers/                   # Main wallpaper images (20+ folders)
│   ├── abstract/
│   ├── nature/
│   ├── space/
│   ├── gaming/
│   ├── anime/
│   ├── cars/
│   ├── sports/
│   └── ... (20+ category folders)
├── thumbnails/                   # Optimized preview images
│   ├── abstract/
│   ├── nature/
│   ├── space/
│   └── ... (matching structure)
├── review_system/                # AI quality assessment
│   ├── approved/                 # Auto-approved images
│   ├── rejected/                 # Auto-rejected images
│   └── manual_review/            # Requires human review
├── crawl_cache/                  # Temporary download cache
│   ├── unsplash/
│   ├── pexels/
│   └── wallhaven/
└── scripts/                      # Management automation
    ├── crawl_images.py          # Multi-source image crawler
    ├── review_images.py         # AI quality assessment
    ├── process_approved.py      # Handle approved images
    ├── batch_processor.py       # Orchestrate entire pipeline
    ├── upload_batch.py          # Batch upload processor
    ├── generate_index.py        # JSON index generator
    ├── optimize_images.py       # Image optimization
    └── compress_images.py       # Image compression
```

### Image Naming Convention
- **Format**: `{category}_{number}.{extension}`
- **Examples**: `abstract_001.jpg`, `nature_045.jpg`, `gaming_012.jpg`
- **Rules**: 3-digit numbers, lowercase categories, no spaces

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

### GitHub Raw Files Access
- **Base URL**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/`
- **Master Index**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/index.json`
- **Category Index**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/categories/{category}.json`
- **Wallpaper Image**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/{category}/{filename}`
- **Thumbnail**: `https://raw.githubusercontent.com/username/wallpaper-collection/main/thumbnails/{category}/{filename}`

### GitHub API Access
- **Contents API**: `https://api.github.com/repos/username/wallpaper-collection/contents/wallpapers/{category}`
- **Repository Info**: `https://api.github.com/repos/username/wallpaper-collection`

## Development Workflow

### Adding New Wallpapers
1. Place images in appropriate folder structure
2. Run `python scripts/upload_batch.py --folder ./new_images --category {category}`
3. Script automatically:
   - Optimizes images for mobile
   - Generates thumbnails
   - Creates metadata
   - Updates JSON indexes
   - Generates unique filenames

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