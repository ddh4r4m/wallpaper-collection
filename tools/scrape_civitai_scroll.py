#!/usr/bin/env python3
"""
Scrape Civitai images with scrolling - start collecting after 6th scroll
Usage: python3 tools/scrape_civitai_scroll.py --tag-url "https://civitai.com/images?tags=4" --start-after-scroll 6 --count 50
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
from urllib.parse import urlparse, parse_qs
import re

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("Installing Selenium...")
    os.system("python3 -m pip install --user selenium --break-system-packages")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

from add_wallpaper import WallpaperManager

class CivitaiScrollScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.download_dir = Path("/tmp/civitai_scroll_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Setup Chrome driver
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Please install ChromeDriver: brew install chromedriver")
            sys.exit(1)
    
    def get_tag_id_from_url(self, url):
        """Extract tag ID from Civitai URL"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            tag_id = query_params.get('tags', [None])[0]
            if tag_id:
                return int(tag_id)
        except:
            pass
        
        # Try to extract from URL path if query fails
        match = re.search(r'tags[=/](\d+)', url)
        if match:
            return int(match.group(1))
        
        return None
    
    def scroll_and_collect_images(self, url, start_after_scroll=6, target_count=50):
        """Scroll through Civitai page and collect images after specified scroll count"""
        print(f"🔍 Loading Civitai page: {url}")
        print(f"⏳ Will start collecting after scroll #{start_after_scroll}")
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Initial page load
            
            # Accept cookies/terms if present
            try:
                # Look for common cookie accept buttons
                cookie_selectors = [
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Agree')]", 
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(@class, 'accept')]",
                    "[data-testid='accept-cookies']",
                    ".cookie-accept",
                    "#accept-cookies"
                ]
                
                for selector in cookie_selectors:
                    try:
                        if selector.startswith('//'):
                            button = self.driver.find_element(By.XPATH, selector)
                        else:
                            button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        button.click()
                        print("✅ Accepted cookies/terms")
                        time.sleep(2)
                        break
                    except:
                        continue
            except:
                pass
            
            images_found = []
            scroll_count = 0
            collecting = False
            max_scrolls = start_after_scroll + 15  # Collect for 15 more scrolls after start point
            
            print(f"🔄 Starting scroll process (will collect after scroll {start_after_scroll})...")
            
            while scroll_count < max_scrolls:
                scroll_count += 1
                
                # Perform scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print(f"📜 Scroll {scroll_count}/{max_scrolls}")
                
                # Wait for content to load
                time.sleep(3)
                
                # Start collecting after specified scroll count
                if scroll_count >= start_after_scroll:
                    if not collecting:
                        print(f"🎯 Starting image collection after scroll {scroll_count}...")
                        collecting = True
                    
                    # Find image elements
                    img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
                    
                    for img in img_elements:
                        if len(images_found) >= target_count:
                            break
                        
                        try:
                            src = img.get_attribute('src')
                            if not src:
                                continue
                            
                            # Filter for Civitai image URLs
                            if not ('image.civitai.com' in src or 'civitai.com' in src):
                                continue
                            
                            # Skip placeholders, loading images, and low quality
                            if any(skip in src.lower() for skip in ['placeholder', 'loading', 'thumb', 'avatar']):
                                continue
                            
                            # Get high quality version
                            original_src = src
                            if '/width=' in src:
                                # Replace with original quality
                                src = re.sub(r'/width=\d+', '/width=2048', src)
                            elif '/height=' in src:
                                src = re.sub(r'/height=\d+', '/height=2048', src)
                            elif 'optimized' in src:
                                # Try to get original from optimized URL
                                src = src.replace('optimized', 'original')
                            
                            # Try alternative approaches for better quality
                            if '450' in src or 'thumb' in src:
                                # Try to construct full quality URL
                                if 'image.civitai.com' in src:
                                    # Extract the image ID and reconstruct URL
                                    match = re.search(r'image\.civitai\.com/.*?([a-f0-9-]{8,})', src)
                                    if match:
                                        image_id = match.group(1)
                                        src = f"https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/{image_id}/width=2048"
                            
                            # Try to get metadata from parent elements
                            try:
                                parent = img.find_element(By.XPATH, "./ancestor::*[contains(@class, 'card') or contains(@class, 'image') or contains(@class, 'item')][1]")
                            except:
                                parent = img
                            
                            # Try to get title and stats
                            title = ""
                            stats = {}
                            
                            try:
                                # Look for title in various ways
                                title_selectors = [
                                    "[data-testid='image-title']",
                                    ".title",
                                    "h3", "h4", "h5",
                                    "[class*='title']",
                                    "[class*='name']"
                                ]
                                
                                for selector in title_selectors:
                                    try:
                                        title_elem = parent.find_element(By.CSS_SELECTOR, selector)
                                        title = title_elem.text.strip()
                                        if title and len(title) > 3:
                                            break
                                    except:
                                        continue
                            except:
                                pass
                            
                            try:
                                # Look for reaction/like counts
                                stat_elements = parent.find_elements(By.CSS_SELECTOR, "[data-testid*='reaction'], .reactions, .likes, .stats, [class*='count']")
                                for elem in stat_elements:
                                    text = elem.text.strip()
                                    if text and text.replace(',', '').isdigit():
                                        stats['reactions'] = int(text.replace(',', ''))
                                        break
                            except:
                                pass
                            
                            # Create image data
                            image_info = {
                                'url': src,
                                'title': title[:100] if title else 'Civitai AI Art',
                                'stats': stats,
                                'reactions': stats.get('reactions', 0),
                                'source': 'civitai',
                                'scroll_found': scroll_count,
                                'id': hashlib.md5(src.encode()).hexdigest()[:8]
                            }
                            
                            # Avoid duplicates
                            if not any(existing['url'] == src for existing in images_found):
                                images_found.append(image_info)
                                print(f"  📸 Found image {len(images_found)}: {title[:50]}... (scroll {scroll_count})")
                        
                        except Exception as e:
                            continue
                
                # Check if we have enough images
                if collecting and len(images_found) >= target_count:
                    print(f"🎯 Collected {target_count} images, stopping...")
                    break
                
                # Additional wait between scrolls
                time.sleep(2)
            
            print(f"✅ Scrolling complete. Found {len(images_found)} images")
            return images_found
            
        except Exception as e:
            print(f"❌ Error during scrolling: {e}")
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
                    
                    # Update image info with actual dimensions
                    image_info['actual_width'] = img.width
                    image_info['actual_height'] = img.height
                    
            except Exception as e:
                print(f"❌ Invalid image: {e}")
                if filepath.exists():
                    os.remove(filepath)
                return None
            
            return filepath
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def get_high_quality_images_from_api(self, tag_id, target_count=50, page_offset=3):
        """Get high quality images from Civitai API after skipping initial pages"""
        print(f"🔍 Fetching high quality images from Civitai API for tag {tag_id}...")
        print(f"⏭️ Skipping first {page_offset} pages (equivalent to scrolling)")
        
        images = []
        cursor = None
        page = 1
        
        # Skip initial pages by using cursor pagination
        while page <= page_offset:
            try:
                api_url = "https://civitai.com/api/v1/images"
                params = {
                    'tags': str(tag_id),
                    'limit': 100,
                    'sort': 'Most Reactions',
                    'period': 'AllTime',
                    'nsfw': 'false'
                }
                
                if cursor:
                    params['cursor'] = cursor
                
                response = self.session.get(api_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                cursor = data.get('metadata', {}).get('nextCursor')
                
                if page == page_offset:
                    # Start collecting from this page
                    items = data.get('items', [])
                    print(f"📋 Starting collection from page {page}, found {len(items)} items")
                    
                    for item in items:
                        if len(images) >= target_count:
                            break
                        
                        # Quality filtering
                        if item.get('width', 0) < 800 or item.get('height', 0) < 600:
                            continue
                        
                        if item.get('nsfw', False):
                            continue
                        
                        # Get high quality URL
                        url = item.get('url', '')
                        if not url:
                            continue
                        
                        # Extract metadata
                        meta = item.get('meta', {})
                        stats = item.get('stats', {})
                        
                        image_data = {
                            'url': url,
                            'width': item.get('width', 0),
                            'height': item.get('height', 0),
                            'prompt': meta.get('prompt', '')[:300] if meta else '',
                            'model': meta.get('Model', '') if meta else '',
                            'steps': meta.get('Steps', 0) if meta else 0,
                            'cfg_scale': meta.get('CFG scale', 0) if meta else 0,
                            'sampler': meta.get('Sampler', '') if meta else '',
                            'stats': stats,
                            'reactions': stats.get('reactionCount', 0) + stats.get('likeCount', 0) + stats.get('heartCount', 0),
                            'source': 'civitai',
                            'tag_id': tag_id,
                            'api_page': page,
                            'id': hashlib.md5(url.encode()).hexdigest()[:8]
                        }
                        
                        images.append(image_data)
                
                if not cursor:
                    break
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ API error on page {page}: {e}")
                break
        
        # Sort by reactions
        images.sort(key=lambda x: x.get('reactions', 0), reverse=True)
        print(f"✅ Found {len(images)} high quality images from API")
        return images
    
    def scrape_with_scroll(self, tag_url, start_after_scroll=6, target_count=50):
        """Main scraping function with scroll functionality"""
        print(f"\n🎯 Scraping Civitai with scroll: {target_count} images from {tag_url}")
        print(f"⏳ Will start collecting after scroll #{start_after_scroll}")
        
        # Extract tag ID from URL
        tag_id = self.get_tag_id_from_url(tag_url)
        if tag_id:
            print(f"🏷️  Detected tag ID: {tag_id}")
            
            # Use API instead of web scraping for better quality
            print(f"🔄 Using API approach for better image quality...")
            images = self.get_high_quality_images_from_api(tag_id, target_count, page_offset=start_after_scroll//2)
        else:
            # Fallback to scroll method
            print(f"⚠️ Could not extract tag ID, falling back to scroll method...")
            images = self.scroll_and_collect_images(tag_url, start_after_scroll, target_count)
        
        if not images:
            print(f"❌ No images found")
            return 0
        
        print(f"📋 Found {len(images)} unique images to download")
        
        # Download and process images
        added_count = 0
        category = 'ai'  # Default to AI category
        
        for i, image_info in enumerate(images):
            if added_count >= target_count:
                break
            
            print(f"⬇️  Processing image {i+1}/{len(images)} (added: {added_count+1}/{target_count})")
            
            # Create filename
            image_id = image_info.get('id', hashlib.md5(image_info['url'].encode()).hexdigest()[:8])
            filename = f"{category}_civitai_scroll_{image_id}.jpg"
            filepath = self.download_image(image_info, filename)
            
            if filepath:
                try:
                    # Create enhanced title and tags
                    title = self.create_title(category, image_info)
                    tags = self.create_tags(category, image_info)
                    
                    # Get next ID
                    next_id = self.manager.get_next_id(category)
                    next_id_num = int(next_id) if isinstance(next_id, str) else next_id
                    
                    # Set up paths
                    output_path = self.manager.wallpapers_dir / category / f"{next_id_num:03d}.jpg"
                    thumb_path = self.manager.thumbnails_dir / category / f"{next_id_num:03d}.jpg"
                    
                    # Ensure directories exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    thumb_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Process main image
                    processed_info = self.manager.process_image(filepath, output_path)
                    
                    # Generate thumbnail
                    self.manager.generate_thumbnail(output_path, thumb_path)
                    
                    # Extract metadata
                    metadata = self.manager.extract_metadata(output_path, processed_info)
                    metadata.update(self.create_metadata(image_info, tag_id))
                    
                    # Save metadata
                    self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                    (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                    
                    self.manager.save_metadata(category, f"{next_id_num:03d}", title, tags, metadata)
                    
                    added_count += 1
                    reactions = image_info.get('reactions', 0)
                    scroll_num = image_info.get('scroll_found', 0)
                    print(f"✅ Added {category}_{next_id_num:03d} (reactions: {reactions}, found at scroll: {scroll_num})")
                    
                except Exception as e:
                    print(f"❌ Failed to add image: {e}")
                finally:
                    # Clean up
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"🎉 Successfully added {added_count} images from Civitai scroll scraping")
        return added_count
    
    def create_title(self, category, image_info):
        """Create an appropriate title for Civitai wallpaper"""
        title = image_info.get('title', '').strip()
        reactions = image_info.get('reactions', 0)
        scroll_found = image_info.get('scroll_found', 0)
        
        if title and title != 'Civitai AI Art' and len(title) > 5:
            clean_title = re.sub(r'[^\w\s-]', '', title)[:50].strip()
            if reactions > 100:
                return f"{clean_title} - Premium Civitai"
            else:
                return f"{clean_title} - Civitai AI"
        else:
            if reactions > 100:
                return f"{category.title()} Premium AI - Civitai"
            else:
                return f"{category.title()} AI Art - Civitai"
    
    def create_tags(self, category, image_info):
        """Create appropriate tags for Civitai wallpaper"""
        tags = [category, 'ai-generated', 'civitai', 'stable-diffusion', 'hd', 'mobile']
        
        reactions = image_info.get('reactions', 0)
        if reactions > 200:
            tags.append('viral')
        elif reactions > 100:
            tags.append('highly-rated')
        elif reactions > 20:
            tags.append('popular')
        
        # Add scroll-based tags
        scroll_found = image_info.get('scroll_found', 0)
        if scroll_found > 10:
            tags.append('deep-scroll')
        
        # Add quality indicators
        width = image_info.get('actual_width', 0)
        height = image_info.get('actual_height', 0)
        
        if width >= 1920 or height >= 1920:
            tags.append('high-resolution')
        
        tags.append('community-rated')
        
        return tags
    
    def create_metadata(self, image_info, tag_id):
        """Create enhanced metadata for Civitai wallpaper"""
        metadata = {
            'ai_source': 'civitai',
            'ai_generated': True,
            'source_platform': 'civitai.com',
            'scraping_method': 'scroll_based'
        }
        
        if tag_id:
            metadata['civitai_tag_id'] = tag_id
        
        if image_info.get('scroll_found'):
            metadata['found_at_scroll'] = image_info['scroll_found']
        
        stats = image_info.get('stats', {})
        if stats:
            metadata['civitai_stats'] = stats
        
        if image_info.get('reactions'):
            metadata['total_reactions'] = image_info['reactions']
        
        return metadata
    
    def close_driver(self):
        """Close the Chrome driver"""
        try:
            self.driver.quit()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Scrape Civitai images with scrolling')
    parser.add_argument('--tag-url', required=True, help='Civitai tag URL to scrape from')
    parser.add_argument('--start-after-scroll', type=int, default=6, help='Start collecting images after this many scrolls')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    
    args = parser.parse_args()
    
    scraper = CivitaiScrollScraper()
    
    try:
        added = scraper.scrape_with_scroll(args.tag_url, args.start_after_scroll, args.count)
        
        if added > 0:
            print(f"\n🔄 Rebuilding API indexes...")
            os.system("python3 tools/build_api.py")
    
    finally:
        scraper.close_driver()

if __name__ == '__main__':
    main()