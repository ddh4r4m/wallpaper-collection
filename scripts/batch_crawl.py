#!/usr/bin/env python3
"""
Batch crawler to get 100+ images per category quickly
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_crawler(category: str, limit: int = 50):
    """Run enhanced demo crawler for a category"""
    cmd = [
        'python', 'scripts/enhanced_demo_crawler.py',
        '--category', category,
        '--limit', str(limit)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        logger.info(f"Crawler for {category} completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Errors: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.warning(f"Crawler for {category} timed out")
        return False
    except Exception as e:
        logger.error(f"Failed to run crawler for {category}: {e}")
        return False

def main():
    # Categories to crawl
    categories = ['nature', 'abstract', 'space', 'technology', 'minimal']
    
    # Run crawlers for each category
    for category in categories:
        logger.info(f"Starting crawler for category: {category}")
        success = run_crawler(category, 50)
        
        if success:
            logger.info(f"✅ Successfully crawled {category}")
        else:
            logger.error(f"❌ Failed to crawl {category}")
        
        # Small delay between categories
        time.sleep(2)
    
    # Check results
    crawl_cache = Path('crawl_cache')
    if crawl_cache.exists():
        jpg_files = list(crawl_cache.glob('*.jpg'))
        logger.info(f"📊 Total images downloaded: {len(jpg_files)}")
        
        # Count by category
        category_counts = {}
        for jpg_file in jpg_files:
            if '_' in jpg_file.stem:
                category = jpg_file.stem.split('_')[1]
                category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            logger.info(f"   {category}: {count} images")
    
    print("🎉 Batch crawling completed!")
    print("🔄 Next steps:")
    print("1. Review images: python scripts/review_images.py --input crawl_cache")
    print("2. Process approved images with batch_processor.py")

if __name__ == "__main__":
    main()