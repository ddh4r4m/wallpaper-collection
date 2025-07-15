#!/usr/bin/env python3
"""
Multi-source image crawler for wallpaper collection
Supports Unsplash, Pexels, Pixabay, Wallhaven, and custom scrapers
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl_images.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageCrawler:
    """Multi-source image crawler with rate limiting and duplicate detection"""
    
    def __init__(self, output_dir: str = "crawl_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # API keys (set these in environment variables)
        self.unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY', '')
        self.pexels_key = os.getenv('PEXELS_API_KEY', '')
        self.pixabay_key = os.getenv('PIXABAY_API_KEY', '')
        
        # For demo purposes, we'll use public endpoints where possible
        self.demo_mode = True
        
        # Rate limiting settings
        self.rate_limits = {
            'unsplash': 50,  # requests per hour
            'pexels': 200,   # requests per hour
            'pixabay': 100,  # requests per hour
            'wallhaven': 45, # requests per minute
            'custom': 30     # requests per minute
        }
        
        # Source-category mapping for optimal results
        self.source_mapping = {
            'nature': ['unsplash', 'pexels', 'pixabay'],
            'gaming': ['wallhaven', 'custom'],
            'anime': ['wallhaven', 'custom'],
            'cars': ['pexels', 'unsplash'],
            'sports': ['pexels', 'unsplash'],
            'technology': ['unsplash', 'pexels', 'wallhaven'],
            'space': ['unsplash', 'pexels', 'pixabay'],
            'abstract': ['pixabay', 'unsplash', 'pexels'],
            'architecture': ['unsplash', 'pexels'],
            'art': ['pixabay', 'unsplash'],
            'movies': ['custom', 'pixabay'],
            'music': ['unsplash', 'pexels'],
            'cyberpunk': ['wallhaven', 'custom'],
            'minimal': ['unsplash', 'pixabay'],
            'dark': ['wallhaven', 'custom'],
            'neon': ['wallhaven', 'custom'],
            'pastel': ['pixabay', 'unsplash'],
            'vintage': ['pixabay', 'unsplash'],
            'gradient': ['pixabay', 'unsplash'],
            'seasonal': ['unsplash', 'pexels']
        }
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WallpaperCollection/1.0 (Educational Purpose)'
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
    
    def crawl_unsplash(self, category: str, limit: int = 30) -> List[Dict]:
        """Crawl images from Unsplash API"""
        if not self.unsplash_key:
            logger.error("Unsplash API key not found. Set UNSPLASH_ACCESS_KEY environment variable.")
            return []
        
        logger.info(f"Crawling Unsplash for category: {category}")
        
        # Category mapping for Unsplash
        category_mapping = {
            'nature': 'nature',
            'space': 'space',
            'cars': 'cars',
            'sports': 'sports',
            'technology': 'technology',
            'architecture': 'architecture',
            'art': 'art',
            'music': 'music',
            'abstract': 'abstract',
            'minimal': 'minimal',
            'vintage': 'vintage',
            'gradient': 'gradient',
            'seasonal': 'seasonal'
        }
        
        query = category_mapping.get(category, category)
        
        images = []
        page = 1
        per_page = min(30, limit)
        
        while len(images) < limit:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                'query': query,
                'page': page,
                'per_page': per_page,
                'orientation': 'portrait',
                'client_id': self.unsplash_key
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('results'):
                    break
                
                for item in data['results']:
                    if len(images) >= limit:
                        break
                    
                    # Get high-resolution image URL
                    image_url = item['urls']['regular']  # 1080px wide
                    
                    # Create filename
                    filename = f"unsplash_{category}_{item['id']}.jpg"
                    
                    # Prepare metadata
                    metadata = {
                        'id': item['id'],
                        'source': 'unsplash',
                        'category': category,
                        'title': item.get('alt_description', f"{category} wallpaper"),
                        'description': item.get('description', ''),
                        'photographer': item['user']['name'],
                        'photographer_url': item['user']['links']['html'],
                        'width': item['width'],
                        'height': item['height'],
                        'color': item.get('color', '#000000'),
                        'tags': [tag['title'] for tag in item.get('tags', [])],
                        'download_url': image_url,
                        'source_url': item['links']['html'],
                        'crawled_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    # Download image
                    if self.download_image(image_url, filename, metadata):
                        images.append(metadata)
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error crawling Unsplash page {page}: {e}")
                break
        
        return images
    
    def crawl_pexels(self, category: str, limit: int = 30) -> List[Dict]:
        """Crawl images from Pexels API"""
        if not self.pexels_key:
            logger.error("Pexels API key not found. Set PEXELS_API_KEY environment variable.")
            return []
        
        logger.info(f"Crawling Pexels for category: {category}")
        
        images = []
        page = 1
        per_page = min(80, limit)
        
        headers = {'Authorization': self.pexels_key}
        
        while len(images) < limit:
            url = f"https://api.pexels.com/v1/search"
            params = {
                'query': category,
                'page': page,
                'per_page': per_page,
                'orientation': 'portrait'
            }
            
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('photos'):
                    break
                
                for item in data['photos']:
                    if len(images) >= limit:
                        break
                    
                    # Get high-resolution image URL
                    image_url = item['src']['large']  # Large size
                    
                    # Create filename
                    filename = f"pexels_{category}_{item['id']}.jpg"
                    
                    # Prepare metadata
                    metadata = {
                        'id': str(item['id']),
                        'source': 'pexels',
                        'category': category,
                        'title': item.get('alt', f"{category} wallpaper"),
                        'photographer': item['photographer'],
                        'photographer_url': item['photographer_url'],
                        'width': item['width'],
                        'height': item['height'],
                        'avg_color': item.get('avg_color', '#000000'),
                        'download_url': image_url,
                        'source_url': item['url'],
                        'crawled_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    # Download image
                    if self.download_image(image_url, filename, metadata):
                        images.append(metadata)
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error crawling Pexels page {page}: {e}")
                break
        
        return images
    
    def crawl_pixabay(self, category: str, limit: int = 30) -> List[Dict]:
        """Crawl images from Pixabay API"""
        if not self.pixabay_key:
            logger.error("Pixabay API key not found. Set PIXABAY_API_KEY environment variable.")
            return []
        
        logger.info(f"Crawling Pixabay for category: {category}")
        
        images = []
        page = 1
        per_page = min(200, limit)
        
        while len(images) < limit:
            url = f"https://pixabay.com/api/"
            params = {
                'key': self.pixabay_key,
                'q': category,
                'image_type': 'photo',
                'orientation': 'vertical',
                'category': 'backgrounds',
                'min_width': 1080,
                'min_height': 1920,
                'per_page': per_page,
                'page': page
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('hits'):
                    break
                
                for item in data['hits']:
                    if len(images) >= limit:
                        break
                    
                    # Get high-resolution image URL
                    image_url = item['largeImageURL']
                    
                    # Create filename
                    filename = f"pixabay_{category}_{item['id']}.jpg"
                    
                    # Prepare metadata
                    metadata = {
                        'id': str(item['id']),
                        'source': 'pixabay',
                        'category': category,
                        'title': f"{category} wallpaper",
                        'tags': item.get('tags', '').split(', '),
                        'user': item['user'],
                        'width': item['imageWidth'],
                        'height': item['imageHeight'],
                        'download_url': image_url,
                        'source_url': item['pageURL'],
                        'crawled_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    # Download image
                    if self.download_image(image_url, filename, metadata):
                        images.append(metadata)
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error crawling Pixabay page {page}: {e}")
                break
        
        return images
    
    def crawl_wallhaven(self, category: str, limit: int = 30) -> List[Dict]:
        """Crawl images from Wallhaven (basic implementation)"""
        logger.info(f"Crawling Wallhaven for category: {category}")
        
        # Category mapping for Wallhaven
        category_mapping = {
            'gaming': 'gaming',
            'anime': 'anime',
            'technology': 'technology',
            'cyberpunk': 'cyberpunk',
            'dark': 'dark',
            'neon': 'neon'
        }
        
        query = category_mapping.get(category, category)
        
        images = []
        page = 1
        
        while len(images) < limit and page <= 3:  # Limit pages to respect rate limits
            url = f"https://wallhaven.cc/api/v1/search"
            params = {
                'q': query,
                'categories': '111',  # General, Anime, People
                'purity': '100',      # SFW only
                'sorting': 'relevance',
                'order': 'desc',
                'page': page
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('data'):
                    break
                
                for item in data['data']:
                    if len(images) >= limit:
                        break
                    
                    # Get image URL
                    image_url = item['path']
                    
                    # Create filename
                    filename = f"wallhaven_{category}_{item['id']}.jpg"
                    
                    # Prepare metadata
                    metadata = {
                        'id': item['id'],
                        'source': 'wallhaven',
                        'category': category,
                        'title': f"{category} wallpaper",
                        'width': item['resolution'].split('x')[0],
                        'height': item['resolution'].split('x')[1],
                        'file_size': item['file_size'],
                        'colors': item.get('colors', []),
                        'tags': [tag['name'] for tag in item.get('tags', [])],
                        'download_url': image_url,
                        'source_url': item['url'],
                        'crawled_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    # Download image
                    if self.download_image(image_url, filename, metadata):
                        images.append(metadata)
                
                page += 1
                time.sleep(2)  # Rate limiting - more conservative
                
            except Exception as e:
                logger.error(f"Error crawling Wallhaven page {page}: {e}")
                break
        
        return images
    
    def crawl_category(self, category: str, sources: List[str], limit: int = 100) -> List[Dict]:
        """Crawl images for a specific category from multiple sources"""
        logger.info(f"Starting crawl for category: {category}")
        
        if not sources:
            sources = self.source_mapping.get(category, ['unsplash', 'pexels'])
        
        all_images = []
        images_per_source = limit // len(sources)
        
        for source in sources:
            try:
                if source == 'unsplash' and self.unsplash_key:
                    images = self.crawl_unsplash(category, images_per_source)
                elif source == 'pexels' and self.pexels_key:
                    images = self.crawl_pexels(category, images_per_source)
                elif source == 'pixabay' and self.pixabay_key:
                    images = self.crawl_pixabay(category, images_per_source)
                elif source == 'wallhaven':
                    images = self.crawl_wallhaven(category, images_per_source)
                else:
                    logger.warning(f"Source {source} not supported or API key missing")
                    continue
                
                all_images.extend(images)
                
            except Exception as e:
                logger.error(f"Error crawling {source} for {category}: {e}")
        
        # Save crawl summary
        summary = {
            'category': category,
            'sources': sources,
            'total_images': len(all_images),
            'images_per_source': {source: len([img for img in all_images if img['source'] == source]) for source in sources},
            'crawl_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / f"{category}_crawl_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()
        
        logger.info(f"Crawl completed for {category}: {len(all_images)} images")
        return all_images

def main():
    parser = argparse.ArgumentParser(description='Multi-source image crawler')
    parser.add_argument('--category', required=True, help='Category to crawl')
    parser.add_argument('--sources', help='Comma-separated list of sources')
    parser.add_argument('--limit', type=int, default=100, help='Max images to crawl')
    parser.add_argument('--output', default='crawl_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Parse sources
    sources = []
    if args.sources:
        sources = [s.strip() for s in args.sources.split(',')]
    
    # Create crawler
    crawler = ImageCrawler(args.output)
    
    # Crawl images
    images = crawler.crawl_category(args.category, sources, args.limit)
    
    print(f"\n🎉 Crawl complete!")
    print(f"📊 Downloaded: {len(images)} images")
    print(f"📁 Category: {args.category}")
    print(f"🔍 Sources: {sources if sources else 'auto-selected'}")
    print(f"\n🔄 Next steps:")
    print(f"1. python scripts/review_images.py --input {args.output}")
    print(f"2. Review approved/rejected images")
    print(f"3. python scripts/process_approved.py --category {args.category}")

if __name__ == "__main__":
    main()