#!/usr/bin/env python3
"""
Multi-Category Unsplash Scraper
Comprehensive scraper for multiple wallpaper categories with improved pagination
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
from typing import Dict, List, Set, Tuple
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

class MultiCategoryScraper:
    """Enhanced multi-category scraper with improved pagination"""
    
    def __init__(self, base_output_dir: str = "bulk_download"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Category configurations (initialize first)
        self.categories = {
            'nature': {
                'search_term': 'nature landscape',
                'keywords': ['nature', 'landscape', 'mountain', 'forest', 'ocean', 'lake', 'river', 'tree', 'flower', 'sunset', 'sunrise', 'wildlife', 'natural', 'scenic', 'outdoor'],
                'description': 'High-quality nature wallpaper from Unsplash'
            },
            'abstract': {
                'search_term': 'abstract art',
                'keywords': ['abstract', 'geometric', 'pattern', 'artistic', 'design', 'modern', 'contemporary', 'digital art', 'texture', 'gradient', 'color'],
                'description': 'High-quality abstract wallpaper from Unsplash'
            },
            'minimal': {
                'search_term': 'minimal design',
                'keywords': ['minimal', 'clean', 'simple', 'modern', 'geometric', 'monochrome', 'zen', 'contemporary', 'design', 'elegant'],
                'description': 'High-quality minimal wallpaper from Unsplash'
            },
            'cyberpunk': {
                'search_term': 'cyberpunk neon',
                'keywords': ['cyberpunk', 'neon', 'futuristic', 'sci-fi', 'digital', 'cyber', 'tech', 'dystopian', 'electric', 'glow'],
                'description': 'High-quality cyberpunk wallpaper from Unsplash'
            },
            'architecture': {
                'search_term': 'architecture building',
                'keywords': ['architecture', 'building', 'structure', 'modern', 'urban', 'city', 'skyscraper', 'design', 'construction', 'bridge'],
                'description': 'High-quality architecture wallpaper from Unsplash'
            },
            'art': {
                'search_term': 'digital art',
                'keywords': ['art', 'digital', 'painting', 'illustration', 'creative', 'artistic', 'design', 'contemporary', 'modern', 'gallery'],
                'description': 'High-quality art wallpaper from Unsplash'
            },
            'gradient': {
                'search_term': 'gradient color',
                'keywords': ['gradient', 'color', 'smooth', 'blend', 'transition', 'spectrum', 'rainbow', 'ombre', 'fade', 'abstract'],
                'description': 'High-quality gradient wallpaper from Unsplash'
            },
            'technology': {
                'search_term': 'technology digital',
                'keywords': ['technology', 'tech', 'digital', 'computer', 'circuit', 'electronic', 'innovation', 'futuristic', 'data', 'coding'],
                'description': 'High-quality technology wallpaper from Unsplash'
            },
            'dark': {
                'search_term': 'dark moody',
                'keywords': ['dark', 'moody', 'black', 'shadow', 'dramatic', 'gothic', 'mysterious', 'noir', 'deep', 'night'],
                'description': 'High-quality dark wallpaper from Unsplash'
            },
            'neon': {
                'search_term': 'neon lights',
                'keywords': ['neon', 'lights', 'electric', 'bright', 'glowing', 'colorful', 'vibrant', 'synthwave', 'retro', 'fluorescent'],
                'description': 'High-quality neon wallpaper from Unsplash'
            },
            'pastel': {
                'search_term': 'pastel soft',
                'keywords': ['pastel', 'soft', 'gentle', 'light', 'pale', 'sweet', 'kawaii', 'dreamy', 'delicate', 'feminine'],
                'description': 'High-quality pastel wallpaper from Unsplash'
            },
            'vintage': {
                'search_term': 'vintage retro',
                'keywords': ['vintage', 'retro', 'old', 'classic', 'antique', 'nostalgic', 'aged', 'historical', 'traditional', 'timeless'],
                'description': 'High-quality vintage wallpaper from Unsplash'
            },
            'seasonal': {
                'search_term': 'seasonal holiday',
                'keywords': ['seasonal', 'holiday', 'christmas', 'halloween', 'spring', 'summer', 'autumn', 'winter', 'celebration', 'festive'],
                'description': 'High-quality seasonal wallpaper from Unsplash'
            },
            'gaming': {
                'search_term': 'gaming esports',
                'keywords': ['gaming', 'esports', 'video games', 'console', 'controller', 'digital', 'virtual', 'gamer', 'tech', 'entertainment'],
                'description': 'High-quality gaming wallpaper from Unsplash'
            },
            'cars': {
                'search_term': 'cars automotive',
                'keywords': ['cars', 'automotive', 'vehicle', 'sports car', 'luxury', 'racing', 'speed', 'motor', 'drive', 'transport'],
                'description': 'High-quality automotive wallpaper from Unsplash'
            },
            'sports': {
                'search_term': 'sports fitness',
                'keywords': ['sports', 'fitness', 'athletic', 'exercise', 'training', 'competition', 'team', 'outdoor', 'activity', 'health'],
                'description': 'High-quality sports wallpaper from Unsplash'
            },
            'music': {
                'search_term': 'music instruments',
                'keywords': ['music', 'instruments', 'concert', 'sound', 'audio', 'melody', 'rhythm', 'performance', 'band', 'acoustic'],
                'description': 'High-quality music wallpaper from Unsplash'
            },
            'movies': {
                'search_term': 'cinema film',
                'keywords': ['cinema', 'film', 'movie', 'theater', 'entertainment', 'dramatic', 'cinematic', 'scene', 'story', 'visual'],
                'description': 'High-quality cinema wallpaper from Unsplash'
            }
        }
        
        # Track downloaded hashes globally
        self.downloaded_hashes: Set[str] = set()
        self.hash_lock = threading.Lock()
        self.load_existing_hashes()
        
        # Enhanced Chrome options
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
        """Load existing hashes from all sources"""
        hash_files = [
            'high_quality_abstract/abstract_hashes.json',
            'high_quality_space/space_hashes.json',
            'more_space_images/space_hashes.json',
            f'{self.base_output_dir}/global_hashes.json'
        ]
        
        # Also check for category-specific hash files
        for category in self.categories.keys():
            hash_files.append(f'{self.base_output_dir}/{category}_hashes.json')
        
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
    
    def save_hashes(self, category: str = None):
        """Save hashes"""
        if category:
            hash_file = self.base_output_dir / f'{category}_hashes.json'
        else:
            hash_file = self.base_output_dir / 'global_hashes.json'
            
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
        """Enhanced scrolling and loading with multiple strategies"""
        logger.info("Attempting enhanced content loading...")
        
        # Strategy 1: Multiple scroll attempts with button detection
        for scroll_attempt in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for load more buttons
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load more') or contains(text(), 'Show more') or contains(text(), 'More')]")
            if load_more_buttons:
                try:
                    button = load_more_buttons[0]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    logger.info("✅ Clicked 'Load more' button")
                    time.sleep(6)
                    return True
                except Exception as e:
                    logger.debug(f"Button click failed: {e}")
        
        # Strategy 2: Infinite scroll detection
        try:
            current_height = driver.execute_script("return document.body.scrollHeight")
            # Progressive scrolling
            for i in range(15):
                scroll_position = current_height * (i + 1) / 15
                driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.8)
            
            # Wait and check for new content
            time.sleep(4)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > current_height:
                logger.info("✅ Infinite scroll triggered - content loaded")
                return True
        except Exception as e:
            logger.debug(f"Infinite scroll failed: {e}")
        
        # Strategy 3: Page Down + End key combination
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            for _ in range(8):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)
            body.send_keys(Keys.END)
            time.sleep(3)
            
            # Check for buttons again
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load') or contains(text(), 'More') or contains(text(), 'Show')]")
            if load_more_buttons:
                button = load_more_buttons[0]
                driver.execute_script("arguments[0].click();", button)
                logger.info("✅ Button clicked after Page Down")
                time.sleep(6)
                return True
        except Exception as e:
            logger.debug(f"Page Down strategy failed: {e}")
        
        # Strategy 4: Generic button search with click attempts
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='button'], button:not([type])")
            for button in buttons:
                try:
                    button_text = button.text.lower()
                    if any(word in button_text for word in ['load', 'more', 'show', 'next', 'continue']):
                        driver.execute_script("arguments[0].click();", button)
                        logger.info(f"✅ Clicked button: {button_text}")
                        time.sleep(6)
                        return True
                except:
                    continue
        except Exception as e:
            logger.debug(f"Generic button search failed: {e}")
        
        logger.warning("❌ Could not load more content")
        return False
    
    def scrape_category_images(self, category: str, max_pages: int = 8) -> List[Dict]:
        """Scrape images for a specific category"""
        if category not in self.categories:
            logger.error(f"Unknown category: {category}")
            return []
        
        config = self.categories[category]
        search_term = config['search_term']
        keywords = config['keywords']
        
        logger.info(f"Starting {category} scraping (max {max_pages} pages)")
        
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
            
            while page_count < max_pages and consecutive_failures < 3:
                page_count += 1
                logger.info(f"Processing {category} page {page_count}/{max_pages}")
                
                # Wait for images to load
                time.sleep(3)
                
                # Get all images
                image_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='images.unsplash.com']")
                
                page_images = []
                for img_element in image_elements:
                    try:
                        src = img_element.get_attribute('src')
                        alt = img_element.get_attribute('alt') or f'{category.title()} wallpaper'
                        
                        # Skip small images
                        if any(size in src for size in ['w=400', 'w=200', 'w=150', 'w=100']):
                            continue
                        
                        # Filter by keywords
                        alt_lower = alt.lower()
                        if any(keyword in alt_lower for keyword in keywords) or category in alt_lower:
                            high_res_url = self.get_high_res_url(src)
                            
                            image_info = {
                                'url': high_res_url,
                                'original_url': src,
                                'alt': alt,
                                'photographer': 'Unsplash Contributor',
                                'source': f'unsplash_{category}_bulk',
                                'category': category,
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
                logger.info(f"Found {len(unique_page_images)} unique {category} images on page {page_count}")
                
                if len(unique_page_images) == 0:
                    consecutive_failures += 1
                    logger.warning(f"No new images found on page {page_count} (failure {consecutive_failures}/3)")
                else:
                    consecutive_failures = 0
                
                # Try to load more content for next page
                if page_count < max_pages:
                    success = self.enhanced_scroll_and_load(driver)
                    if not success:
                        consecutive_failures += 1
                        if consecutive_failures >= 2:
                            logger.warning("Multiple pagination failures, stopping")
                            break
                
                # Rate limiting
                time.sleep(2)
            
            logger.info(f"Scraped {len(all_images)} total {category} images from {page_count} pages")
            return all_images
            
        except Exception as e:
            logger.error(f"Error during {category} scraping: {e}")
            return all_images
        finally:
            if driver:
                driver.quit()
    
    def download_image(self, image_info: Dict, index: int, category: str) -> Dict:
        """Download a single image"""
        try:
            url = image_info['url']
            filename = f"{category}_{index:03d}.jpg"
            
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
                    category_dir = self.base_output_dir / category
                    category_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save image
                    filepath = category_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Create metadata
                    config = self.categories[category]
                    metadata = {
                        'id': f"{category}_{index:03d}",
                        'source': f'unsplash_{category}_bulk',
                        'category': category,
                        'title': f'High-Quality {category.title()} Wallpaper {index}',
                        'description': f'{config["description"]}: {image_info.get("alt", f"{category} imagery")}',
                        'width': 1080,
                        'height': 1920,
                        'photographer': image_info.get('photographer', 'Unsplash Contributor'),
                        'tags': [category, 'wallpaper', 'hd', 'high resolution', 'mobile'] + config['keywords'][:5],
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
                        'alt': image_info.get('alt', '')[:50]
                    }
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        return {'status': 'error', 'error': str(e)}
                    time.sleep(1)
                    
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def download_category_images(self, category: str, images: List[Dict], target: int = 200) -> Dict:
        """Download all images for a category"""
        logger.info(f"Starting download of {len(images)} {category} images (target: {target})")
        
        random.shuffle(images)
        
        downloaded = 0
        duplicates = 0
        errors = 0
        too_small = 0
        
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = []
            for i, image_info in enumerate(images[:target*2], 1):
                future = executor.submit(self.download_image, image_info, i, category)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    if downloaded % 20 == 0:
                        logger.info(f"✅ {category}: {downloaded}/{target} - {result['filename']} ({result['size']} bytes)")
                elif result['status'] == 'duplicate':
                    duplicates += 1
                elif result['status'] == 'too_small':
                    too_small += 1
                elif result['status'] == 'error':
                    errors += 1
                
                if downloaded >= target:
                    break
        
        self.save_hashes(category)
        
        return {
            'downloaded': downloaded,
            'duplicates': duplicates,
            'too_small': too_small,
            'errors': errors,
            'target': target
        }

def main():
    parser = argparse.ArgumentParser(description='Multi-Category Unsplash Scraper')
    parser.add_argument('--categories', nargs='+', default=['nature', 'abstract', 'minimal'], help='Categories to scrape')
    parser.add_argument('--target', type=int, default=200, help='Target images per category')
    parser.add_argument('--pages', type=int, default=8, help='Max pages per category')
    parser.add_argument('--output', default='bulk_download', help='Output directory')
    
    args = parser.parse_args()
    
    print(f"🚀 Multi-Category Unsplash Scraper")
    print(f"=" * 60)
    print(f"📂 Categories: {', '.join(args.categories)}")
    print(f"🎯 Target per category: {args.target} images")
    print(f"📄 Max pages: {args.pages}")
    print(f"📁 Output: {args.output}")
    
    scraper = MultiCategoryScraper(args.output)
    
    total_start_time = time.time()
    total_results = {}
    
    for category in args.categories:
        if category not in scraper.categories:
            print(f"❌ Unknown category: {category}")
            continue
            
        print(f"\n🔍 Scraping {category.upper()} category...")
        start_time = time.time()
        
        # Scrape images
        images = scraper.scrape_category_images(category, max_pages=args.pages)
        
        if not images:
            print(f"❌ No {category} images found!")
            continue
        
        print(f"🎉 Found {len(images)} {category} images!")
        
        # Download images
        print(f"⬇️  Downloading {category} images...")
        results = scraper.download_category_images(category, images, target=args.target)
        
        category_time = time.time() - start_time
        total_results[category] = results
        
        print(f"\n✅ {category.upper()} COMPLETE!")
        print(f"Downloaded: {results['downloaded']}, Duplicates: {results['duplicates']}, Errors: {results['errors']}")
        print(f"Time: {category_time:.1f}s, Rate: {results['downloaded'] / category_time:.1f} images/s")
    
    # Summary
    total_time = time.time() - total_start_time
    total_downloaded = sum(r['downloaded'] for r in total_results.values())
    
    print(f"\n🎉 BULK SCRAPING COMPLETE!")
    print(f"=" * 60)
    print(f"📊 Total downloaded: {total_downloaded}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"🚀 Average rate: {total_downloaded / total_time:.1f} images/second")
    
    print(f"\n📂 Results by category:")
    for category, results in total_results.items():
        print(f"  {category}: {results['downloaded']} images")
    
    print(f"\n🔄 Next steps:")
    print(f"1. Review quality: Check {args.output}/ directories")
    print(f"2. Move to wallpapers: mv {args.output}/*/*.jpg wallpapers/")
    print(f"3. Move metadata: mv {args.output}/*/*.json wallpapers/")
    print(f"4. Generate index: python3 scripts/generate_index.py --update-all")

if __name__ == "__main__":
    main()