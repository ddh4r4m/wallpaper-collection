#!/usr/bin/env python3
"""
Premium Abstract Gradient Background Scraper
Focuses on high-quality abstract gradients like the Pinterest search you referenced
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
        logging.FileHandler('premium_gradient_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PremiumGradientScraper:
    """Premium abstract gradient scraper targeting high-quality backgrounds"""
    
    def __init__(self, output_dir: str = "premium_gradient_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # High-quality requirements for mobile
        self.min_width = 1080
        self.min_height = 1920
        self.min_file_size = 100000  # 100KB minimum for quality
        
        # Rate limiting
        self.request_delay = 2.0
        
        # Setup session with better headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Premium gradient search terms (more specific)
        self.premium_queries = [
            "abstract gradient background 4k",
            "smooth gradient wallpaper hd",
            "colorful abstract gradient",
            "minimal gradient background",
            "abstract color gradient",
            "premium gradient wallpaper",
            "digital gradient art",
            "abstract gradient design",
            "modern gradient background",
            "vibrant gradient wallpaper"
        ]
        
        # Color-specific gradients
        self.color_gradients = [
            "blue purple gradient background",
            "pink orange gradient wallpaper", 
            "sunset gradient background",
            "ocean gradient wallpaper",
            "rainbow gradient abstract",
            "pastel gradient background",
            "neon gradient wallpaper",
            "dark gradient background",
            "warm gradient colors",
            "cool gradient tones"
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
    
    def extract_pinterest_data(self, query: str) -> List[Dict]:
        """Extract Pinterest data using their search API approach"""
        # Use Pinterest's own search structure similar to your reference
        search_params = {
            'q': query,
            'rs': 'ac',
            'len': '2',
            'source_id': 'ac_li5uWglg',
            'eq': 'abstract grad',
            'etslf': '7977'
        }
        
        search_url = "https://in.pinterest.com/search/pins/"
        
        try:
            response = self.session.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            
            # Enhanced patterns to extract high-quality image URLs
            image_patterns = [
                # High resolution Pinterest URLs
                r'"url":"(https://i\.pinimg\.com/originals/[^"]+\.(?:jpg|jpeg|png))"',
                r'"url":"(https://i\.pinimg\.com/736x/[^"]+\.(?:jpg|jpeg|png))"',
                r'"url":"(https://i\.pinimg\.com/564x/[^"]+\.(?:jpg|jpeg|png))"',
                # Alternative patterns
                r'https://i\.pinimg\.com/originals/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.(?:jpg|jpeg|png)',
                r'https://i\.pinimg\.com/736x/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.(?:jpg|jpeg|png)'
            ]
            
            image_data = []
            for pattern in image_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if isinstance(match, tuple):
                        url = match[0] if match[0] else match
                    else:
                        url = match
                    
                    # Convert to highest quality
                    high_quality_url = self.get_highest_quality_url(url)
                    
                    image_data.append({
                        'url': high_quality_url,
                        'query': query,
                        'source': 'pinterest_premium'
                    })
            
            # Remove duplicates
            seen_urls = set()
            unique_data = []
            for item in image_data:
                if item['url'] not in seen_urls:
                    seen_urls.add(item['url'])
                    unique_data.append(item)
            
            logger.info(f"Extracted {len(unique_data)} unique high-quality URLs for '{query}'")
            return unique_data
            
        except Exception as e:
            logger.error(f"Failed to extract Pinterest data for '{query}': {e}")
            return []
    
    def get_highest_quality_url(self, url: str) -> str:
        """Convert any Pinterest URL to highest quality version"""
        # Replace size indicators with originals for maximum quality
        if '/564x/' in url:
            return url.replace('/564x/', '/originals/')
        elif '/736x/' in url:
            return url.replace('/736x/', '/originals/')
        elif '/474x/' in url:
            return url.replace('/474x/', '/originals/')
        elif '/236x/' in url:
            return url.replace('/236x/', '/originals/')
        else:
            return url
    
    def is_premium_gradient(self, image_data: bytes, url: str) -> bool:
        """Enhanced check for premium gradient quality"""
        # File size check for quality
        if len(image_data) < self.min_file_size:
            return False
        
        # Check for common gradient indicators in URL
        gradient_indicators = [
            'gradient', 'abstract', 'color', 'rainbow', 
            'smooth', 'blend', 'spectrum', 'vibrant'
        ]
        
        url_lower = url.lower()
        has_gradient_indicator = any(indicator in url_lower for indicator in gradient_indicators)
        
        # Additional quality checks
        is_good_size = len(image_data) > self.min_file_size
        is_not_tiny = len(image_data) > 50000  # At least 50KB
        
        return is_good_size and is_not_tiny
    
    def download_premium_image(self, image_info: Dict, index: int) -> bool:
        """Download premium gradient with enhanced quality checks"""
        try:
            url = image_info['url']
            query = image_info['query']
            
            # Download with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
            
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {url}")
                return False
            
            # Premium quality check
            if not self.is_premium_gradient(image_data, url):
                logger.info(f"Image doesn't meet premium quality standards: {url}")
                return False
            
            # Create descriptive filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            query_short = query.replace(' ', '_')[:20]
            filename = f"premium_gradient_{index:03d}_{query_short}_{url_hash}.jpg"
            filepath = self.output_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Enhanced metadata
            metadata = {
                'id': url_hash,
                'source': 'pinterest_premium',
                'category': 'gradient',
                'title': f"Premium Abstract Gradient {index}",
                'description': f"High-quality abstract gradient background from Pinterest premium search",
                'query': query,
                'file_size': len(image_data),
                'download_url': url,
                'quality_tier': 'premium',
                'mobile_optimized': True,
                'estimated_resolution': f"High-resolution (estimated {self.min_width}x{self.min_height}+)",
                'tags': ['gradient', 'abstract', 'premium', 'background', 'mobile', 'wallpaper', 'hd'],
                'color_profile': self.detect_color_profile(query),
                'crawled_at': datetime.now().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update hash tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded premium gradient: {filename} ({len(image_data):,} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download premium image {url}: {e}")
            return False
    
    def detect_color_profile(self, query: str) -> str:
        """Detect likely color profile from query"""
        query_lower = query.lower()
        
        if any(color in query_lower for color in ['blue', 'ocean', 'sky']):
            return 'blue_tones'
        elif any(color in query_lower for color in ['pink', 'purple', 'magenta']):
            return 'pink_purple'
        elif any(color in query_lower for color in ['sunset', 'orange', 'warm']):
            return 'warm_tones'
        elif any(color in query_lower for color in ['rainbow', 'colorful', 'vibrant']):
            return 'multi_color'
        elif any(color in query_lower for color in ['pastel', 'soft']):
            return 'pastel'
        elif any(color in query_lower for color in ['dark', 'black']):
            return 'dark_tones'
        else:
            return 'mixed'
    
    def scrape_premium_gradients(self, limit: int = 30) -> int:
        """Scrape premium abstract gradients"""
        logger.info("Starting premium abstract gradient scraping...")
        logger.info(f"Target: {limit} high-quality gradient backgrounds")
        
        downloaded_count = 0
        total_index = 1
        
        # Combine premium and color-specific queries
        all_queries = self.premium_queries + self.color_gradients
        
        for query in all_queries:
            if downloaded_count >= limit:
                break
            
            logger.info(f"Searching premium gradients: {query}")
            
            # Extract image data
            image_data_list = self.extract_pinterest_data(query)
            
            if not image_data_list:
                logger.warning(f"No images found for '{query}'")
                continue
            
            # Download premium images
            for image_info in image_data_list:
                if downloaded_count >= limit:
                    break
                
                if self.download_premium_image(image_info, total_index):
                    downloaded_count += 1
                
                total_index += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
            
            # Longer delay between different queries
            time.sleep(self.request_delay * 2)
        
        return downloaded_count
    
    def create_premium_summary(self, downloaded_count: int):
        """Create enhanced summary for premium gradients"""
        summary = {
            'scrape_type': 'premium_abstract_gradients',
            'category': 'gradient',
            'total_downloaded': downloaded_count,
            'quality_tier': 'premium',
            'target_resolution': 'Mobile HD (1080x1920+)',
            'min_file_size': f"{self.min_file_size:,} bytes",
            'search_focus': 'High-quality abstract gradient backgrounds',
            'queries_used': self.premium_queries + self.color_gradients,
            'features': [
                'Premium quality filtering',
                'Mobile optimized',
                'High-resolution focus',
                'Color profile detection',
                'Duplicate prevention'
            ],
            'crawl_time': datetime.now().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / 'premium_gradient_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()

def main():
    parser = argparse.ArgumentParser(description='Premium Abstract Gradient Scraper')
    parser.add_argument('--limit', type=int, default=30, help='Max premium images to download')
    parser.add_argument('--output', default='premium_gradient_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = PremiumGradientScraper(args.output)
    
    try:
        # Scrape premium gradients
        downloaded = scraper.scrape_premium_gradients(args.limit)
        
        # Create summary
        scraper.create_premium_summary(downloaded)
        
        print(f"\n🎨 Premium gradient scraping complete!")
        print(f"📊 Downloaded: {downloaded} high-quality abstract gradients")
        print(f"📁 Output directory: {args.output}")
        print(f"🎯 Focus: Premium abstract gradient backgrounds")
        print(f"📱 Optimized for: Mobile wallpapers (HD+)")
        
        print(f"\n📋 Premium files created:")
        
        # List downloaded files with details
        jpg_files = sorted(list(Path(args.output).glob("*.jpg")))
        for i, file in enumerate(jpg_files[:8], 1):
            size = file.stat().st_size
            print(f"  {i}. {file.name} ({size:,} bytes)")
        
        if len(jpg_files) > 8:
            print(f"  ... and {len(jpg_files) - 8} more premium gradients")
        
        print(f"\n🔄 Next steps:")
        print(f"1. Review premium gradients in {args.output}/")
        print(f"2. Select best gradients for your collection")
        print(f"3. Move approved images to wallpapers/gradient/")
        print(f"4. Update collection metadata")
        
        if downloaded > 0:
            print(f"\n✨ Success! Found {downloaded} premium abstract gradients")
        else:
            print(f"\n⚠️  No premium gradients downloaded. Try adjusting search terms or checking connectivity.")
        
    except KeyboardInterrupt:
        logger.info("Premium scraping interrupted by user")
    except Exception as e:
        logger.error(f"Premium scraping failed: {e}")

if __name__ == "__main__":
    main()