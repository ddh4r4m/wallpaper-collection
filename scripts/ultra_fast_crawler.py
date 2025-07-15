#!/usr/bin/env python3
"""
Ultra Fast Crawler - Optimized for maximum speed and scale
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
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraFastCrawler:
    """Ultra fast crawler optimized for massive parallel downloads"""
    
    def __init__(self, output_dir: str = "ultra_crawl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Category configurations
        self.categories = {
            'nature': ['landscape', 'forest', 'mountains', 'ocean', 'sunset'],
            'space': ['galaxy', 'nebula', 'stars', 'universe', 'cosmos'],
            'anime': ['anime', 'manga', 'kawaii', 'otaku'],
            'cars': ['sports car', 'racing', 'automotive', 'supercar'],
            'gaming': ['gaming', 'video games', 'esports', 'controller'],
            'cyberpunk': ['cyberpunk', 'neon', 'futuristic', 'sci-fi'],
            'minimal': ['minimal', 'clean', 'simple', 'zen'],
            'dark': ['dark', 'black', 'gothic', 'shadow'],
            'technology': ['technology', 'digital', 'circuit', 'tech'],
            'abstract': ['abstract', 'geometric', 'pattern', 'digital art'],
            'sports': ['football', 'basketball', 'soccer', 'athletics'],
            'architecture': ['buildings', 'skyscrapers', 'urban', 'city']
        }
        
        # Thread-safe counters
        self.counters = defaultdict(int)
        self.counter_lock = threading.Lock()
        
        # Hash tracking
        self.downloaded_hashes = set()
        self.hash_lock = threading.Lock()
        self.load_hashes()
    
    def load_hashes(self):
        """Load existing hashes"""
        hash_files = [
            'crawl_cache/downloaded_hashes.json',
            'multi_crawl_cache/downloaded_hashes.json', 
            'wallhaven_cache/wallhaven_hashes.json',
            'massive_crawl/massive_hashes.json'
        ]
        
        for hash_file in hash_files:
            if Path(hash_file).exists():
                try:
                    with open(hash_file, 'r') as f:
                        self.downloaded_hashes.update(json.load(f))
                except:
                    pass
        
        logger.info(f"Loaded {len(self.downloaded_hashes)} existing hashes")
    
    def get_next_index(self, category: str) -> int:
        """Get next available index for category"""
        with self.counter_lock:
            self.counters[category] += 1
            return self.counters[category]
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check and add hash atomically"""
        image_hash = hashlib.md5(image_data).hexdigest()
        with self.hash_lock:
            if image_hash in self.downloaded_hashes:
                return True
            self.downloaded_hashes.add(image_hash)
            return False
    
    def search_wallhaven_fast(self, query: str, pages: int = 3) -> List[Dict]:
        """Fast Wallhaven search"""
        images = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for page in range(1, pages + 1):
            try:
                response = session.get("https://wallhaven.cc/api/v1/search", params={
                    "q": query,
                    "categories": "111",
                    "purity": "100",
                    "sorting": "toplist",
                    "page": page,
                    "atleast": "1920x1080"
                }, timeout=8)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('data', []):
                        images.append({
                            'id': item['id'],
                            'url': item['path']
                        })
                else:
                    break  # Stop on rate limit
                    
                time.sleep(0.4)  # Rate limiting
                
            except:
                break
        
        return images
    
    def download_image_fast(self, image_info: Dict, category: str) -> Dict:
        """Ultra fast single image download"""
        session = requests.Session()
        
        try:
            # Get next index
            index = self.get_next_index(category)
            filename = f"{category}_{index:03d}.jpg"
            
            # Download
            response = session.get(image_info['url'], timeout=20)
            response.raise_for_status()
            
            image_data = response.content
            
            # Skip tiny images
            if len(image_data) < 30000:
                return {'status': 'small'}
            
            # Check duplicates
            if self.is_duplicate(image_data):
                return {'status': 'duplicate'}
            
            # Save
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Quick metadata
            metadata = {
                'id': f"{category}_{index:03d}",
                'category': category,
                'source': 'wallhaven_ultra',
                'url': image_info['url'],
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(filepath.with_suffix('.json'), 'w') as f:
                json.dump(metadata, f)
            
            return {'status': 'success', 'filename': filename}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def crawl_category_ultra(self, category: str, target: int = 100) -> Dict:
        """Ultra fast category crawling"""
        logger.info(f"🚀 ULTRA CRAWL: {category} (target: {target})")
        
        # Get search terms
        search_terms = self.categories.get(category, [category])
        
        # Collect images from all terms
        all_images = []
        for term in search_terms[:3]:  # Limit terms to avoid rate limits
            images = self.search_wallhaven_fast(term, pages=4)
            all_images.extend(images)
        
        # Remove duplicates
        seen_ids = set()
        unique_images = []
        for img in all_images:
            if img['id'] not in seen_ids:
                seen_ids.add(img['id'])
                unique_images.append(img)
        
        random.shuffle(unique_images)
        logger.info(f"{category}: Found {len(unique_images)} unique images")
        
        # Download with high parallelization
        downloaded = 0
        duplicates = 0
        errors = 0
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            # Submit downloads
            futures = []
            for image_info in unique_images[:target*2]:  # Get extra for failures
                future = executor.submit(self.download_image_fast, image_info, category)
                futures.append(future)
            
            # Process results
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    downloaded += 1
                    if downloaded % 10 == 0:
                        logger.info(f"✅ {category}: {downloaded}/{target}")
                    
                elif result['status'] == 'duplicate':
                    duplicates += 1
                    
                elif result['status'] == 'error':
                    errors += 1
                
                # Stop when target reached
                if downloaded >= target:
                    break
        
        logger.info(f"🎉 {category}: {downloaded}/{target} downloaded")
        return {
            'category': category,
            'downloaded': downloaded,
            'duplicates': duplicates,
            'errors': errors,
            'target': target
        }
    
    def ultra_parallel_crawl(self, categories: List[str], target: int = 100, workers: int = 6) -> Dict:
        """Launch ultra parallel crawl"""
        logger.info(f"🚀 ULTRA PARALLEL CRAWL STARTING")
        logger.info(f"Categories: {len(categories)}, Target: {target} each, Workers: {workers}")
        
        start_time = time.time()
        
        # Process categories in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.crawl_category_ultra, cat, target): cat 
                for cat in categories if cat in self.categories
            }
            
            results = []
            for future in as_completed(futures):
                category = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ COMPLETE: {category} - {result['downloaded']}/{result['target']}")
                except Exception as e:
                    logger.error(f"❌ FAILED: {category} - {e}")
                    results.append({
                        'category': category,
                        'downloaded': 0,
                        'duplicates': 0,
                        'errors': 1,
                        'target': target
                    })
        
        # Save hashes
        hash_file = self.output_dir / 'ultra_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
        
        # Calculate summary
        total_time = time.time() - start_time
        total_downloaded = sum(r['downloaded'] for r in results)
        
        return {
            'results': results,
            'summary': {
                'total_downloaded': total_downloaded,
                'total_time': total_time,
                'rate': total_downloaded / total_time if total_time > 0 else 0,
                'categories': len(results)
            }
        }

def main():
    parser = argparse.ArgumentParser(description='Ultra Fast Crawler')
    parser.add_argument('--categories', 
                       default='nature,space,anime,cars,gaming,cyberpunk,minimal,dark,technology,abstract,sports,architecture',
                       help='Categories to crawl')
    parser.add_argument('--target', type=int, default=100, help='Images per category')
    parser.add_argument('--workers', type=int, default=6, help='Parallel workers')
    parser.add_argument('--output', default='ultra_crawl', help='Output directory')
    
    args = parser.parse_args()
    
    categories = [c.strip() for c in args.categories.split(',')]
    crawler = UltraFastCrawler(args.output)
    
    # Launch ultra crawl
    results = crawler.ultra_parallel_crawl(categories, args.target, args.workers)
    
    # Print results
    summary = results['summary']
    print(f"\n🎉 ULTRA CRAWL COMPLETE!")
    print(f"=" * 50)
    print(f"✅ Total Downloaded: {summary['total_downloaded']}")
    print(f"⏱️  Total Time: {summary['total_time']:.1f}s")
    print(f"🚀 Download Rate: {summary['rate']:.1f} images/sec")
    print(f"📊 Categories: {summary['categories']}")
    
    print(f"\n📁 BREAKDOWN:")
    for result in sorted(results['results'], key=lambda x: x['downloaded'], reverse=True):
        success = (result['downloaded']/result['target']*100) if result['target'] > 0 else 0
        print(f"  {result['category']:<12}: {result['downloaded']:>3}/{result['target']:<3} ({success:>5.1f}%)")
    
    print(f"\n🔄 Next: Review images in {args.output}/")

if __name__ == "__main__":
    main()