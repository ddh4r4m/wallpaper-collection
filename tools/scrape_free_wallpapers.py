#!/usr/bin/env python3
"""
Scrape wallpapers from free sources without API keys
Usage: ./tools/scrape_free_wallpapers.py --category cars --count 71 [options]

This tool fetches wallpapers from:
- Unsplash (public feed)
- Pixabay (public pages)
- Pexels (public pages)
- Other free sources
"""

import os
import sys
import json
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
import hashlib
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
from add_wallpaper import WallpaperManager

class FreeWallpaperScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Download directory
        self.download_dir = Path("/tmp/wallpaper_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Category search terms and sources
        self.category_configs = {
            'cars': {
                'terms': ['sports-car', 'luxury-car', 'automotive', 'supercar', 'racing-car'],
                'sources': ['unsplash', 'pixabay']
            },
            'technology': {
                'terms': ['technology', 'computer', 'digital', 'electronics', 'gadgets'],
                'sources': ['unsplash', 'pixabay']
            },
            'vintage': {
                'terms': ['vintage', 'retro', 'classic', 'antique', 'old-style'],
                'sources': ['unsplash', 'pixabay']
            },
            'cyberpunk': {
                'terms': ['cyberpunk', 'neon', 'futuristic', 'sci-fi', 'digital-future'],
                'sources': ['unsplash', 'pixabay']
            },
            'gaming': {
                'terms': ['gaming', 'video-games', 'esports', 'game-controller'],
                'sources': ['unsplash', 'pixabay']
            },
            'pastel': {
                'terms': ['pastel-colors', 'soft-colors', 'gentle', 'minimal-colors'],
                'sources': ['unsplash', 'pixabay']
            },
            'minimal': {
                'terms': ['minimal', 'minimalist', 'clean', 'simple', 'geometric'],
                'sources': ['unsplash', 'pixabay']
            },
            'art': {
                'terms': ['digital-art', 'artwork', 'illustration', 'creative', 'artistic'],
                'sources': ['unsplash', 'pixabay']
            },
            'seasonal': {
                'terms': ['autumn', 'winter', 'spring', 'summer', 'seasons'],
                'sources': ['unsplash', 'pixabay']
            },
            'neon': {
                'terms': ['neon-lights', 'neon-signs', 'glowing', 'electric', 'bright-lights'],
                'sources': ['unsplash', 'pixabay']
            },
            'space': {
                'terms': ['space', 'galaxy', 'stars', 'nebula', 'cosmos', 'universe'],
                'sources': ['unsplash', 'pixabay']
            },
            'dark': {
                'terms': ['dark', 'black', 'shadow', 'night', 'moody', 'gothic'],
                'sources': ['unsplash', 'pixabay']
            },
            'animals': {
                'terms': ['animals', 'wildlife', 'pets', 'cats', 'dogs', 'wild-animals'],
                'sources': ['unsplash', 'pixabay']
            }
        }
    
    def scrape_unsplash_search(self, query, count=20):
        """Scrape Unsplash search results"""
        print(f"🔍 Searching Unsplash for: {query}")
        
        try:
            url = f"https://unsplash.com/s/photos/{query}"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            
            # Find image elements
            img_elements = soup.find_all('img', {'src': re.compile(r'images\.unsplash\.com')})
            
            for img in img_elements[:count]:
                src = img.get('src')
                if src and 'images.unsplash.com' in src:
                    # Convert to full resolution
                    full_url = src.replace('&w=400', '&w=1080').replace('&h=400', '&h=1920')
                    
                    # Try to extract photographer
                    photographer = "Unknown"
                    parent = img.find_parent()
                    if parent:
                        alt_text = img.get('alt', '')
                        if 'by' in alt_text:
                            photographer = alt_text.split('by')[-1].strip()
                    
                    images.append({
                        'url': full_url,
                        'photographer': photographer,
                        'source': 'unsplash',
                        'id': hashlib.md5(full_url.encode()).hexdigest()[:8]
                    })
            
            print(f"✅ Found {len(images)} images from Unsplash")
            return images
            
        except Exception as e:
            print(f"❌ Unsplash scraping error: {e}")
            return []
    
    def scrape_pixabay_search(self, query, count=20):
        """Scrape Pixabay search results"""
        print(f"🔍 Searching Pixabay for: {query}")
        
        try:
            url = f"https://pixabay.com/images/search/{query}/"
            params = {
                'orientation': 'vertical',
                'image_type': 'photo',
                'min_width': 1000,
                'min_height': 1000
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            
            # Find image containers
            img_containers = soup.find_all('div', class_='item')
            
            for container in img_containers[:count]:
                img = container.find('img')
                if img:
                    src = img.get('data-src') or img.get('src')
                    if src:
                        # Convert to full resolution
                        full_url = src.replace('_640', '_1280').replace('_960', '_1920')
                        
                        # Extract photographer
                        photographer = "Unknown"
                        user_link = container.find('a', href=re.compile(r'/users/'))
                        if user_link:
                            photographer = user_link.text.strip()
                        
                        images.append({
                            'url': full_url,
                            'photographer': photographer,
                            'source': 'pixabay',
                            'id': hashlib.md5(full_url.encode()).hexdigest()[:8]
                        })
            
            print(f"✅ Found {len(images)} images from Pixabay")
            return images
            
        except Exception as e:
            print(f"❌ Pixabay scraping error: {e}")
            return []
    
    def scrape_wallpaper_sites(self, query, count=20):
        """Scrape free wallpaper sites"""
        print(f"🔍 Searching wallpaper sites for: {query}")
        
        images = []
        
        # Try different free wallpaper sites
        sites = [
            f"https://wallhaven.cc/search?q={query}&sorting=relevance&order=desc",
            f"https://www.wallpaperflare.com/search?wallpaper={query}",
        ]
        
        for site_url in sites:
            try:
                response = self.session.get(site_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find high-res images
                img_elements = soup.find_all('img', {'src': re.compile(r'\.(jpg|jpeg|png)$', re.I)})
                
                for img in img_elements[:count//len(sites)]:
                    src = img.get('src')
                    if src and any(res in src for res in ['1080', '1920', '2560', '3840']):
                        full_url = urljoin(site_url, src)
                        
                        images.append({
                            'url': full_url,
                            'photographer': "Unknown",
                            'source': 'wallpaper-site',
                            'id': hashlib.md5(full_url.encode()).hexdigest()[:8]
                        })
                
                if len(images) >= count:
                    break
                    
            except Exception as e:
                print(f"❌ Error scraping {site_url}: {e}")
                continue
        
        print(f"✅ Found {len(images)} images from wallpaper sites")
        return images[:count]
    
    def download_image(self, image_info, filename):
        """Download an image with validation"""
        try:
            filepath = self.download_dir / filename
            
            # Add proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://unsplash.com/' if 'unsplash' in image_info['url'] else 'https://pixabay.com/'
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
        if category not in self.category_configs:
            print(f"❌ No configuration for category: {category}")
            return 0
        
        config = self.category_configs[category]
        print(f"\n🎯 Scraping {needed_count} images for category: {category}")
        
        all_images = []
        
        # Scrape from different sources
        for term in config['terms']:
            if len(all_images) >= needed_count * 2:  # Get extra to account for failures
                break
            
            images_per_term = (needed_count * 2) // len(config['terms'])
            
            # Scrape from each source
            if 'unsplash' in config['sources']:
                all_images.extend(self.scrape_unsplash_search(term, images_per_term // 2))
                time.sleep(2)  # Rate limiting
            
            if 'pixabay' in config['sources']:
                all_images.extend(self.scrape_pixabay_search(term, images_per_term // 2))
                time.sleep(2)  # Rate limiting
            
            # Try wallpaper sites as fallback
            if len(all_images) < needed_count:
                all_images.extend(self.scrape_wallpaper_sites(term, images_per_term // 3))
                time.sleep(3)  # Longer delay for wallpaper sites
        
        # Remove duplicates
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        print(f"📋 Found {len(unique_images)} unique images")
        
        # Download and add images
        added_count = 0
        for i, image_info in enumerate(unique_images):
            if added_count >= needed_count:
                break
            
            print(f"⬇️  Processing image {i+1}/{len(unique_images)} (added: {added_count}/{needed_count})")
            
            # Create filename
            filename = f"{category}_{image_info['source']}_{image_info['id']}.jpg"
            filepath = self.download_image(image_info, filename)
            
            if filepath:
                try:
                    # Add to collection
                    title = f"{category.title()} Wallpaper"
                    tags = [category, image_info['source'], 'hd', 'mobile']
                    
                    # Get next ID
                    image_id = self.manager.get_next_id(category)
                    
                    # Set up paths
                    output_path = self.manager.wallpapers_dir / category / f"{image_id}.jpg"
                    thumb_path = self.manager.thumbnails_dir / category / f"{image_id}.jpg"
                    
                    # Ensure directories exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    thumb_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Process main image
                    processed_info = self.manager.process_image(filepath, output_path)
                    
                    # Generate thumbnail
                    self.manager.generate_thumbnail(output_path, thumb_path)
                    
                    # Extract metadata
                    metadata = self.manager.extract_metadata(output_path, processed_info)
                    metadata['photographer'] = image_info.get('photographer', 'Unknown')
                    
                    # Save metadata
                    self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                    (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                    
                    self.manager.save_metadata(category, image_id, title, tags, metadata)
                    
                    added_count += 1
                    print(f"✅ Added {category}_{image_id} ({added_count}/{needed_count})")
                    
                except Exception as e:
                    print(f"❌ Failed to add image: {e}")
                finally:
                    # Clean up
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"🎉 Successfully added {added_count} images to {category}")
        return added_count
    
    def scrape_all_needed(self):
        """Scrape all categories that need more images"""
        # Get current stats
        stats_file = self.manager.api_dir / 'stats.json'
        if not stats_file.exists():
            print("❌ No stats file found. Running build_api.py...")
            self.manager.rebuild_apis()
        
        with open(stats_file) as f:
            stats = json.load(f)
        
        categories_to_scrape = []
        
        for category, info in stats['data']['categories'].items():
            if info['count'] < 100 and category in self.category_configs:
                needed = 100 - info['count']
                categories_to_scrape.append((category, needed))
        
        if not categories_to_scrape:
            print("🎉 All configured categories already have 100+ images!")
            return
        
        # Sort by most needed first
        categories_to_scrape.sort(key=lambda x: x[1], reverse=True)
        
        print(f"📋 Categories needing images:")
        for category, needed in categories_to_scrape:
            print(f"  - {category}: need {needed} more images")
        
        # Scrape each category
        total_added = 0
        for category, needed in categories_to_scrape:
            print(f"\n{'='*60}")
            print(f"🎯 Starting {category} ({needed} images needed)")
            print(f"{'='*60}")
            
            added = self.scrape_category(category, needed)
            total_added += added
            
            print(f"✅ Completed {category}: {added} images added")
            
            # Brief pause between categories
            time.sleep(5)
        
        print(f"\n🎉 Scraping complete! Added {total_added} images total")
        
        # Rebuild APIs
        print("🔄 Rebuilding APIs...")
        self.manager.rebuild_apis()
        print("✅ APIs rebuilt successfully!")

def main():
    parser = argparse.ArgumentParser(description='Scrape wallpapers from free sources')
    parser.add_argument('--category', help='Specific category to scrape')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    parser.add_argument('--all', action='store_true', help='Scrape all categories that need images')
    
    args = parser.parse_args()
    
    # Install required packages
    try:
        from bs4 import BeautifulSoup
        from PIL import Image
    except ImportError:
        print("❌ Missing required packages. Installing...")
        os.system("pip install beautifulsoup4 pillow")
        print("✅ Packages installed. Please run the script again.")
        sys.exit(1)
    
    scraper = FreeWallpaperScraper()
    
    if args.all:
        scraper.scrape_all_needed()
    elif args.category:
        scraper.scrape_category(args.category, args.count)
    else:
        print("❌ Please specify --category or --all")
        sys.exit(1)

if __name__ == '__main__':
    main()