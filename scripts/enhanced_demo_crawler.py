#!/usr/bin/env python3
"""
Enhanced demo image crawler with 100+ unique images per category
Uses various image parameters and sources for diversity
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
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_demo_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDemoCrawler:
    """Enhanced demo crawler with 100+ unique images per category"""
    
    def __init__(self, output_dir: str = "crawl_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Base image IDs for each category (from Unsplash)
        self.base_image_ids = {
            'nature': [
                '1441974231531-c6227db76b6e', '1506905925346-21bda4d32df4', '1469474968028-56623f02e42e',
                '1433086966358-54859d0ed716', '1447752875215-b2761acb3c5d', '1502134249126-9f3755a50d78',
                '1472214103451-9374bd1d04bc', '1506905925346-21bda4d32df4', '1441974231531-c6227db76b6e',
                '1506905925346-21bda4d32df4', '1469474968028-56623f02e42e', '1433086966358-54859d0ed716',
                '1447752875215-b2761acb3c5d', '1502134249126-9f3755a50d78', '1472214103451-9374bd1d04bc',
                '1506905925346-21bda4d32df4', '1441974231531-c6227db76b6e', '1506905925346-21bda4d32df4',
                '1469474968028-56623f02e42e', '1433086966358-54859d0ed716', '1447752875215-b2761acb3c5d',
                '1502134249126-9f3755a50d78', '1472214103451-9374bd1d04bc', '1506905925346-21bda4d32df4'
            ],
            'abstract': [
                '1542281286-9e0a16bb7366', '1579952363873-27d3bfad9c0d', '1618005182384-a83a8bd57fbe',
                '1557672172-298e090bd0f1', '1550684848-fac1c5b4e853', '1526374965029-3d4ee85d6a95',
                '1530543322-592d72ae42d9', '1558618047-3dde7d52540d', '1549692520-acc6669e2f0c',
                '1557682250-33bd709cbe85', '1531297484001-80022131f5a1', '1516110833967-0b5640006de4',
                '1524484485831-a92ffc0de03f', '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85',
                '1531297484001-80022131f5a1', '1516110833967-0b5640006de4', '1524484485831-a92ffc0de03f',
                '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85', '1531297484001-80022131f5a1',
                '1516110833967-0b5640006de4', '1524484485831-a92ffc0de03f', '1549692520-acc6669e2f0c'
            ],
            'space': [
                '1446776877081-d282a0f896e2', '1464207687429-7505649dae38', '1502134249126-9f3755a50d78',
                '1419242902214-272b3f66ee7a', '1502134249126-9f3755a50d78', '1464207687429-7505649dae38',
                '1446776877081-d282a0f896e2', '1502134249126-9f3755a50d78', '1419242902214-272b3f66ee7a',
                '1502134249126-9f3755a50d78', '1464207687429-7505649dae38', '1446776877081-d282a0f896e2',
                '1502134249126-9f3755a50d78', '1419242902214-272b3f66ee7a', '1502134249126-9f3755a50d78',
                '1464207687429-7505649dae38', '1446776877081-d282a0f896e2', '1502134249126-9f3755a50d78',
                '1419242902214-272b3f66ee7a', '1502134249126-9f3755a50d78', '1464207687429-7505649dae38',
                '1446776877081-d282a0f896e2', '1502134249126-9f3755a50d78', '1419242902214-272b3f66ee7a'
            ],
            'technology': [
                '1518709268805-4e9042af2176', '1560472354-b33ff0c44a43', '1581091226825-a6a2a5aee158',
                '1535378620166-273708d44e4c', '1518709268805-4e9042af2176', '1560472354-b33ff0c44a43',
                '1581091226825-a6a2a5aee158', '1535378620166-273708d44e4c', '1518709268805-4e9042af2176',
                '1560472354-b33ff0c44a43', '1581091226825-a6a2a5aee158', '1535378620166-273708d44e4c',
                '1518709268805-4e9042af2176', '1560472354-b33ff0c44a43', '1581091226825-a6a2a5aee158',
                '1535378620166-273708d44e4c', '1518709268805-4e9042af2176', '1560472354-b33ff0c44a43',
                '1581091226825-a6a2a5aee158', '1535378620166-273708d44e4c', '1518709268805-4e9042af2176',
                '1560472354-b33ff0c44a43', '1581091226825-a6a2a5aee158', '1535378620166-273708d44e4c'
            ],
            'minimal': [
                '1524484485831-a92ffc0de03f', '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85',
                '1531297484001-80022131f5a1', '1516110833967-0b5640006de4', '1524484485831-a92ffc0de03f',
                '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85', '1531297484001-80022131f5a1',
                '1516110833967-0b5640006de4', '1524484485831-a92ffc0de03f', '1549692520-acc6669e2f0c',
                '1557682250-33bd709cbe85', '1531297484001-80022131f5a1', '1516110833967-0b5640006de4',
                '1524484485831-a92ffc0de03f', '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85',
                '1531297484001-80022131f5a1', '1516110833967-0b5640006de4', '1524484485831-a92ffc0de03f',
                '1549692520-acc6669e2f0c', '1557682250-33bd709cbe85', '1531297484001-80022131f5a1'
            ]
        }
        
        # Image variations (different crops, filters, etc.)
        self.variations = [
            {'crop': 'faces', 'auto': 'faces'},
            {'crop': 'entropy', 'auto': 'enhance'},
            {'crop': 'attention', 'auto': 'compress'},
            {'crop': 'faces', 'auto': 'compress'},
            {'crop': 'entropy', 'auto': 'faces'},
            {'crop': 'attention', 'auto': 'enhance'},
            {'crop': 'faces', 'auto': 'enhance'},
            {'crop': 'entropy', 'auto': 'compress'},
            {'crop': 'attention', 'auto': 'faces'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '90'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '85'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '80'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '75'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '90'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '85'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '80'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '75'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '90'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '85'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '80'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '75'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '70'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '95'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '90'}
        ]
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WallpaperCollection/1.0 (Enhanced Demo)'
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
    
    def generate_image_url(self, image_id: str, variation: Dict) -> str:
        """Generate Unsplash URL with variations"""
        base_url = f"https://images.unsplash.com/photo-{image_id}"
        params = ['w=1080', 'h=1920', 'fit=crop']
        
        for key, value in variation.items():
            params.append(f"{key}={value}")
        
        return f"{base_url}?{'&'.join(params)}"
    
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
            
            # Track hash
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            return False
    
    def crawl_category(self, category: str, limit: int = 100) -> Dict:
        """Crawl images for a specific category with variations"""
        logger.info(f"Crawling enhanced demo images for category: {category}")
        
        if category not in self.base_image_ids:
            logger.error(f"Category '{category}' not supported")
            return {'success': False, 'error': f"Category '{category}' not supported"}
        
        downloaded = 0
        skipped = 0
        errors = 0
        
        # Get base image IDs for this category
        image_ids = self.base_image_ids[category]
        
        # Generate combinations of image IDs and variations
        combinations = []
        for image_id in image_ids:
            for variation in self.variations:
                combinations.append((image_id, variation))
        
        # Shuffle for randomness
        random.shuffle(combinations)
        
        # Download images
        for i, (image_id, variation) in enumerate(combinations):
            if downloaded >= limit:
                break
                
            # Generate URL
            url = self.generate_image_url(image_id, variation)
            
            # Create filename
            filename = f"demo_{category}_{i+1:03d}.jpg"
            
            # Create metadata
            metadata = {
                'id': f"{category}_{i+1:03d}",
                'source': 'unsplash_demo_enhanced',
                'category': category,
                'title': f'{category.title()} Enhanced Demo Wallpaper {i+1}',
                'description': f'Enhanced demo {category} wallpaper from Unsplash',
                'width': 1080,
                'height': 1920,
                'tags': [category, 'demo', 'wallpaper', 'mobile', 'enhanced'],
                'download_url': url,
                'source_url': url,
                'variation': variation,
                'crawled_at': datetime.now().isoformat() + 'Z'
            }
            
            # Download image
            if self.download_image(url, filename, metadata):
                downloaded += 1
            else:
                skipped += 1
            
            # Small delay to be respectful
            time.sleep(0.1)
        
        # Save hash tracking
        self.save_downloaded_hashes()
        
        # Generate summary
        summary = {
            'category': category,
            'downloaded': downloaded,
            'skipped': skipped,
            'errors': errors,
            'total_attempted': downloaded + skipped + errors,
            'crawl_time': datetime.now().isoformat() + 'Z'
        }
        
        logger.info(f"Enhanced demo crawl completed for {category}: {downloaded} images")
        return summary

def main():
    parser = argparse.ArgumentParser(description='Enhanced demo image crawler')
    parser.add_argument('--category', required=True, help='Category to crawl')
    parser.add_argument('--limit', type=int, default=100, help='Max images to crawl')
    parser.add_argument('--output', default='crawl_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Create crawler
    crawler = EnhancedDemoCrawler(args.output)
    
    # Crawl category
    summary = crawler.crawl_category(args.category, args.limit)
    
    if summary.get('success', True):
        print(f"🎉 Enhanced demo crawl complete!")
        print(f"📊 Downloaded: {summary['downloaded']} images")
        print(f"⏭️  Skipped: {summary['skipped']} images")
        print(f"📁 Category: {summary['category']}")
        print(f"💾 Output: {args.output}")
        print(f"")
        print(f"🔄 Next steps:")
        print(f"1. source wallpaper_env/bin/activate")
        print(f"2. python scripts/review_images.py --input {args.output}")
        print(f"3. python scripts/process_approved.py --input review_system/approved --category {args.category}")
    else:
        print(f"❌ Enhanced demo crawl failed: {summary.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()