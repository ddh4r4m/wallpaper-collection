#!/usr/bin/env python3
"""
Scrape AI wallpapers from specific Civitai tag URLs
Usage: python3 tools/scrape_civitai_tags.py --count 50
"""

import os
import sys
import json
import argparse
import requests
import time
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from add_wallpaper import WallpaperManager

class CivitaiTagScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.download_dir = Path("/tmp/civitai_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Tag URLs with their categories
        self.tag_urls = {
            'abstract': ['https://civitai.com/images?tags=5193', 'https://civitai.com/images?tags=111763'],
            'cyberpunk': ['https://civitai.com/images?tags=414', 'https://civitai.com/images?tags=617'],
            'space': ['https://civitai.com/images?tags=172', 'https://civitai.com/images?tags=213'],
            'ai': ['https://civitai.com/images?tags=3060', 'https://civitai.com/images?tags=5499']
        }
        
        # Setup Chrome driver
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Please install ChromeDriver: brew install chromedriver")
            sys.exit(1)
    
    def scroll_and_load_images(self, url, target_count=20):
        """Scroll down and wait for images to load dynamically"""
        print(f"🔍 Loading images from: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Initial page load
            
            # Accept cookies/terms if present
            try:
                accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree')]")
                accept_button.click()
                time.sleep(2)
            except:
                pass
            
            images_found = []
            scroll_attempts = 0
            max_scrolls = 10
            
            while len(images_found) < target_count and scroll_attempts < max_scrolls:
                # Scroll down to load more images
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Wait for images to load
                
                # Find all image elements
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='image.civitai.com'], img[src*='civitai.com']")
                
                for img in img_elements:
                    if len(images_found) >= target_count:
                        break
                    
                    try:
                        src = img.get_attribute('src')
                        if not src or 'placeholder' in src.lower() or 'loading' in src.lower():
                            continue
                        
                        # Get high quality version
                        if '/original/' not in src and '/width=' in src:
                            # Replace with original quality
                            src = re.sub(r'/width=\d+', '/original=true', src)
                        
                        # Get metadata from parent elements
                        parent = img.find_element(By.XPATH, "./ancestor::*[contains(@class, 'card') or contains(@class, 'image')][1]")
                        
                        # Try to get title and stats
                        title = ""
                        stats = {}
                        
                        try:
                            title_elem = parent.find_element(By.CSS_SELECTOR, "[data-testid='image-title'], .title, h3, h4")
                            title = title_elem.text.strip()
                        except:
                            pass
                        
                        try:
                            # Look for reaction/like counts
                            reactions = parent.find_elements(By.CSS_SELECTOR, "[data-testid*='reaction'], .reactions, .likes")
                            for reaction in reactions:
                                text = reaction.text.strip()
                                if text.isdigit():
                                    stats['reactions'] = int(text)
                                    break
                        except:
                            pass
                        
                        image_info = {
                            'url': src,
                            'title': title[:100] if title else 'Civitai AI Art',
                            'stats': stats,
                            'source': 'civitai',
                            'id': hashlib.md5(src.encode()).hexdigest()[:8]
                        }
                        
                        # Avoid duplicates
                        if not any(existing['url'] == src for existing in images_found):
                            images_found.append(image_info)
                            print(f"  📸 Found image {len(images_found)}: {title[:50]}...")
                    
                    except Exception as e:
                        continue
                
                scroll_attempts += 1
                print(f"  📜 Scroll {scroll_attempts}: Found {len(images_found)} images")
                
                # Break if no new images found in last few scrolls
                if scroll_attempts > 3 and len(images_found) == 0:
                    break
            
            print(f"✅ Found {len(images_found)} images from tag URL")
            return images_found
            
        except Exception as e:
            print(f"❌ Error loading images from {url}: {e}")
            return []
    
    def download_image(self, image_info, filename):
        """Download and validate a Civitai image"""
        try:
            filepath = self.download_dir / filename
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://civitai.com/'
            }
            
            response = self.session.get(image_info['url'], headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"❌ Not an image: {content_type}")
                return None
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify it's a valid image
            try:
                from PIL import Image
                with Image.open(filepath) as img:
                    if img.width < 800 or img.height < 600:
                        print(f"❌ Image too small: {img.width}x{img.height}")
                        os.remove(filepath)
                        return None
                    
                    # Check file size
                    file_size = filepath.stat().st_size
                    if file_size < 50000:  # 50KB minimum
                        print(f"❌ File too small: {file_size} bytes")
                        os.remove(filepath)
                        return None
                    
            except Exception as e:
                print(f"❌ Invalid image: {e}")
                if filepath.exists():
                    os.remove(filepath)
                return None
            
            return filepath
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def scrape_category_tags(self, category, needed_count):
        """Scrape images from all tag URLs for a category"""
        print(f"\n🎯 Scraping {needed_count} Civitai wallpapers for category: {category}")
        
        if category not in self.tag_urls:
            print(f"❌ No tag URLs configured for category: {category}")
            return 0
        
        all_images = []
        urls = self.tag_urls[category]
        images_per_url = max(needed_count // len(urls), 10)
        
        for url in urls:
            try:
                images = self.scroll_and_load_images(url, images_per_url)
                all_images.extend(images)
                time.sleep(2)  # Rate limiting between URLs
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
                continue
        
        # Remove duplicates
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        print(f"📋 Found {len(unique_images)} unique Civitai images")
        
        # Download and add images
        added_count = 0
        for i, image_info in enumerate(unique_images):
            if added_count >= needed_count:
                break
            
            print(f"⬇️  Processing Civitai image {i+1}/{len(unique_images)} (added: {added_count}/{needed_count})")
            
            # Create filename
            image_id = image_info.get('id', hashlib.md5(image_info['url'].encode()).hexdigest()[:8])
            filename = f"{category}_civitai_{image_id}.jpg"
            filepath = self.download_image(image_info, filename)
            
            if filepath:
                try:
                    # Create enhanced title and tags
                    title = self.create_civitai_title(category, image_info)
                    tags = self.create_civitai_tags(category, image_info)
                    
                    # Get next ID
                    next_id = self.manager.get_next_id(category)
                    
                    # Set up paths
                    output_path = self.manager.wallpapers_dir / category / f"{next_id}.jpg"
                    thumb_path = self.manager.thumbnails_dir / category / f"{next_id}.jpg"
                    
                    # Ensure directories exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    thumb_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Process main image
                    processed_info = self.manager.process_image(filepath, output_path)
                    
                    # Generate thumbnail
                    self.manager.generate_thumbnail(output_path, thumb_path)
                    
                    # Extract metadata
                    metadata = self.manager.extract_metadata(output_path, processed_info)
                    metadata.update(self.create_civitai_metadata(image_info))
                    
                    # Save metadata
                    self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                    (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                    
                    self.manager.save_metadata(category, next_id, title, tags, metadata)
                    
                    added_count += 1
                    print(f"✅ Added Civitai wallpaper {category}_{next_id} ({added_count}/{needed_count})")
                    
                except Exception as e:
                    print(f"❌ Failed to add Civitai image: {e}")
                finally:
                    # Clean up
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"🎉 Successfully added {added_count} Civitai wallpapers to {category}")
        return added_count
    
    def create_civitai_title(self, category, image_info):
        """Create an appropriate title for Civitai wallpaper"""
        title = image_info.get('title', '').strip()
        
        if title and title != 'Civitai AI Art':
            return f"{title[:40]} - Civitai AI"
        else:
            return f"{category.title()} AI Art - Civitai"
    
    def create_civitai_tags(self, category, image_info):
        """Create appropriate tags for Civitai wallpaper"""
        tags = [category, 'ai-generated', 'civitai', 'stable-diffusion', 'hd', 'mobile']
        
        # Add reaction-based quality tags
        stats = image_info.get('stats', {})
        reactions = stats.get('reactions', 0)
        
        if reactions > 100:
            tags.append('highly-rated')
        elif reactions > 20:
            tags.append('popular')
        
        tags.append('community-rated')
        
        return tags
    
    def create_civitai_metadata(self, image_info):
        """Create enhanced metadata for Civitai wallpaper"""
        metadata = {
            'ai_source': 'civitai',
            'ai_generated': True,
            'source_platform': 'civitai.com'
        }
        
        # Add stats if available
        stats = image_info.get('stats', {})
        if stats:
            metadata['civitai_stats'] = stats
        
        if stats.get('reactions'):
            metadata['community_reactions'] = stats['reactions']
        
        return metadata
    
    def close_driver(self):
        """Close the Chrome driver"""
        try:
            self.driver.quit()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Scrape AI wallpapers from Civitai tag URLs')
    parser.add_argument('--category', choices=['abstract', 'cyberpunk', 'space', 'ai'], help='Specific category to scrape')
    parser.add_argument('--count', type=int, default=20, help='Number of images to scrape per category')
    
    args = parser.parse_args()
    
    # Check for required packages
    try:
        from selenium import webdriver
        from PIL import Image
    except ImportError:
        print("❌ Missing required packages. Installing...")
        os.system("pip install selenium pillow")
        print("💡 Also install ChromeDriver: brew install chromedriver")
        print("✅ Packages installed. Please run the script again.")
        sys.exit(1)
    
    scraper = CivitaiTagScraper()
    
    try:
        if args.category:
            scraper.scrape_category_tags(args.category, args.count)
        else:
            # Scrape all categories
            total_added = 0
            for category in ['abstract', 'cyberpunk', 'space', 'ai']:
                added = scraper.scrape_category_tags(category, args.count)
                total_added += added
                time.sleep(3)  # Break between categories
            
            print(f"\n🎉 Total Civitai wallpapers added: {total_added}")
    
    finally:
        scraper.close_driver()

if __name__ == '__main__':
    main()