#!/usr/bin/env python3
"""
Scrape 4K wallpapers from Unsplash
URL: https://unsplash.com/s/photos/wallpaper-4k?orientation=portrait
"""

import requests
import json
import time
import os
from pathlib import Path
import sys
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime
import random

class UnsplashScraper:
    def __init__(self, output_dir="4k_scrape_cache"):
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
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting
        self.delay_range = (2, 5)  # Random delay between requests
    
    def get_unsplash_photos(self, query="wallpaper-4k", orientation="portrait", per_page=20, page=1):
        """Get photos from Unsplash search API"""
        # Unsplash search URL
        url = "https://unsplash.com/napi/search/photos"
        
        params = {
            'query': query,
            'orientation': orientation,
            'per_page': per_page,
            'page': page,
            'order_by': 'relevant'
        }
        
        try:
            print(f"Fetching page {page} with query '{query}'...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            print(f"Error fetching photos: {e}")
            return []
    
    def download_image(self, photo_data, index):
        """Download a single image"""
        try:
            # Get the highest quality URL available
            urls = photo_data.get('urls', {})
            
            # Priority: raw > full > regular > small
            image_url = None
            for quality in ['raw', 'full', 'regular', 'small']:
                if quality in urls:
                    image_url = urls[quality]
                    break
            
            if not image_url:
                print(f"No suitable image URL found for photo {index}")
                return None
            
            # Add high quality parameters for better resolution
            if '?' in image_url:
                image_url += "&w=2160&h=3840&fit=crop&crop=center&q=85"
            else:
                image_url += "?w=2160&h=3840&fit=crop&crop=center&q=85"
            
            print(f"Downloading image {index}: {image_url}")
            
            # Download the image
            img_response = self.session.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            # Generate filename
            photo_id = photo_data.get('id', f'unknown_{index}')
            filename = f"4k_{index:03d}_{photo_id}.jpg"
            filepath = self.output_dir / filename
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # Extract metadata
            user = photo_data.get('user', {})
            photographer = user.get('name', 'Unknown')
            alt_description = photo_data.get('alt_description', '')
            description = photo_data.get('description', alt_description)
            
            # Get image dimensions from response
            width = photo_data.get('width', 0)
            height = photo_data.get('height', 0)
            
            metadata = {
                'id': f"4k_{index:03d}",
                'source': 'unsplash_4k_search',
                'category': '4k',
                'title': f"4K Wallpaper {index:03d}",
                'description': description[:200] if description else f"High-quality 4K wallpaper from Unsplash",
                'photographer': photographer,
                'tags': ['4k', 'wallpaper', 'hd', 'high resolution', 'portrait', 'mobile'],
                'unsplash_id': photo_id,
                'original_url': image_url.split('?')[0],  # Clean URL
                'download_url': image_url,
                'alt_text': alt_description,
                'width': width,
                'height': height,
                'scraped_at': datetime.now().isoformat(),
                'filename': filename,
                'file_size': len(img_response.content),
                'quality': 'raw' if 'raw' in image_url else 'full'
            }
            
            # Save metadata
            metadata_file = self.output_dir / f"{filename}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Downloaded: {filename} ({len(img_response.content)/1024:.1f}KB)")
            print(f"   Photographer: {photographer}")
            print(f"   Dimensions: {width}x{height}")
            
            return {
                'filepath': filepath,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"❌ Error downloading image {index}: {e}")
            return None
    
    def scrape_4k_wallpapers(self, total_images=100):
        """Scrape 4K wallpapers from Unsplash"""
        print(f"🚀 Starting 4K wallpaper scrape - Target: {total_images} images")
        print(f"📁 Output directory: {self.output_dir}")
        
        downloaded = 0
        page = 1
        per_page = 20
        
        # Different search queries to get variety
        queries = [
            "wallpaper-4k",
            "4k-wallpaper", 
            "ultra-hd-wallpaper",
            "high-resolution-wallpaper",
            "mobile-wallpaper-4k",
            "portrait-wallpaper",
            "phone-wallpaper-4k"
        ]
        
        current_query_index = 0
        
        while downloaded < total_images:
            try:
                # Use different queries for variety
                current_query = queries[current_query_index % len(queries)]
                
                # Get photos from current page
                photos = self.get_unsplash_photos(
                    query=current_query, 
                    orientation="portrait",
                    per_page=per_page, 
                    page=page
                )
                
                if not photos:
                    print(f"No more photos found for query '{current_query}', trying next query...")
                    current_query_index += 1
                    page = 1
                    
                    if current_query_index >= len(queries):
                        print("Exhausted all queries")
                        break
                    continue
                
                # Download each photo
                for i, photo in enumerate(photos):
                    if downloaded >= total_images:
                        break
                    
                    result = self.download_image(photo, downloaded + 1)
                    if result:
                        downloaded += 1
                        print(f"Progress: {downloaded}/{total_images}")
                    
                    # Rate limiting
                    delay = random.uniform(*self.delay_range)
                    print(f"⏳ Waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                page += 1
                
                # Switch query every 2 pages for variety
                if page % 3 == 0:
                    current_query_index += 1
                    page = 1
                
            except KeyboardInterrupt:
                print("\n⏹️ Scraping interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error on page {page}: {e}")
                time.sleep(5)
                continue
        
        print(f"\n🎉 Scraping complete!")
        print(f"📊 Downloaded: {downloaded} images")
        print(f"📁 Saved to: {self.output_dir}")
        
        return downloaded

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape 4K wallpapers from Unsplash')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    parser.add_argument('--output', default='4k_scrape_cache', help='Output directory')
    
    args = parser.parse_args()
    
    scraper = UnsplashScraper(output_dir=args.output)
    downloaded = scraper.scrape_4k_wallpapers(total_images=args.count)
    
    if downloaded > 0:
        print(f"\n✅ Successfully downloaded {downloaded} 4K wallpapers!")
        print(f"📁 Files saved to: {args.output}/")
        print("\n🔧 Next steps:")
        print("1. Review the downloaded images")
        print("2. Use tools/add_wallpaper.py to add them to the collection")
        print("3. Run tools/build_api.py to update APIs")
    else:
        print("❌ No images were downloaded")

if __name__ == '__main__':
    main()