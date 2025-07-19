#!/usr/bin/env python3
"""
Scrape AI-generated wallpapers from multiple sources
Usage: ./tools/scrape_ai_wallpapers.py --category abstract --count 50 [options]

This tool fetches AI-generated wallpapers from:
- Civitai (Stable Diffusion community)
- Lexica (Stable Diffusion search engine)
- Arthub.ai (AI art community)
- Reddit AI communities
"""

import os
import sys
import json
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
import hashlib
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
from add_wallpaper import WallpaperManager

class AIWallpaperScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Download directory
        self.download_dir = Path("/tmp/ai_wallpaper_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # AI source configurations
        self.ai_sources = {
            'civitai': {
                'api_url': 'https://civitai.com/api/v1/images',
                'rate_limit': 2,
                'quality': 'excellent'
            },
            'lexica': {
                'api_url': 'https://lexica.art/api/v1/search',
                'rate_limit': 1,
                'quality': 'excellent'
            },
            'arthub': {
                'base_url': 'https://arthub.ai',
                'rate_limit': 3,
                'quality': 'good'
            }
        }
        
        # Category-specific AI prompts and search terms
        self.ai_category_configs = {
            'abstract': {
                'civitai_tags': ['abstract', 'geometric', 'patterns', 'digital art'],
                'lexica_prompts': ['abstract wallpaper', 'geometric patterns', 'digital abstract art', 'minimalist abstract'],
                'arthub_categories': ['abstract', 'digital-art'],
                'reddit_subreddits': ['StableDiffusion', 'midjourney']
            },
            'cyberpunk': {
                'civitai_tags': ['cyberpunk', 'neon', 'futuristic', 'sci-fi'],
                'lexica_prompts': ['cyberpunk city', 'neon cyberpunk', 'futuristic cityscape', 'sci-fi wallpaper'],
                'arthub_categories': ['cyberpunk', 'sci-fi'],
                'reddit_subreddits': ['cyberpunk', 'StableDiffusion']
            },
            'nature': {
                'civitai_tags': ['landscape', 'nature', 'forest', 'mountains'],
                'lexica_prompts': ['AI landscape', 'fantasy nature', 'digital forest', 'mountain wallpaper'],
                'arthub_categories': ['landscape', 'nature'],
                'reddit_subreddits': ['EarthPorn', 'StableDiffusion']
            },
            'space': {
                'civitai_tags': ['space', 'cosmic', 'galaxy', 'nebula'],
                'lexica_prompts': ['space wallpaper', 'cosmic landscape', 'galaxy art', 'nebula digital art'],
                'arthub_categories': ['space', 'sci-fi'],
                'reddit_subreddits': ['spaceporn', 'StableDiffusion']
            },
            'anime': {
                'civitai_tags': ['anime', 'manga', 'illustration'],
                'lexica_prompts': ['anime wallpaper', 'anime landscape', 'manga art', 'anime style'],
                'arthub_categories': ['anime', 'illustration'],
                'reddit_subreddits': ['anime', 'AnimeART']
            },
            'minimal': {
                'civitai_tags': ['minimal', 'clean', 'simple', 'geometric'],
                'lexica_prompts': ['minimal wallpaper', 'clean design', 'simple geometric', 'minimalist art'],
                'arthub_categories': ['minimal', 'geometric'],
                'reddit_subreddits': ['minimalism', 'StableDiffusion']
            },
            'art': {
                'civitai_tags': ['digital art', 'artwork', 'painting', 'illustration'],
                'lexica_prompts': ['digital artwork', 'AI painting', 'digital illustration', 'artistic wallpaper'],
                'arthub_categories': ['digital-art', 'painting'],
                'reddit_subreddits': ['DigitalArt', 'Art']
            },
            'dark': {
                'civitai_tags': ['dark', 'gothic', 'moody', 'black'],
                'lexica_prompts': ['dark wallpaper', 'gothic art', 'moody atmosphere', 'dark aesthetic'],
                'arthub_categories': ['dark', 'gothic'],
                'reddit_subreddits': ['DarkArt', 'StableDiffusion']
            },
            'ai': {
                'civitai_tags': ['digital art', 'ai generated', 'concept art', 'illustration'],
                'lexica_prompts': ['ai generated wallpaper', 'digital art wallpaper', 'ai artwork wallpaper', 'generative art'],
                'arthub_categories': ['digital-art', 'ai-art'],
                'reddit_subreddits': ['StableDiffusion', 'midjourney', 'artificial', 'deepdream']
            }
        }
    
    def scrape_civitai(self, category, count=20):
        """Scrape AI wallpapers from Civitai API"""
        print(f"🔍 Searching Civitai for {category} wallpapers...")
        
        if category not in self.ai_category_configs:
            print(f"❌ No Civitai configuration for category: {category}")
            return []
        
        config = self.ai_category_configs[category]
        images = []
        
        try:
            # Use Civitai API
            params = {
                'limit': min(count * 2, 100),  # Get extra for filtering
                'sort': 'Most Reactions',
                'period': 'Week',
                'nsfw': 'false',
                'tags': ','.join(config['civitai_tags'][:3])  # Limit tags
            }
            
            response = self.session.get(self.ai_sources['civitai']['api_url'], params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('items', [])[:count]:
                if item.get('url') and item.get('width', 0) >= 800:
                    # Extract metadata
                    meta = item.get('meta', {})
                    prompt = meta.get('prompt', '') if meta else ''
                    
                    images.append({
                        'url': item['url'],
                        'width': item.get('width', 0),
                        'height': item.get('height', 0),
                        'prompt': prompt[:100] if prompt else '',  # Truncate long prompts
                        'stats': item.get('stats', {}),
                        'source': 'civitai',
                        'id': hashlib.md5(item['url'].encode()).hexdigest()[:8],
                        'nsfw': item.get('nsfw', False)
                    })
            
            print(f"✅ Found {len(images)} images from Civitai")
            return images
            
        except Exception as e:
            print(f"❌ Civitai scraping error: {e}")
            return []
    
    def scrape_lexica(self, category, count=20):
        """Scrape AI wallpapers from Lexica search engine"""
        print(f"🔍 Searching Lexica for {category} wallpapers...")
        
        if category not in self.ai_category_configs:
            print(f"❌ No Lexica configuration for category: {category}")
            return []
        
        config = self.ai_category_configs[category]
        images = []
        
        try:
            # Search with different prompts
            for prompt in config['lexica_prompts'][:2]:  # Limit to 2 prompts
                params = {
                    'q': f"{prompt} wallpaper 4k",
                    'searchMode': 'images',
                    'model': 'lexica-aperture-v2'
                }
                
                response = self.session.get(self.ai_sources['lexica']['api_url'], params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for item in data.get('images', [])[:count//2]:
                    if item.get('src') and item.get('width', 0) >= 800:
                        images.append({
                            'url': item['src'],
                            'width': item.get('width', 0),
                            'height': item.get('height', 0),
                            'prompt': item.get('prompt', '')[:100],
                            'model': item.get('model', 'stable-diffusion'),
                            'source': 'lexica',
                            'id': hashlib.md5(item['src'].encode()).hexdigest()[:8],
                            'nsfw': False  # Lexica is generally safe
                        })
                
                time.sleep(self.ai_sources['lexica']['rate_limit'])
            
            print(f"✅ Found {len(images)} images from Lexica")
            return images
            
        except Exception as e:
            print(f"❌ Lexica scraping error: {e}")
            return []
    
    def scrape_arthub(self, category, count=20):
        """Scrape AI wallpapers from Arthub.ai"""
        print(f"🔍 Searching Arthub for {category} wallpapers...")
        
        if category not in self.ai_category_configs:
            print(f"❌ No Arthub configuration for category: {category}")
            return []
        
        config = self.ai_category_configs[category]
        images = []
        
        try:
            for art_category in config['arthub_categories'][:2]:
                url = f"{self.ai_sources['arthub']['base_url']}/artworks"
                params = {
                    'category': art_category,
                    'sort': 'popular',
                    'page': 1
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find artwork containers (adjust selectors based on actual HTML)
                artwork_items = soup.find_all('div', class_='artwork-item')[:count//2]
                
                for item in artwork_items:
                    img_tag = item.find('img')
                    if img_tag and img_tag.get('src'):
                        img_url = urljoin(url, img_tag['src'])
                        
                        # Try to get higher resolution version
                        if 'thumb' in img_url:
                            img_url = img_url.replace('thumb', 'large')
                        
                        title = img_tag.get('alt', '') or item.get('title', '')
                        
                        images.append({
                            'url': img_url,
                            'title': title[:100],
                            'source': 'arthub',
                            'id': hashlib.md5(img_url.encode()).hexdigest()[:8],
                            'category': art_category
                        })
                
                time.sleep(self.ai_sources['arthub']['rate_limit'])
            
            print(f"✅ Found {len(images)} images from Arthub")
            return images
            
        except Exception as e:
            print(f"❌ Arthub scraping error: {e}")
            return []
    
    def scrape_reddit_ai(self, category, count=20):
        """Scrape AI wallpapers from relevant Reddit communities"""
        print(f"🔍 Searching Reddit AI communities for {category}...")
        
        if category not in self.ai_category_configs:
            return []
        
        config = self.ai_category_configs[category]
        images = []
        
        try:
            for subreddit in config['reddit_subreddits'][:2]:
                # Use Reddit JSON API (no auth required for public posts)
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                params = {'limit': 25}
                
                headers = {'User-Agent': 'AI Wallpaper Scraper 1.0'}
                response = self.session.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    
                    # Look for image posts
                    if post_data.get('post_hint') == 'image' and post_data.get('url'):
                        url_str = post_data['url']
                        
                        # Filter for image URLs
                        if any(ext in url_str.lower() for ext in ['.jpg', '.jpeg', '.png']):
                            images.append({
                                'url': url_str,
                                'title': post_data.get('title', '')[:100],
                                'score': post_data.get('score', 0),
                                'subreddit': subreddit,
                                'source': 'reddit',
                                'id': hashlib.md5(url_str.encode()).hexdigest()[:8]
                            })
                
                time.sleep(2)  # Be nice to Reddit
                
                if len(images) >= count:
                    break
            
            print(f"✅ Found {len(images)} images from Reddit")
            return images[:count]
            
        except Exception as e:
            print(f"❌ Reddit scraping error: {e}")
            return []
    
    def download_image(self, image_info, filename):
        """Download and validate an AI-generated image"""
        try:
            filepath = self.download_dir / filename
            
            # Add proper headers for different sources
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': self.get_referer(image_info['source'])
            }
            
            response = self.session.get(image_info['url'], headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"❌ Not an image: {content_type}")
                return None
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify it's a valid image
            try:
                from PIL import Image
                with Image.open(filepath) as img:
                    if img.width < 800 or img.height < 600:
                        print(f"❌ Image too small: {img.width}x{img.height}")
                        os.remove(filepath)
                        return None
                    
                    # Check file size
                    file_size = filepath.stat().st_size
                    if file_size < 50000:  # 50KB minimum
                        print(f"❌ File too small: {file_size} bytes")
                        os.remove(filepath)
                        return None
                    
            except Exception as e:
                print(f"❌ Invalid image: {e}")
                if filepath.exists():
                    os.remove(filepath)
                return None
            
            return filepath
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def get_referer(self, source):
        """Get appropriate referer for different sources"""
        referers = {
            'civitai': 'https://civitai.com/',
            'lexica': 'https://lexica.art/',
            'arthub': 'https://arthub.ai/',
            'reddit': 'https://reddit.com/'
        }
        return referers.get(source, 'https://google.com/')
    
    def scrape_ai_category(self, category, needed_count):
        """Scrape AI-generated images for a specific category"""
        if category not in self.ai_category_configs:
            print(f"❌ No AI configuration for category: {category}")
            return 0
        
        print(f"\n🎯 Scraping {needed_count} AI wallpapers for category: {category}")
        
        all_images = []
        
        # Scrape from different AI sources
        sources_to_try = [
            ('civitai', self.scrape_civitai),
            ('lexica', self.scrape_lexica),
            ('arthub', self.scrape_arthub),
            ('reddit', self.scrape_reddit_ai)
        ]
        
        images_per_source = max(needed_count // len(sources_to_try), 10)
        
        for source_name, scrape_func in sources_to_try:
            if len(all_images) >= needed_count * 2:  # Get extra for filtering
                break
            
            try:
                images = scrape_func(category, images_per_source)
                all_images.extend(images)
                time.sleep(2)  # Rate limiting between sources
            except Exception as e:
                print(f"❌ Error scraping {source_name}: {e}")
                continue
        
        # Remove duplicates based on URL
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        print(f"📋 Found {len(unique_images)} unique AI images")
        
        # Download and add images
        added_count = 0
        for i, image_info in enumerate(unique_images):
            if added_count >= needed_count:
                break
            
            print(f"⬇️  Processing AI image {i+1}/{len(unique_images)} (added: {added_count}/{needed_count})")
            
            # Create filename
            source = image_info.get('source', 'ai')
            image_id = image_info.get('id', hashlib.md5(image_info['url'].encode()).hexdigest()[:8])
            filename = f"{category}_ai_{source}_{image_id}.jpg"
            filepath = self.download_image(image_info, filename)
            
            if filepath:
                try:
                    # Create enhanced title and tags
                    title = self.create_ai_title(category, image_info)
                    tags = self.create_ai_tags(category, image_info)
                    
                    # Get next ID
                    next_id = self.manager.get_next_id(category)
                    
                    # Set up paths
                    output_path = self.manager.wallpapers_dir / category / f"{next_id}.jpg"
                    thumb_path = self.manager.thumbnails_dir / category / f"{next_id}.jpg"
                    
                    # Ensure directories exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    thumb_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Process main image
                    processed_info = self.manager.process_image(filepath, output_path)
                    
                    # Generate thumbnail
                    self.manager.generate_thumbnail(output_path, thumb_path)
                    
                    # Extract metadata
                    metadata = self.manager.extract_metadata(output_path, processed_info)
                    metadata.update(self.create_ai_metadata(image_info))
                    
                    # Save metadata
                    self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                    (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                    
                    self.manager.save_metadata(category, next_id, title, tags, metadata)
                    
                    added_count += 1
                    print(f"✅ Added AI wallpaper {category}_{next_id} ({added_count}/{needed_count})")
                    
                except Exception as e:
                    print(f"❌ Failed to add AI image: {e}")
                finally:
                    # Clean up
                    if filepath.exists():
                        os.remove(filepath)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"🎉 Successfully added {added_count} AI wallpapers to {category}")
        return added_count
    
    def create_ai_title(self, category, image_info):
        """Create an appropriate title for AI wallpaper"""
        source = image_info.get('source', 'AI')
        
        if image_info.get('title'):
            return f"{image_info['title'][:30]} - {source.title()} AI"
        elif image_info.get('prompt'):
            # Clean up prompt
            prompt = image_info['prompt'][:40].strip()
            return f"{prompt} - {source.title()} AI"
        else:
            return f"{category.title()} AI Wallpaper - {source.title()}"
    
    def create_ai_tags(self, category, image_info):
        """Create appropriate tags for AI wallpaper"""
        base_tags = [category, 'ai-generated', 'hd', 'mobile']
        
        source = image_info.get('source', 'ai')
        if source == 'civitai':
            base_tags.append('stable-diffusion')
        elif source == 'lexica':
            base_tags.append('stable-diffusion')
        elif source == 'arthub':
            base_tags.append('ai-art')
        elif source == 'reddit':
            base_tags.append('community')
        
        # Add model info if available
        if image_info.get('model'):
            base_tags.append(image_info['model'].lower().replace(' ', '-'))
        
        return base_tags
    
    def create_ai_metadata(self, image_info):
        """Create enhanced metadata for AI wallpaper"""
        metadata = {
            'ai_source': image_info.get('source', 'unknown'),
            'ai_generated': True
        }
        
        # Add source-specific metadata
        if image_info.get('prompt'):
            metadata['ai_prompt'] = image_info['prompt'][:200]
        
        if image_info.get('model'):
            metadata['ai_model'] = image_info['model']
        
        if image_info.get('stats'):
            metadata['source_stats'] = image_info['stats']
        
        if image_info.get('score'):
            metadata['community_score'] = image_info['score']
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Scrape AI-generated wallpapers')
    parser.add_argument('--category', help='Specific category to scrape')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    parser.add_argument('--source', choices=['civitai', 'lexica', 'arthub', 'reddit'], help='Specific source to scrape from')
    
    args = parser.parse_args()
    
    # Install required packages
    try:
        from bs4 import BeautifulSoup
        from PIL import Image
    except ImportError:
        print("❌ Missing required packages. Installing...")
        os.system("pip install beautifulsoup4 pillow requests")
        print("✅ Packages installed. Please run the script again.")
        sys.exit(1)
    
    scraper = AIWallpaperScraper()
    
    if args.category:
        scraper.scrape_ai_category(args.category, args.count)
    else:
        print("❌ Please specify --category")
        sys.exit(1)

if __name__ == '__main__':
    main()