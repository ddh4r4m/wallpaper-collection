#!/usr/bin/env python3
"""
Enhanced Civitai scraper with gap filling and scrolling
Scrapes from specific tag URL and fills gaps from deleted images
Usage: python3 tools/scrape_civitai_gap_filler.py --tag-url "https://civitai.com/images?tags=5133" --count 50
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
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing BeautifulSoup...")
    os.system("python3 -m pip install --user beautifulsoup4 --break-system-packages")
    from bs4 import BeautifulSoup

from add_wallpaper import WallpaperManager

class CivitaiGapFillerScraper:
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
        
        self.download_dir = Path("/tmp/civitai_gap_filler")
        self.download_dir.mkdir(exist_ok=True)
    
    def find_gaps_in_category(self, category):
        """Find missing image numbers in a category to fill gaps"""
        category_dir = self.manager.wallpapers_dir / category
        if not category_dir.exists():
            print(f"❌ Category directory not found: {category}")
            return []
        
        # Get all existing image files
        existing_files = list(category_dir.glob("*.jpg"))
        existing_numbers = []
        
        for file_path in existing_files:
            filename = file_path.stem
            if filename.isdigit():
                existing_numbers.append(int(filename))
        
        if not existing_numbers:
            print(f"❌ No numbered images found in {category}")
            return [1]  # Start from 1 if empty
        
        existing_numbers.sort()
        max_number = max(existing_numbers)
        
        # Find gaps in the sequence
        gaps = []
        for i in range(1, max_number + 1):
            if i not in existing_numbers:
                gaps.append(i)
        
        print(f"📋 Found {len(gaps)} gaps in {category}: {gaps[:10]}{'...' if len(gaps) > 10 else ''}")
        return gaps
    
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
    
    def get_images_from_civitai_api(self, tag_id, limit=100, cursor=None):
        """Get images from Civitai API with pagination"""
        print(f"🔍 Fetching images from Civitai API for tag {tag_id}...")
        
        try:
            api_url = "https://civitai.com/api/v1/images"
            params = {
                'tags': str(tag_id),
                'limit': min(limit, 200),  # Max per request
                'sort': 'Most Reactions',
                'period': 'AllTime',  # Get more images
                'nsfw': 'false'
            }
            
            if cursor:
                params['cursor'] = cursor
            
            response = self.session.get(api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                next_cursor = data.get('metadata', {}).get('nextCursor')
                print(f"  ✅ API returned {len(items)} images for tag {tag_id}")
                return items, next_cursor
            else:
                print(f"  ❌ API request failed: {response.status_code}")
                return [], None
                
        except Exception as e:
            print(f"  ❌ API error: {e}")
            return [], None
    
    def scrape_multiple_pages(self, tag_id, target_count=50):
        """Scrape multiple pages to get enough images"""
        print(f"🎯 Scraping {target_count} images from tag {tag_id}...")
        
        all_images = []
        cursor = None
        page = 1
        max_pages = 5  # Limit to prevent infinite loop
        
        while len(all_images) < target_count * 2 and page <= max_pages:
            print(f"  📄 Fetching page {page}...")
            
            images, next_cursor = self.get_images_from_civitai_api(tag_id, 50, cursor)
            
            if not images:
                print(f"  ❌ No more images available")
                break
            
            # Process and filter images
            for item in images:
                if len(all_images) >= target_count * 2:  # Get extra for filtering
                    break
                
                # Quality checks
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
                    'prompt': meta.get('prompt', '')[:300] if meta else '',
                    'model': meta.get('Model', '') if meta else '',
                    'steps': meta.get('Steps', 0) if meta else 0,
                    'cfg_scale': meta.get('CFG scale', 0) if meta else 0,
                    'sampler': meta.get('Sampler', '') if meta else '',
                    'stats': stats,
                    'reactions': stats.get('reactionCount', 0) + stats.get('likeCount', 0) + stats.get('heartCount', 0),
                    'source': 'civitai',
                    'tag_id': tag_id,
                    'id': hashlib.md5(url.encode()).hexdigest()[:8]
                }
                
                all_images.append(image_data)
            
            cursor = next_cursor
            if not cursor:
                print(f"  ✅ No more pages available")
                break
            
            page += 1
            time.sleep(2)  # Rate limiting between pages
        
        # Remove duplicates and sort by reactions
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        unique_images.sort(key=lambda x: x.get('reactions', 0), reverse=True)
        
        print(f"📋 Found {len(unique_images)} unique high-quality images")
        return unique_images
    
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
    
    def fill_gaps_with_images(self, category, tag_url, target_count=50):
        """Fill gaps in category with images from tag URL"""
        print(f"\n🎯 Filling gaps in {category} with {target_count} images from {tag_url}")
        
        # Extract tag ID from URL
        tag_id = self.get_tag_id_from_url(tag_url)
        if not tag_id:
            print(f"❌ Could not extract tag ID from URL: {tag_url}")
            return 0
        
        print(f"🏷️  Extracted tag ID: {tag_id}")
        
        # Find gaps in the category
        gaps = self.find_gaps_in_category(category)
        
        # If no gaps, find the next available numbers
        if not gaps:
            category_dir = self.manager.wallpapers_dir / category
            existing_files = list(category_dir.glob("*.jpg"))
            existing_numbers = []
            
            for file_path in existing_files:
                filename = file_path.stem
                if filename.isdigit():
                    existing_numbers.append(int(filename))
            
            if existing_numbers:
                max_number = max(existing_numbers)
                gaps = list(range(max_number + 1, max_number + target_count + 1))
            else:
                gaps = list(range(1, target_count + 1))
            
            print(f"📋 No gaps found, will use next available numbers: {gaps[:5]}...")
        
        # Ensure we have enough gap slots
        available_slots = gaps[:target_count]
        
        # Scrape images from Civitai
        images = self.scrape_multiple_pages(tag_id, target_count)
        
        if not images:
            print(f"❌ No images found for tag {tag_id}")
            return 0
        
        # Download and process images
        added_count = 0
        used_slots = []
        
        for i, image_info in enumerate(images):
            if added_count >= len(available_slots):
                break
            
            slot_number = available_slots[added_count]
            
            print(f"⬇️  Processing image {i+1}/{len(images)} → slot {slot_number} (added: {added_count+1}/{len(available_slots)})")
            
            # Create filename
            image_id = image_info.get('id', hashlib.md5(image_info['url'].encode()).hexdigest()[:8])
            temp_filename = f"{category}_civitai_{slot_number}_{image_id}.jpg"
            filepath = self.download_image(image_info, temp_filename)
            
            if filepath:
                try:
                    # Create enhanced title and tags
                    title = self.create_title(category, image_info)
                    tags = self.create_tags(category, image_info)
                    
                    # Set up paths using the gap slot number
                    output_path = self.manager.wallpapers_dir / category / f"{slot_number:03d}.jpg"
                    thumb_path = self.manager.thumbnails_dir / category / f"{slot_number:03d}.jpg"
                    
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
                    
                    self.manager.save_metadata(category, f"{slot_number:03d}", title, tags, metadata)
                    
                    added_count += 1
                    used_slots.append(slot_number)
                    reactions = image_info.get('reactions', 0)
                    print(f"✅ Added {category}_{slot_number:03d} (reactions: {reactions})")
                    
                except Exception as e:
                    print(f"❌ Failed to add image to slot {slot_number}: {e}")
                finally:
                    # Clean up
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"🎉 Successfully filled {added_count} gaps in {category}")
        print(f"📋 Used slots: {used_slots}")
        return added_count
    
    def create_title(self, category, image_info):
        """Create an appropriate title for Civitai wallpaper"""
        prompt = image_info.get('prompt', '').strip()
        reactions = image_info.get('reactions', 0)
        model = image_info.get('model', '').strip()
        
        if prompt and len(prompt) > 15:
            # Clean up the prompt for title
            clean_prompt = re.sub(r'[^\w\s-]', '', prompt)[:50].strip()
            if reactions > 100:
                return f"{clean_prompt} - Premium Civitai"
            else:
                return f"{clean_prompt} - Civitai AI"
        elif model and len(model) > 3:
            if reactions > 100:
                return f"{model} {category.title()} - Premium Civitai"
            else:
                return f"{model} {category.title()} - Civitai"
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
        
        model = image_info.get('model', '')
        if model and len(model) > 3:
            clean_model = re.sub(r'[^a-zA-Z0-9-]', '-', model.lower())[:20]
            tags.append(clean_model)
        
        sampler = image_info.get('sampler', '')
        if sampler and len(sampler) > 3:
            clean_sampler = re.sub(r'[^a-zA-Z0-9-]', '-', sampler.lower())[:15]
            tags.append(clean_sampler)
        
        # Add quality indicators
        width = image_info.get('actual_width', image_info.get('width', 0))
        height = image_info.get('actual_height', image_info.get('height', 0))
        
        if width >= 1920 or height >= 1920:
            tags.append('high-resolution')
        
        tags.append('community-rated')
        
        return tags
    
    def create_metadata(self, image_info):
        """Create enhanced metadata for Civitai wallpaper"""
        metadata = {
            'ai_source': 'civitai',
            'ai_generated': True,
            'source_platform': 'civitai.com',
            'civitai_tag_id': image_info.get('tag_id')
        }
        
        if image_info.get('prompt'):
            metadata['ai_prompt'] = image_info['prompt'][:500]  # Longer prompts
        
        if image_info.get('model'):
            metadata['ai_model'] = image_info['model']
        
        if image_info.get('steps'):
            metadata['ai_steps'] = image_info['steps']
        
        if image_info.get('cfg_scale'):
            metadata['ai_cfg_scale'] = image_info['cfg_scale']
        
        if image_info.get('sampler'):
            metadata['ai_sampler'] = image_info['sampler']
        
        stats = image_info.get('stats', {})
        if stats:
            metadata['civitai_stats'] = stats
        
        if image_info.get('reactions'):
            metadata['total_reactions'] = image_info['reactions']
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Fill gaps in AI category with Civitai images')
    parser.add_argument('--tag-url', required=True, help='Civitai tag URL to scrape from')
    parser.add_argument('--category', default='ai', help='Category to fill gaps in')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    
    args = parser.parse_args()
    
    scraper = CivitaiGapFillerScraper()
    scraper.fill_gaps_with_images(args.category, args.tag_url, args.count)

if __name__ == '__main__':
    main()