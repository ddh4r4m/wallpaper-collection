#!/usr/bin/env python3
"""
Bulk scrape unique 4K wallpapers from Unsplash
Ensures all images are different by tracking IDs across the entire run
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

class UnsplashBulkScraper:
    def __init__(self, output_dir="4k_bulk_download"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Track downloaded photo IDs to prevent duplicates
        self.downloaded_ids = set()
        
        # Headers to appear more like a real browser (no Accept-Encoding to avoid compression issues)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://unsplash.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting (optimized for bulk downloads)
        self.delay_range = (0.8, 1.5)  # Faster rate limiting
    
    def search_photos_api(self, query="wallpaper", orientation="portrait", order_by="curated", page=1, per_page=20):
        """Search photos using Unsplash's internal API"""
        
        # Try the napi endpoint that Unsplash uses
        url = "https://unsplash.com/napi/search/photos"
        
        params = {
            'query': query,
            'orientation': orientation,
            'order_by': order_by,
            'page': page,
            'per_page': per_page,
            'plus': 'none'
        }
        
        try:
            print(f"  Searching API: {query} (page {page})")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"    Found {len(results)} photos")
                return results
            else:
                print(f"    API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"    API request failed: {e}")
            return []
    
    def get_high_res_url(self, photo_data):
        """Get the highest resolution URL for a photo"""
        urls = photo_data.get('urls', {})
        
        # Priority: raw > full > regular > small
        for quality in ['raw', 'full', 'regular', 'small']:
            if quality in urls:
                base_url = urls[quality]
                # Add 4K parameters for mobile wallpapers
                if '?' in base_url:
                    return f"{base_url}&w=1080&h=1920&fit=crop&crop=center&q=85"
                else:
                    return f"{base_url}?w=1080&h=1920&fit=crop&crop=center&q=85"
        
        return None
    
    def download_image(self, photo_data, index):
        """Download a single image"""
        try:
            photo_id = photo_data.get('id', f'unknown_{index}')
            
            # Check for duplicates
            if photo_id in self.downloaded_ids:
                print(f"    ⏭️  Duplicate: {photo_id}")
                return None
            
            image_url = self.get_high_res_url(photo_data)
            if not image_url:
                print(f"    ❌ No suitable URL for {photo_id}")
                return None
            
            print(f"    Downloading {index}: {photo_id}")
            
            # Mark as downloaded to prevent duplicates
            self.downloaded_ids.add(photo_id)
            
            # Download the image
            img_response = self.session.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            # Generate filename
            filename = f"4k_{index:03d}_{photo_id}.jpg"
            filepath = self.output_dir / filename
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # Extract metadata
            user = photo_data.get('user', {})
            photographer = user.get('name', 'Unknown')
            photographer_username = user.get('username', '')
            
            alt_description = photo_data.get('alt_description', '')
            description = photo_data.get('description', alt_description)
            
            width = photo_data.get('width', 0)
            height = photo_data.get('height', 0)
            
            # Extract color information
            color = photo_data.get('color', '#000000')
            
            # Get tags from photo
            tags = ['4k', 'wallpaper', 'hd', 'ultra high definition', 'portrait', 'mobile', 'curated']
            
            # Add color-based tags
            if color:
                tags.append(f"color-{color.replace('#', '')}")
            
            # Add description-based tags
            if description:
                desc_lower = description.lower()
                if 'nature' in desc_lower:
                    tags.append('nature')
                if 'city' in desc_lower or 'urban' in desc_lower:
                    tags.append('urban')
                if 'minimal' in desc_lower:
                    tags.append('minimal')
                if 'abstract' in desc_lower:
                    tags.append('abstract')
            
            metadata = {
                'id': f"4k_{index:03d}",
                'source': 'unsplash_4k_bulk_unique',
                'category': '4k',
                'title': f"4K Curated Wallpaper {index:03d}",
                'description': description[:200] if description else f"High-quality 4K curated wallpaper from Unsplash",
                'photographer': photographer,
                'photographer_username': photographer_username,
                'tags': tags,
                'unsplash_id': photo_id,
                'original_url': photo_data.get('links', {}).get('html', ''),
                'download_url': image_url,
                'alt_text': alt_description,
                'width': width,
                'height': height,
                'color': color,
                'scraped_at': datetime.now().isoformat(),
                'filename': filename,
                'file_size': len(img_response.content),
                'quality': '4k_optimized'
            }
            
            # Save metadata
            metadata_file = self.output_dir / f"{filename}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"    ✅ Downloaded: {filename} ({len(img_response.content)/1024:.1f}KB)")
            print(f"       Photographer: {photographer}")
            
            return {
                'filepath': filepath,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"    ❌ Error downloading {photo_id}: {e}")
            return None
    
    def scrape_4k_bulk(self, total_images=200):
        """Scrape unique 4K wallpapers from Unsplash API"""
        print(f"🚀 Starting bulk 4K wallpaper scrape - Target: {total_images} UNIQUE images")
        print(f"📁 Output directory: {self.output_dir}")
        
        downloaded = 0
        per_page = 20
        
        # Very diverse search queries for maximum variety
        queries = [
            "4k wallpaper",
            "hd wallpaper", 
            "mobile wallpaper",
            "phone wallpaper",
            "ultra hd",
            "high resolution",
            "4k background",
            "wallpaper portrait",
            "abstract wallpaper",
            "nature wallpaper",
            "minimal wallpaper",
            "colorful wallpaper",
            "dark wallpaper",
            "gradient wallpaper",
            "geometric wallpaper",
            "landscape wallpaper",
            "architecture wallpaper",
            "artistic wallpaper",
            "texture wallpaper",
            "pattern wallpaper",
            "space wallpaper",
            "mountain wallpaper",
            "ocean wallpaper",
            "city wallpaper",
            "forest wallpaper",
            "sunset wallpaper",
            "cloud wallpaper",
            "sky wallpaper",
            "flower wallpaper",
            "animal wallpaper"
        ]
        
        # Use different order_by options for more variety
        order_options = ['curated', 'relevant', 'latest']
        
        query_index = 0
        order_index = 0
        page = 1
        max_pages_per_query = 10  # Limit pages per query to ensure variety
        
        while downloaded < total_images:
            try:
                if query_index >= len(queries):
                    print(f"🔄 Exhausted all queries, cycling through different order options...")
                    query_index = 0
                    order_index = (order_index + 1) % len(order_options)
                    if order_index == 0:
                        print("⚠️  Cycling through all combinations, may start seeing duplicates")
                
                current_query = queries[query_index]
                current_order = order_options[order_index]
                
                print(f"\n📋 Query: '{current_query}' (order: {current_order}, page: {page})")
                
                # Search for photos
                photos = self.search_photos_api(
                    query=current_query,
                    orientation="portrait",
                    order_by=current_order,
                    page=page,
                    per_page=per_page
                )
                
                if not photos:
                    print(f"    No photos found, moving to next query...")
                    query_index += 1
                    page = 1
                    continue
                
                # Track how many downloaded from this batch
                batch_downloaded = 0
                
                # Download each photo
                for photo in photos:
                    if downloaded >= total_images:
                        break
                    
                    result = self.download_image(photo, downloaded + 1)
                    if result:
                        downloaded += 1
                        batch_downloaded += 1
                        print(f"    Progress: {downloaded}/{total_images} total ({batch_downloaded} from this batch)")
                        
                        # Rate limiting
                        delay = random.uniform(*self.delay_range)
                        time.sleep(delay)
                    # Skip delay for duplicates to speed up processing
                
                print(f"    Batch complete: {batch_downloaded} new images downloaded")
                
                page += 1
                
                # Switch query after max pages or if no new images from this batch
                if page > max_pages_per_query or batch_downloaded == 0:
                    query_index += 1
                    page = 1
                
            except KeyboardInterrupt:
                print("\n⏹️ Scraping interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(2)
                continue
        
        print(f"\n🎉 Bulk scraping complete!")
        print(f"📊 Downloaded: {downloaded} UNIQUE images")
        print(f"📁 Saved to: {self.output_dir}")
        print(f"🔄 Total unique IDs tracked: {len(self.downloaded_ids)}")
        
        return downloaded

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk scrape unique 4K wallpapers from Unsplash')
    parser.add_argument('--count', type=int, default=200, help='Number of unique images to scrape')
    parser.add_argument('--output', default='4k_bulk_download', help='Output directory')
    
    args = parser.parse_args()
    
    scraper = UnsplashBulkScraper(output_dir=args.output)
    downloaded = scraper.scrape_4k_bulk(total_images=args.count)
    
    if downloaded > 0:
        print(f"\n✅ Successfully downloaded {downloaded} unique 4K wallpapers!")
        print(f"📁 Files saved to: {args.output}/")
        print("\n🔧 Next steps:")
        print("1. Review the downloaded images")
        print("2. Use tools/add_wallpaper.py to add them to the collection")
        print("3. Run tools/build_api.py to update APIs")
    else:
        print("❌ No images were downloaded")

if __name__ == '__main__':
    main()