#!/usr/bin/env python3
"""
Unsplash Abstract Image Scraper with Pagination Support
Extracts high-quality abstract images from Unsplash search results
"""

import os
import sys
import json
import time
import requests
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnsplashAbstractScraper:
    """High-quality abstract image scraper for Unsplash"""
    
    def __init__(self, output_dir: str = "high_quality_abstract"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track downloaded hashes to avoid duplicates
        self.downloaded_hashes: Set[str] = set()
        self.hash_lock = threading.Lock()
        self.load_existing_hashes()
        
        # Setup Chrome driver with options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # Run in background
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Session for downloading images
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def load_existing_hashes(self):
        """Load existing hashes to avoid duplicates"""
        hash_files = [
            'crawl_cache/downloaded_hashes.json',
            'multi_crawl_cache/downloaded_hashes.json',
            'ultra_crawl/ultra_hashes.json',
            f'{self.output_dir}/abstract_hashes.json'
        ]
        
        for hash_file in hash_files:
            if Path(hash_file).exists():
                try:
                    with open(hash_file, 'r') as f:
                        hashes = json.load(f)
                        if isinstance(hashes, list):
                            self.downloaded_hashes.update(hashes)
                        elif isinstance(hashes, set):
                            self.downloaded_hashes.update(hashes)
                except Exception as e:
                    logger.warning(f"Could not load hashes from {hash_file}: {e}")
        
        logger.info(f"Loaded {len(self.downloaded_hashes)} existing hashes")
    
    def save_hashes(self):
        """Save downloaded hashes"""
        hash_file = self.output_dir / 'abstract_hashes.json'
        with self.hash_lock:
            with open(hash_file, 'w') as f:
                json.dump(list(self.downloaded_hashes), f)
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check if image is duplicate"""
        image_hash = hashlib.md5(image_data).hexdigest()
        with self.hash_lock:
            if image_hash in self.downloaded_hashes:
                return True
            self.downloaded_hashes.add(image_hash)
            return False
    
    def get_high_res_url(self, unsplash_url: str) -> str:
        """Convert Unsplash URL to high resolution download URL"""
        try:
            # Extract the image ID from various Unsplash URL formats
            if 'photo-' in unsplash_url:
                # Format: https://images.unsplash.com/photo-1234567890?params
                photo_id = unsplash_url.split('photo-')[1].split('?')[0]
            elif '/photos/' in unsplash_url:
                # Format: https://unsplash.com/photos/abc123
                photo_id = unsplash_url.split('/photos/')[1].split('?')[0]
            else:
                # Try to extract from URL patterns
                patterns = [
                    r'unsplash\.com/.*?([a-zA-Z0-9_-]{11})',
                    r'images\.unsplash\.com/.*?([a-zA-Z0-9_-]{11})'
                ]
                photo_id = None
                for pattern in patterns:
                    match = re.search(pattern, unsplash_url)
                    if match:
                        photo_id = match.group(1)
                        break
                
                if not photo_id:
                    return unsplash_url
            
            # Create high-resolution URL (mobile portrait format)
            high_res_url = f"https://images.unsplash.com/photo-{photo_id}?w=1080&h=1920&fit=crop&crop=center&q=85"
            return high_res_url
            
        except Exception as e:
            logger.warning(f"Could not convert URL {unsplash_url}: {e}")
            return unsplash_url
    
    def scrape_unsplash_images(self, max_pages: int = 5, images_per_page: int = 20) -> List[Dict]:
        """Scrape abstract images from Unsplash with pagination"""
        logger.info(f"Starting Unsplash scrape for abstract images (max {max_pages} pages)")
        
        driver = None
        all_images = []
        
        try:
            # Initialize Chrome driver
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Navigate to Unsplash abstract search
            url = "https://unsplash.com/s/photos/abstract"
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for initial page load
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            
            page_count = 0
            
            while page_count < max_pages:
                page_count += 1
                logger.info(f"Processing page {page_count}/{max_pages}")
                
                # Wait a bit for images to load
                time.sleep(3)
                
                # Find all image elements
                image_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
                
                page_images = []
                for img_element in image_elements:
                    try:
                        src = img_element.get_attribute('src')
                        alt = img_element.get_attribute('alt') or 'Abstract wallpaper'
                        
                        # Skip very small images (thumbnails)
                        if 'w=400' in src or 'w=200' in src:
                            continue
                        
                        # Get high resolution URL
                        high_res_url = self.get_high_res_url(src)
                        
                        # Try to get photographer info from parent elements
                        photographer = "Unsplash Contributor"
                        try:
                            # Look for photographer info in nearby elements
                            parent = img_element.find_element(By.XPATH, "./ancestor::figure | ./ancestor::div[@class*='photo']")
                            photo_links = parent.find_elements(By.CSS_SELECTOR, "a[href*='/photos/']")
                            if photo_links:
                                href = photo_links[0].get_attribute('href')
                                if '/photos/' in href:
                                    photo_id = href.split('/photos/')[1].split('?')[0]
                                    photographer = f"Unsplash Photo {photo_id[:8]}"
                        except:
                            pass
                        
                        image_info = {
                            'url': high_res_url,
                            'original_url': src,
                            'alt': alt,
                            'photographer': photographer,
                            'source': 'unsplash_abstract',
                            'page': page_count
                        }
                        
                        page_images.append(image_info)
                        
                    except Exception as e:
                        logger.debug(f"Error processing image element: {e}")
                        continue
                
                # Remove duplicates from this page
                unique_urls = set()
                unique_page_images = []
                for img in page_images:
                    if img['url'] not in unique_urls:
                        unique_urls.add(img['url'])
                        unique_page_images.append(img)
                
                all_images.extend(unique_page_images)
                logger.info(f"Found {len(unique_page_images)} unique images on page {page_count}")
                
                # Try to click "Load more" button for next page
                if page_count < max_pages:
                    try:
                        # Look for the load more button
                        load_more_selectors = [
                            "button:contains('Load more')",
                            "button[type='button']",
                            ".nwrEn button",
                            "[data-test='load-more-button']"
                        ]
                        
                        load_more_button = None
                        for selector in load_more_selectors:
                            try:
                                if ':contains(' in selector:
                                    # Use XPath for text-based search
                                    buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load more')]")
                                    if buttons:
                                        load_more_button = buttons[0]
                                        break
                                else:
                                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                                    # Find button that might be "Load more"
                                    for btn in buttons:
                                        if 'load' in btn.text.lower() or 'more' in btn.text.lower():
                                            load_more_button = btn
                                            break
                                    if load_more_button:
                                        break
                            except:
                                continue
                        
                        if load_more_button:
                            logger.info(f"Clicking 'Load more' button for page {page_count + 1}")
                            
                            # Scroll to button first
                            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                            time.sleep(1)
                            
                            # Click the button
                            driver.execute_script("arguments[0].click();", load_more_button)
                            
                            # Wait for new content to load
                            time.sleep(5)
                            
                        else:
                            logger.warning("Could not find 'Load more' button, stopping pagination")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error clicking load more button: {e}")
                        break
                
                # Don't overload the server
                time.sleep(2)
            
            logger.info(f"Scraped {len(all_images)} total images from {page_count} pages")
            return all_images
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return all_images
            
        finally:
            if driver:
                driver.quit()
    
    def download_image(self, image_info: Dict, index: int) -> Dict:
        """Download a single high-quality image"""
        try:
            url = image_info['url']
            filename = f"abstract_{index:03d}.jpg"
            
            # Download with timeout and retries
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    image_data = response.content
                    
                    # Skip tiny images
                    if len(image_data) < 50000:
                        return {'status': 'too_small', 'size': len(image_data)}
                    
                    # Check for duplicates
                    if self.is_duplicate(image_data):
                        return {'status': 'duplicate'}
                    
                    # Save image
                    filepath = self.output_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Create metadata
                    metadata = {
                        'id': f"abstract_{index:03d}",
                        'source': 'unsplash_abstract_hq',
                        'category': 'abstract',
                        'title': f'High-Quality Abstract Wallpaper {index}',
                        'description': f'High-quality abstract wallpaper from Unsplash: {image_info.get("alt", "Abstract art")}',
                        'width': 1080,
                        'height': 1920,
                        'photographer': image_info.get('photographer', 'Unsplash Contributor'),
                        'tags': ['abstract', 'wallpaper', 'hd', 'high resolution', 'mobile', 'art', 'design', 'modern'],
                        'download_url': url,
                        'original_url': image_info.get('original_url', url),
                        'alt_text': image_info.get('alt', ''),
                        'scraped_at': datetime.now().isoformat() + 'Z',
                        'filename': filename
                    }
                    
                    # Save metadata
                    metadata_file = filepath.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return {
                        'status': 'success', 
                        'filename': filename,
                        'size': len(image_data),
                        'photographer': image_info.get('photographer', 'Unknown')
                    }
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:  # Last attempt
                        return {'status': 'error', 'error': str(e)}
                    time.sleep(1)
                    
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def download_all_images(self, images: List[Dict], target: int = 100, max_workers: int = 8) -> Dict:
        """Download all scraped images with high concurrency"""
        logger.info(f"Starting download of {len(images)} images (target: {target})")
        
        # Shuffle for variety
        random.shuffle(images)
        
        downloaded = 0
        duplicates = 0
        errors = 0
        too_small = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit download tasks
            futures = []
            for i, image_info in enumerate(images[:target*2], 1):  # Get extra for failures
                if downloaded >= target:
                    break
                future = executor.submit(self.download_image, image_info, i)
                futures.append(future)
            
            # Process results
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    if downloaded % 10 == 0:
                        logger.info(f"✅ Downloaded {downloaded}/{target} - {result['filename']} ({result['size']} bytes)")
                    
                elif result['status'] == 'duplicate':
                    duplicates += 1
                    
                elif result['status'] == 'too_small':
                    too_small += 1
                    
                elif result['status'] == 'error':
                    errors += 1
                    logger.debug(f"❌ Download failed: {result.get('error', 'Unknown error')}")
                
                # Stop when target reached
                if downloaded >= target:
                    break
        
        # Save final hash state
        self.save_hashes()
        
        return {
            'downloaded': downloaded,
            'duplicates': duplicates,
            'too_small': too_small,
            'errors': errors,
            'target': target
        }

def move_old_abstract_images():
    """Move current poor-quality abstract images to dump folder"""
    logger.info("Moving old abstract images to dump folder")
    
    abstract_dir = Path("wallpapers/abstract")
    dump_dir = Path("dump/old_abstract")
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    if not abstract_dir.exists():
        logger.info("No existing abstract directory found")
        return 0
    
    moved_count = 0
    for file in abstract_dir.glob("*"):
        if file.is_file():
            destination = dump_dir / file.name
            file.rename(destination)
            moved_count += 1
    
    logger.info(f"Moved {moved_count} files to dump folder")
    return moved_count

def main():
    parser = argparse.ArgumentParser(description='Unsplash High-Quality Abstract Scraper')
    parser.add_argument('--target', type=int, default=100, help='Target number of images to download')
    parser.add_argument('--pages', type=int, default=5, help='Max pages to scrape')
    parser.add_argument('--workers', type=int, default=8, help='Download workers')
    parser.add_argument('--output', default='high_quality_abstract', help='Output directory')
    parser.add_argument('--keep-old', action='store_true', help='Keep old abstract images')
    
    args = parser.parse_args()
    
    print(f"🎨 Unsplash High-Quality Abstract Scraper")
    print(f"=" * 50)
    print(f"🎯 Target: {args.target} images")
    print(f"📄 Max pages: {args.pages}")
    print(f"⚡ Workers: {args.workers}")
    print(f"📁 Output: {args.output}")
    
    # Move old images unless user wants to keep them
    if not args.keep_old:
        moved = move_old_abstract_images()
        print(f"📦 Moved {moved} old abstract images to dump")
    
    # Create scraper and run
    scraper = UnsplashAbstractScraper(args.output)
    
    start_time = time.time()
    
    # Scrape images from Unsplash
    print(f"\n🔍 Scraping Unsplash for abstract images...")
    images = scraper.scrape_unsplash_images(max_pages=args.pages)
    
    if not images:
        print("❌ No images found! Check your internet connection and try again.")
        return
    
    print(f"🎉 Found {len(images)} abstract images from Unsplash!")
    
    # Download images
    print(f"\n⬇️  Downloading high-quality images...")
    results = scraper.download_all_images(images, target=args.target, max_workers=args.workers)
    
    # Print results
    total_time = time.time() - start_time
    print(f"\n🎉 UNSPLASH SCRAPE COMPLETE!")
    print(f"=" * 50)
    print(f"✅ Downloaded: {results['downloaded']}")
    print(f"🔄 Duplicates: {results['duplicates']}")
    print(f"📏 Too small: {results['too_small']}")
    print(f"❌ Errors: {results['errors']}")
    print(f"⏱️  Time: {total_time:.1f} seconds")
    print(f"🚀 Rate: {results['downloaded'] / total_time:.1f} images/second")
    
    print(f"\n🔄 Next steps:")
    print(f"1. Move to wallpapers: mv {args.output}/* wallpapers/abstract/")
    print(f"2. Generate index: python3 scripts/generate_index.py --update-all")
    print(f"3. Review quality: Check {args.output}/ directory")

if __name__ == "__main__":
    main()