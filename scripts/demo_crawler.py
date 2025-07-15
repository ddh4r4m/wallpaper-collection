#!/usr/bin/env python3
"""
Demo image crawler for testing the wallpaper collection system
Uses publicly available images for demonstration purposes
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DemoCrawler:
    """Demo crawler using publicly available images"""
    
    def __init__(self, output_dir: str = "crawl_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Demo image sources (publicly available)
        self.demo_sources = {
            'nature': [
                'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1080&h=1920&fit=crop'
            ],
            'abstract': [
                'https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1080&h=1920&fit=crop'
            ],
            'space': [
                'https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1080&h=1920&fit=crop'
            ],
            'technology': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop'
            ],
            'minimal': [
                'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1516110833967-0b5640006de4?w=1080&h=1920&fit=crop'
            ]
        }
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WallpaperCollection/1.0 (Demo)'
        })
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images to avoid duplicates"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
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
    
    def download_image(self, url: str, filename: str, metadata: Dict) -> bool:
        """Download image with duplicate detection"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {filename}")
                return False
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update hash tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def crawl_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Crawl demo images for a specific category"""
        logger.info(f"Crawling demo images for category: {category}")
        
        if category not in self.demo_sources:
            logger.error(f"Category {category} not available in demo mode")
            return []
        
        urls = self.demo_sources[category][:limit]
        images = []
        
        for i, url in enumerate(urls, 1):
            # Create filename
            filename = f"demo_{category}_{i:03d}.jpg"
            
            # Prepare metadata
            metadata = {
                'id': f"{category}_{i:03d}",
                'source': 'unsplash_demo',
                'category': category,
                'title': f"{category.title()} Demo Wallpaper {i}",
                'description': f"Demo {category} wallpaper from Unsplash",
                'width': 1080,
                'height': 1920,
                'tags': [category, 'demo', 'wallpaper', 'mobile'],
                'download_url': url,
                'source_url': url,
                'crawled_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Download image
            if self.download_image(url, filename, metadata):
                images.append(metadata)
            
            # Rate limiting
            time.sleep(1)
        
        # Save crawl summary
        summary = {
            'category': category,
            'source': 'demo',
            'total_images': len(images),
            'crawl_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / f"{category}_crawl_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()
        
        logger.info(f"Demo crawl completed for {category}: {len(images)} images")
        return images

def main():
    parser = argparse.ArgumentParser(description='Demo image crawler')
    parser.add_argument('--category', required=True, help='Category to crawl')
    parser.add_argument('--limit', type=int, default=5, help='Max images to crawl')
    parser.add_argument('--output', default='crawl_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Create crawler
    crawler = DemoCrawler(args.output)
    
    # Crawl images
    images = crawler.crawl_category(args.category, args.limit)
    
    print(f"\n🎉 Demo crawl complete!")
    print(f"📊 Downloaded: {len(images)} images")
    print(f"📁 Category: {args.category}")
    print(f"💾 Output: {args.output}")
    print(f"\n🔄 Next steps:")
    print(f"1. source wallpaper_env/bin/activate")
    print(f"2. python scripts/review_images.py --input {args.output}")
    print(f"3. python scripts/process_approved.py --input review_system/approved --category {args.category}")

if __name__ == "__main__":
    main()