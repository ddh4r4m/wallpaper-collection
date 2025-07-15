#!/usr/bin/env python3
"""
Wallhaven-focused fast crawler for remaining categories
"""

import os
import json
import time
import requests
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WallhavenCrawler:
    """Fast Wallhaven-based crawler for missing categories"""
    
    def __init__(self, output_dir: str = "wallhaven_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Category search terms optimized for Wallhaven
        self.category_queries = {
            'anime': 'anime',
            'cars': 'cars',
            'gaming': 'gaming',
            'cyberpunk': 'cyberpunk',
            'architecture': 'architecture',
            'art': 'art',
            'dark': 'dark',
            'neon': 'neon',
            'pastel': 'pastel',
            'vintage': 'vintage',
            'gradient': 'gradient',
            'sports': 'sports',
            'minimal': 'minimal'
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Downloaded hashes
        self.downloaded_hashes = set()
        self.load_existing_hashes()
    
    def load_existing_hashes(self):
        """Load existing hashes"""
        hash_file = self.output_dir / 'wallhaven_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
            except:
                pass
    
    def save_hashes(self):
        """Save hashes"""
        hash_file = self.output_dir / 'wallhaven_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
    
    def search_wallhaven(self, query: str, pages: int = 3) -> List[Dict]:
        """Search Wallhaven for images"""
        images = []
        
        for page in range(1, pages + 1):
            try:
                url = "https://wallhaven.cc/api/v1/search"
                params = {
                    "q": query,
                    "categories": "111",
                    "purity": "100", 
                    "sorting": "relevance",
                    "order": "desc",
                    "page": page,
                    "atleast": "1920x1080"
                }
                
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                for wallpaper in data.get('data', []):
                    images.append({
                        'id': wallpaper['id'],
                        'url': wallpaper['path'],
                        'resolution': wallpaper['resolution'],
                        'file_size': wallpaper['file_size']
                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Search failed for {query} page {page}: {e}")
        
        logger.info(f"Found {len(images)} images for '{query}'")
        return images
    
    def download_image(self, image_info: Dict, category: str, index: int) -> bool:
        """Download single image"""
        try:
            url = image_info['url']
            filename = f"{category}_{index:03d}.jpg"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            image_data = response.content
            image_hash = hashlib.md5(image_data).hexdigest()
            
            if image_hash in self.downloaded_hashes:
                return False
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Save metadata
            metadata = {
                'id': f"{category}_{index:03d}",
                'source': 'wallhaven',
                'category': category,
                'title': f'{category.title()} Wallpaper {index}',
                'description': f'High-quality {category} wallpaper from Wallhaven',
                'width': 1080,
                'height': 1920,
                'tags': [category, 'wallpaper', 'hd', 'wallhaven'],
                'download_url': url,
                'original_info': image_info,
                'crawled_at': datetime.now().isoformat() + 'Z'
            }
            
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.downloaded_hashes.add(image_hash)
            logger.info(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False
    
    def crawl_category(self, category: str, limit: int = 50) -> Dict:
        """Crawl category"""
        logger.info(f"Crawling {category} (target: {limit})")
        
        if category not in self.category_queries:
            return {'category': category, 'downloaded': 0, 'errors': 1}
        
        query = self.category_queries[category]
        images = self.search_wallhaven(query, pages=5)
        
        random.shuffle(images)
        downloaded = 0
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for i, image_info in enumerate(images[:limit*2], 1):  # Get extra in case of failures
                future = executor.submit(self.download_image, image_info, category, downloaded + 1)
                futures.append(future)
            
            for future in as_completed(futures):
                if future.result():
                    downloaded += 1
                    if downloaded >= limit:
                        break
        
        self.save_hashes()
        return {'category': category, 'downloaded': downloaded, 'target': limit}
    
    def crawl_all(self, categories: List[str], limit: int = 50) -> Dict:
        """Crawl all categories"""
        logger.info(f"Starting Wallhaven crawl for {len(categories)} categories")
        
        results = []
        for category in categories:
            result = self.crawl_category(category, limit)
            results.append(result)
            logger.info(f"✅ {category}: {result['downloaded']}/{result.get('target', limit)}")
            time.sleep(2)  # Spacing between categories
        
        total_downloaded = sum(r['downloaded'] for r in results)
        return {
            'total_categories': len(results),
            'total_downloaded': total_downloaded,
            'results': results
        }

def main():
    parser = argparse.ArgumentParser(description='Wallhaven fast crawler')
    parser.add_argument('--categories', default='anime,cars,gaming,cyberpunk,architecture,sports', 
                       help='Categories to crawl')
    parser.add_argument('--limit', type=int, default=50, help='Images per category')
    parser.add_argument('--output', default='wallhaven_cache', help='Output directory')
    
    args = parser.parse_args()
    
    categories = [cat.strip() for cat in args.categories.split(',')]
    crawler = WallhavenCrawler(args.output)
    
    start_time = time.time()
    results = crawler.crawl_all(categories, args.limit)
    processing_time = time.time() - start_time
    
    print(f"\n🎉 Wallhaven Crawl Complete!")
    print(f"📊 Categories: {results['total_categories']}")
    print(f"✅ Downloaded: {results['total_downloaded']}")
    print(f"⏱️  Time: {processing_time:.1f} seconds")
    
    print(f"\n📁 Results:")
    for result in results['results']:
        print(f"   {result['category']:12} : {result['downloaded']:3d}")

if __name__ == "__main__":
    main()