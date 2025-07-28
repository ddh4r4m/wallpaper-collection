#!/usr/bin/env python3
"""
Pinterest High-Resolution Wallpaper Scraper
Educational purposes only - respects Pinterest's rate limits and ToS
Focuses on high-quality wallpapers with advanced filtering
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse, urljoin, quote
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests.adapters
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pinterest_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestScraper:
    """High-resolution Pinterest wallpaper scraper with advanced filtering"""
    
    def __init__(self, output_dir: str = "pinterest_cache", headless: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # High-resolution requirements
        self.min_width = 1920
        self.min_height = 1080
        self.preferred_width = 3840  # 4K
        self.preferred_height = 2160  # 4K
        
        # Rate limiting and respect settings
        self.request_delay = 2.0  # Seconds between requests
        self.max_pages = 3  # Limit pages to be respectful
        self.max_images_per_search = 50
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        
        # Setup headless browser for dynamic content
        self.setup_browser(headless)
        
        # Category mapping for better search results
        self.category_keywords = {
            'nature': ['nature wallpaper 4k', 'landscape photography', 'mountain scenery', 'forest wallpaper'],
            'space': ['space wallpaper 4k', 'galaxy background', 'nebula wallpaper', 'astronomy photography'],
            'abstract': ['abstract wallpaper 4k', 'geometric patterns', 'digital art background'],
            'minimal': ['minimal wallpaper 4k', 'clean background', 'simple wallpaper'],
            'cyberpunk': ['cyberpunk wallpaper 4k', 'neon city', 'futuristic background'],
            'gaming': ['gaming wallpaper 4k', 'video game background', 'game art wallpaper'],
            'anime': ['anime wallpaper 4k', 'anime background', 'manga wallpaper'],
            'cars': ['car wallpaper 4k', 'supercar photography', 'automotive wallpaper'],
            'sports': ['sports wallpaper 4k', 'athletic photography', 'stadium background'],
            'technology': ['technology wallpaper 4k', 'tech background', 'circuit board wallpaper'],
            'architecture': ['architecture wallpaper 4k', 'building photography', 'modern architecture'],
            'art': ['art wallpaper 4k', 'digital artwork', 'artistic background'],
            'dark': ['dark wallpaper 4k', 'black background', 'dark aesthetic'],
            'neon': ['neon wallpaper 4k', 'neon lights', 'cyberpunk neon'],
            'pastel': ['pastel wallpaper 4k', 'soft colors', 'pastel aesthetic'],
            'vintage': ['vintage wallpaper 4k', 'retro background', 'old style wallpaper'],
            'gradient': ['gradient wallpaper 4k', 'color gradient', 'smooth gradient background']
        }
    
    def setup_browser(self, headless: bool = True):
        """Setup Chrome browser with optimal settings"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Disable images initially to speed up page loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            logger.error(f"Failed to setup Chrome browser: {e}")
            logger.info("Please ensure Chrome is installed or use a different method")
            sys.exit(1)
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images to avoid duplicates"""
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
    
    def get_image_dimensions(self, image_url: str) -> Tuple[int, int]:
        """Get image dimensions without downloading full image"""
        try:
            response = self.session.head(image_url, timeout=10)
            if response.status_code == 200:
                # Try to get dimensions from URL patterns
                url_lower = image_url.lower()
                
                # Pinterest URL patterns often contain dimensions
                dimension_patterns = [
                    r'(\d{3,4})x(\d{3,4})',  # WIDTHxHEIGHT
                    r'/(\d{3,4})/(\d{3,4})/',  # /WIDTH/HEIGHT/
                ]
                
                for pattern in dimension_patterns:
                    match = re.search(pattern, url_lower)
                    if match:
                        return int(match.group(1)), int(match.group(2))
                
                # If no dimensions in URL, download first few bytes to check
                response = self.session.get(image_url, stream=True, timeout=10)
                response.raise_for_status()
                
                # Read first 2KB to get image header
                chunk = response.raw.read(2048)
                response.close()
                
                # Basic JPEG dimension extraction
                if chunk.startswith(b'\xff\xd8'):  # JPEG
                    # Look for SOF markers
                    sof_markers = [b'\xff\xc0', b'\xff\xc1', b'\xff\xc2']
                    for marker in sof_markers:
                        pos = chunk.find(marker)
                        if pos != -1 and pos + 7 < len(chunk):
                            height = int.from_bytes(chunk[pos+5:pos+7], 'big')
                            width = int.from_bytes(chunk[pos+7:pos+9], 'big')
                            return width, height
                
                # Default assumption for unknown dimensions
                return 1920, 1080
                
        except Exception as e:
            logger.debug(f"Could not get dimensions for {image_url}: {e}")
            return 0, 0
    
    def is_high_resolution(self, image_url: str) -> bool:
        """Check if image meets high-resolution requirements"""
        width, height = self.get_image_dimensions(image_url)
        return width >= self.min_width and height >= self.min_height
    
    def get_highest_resolution_url(self, pin_data: Dict) -> Optional[str]:
        """Extract the highest resolution image URL from Pinterest pin data"""
        try:
            # Pinterest typically provides multiple image sizes
            # Look for common high-res patterns
            high_res_patterns = [
                'originals',
                '736x',
                '564x',
                'full'
            ]
            
            if 'images' in pin_data:
                images = pin_data['images']
                # Look for original or highest quality version
                if 'orig' in images:
                    return images['orig']['url']
                elif '736x' in images:
                    return images['736x']['url']
                elif '564x' in images:
                    return images['564x']['url']
            
            # Fallback to direct image URL modification
            if 'image_url' in pin_data:
                url = pin_data['image_url']
                # Replace size parameters with high-res versions
                url = re.sub(r'/\d+x\d+/', '/originals/', url)
                url = re.sub(r'_\d+x\d+\.', '_originals.', url)
                return url
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting high-res URL: {e}")
            return None
    
    def search_pinterest(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search Pinterest for images using web scraping"""
        logger.info(f"Searching Pinterest for: {query}")
        
        search_url = f"https://www.pinterest.com/search/pins/?q={quote(query)}"
        pins = []
        
        try:
            self.driver.get(search_url)
            time.sleep(3)  # Wait for initial load
            
            # Scroll to load more content
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 5  # Limit scrolling to be respectful
            
            while scroll_attempts < max_scrolls and len(pins) < max_results:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Find pin elements
                pin_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-id="pin"]')
                
                for pin_element in pin_elements:
                    if len(pins) >= max_results:
                        break
                    
                    try:
                        # Extract pin data
                        img_element = pin_element.find_element(By.TAG_NAME, 'img')
                        pin_link = pin_element.find_element(By.CSS_SELECTOR, 'a[href*="/pin/"]')
                        
                        image_url = img_element.get_attribute('src')
                        pin_url = pin_link.get_attribute('href')
                        title = img_element.get_attribute('alt') or f"Pinterest {query} wallpaper"
                        
                        # Get high-resolution version
                        high_res_url = self.get_highest_resolution_url({'image_url': image_url})
                        if not high_res_url:
                            high_res_url = image_url
                        
                        # Check if it meets our resolution requirements
                        if self.is_high_resolution(high_res_url):
                            pin_data = {
                                'id': pin_url.split('/')[-2] if '/pin/' in pin_url else str(time.time()),
                                'title': title,
                                'image_url': high_res_url,
                                'pin_url': pin_url,
                                'query': query,
                                'found_at': datetime.utcnow().isoformat() + 'Z'
                            }
                            pins.append(pin_data)
                            logger.debug(f"Found high-res pin: {title}")
                    
                    except (NoSuchElementException, AttributeError) as e:
                        continue
                
                # Check if page height changed
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1
                
                # Respectful delay between scrolls
                time.sleep(self.request_delay)
        
        except Exception as e:
            logger.error(f"Error searching Pinterest: {e}")
        
        logger.info(f"Found {len(pins)} high-resolution pins for query: {query}")
        return pins
    
    def download_image(self, pin_data: Dict, category: str) -> bool:
        """Download high-resolution image with metadata"""
        try:
            image_url = pin_data['image_url']
            pin_id = pin_data['id']
            
            # Create filename
            filename = f"pinterest_{category}_{pin_id}.jpg"
            
            # Download image
            response = self.session.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {filename}")
                return False
            
            # Verify it's actually high resolution
            width, height = self.get_image_dimensions(image_url)
            if width < self.min_width or height < self.min_height:
                logger.info(f"Image too small ({width}x{height}), skipping: {filename}")
                return False
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create comprehensive metadata
            metadata = {
                'id': pin_id,
                'source': 'pinterest',
                'category': category,
                'title': pin_data['title'],
                'description': f"High-resolution {category} wallpaper from Pinterest",
                'query': pin_data['query'],
                'width': width,
                'height': height,
                'file_size': len(image_data),
                'download_url': image_url,
                'source_url': pin_data['pin_url'],
                'tags': [category, 'high-resolution', '4k', 'wallpaper'],
                'quality_score': self.calculate_quality_score(width, height, len(image_data)),
                'crawled_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update hash tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded high-res image: {filename} ({width}x{height})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {pin_data.get('image_url', 'unknown')}: {e}")
            return False
    
    def calculate_quality_score(self, width: int, height: int, file_size: int) -> float:
        """Calculate quality score based on resolution and file size"""
        # Base score from resolution
        resolution_score = min(1.0, (width * height) / (self.preferred_width * self.preferred_height))
        
        # File size score (larger files generally better quality)
        size_score = min(1.0, file_size / (2 * 1024 * 1024))  # 2MB baseline
        
        # Combined score
        return round((resolution_score * 0.7 + size_score * 0.3) * 10, 2)
    
    def crawl_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Crawl Pinterest for high-resolution wallpapers in a specific category"""
        logger.info(f"Starting Pinterest crawl for category: {category}")
        
        # Get search queries for this category
        queries = self.category_keywords.get(category, [f"{category} wallpaper 4k"])
        
        all_pins = []
        downloaded_images = []
        
        for query in queries:
            if len(downloaded_images) >= limit:
                break
            
            # Search for pins
            pins = self.search_pinterest(query, max_results=limit//len(queries) + 10)
            all_pins.extend(pins)
            
            # Download high-quality images
            for pin in pins:
                if len(downloaded_images) >= limit:
                    break
                
                if self.download_image(pin, category):
                    downloaded_images.append(pin)
                
                # Respectful delay between downloads
                time.sleep(self.request_delay)
        
        # Save crawl summary
        summary = {
            'category': category,
            'queries_used': queries,
            'total_pins_found': len(all_pins),
            'high_res_downloaded': len(downloaded_images),
            'min_resolution': f"{self.min_width}x{self.min_height}",
            'preferred_resolution': f"{self.preferred_width}x{self.preferred_height}",
            'crawl_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / f"pinterest_{category}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()
        
        logger.info(f"Pinterest crawl completed for {category}: {len(downloaded_images)} high-res images")
        return downloaded_images
    
    def cleanup(self):
        """Close browser and cleanup resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description='Pinterest High-Resolution Wallpaper Scraper')
    parser.add_argument('--category', required=True, help='Category to scrape')
    parser.add_argument('--limit', type=int, default=25, help='Max images to download (default: 25)')
    parser.add_argument('--output', default='pinterest_cache', help='Output directory')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--min-width', type=int, default=1920, help='Minimum image width')
    parser.add_argument('--min-height', type=int, default=1080, help='Minimum image height')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = PinterestScraper(args.output, headless=args.headless)
    scraper.min_width = args.min_width
    scraper.min_height = args.min_height
    
    try:
        # Crawl images
        images = scraper.crawl_category(args.category, args.limit)
        
        print(f"\n🎉 Pinterest crawl complete!")
        print(f"📊 Downloaded: {len(images)} high-resolution images")
        print(f"📁 Category: {args.category}")
        print(f"📏 Min resolution: {args.min_width}x{args.min_height}")
        print(f"🔍 Search focus: High-quality wallpapers")
        print(f"\n🔄 Next steps:")
        print(f"1. python scripts/review_images.py --input {args.output}")
        print(f"2. Review and approve high-quality images")
        print(f"3. python scripts/process_approved.py --category {args.category}")
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()