#!/usr/bin/env python3
"""
Improved Pastel Scraper
Better search terms and more lenient filtering for pastel wallpapers
"""

import os
import sys
import json
import time
import requests
import hashlib
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
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedPastelScraper:
    """Improved pastel scraper with better search terms"""
    
    def __init__(self, output_dir: str = "bulk_download"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Multiple search terms for pastel content
        self.search_terms = [
            'pastel colors',
            'soft pastels',
            'light pink aesthetic',
            'kawaii pastel',
            'aesthetic pastel',
            'pastel gradient'
        ]
        
        # More relaxed keywords for pastel filtering
        self.pastel_keywords = [
            'pastel', 'soft', 'light', 'pale', 'pink', 'purple', 'blue', 'mint', 'peach',
            'lavender', 'cream', 'gentle', 'delicate', 'sweet', 'kawaii', 'cute', 'dreamy',
            'aesthetic', 'minimalist', 'color', 'gradient', 'background', 'texture',
            'abstract', 'sky', 'cloud', 'flower', 'nature'
        ]
        
        # Track downloaded hashes
        self.downloaded_hashes: Set[str] = set()
        self.hash_lock = threading.Lock()
        self.load_existing_hashes()
        
        # Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        # Session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def load_existing_hashes(self):
        """Load existing hashes from all sources"""
        hash_files = [
            'bulk_download/pastel_hashes.json',
            'bulk_download/global_hashes.json'
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
        hash_file = self.output_dir / 'pastel_hashes.json'
        with self.hash_lock:
            with open(hash_file, 'w') as f:
                json.dump(list(self.downloaded_hashes), f)
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check for duplicates"""
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
    
    def enhanced_scroll_and_load(self, driver, max_attempts: int = 6) -> bool:
        """Enhanced scrolling and loading"""
        logger.info("Attempting enhanced content loading...")
        
        # Strategy 1: Look for load more button
        try:
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load more') or contains(text(), 'Show more')]")
            if load_more_buttons:
                button = load_more_buttons[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", button)
                logger.info("✅ Clicked 'Load more' button")
                time.sleep(6)
                return True
        except Exception as e:
            logger.debug(f"Button click failed: {e}")
        
        # Strategy 2: Infinite scroll
        try:
            current_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(10):
                scroll_position = current_height * (i + 1) / 10
                driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1)
            
            time.sleep(4)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > current_height:
                logger.info("✅ Infinite scroll triggered - content loaded")
                return True
        except Exception as e:
            logger.debug(f"Infinite scroll failed: {e}")
        
        return False
    
    def scrape_with_search_term(self, search_term: str, max_pages: int = 3) -> List[Dict]:
        """Scrape images for a specific search term"""
        logger.info(f"Scraping with search term: '{search_term}'")
        
        driver = None
        all_images = []
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate to Unsplash search
            url = f"https://unsplash.com/s/photos/{search_term.replace(' ', '-')}"
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for initial load
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            time.sleep(3)
            
            page_count = 0
            consecutive_failures = 0
            
            while page_count < max_pages and consecutive_failures < 2:
                page_count += 1
                logger.info(f"Processing page {page_count}/{max_pages} for '{search_term}'")
                
                time.sleep(3)
                
                # Get all images
                image_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
                
                page_images = []
                for img_element in image_elements:
                    try:
                        src = img_element.get_attribute('src')
                        alt = img_element.get_attribute('alt') or f'Pastel wallpaper'
                        
                        # Skip small images
                        if any(size in src for size in ['w=400', 'w=200', 'w=150', 'w=100']):
                            continue
                        
                        # More lenient filtering - just check for pastel-related content
                        alt_lower = alt.lower()
                        if any(keyword in alt_lower for keyword in self.pastel_keywords[:15]):  # Use first 15 keywords
                            high_res_url = self.get_high_res_url(src)
                            
                            image_info = {
                                'url': high_res_url,
                                'original_url': src,
                                'alt': alt,
                                'photographer': 'Unsplash Contributor',
                                'source': f'unsplash_pastel_improved',
                                'category': 'pastel',
                                'search_term': search_term,
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
                logger.info(f"Found {len(unique_page_images)} unique pastel images on page {page_count}")
                
                if len(unique_page_images) == 0:
                    consecutive_failures += 1
                    logger.warning(f"No new images found on page {page_count}")
                else:
                    consecutive_failures = 0
                
                # Try to load more content for next page
                if page_count < max_pages:
                    success = self.enhanced_scroll_and_load(driver)
                    if not success:
                        consecutive_failures += 1
                
                time.sleep(2)
            
            return all_images
            
        except Exception as e:
            logger.error(f"Error during scraping with '{search_term}': {e}")
            return all_images
        finally:
            if driver:
                driver.quit()
    
    def download_image(self, image_info: Dict, index: int) -> Dict:
        """Download a single image"""
        try:
            url = image_info['url']
            filename = f"pastel_{index:03d}.jpg"
            
            # Download with retries
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    image_data = response.content
                    
                    # Skip tiny images
                    if len(image_data) < 30000:
                        return {'status': 'too_small', 'size': len(image_data)}
                    
                    if self.is_duplicate(image_data):
                        return {'status': 'duplicate'}
                    
                    # Create category directory
                    category_dir = self.output_dir / 'pastel'
                    category_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save image
                    filepath = category_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Create metadata
                    metadata = {
                        'id': f"pastel_{index:03d}",
                        'source': 'unsplash_pastel_improved',
                        'category': 'pastel',
                        'title': f'High-Quality Pastel Wallpaper {index}',
                        'description': f'High-quality pastel wallpaper from Unsplash: {image_info.get("alt", "pastel aesthetic")}',
                        'width': 1080,
                        'height': 1920,
                        'photographer': image_info.get('photographer', 'Unsplash Contributor'),
                        'tags': ['pastel', 'soft', 'aesthetic', 'light', 'wallpaper', 'hd', 'high resolution', 'mobile'],
                        'download_url': url,
                        'original_url': image_info.get('original_url', url),
                        'alt_text': image_info.get('alt', ''),
                        'scraped_at': datetime.now().isoformat() + 'Z',
                        'filename': filename,
                        'search_term': image_info.get('search_term', 'pastel')
                    }
                    
                    metadata_file = filepath.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return {
                        'status': 'success',
                        'filename': filename,
                        'size': len(image_data),
                        'alt': image_info.get('alt', '')[:50]
                    }
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        return {'status': 'error', 'error': str(e)}
                    time.sleep(1)
                    
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_improved_pastel_scraping(self, target: int = 100):
        """Run improved pastel scraping with multiple search terms"""
        logger.info(f"Starting improved pastel scraping (target: {target})")
        
        all_images = []
        
        # Scrape with multiple search terms
        for search_term in self.search_terms:
            images = self.scrape_with_search_term(search_term, max_pages=3)
            all_images.extend(images)
            if len(all_images) >= target * 2:  # Get extra to account for duplicates
                break
        
        logger.info(f"Found {len(all_images)} total pastel images from all search terms")
        
        # Remove duplicates across all search terms
        unique_urls = set()
        unique_images = []
        for img in all_images:
            if img['url'] not in unique_urls:
                unique_urls.add(img['url'])
                unique_images.append(img)
        
        logger.info(f"After deduplication: {len(unique_images)} unique images")
        
        # Shuffle for variety
        random.shuffle(unique_images)
        
        # Download images
        downloaded = 0
        duplicates = 0
        errors = 0
        too_small = 0
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for i, image_info in enumerate(unique_images[:target*2], 1):
                future = executor.submit(self.download_image, image_info, i)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    if downloaded % 10 == 0:
                        logger.info(f"✅ pastel: {downloaded}/{target} - {result['filename']}")
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
    print("🎨 Improved Pastel Wallpaper Scraper")
    print("=" * 50)
    
    scraper = ImprovedPastelScraper()
    start_time = time.time()
    
    results = scraper.run_improved_pastel_scraping(target=80)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ IMPROVED PASTEL SCRAPING COMPLETE!")
    print(f"Downloaded: {results['downloaded']}")
    print(f"Duplicates: {results['duplicates']}")
    print(f"Errors: {results['errors']}")
    print(f"Time: {elapsed_time:.1f}s")
    print(f"Rate: {results['downloaded'] / elapsed_time:.1f} images/s")

if __name__ == "__main__":
    main()