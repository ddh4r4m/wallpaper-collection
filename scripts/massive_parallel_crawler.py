#!/usr/bin/env python3
"""
Massive Parallel Crawler - Scale to 100+ images per category with full parallelization
"""

import os
import json
import time
import requests
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import random
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)-10s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MassiveParallelCrawler:
    """High-performance parallel crawler for massive scaling"""
    
    def __init__(self, output_dir: str = "massive_crawl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # All categories with optimized search terms
        self.category_configs = {
            'nature': {
                'terms': ['landscape', 'forest', 'mountains', 'ocean', 'sunset', 'trees', 'waterfall', 'lake'],
                'wallhaven_cat': 'nature',
                'priority': 1
            },
            'space': {
                'terms': ['galaxy', 'nebula', 'stars', 'universe', 'cosmos', 'planets', 'astronomy'],
                'wallhaven_cat': 'space',
                'priority': 1
            },
            'abstract': {
                'terms': ['geometric', 'pattern', 'texture', 'modern art', 'digital art', 'gradient'],
                'wallhaven_cat': 'abstract',
                'priority': 1
            },
            'technology': {
                'terms': ['circuit', 'computer', 'digital', 'tech', 'futuristic', 'code', 'electronics'],
                'wallhaven_cat': 'technology',
                'priority': 1
            },
            'anime': {
                'terms': ['anime', 'manga', 'japanese art', 'kawaii', 'otaku', 'anime girl'],
                'wallhaven_cat': 'anime',
                'priority': 2
            },
            'cars': {
                'terms': ['sports car', 'luxury car', 'racing', 'automotive', 'supercars', 'bmw', 'ferrari'],
                'wallhaven_cat': 'cars',
                'priority': 2
            },
            'gaming': {
                'terms': ['gaming', 'video games', 'esports', 'gaming pc', 'controller', 'fps'],
                'wallhaven_cat': 'gaming',
                'priority': 2
            },
            'cyberpunk': {
                'terms': ['cyberpunk', 'neon', 'futuristic city', 'sci-fi', 'dystopian', 'blade runner'],
                'wallhaven_cat': 'cyberpunk',
                'priority': 2
            },
            'minimal': {
                'terms': ['minimal', 'clean', 'simple', 'zen', 'monochrome', 'white', 'black'],
                'wallhaven_cat': 'minimal',
                'priority': 3
            },
            'dark': {
                'terms': ['dark', 'black', 'gothic', 'noir', 'shadow', 'mysterious', 'moody'],
                'wallhaven_cat': 'dark',
                'priority': 3
            },
            'neon': {
                'terms': ['neon', 'bright colors', 'synthwave', 'electric', 'glowing', 'vibrant'],
                'wallhaven_cat': 'neon',
                'priority': 3
            },
            'sports': {
                'terms': ['football', 'basketball', 'soccer', 'tennis', 'athletics', 'fitness'],
                'wallhaven_cat': 'sports',
                'priority': 3
            },
            'architecture': {
                'terms': ['buildings', 'skyscrapers', 'modern architecture', 'urban', 'city'],
                'wallhaven_cat': 'architecture',
                'priority': 3
            },
            'art': {
                'terms': ['painting', 'artwork', 'canvas', 'artistic', 'fine art', 'gallery'],
                'wallhaven_cat': 'art',
                'priority': 3
            },
            'vintage': {
                'terms': ['retro', 'classic', 'old style', 'vintage design', 'antique', 'nostalgic'],
                'wallhaven_cat': 'vintage',
                'priority': 4
            },
            'gradient': {
                'terms': ['gradient', 'color fade', 'smooth transition', 'blend', 'ombre'],
                'wallhaven_cat': 'gradient',
                'priority': 4
            }
        }
        
        # Thread-safe hash tracking
        self.downloaded_hashes: Set[str] = set()
        self.hash_lock = threading.Lock()
        self.load_existing_hashes()
        
        # Statistics tracking
        self.stats = {
            'total_downloaded': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'category_stats': {}
        }
        self.stats_lock = threading.Lock()
    
    def load_existing_hashes(self):
        """Load all existing hashes from all sources"""
        hash_files = [
            self.output_dir / 'massive_hashes.json',
            Path('crawl_cache/downloaded_hashes.json'),
            Path('multi_crawl_cache/downloaded_hashes.json'),
            Path('wallhaven_cache/wallhaven_hashes.json')
        ]
        
        for hash_file in hash_files:
            if hash_file.exists():
                try:
                    with open(hash_file, 'r') as f:
                        existing_hashes = set(json.load(f))
                        self.downloaded_hashes.update(existing_hashes)
                except Exception as e:
                    logger.warning(f"Could not load hashes from {hash_file}: {e}")
        
        logger.info(f"Loaded {len(self.downloaded_hashes)} existing hashes")
    
    def save_hashes(self):
        """Save hashes"""
        hash_file = self.output_dir / 'massive_hashes.json'
        with self.hash_lock:
            with open(hash_file, 'w') as f:
                json.dump(list(self.downloaded_hashes), f)
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Thread-safe duplicate check"""
        image_hash = hashlib.md5(image_data).hexdigest()
        with self.hash_lock:
            if image_hash in self.downloaded_hashes:
                return True
            self.downloaded_hashes.add(image_hash)
            return False
    
    def update_stats(self, category: str, downloaded: int = 0, duplicates: int = 0, errors: int = 0):
        """Thread-safe stats update"""
        with self.stats_lock:
            self.stats['total_downloaded'] += downloaded
            self.stats['total_duplicates'] += duplicates
            self.stats['total_errors'] += errors
            
            if category not in self.stats['category_stats']:
                self.stats['category_stats'][category] = {'downloaded': 0, 'duplicates': 0, 'errors': 0}
            
            self.stats['category_stats'][category]['downloaded'] += downloaded
            self.stats['category_stats'][category]['duplicates'] += duplicates
            self.stats['category_stats'][category]['errors'] += errors
    
    def search_wallhaven_massive(self, category: str, terms: List[str], pages_per_term: int = 5) -> List[Dict]:
        """Massive Wallhaven search with multiple terms"""
        all_images = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for term in terms:
            for page in range(1, pages_per_term + 1):
                try:
                    url = "https://wallhaven.cc/api/v1/search"
                    params = {
                        "q": term,
                        "categories": "111",
                        "purity": "100",
                        "sorting": "toplist",
                        "order": "desc",
                        "page": page,
                        "atleast": "1920x1080"
                    }
                    
                    response = session.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    for wallpaper in data.get('data', []):
                        all_images.append({
                            'id': wallpaper['id'],
                            'url': wallpaper['path'],
                            'resolution': wallpaper['resolution'],
                            'file_size': wallpaper['file_size'],
                            'term': term
                        })
                    
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Search failed for {term} page {page}: {e}")
                    continue
        
        # Remove duplicates by ID
        seen_ids = set()
        unique_images = []
        for img in all_images:
            if img['id'] not in seen_ids:
                seen_ids.add(img['id'])
                unique_images.append(img)
        
        random.shuffle(unique_images)
        logger.info(f"{category}: Found {len(unique_images)} unique images from {len(terms)} terms")
        return unique_images
    
    def download_single_image(self, image_info: Dict, category: str, index: int) -> Dict:
        """Download single image with full error handling"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        try:
            url = image_info['url']
            filename = f"{category}_{index:03d}.jpg"
            
            # Download with retries
            for attempt in range(3):
                try:
                    response = session.get(url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # Read image data
                    image_data = response.content
                    
                    # Check for duplicates
                    if self.is_duplicate(image_data):
                        return {'status': 'duplicate', 'category': category}
                    
                    # Validate image size
                    if len(image_data) < 50000:  # Skip tiny images
                        return {'status': 'too_small', 'category': category}
                    
                    # Save image
                    filepath = self.output_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Create metadata
                    metadata = {
                        'id': f"{category}_{index:03d}",
                        'source': 'wallhaven_massive',
                        'category': category,
                        'title': f'{category.title()} Wallpaper {index}',
                        'description': f'High-quality {category} wallpaper from massive crawl',
                        'width': 1080,
                        'height': 1920,
                        'tags': [category, 'wallpaper', 'hd', 'high resolution', 'mobile'],
                        'download_url': url,
                        'original_info': image_info,
                        'crawled_at': datetime.now().isoformat() + 'Z'
                    }
                    
                    # Save metadata
                    metadata_file = filepath.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return {'status': 'success', 'category': category, 'filename': filename}
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:  # Last attempt
                        return {'status': 'error', 'category': category, 'error': str(e)}
                    time.sleep(1)  # Wait before retry
                    
        except Exception as e:
            return {'status': 'error', 'category': category, 'error': str(e)}
    
    def crawl_category_massive(self, category: str, target: int = 150) -> Dict:
        """Massively crawl single category with high parallelization"""
        logger.info(f"🚀 MASSIVE CRAWL: {category} (target: {target} images)")
        
        config = self.category_configs[category]
        terms = config['terms']
        
        # Search for images
        images = self.search_wallhaven_massive(category, terms, pages_per_term=8)
        
        if not images:
            logger.warning(f"No images found for {category}")
            return {'category': category, 'downloaded': 0, 'duplicates': 0, 'errors': 1}
        
        # Download with massive parallelization
        downloaded = 0
        duplicates = 0
        errors = 0
        
        with ThreadPoolExecutor(max_workers=12) as executor:  # High concurrency
            # Submit download tasks
            futures = []
            for i, image_info in enumerate(images[:target*2], 1):  # Get extra for failures
                future = executor.submit(self.download_single_image, image_info, category, downloaded + 1)
                futures.append(future)
            
            # Process results as they complete
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    logger.info(f"✅ {category}: {downloaded}/{target} - {result['filename']}")
                    
                elif result['status'] == 'duplicate':
                    duplicates += 1
                    
                elif result['status'] == 'error':
                    errors += 1
                    logger.warning(f"❌ {category}: Download failed - {result.get('error', 'Unknown')}")
                
                # Stop when we reach target
                if downloaded >= target:
                    break
        
        # Update global stats
        self.update_stats(category, downloaded, duplicates, errors)
        
        result = {
            'category': category,
            'downloaded': downloaded,
            'duplicates': duplicates,
            'errors': errors,
            'target': target,
            'found': len(images)
        }
        
        logger.info(f"🎉 {category} COMPLETE: {downloaded}/{target} downloaded, {duplicates} duplicates, {errors} errors")
        return result
    
    def massive_parallel_crawl(self, categories: List[str], target_per_category: int = 150, max_category_workers: int = 6) -> Dict:
        """Launch massive parallel crawl across all categories"""
        logger.info(f"🚀 LAUNCHING MASSIVE PARALLEL CRAWL")
        logger.info(f"📊 Categories: {len(categories)}")
        logger.info(f"🎯 Target per category: {target_per_category}")
        logger.info(f"⚡ Max parallel categories: {max_category_workers}")
        logger.info(f"💾 Existing hashes loaded: {len(self.downloaded_hashes)}")
        
        start_time = time.time()
        results = []
        
        # Process categories in parallel using ThreadPoolExecutor (avoids pickling issues)
        with ThreadPoolExecutor(max_workers=max_category_workers) as executor:
            # Submit all category crawl jobs
            future_to_category = {}
            for category in categories:
                if category in self.category_configs:
                    future = executor.submit(self.crawl_category_massive, category, target_per_category)
                    future_to_category[future] = category
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    progress = (completed / len(categories)) * 100
                    logger.info(f"📈 PROGRESS: {completed}/{len(categories)} categories complete ({progress:.1f}%)")
                    logger.info(f"✅ {category}: {result['downloaded']}/{result['target']} images")
                    
                except Exception as e:
                    logger.error(f"❌ Category {category} failed completely: {e}")
                    results.append({
                        'category': category, 
                        'downloaded': 0, 
                        'duplicates': 0, 
                        'errors': 1,
                        'target': target_per_category
                    })
        
        # Save final hashes
        self.save_hashes()
        
        # Calculate final statistics
        total_time = time.time() - start_time
        total_downloaded = sum(r['downloaded'] for r in results)
        total_duplicates = sum(r['duplicates'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        
        return {
            'results': results,
            'summary': {
                'total_categories': len(results),
                'total_downloaded': total_downloaded,
                'total_duplicates': total_duplicates,
                'total_errors': total_errors,
                'processing_time': total_time,
                'average_per_category': total_downloaded / len(results) if results else 0,
                'download_rate': total_downloaded / total_time if total_time > 0 else 0
            }
        }

def main():
    parser = argparse.ArgumentParser(description='Massive Parallel Wallpaper Crawler')
    parser.add_argument('--categories', 
                       default='nature,space,abstract,technology,anime,cars,gaming,cyberpunk,minimal,dark,neon,sports,architecture,art,vintage,gradient',
                       help='Categories to crawl')
    parser.add_argument('--target', type=int, default=150, help='Target images per category')
    parser.add_argument('--workers', type=int, default=6, help='Max parallel category workers')
    parser.add_argument('--output', default='massive_crawl', help='Output directory')
    
    args = parser.parse_args()
    
    # Parse categories
    categories = [cat.strip() for cat in args.categories.split(',')]
    
    # Create crawler
    crawler = MassiveParallelCrawler(args.output)
    
    # Launch massive crawl
    logger.info("🚀 INITIATING MASSIVE PARALLEL CRAWL...")
    results = crawler.massive_parallel_crawl(categories, args.target, args.workers)
    
    # Print comprehensive results
    summary = results['summary']
    
    print(f"\n🎉 MASSIVE CRAWL COMPLETE!")
    print(f"=" * 60)
    print(f"📊 Total Categories: {summary['total_categories']}")
    print(f"✅ Total Downloaded: {summary['total_downloaded']}")
    print(f"🔄 Total Duplicates: {summary['total_duplicates']}")
    print(f"❌ Total Errors: {summary['total_errors']}")
    print(f"⏱️  Total Time: {summary['processing_time']:.1f} seconds")
    print(f"📈 Download Rate: {summary['download_rate']:.1f} images/second")
    print(f"📊 Average per Category: {summary['average_per_category']:.1f} images")
    
    print(f"\n📁 CATEGORY BREAKDOWN:")
    print(f"{'Category':<15} {'Downloaded':<12} {'Target':<8} {'Success %':<10}")
    print(f"-" * 50)
    
    for result in sorted(results['results'], key=lambda x: x['downloaded'], reverse=True):
        success_rate = (result['downloaded'] / result['target']) * 100 if result['target'] > 0 else 0
        print(f"{result['category']:<15} {result['downloaded']:<12} {result['target']:<8} {success_rate:<10.1f}%")
    
    print(f"\n🔄 Next Steps:")
    print(f"1. Review: python scripts/review_images.py --input {args.output}")
    print(f"2. Process: python scripts/parallel_category_processor.py")
    print(f"3. Generate indexes: python scripts/generate_index_simple.py --update-all")

if __name__ == "__main__":
    main()