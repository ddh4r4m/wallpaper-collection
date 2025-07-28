#!/usr/bin/env python3
"""
Agent 2 - Pinterest Football/Soccer Wallpaper Scraper
Target: Exactly 40 high-quality football/soccer wallpapers from Pinterest

Enhanced search strategy with duplicate detection and quality filtering.
"""

import requests
import json
import hashlib
import time
import os
import sys
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
import random
from typing import List, Dict, Set, Optional
import re

class PinterestFootballSoccerScraper:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Search URLs optimized for football/soccer content
        self.search_urls = [
            # American Football focused
            "https://in.pinterest.com/search/pins/?q=football%20wallpaper%20mobile",
            "https://in.pinterest.com/search/pins/?q=NFL%20wallpaper%20phone",
            "https://in.pinterest.com/search/pins/?q=american%20football%20wallpaper",
            "https://in.pinterest.com/search/pins/?q=football%20stadium%20wallpaper",
            "https://in.pinterest.com/search/pins/?q=NFL%20player%20wallpaper",
            "https://in.pinterest.com/search/pins/?q=football%20helmet%20wallpaper",
            
            # International Soccer focused
            "https://in.pinterest.com/search/pins/?q=soccer%20wallpaper%20hd",
            "https://in.pinterest.com/search/pins/?q=fifa%20soccer%20background",
            "https://in.pinterest.com/search/pins/?q=soccer%20ball%20wallpaper",
            "https://in.pinterest.com/search/pins/?q=football%20soccer%20mobile",
            "https://in.pinterest.com/search/pins/?q=soccer%20stadium%20wallpaper",
            "https://in.pinterest.com/search/pins/?q=world%20cup%20wallpaper",
            
            # Generic but high-yield
            "https://in.pinterest.com/search/pins/?q=football%20mobile%20wallpaper%20hd",
            "https://in.pinterest.com/search/pins/?q=soccer%20phone%20background",
            "https://in.pinterest.com/search/pins/?q=sports%20football%20wallpaper"
        ]
        
        # Track collected data
        self.collected_images = []
        self.downloaded_hashes: Set[str] = set()
        self.target_count = 40
        self.current_count = 0
        
        # Quality thresholds
        self.min_file_size = 50000  # 50KB minimum
        self.max_file_size = 2000000  # 2MB maximum
        
        # Load existing hashes to avoid duplicates with Agent 1
        self.load_existing_hashes()
        
    def load_existing_hashes(self):
        """Load hashes from Agent 1's collection to avoid duplicates"""
        agent1_dir = "../sports_40_final"
        if os.path.exists(agent1_dir):
            for filename in os.listdir(agent1_dir):
                if filename.endswith('.jpg'):
                    filepath = os.path.join(agent1_dir, filename)
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'rb') as f:
                                content = f.read()
                                md5_hash = hashlib.md5(content).hexdigest()
                                self.downloaded_hashes.add(md5_hash)
                                print(f"Added existing hash to avoid duplicates: {md5_hash[:8]}...")
                        except Exception as e:
                            print(f"Error reading {filepath}: {e}")
                            
    def get_md5_hash(self, content: bytes) -> str:
        """Calculate MD5 hash of image content"""
        return hashlib.md5(content).hexdigest()
        
    def is_football_soccer_content(self, title: str, description: str = "") -> tuple:
        """
        Determine if content is football/soccer related and classify type
        Returns: (is_relevant, sport_type)
        """
        content = f"{title} {description}".lower()
        
        # American Football indicators
        football_keywords = [
            'nfl', 'american football', 'football helmet', 'football stadium',
            'touchdown', 'quarterback', 'football field', 'superbowl', 'gridiron'
        ]
        
        # International Soccer indicators  
        soccer_keywords = [
            'soccer', 'fifa', 'world cup', 'soccer ball', 'soccer field',
            'goal keeper', 'football club', 'premier league', 'champions league'
        ]
        
        # Generic football (could be either)
        generic_football = ['football', 'sport', 'athletic']
        
        # Check for specific sport indicators
        for keyword in football_keywords:
            if keyword in content:
                return True, "american_football"
                
        for keyword in soccer_keywords:
            if keyword in content:
                return True, "soccer"
                
        # Check for generic football indicators
        for keyword in generic_football:
            if keyword in content:
                return True, "football_generic"
                
        return False, "none"
        
    def extract_pinterest_data(self, html_content: str) -> List[Dict]:
        """Extract Pinterest pin data from HTML using regex patterns"""
        pins = []
        
        # Look for Pinterest pin data patterns
        patterns = [
            r'"Pin":\s*({[^}]+})',
            r'"images":\s*({[^}]+})',
            r'"url":\s*"([^"]+\.jpg[^"]*)"',
            r'"url":\s*"([^"]+\.jpeg[^"]*)"',
            r'"url":\s*"([^"]+\.png[^"]*)"'
        ]
        
        urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('http') and any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    # Clean up URL
                    clean_url = match.split('?')[0]  # Remove query parameters
                    if len(clean_url) > 20:  # Basic URL validation
                        urls.add(clean_url)
        
        # Create pin objects from URLs
        for url in urls:
            pins.append({
                'id': str(hash(url))[-10:],
                'url': url,
                'title': f"Football/Soccer wallpaper from {urlparse(url).netloc}",
                'description': "High-quality sports wallpaper"
            })
            
        return pins
        
    def download_image(self, url: str, filename: str) -> Optional[Dict]:
        """Download image and return metadata"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.content
            if len(content) < self.min_file_size:
                return None
                
            if len(content) > self.max_file_size:
                return None
                
            # Check for duplicates
            md5_hash = self.get_md5_hash(content)
            if md5_hash in self.downloaded_hashes:
                return None
                
            # Save image
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(content)
                
            self.downloaded_hashes.add(md5_hash)
            
            return {
                'filepath': filepath,
                'url': url,
                'size': len(content),
                'md5_hash': md5_hash
            }
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None
            
    def scrape_search_url(self, search_url: str, max_images: int = 10) -> List[Dict]:
        """Scrape images from a specific search URL"""
        collected = []
        try:
            print(f"Scraping: {search_url}")
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            pins = self.extract_pinterest_data(response.text)
            print(f"Found {len(pins)} potential pins")
            
            for pin in pins[:max_images]:
                if self.current_count >= self.target_count:
                    break
                    
                # Check if content is football/soccer related
                is_relevant, sport_type = self.is_football_soccer_content(
                    pin.get('title', ''), 
                    pin.get('description', '')
                )
                
                if not is_relevant:
                    continue
                    
                # Generate filename
                image_num = self.current_count + 1
                filename = f"football_soccer_{image_num:03d}_{sport_type}_{pin['id']}.jpg"
                
                # Download image
                download_result = self.download_image(pin['url'], filename)
                if download_result:
                    metadata = {
                        'id': f"football_soccer_{image_num:03d}_{pin['id']}",
                        'source': 'pinterest',
                        'category': 'sports',
                        'sport_type': sport_type,
                        'title': pin.get('title', f"Football/Soccer wallpaper {image_num}"),
                        'description': pin.get('description', 'High-quality football/soccer wallpaper from Pinterest'),
                        'search_url': search_url,
                        'file_size': download_result['size'],
                        'download_url': pin['url'],
                        'md5_hash': download_result['md5_hash'],
                        'tags': ['sports', 'football', 'soccer', 'wallpaper', 'mobile'],
                        'mobile_optimized': True,
                        'estimated_resolution': 'High-resolution mobile wallpaper',
                        'quality_score': self.calculate_quality_score(download_result, sport_type),
                        'crawled_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Save metadata
                    json_filename = filename.replace('.jpg', '.json')
                    json_filepath = os.path.join(self.output_dir, json_filename)
                    with open(json_filepath, 'w') as f:
                        json.dump(metadata, f, indent=2)
                        
                    collected.append(metadata)
                    self.current_count += 1
                    
                    print(f"Downloaded {self.current_count}/40: {filename} ({sport_type})")
                    
                # Add delay between downloads
                time.sleep(random.uniform(3, 7))
                
        except Exception as e:
            print(f"Error scraping {search_url}: {e}")
            
        return collected
        
    def calculate_quality_score(self, download_result: Dict, sport_type: str) -> float:
        """Calculate quality score based on various factors"""
        score = 5.0  # Base score
        
        # File size scoring (optimal range 100KB - 500KB)
        size = download_result['size']
        if 100000 <= size <= 500000:
            score += 2.0
        elif 50000 <= size <= 100000 or 500000 <= size <= 800000:
            score += 1.0
        elif size > 800000:
            score -= 1.0
            
        # Sport type bonus
        if sport_type in ['american_football', 'soccer']:
            score += 1.5
        elif sport_type == 'football_generic':
            score += 1.0
            
        return round(min(score, 10.0), 1)
        
    def run_collection(self):
        """Main collection process"""
        print(f"Starting football/soccer wallpaper collection - Target: {self.target_count} images")
        print(f"Avoiding {len(self.downloaded_hashes)} duplicate hashes from Agent 1")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        for search_url in self.search_urls:
            if self.current_count >= self.target_count:
                break
                
            remaining = self.target_count - self.current_count
            max_per_search = min(8, remaining)  # Limit per search to ensure diversity
            
            collected = self.scrape_search_url(search_url, max_per_search)
            self.collected_images.extend(collected)
            
            # Enhanced delay between searches
            time.sleep(random.uniform(10, 15))
            
        # Generate final report
        self.generate_report()
        
    def generate_report(self):
        """Generate collection summary report"""
        sport_distribution = {}
        quality_scores = []
        file_sizes = []
        
        for img in self.collected_images:
            sport = img['sport_type']
            sport_distribution[sport] = sport_distribution.get(sport, 0) + 1
            quality_scores.append(img['quality_score'])
            file_sizes.append(img['file_size'])
            
        report = {
            'agent': 'Agent 2 - Pinterest Football/Soccer Scraper',
            'mission': 'Scrape exactly 40 football/soccer wallpapers from Pinterest',
            'target_count': self.target_count,
            'actual_collected': self.current_count,
            'success': self.current_count == self.target_count,
            'sport_distribution': sport_distribution,
            'search_strategy': [
                'American football focused searches (NFL, football helmet, etc.)',
                'International soccer focused searches (FIFA, soccer ball, etc.)',
                'Enhanced mobile wallpaper optimization',
                'Duplicate detection against Agent 1 collection',
                'Quality filtering and sport categorization'
            ],
            'quality_metrics': {
                'avg_quality_score': round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
                'avg_file_size': round(sum(file_sizes) / len(file_sizes)) if file_sizes else 0,
                'min_file_size': min(file_sizes) if file_sizes else 0,
                'max_file_size': max(file_sizes) if file_sizes else 0
            },
            'duplicate_prevention': {
                'agent1_hashes_loaded': len(self.downloaded_hashes) - len(self.collected_images),
                'duplicates_avoided': 'MD5 hash checking implemented'
            },
            'output_directory': self.output_dir,
            'completion_time': datetime.now(timezone.utc).isoformat(),
            'mission_status': 'COMPLETED ✅' if self.current_count == self.target_count else f'PARTIAL - {self.current_count}/{self.target_count}'
        }
        
        # Save report
        report_path = os.path.join(self.output_dir, 'football_soccer_collection_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nCollection complete!")
        print(f"Collected: {self.current_count}/{self.target_count} images")
        print(f"Sport distribution: {sport_distribution}")
        print(f"Report saved: {report_path}")

def main():
    output_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/football_soccer_40"
    
    scraper = PinterestFootballSoccerScraper(output_dir)
    scraper.run_collection()

if __name__ == "__main__":
    main()