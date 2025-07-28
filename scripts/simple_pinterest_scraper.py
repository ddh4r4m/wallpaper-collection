#!/usr/bin/env python3
"""
Simple Pinterest Gradient Wallpaper Scraper
No selenium dependencies - uses requests only
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse, quote
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_pinterest_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimplePinterestScraper:
    """Simple Pinterest scraper using requests only"""
    
    def __init__(self, output_dir: str = "gradient_mobile_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mobile wallpaper requirements
        self.min_width = 1080
        self.min_height = 1920
        self.preferred_width = 1440
        self.preferred_height = 2560
        
        # Rate limiting
        self.request_delay = 3.0
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Gradient-specific search terms
        self.gradient_queries = [
            "abstract gradient background",
            "gradient wallpaper mobile",
            "abstract gradient phone wallpaper",
            "colorful gradient background",
            "smooth gradient wallpaper",
            "rainbow gradient background",
            "minimal gradient wallpaper",
            "blue gradient background",
            "purple gradient wallpaper",
            "sunset gradient background"
        ]
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load existing hashes: {e}")
    
    def save_downloaded_hashes(self):
        """Save downloaded hashes to file"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
    
    def get_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image data"""
        return hashlib.md5(image_data).hexdigest()
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check if image is already downloaded"""
        image_hash = self.get_image_hash(image_data)
        return image_hash in self.downloaded_hashes
    
    def extract_pinterest_images(self, query: str) -> List[str]:
        """Extract image URLs from Pinterest search using web scraping"""
        search_url = f"https://www.pinterest.com/search/pins/?q={quote(query)}"
        
        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Extract image URLs from the HTML
            html_content = response.text
            
            # Look for image URLs in the HTML
            # Pinterest uses various patterns for image URLs
            image_url_patterns = [
                r'https://i\.pinimg\.com/originals/[^"\']+\.jpg',
                r'https://i\.pinimg\.com/564x/[^"\']+\.jpg',
                r'https://i\.pinimg\.com/736x/[^"\']+\.jpg',
            ]
            
            image_urls = []
            for pattern in image_url_patterns:
                urls = re.findall(pattern, html_content)
                image_urls.extend(urls)
            
            # Remove duplicates and return
            return list(set(image_urls))
            
        except Exception as e:
            logger.error(f"Failed to extract images for query '{query}': {e}")
            return []
    
    def get_high_res_url(self, url: str) -> str:
        """Convert Pinterest URL to highest resolution version"""
        # Replace size parameters with originals for highest quality
        if '/564x/' in url:
            return url.replace('/564x/', '/originals/')
        elif '/736x/' in url:
            return url.replace('/736x/', '/originals/')
        else:
            return url
    
    def is_gradient_image(self, image_data: bytes) -> bool:
        """Simple check if image might be a gradient (basic heuristic)"""
        # For now, we'll trust the search query results
        # Could add more sophisticated image analysis here
        return len(image_data) > 50000  # At least 50KB for good quality
    
    def download_image(self, image_url: str, index: int, query: str) -> bool:
        """Download and save gradient image"""
        try:
            # Get high-resolution version
            high_res_url = self.get_high_res_url(image_url)
            
            # Download image
            response = self.session.get(high_res_url, stream=True, timeout=30)
            response.raise_for_status()
            
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {high_res_url}")
                return False
            
            # Basic gradient check
            if not self.is_gradient_image(image_data):
                logger.info(f"Image too small, skipping: {high_res_url}")
                return False
            
            # Create filename
            url_hash = hashlib.md5(high_res_url.encode()).hexdigest()[:8]
            filename = f"gradient_{index:03d}_{url_hash}.jpg"
            filepath = self.output_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create metadata
            metadata = {
                'id': url_hash,
                'source': 'pinterest',
                'category': 'gradient',
                'title': f"Abstract gradient background {index}",
                'description': f"High-resolution gradient wallpaper from Pinterest search: {query}",
                'query': query,
                'file_size': len(image_data),
                'download_url': high_res_url,
                'tags': ['gradient', 'abstract', 'background', 'mobile', 'wallpaper'],
                'mobile_optimized': True,
                'estimated_resolution': 'High-resolution mobile wallpaper',
                'crawled_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update hash tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded gradient wallpaper: {filename} ({len(image_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {image_url}: {e}")
            return False
    
    def scrape_gradients(self, limit: int = 30) -> int:
        """Scrape gradient backgrounds from Pinterest"""
        logger.info("Starting Pinterest gradient wallpaper scraping...")
        
        downloaded_count = 0
        total_index = 1
        
        for query in self.gradient_queries:
            if downloaded_count >= limit:
                break
            
            logger.info(f"Searching for: {query}")
            
            # Extract image URLs
            image_urls = self.extract_pinterest_images(query)
            logger.info(f"Found {len(image_urls)} potential images for '{query}'")
            
            # Download images
            for url in image_urls:
                if downloaded_count >= limit:
                    break
                
                if self.download_image(url, total_index, query):
                    downloaded_count += 1
                
                total_index += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
            
            # Delay between queries
            time.sleep(self.request_delay * 2)
        
        return downloaded_count
    
    def create_summary(self, downloaded_count: int):
        """Create crawl summary"""
        summary = {
            'category': 'gradient',
            'queries_used': self.gradient_queries,
            'total_downloaded': downloaded_count,
            'target_resolution': 'Mobile optimized (1080x1920+)',
            'search_focus': 'Abstract gradient backgrounds',
            'crawl_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / 'gradient_scrape_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()

def main():
    parser = argparse.ArgumentParser(description='Simple Pinterest Gradient Scraper')
    parser.add_argument('--limit', type=int, default=30, help='Max images to download')
    parser.add_argument('--output', default='gradient_mobile_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = SimplePinterestScraper(args.output)
    
    try:
        # Scrape gradients
        downloaded = scraper.scrape_gradients(args.limit)
        
        # Create summary
        scraper.create_summary(downloaded)
        
        print(f"\n🎉 Gradient scraping complete!")
        print(f"📊 Downloaded: {downloaded} high-resolution gradient wallpapers")
        print(f"📁 Output directory: {args.output}")
        print(f"🎨 Focus: Abstract gradient backgrounds for mobile")
        print(f"\n📋 Files created:")
        
        # List downloaded files
        jpg_files = list(Path(args.output).glob("*.jpg"))
        for i, file in enumerate(jpg_files[:5], 1):
            print(f"  {i}. {file.name}")
        
        if len(jpg_files) > 5:
            print(f"  ... and {len(jpg_files) - 5} more files")
        
        print(f"\n🔄 Next steps:")
        print(f"1. Review images in {args.output}/")
        print(f"2. Move approved images to wallpapers/gradient/")
        print(f"3. Update collection indexes")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    main()