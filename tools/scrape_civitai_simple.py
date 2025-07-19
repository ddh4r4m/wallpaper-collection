#!/usr/bin/env python3
"""
Simple Civitai scraper using requests and BeautifulSoup
Usage: python3 tools/scrape_civitai_simple.py --category abstract --count 20
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
from urllib.parse import urlparse, urljoin, parse_qs
import re
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing BeautifulSoup...")
    os.system("python3 -m pip install --user beautifulsoup4 --break-system-packages")
    from bs4 import BeautifulSoup

from add_wallpaper import WallpaperManager

class SimpleCivitaiScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.download_dir = Path("/tmp/civitai_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Civitai API endpoints for tags
        self.tag_mappings = {
            'abstract': [5193, 111763],
            'cyberpunk': [414, 617], 
            'space': [172, 213],
            'ai': [3060, 5499]
        }
    
    def get_images_from_tag(self, tag_id, limit=20):
        """Get images from Civitai API using tag ID"""
        print(f"🔍 Fetching images for tag {tag_id}...")
        
        try:
            # Use Civitai API directly
            api_url = "https://civitai.com/api/v1/images"
            params = {
                'tags': str(tag_id),
                'limit': min(limit, 100),
                'sort': 'Most Reactions',
                'period': 'Week',
                'nsfw': 'false'
            }
            
            response = self.session.get(api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"  ✅ API returned {len(items)} images for tag {tag_id}")
                return items
            else:
                print(f"  ❌ API request failed: {response.status_code}")
                
                # Fallback to web scraping
                return self.fallback_web_scrape(tag_id, limit)
                
        except Exception as e:
            print(f"  ❌ API error: {e}")
            # Fallback to web scraping
            return self.fallback_web_scrape(tag_id, limit)
    
    def fallback_web_scrape(self, tag_id, limit=20):
        """Fallback web scraping method"""
        print(f"  🕷️  Falling back to web scraping for tag {tag_id}...")
        
        try:
            url = f"https://civitai.com/images?tags={tag_id}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"  ❌ Web page request failed: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for JSON data in script tags (Next.js apps often have this)
            script_tags = soup.find_all('script', type='application/json')
            images = []
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    # Recursively search for image data
                    found_images = self.extract_images_from_json(data)
                    images.extend(found_images)
                    if len(images) >= limit:
                        break
                except:
                    continue
            
            # Also try to find image URLs in the HTML
            img_tags = soup.find_all('img')
            for img in img_tags:
                if len(images) >= limit:
                    break
                
                src = img.get('src', '')
                if 'image.civitai.com' in src and 'placeholder' not in src:
                    # Convert to high quality URL
                    if '/width=' in src:
                        src = re.sub(r'/width=\d+', '/original=true', src)
                    
                    images.append({
                        'url': src,
                        'width': 1024,  # Default assumption
                        'height': 1024,
                        'meta': {},
                        'stats': {'reactionCount': 0}
                    })
            
            print(f"  ✅ Web scraping found {len(images)} images")
            return images[:limit]
            
        except Exception as e:
            print(f"  ❌ Web scraping error: {e}")
            return []
    
    def extract_images_from_json(self, data, images=None):
        """Recursively extract image data from JSON"""
        if images is None:
            images = []
        
        if isinstance(data, dict):
            # Look for image-like objects
            if 'url' in data and 'image.civitai.com' in str(data.get('url', '')):
                images.append(data)
            else:
                for value in data.values():
                    self.extract_images_from_json(value, images)
        
        elif isinstance(data, list):
            for item in data:
                self.extract_images_from_json(item, images)
        
        return images
    
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
    
    def scrape_category(self, category, needed_count):
        """Scrape images for a specific category"""
        print(f"\n🎯 Scraping {needed_count} Civitai wallpapers for category: {category}")
        
        if category not in self.tag_mappings:
            print(f"❌ No tag mapping for category: {category}")
            return 0
        
        all_images = []
        tag_ids = self.tag_mappings[category]
        images_per_tag = max(needed_count // len(tag_ids), 10)
        
        for tag_id in tag_ids:
            try:
                images = self.get_images_from_tag(tag_id, images_per_tag)
                
                # Process and filter images
                for item in images:
                    if len(all_images) >= needed_count * 2:  # Get extra for filtering
                        break
                    
                    # Basic quality checks
                    if item.get('width', 0) < 800 or item.get('height', 0) < 600:
                        continue
                    
                    if item.get('nsfw', False):
                        continue
                    
                    # Get high quality URL
                    url = item.get('url', '')
                    if not url:
                        continue
                    
                    # Ensure we get original quality
                    if '/width=' in url:
                        url = re.sub(r'/width=\d+', '/original=true', url)
                    
                    meta = item.get('meta', {})
                    stats = item.get('stats', {})
                    
                    image_data = {
                        'url': url,
                        'width': item.get('width', 0),
                        'height': item.get('height', 0),
                        'prompt': meta.get('prompt', '')[:200] if meta else '',
                        'model': meta.get('Model', '') if meta else '',
                        'stats': stats,
                        'reactions': stats.get('reactionCount', 0),
                        'source': 'civitai',
                        'id': hashlib.md5(url.encode()).hexdigest()[:8]
                    }
                    
                    all_images.append(image_data)
                
                time.sleep(2)  # Rate limiting between tags
                
            except Exception as e:
                print(f"❌ Error processing tag {tag_id}: {e}")
                continue
        
        # Remove duplicates and sort by reactions
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        unique_images.sort(key=lambda x: x.get('reactions', 0), reverse=True)
        
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
                    title = self.create_title(category, image_info)
                    tags = self.create_tags(category, image_info)
                    
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
                    metadata.update(self.create_metadata(image_info))
                    
                    # Save metadata
                    self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                    (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                    
                    self.manager.save_metadata(category, next_id, title, tags, metadata)
                    
                    added_count += 1
                    reactions = image_info.get('reactions', 0)
                    print(f"✅ Added Civitai wallpaper {category}_{next_id} (reactions: {reactions})")
                    
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
    
    def create_title(self, category, image_info):
        """Create an appropriate title for Civitai wallpaper"""
        prompt = image_info.get('prompt', '').strip()
        reactions = image_info.get('reactions', 0)
        
        if prompt and len(prompt) > 10:
            title = prompt[:40].strip()
            if reactions > 50:
                return f"{title} - Premium Civitai AI"
            else:
                return f"{title} - Civitai AI"
        else:
            if reactions > 50:
                return f"{category.title()} Premium AI Art - Civitai"
            else:
                return f"{category.title()} AI Art - Civitai"
    
    def create_tags(self, category, image_info):
        """Create appropriate tags for Civitai wallpaper"""
        tags = [category, 'ai-generated', 'civitai', 'stable-diffusion', 'hd', 'mobile']
        
        reactions = image_info.get('reactions', 0)
        if reactions > 100:
            tags.append('highly-rated')
        elif reactions > 20:
            tags.append('popular')
        
        model = image_info.get('model', '')
        if model and len(model) > 3:
            clean_model = re.sub(r'[^a-zA-Z0-9-]', '-', model.lower())[:20]
            tags.append(clean_model)
        
        tags.append('community-rated')
        
        return tags
    
    def create_metadata(self, image_info):
        """Create enhanced metadata for Civitai wallpaper"""
        metadata = {
            'ai_source': 'civitai',
            'ai_generated': True,
            'source_platform': 'civitai.com'
        }
        
        if image_info.get('prompt'):
            metadata['ai_prompt'] = image_info['prompt'][:300]
        
        if image_info.get('model'):
            metadata['ai_model'] = image_info['model']
        
        stats = image_info.get('stats', {})
        if stats:
            metadata['civitai_stats'] = stats
        
        if image_info.get('reactions'):
            metadata['community_reactions'] = image_info['reactions']
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Scrape AI wallpapers from Civitai using tag IDs')
    parser.add_argument('--category', choices=['abstract', 'cyberpunk', 'space', 'ai'], help='Specific category to scrape')
    parser.add_argument('--count', type=int, default=20, help='Number of images to scrape per category')
    
    args = parser.parse_args()
    
    scraper = SimpleCivitaiScraper()
    
    if args.category:
        scraper.scrape_category(args.category, args.count)
    else:
        # Scrape all categories
        total_added = 0
        for category in ['abstract', 'cyberpunk', 'space', 'ai']:
            added = scraper.scrape_category(category, args.count)
            total_added += added
            time.sleep(3)  # Break between categories
        
        print(f"\n🎉 Total Civitai wallpapers added: {total_added}")

if __name__ == '__main__':
    main()