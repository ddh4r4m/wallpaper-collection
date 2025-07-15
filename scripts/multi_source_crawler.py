#!/usr/bin/env python3
"""
Multi-Source Wallpaper Crawler - Fast API-based crawler using multiple sources
"""

import os
import sys
import json
import time
import requests
import hashlib
# Removed async imports - using threading instead
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiSourceCrawler:
    """Fast multi-source wallpaper crawler using APIs"""
    
    def __init__(self, output_dir: str = "crawl_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # API Keys (add your own)
        self.pexels_api_key = "T8LQQ7fP5zOqFODKCOD8sAKbTxRQ6t6AYejbLZMWXTVhKCYrG7lEYsUa"
        self.unsplash_access_key = ""  # Add if available
        
        # Category search terms for better results
        self.category_terms = {
            'nature': ['landscape', 'forest', 'mountains', 'ocean', 'sunset', 'trees', 'wildlife', 'flowers'],
            'space': ['galaxy', 'nebula', 'stars', 'universe', 'cosmos', 'planets', 'astronomy', 'milky way'],
            'abstract': ['geometric', 'pattern', 'texture', 'modern art', 'digital art', 'gradient', 'minimalist'],
            'minimal': ['clean', 'simple', 'white', 'black and white', 'zen', 'minimal design', 'monochrome'],
            'technology': ['circuit', 'computer', 'digital', 'tech', 'futuristic', 'code', 'electronics'],
            'cyberpunk': ['neon', 'cyberpunk', 'futuristic city', 'neon lights', 'sci-fi', 'dystopian'],
            'gaming': ['gaming setup', 'controllers', 'video games', 'esports', 'gaming pc', 'arcade'],
            'anime': ['anime art', 'manga', 'japanese art', 'kawaii', 'otaku', 'anime character'],
            'cars': ['sports car', 'luxury car', 'racing', 'automotive', 'supercars', 'vintage cars'],
            'sports': ['football', 'basketball', 'soccer', 'tennis', 'athletics', 'fitness', 'gym'],
            'architecture': ['buildings', 'skyscrapers', 'modern architecture', 'urban', 'city', 'structures'],
            'art': ['painting', 'artwork', 'canvas', 'artistic', 'fine art', 'gallery', 'creative'],
            'dark': ['dark theme', 'black', 'gothic', 'noir', 'shadow', 'mysterious', 'moody'],
            'neon': ['neon lights', 'bright colors', 'synthwave', 'electric', 'glowing', 'vibrant'],
            'pastel': ['pastel colors', 'soft colors', 'light pink', 'baby blue', 'mint green'],
            'vintage': ['retro', 'classic', 'old style', 'vintage design', 'antique', 'nostalgic'],
            'gradient': ['color gradient', 'smooth transition', 'blend', 'ombre', 'color fade'],
            'seasonal': ['autumn', 'winter', 'spring', 'summer', 'seasons', 'weather', 'holidays']
        }
        
        # Downloaded hashes tracking
        self.downloaded_hashes: Set[str] = set()
        self.load_existing_hashes()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WallpaperCollection/1.0 (Multi-Source)'
        })
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
                logger.info(f"Loaded {len(self.downloaded_hashes)} existing hashes")
            except Exception as e:
                logger.warning(f"Could not load existing hashes: {e}")
    
    def save_downloaded_hashes(self):
        """Save downloaded hashes to file"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
    
    def get_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image data"""
        return hashlib.md5(image_data).hexdigest()
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check if image is already downloaded"""
        image_hash = self.get_image_hash(image_data)
        return image_hash in self.downloaded_hashes
    
    def search_pexels(self, category: str, query: str, per_page: int = 30) -> List[Dict]:
        """Search Pexels API for images"""
        if not self.pexels_api_key:
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "portrait",
                "size": "large"
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('photos', []):
                # Get the largest portrait image
                src = photo.get('src', {})
                download_url = src.get('large2x') or src.get('large') or src.get('medium')
                
                if download_url:
                    images.append({
                        'id': f"pexels_{photo['id']}",
                        'url': download_url,
                        'source': 'pexels',
                        'photographer': photo.get('photographer', 'Unknown'),
                        'alt': photo.get('alt', query),
                        'width': photo.get('width', 1080),
                        'height': photo.get('height', 1920)
                    })
            
            logger.info(f"Pexels: Found {len(images)} images for '{query}'")
            return images
            
        except Exception as e:
            logger.error(f"Pexels search failed for '{query}': {e}")
            return []
    
    def search_pixabay(self, category: str, query: str, per_page: int = 30) -> List[Dict]:
        """Search Pixabay API for images (free tier)"""
        try:
            # Using Pixabay's free API (no key required for basic usage)
            url = "https://pixabay.com/api/"
            params = {
                "key": "44863573-965c95b2bcc00b2e44dd5e1d7",  # Free public key
                "q": query,
                "image_type": "photo",
                "orientation": "vertical",
                "min_width": 1080,
                "min_height": 1920,
                "per_page": per_page,
                "safesearch": "true"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for hit in data.get('hits', []):
                # Get the largest available image
                download_url = hit.get('largeImageURL') or hit.get('webformatURL')
                
                if download_url:
                    images.append({
                        'id': f"pixabay_{hit['id']}",
                        'url': download_url,
                        'source': 'pixabay',
                        'photographer': hit.get('user', 'Unknown'),
                        'alt': hit.get('tags', query),
                        'width': hit.get('imageWidth', 1080),
                        'height': hit.get('imageHeight', 1920)
                    })
            
            logger.info(f"Pixabay: Found {len(images)} images for '{query}'")
            return images
            
        except Exception as e:
            logger.error(f"Pixabay search failed for '{query}': {e}")
            return []
    
    def search_unsplash(self, category: str, query: str, per_page: int = 30) -> List[Dict]:
        """Search Unsplash API for images"""
        try:
            # Use Unsplash Source API (no key required)
            images = []
            for i in range(per_page):
                # Generate different variations
                width, height = 1080, 1920
                url = f"https://source.unsplash.com/{width}x{height}/?{query.replace(' ', ',')}"
                
                images.append({
                    'id': f"unsplash_{category}_{i+1:03d}",
                    'url': url,
                    'source': 'unsplash',
                    'photographer': 'Unsplash Contributor',
                    'alt': f"{query} wallpaper",
                    'width': width,
                    'height': height
                })
            
            logger.info(f"Unsplash: Generated {len(images)} image URLs for '{query}'")
            return images
            
        except Exception as e:
            logger.error(f"Unsplash search failed for '{query}': {e}")
            return []
    
    def search_wallhaven(self, category: str, query: str, per_page: int = 30) -> List[Dict]:
        """Search Wallhaven for images"""
        try:
            url = "https://wallhaven.cc/api/v1/search"
            params = {
                "q": query,
                "categories": "111",  # General, Anime, People
                "purity": "100",      # SFW only
                "sorting": "relevance",
                "order": "desc",
                "page": 1,
                "atleast": "1920x1080",
                "ratios": "portrait"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for wallpaper in data.get('data', []):
                download_url = wallpaper.get('path')
                
                if download_url:
                    images.append({
                        'id': f"wallhaven_{wallpaper['id']}",
                        'url': download_url,
                        'source': 'wallhaven',
                        'photographer': 'Wallhaven Contributor',
                        'alt': f"{query} wallpaper",
                        'width': wallpaper.get('dimension_x', 1080),
                        'height': wallpaper.get('dimension_y', 1920)
                    })
            
            logger.info(f"Wallhaven: Found {len(images)} images for '{query}'")
            return images
            
        except Exception as e:
            logger.error(f"Wallhaven search failed for '{query}': {e}")
            return []
    
    def download_image(self, image_info: Dict, category: str, index: int) -> bool:
        """Download a single image"""
        try:
            url = image_info['url']
            filename = f"{category}_{index:03d}.jpg"
            
            # Download image
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate skipped: {filename}")
                return False
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create metadata
            metadata = {
                'id': f"{category}_{index:03d}",
                'source': image_info['source'],
                'category': category,
                'title': f'{category.title()} Wallpaper {index}',
                'description': f'High-quality {category} wallpaper from {image_info["source"]}',
                'width': 1080,
                'height': 1920,
                'photographer': image_info.get('photographer', 'Unknown'),
                'tags': [category, 'wallpaper', 'hd', 'high resolution', 'mobile'],
                'download_url': url,
                'source_url': url,
                'original_info': image_info,
                'crawled_at': datetime.now().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Track hash
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded: {filename} from {image_info['source']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {image_info.get('url', 'unknown')}: {e}")
            return False
    
    def crawl_category(self, category: str, limit: int = 100) -> Dict:
        """Crawl images for a specific category using multiple sources"""
        logger.info(f"Crawling category: {category} (target: {limit} images)")
        
        if category not in self.category_terms:
            logger.error(f"Category '{category}' not supported")
            return {'category': category, 'downloaded': 0, 'errors': 1}
        
        downloaded = 0
        errors = 0
        all_images = []
        
        # Get search terms for this category
        search_terms = self.category_terms[category]
        
        # Search multiple sources
        for term in search_terms[:3]:  # Use first 3 terms to avoid rate limits
            try:
                # Search Pexels
                pexels_images = self.search_pexels(category, term, per_page=20)
                all_images.extend(pexels_images)
                
                # Search Pixabay
                pixabay_images = self.search_pixabay(category, term, per_page=20)
                all_images.extend(pixabay_images)
                
                # Search Unsplash
                unsplash_images = self.search_unsplash(category, term, per_page=15)
                all_images.extend(unsplash_images)
                
                # Search Wallhaven
                wallhaven_images = self.search_wallhaven(category, term, per_page=10)
                all_images.extend(wallhaven_images)
                
                # Small delay between searches
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error searching for '{term}': {e}")
                errors += 1
        
        # Shuffle for variety and remove duplicates by URL
        seen_urls = set()
        unique_images = []
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        random.shuffle(unique_images)
        logger.info(f"Found {len(unique_images)} unique images for {category}")
        
        # Download images in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for i, image_info in enumerate(unique_images[:limit], 1):
                future = executor.submit(self.download_image, image_info, category, downloaded + i)
                futures.append(future)
            
            for future in as_completed(futures):
                if future.result():
                    downloaded += 1
                    if downloaded >= limit:
                        break
                else:
                    errors += 1
        
        # Save hash tracking
        self.save_downloaded_hashes()
        
        return {
            'category': category,
            'downloaded': downloaded,
            'errors': errors,
            'total_found': len(unique_images)
        }
    
    def crawl_all_categories(self, categories: List[str], limit_per_category: int = 100, max_workers: int = 4) -> Dict:
        """Crawl all categories in parallel"""
        logger.info(f"Starting multi-source crawl for {len(categories)} categories...")
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit jobs
            future_to_category = {
                executor.submit(self.crawl_category, category, limit_per_category): category
                for category in categories
            }
            
            # Collect results
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ {category}: {result['downloaded']} downloaded from {result['total_found']} found")
                except Exception as e:
                    logger.error(f"❌ {category} failed: {e}")
                    results.append({'category': category, 'downloaded': 0, 'errors': 1, 'total_found': 0})
        
        return {
            'total_categories': len(results),
            'total_downloaded': sum(r['downloaded'] for r in results),
            'total_errors': sum(r['errors'] for r in results),
            'category_results': results
        }

def main():
    parser = argparse.ArgumentParser(description='Multi-source wallpaper crawler')
    parser.add_argument('--categories', default='nature,space,abstract,minimal,technology,cyberpunk,gaming,anime,cars,sports', 
                       help='Comma-separated list of categories')
    parser.add_argument('--limit', type=int, default=100, help='Max images per category')
    parser.add_argument('--workers', type=int, default=4, help='Max parallel workers')
    parser.add_argument('--output', default='multi_crawl_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Parse categories
    categories = [cat.strip() for cat in args.categories.split(',')]
    
    # Create crawler
    crawler = MultiSourceCrawler(args.output)
    
    # Crawl all categories
    start_time = time.time()
    results = crawler.crawl_all_categories(categories, args.limit, args.workers)
    processing_time = time.time() - start_time
    
    # Print results
    print(f"\n🎉 Multi-Source Crawl Complete!")
    print(f"📊 Total Categories: {results['total_categories']}")
    print(f"✅ Total Downloaded: {results['total_downloaded']}")
    print(f"❌ Total Errors: {results['total_errors']}")
    print(f"⏱️  Processing Time: {processing_time:.1f} seconds")
    
    print(f"\n📁 Category Breakdown:")
    for result in results['category_results']:
        print(f"   {result['category']:12} : {result['downloaded']:3d} downloaded ({result.get('total_found', 0)} found)")
    
    print(f"\n🔄 Next steps:")
    print(f"1. Review images: python scripts/review_images.py --input {args.output}")
    print(f"2. Process approved: python scripts/parallel_category_processor.py")
    print(f"3. Generate indexes: python scripts/generate_index_simple.py --update-all")

if __name__ == "__main__":
    main()