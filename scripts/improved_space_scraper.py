#!/usr/bin/env python3
"""
Improved Unsplash Space Scraper with Better Pagination
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedSpaceScraper:
    """Improved space scraper with better pagination and scrolling"""
    
    def __init__(self, output_dir: str = "more_space_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track downloaded hashes
        self.downloaded_hashes: Set[str] = set()
        self.hash_lock = threading.Lock()
        self.load_existing_hashes()
        
        # Setup Chrome with better options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-web-security')
        self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def load_existing_hashes(self):
        """Load existing hashes"""
        hash_files = [
            'high_quality_abstract/abstract_hashes.json',
            'high_quality_space/space_hashes.json',
            f'{self.output_dir}/space_hashes.json'
        ]
        
        for hash_file in hash_files:
            if Path(hash_file).exists():
                try:
                    with open(hash_file, 'r') as f:
                        hashes = json.load(f)
                        if isinstance(hashes, list):
                            self.downloaded_hashes.update(hashes)
                except Exception as e:
                    logger.warning(f"Could not load hashes from {hash_file}: {e}")
        
        logger.info(f"Loaded {len(self.downloaded_hashes)} existing hashes")
    
    def save_hashes(self):
        """Save hashes"""
        hash_file = self.output_dir / 'space_hashes.json'
        with self.hash_lock:
            with open(hash_file, 'w') as f:
                json.dump(list(self.downloaded_hashes), f)
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check duplicates"""
        image_hash = hashlib.md5(image_data).hexdigest()
        with self.hash_lock:
            if image_hash in self.downloaded_hashes:
                return True
            self.downloaded_hashes.add(image_hash)
            return False
    
    def get_high_res_url(self, unsplash_url: str) -> str:
        """Convert to high-res URL"""
        try:
            if 'photo-' in unsplash_url:
                photo_id = unsplash_url.split('photo-')[1].split('?')[0]
                return f"https://images.unsplash.com/photo-{photo_id}?w=1080&h=1920&fit=crop&crop=center&q=85"
            return unsplash_url
        except:
            return unsplash_url
    
    def scroll_and_load_more(self, driver, max_attempts: int = 5) -> bool:
        """Improved scrolling and load more detection"""
        logger.info("Attempting to load more content...")
        
        # Strategy 1: Scroll to bottom multiple times
        for scroll_attempt in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check if load more button appeared
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load more') or contains(text(), 'Show more')]")
            if load_more_buttons:
                try:
                    button = load_more_buttons[0]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    logger.info("✅ Clicked 'Load more' button via scrolling")
                    time.sleep(5)  # Wait for content to load
                    return True
                except Exception as e:
                    logger.debug(f"Failed to click load more button: {e}")
        
        # Strategy 2: Look for infinite scroll trigger
        try:
            # Scroll in smaller increments to trigger infinite scroll
            current_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(10):
                driver.execute_script(f"window.scrollTo(0, {current_height * (i + 1) / 10});")
                time.sleep(1)
            
            # Wait and check if new content loaded
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > current_height:
                logger.info("✅ Infinite scroll triggered - new content loaded")
                return True
        except Exception as e:
            logger.debug(f"Infinite scroll failed: {e}")
        
        # Strategy 3: Press Page Down multiple times
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            for _ in range(5):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
            
            # Check for load more button again
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load more') or contains(text(), 'Show more')]")
            if load_more_buttons:
                button = load_more_buttons[0]
                driver.execute_script("arguments[0].click();", button)
                logger.info("✅ Clicked 'Load more' button after Page Down")
                time.sleep(5)
                return True
        except Exception as e:
            logger.debug(f"Page Down strategy failed: {e}")
        
        # Strategy 4: Look for any clickable button that might load more
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='button'], button:not([type]), .load-more, [class*='load'], [class*='more']")
            for button in buttons:
                try:
                    button_text = button.text.lower()
                    if any(word in button_text for word in ['load', 'more', 'show', 'next']):
                        driver.execute_script("arguments[0].click();", button)
                        logger.info(f"✅ Clicked button with text: {button_text}")
                        time.sleep(5)
                        return True
                except:
                    continue
        except Exception as e:
            logger.debug(f"Button search strategy failed: {e}")
        
        logger.warning("❌ Could not load more content")
        return False
    
    def scrape_space_images_improved(self, max_pages: int = 6) -> List[Dict]:
        """Improved scraping with better pagination"""
        logger.info(f"Starting improved space scraping (max {max_pages} pages)")
        
        driver = None
        all_images = []
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.set_page_load_timeout(30)
            
            url = "https://unsplash.com/s/photos/space"
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for initial load
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            time.sleep(3)
            
            page_count = 0
            consecutive_failures = 0
            
            while page_count < max_pages and consecutive_failures < 3:
                page_count += 1
                logger.info(f"Processing page {page_count}/{max_pages}")
                
                # Wait for images to load
                time.sleep(3)
                
                # Get all images
                image_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
                
                page_images = []
                for img_element in image_elements:
                    try:
                        src = img_element.get_attribute('src')
                        alt = img_element.get_attribute('alt') or 'Space wallpaper'
                        
                        # Skip small images
                        if any(size in src for size in ['w=400', 'w=200', 'w=150', 'w=100']):
                            continue
                        
                        # Space filtering
                        space_keywords = ['space', 'galaxy', 'nebula', 'star', 'planet', 'cosmic', 'universe', 'astronaut', 'earth', 'moon', 'saturn', 'jupiter', 'mars', 'solar', 'milky', 'astronomy', 'black hole', 'comet', 'meteor']
                        alt_lower = alt.lower()
                        
                        if any(keyword in alt_lower for keyword in space_keywords):
                            high_res_url = self.get_high_res_url(src)
                            
                            image_info = {
                                'url': high_res_url,
                                'original_url': src,
                                'alt': alt,
                                'photographer': 'Unsplash Contributor',
                                'source': 'unsplash_space_improved',
                                'page': page_count
                            }
                            page_images.append(image_info)
                    except Exception as e:
                        logger.debug(f"Error processing image: {e}")
                        continue
                
                # Remove duplicates from this page
                unique_urls = set()
                unique_page_images = []
                for img in page_images:
                    if img['url'] not in unique_urls:
                        unique_urls.add(img['url'])
                        unique_page_images.append(img)
                
                all_images.extend(unique_page_images)
                logger.info(f"Found {len(unique_page_images)} unique space images on page {page_count}")
                
                if len(unique_page_images) == 0:
                    consecutive_failures += 1
                    logger.warning(f"No new images found on page {page_count} (failure {consecutive_failures}/3)")
                else:
                    consecutive_failures = 0
                
                # Try to load more content for next page
                if page_count < max_pages:
                    success = self.scroll_and_load_more(driver)
                    if not success:
                        consecutive_failures += 1
                        if consecutive_failures >= 2:
                            logger.warning("Multiple pagination failures, stopping")
                            break
                
                # Don't overload
                time.sleep(2)
            
            logger.info(f"Scraped {len(all_images)} total space images from {page_count} pages")
            return all_images
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return all_images
        finally:
            if driver:
                driver.quit()
    
    def download_image(self, image_info: Dict, index: int) -> Dict:
        """Download space image"""
        try:
            url = image_info['url']
            filename = f"space_{index:03d}.jpg"
            
            # Download with retries
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    image_data = response.content
                    
                    if len(image_data) < 30000:  # Skip tiny images
                        return {'status': 'too_small', 'size': len(image_data)}
                    
                    if self.is_duplicate(image_data):
                        return {'status': 'duplicate'}
                    
                    # Save image
                    filepath = self.output_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Create metadata
                    metadata = {
                        'id': f"space_{index:03d}",
                        'source': 'unsplash_space_improved',
                        'category': 'space',
                        'title': f'High-Quality Space Wallpaper {index}',
                        'description': f'High-quality space wallpaper from Unsplash: {image_info.get("alt", "Space imagery")}',
                        'width': 1080,
                        'height': 1920,
                        'photographer': image_info.get('photographer', 'Unsplash Contributor'),
                        'tags': ['space', 'wallpaper', 'hd', 'high resolution', 'mobile', 'cosmic', 'universe', 'astronomy', 'galaxy', 'stellar'],
                        'download_url': url,
                        'original_url': image_info.get('original_url', url),
                        'alt_text': image_info.get('alt', ''),
                        'scraped_at': datetime.now().isoformat() + 'Z',
                        'filename': filename
                    }
                    
                    metadata_file = filepath.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return {
                        'status': 'success',
                        'filename': filename,
                        'size': len(image_data),
                        'alt': image_info.get('alt', '')[:60]
                    }
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        return {'status': 'error', 'error': str(e)}
                    time.sleep(1)
                    
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def download_all_images(self, images: List[Dict], target: int = 80) -> Dict:
        """Download all images"""
        logger.info(f"Starting download of {len(images)} space images (target: {target})")
        
        random.shuffle(images)
        
        downloaded = 0
        duplicates = 0
        errors = 0
        too_small = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, image_info in enumerate(images[:target*2], 1):
                future = executor.submit(self.download_image, image_info, i)
                futures.append(future)
            
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
                
                if downloaded >= target:
                    break
        
        self.save_hashes()
        
        return {
            'downloaded': downloaded,
            'duplicates': duplicates,
            'too_small': too_small,
            'errors': errors,
            'target': target
        }

def main():
    parser = argparse.ArgumentParser(description='Improved Space Scraper')
    parser.add_argument('--target', type=int, default=80, help='Target images')
    parser.add_argument('--pages', type=int, default=6, help='Max pages')
    parser.add_argument('--output', default='more_space_images', help='Output dir')
    
    args = parser.parse_args()
    
    print(f"🚀 Improved Space Scraper")
    print(f"🎯 Target: {args.target} images")
    print(f"📄 Max pages: {args.pages}")
    
    scraper = ImprovedSpaceScraper(args.output)
    
    start_time = time.time()
    
    print(f"\n🔍 Scraping with improved pagination...")
    images = scraper.scrape_space_images_improved(max_pages=args.pages)
    
    if not images:
        print("❌ No images found!")
        return
    
    print(f"🎉 Found {len(images)} space images!")
    
    print(f"\n⬇️  Downloading images...")
    results = scraper.download_all_images(images, target=args.target)
    
    total_time = time.time() - start_time
    print(f"\n🎉 IMPROVED SPACE SCRAPE COMPLETE!")
    print(f"=" * 50)
    print(f"✅ Downloaded: {results['downloaded']}")
    print(f"🔄 Duplicates: {results['duplicates']}")
    print(f"📏 Too small: {results['too_small']}")
    print(f"❌ Errors: {results['errors']}")
    print(f"⏱️  Time: {total_time:.1f} seconds")
    print(f"🚀 Rate: {results['downloaded'] / total_time:.1f} images/second")

if __name__ == "__main__":
    main()