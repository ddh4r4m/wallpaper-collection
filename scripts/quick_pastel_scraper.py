#!/usr/bin/env python3
"""
Quick Pastel Scraper
Faster approach with broader search terms
"""

import os
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickPastelScraper:
    """Quick pastel scraper with minimal filtering"""
    
    def __init__(self, output_dir: str = "bulk_download"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        # Session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def load_existing_hashes(self):
        """Load existing hashes"""
        hash_files = ['bulk_download/pastel_hashes.json', 'bulk_download/global_hashes.json']
        
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
    
    def quick_scrape_pastel(self, search_term: str = "aesthetic pastel", target: int = 50) -> List[Dict]:
        """Quick scrape with minimal filtering"""
        logger.info(f"Quick scraping: '{search_term}' (target: {target})")
        
        driver = None
        all_images = []
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.set_page_load_timeout(20)
            
            url = f"https://unsplash.com/s/photos/{search_term.replace(' ', '-')}"
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            time.sleep(2)
            
            # Get initial page
            image_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
            
            for img_element in image_elements:
                try:
                    src = img_element.get_attribute('src')
                    alt = img_element.get_attribute('alt') or 'Aesthetic pastel wallpaper'
                    
                    # Skip small images only
                    if any(size in src for size in ['w=400', 'w=200', 'w=150']):
                        continue
                    
                    # Very minimal filtering - just need reasonable alt text
                    alt_lower = alt.lower()
                    if len(alt_lower) > 3 and not any(bad in alt_lower for bad in ['user', 'profile', 'avatar']):
                        high_res_url = self.get_high_res_url(src)
                        
                        image_info = {
                            'url': high_res_url,
                            'original_url': src,
                            'alt': alt,
                            'photographer': 'Unsplash Contributor',
                            'source': 'unsplash_pastel_quick',
                            'category': 'pastel'
                        }
                        all_images.append(image_info)
                        
                        if len(all_images) >= target:
                            break
                            
                except Exception as e:
                    continue
            
            # Try one scroll for more content
            if len(all_images) < target:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    new_images = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
                    for img_element in new_images[len(image_elements):]:
                        try:
                            src = img_element.get_attribute('src')
                            alt = img_element.get_attribute('alt') or 'Aesthetic pastel wallpaper'
                            
                            if any(size in src for size in ['w=400', 'w=200']):
                                continue
                            
                            alt_lower = alt.lower()
                            if len(alt_lower) > 3:
                                high_res_url = self.get_high_res_url(src)
                                
                                image_info = {
                                    'url': high_res_url,
                                    'original_url': src,
                                    'alt': alt,
                                    'photographer': 'Unsplash Contributor',
                                    'source': 'unsplash_pastel_quick',
                                    'category': 'pastel'
                                }
                                all_images.append(image_info)
                                
                                if len(all_images) >= target:
                                    break
                                    
                        except Exception:
                            continue
                except Exception:
                    pass
            
            # Remove duplicates
            unique_urls = set()
            unique_images = []
            for img in all_images:
                if img['url'] not in unique_urls:
                    unique_urls.add(img['url'])
                    unique_images.append(img)
            
            logger.info(f"Found {len(unique_images)} unique images")
            return unique_images
            
        except Exception as e:
            logger.error(f"Error during quick scraping: {e}")
            return all_images
        finally:
            if driver:
                driver.quit()
    
    def download_image(self, image_info: Dict, index: int) -> Dict:
        """Download a single image"""
        try:
            url = image_info['url']
            filename = f"pastel_{index+100:03d}.jpg"  # Start from 100 to avoid conflicts
            
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            image_data = response.content
            
            if len(image_data) < 30000:
                return {'status': 'too_small'}
            
            if self.is_duplicate(image_data):
                return {'status': 'duplicate'}
            
            # Create directory
            category_dir = self.output_dir / 'pastel'
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Save image
            filepath = category_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create metadata
            metadata = {
                'id': f"pastel_{index+100:03d}",
                'source': 'unsplash_pastel_quick',
                'category': 'pastel',
                'title': f'Aesthetic Pastel Wallpaper {index+100}',
                'description': f'High-quality pastel aesthetic wallpaper: {image_info.get("alt", "pastel aesthetic")}',
                'width': 1080,
                'height': 1920,
                'photographer': 'Unsplash Contributor',
                'tags': ['pastel', 'aesthetic', 'soft', 'wallpaper', 'hd', 'mobile'],
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
                'size': len(image_data)
            }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_quick_pastel_scraping(self, target: int = 50):
        """Run quick pastel scraping"""
        # Try multiple search terms
        search_terms = ['aesthetic pastel', 'pastel aesthetic', 'soft colors']
        all_images = []
        
        for term in search_terms:
            images = self.quick_scrape_pastel(term, target//len(search_terms) + 10)
            all_images.extend(images)
            if len(all_images) >= target:
                break
        
        # Remove duplicates again
        unique_urls = set()
        unique_images = []
        for img in all_images:
            if img['url'] not in unique_urls:
                unique_urls.add(img['url'])
                unique_images.append(img)
        
        logger.info(f"Total unique images found: {len(unique_images)}")
        random.shuffle(unique_images)
        
        # Download
        downloaded = 0
        duplicates = 0
        errors = 0
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(self.download_image, img, i) for i, img in enumerate(unique_images[:target])]
            
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    if downloaded % 5 == 0:
                        logger.info(f"✅ Downloaded {downloaded} pastel images")
                elif result['status'] == 'duplicate':
                    duplicates += 1
                elif result['status'] == 'error':
                    errors += 1
        
        # Save hashes
        hash_file = self.output_dir / 'pastel_hashes.json'
        with self.hash_lock:
            with open(hash_file, 'w') as f:
                json.dump(list(self.downloaded_hashes), f)
        
        return {
            'downloaded': downloaded,
            'duplicates': duplicates,
            'errors': errors
        }

def main():
    print("🎨 Quick Pastel Wallpaper Scraper")
    print("=" * 40)
    
    scraper = QuickPastelScraper()
    start_time = time.time()
    
    results = scraper.run_quick_pastel_scraping(target=50)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ QUICK PASTEL SCRAPING COMPLETE!")
    print(f"Downloaded: {results['downloaded']}")
    print(f"Duplicates: {results['duplicates']}")
    print(f"Errors: {results['errors']}")
    print(f"Time: {elapsed_time:.1f}s")

if __name__ == "__main__":
    main()