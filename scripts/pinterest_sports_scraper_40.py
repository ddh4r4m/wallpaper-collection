#!/usr/bin/env python3
"""
Pinterest Sports Wallpaper Scraper - Agent 1
Targets exactly 40 high-quality sports wallpapers from Pinterest
Enhanced with comprehensive sports search strategy
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse, quote
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pinterest_sports_scraper_40.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestSportsScraper:
    """Pinterest sports wallpaper scraper targeting exactly 40 images"""
    
    def __init__(self, output_dir: str = "crawl_cache/pinterest/sports_40"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mobile wallpaper requirements
        self.min_width = 1080
        self.min_height = 1920
        self.preferred_width = 1440
        self.preferred_height = 2560
        
        # Target exactly 40 images
        self.target_count = 40
        
        # Enhanced rate limiting for better scraping
        self.request_delay = 8.0  # 8 seconds between requests
        self.query_delay = 10.0   # 10 seconds between different queries
        
        # Setup session with mobile user agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # Downloaded images tracking
        self.downloaded_hashes = set()
        self.load_existing_hashes()
        
        # Comprehensive sports search queries
        self.sports_queries = [
            # General sports
            "sports wallpaper mobile",
            "sports background hd",
            "athletic wallpaper",
            "sports phone wallpaper",
            "sports motivation wallpaper",
            "sports action wallpaper",
            
            # Specific sports
            "football wallpaper mobile",
            "basketball wallpaper phone",
            "soccer wallpaper hd",
            "tennis wallpaper mobile",
            "baseball wallpaper phone",
            "golf wallpaper mobile",
            
            # Sports equipment and themes
            "sports equipment wallpaper",
            "stadium wallpaper mobile",
            "sports arena background",
            "athletic motivation background",
            "sports field wallpaper",
            "gym motivation wallpaper",
            
            # Dynamic sports
            "sports action shot wallpaper",
            "athlete silhouette wallpaper",
            "sports dynamic wallpaper",
            "running wallpaper mobile",
            "fitness motivation wallpaper",
            "sports team wallpaper",
            
            # Olympic and professional sports
            "olympic sports wallpaper",
            "professional sports wallpaper",
            "sports championship wallpaper",
            "sports victory wallpaper"
        ]
        
        # Sports categorization for tracking
        self.sports_categories = {
            'football': ['football', 'nfl', 'american football'],
            'basketball': ['basketball', 'nba', 'basketball court'],
            'soccer': ['soccer', 'football', 'fifa', 'soccer ball'],
            'tennis': ['tennis', 'tennis court', 'tennis ball'],
            'baseball': ['baseball', 'mlb', 'baseball field'],
            'golf': ['golf', 'golf course', 'golf ball'],
            'general': ['sports', 'athletic', 'gym', 'fitness', 'stadium']
        }
        
        self.downloaded_by_category = {cat: 0 for cat in self.sports_categories}
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
                logger.info(f"Loaded {len(self.downloaded_hashes)} existing image hashes")
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
    
    def categorize_sport(self, query: str, url: str) -> str:
        """Categorize the sport based on query and URL"""
        query_lower = query.lower()
        url_lower = url.lower()
        
        for category, keywords in self.sports_categories.items():
            for keyword in keywords:
                if keyword in query_lower or keyword in url_lower:
                    return category
        
        return 'general'
    
    def extract_pinterest_images(self, query: str) -> List[str]:
        """Extract image URLs from Pinterest search using web scraping"""
        search_url = f"https://in.pinterest.com/search/pins/?q={quote(query)}"
        
        try:
            logger.info(f"Searching Pinterest: {search_url}")
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Extract image URLs from the HTML
            html_content = response.text
            
            # Enhanced Pinterest image URL patterns
            image_url_patterns = [
                r'https://i\.pinimg\.com/originals/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.jpg',
                r'https://i\.pinimg\.com/564x/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.jpg',
                r'https://i\.pinimg\.com/736x/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.jpg',
                r'https://i\.pinimg\.com/1200x/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]+\.jpg',
            ]
            
            image_urls = []
            for pattern in image_url_patterns:
                urls = re.findall(pattern, html_content)
                image_urls.extend(urls)
            
            # Remove duplicates
            unique_urls = list(set(image_urls))
            logger.info(f"Found {len(unique_urls)} unique image URLs for query: {query}")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"Failed to extract images for query '{query}': {e}")
            return []
    
    def get_high_res_url(self, url: str) -> str:
        """Convert Pinterest URL to highest resolution version"""
        # Replace size parameters with originals for highest quality
        if '/564x/' in url:
            return url.replace('/564x/', '/originals/')
        elif '/736x/' in url:
            return url.replace('/736x/', '/originals/')
        elif '/1200x/' in url:
            return url.replace('/1200x/', '/originals/')
        else:
            return url
    
    def is_valid_sports_image(self, image_data: bytes, query: str) -> bool:
        """Enhanced validation for sports images"""
        # Size check for high quality
        if len(image_data) < 100000:  # At least 100KB for good quality
            return False
        
        # Check if it's too large (likely not optimized)
        if len(image_data) > 5000000:  # More than 5MB
            return False
        
        return True
    
    def download_image(self, image_url: str, index: int, query: str) -> bool:
        """Download and save sports image"""
        try:
            # Get high-resolution version
            high_res_url = self.get_high_res_url(image_url)
            
            # Download image
            logger.info(f"Downloading: {high_res_url}")
            response = self.session.get(high_res_url, stream=True, timeout=30)
            response.raise_for_status()
            
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {high_res_url}")
                return False
            
            # Validate sports image
            if not self.is_valid_sports_image(image_data, query):
                logger.info(f"Invalid sports image, skipping: {high_res_url}")
                return False
            
            # Categorize sport
            sport_category = self.categorize_sport(query, high_res_url)
            
            # Create filename
            url_hash = hashlib.md5(high_res_url.encode()).hexdigest()[:12]
            filename = f"sports_{index:03d}_{sport_category}_{url_hash}.jpg"
            filepath = self.output_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Create metadata
            metadata = {
                'id': f"sports_{index:03d}_{url_hash}",
                'source': 'pinterest',
                'category': 'sports',
                'sport_type': sport_category,
                'title': f"Sports wallpaper - {sport_category.title()} {index}",
                'description': f"High-quality sports wallpaper from Pinterest search: {query}",
                'query': query,
                'file_size': len(image_data),
                'download_url': high_res_url,
                'tags': ['sports', sport_category, 'wallpaper', 'mobile', 'athletic'],
                'mobile_optimized': True,
                'estimated_resolution': 'High-resolution mobile wallpaper',
                'quality_score': min(10.0, len(image_data) / 100000),  # Simple quality estimate
                'crawled_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update tracking
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            self.downloaded_by_category[sport_category] += 1
            
            logger.info(f"✅ Downloaded sports wallpaper: {filename} ({len(image_data):,} bytes) - {sport_category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {image_url}: {e}")
            return False
    
    def scrape_sports_wallpapers(self) -> int:
        """Scrape exactly 40 sports wallpapers from Pinterest"""
        logger.info(f"🏈 Starting Pinterest sports wallpaper scraping - Target: {self.target_count} images")
        
        downloaded_count = 0
        total_attempts = 0
        query_index = 0
        
        while downloaded_count < self.target_count and query_index < len(self.sports_queries):
            query = self.sports_queries[query_index]
            logger.info(f"\n🔍 Searching ({downloaded_count}/{self.target_count}): {query}")
            
            # Extract image URLs
            image_urls = self.extract_pinterest_images(query)
            
            if not image_urls:
                logger.warning(f"No images found for query: {query}")
                query_index += 1
                continue
            
            # Download images from this query
            for url in image_urls:
                if downloaded_count >= self.target_count:
                    break
                
                total_attempts += 1
                
                if self.download_image(url, downloaded_count + 1, query):
                    downloaded_count += 1
                    logger.info(f"📊 Progress: {downloaded_count}/{self.target_count} ({(downloaded_count/self.target_count)*100:.1f}%)")
                
                # Rate limiting between downloads
                time.sleep(self.request_delay)
                
                # Check if we've reached our target
                if downloaded_count >= self.target_count:
                    break
            
            # Move to next query
            query_index += 1
            
            # Delay between different queries for better scraping
            if query_index < len(self.sports_queries) and downloaded_count < self.target_count:
                logger.info(f"⏱️  Waiting {self.query_delay}s before next query...")
                time.sleep(self.query_delay)
        
        logger.info(f"\n🎯 Sports scraping complete!")
        logger.info(f"📊 Final count: {downloaded_count}/{self.target_count} images")
        logger.info(f"🔄 Total attempts: {total_attempts}")
        
        return downloaded_count
    
    def create_comprehensive_summary(self, downloaded_count: int):
        """Create detailed crawl summary"""
        summary = {
            'agent': 'Agent 1 - Pinterest Sports Scraper',
            'target_count': self.target_count,
            'actual_downloaded': downloaded_count,
            'success_rate': f"{(downloaded_count/self.target_count)*100:.1f}%",
            'category': 'sports',
            'source': 'pinterest',
            'search_strategy': {
                'total_queries': len(self.sports_queries),
                'query_categories': [
                    'General sports terms',
                    'Specific sports (football, basketball, etc.)',
                    'Sports equipment and venues',
                    'Dynamic action shots',
                    'Professional and Olympic sports'
                ]
            },
            'sport_distribution': self.downloaded_by_category,
            'quality_requirements': {
                'min_file_size': '100KB',
                'max_file_size': '5MB',
                'target_resolution': 'Mobile optimized (1080x1920+)',
                'duplicate_detection': 'MD5 hash-based'
            },
            'search_queries_used': self.sports_queries,
            'technical_details': {
                'request_delay': f"{self.request_delay}s",
                'query_delay': f"{self.query_delay}s",
                'user_agent': 'Mobile iOS Safari',
                'pinterest_domains': ['in.pinterest.com'],
                'image_url_patterns': 4
            },
            'output_directory': str(self.output_dir),
            'crawl_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = self.output_dir / 'sports_scrape_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save downloaded hashes
        self.save_downloaded_hashes()
        
        logger.info(f"\n📋 Summary saved to: {summary_file}")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='Pinterest Sports Scraper - Agent 1 (40 Images)')
    parser.add_argument('--output', default='crawl_cache/pinterest/sports_40', help='Output directory')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = PinterestSportsScraper(args.output)
    
    try:
        # Scrape exactly 40 sports wallpapers
        downloaded = scraper.scrape_sports_wallpapers()
        
        # Create comprehensive summary
        summary = scraper.create_comprehensive_summary(downloaded)
        
        print(f"\n🏆 PINTEREST SPORTS SCRAPING COMPLETE - AGENT 1")
        print(f"=" * 60)
        print(f"🎯 Target: {scraper.target_count} images")
        print(f"✅ Downloaded: {downloaded} high-quality sports wallpapers")
        print(f"📊 Success Rate: {(downloaded/scraper.target_count)*100:.1f}%")
        print(f"📁 Output Directory: {args.output}")
        print(f"🏈 Focus: Diverse sports wallpapers for mobile")
        
        print(f"\n📋 Sport Distribution:")
        for sport, count in scraper.downloaded_by_category.items():
            if count > 0:
                print(f"  {sport.title()}: {count} images")
        
        print(f"\n📂 Files Created:")
        jpg_files = list(Path(args.output).glob("*.jpg"))
        for i, file in enumerate(jpg_files[:5], 1):
            sport_type = file.name.split('_')[2] if len(file.name.split('_')) > 2 else 'general'
            print(f"  {i}. {file.name} ({sport_type})")
        
        if len(jpg_files) > 5:
            print(f"  ... and {len(jpg_files) - 5} more files")
        
        print(f"\n🔄 Next Steps:")
        print(f"1. Review images in {args.output}/")
        print(f"2. Verify mobile wallpaper quality (1080x1920+)")
        print(f"3. Move approved images to wallpapers/sports/")
        print(f"4. Update collection indexes")
        
        if downloaded == scraper.target_count:
            print(f"\n🎉 MISSION ACCOMPLISHED! Exactly {scraper.target_count} sports wallpapers scraped!")
        else:
            print(f"\n⚠️  Target not fully met. Consider running additional queries or sources.")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print(f"\n⏸️  Scraping interrupted. Partial results may be available.")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()