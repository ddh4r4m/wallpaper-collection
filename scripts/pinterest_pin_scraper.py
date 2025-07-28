#!/usr/bin/env python3
"""
Pinterest Specific Pin Scraper Agent 2
Scrapes specific Pinterest pins and their related content for gradient wallpapers
Handles individual pin URLs and extracts "More like this" suggestions
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests.adapters
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pinterest_pin_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestPinScraper:
    """Specialized scraper for individual Pinterest pins and their related content"""
    
    def __init__(self, output_dir: str = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/specific_pins"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Target specific pin URLs
        self.target_pins = [
            "https://in.pinterest.com/pin/4081455906953894/",
            "https://in.pinterest.com/pin/281543725129330/",
            "https://in.pinterest.com/pin/14003448837374227/",
            "https://in.pinterest.com/pin/985231164541094/"
        ]
        
        # High-resolution requirements for mobile wallpapers
        self.min_width = 1080
        self.min_height = 1920  # Mobile wallpaper preferred
        self.preferred_width = 1440
        self.preferred_height = 2560  # Even better mobile resolution
        
        # Rate limiting
        self.pin_visit_delay = 8.0  # Wait 8 seconds between pin visits
        self.related_scroll_delay = 3.0  # Wait for related pins to load
        self.download_delay = 2.0
        
        # Target settings
        self.target_images_per_pin = 10  # Main pin + related
        self.max_related_per_pin = 15   # Maximum related pins to extract
        self.total_target = 40          # Total target across all pins
        
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
        
        # Setup browser
        self.setup_browser()
        
        # Stats tracking
        self.stats = {
            'pins_processed': 0,
            'main_pins_extracted': 0,
            'related_pins_found': 0,
            'high_res_images': 0,
            'downloaded_count': 0,
            'duplicates_skipped': 0,
            'low_res_skipped': 0,
            'failed_downloads': 0
        }
    
    def setup_browser(self):
        """Setup Chrome browser with optimal settings for Pinterest pin viewing"""
        chrome_options = Options()
        # Don't use headless for pin scraping - Pinterest may detect it
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
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Browser setup complete for pin scraping")
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
    
    def scrape_individual_pin(self, pin_url: str) -> Dict:
        """Scrape a specific Pinterest pin and its related content"""
        logger.info(f"Processing pin: {pin_url}")
        pin_data = {
            'pin_url': pin_url,
            'main_image': None,
            'related_pins': [],
            'total_images_found': 0,
            'high_res_found': 0,
            'downloaded_images': []
        }
        
        try:
            # Navigate to the pin
            self.driver.get(pin_url)
            time.sleep(5)  # Wait for page load
            
            # Extract main pin image
            main_image = self.extract_main_pin_image(pin_url)
            if main_image:
                pin_data['main_image'] = main_image
                pin_data['total_images_found'] += 1
                self.stats['main_pins_extracted'] += 1
                
                # Download main image if high resolution
                if self.is_high_resolution(main_image['image_url']):
                    pin_data['high_res_found'] += 1
                    if self.download_pin_image(main_image, pin_url, 'main'):
                        pin_data['downloaded_images'].append(main_image)
            
            # Scroll down to load related pins section
            self.scroll_to_related_pins()
            
            # Extract related pins
            related_pins = self.extract_related_pins(pin_url)
            pin_data['related_pins'] = related_pins
            pin_data['total_images_found'] += len(related_pins)
            self.stats['related_pins_found'] += len(related_pins)
            
            # Download high-resolution related pins
            for i, related_pin in enumerate(related_pins):
                if len(pin_data['downloaded_images']) >= self.target_images_per_pin:
                    break
                
                if self.is_high_resolution(related_pin['image_url']):
                    pin_data['high_res_found'] += 1
                    if self.download_pin_image(related_pin, pin_url, f'related_{i}'):
                        pin_data['downloaded_images'].append(related_pin)
                
                time.sleep(1)  # Small delay between downloads
            
            logger.info(f"Pin processed: {len(pin_data['downloaded_images'])} images downloaded")
            return pin_data
            
        except Exception as e:
            logger.error(f"Error processing pin {pin_url}: {e}")
            return pin_data
    
    def extract_main_pin_image(self, pin_url: str) -> Optional[Dict]:
        """Extract the main image from a Pinterest pin"""
        try:
            # Multiple selectors for main pin image
            main_img_selectors = [
                'img[alt*="gradient"]',
                'img[alt*="background"]',
                'img[alt*="wallpaper"]',
                '[data-test-id="pin-closeup-image"] img',
                '[data-test-id="visual-content-container"] img',
                'div[role="img"] img',
                'img[src*="originals"]',
                'img[src*="736x"]'
            ]
            
            main_img_element = None
            for selector in main_img_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Get the largest image
                        main_img_element = max(elements, key=lambda elem: self.get_element_size(elem))
                        break
                except NoSuchElementException:
                    continue
            
            if not main_img_element:
                # Fallback to any large image
                images = self.driver.find_elements(By.TAG_NAME, 'img')
                if images:
                    main_img_element = max(images, key=lambda elem: self.get_element_size(elem))
            
            if main_img_element:
                image_url = main_img_element.get_attribute('src')
                if image_url and image_url not in self.seen_urls:
                    self.seen_urls.add(image_url)
                    
                    # Extract pin ID from URL
                    pin_id = pin_url.split('/')[-2] if '/pin/' in pin_url else f"pin_{int(time.time())}"
                    
                    # Get high-resolution version
                    high_res_url = self.extract_high_res_url(image_url)
                    
                    return {
                        'id': f"{pin_id}_main",
                        'title': main_img_element.get_attribute('alt') or f"Gradient Pin {pin_id}",
                        'image_url': high_res_url,
                        'original_url': image_url,
                        'pin_url': pin_url,
                        'type': 'main_pin',
                        'found_at': datetime.utcnow().isoformat() + 'Z'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting main pin image: {e}")
            return None
    
    def get_element_size(self, element) -> int:
        """Get approximate element size for comparison"""
        try:
            size = element.size
            return size.get('width', 0) * size.get('height', 0)
        except:
            return 0
    
    def scroll_to_related_pins(self):
        """Scroll down to load the related pins section"""
        try:
            # Scroll down to load more content
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(self.related_scroll_delay)
            
            # Look for "More like this" or related pins section
            related_selectors = [
                '[data-test-id="more-ideas"]',
                '[data-test-id="related-pins"]',
                'h3:contains("More like this")',
                'h3:contains("More ideas")',
                'div[aria-label="More ideas"]'
            ]
            
            for selector in related_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(2)
                    break
                except NoSuchElementException:
                    continue
            
            # Additional scroll to load more related content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
        except Exception as e:
            logger.debug(f"Error scrolling to related pins: {e}")
    
    def extract_related_pins(self, source_pin_url: str) -> List[Dict]:
        """Extract related/similar pins from the page"""
        related_pins = []
        
        try:
            # Selectors for related pin containers
            related_containers = [
                '[data-test-id="more-ideas"] [data-test-id="pin"]',
                '[data-test-id="related-pins"] [data-test-id="pin"]',
                'div[role="listitem"] img',
                '.ReactVirtualized__Grid__innerScrollContainer img'
            ]
            
            pin_elements = []
            for selector in related_containers:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    pin_elements.extend(elements[:self.max_related_per_pin])
                    break
            
            # If no specific related section found, get other images on page
            if not pin_elements:
                all_images = self.driver.find_elements(By.TAG_NAME, 'img')
                # Filter out small images (likely thumbnails or icons)
                pin_elements = [img for img in all_images if self.get_element_size(img) > 10000][:self.max_related_per_pin]
            
            logger.info(f"Found {len(pin_elements)} potential related pins")
            
            for i, element in enumerate(pin_elements):
                try:
                    if isinstance(element, type(element)) and element.tag_name == 'img':
                        img_element = element
                    else:
                        img_element = element.find_element(By.TAG_NAME, 'img')
                    
                    image_url = img_element.get_attribute('src')
                    if not image_url or image_url in self.seen_urls:
                        continue
                    
                    self.seen_urls.add(image_url)
                    
                    # Try to get related pin URL
                    related_pin_url = None
                    try:
                        parent = img_element.find_element(By.XPATH, './ancestor::a[@href]')
                        related_pin_url = parent.get_attribute('href')
                    except NoSuchElementException:
                        related_pin_url = f"{source_pin_url}#related_{i}"
                    
                    # Extract pin ID
                    pin_id = related_pin_url.split('/')[-2] if '/pin/' in str(related_pin_url) else f"related_{i}"
                    
                    # Get high-resolution version
                    high_res_url = self.extract_high_res_url(image_url)
                    
                    related_pin = {
                        'id': f"{pin_id}_related_{i}",
                        'title': img_element.get_attribute('alt') or f"Related Gradient {i}",
                        'image_url': high_res_url,
                        'original_url': image_url,
                        'pin_url': related_pin_url,
                        'source_pin': source_pin_url,
                        'type': 'related_pin',
                        'found_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    related_pins.append(related_pin)
                    
                    if len(related_pins) >= self.max_related_per_pin:
                        break
                
                except Exception as e:
                    logger.debug(f"Error extracting related pin {i}: {e}")
                    continue
            
            logger.info(f"Extracted {len(related_pins)} related pins")
            return related_pins
            
        except Exception as e:
            logger.error(f"Error extracting related pins: {e}")
            return related_pins
    
    def download_pin_image(self, pin_data: Dict, source_pin_url: str, image_type: str) -> bool:
        """Download an image from a pin with metadata"""
        try:
            image_url = pin_data['image_url']
            pin_id = pin_data['id']
            
            # Create filename with source pin info
            source_id = source_pin_url.split('/')[-2] if '/pin/' in source_pin_url else 'unknown'
            filename = f"pin_{source_id}_{image_type}_{pin_id}.jpg"
            
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
                'source': 'pinterest_pin',
                'source_pin_url': source_pin_url,
                'category': 'gradient',
                'subcategory': 'specific_pin_collection',
                'image_type': image_type,  # 'main' or 'related_X'
                'title': pin_data['title'],
                'description': f"High-resolution gradient image from Pinterest pin collection - {image_type}",
                'width': width,
                'height': height,
                'file_size': len(image_data),
                'download_url': image_url,
                'original_url': pin_data.get('original_url', image_url),
                'pin_url': pin_data['pin_url'],
                'tags': ['gradient', 'abstract', 'background', 'wallpaper', 'pinterest', 'mobile', 'high-resolution'],
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
            self.stats['high_res_images'] += 1
            
            logger.info(f"Downloaded: {filename} ({width}x{height}, {len(image_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {pin_data.get('image_url', 'unknown')}: {e}")
            self.stats['failed_downloads'] += 1
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
    
    def run_pin_scraping(self) -> Dict:
        """Run the complete pin scraping process"""
        logger.info("🎯 Starting Pinterest Specific Pin Scraping (Agent 2)")
        logger.info(f"Target pins: {len(self.target_pins)}")
        logger.info(f"Goal: {self.total_target} high-quality gradient images")
        
        start_time = time.time()
        all_pin_data = []
        
        try:
            for i, pin_url in enumerate(self.target_pins):
                logger.info(f"\n📌 Processing pin {i+1}/{len(self.target_pins)}: {pin_url}")
                
                pin_data = self.scrape_individual_pin(pin_url)
                all_pin_data.append(pin_data)
                self.stats['pins_processed'] += 1
                
                # Log progress
                logger.info(f"Pin {i+1} results: {len(pin_data['downloaded_images'])} images downloaded")
                logger.info(f"Total downloaded so far: {self.stats['downloaded_count']}")
                
                # Check if we've reached our target
                if self.stats['downloaded_count'] >= self.total_target:
                    logger.info(f"Target of {self.total_target} images reached!")
                    break
                
                # Rate limiting between pins
                if i < len(self.target_pins) - 1:
                    logger.info(f"Waiting {self.pin_visit_delay} seconds before next pin...")
                    time.sleep(self.pin_visit_delay)
            
            # Save final state
            self.save_downloaded_hashes()
            
            # Generate summary
            final_stats = self.get_final_stats(start_time)
            self.save_pin_scraping_summary(final_stats, all_pin_data)
            
            logger.info("🎉 Pinterest pin scraping completed!")
            return final_stats
            
        except KeyboardInterrupt:
            logger.info("Pin scraping interrupted by user")
            return self.get_final_stats(start_time)
        except Exception as e:
            logger.error(f"Pin scraping failed: {e}")
            return self.get_final_stats(start_time)
        finally:
            self.cleanup()
    
    def get_final_stats(self, start_time: float) -> Dict:
        """Generate final statistics"""
        duration = time.time() - start_time
        return {
            'duration_seconds': round(duration, 2),
            'pins_processed': self.stats['pins_processed'],
            'main_pins_extracted': self.stats['main_pins_extracted'],
            'related_pins_found': self.stats['related_pins_found'],
            'high_res_images': self.stats['high_res_images'],
            'downloaded_count': self.stats['downloaded_count'],
            'duplicates_skipped': self.stats['duplicates_skipped'],
            'low_res_skipped': self.stats['low_res_skipped'],
            'failed_downloads': self.stats['failed_downloads'],
            'success_rate': round((self.stats['downloaded_count'] / max(1, self.stats['high_res_images'])) * 100, 2),
            'target_achieved': self.stats['downloaded_count'] >= self.total_target * 0.8
        }
    
    def save_pin_scraping_summary(self, stats: Dict, all_pin_data: List):
        """Save comprehensive pin scraping summary"""
        summary = {
            'scraping_type': 'specific_pinterest_pins',
            'target_pins': self.target_pins,
            'scraping_stats': stats,
            'requirements': {
                'min_width': self.min_width,
                'min_height': self.min_height,
                'preferred_width': self.preferred_width,
                'preferred_height': self.preferred_height,
                'total_target': self.total_target,
                'target_per_pin': self.target_images_per_pin
            },
            'pin_results': [
                {
                    'pin_url': pin['pin_url'],
                    'total_found': pin['total_images_found'],
                    'high_res_found': pin['high_res_found'],
                    'downloaded': len(pin['downloaded_images']),
                    'main_image_downloaded': pin['main_image'] is not None and any(
                        img['type'] == 'main_pin' for img in pin['downloaded_images']
                    ),
                    'related_pins_found': len(pin['related_pins'])
                } for pin in all_pin_data
            ],
            'download_summary': {
                'total_images': self.stats['downloaded_count'],
                'main_pin_images': sum(1 for pin in all_pin_data for img in pin['downloaded_images'] if img.get('type') == 'main_pin'),
                'related_images': sum(1 for pin in all_pin_data for img in pin['downloaded_images'] if img.get('type') == 'related_pin')
            },
            'crawl_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / 'pinterest_pin_scraping_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Pin scraping summary saved: {summary_file}")
    
    def cleanup(self):
        """Close browser and cleanup resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

def main():
    """Main execution function"""
    scraper = PinterestPinScraper()
    
    try:
        stats = scraper.run_pin_scraping()
        
        print(f"\n🎯 Pinterest Pin Scraping Complete (Agent 2)!")
        print(f"📌 Pins Processed: {stats['pins_processed']}/4")
        print(f"🖼️  Main Pin Images: {stats['main_pins_extracted']}")
        print(f"🔗 Related Pins Found: {stats['related_pins_found']}")
        print(f"📊 Total Images Downloaded: {stats['downloaded_count']}")
        print(f"📏 High-Resolution Images: {stats['high_res_images']}")
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
        print(f"❌ Pin scraping failed: {e}")

if __name__ == "__main__":
    main()