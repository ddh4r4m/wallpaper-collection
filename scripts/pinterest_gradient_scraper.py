#!/usr/bin/env python3
"""
Pinterest Gradient Background Scraper with Enhanced Scrolling
Scrapes abstract gradient backgrounds from Pinterest search results
Implements intelligent scrolling and high-resolution filtering
"""

import os
import sys
import json
import time
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
        logging.FileHandler('pinterest_gradient_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestGradientScraper:
    """Enhanced Pinterest scraper for abstract gradient backgrounds with scrolling"""
    
    def __init__(self, output_dir: str = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/gradient_search"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Target the specific Pinterest search URL
        self.search_url = "https://in.pinterest.com/search/pins/?q=abstract%20gradient%20background&rs=ac&len=13&source_id=ac_li5uWglg&eq=abstract%20grad&etslf=7977"
        
        # High-resolution requirements for mobile wallpapers
        self.min_width = 1080
        self.min_height = 1920  # Mobile wallpaper preferred
        self.preferred_width = 1440
        self.preferred_height = 2560  # Even better mobile resolution
        
        # Enhanced scrolling settings
        self.scroll_pause_time = 4.0  # Wait 4 seconds between scrolls
        self.max_scrolls = 20  # More scrolls to get 40-50 images
        self.target_images = 50  # Target number of images
        self.images_per_scroll = 10  # Expected new images per scroll
        
        # Rate limiting
        self.request_delay = 2.0
        self.download_delay = 1.5
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2
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
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        })
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.seen_urls = set()
        self.load_existing_hashes()
        
        # Setup browser for gradient searching
        self.setup_browser()
        
        # Stats tracking
        self.stats = {
            'scrolls_performed': 0,
            'pins_found': 0,
            'high_res_pins': 0,
            'downloaded_count': 0,
            'duplicates_skipped': 0,
            'low_res_skipped': 0
        }
    
    def setup_browser(self):
        """Setup Chrome browser with optimal settings for Pinterest"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for better performance
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Allow images to load for proper extraction
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Browser setup complete")
        except Exception as e:
            logger.error(f"Failed to setup Chrome browser: {e}")
            sys.exit(1)
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images to avoid duplicates"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
                logger.info(f"Loaded {len(self.downloaded_hashes)} existing image hashes")
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
    
    def extract_high_res_url(self, image_url: str) -> str:
        """Convert Pinterest image URL to highest resolution version"""
        try:
            # Pinterest URL patterns for high resolution
            high_res_patterns = [
                (r'/236x/', '/originals/'),  # 236x to originals
                (r'/474x/', '/originals/'),  # 474x to originals
                (r'/564x/', '/originals/'),  # 564x to originals
                (r'/736x/', '/originals/'),  # 736x to originals
                (r'_236\.', '_originals.'),  # _236 to _originals
                (r'_474\.', '_originals.'),  # _474 to _originals
                (r'_564\.', '_originals.'),  # _564 to _originals
                (r'_736\.', '_originals.'),  # _736 to _originals
            ]
            
            high_res_url = image_url
            for pattern, replacement in high_res_patterns:
                high_res_url = re.sub(pattern, replacement, high_res_url)
            
            return high_res_url
        except Exception as e:
            logger.debug(f"Error extracting high-res URL: {e}")
            return image_url
    
    def get_image_dimensions(self, image_url: str) -> Tuple[int, int]:
        """Get image dimensions from URL or by downloading headers"""
        try:
            # Try to extract dimensions from URL first
            dimension_patterns = [
                r'/(\d{3,4})x(\d{3,4})/',  # /WIDTHxHEIGHT/
                r'_(\d{3,4})x(\d{3,4})\.',  # _WIDTHxHEIGHT.
                r'(\d{3,4})x(\d{3,4})',     # WIDTHxHEIGHT anywhere
            ]
            
            for pattern in dimension_patterns:
                match = re.search(pattern, image_url)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    if width > 100 and height > 100:  # Sanity check
                        return width, height
            
            # If URL doesn't contain dimensions, try HEAD request
            response = self.session.head(image_url, timeout=10)
            if response.status_code == 200:
                # For originals URLs, assume high resolution
                if 'originals' in image_url:
                    return 1440, 2560  # Assume mobile wallpaper resolution
                elif any(size in image_url for size in ['736x', '564x']):
                    return 1080, 1920  # Good mobile resolution
            
            return 800, 600  # Default fallback
            
        except Exception as e:
            logger.debug(f"Could not get dimensions for {image_url}: {e}")
            return 0, 0
    
    def is_high_resolution(self, image_url: str) -> bool:
        """Check if image meets high-resolution requirements"""
        width, height = self.get_image_dimensions(image_url)
        
        # Check for mobile wallpaper dimensions (vertical or square)
        mobile_criteria = (
            (width >= self.min_width and height >= self.min_height) or  # Standard mobile
            (height >= self.min_width and width >= self.min_height) or  # Landscape mobile
            (width >= 1200 and height >= 1200)  # High-res square
        )
        
        return mobile_criteria
    
    def scroll_and_extract_pins(self) -> List[Dict]:
        """Enhanced scrolling to extract pins with proper wait times"""
        logger.info(f"Starting enhanced scrolling extraction from: {self.search_url}")
        
        try:
            # Navigate to search URL
            self.driver.get(self.search_url)
            time.sleep(5)  # Initial wait for page load
            
            all_pins = []
            scroll_count = 0
            last_pin_count = 0
            consecutive_no_new_pins = 0
            
            while scroll_count < self.max_scrolls and len(all_pins) < self.target_images:
                logger.info(f"Scroll {scroll_count + 1}/{self.max_scrolls} - Current pins: {len(all_pins)}")
                
                # Extract current pins
                current_pins = self.extract_pins_from_page()
                new_pins = [pin for pin in current_pins if pin['image_url'] not in self.seen_urls]
                
                # Add new pins
                for pin in new_pins:
                    self.seen_urls.add(pin['image_url'])
                    all_pins.append(pin)
                
                logger.info(f"Found {len(new_pins)} new pins this scroll")
                
                # Check if we're getting new content
                if len(all_pins) == last_pin_count:
                    consecutive_no_new_pins += 1
                    if consecutive_no_new_pins >= 3:
                        logger.info("No new pins found for 3 consecutive scrolls, stopping")
                        break
                else:
                    consecutive_no_new_pins = 0
                
                last_pin_count = len(all_pins)
                
                # Perform scroll - scroll multiple times per iteration
                for micro_scroll in range(3):
                    self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
                    time.sleep(1)
                
                # Main wait for content to load
                time.sleep(self.scroll_pause_time)
                
                # Additional scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                scroll_count += 1
                self.stats['scrolls_performed'] = scroll_count
            
            logger.info(f"Scrolling complete! Found {len(all_pins)} total pins after {scroll_count} scrolls")
            return all_pins
            
        except Exception as e:
            logger.error(f"Error during scrolling extraction: {e}")
            return []
    
    def extract_pins_from_page(self) -> List[Dict]:
        """Extract pin data from current page state"""
        pins = []
        
        try:
            # Multiple selectors to find Pinterest pins
            pin_selectors = [
                '[data-test-id="pin"]',
                '[data-test-id="pinWrapper"]',
                'div[role="listitem"]',
                '.ReactVirtualized__Grid__innerScrollContainer > div'
            ]
            
            pin_elements = []
            for selector in pin_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    pin_elements = elements
                    logger.debug(f"Found {len(elements)} pins using selector: {selector}")
                    break
            
            if not pin_elements:
                logger.warning("No pin elements found with any selector")
                return pins
            
            for element in pin_elements:
                try:
                    # Extract image element
                    img_element = element.find_element(By.TAG_NAME, 'img')
                    image_url = img_element.get_attribute('src')
                    
                    if not image_url:
                        continue
                    
                    # Skip if already seen
                    if image_url in self.seen_urls:
                        continue
                    
                    # Extract pin URL
                    pin_url = None
                    try:
                        pin_link = element.find_element(By.CSS_SELECTOR, 'a[href*="/pin/"]')
                        pin_url = pin_link.get_attribute('href')
                    except NoSuchElementException:
                        pin_url = f"pinterest_gradient_{len(pins)}"
                    
                    # Extract title/alt text
                    title = img_element.get_attribute('alt') or f"Abstract Gradient Background {len(pins)}"
                    
                    # Get high-resolution version
                    high_res_url = self.extract_high_res_url(image_url)
                    
                    pin_data = {
                        'id': pin_url.split('/')[-2] if '/pin/' in str(pin_url) else f"gradient_{int(time.time())}_{len(pins)}",
                        'title': title,
                        'image_url': high_res_url,
                        'original_url': image_url,
                        'pin_url': pin_url,
                        'found_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    pins.append(pin_data)
                    
                except (NoSuchElementException, AttributeError) as e:
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting pin data: {e}")
                    continue
            
            self.stats['pins_found'] = len(pins)
            return pins
            
        except Exception as e:
            logger.error(f"Error extracting pins from page: {e}")
            return pins
    
    def download_image(self, pin_data: Dict) -> bool:
        """Download high-resolution image with metadata"""
        try:
            image_url = pin_data['image_url']
            pin_id = pin_data['id']
            
            # Check resolution first
            if not self.is_high_resolution(image_url):
                logger.info(f"Image too low resolution, skipping: {pin_id}")
                self.stats['low_res_skipped'] += 1
                return False
            
            # Create filename
            filename = f"pinterest_gradient_{pin_id}.jpg"
            
            # Download image
            response = self.session.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {filename}")
                self.stats['duplicates_skipped'] += 1
                return False
            
            # Get actual dimensions
            width, height = self.get_image_dimensions(image_url)
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create comprehensive metadata
            metadata = {
                'id': pin_id,
                'source': 'pinterest',
                'search_url': self.search_url,
                'category': 'gradient',
                'subcategory': 'abstract_gradient_background',
                'title': pin_data['title'],
                'description': "High-resolution abstract gradient background wallpaper from Pinterest",
                'width': width,
                'height': height,
                'file_size': len(image_data),
                'download_url': image_url,
                'original_url': pin_data['original_url'],
                'source_url': pin_data['pin_url'],
                'tags': ['gradient', 'abstract', 'background', 'wallpaper', 'mobile', 'high-resolution'],
                'quality_score': self.calculate_quality_score(width, height, len(image_data)),
                'mobile_optimized': width >= self.min_width and height >= self.min_height,
                'crawled_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update hash tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            self.stats['downloaded_count'] += 1
            self.stats['high_res_pins'] += 1
            
            logger.info(f"Downloaded: {filename} ({width}x{height}, {len(image_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {pin_data.get('image_url', 'unknown')}: {e}")
            return False
    
    def calculate_quality_score(self, width: int, height: int, file_size: int) -> float:
        """Calculate quality score based on resolution and file size"""
        # Resolution score (mobile wallpaper optimized)
        target_pixels = self.preferred_width * self.preferred_height
        actual_pixels = width * height
        resolution_score = min(1.0, actual_pixels / target_pixels)
        
        # File size score (larger files generally better quality)
        target_size = 1.5 * 1024 * 1024  # 1.5MB baseline for gradients
        size_score = min(1.0, file_size / target_size)
        
        # Mobile aspect ratio bonus
        aspect_ratio = height / width if width > 0 else 0
        mobile_bonus = 1.0 if 1.5 <= aspect_ratio <= 2.5 else 0.8
        
        # Combined score
        return round((resolution_score * 0.5 + size_score * 0.3 + mobile_bonus * 0.2) * 10, 2)
    
    def run_gradient_scraping(self) -> Dict:
        """Run the complete gradient scraping process"""
        logger.info("🎨 Starting Pinterest gradient background scraping")
        logger.info(f"Target: {self.target_images} high-quality gradient images")
        logger.info(f"Search URL: {self.search_url}")
        
        start_time = time.time()
        
        try:
            # Phase 1: Scroll and extract pins
            logger.info("Phase 1: Scrolling and extracting pins...")
            all_pins = self.scroll_and_extract_pins()
            
            if not all_pins:
                logger.error("No pins found during scrolling")
                return self.get_final_stats(start_time)
            
            logger.info(f"Found {len(all_pins)} total pins")
            
            # Phase 2: Filter for high-resolution pins
            logger.info("Phase 2: Filtering for high-resolution pins...")
            high_res_pins = []
            for pin in all_pins:
                if self.is_high_resolution(pin['image_url']):
                    high_res_pins.append(pin)
            
            logger.info(f"Found {len(high_res_pins)} high-resolution pins")
            
            # Phase 3: Download high-quality images
            logger.info("Phase 3: Downloading high-quality images...")
            downloaded_images = []
            
            for pin in high_res_pins:
                if len(downloaded_images) >= self.target_images:
                    break
                
                if self.download_image(pin):
                    downloaded_images.append(pin)
                
                # Respectful delay between downloads
                time.sleep(self.download_delay)
            
            # Save final state
            self.save_downloaded_hashes()
            
            # Generate summary
            final_stats = self.get_final_stats(start_time)
            self.save_crawl_summary(final_stats, all_pins, high_res_pins, downloaded_images)
            
            logger.info("🎉 Pinterest gradient scraping completed!")
            return final_stats
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            return self.get_final_stats(start_time)
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return self.get_final_stats(start_time)
        finally:
            self.cleanup()
    
    def get_final_stats(self, start_time: float) -> Dict:
        """Generate final statistics"""
        duration = time.time() - start_time
        return {
            'duration_seconds': round(duration, 2),
            'scrolls_performed': self.stats['scrolls_performed'],
            'total_pins_found': self.stats['pins_found'],
            'high_res_pins': self.stats['high_res_pins'],
            'downloaded_count': self.stats['downloaded_count'],
            'duplicates_skipped': self.stats['duplicates_skipped'],
            'low_res_skipped': self.stats['low_res_skipped'],
            'success_rate': round((self.stats['downloaded_count'] / max(1, self.stats['pins_found'])) * 100, 2),
            'target_achieved': self.stats['downloaded_count'] >= self.target_images * 0.8
        }
    
    def save_crawl_summary(self, stats: Dict, all_pins: List, high_res_pins: List, downloaded_images: List):
        """Save comprehensive crawl summary"""
        summary = {
            'search_url': self.search_url,
            'scraping_stats': stats,
            'requirements': {
                'min_width': self.min_width,
                'min_height': self.min_height,
                'preferred_width': self.preferred_width,
                'preferred_height': self.preferred_height,
                'target_images': self.target_images
            },
            'downloaded_files': [
                {
                    'filename': f"pinterest_gradient_{img['id']}.jpg",
                    'title': img['title'],
                    'image_url': img['image_url']
                } for img in downloaded_images
            ],
            'high_quality_urls': [pin['image_url'] for pin in high_res_pins[:10]],  # Top 10
            'crawl_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / 'pinterest_gradient_crawl_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Crawl summary saved: {summary_file}")
    
    def cleanup(self):
        """Close browser and cleanup resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

def main():
    """Main execution function"""
    scraper = PinterestGradientScraper()
    
    try:
        stats = scraper.run_gradient_scraping()
        
        print(f"\n🎨 Pinterest Gradient Scraping Complete!")
        print(f"📊 Total Images Downloaded: {stats['downloaded_count']}")
        print(f"🔄 Scrolls Performed: {stats['scrolls_performed']}")
        print(f"📍 Total Pins Found: {stats['total_pins_found']}")
        print(f"📏 High-Resolution Pins: {stats['high_res_pins']}")
        print(f"⏱️  Duration: {stats['duration_seconds']} seconds")
        print(f"✅ Success Rate: {stats['success_rate']}%")
        print(f"🎯 Target Achieved: {'Yes' if stats['target_achieved'] else 'No'}")
        
        if stats['downloaded_count'] > 0:
            print(f"\n📁 Images saved to: {scraper.output_dir}")
            print(f"🔍 High-quality gradient backgrounds ready for review")
            
            # List some downloaded files
            image_files = list(scraper.output_dir.glob("*.jpg"))
            if image_files:
                print(f"\n📋 Sample downloaded files:")
                for img_file in image_files[:5]:  # Show first 5
                    print(f"   - {img_file.name}")
                if len(image_files) > 5:
                    print(f"   ... and {len(image_files) - 5} more")
        
        print(f"\n🔄 Next steps:")
        print(f"1. Review downloaded images in: {scraper.output_dir}")
        print(f"2. Use quality assessment: python scripts/review_images.py")
        print(f"3. Process approved images for the wallpaper collection")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()