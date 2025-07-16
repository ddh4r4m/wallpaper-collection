#!/usr/bin/env python3
"""
Scrape curated 4K wallpapers from Unsplash
URL: https://unsplash.com/s/photos/wallpaper-4k?order_by=curated&orientation=portrait
"""

import requests
import json
import time
import os
import re
from pathlib import Path
import sys
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime
import random
from bs4 import BeautifulSoup

class UnsplashCuratedScraper:
    def __init__(self, output_dir="4k_curated_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Headers to appear more like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting
        self.delay_range = (3, 7)  # Random delay between requests
    
    def get_page_content(self, url):
        """Get page content from Unsplash"""
        try:
            print(f"Fetching page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None
    
    def extract_image_urls_from_html(self, html_content):
        """Extract image URLs from the HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for image elements and data attributes
            images = []
            
            # Find all img tags with srcset or data-src
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                # Check for various URL attributes
                src = img.get('src', '')
                srcset = img.get('srcset', '')
                data_src = img.get('data-src', '')
                
                # Look for high-resolution Unsplash URLs
                for url_attr in [src, data_src]:
                    if url_attr and 'images.unsplash.com' in url_attr:
                        # Clean up the URL and extract the photo ID
                        if '/photo-' in url_attr:
                            # Extract photo ID from URL
                            photo_id_match = re.search(r'/photo-([a-zA-Z0-9_-]+)', url_attr)
                            if photo_id_match:
                                photo_id = photo_id_match.group(1)
                                # Construct high-quality URL
                                high_res_url = f"https://images.unsplash.com/photo-{photo_id}?w=2160&h=3840&fit=crop&crop=center&q=85"
                                images.append({
                                    'url': high_res_url,
                                    'photo_id': photo_id,
                                    'original_url': url_attr
                                })
                
                # Also check srcset for multiple resolutions
                if srcset and 'images.unsplash.com' in srcset:
                    # Extract URLs from srcset
                    srcset_urls = re.findall(r'(https://[^\s]+)', srcset)
                    for srcset_url in srcset_urls:
                        if 'photo-' in srcset_url:
                            photo_id_match = re.search(r'/photo-([a-zA-Z0-9_-]+)', srcset_url)
                            if photo_id_match:
                                photo_id = photo_id_match.group(1)
                                high_res_url = f"https://images.unsplash.com/photo-{photo_id}?w=2160&h=3840&fit=crop&crop=center&q=85"
                                images.append({
                                    'url': high_res_url,
                                    'photo_id': photo_id,
                                    'original_url': srcset_url
                                })
            
            # Remove duplicates based on photo_id
            unique_images = {}
            for img in images:
                photo_id = img['photo_id']
                if photo_id not in unique_images:
                    unique_images[photo_id] = img
            
            return list(unique_images.values())
            
        except Exception as e:
            print(f"Error extracting image URLs: {e}")
            return []
    
    def download_image(self, image_data, index):
        """Download a single image"""
        try:
            image_url = image_data['url']
            photo_id = image_data['photo_id']
            
            print(f"Downloading image {index}: {image_url}")
            
            # Download the image
            img_response = self.session.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            # Generate filename
            filename = f"4k_{index:03d}_{photo_id}.jpg"
            filepath = self.output_dir / filename
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # Create metadata
            metadata = {
                'id': f"4k_{index:03d}",
                'source': 'unsplash_4k_curated',
                'category': '4k',
                'title': f"4K Curated Wallpaper {index:03d}",
                'description': f"High-quality 4K curated wallpaper from Unsplash",
                'photographer': 'Unsplash Contributor',
                'tags': ['4k', 'wallpaper', 'hd', 'ultra high definition', 'portrait', 'mobile', 'curated'],
                'unsplash_id': photo_id,
                'original_url': image_data['original_url'],
                'download_url': image_url,
                'scraped_at': datetime.now().isoformat(),
                'filename': filename,
                'file_size': len(img_response.content),
                'quality': '4k'
            }
            
            # Save metadata
            metadata_file = self.output_dir / f"{filename}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Downloaded: {filename} ({len(img_response.content)/1024:.1f}KB)")
            
            return {
                'filepath': filepath,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"❌ Error downloading image {index}: {e}")
            return None
    
    def scrape_4k_curated(self, total_images=25):
        """Scrape curated 4K wallpapers from Unsplash"""
        print(f"🚀 Starting curated 4K wallpaper scrape - Target: {total_images} images")
        print(f"📁 Output directory: {self.output_dir}")
        
        downloaded = 0
        
        # Different page URLs to get variety
        base_urls = [
            "https://unsplash.com/s/photos/wallpaper-4k?order_by=curated&orientation=portrait",
            "https://unsplash.com/s/photos/4k-wallpaper?order_by=curated&orientation=portrait",
            "https://unsplash.com/s/photos/hd-wallpaper?order_by=curated&orientation=portrait",
            "https://unsplash.com/s/photos/mobile-wallpaper?order_by=curated&orientation=portrait",
            "https://unsplash.com/s/photos/phone-wallpaper?order_by=curated&orientation=portrait"
        ]
        
        for base_url in base_urls:
            if downloaded >= total_images:
                break
                
            try:
                # Get the page content
                html_content = self.get_page_content(base_url)
                if not html_content:
                    print(f"Failed to get content from {base_url}")
                    continue
                
                # Extract image URLs
                images = self.extract_image_urls_from_html(html_content)
                print(f"Found {len(images)} images on page")
                
                if not images:
                    print(f"No images found on {base_url}")
                    continue
                
                # Download each image
                for image_data in images:
                    if downloaded >= total_images:
                        break
                    
                    result = self.download_image(image_data, downloaded + 1)
                    if result:
                        downloaded += 1
                        print(f"Progress: {downloaded}/{total_images}")
                    
                    # Rate limiting
                    delay = random.uniform(*self.delay_range)
                    print(f"⏳ Waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                # Delay between pages
                if downloaded < total_images:
                    page_delay = random.uniform(5, 10)
                    print(f"🔄 Moving to next page, waiting {page_delay:.1f}s...")
                    time.sleep(page_delay)
                
            except KeyboardInterrupt:
                print("\n⏹️ Scraping interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error processing {base_url}: {e}")
                time.sleep(5)
                continue
        
        print(f"\n🎉 Scraping complete!")
        print(f"📊 Downloaded: {downloaded} images")
        print(f"📁 Saved to: {self.output_dir}")
        
        return downloaded

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape curated 4K wallpapers from Unsplash')
    parser.add_argument('--count', type=int, default=25, help='Number of images to scrape')
    parser.add_argument('--output', default='4k_curated_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Check if BeautifulSoup is available
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ BeautifulSoup4 is required. Install it with:")
        print("pip3 install --break-system-packages beautifulsoup4")
        return
    
    scraper = UnsplashCuratedScraper(output_dir=args.output)
    downloaded = scraper.scrape_4k_curated(total_images=args.count)
    
    if downloaded > 0:
        print(f"\n✅ Successfully downloaded {downloaded} curated 4K wallpapers!")
        print(f"📁 Files saved to: {args.output}/")
        print("\n🔧 Next steps:")
        print("1. Review the downloaded images")
        print("2. Use tools/add_wallpaper.py to add them to the collection")
        print("3. Run tools/build_api.py to update APIs")
    else:
        print("❌ No images were downloaded")

if __name__ == '__main__':
    main()