# Pinterest High-Resolution Wallpaper Scraper Setup

## Overview

The Pinterest scraper is designed to collect high-resolution wallpapers (minimum 1920x1080, preferring 4K) from Pinterest while respecting rate limits and terms of service.

## Features

- ✅ **High-Resolution Focus**: Filters for images ≥1920x1080, prefers 4K
- ✅ **Duplicate Detection**: MD5 hash-based deduplication
- ✅ **Quality Scoring**: Advanced quality assessment algorithm
- ✅ **Rate Limiting**: Respectful delays and request limits
- ✅ **Category Optimization**: Tailored search queries per category
- ✅ **Headless Operation**: Automated browser control
- ✅ **Comprehensive Metadata**: Rich image information storage

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `selenium>=4.15.0` - Browser automation
- `webdriver-manager>=4.0.0` - Automatic ChromeDriver management
- `requests>=2.31.0` - HTTP requests
- `Pillow>=10.0.0` - Image processing

### 2. Install Chrome Browser

The scraper requires Google Chrome to be installed on your system.

**macOS:**
```bash
brew install google-chrome
```

**Ubuntu/Debian:**
```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable
```

## Usage

### Standalone Pinterest Scraper

```bash
# Basic usage
python scripts/pinterest_scraper.py --category nature --limit 25

# Advanced options
python scripts/pinterest_scraper.py \
  --category abstract \
  --limit 50 \
  --output pinterest_cache \
  --headless \
  --min-width 2560 \
  --min-height 1440
```

#### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--category` | Category to scrape (required) | - |
| `--limit` | Maximum images to download | 25 |
| `--output` | Output directory | `pinterest_cache` |
| `--headless` | Run browser in headless mode | `False` |
| `--min-width` | Minimum image width | 1920 |
| `--min-height` | Minimum image height | 1080 |

### Integrated with Batch Processor

```bash
# Use Pinterest as primary source
python scripts/batch_processor.py \
  --categories nature,abstract,space \
  --sources pinterest \
  --limit 100

# Mix Pinterest with other sources
python scripts/batch_processor.py \
  --categories gaming,anime \
  --sources pinterest,wallhaven \
  --limit 50
```

## Supported Categories

The Pinterest scraper has optimized search queries for these categories:

| Category | Search Optimization |
|----------|-------------------|
| **nature** | Nature wallpaper 4k, landscape photography, mountain scenery |
| **space** | Space wallpaper 4k, galaxy background, nebula wallpaper |
| **abstract** | Abstract wallpaper 4k, geometric patterns, digital art |
| **minimal** | Minimal wallpaper 4k, clean background, simple wallpaper |
| **cyberpunk** | Cyberpunk wallpaper 4k, neon city, futuristic background |
| **gaming** | Gaming wallpaper 4k, video game background, game art |
| **anime** | Anime wallpaper 4k, anime background, manga wallpaper |
| **cars** | Car wallpaper 4k, supercar photography, automotive |
| **architecture** | Architecture wallpaper 4k, building photography |
| **dark** | Dark wallpaper 4k, black background, dark aesthetic |
| **neon** | Neon wallpaper 4k, neon lights, cyberpunk neon |
| **pastel** | Pastel wallpaper 4k, soft colors, pastel aesthetic |

## Configuration

### Rate Limiting Settings

```python
# Pinterest scraper configuration
request_delay = 2.0  # Seconds between requests
max_pages = 3        # Maximum pages to scroll
max_images_per_search = 50  # Images per category
```

### Quality Requirements

```python
# Resolution requirements
min_width = 1920      # Minimum width (1080p)
min_height = 1080     # Minimum height (1080p)
preferred_width = 3840   # Preferred width (4K)
preferred_height = 2160  # Preferred height (4K)
```

## Output Structure

### Downloaded Files

```
pinterest_cache/
├── pinterest_nature_123456.jpg          # High-res image
├── pinterest_nature_123456.jpg.json     # Metadata
├── pinterest_nature_789012.jpg
├── pinterest_nature_789012.jpg.json
├── downloaded_hashes.json               # Duplicate prevention
└── pinterest_nature_summary.json        # Crawl summary
```

### Metadata Format

```json
{
  "id": "123456",
  "source": "pinterest",
  "category": "nature",
  "title": "Mountain landscape wallpaper",
  "description": "High-resolution nature wallpaper from Pinterest",
  "query": "nature wallpaper 4k",
  "width": 3840,
  "height": 2160,
  "file_size": 2458624,
  "download_url": "https://i.pinimg.com/originals/...",
  "source_url": "https://pinterest.com/pin/123456/",
  "tags": ["nature", "high-resolution", "4k", "wallpaper"],
  "quality_score": 8.7,
  "crawled_at": "2025-01-20T10:30:00Z"
}
```

### Summary Report

```json
{
  "category": "nature",
  "queries_used": ["nature wallpaper 4k", "landscape photography"],
  "total_pins_found": 47,
  "high_res_downloaded": 23,
  "min_resolution": "1920x1080",
  "preferred_resolution": "3840x2160",
  "crawl_time": "2025-01-20T10:30:00Z"
}
```

## Testing

### Quick Test

```bash
# Test Pinterest scraper functionality
python test_pinterest.py
```

### Manual Test

```bash
# Test with small limit
python scripts/pinterest_scraper.py \
  --category nature \
  --limit 3 \
  --output test_output
```

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   # Update ChromeDriver automatically
   pip install --upgrade webdriver-manager
   ```

2. **Rate Limiting**
   - Reduce `--limit` parameter
   - Increase delays in script configuration

3. **No Images Downloaded**
   - Check internet connection
   - Verify Chrome is installed
   - Try different category

4. **Permission Denied**
   ```bash
   # Ensure output directory is writable
   mkdir -p pinterest_cache
   chmod 755 pinterest_cache
   ```

### Debug Mode

```bash
# Run without headless mode to see browser
python scripts/pinterest_scraper.py \
  --category nature \
  --limit 5
  # Remove --headless flag
```

## Ethical Considerations

- ✅ Respects rate limits (2+ second delays)
- ✅ Limited scope (3 pages max per search)
- ✅ Educational purpose only
- ✅ No bulk downloading
- ✅ Proper attribution in metadata

## Performance Optimization

### For Better Results

1. **Use specific categories**: More focused searches yield better results
2. **Reasonable limits**: 25-50 images per run is optimal
3. **Run during off-peak hours**: Better Pinterest responsiveness
4. **Monitor quality scores**: Adjust minimum resolution if needed

### Batch Processing Integration

The Pinterest scraper automatically integrates with the existing pipeline:

```bash
# Full pipeline with Pinterest
python scripts/batch_processor.py \
  --categories nature,abstract \
  --sources pinterest,unsplash \
  --limit 100

# This will:
# 1. Scrape from Pinterest (25 images)
# 2. Scrape from Unsplash (75 images)  
# 3. Review image quality
# 4. Process approved images
# 5. Update collection indexes
```

## Advanced Usage

### Custom Search Queries

Modify `category_keywords` in `pinterest_scraper.py` to add custom search terms:

```python
self.category_keywords = {
    'your_category': ['custom search term', 'another term', 'specific query']
}
```

### Integration with Review System

Pinterest images automatically flow into the review system:

```bash
# After scraping
python scripts/review_images.py --input pinterest_cache
python scripts/process_approved.py --category nature
```

## Next Steps

After setup:

1. **Test the scraper**: `python test_pinterest.py`
2. **Run a small batch**: `python scripts/pinterest_scraper.py --category nature --limit 10`
3. **Review results**: Check `pinterest_cache/` directory
4. **Integrate with pipeline**: Use batch processor for automated workflow

The Pinterest scraper is now ready to provide high-quality wallpapers for your collection! 🎉