#!/usr/bin/env python3
"""
Scrape wallpapers from multiple sources to reach 100+ per category
Usage: ./tools/scrape_wallpapers.py --category cars --count 71 [options]

This tool fetches wallpapers from:
- Unsplash (via API)
- Pixabay (via API)
- Pexels (via API)
- Web scraping (fallback)
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
from urllib.parse import urlparse
from add_wallpaper import WallpaperManager

class WallpaperScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # API keys (add your own)
        self.unsplash_key = "YOUR_UNSPLASH_ACCESS_KEY"
        self.pixabay_key = "YOUR_PIXABAY_API_KEY"
        self.pexels_key = "YOUR_PEXELS_API_KEY"
        
        # Download directory
        self.download_dir = Path("/tmp/wallpaper_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Category search terms
        self.search_terms = {
            'cars': ['sports car', 'luxury car', 'automotive', 'vehicle', 'supercar', 'racing car', 'vintage car'],
            'technology': ['technology', 'gadgets', 'computer', 'circuit', 'digital', 'electronics', 'innovation'],
            'vintage': ['vintage', 'retro', 'classic', 'antique', 'nostalgia', 'old style'],
            'cyberpunk': ['cyberpunk', 'neon', 'futuristic', 'sci-fi', 'dystopian', 'digital future'],
            'gaming': ['gaming', 'video games', 'esports', 'game controller', 'gaming setup'],
            'pastel': ['pastel colors', 'soft colors', 'gentle', 'minimal colors', 'light colors'],
            'minimal': ['minimal', 'minimalist', 'clean', 'simple', 'geometric'],
            'art': ['digital art', 'artwork', 'illustration', 'creative', 'artistic'],
            'seasonal': ['seasonal', 'autumn', 'winter', 'spring', 'summer', 'holidays'],
            'neon': ['neon lights', 'neon signs', 'glowing', 'electric', 'bright lights'],
            'space': ['space', 'galaxy', 'stars', 'nebula', 'cosmos', 'universe'],
            'dark': ['dark', 'black', 'shadow', 'night', 'moody', 'gothic']
        }
    
    def fetch_unsplash(self, query, count=30):
        """Fetch images from Unsplash API"""
        if self.unsplash_key == "YOUR_UNSPLASH_ACCESS_KEY":
            print("⚠️  Unsplash API key not configured")
            return []
        
        print(f"🔍 Searching Unsplash for: {query}")
        
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': query,
                'per_page': min(count, 30),
                'orientation': 'portrait',
                'client_id': self.unsplash_key
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('results', []):
                images.append({
                    'url': photo['urls']['full'],
                    'photographer': photo['user']['name'],
                    'source': 'unsplash',
                    'id': photo['id']
                })
            
            print(f"✅ Found {len(images)} images from Unsplash")
            return images
            
        except Exception as e:
            print(f"❌ Unsplash error: {e}")
            return []
    
    def fetch_pexels(self, query, count=30):
        """Fetch images from Pexels API"""
        if self.pexels_key == "YOUR_PEXELS_API_KEY":
            print("⚠️  Pexels API key not configured")
            return []
        
        print(f"🔍 Searching Pexels for: {query}")
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {'Authorization': self.pexels_key}
            params = {
                'query': query,
                'per_page': min(count, 80),
                'orientation': 'portrait'
            }
            
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('photos', []):
                images.append({
                    'url': photo['src']['original'],
                    'photographer': photo['photographer'],
                    'source': 'pexels',
                    'id': photo['id']
                })
            
            print(f"✅ Found {len(images)} images from Pexels")
            return images
            
        except Exception as e:
            print(f"❌ Pexels error: {e}")
            return []
    
    def fetch_pixabay(self, query, count=30):
        """Fetch images from Pixabay API"""
        if self.pixabay_key == "YOUR_PIXABAY_API_KEY":
            print("⚠️  Pixabay API key not configured")
            return []
        
        print(f"🔍 Searching Pixabay for: {query}")
        
        try:
            url = "https://pixabay.com/api/"
            params = {
                'key': self.pixabay_key,
                'q': query,
                'per_page': min(count, 200),
                'orientation': 'vertical',
                'image_type': 'photo',
                'min_width': 1000,
                'min_height': 1000
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('hits', []):
                images.append({
                    'url': photo['fullHDURL'] or photo['webformatURL'],
                    'photographer': photo['user'],
                    'source': 'pixabay',
                    'id': photo['id']
                })
            
            print(f"✅ Found {len(images)} images from Pixabay")
            return images
            
        except Exception as e:
            print(f"❌ Pixabay error: {e}")
            return []
    
    def download_image(self, image_info, filename):
        """Download an image"""
        try:
            filepath = self.download_dir / filename
            
            response = self.session.get(image_info['url'], stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify it's a valid image
            try:
                from PIL import Image
                with Image.open(filepath) as img:
                    if img.width < 800 or img.height < 600:
                        os.remove(filepath)
                        return None
            except:
                os.remove(filepath)
                return None
            
            return filepath
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def scrape_category(self, category, needed_count):
        """Scrape images for a specific category"""
        if category not in self.search_terms:
            print(f"❌ No search terms defined for category: {category}")
            return 0
        
        print(f"\n🎯 Scraping {needed_count} images for category: {category}")
        
        all_images = []
        search_terms = self.search_terms[category]
        
        # Fetch from all sources
        for term in search_terms:
            if len(all_images) >= needed_count:
                break
            
            # Try each source
            remaining = needed_count - len(all_images)
            per_source = max(10, remaining // len(search_terms))
            
            # Fetch from APIs
            images = []
            images.extend(self.fetch_unsplash(term, per_source))
            images.extend(self.fetch_pexels(term, per_source))
            images.extend(self.fetch_pixabay(term, per_source))
            
            all_images.extend(images)
            
            # Rate limiting
            time.sleep(1)
        
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
        for i, image_info in enumerate(unique_images[:needed_count]):
            if added_count >= needed_count:
                break
            
            print(f"⬇️  Downloading image {i+1}/{min(len(unique_images), needed_count)}")
            
            # Create filename
            filename = f"{category}_{image_info['source']}_{image_info['id']}.jpg"
            filepath = self.download_image(image_info, filename)
            
            if filepath:
                try:
                    # Add to collection
                    title = f"{category.title()} Wallpaper"
                    tags = [category, image_info['source']]
                    
                    self.manager.add_wallpaper(
                        category=category,
                        image_path=filepath,
                        title=title,
                        tags=tags,
                        photographer=image_info.get('photographer')
                    )
                    
                    added_count += 1
                    print(f"✅ Added {category}_{added_count}")
                    
                    # Clean up
                    os.remove(filepath)
                    
                except Exception as e:
                    print(f"❌ Failed to add image: {e}")
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"🎉 Successfully added {added_count} images to {category}")
        return added_count
    
    def scrape_all_needed(self):
        """Scrape all categories that need more images"""
        # Get current stats
        stats_file = self.manager.api_dir / 'stats.json'
        if not stats_file.exists():
            print("❌ No stats file found. Run build_api.py first.")
            return
        
        with open(stats_file) as f:
            stats = json.load(f)
        
        categories_to_scrape = []
        
        for category, info in stats['data']['categories'].items():
            if info['count'] < 100:
                needed = 100 - info['count']
                categories_to_scrape.append((category, needed))
        
        if not categories_to_scrape:
            print("🎉 All categories already have 100+ images!")
            return
        
        # Sort by most needed first
        categories_to_scrape.sort(key=lambda x: x[1], reverse=True)
        
        print(f"📋 Categories needing images:")
        for category, needed in categories_to_scrape:
            print(f"  - {category}: need {needed} more images")
        
        # Scrape each category
        total_added = 0
        for category, needed in categories_to_scrape:
            added = self.scrape_category(category, needed)
            total_added += added
            
            # Brief pause between categories
            time.sleep(2)
        
        print(f"\n🎉 Scraping complete! Added {total_added} images total")
        
        # Rebuild APIs
        print("🔄 Rebuilding APIs...")
        self.manager.rebuild_apis()
        print("✅ APIs rebuilt successfully!")

def main():
    parser = argparse.ArgumentParser(description='Scrape wallpapers from multiple sources')
    parser.add_argument('--category', help='Specific category to scrape')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    parser.add_argument('--all', action='store_true', help='Scrape all categories that need images')
    
    args = parser.parse_args()
    
    scraper = WallpaperScraper()
    
    if args.all:
        scraper.scrape_all_needed()
    elif args.category:
        scraper.scrape_category(args.category, args.count)
    else:
        print("❌ Please specify --category or --all")
        sys.exit(1)

if __name__ == '__main__':
    main()