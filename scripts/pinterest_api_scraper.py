#!/usr/bin/env python3
"""
Pinterest API Scraper with Automatic API Generation
Scrapes Pinterest images and automatically generates API endpoints with pagination
Integrates with the existing wallpaper collection structure
"""

import os
import sys
import json
import time
import requests
import hashlib
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlparse, quote
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import re
from PIL import Image
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
        logging.FileHandler('pinterest_api_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestAPIScraper:
    """Pinterest scraper with automatic API generation and pagination"""
    
    def __init__(self):
        # Project paths
        self.project_root = Path("/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection")
        self.collection_root = self.project_root / "collection"
        self.wallpapers_dir = self.collection_root / "wallpapers"
        self.thumbnails_dir = self.collection_root / "thumbnails"
        self.api_dir = self.collection_root / "api" / "v1"
        
        # Ensure directories exist
        self.wallpapers_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.api_dir.mkdir(parents=True, exist_ok=True)
        
        # Temp directory for processing
        self.temp_dir = self.project_root / "temp_scrape"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Image requirements
        self.min_width = 800
        self.min_height = 1200  # Mobile optimized
        self.preferred_width = 1080
        self.preferred_height = 1920
        
        # Rate limiting
        self.request_delay = 2.0
        self.download_delay = 1.5
        self.max_scrolls = 15
        
        # Setup session
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
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Tracking
        self.downloaded_hashes = set()
        self.seen_urls = set()
        
        # Setup browser
        self.setup_browser()
        
        # Stats
        self.stats = {
            'pins_found': 0,
            'high_res_pins': 0,
            'downloaded_count': 0,
            'duplicates_skipped': 0,
            'low_res_skipped': 0,
            'api_generated': False,
            'pagination_generated': False
        }
    
    def setup_browser(self):
        """Setup Chrome browser with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Allow images to load
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
    
    def get_user_input(self) -> Dict:
        """Get scraping parameters from user"""
        print("\n🎨 Pinterest API Scraper")
        print("=" * 50)
        
        # Get Pinterest URL
        while True:
            url = input("📌 Pinterest URL (search/board/user): ").strip()
            if url and ('pinterest.com' in url):
                break
            print("❌ Please enter a valid Pinterest URL")
        
        # Get category
        while True:
            category = input("📂 Category name (e.g., gradient, nature, gaming): ").strip().lower()
            if category and category.replace('_', '').isalnum():
                break
            print("❌ Please enter a valid category name (letters, numbers, underscore only)")
        
        # Get quantity
        while True:
            try:
                quantity = int(input("🔢 Number of images to scrape (1-100): ").strip())
                if 1 <= quantity <= 100:
                    break
                print("❌ Please enter a number between 1 and 100")
            except ValueError:
                print("❌ Please enter a valid number")
        
        return {
            'url': url,
            'category': category,
            'quantity': quantity
        }
    
    def extract_high_res_url(self, image_url: str) -> str:
        """Convert Pinterest image URL to highest resolution version"""
        try:
            high_res_patterns = [
                (r'/236x/', '/originals/'),
                (r'/474x/', '/originals/'),
                (r'/564x/', '/originals/'),
                (r'/736x/', '/originals/'),
                (r'_236\.', '_originals.'),
                (r'_474\.', '_originals.'),
                (r'_564\.', '_originals.'),
                (r'_736\.', '_originals.'),
            ]
            
            high_res_url = image_url
            for pattern, replacement in high_res_patterns:
                high_res_url = re.sub(pattern, replacement, high_res_url)
            
            return high_res_url
        except Exception as e:
            logger.debug(f"Error extracting high-res URL: {e}")
            return image_url
    
    def get_image_dimensions_from_file(self, filepath: Path) -> Tuple[int, int]:
        """Get actual image dimensions from file"""
        try:
            with Image.open(filepath) as img:
                return img.size  # Returns (width, height)
        except Exception as e:
            logger.debug(f"Could not get dimensions from {filepath}: {e}")
            return 0, 0
    
    def is_high_resolution(self, width: int, height: int) -> bool:
        """Check if image meets high-resolution requirements"""
        return (width >= self.min_width and height >= self.min_height) or \
               (height >= self.min_width and width >= self.min_height)
    
    def scrape_pinterest_url(self, url: str, quantity: int) -> List[Dict]:
        """Scrape images from Pinterest URL"""
        logger.info(f"Starting Pinterest scrape from: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Initial wait
            
            all_pins = []
            scroll_count = 0
            consecutive_no_new = 0
            
            while scroll_count < self.max_scrolls and len(all_pins) < quantity:
                logger.info(f"Scroll {scroll_count + 1}/{self.max_scrolls} - Pins found: {len(all_pins)}")
                
                # Extract pins from current page
                current_pins = self.extract_pins_from_page()
                new_pins = [pin for pin in current_pins if pin['image_url'] not in self.seen_urls]
                
                # Add new pins
                for pin in new_pins:
                    if len(all_pins) >= quantity:
                        break
                    self.seen_urls.add(pin['image_url'])
                    all_pins.append(pin)
                
                logger.info(f"Found {len(new_pins)} new pins this scroll")
                
                # Check for new content
                if len(new_pins) == 0:
                    consecutive_no_new += 1
                    if consecutive_no_new >= 3:
                        logger.info("No new pins for 3 scrolls, stopping")
                        break
                else:
                    consecutive_no_new = 0
                
                # Scroll page
                for micro_scroll in range(3):
                    self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
                    time.sleep(1)
                
                time.sleep(self.request_delay)
                scroll_count += 1
            
            self.stats['pins_found'] = len(all_pins)
            logger.info(f"Pinterest scraping complete! Found {len(all_pins)} pins")
            return all_pins
            
        except Exception as e:
            logger.error(f"Error scraping Pinterest: {e}")
            return []
    
    def extract_pins_from_page(self) -> List[Dict]:
        """Extract pin data from current page"""
        pins = []
        
        try:
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
                    break
            
            for element in pin_elements:
                try:
                    img_element = element.find_element(By.TAG_NAME, 'img')
                    image_url = img_element.get_attribute('src')
                    
                    if not image_url or image_url in self.seen_urls:
                        continue
                    
                    # Get pin URL
                    pin_url = None
                    try:
                        pin_link = element.find_element(By.CSS_SELECTOR, 'a[href*="/pin/"]')
                        pin_url = pin_link.get_attribute('href')
                    except NoSuchElementException:
                        pin_url = f"pinterest_pin_{len(pins)}"
                    
                    # Get title
                    title = img_element.get_attribute('alt') or f"Pinterest Image {len(pins)}"
                    
                    # Get high-resolution version
                    high_res_url = self.extract_high_res_url(image_url)
                    
                    pin_data = {
                        'id': pin_url.split('/')[-2] if '/pin/' in str(pin_url) else f"pin_{int(time.time())}_{len(pins)}",
                        'title': title,
                        'image_url': high_res_url,
                        'original_url': image_url,
                        'pin_url': pin_url,
                        'found_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    pins.append(pin_data)
                    
                except (NoSuchElementException, AttributeError):
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting pin: {e}")
                    continue
            
            return pins
            
        except Exception as e:
            logger.error(f"Error extracting pins from page: {e}")
            return []
    
    def download_and_process_images(self, pins: List[Dict], category: str) -> List[Dict]:
        """Download images and process them"""
        logger.info(f"Starting download of {len(pins)} images for category: {category}")
        
        downloaded_images = []
        
        # Create category directories
        category_wallpaper_dir = self.wallpapers_dir / category
        category_thumbnail_dir = self.thumbnails_dir / category
        category_wallpaper_dir.mkdir(exist_ok=True)
        category_thumbnail_dir.mkdir(exist_ok=True)
        
        # Get next sequential number
        existing_files = list(category_wallpaper_dir.glob("*.jpg"))
        next_number = len(existing_files) + 1
        
        for pin in pins:
            if len(downloaded_images) >= len(pins):
                break
            
            try:
                image_url = pin['image_url']
                logger.info(f"Downloading image {len(downloaded_images) + 1}/{len(pins)}: {pin['title']}")
                
                # Download image
                response = self.session.get(image_url, stream=True, timeout=30)
                response.raise_for_status()
                
                image_data = response.content
                
                # Check for duplicates
                image_hash = hashlib.md5(image_data).hexdigest()
                if image_hash in self.downloaded_hashes:
                    logger.info(f"Duplicate image skipped")
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                # Save to temp file first to check dimensions
                temp_file = self.temp_dir / f"temp_{next_number:03d}.jpg"
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Check dimensions
                width, height = self.get_image_dimensions_from_file(temp_file)
                if not self.is_high_resolution(width, height):
                    logger.info(f"Image too low resolution ({width}x{height}), skipping")
                    self.stats['low_res_skipped'] += 1
                    temp_file.unlink()
                    continue
                
                # File names
                filename = f"{next_number:03d}.jpg"
                wallpaper_path = category_wallpaper_dir / filename
                thumbnail_path = category_thumbnail_dir / filename
                
                # Move to wallpaper directory
                shutil.move(str(temp_file), str(wallpaper_path))
                
                # Create thumbnail
                self.create_thumbnail(wallpaper_path, thumbnail_path)
                
                # Create image metadata
                image_metadata = {
                    'id': f"{category}_{next_number:03d}",
                    'category': category,
                    'title': f"{category.title()} Wallpaper {next_number:03d}",
                    'tags': [category],
                    'urls': {
                        'raw': f"https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/{category}/{filename}",
                        'thumb': f"https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/{category}/{filename}"
                    },
                    'metadata': {
                        'added_at': datetime.utcnow().isoformat(),
                        'file_size': len(image_data),
                        'dimensions': {
                            'width': width,
                            'height': height
                        },
                        'source': 'pinterest',
                        'source_url': pin['pin_url']
                    }
                }
                
                downloaded_images.append(image_metadata)
                self.downloaded_hashes.add(image_hash)
                self.stats['downloaded_count'] += 1
                self.stats['high_res_pins'] += 1
                
                logger.info(f"✅ Downloaded: {filename} ({width}x{height})")
                next_number += 1
                
                # Respectful delay
                time.sleep(self.download_delay)
                
            except Exception as e:
                logger.error(f"Failed to download image: {e}")
                continue
        
        logger.info(f"Download complete! {len(downloaded_images)} images processed")
        return downloaded_images
    
    def create_thumbnail(self, source_path: Path, thumbnail_path: Path, size: Tuple[int, int] = (400, 600)):
        """Create thumbnail from source image"""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            # Copy original as fallback
            shutil.copy2(source_path, thumbnail_path)
    
    def generate_apis(self, category: str):
        """Generate API endpoints and pagination"""
        logger.info(f"Generating APIs for category: {category}")
        
        try:
            # Run the build_api.py script
            build_script = self.project_root / "tools" / "build_api.py"
            
            if build_script.exists():
                logger.info("Running API generation script...")
                result = subprocess.run([
                    sys.executable, str(build_script)
                ], capture_output=True, text=True, cwd=str(self.project_root))
                
                if result.returncode == 0:
                    logger.info("✅ API generation completed successfully")
                    self.stats['api_generated'] = True
                    self.stats['pagination_generated'] = True
                else:
                    logger.error(f"API generation failed: {result.stderr}")
            else:
                logger.error("API build script not found")
                
        except Exception as e:
            logger.error(f"Error generating APIs: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            
            # Clean temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def run_complete_pipeline(self) -> Dict:
        """Run the complete scraping and API generation pipeline"""
        logger.info("🚀 Starting Pinterest API Scraper Pipeline")
        
        start_time = time.time()
        
        try:
            # Get user input
            params = self.get_user_input()
            url = params['url']
            category = params['category']
            quantity = params['quantity']
            
            logger.info(f"📌 URL: {url}")
            logger.info(f"📂 Category: {category}")
            logger.info(f"🔢 Quantity: {quantity}")
            
            # Phase 1: Scrape Pinterest
            logger.info("\n🔍 Phase 1: Scraping Pinterest...")
            pins = self.scrape_pinterest_url(url, quantity)
            
            if not pins:
                logger.error("No pins found!")
                return self.get_final_stats(start_time)
            
            # Phase 2: Download and process images
            logger.info(f"\n⬇️  Phase 2: Downloading {len(pins)} images...")
            downloaded_images = self.download_and_process_images(pins, category)
            
            if not downloaded_images:
                logger.error("No images downloaded!")
                return self.get_final_stats(start_time)
            
            # Phase 3: Generate APIs
            logger.info(f"\n🔧 Phase 3: Generating APIs and pagination...")
            self.generate_apis(category)
            
            # Final stats
            final_stats = self.get_final_stats(start_time)
            self.save_summary(final_stats, params, downloaded_images)
            
            logger.info("🎉 Pipeline completed successfully!")
            return final_stats
            
        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
            return self.get_final_stats(start_time)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return self.get_final_stats(start_time)
        finally:
            self.cleanup()
    
    def get_final_stats(self, start_time: float) -> Dict:
        """Generate final statistics"""
        duration = time.time() - start_time
        return {
            'duration_seconds': round(duration, 2),
            'pins_found': self.stats['pins_found'],
            'high_res_pins': self.stats['high_res_pins'],
            'downloaded_count': self.stats['downloaded_count'],
            'duplicates_skipped': self.stats['duplicates_skipped'],
            'low_res_skipped': self.stats['low_res_skipped'],
            'api_generated': self.stats['api_generated'],
            'pagination_generated': self.stats['pagination_generated'],
            'success_rate': round((self.stats['downloaded_count'] / max(1, self.stats['pins_found'])) * 100, 2)
        }
    
    def save_summary(self, stats: Dict, params: Dict, downloaded_images: List[Dict]):
        """Save scraping summary"""
        summary = {
            'scrape_params': params,
            'scraping_stats': stats,
            'downloaded_images': len(downloaded_images),
            'sample_images': downloaded_images[:5],  # First 5 as sample
            'api_endpoints': {
                'category_api': f"/collection/api/v1/{params['category']}.json",
                'pagination_base': f"/collection/api/v1/{params['category']}/pages/",
                'wallpapers_base': f"/collection/wallpapers/{params['category']}/",
                'thumbnails_base': f"/collection/thumbnails/{params['category']}/"
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.project_root / f"pinterest_scrape_summary_{params['category']}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved: {summary_file}")

def main():
    """Main execution function"""
    scraper = PinterestAPIScraper()
    
    try:
        stats = scraper.run_complete_pipeline()
        
        print(f"\n🎉 Pinterest API Scraper Complete!")
        print(f"📊 Total Images Downloaded: {stats['downloaded_count']}")
        print(f"🔍 Total Pins Found: {stats['pins_found']}")
        print(f"📏 High-Resolution Pins: {stats['high_res_pins']}")
        print(f"⏱️  Duration: {stats['duration_seconds']} seconds")
        print(f"✅ Success Rate: {stats['success_rate']}%")
        print(f"🔧 API Generated: {'Yes' if stats['api_generated'] else 'No'}")
        print(f"📄 Pagination Generated: {'Yes' if stats['pagination_generated'] else 'No'}")
        
        if stats['downloaded_count'] > 0:
            print(f"\n📁 Images saved to collection structure")
            print(f"🌐 APIs available at: /collection/api/v1/")
            print(f"📱 Ready for mobile app consumption!")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()