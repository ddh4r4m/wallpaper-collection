#!/usr/bin/env python3
"""
Advanced AI Wallpaper Scraper with Enhanced Sources
Usage: ./tools/scrape_ai_advanced.py --category abstract --count 50 [options]

Features:
- Civitai API with quality scoring
- Lexica search with advanced filtering  
- Hugging Face Spaces integration
- Reddit AI communities with OAuth
- Quality-based ranking and selection
- Concurrent downloads for speed
"""

import os
import sys
import json
import argparse
import requests
import time
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import hashlib
from urllib.parse import urlparse, urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import our configuration
from ai_sources_config import (
    get_source_config, get_category_config, get_api_headers,
    calculate_quality_score, SOURCE_RELIABILITY, RATE_LIMITING,
    IMAGE_PROCESSING, API_KEYS
)
from add_wallpaper import WallpaperManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedAIWallpaperScraper:
    def __init__(self):
        self.manager = WallpaperManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI Wallpaper Scraper 2.0 (Educational/Research)'
        })
        
        self.download_dir = Path("/tmp/ai_wallpaper_downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # Quality threshold for auto-acceptance
        self.quality_threshold = 75
        
        # Initialize Reddit OAuth if credentials are available
        self.reddit_token = None
        if API_KEYS['reddit_client_id']:
            self.authenticate_reddit()
    
    def authenticate_reddit(self):
        """Authenticate with Reddit API for higher rate limits"""
        try:
            auth = requests.auth.HTTPBasicAuth(
                API_KEYS['reddit_client_id'], 
                API_KEYS['reddit_client_secret']
            )
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            headers = {'User-Agent': 'AI Wallpaper Scraper 2.0'}
            
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth, data=data, headers=headers
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.reddit_token = token_data['access_token']
                logger.info("✅ Reddit authentication successful")
            else:
                logger.warning("❌ Reddit authentication failed")
                
        except Exception as e:
            logger.warning(f"❌ Reddit authentication error: {e}")
    
    def scrape_civitai_advanced(self, category, count=20):
        """Advanced Civitai scraping with quality scoring"""
        logger.info(f"🔍 Advanced Civitai search for {category}...")
        
        category_config = get_category_config(category)
        if not category_config:
            return []
        
        source_config = get_source_config('civitai')
        headers = get_api_headers('civitai')
        
        images = []
        
        try:
            # Use category-specific tags
            tags = category_config.get('civitai_tags', [])
            
            for tag_set in [tags[:2], tags[2:4]]:  # Split into batches
                if not tag_set:
                    continue
                    
                params = {
                    'limit': min(count, source_config.get('max_per_request', 100)),
                    'sort': 'Most Reactions',
                    'period': 'Week',
                    'nsfw': 'false',
                    'tags': ','.join(tag_set)
                }
                
                response = self.session.get(
                    source_config['api_url'], 
                    params=params, 
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                for item in data.get('items', []):
                    if len(images) >= count * 2:  # Get extra for quality filtering
                        break
                    
                    # Quality filtering
                    if not self.meets_civitai_quality_standards(item, source_config):
                        continue
                    
                    # Calculate quality score
                    quality_score = calculate_quality_score('civitai', item)
                    
                    # Enhanced metadata extraction
                    meta = item.get('meta', {})
                    prompt = meta.get('prompt', '') if meta else ''
                    
                    image_data = {
                        'url': item['url'],
                        'width': item.get('width', 0),
                        'height': item.get('height', 0),
                        'prompt': prompt[:200],  # Longer prompts
                        'stats': item.get('stats', {}),
                        'quality_score': quality_score,
                        'model_name': meta.get('Model', 'unknown') if meta else 'unknown',
                        'steps': meta.get('Steps', 0) if meta else 0,
                        'cfg_scale': meta.get('CFG scale', 0) if meta else 0,
                        'source': 'civitai',
                        'id': hashlib.md5(item['url'].encode()).hexdigest()[:8],
                        'nsfw': item.get('nsfw', False)
                    }
                    
                    images.append(image_data)
                
                # Rate limiting
                time.sleep(source_config.get('rate_limit', 2))
            
            # Sort by quality score
            images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            logger.info(f"✅ Found {len(images)} quality images from Civitai")
            return images[:count]
            
        except Exception as e:
            logger.error(f"❌ Civitai scraping error: {e}")
            return []
    
    def meets_civitai_quality_standards(self, item, config):
        """Check if Civitai item meets quality standards"""
        quality_filters = config.get('quality_filters', {})
        
        # Check dimensions
        if item.get('width', 0) < quality_filters.get('min_width', 1024):
            return False
        if item.get('height', 0) < quality_filters.get('min_height', 1024):
            return False
        
        # Check reactions
        stats = item.get('stats', {})
        if stats.get('reactionCount', 0) < quality_filters.get('min_reactions', 5):
            return False
        
        # Check for blocked content
        meta = item.get('meta', {})
        if meta:
            prompt = meta.get('prompt', '').lower()
            blocked_terms = quality_filters.get('blocked_tags', [])
            if any(term in prompt for term in blocked_terms):
                return False
        
        return True
    
    def scrape_lexica_advanced(self, category, count=20):
        """Advanced Lexica scraping with enhanced search"""
        logger.info(f"🔍 Advanced Lexica search for {category}...")
        
        category_config = get_category_config(category)
        if not category_config:
            return []
        
        source_config = get_source_config('lexica')
        images = []
        
        try:
            prompts = category_config.get('lexica_prompts', [])
            quality_keywords = category_config.get('quality_keywords', [])
            style_modifiers = category_config.get('style_modifiers', [])
            
            for prompt in prompts:
                # Enhance prompt with quality keywords and style modifiers
                enhanced_prompt = f"{prompt}"
                if quality_keywords:
                    enhanced_prompt += f" {' '.join(quality_keywords[:2])}"
                if style_modifiers:
                    enhanced_prompt += f" {style_modifiers[0]}"
                
                params = {
                    'q': enhanced_prompt,
                    'searchMode': 'images',
                    'model': 'lexica-aperture-v2'
                }
                
                response = self.session.get(source_config['api_url'], params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for item in data.get('images', []):
                    if len(images) >= count * 1.5:
                        break
                    
                    # Quality filtering
                    if not self.meets_lexica_quality_standards(item, source_config):
                        continue
                    
                    # Calculate quality score based on prompt and model
                    quality_score = self.calculate_lexica_quality_score(item, enhanced_prompt)
                    
                    image_data = {
                        'url': item['src'],
                        'width': item.get('width', 0),
                        'height': item.get('height', 0),
                        'prompt': item.get('prompt', '')[:200],
                        'model': item.get('model', 'stable-diffusion'),
                        'quality_score': quality_score,
                        'guidance': item.get('guidance', 0),
                        'seed': item.get('seed', 0),
                        'source': 'lexica',
                        'id': hashlib.md5(item['src'].encode()).hexdigest()[:8]
                    }
                    
                    images.append(image_data)
                
                time.sleep(source_config.get('rate_limit', 1))
            
            # Sort by quality score
            images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            logger.info(f"✅ Found {len(images)} quality images from Lexica")
            return images[:count]
            
        except Exception as e:
            logger.error(f"❌ Lexica scraping error: {e}")
            return []
    
    def meets_lexica_quality_standards(self, item, config):
        """Check if Lexica item meets quality standards"""
        quality_filters = config.get('quality_filters', {})
        
        if item.get('width', 0) < quality_filters.get('min_width', 768):
            return False
        if item.get('height', 0) < quality_filters.get('min_height', 768):
            return False
        
        return True
    
    def calculate_lexica_quality_score(self, item, search_prompt):
        """Calculate quality score for Lexica items"""
        score = 50  # Base score
        
        # Resolution bonus
        width = item.get('width', 0)
        height = item.get('height', 0)
        resolution_factor = (width * height) / (1024 * 1024)
        score += min(resolution_factor * 20, 30)
        
        # Model bonus
        model = item.get('model', '').lower()
        if 'aperture' in model:
            score += 15
        elif 'stable-diffusion' in model:
            score += 10
        
        # Prompt relevance (simple keyword matching)
        item_prompt = item.get('prompt', '').lower()
        search_words = search_prompt.lower().split()
        matches = sum(1 for word in search_words if word in item_prompt)
        score += (matches / len(search_words)) * 20
        
        return min(score, 100)
    
    def scrape_reddit_advanced(self, category, count=20):
        """Advanced Reddit scraping with authentication"""
        logger.info(f"🔍 Advanced Reddit search for {category}...")
        
        category_config = get_category_config(category)
        if not category_config:
            return []
        
        subreddits = category_config.get('reddit_subreddits', [])
        images = []
        
        try:
            headers = {'User-Agent': 'AI Wallpaper Scraper 2.0'}
            if self.reddit_token:
                headers['Authorization'] = f'Bearer {self.reddit_token}'
                base_url = 'https://oauth.reddit.com'
            else:
                base_url = 'https://www.reddit.com'
            
            for subreddit in subreddits:
                params = {
                    'limit': 50,
                    'sort': 'hot',
                    't': 'week'
                }
                
                url = f"{base_url}/r/{subreddit}/hot.json"
                response = self.session.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    
                    if not self.is_valid_reddit_image_post(post_data):
                        continue
                    
                    quality_score = self.calculate_reddit_quality_score(post_data)
                    
                    if quality_score < 30:  # Skip low quality posts
                        continue
                    
                    image_data = {
                        'url': post_data['url'],
                        'title': post_data.get('title', '')[:150],
                        'score': post_data.get('score', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'subreddit': subreddit,
                        'quality_score': quality_score,
                        'author': post_data.get('author', 'unknown'),
                        'created_utc': post_data.get('created_utc', 0),
                        'source': 'reddit',
                        'id': hashlib.md5(post_data['url'].encode()).hexdigest()[:8]
                    }
                    
                    images.append(image_data)
                
                time.sleep(2)  # Reddit rate limiting
                
                if len(images) >= count * 1.5:
                    break
            
            # Sort by quality score
            images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            logger.info(f"✅ Found {len(images)} quality images from Reddit")
            return images[:count]
            
        except Exception as e:
            logger.error(f"❌ Reddit scraping error: {e}")
            return []
    
    def is_valid_reddit_image_post(self, post_data):
        """Check if Reddit post is a valid image post"""
        if post_data.get('post_hint') != 'image':
            return False
        
        url = post_data.get('url', '')
        if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png']):
            return False
        
        # Check score threshold
        if post_data.get('score', 0) < 50:
            return False
        
        return True
    
    def calculate_reddit_quality_score(self, post_data):
        """Calculate quality score for Reddit posts"""
        score = 0
        
        # Score-based rating
        post_score = post_data.get('score', 0)
        score += min(post_score / 10, 40)  # Max 40 points for score
        
        # Comments indicate engagement
        comments = post_data.get('num_comments', 0)
        score += min(comments / 2, 20)  # Max 20 points for comments
        
        # Title quality (keywords)
        title = post_data.get('title', '').lower()
        quality_words = ['wallpaper', '4k', 'hd', 'high resolution', 'artwork']
        title_bonus = sum(5 for word in quality_words if word in title)
        score += min(title_bonus, 25)
        
        # Award bonus
        all_awardings = post_data.get('all_awardings', [])
        if all_awardings:
            score += min(len(all_awardings) * 3, 15)
        
        return min(score, 100)
    
    async def download_image_async(self, session, image_info, filename):
        """Asynchronously download an image"""
        try:
            filepath = self.download_dir / filename
            
            headers = {'Referer': self.get_referer(image_info['source'])}
            
            async with session.get(image_info['url'], headers=headers) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    
                    # Validate image
                    if self.validate_downloaded_image(filepath):
                        return filepath
                    else:
                        if filepath.exists():
                            os.remove(filepath)
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Async download failed: {e}")
            return None
    
    def validate_downloaded_image(self, filepath):
        """Validate downloaded image meets requirements"""
        try:
            from PIL import Image
            
            # Check file size
            file_size = filepath.stat().st_size
            min_size = IMAGE_PROCESSING.get('min_file_size', 100000)
            max_size = IMAGE_PROCESSING.get('max_file_size', 5000000)
            
            if file_size < min_size or file_size > max_size:
                return False
            
            # Check image properties
            with Image.open(filepath) as img:
                if img.width < 800 or img.height < 600:
                    return False
                
                if img.format not in IMAGE_PROCESSING.get('allowed_formats', ['JPEG', 'PNG']):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_referer(self, source):
        """Get appropriate referer for different sources"""
        referers = {
            'civitai': 'https://civitai.com/',
            'lexica': 'https://lexica.art/',
            'arthub': 'https://arthub.ai/',
            'reddit': 'https://reddit.com/',
            'huggingface': 'https://huggingface.co/'
        }
        return referers.get(source, 'https://google.com/')
    
    async def scrape_ai_category_advanced(self, category, needed_count):
        """Advanced AI scraping with concurrent processing"""
        logger.info(f"\n🎯 Advanced AI scraping: {needed_count} wallpapers for {category}")
        
        category_config = get_category_config(category)
        if not category_config:
            logger.error(f"❌ No configuration for category: {category}")
            return 0
        
        # Get images from primary sources
        all_images = []
        
        primary_sources = category_config.get('primary_sources', ['civitai', 'lexica'])
        fallback_sources = category_config.get('fallback_sources', ['reddit'])
        
        images_per_source = max(needed_count // len(primary_sources), 20)
        
        # Scrape from primary sources
        for source in primary_sources:
            try:
                if source == 'civitai':
                    images = self.scrape_civitai_advanced(category, images_per_source)
                elif source == 'lexica':
                    images = self.scrape_lexica_advanced(category, images_per_source)
                elif source == 'reddit':
                    images = self.scrape_reddit_advanced(category, images_per_source)
                else:
                    continue
                
                all_images.extend(images)
                logger.info(f"✅ {source}: {len(images)} images")
                
            except Exception as e:
                logger.error(f"❌ Error scraping {source}: {e}")
        
        # Use fallback sources if needed
        if len(all_images) < needed_count * 1.5:
            for source in fallback_sources:
                try:
                    if source == 'reddit':
                        images = self.scrape_reddit_advanced(category, images_per_source)
                        all_images.extend(images)
                except Exception as e:
                    logger.error(f"❌ Error scraping fallback {source}: {e}")
        
        # Remove duplicates and sort by quality
        unique_images = self.deduplicate_and_rank(all_images)
        logger.info(f"📋 {len(unique_images)} unique high-quality AI images found")
        
        # Download and process images concurrently
        return await self.process_images_concurrently(category, unique_images, needed_count)
    
    def deduplicate_and_rank(self, images):
        """Remove duplicates and rank by quality score"""
        # Remove duplicates by URL
        seen_urls = set()
        unique_images = []
        
        for img in images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        # Sort by quality score
        unique_images.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return unique_images
    
    async def process_images_concurrently(self, category, images, needed_count):
        """Process images with concurrent downloads"""
        added_count = 0
        
        # Limit concurrent downloads
        max_concurrent = RATE_LIMITING.get('concurrent_downloads', 3)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for i, image_info in enumerate(images[:needed_count * 2]):
                if added_count >= needed_count:
                    break
                
                # Create download task
                source = image_info.get('source', 'ai')
                image_id = image_info.get('id', hashlib.md5(image_info['url'].encode()).hexdigest()[:8])
                filename = f"{category}_ai_{source}_{image_id}.jpg"
                
                task = self.download_image_async(session, image_info, filename)
                tasks.append((task, image_info, filename))
                
                # Process in batches
                if len(tasks) >= max_concurrent:
                    added_count += await self.process_download_batch(category, tasks, needed_count - added_count)
                    tasks = []
            
            # Process remaining tasks
            if tasks:
                added_count += await self.process_download_batch(category, tasks, needed_count - added_count)
        
        logger.info(f"🎉 Successfully added {added_count} AI wallpapers to {category}")
        return added_count
    
    async def process_download_batch(self, category, tasks, remaining_needed):
        """Process a batch of download tasks"""
        added_count = 0
        
        # Execute downloads concurrently
        download_tasks = [task[0] for task in tasks]
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        # Process results
        for i, (result, image_info, filename) in enumerate(zip(results, [t[1] for t in tasks], [t[2] for t in tasks])):
            if added_count >= remaining_needed:
                break
            
            if isinstance(result, Exception) or result is None:
                continue
            
            filepath = result
            
            try:
                # Add to collection
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
                metadata.update(self.create_enhanced_ai_metadata(image_info))
                
                # Save metadata
                self.manager.metadata_dir.mkdir(parents=True, exist_ok=True)
                (self.manager.metadata_dir / category).mkdir(parents=True, exist_ok=True)
                
                self.manager.save_metadata(category, next_id, title, tags, metadata)
                
                added_count += 1
                quality_score = image_info.get('quality_score', 0)
                logger.info(f"✅ Added AI wallpaper {category}_{next_id} (quality: {quality_score:.1f})")
                
            except Exception as e:
                logger.error(f"❌ Failed to add AI image: {e}")
            finally:
                # Clean up
                if filepath.exists():
                    os.remove(filepath)
        
        return added_count
    
    def create_ai_title(self, category, image_info):
        """Create enhanced title for AI wallpaper"""
        source = image_info.get('source', 'AI').title()
        quality_score = image_info.get('quality_score', 0)
        
        if image_info.get('title'):
            base_title = image_info['title'][:40]
        elif image_info.get('prompt'):
            base_title = image_info['prompt'][:40].strip()
        else:
            base_title = f"{category.title()} AI Art"
        
        # Add quality indicator for high-quality images
        if quality_score > 80:
            return f"{base_title} - Premium {source} AI"
        elif quality_score > 60:
            return f"{base_title} - {source} AI"
        else:
            return f"{base_title} - {source}"
    
    def create_ai_tags(self, category, image_info):
        """Create comprehensive tags for AI wallpaper"""
        tags = [category, 'ai-generated', 'hd', 'mobile']
        
        source = image_info.get('source', 'ai')
        if source == 'civitai':
            tags.extend(['stable-diffusion', 'community-rated'])
        elif source == 'lexica':
            tags.extend(['stable-diffusion', 'searchable'])
        elif source == 'reddit':
            tags.extend(['community', 'social'])
        
        # Add model information
        model = image_info.get('model', '') or image_info.get('model_name', '')
        if model and model != 'unknown':
            clean_model = re.sub(r'[^a-zA-Z0-9-]', '-', model.lower())[:20]
            tags.append(clean_model)
        
        # Add quality indicator
        quality_score = image_info.get('quality_score', 0)
        if quality_score > 80:
            tags.append('premium-quality')
        elif quality_score > 60:
            tags.append('high-quality')
        
        return tags
    
    def create_enhanced_ai_metadata(self, image_info):
        """Create comprehensive metadata for AI wallpaper"""
        metadata = {
            'ai_source': image_info.get('source', 'unknown'),
            'ai_generated': True,
            'quality_score': image_info.get('quality_score', 0)
        }
        
        # Add source-specific metadata
        if image_info.get('prompt'):
            metadata['ai_prompt'] = image_info['prompt'][:300]
        
        if image_info.get('model') or image_info.get('model_name'):
            metadata['ai_model'] = image_info.get('model') or image_info.get('model_name')
        
        # Civitai-specific metadata
        if image_info.get('stats'):
            metadata['civitai_stats'] = image_info['stats']
        
        if image_info.get('steps'):
            metadata['ai_steps'] = image_info['steps']
        
        if image_info.get('cfg_scale'):
            metadata['ai_cfg_scale'] = image_info['cfg_scale']
        
        # Reddit-specific metadata
        if image_info.get('score'):
            metadata['reddit_score'] = image_info['score']
        
        if image_info.get('subreddit'):
            metadata['source_community'] = image_info['subreddit']
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Advanced AI wallpaper scraper')
    parser.add_argument('--category', required=True, help='Category to scrape')
    parser.add_argument('--count', type=int, default=50, help='Number of images to scrape')
    parser.add_argument('--quality-threshold', type=int, default=75, help='Minimum quality score')
    parser.add_argument('--sources', nargs='+', choices=['civitai', 'lexica', 'reddit', 'huggingface'], help='Specific sources to use')
    
    args = parser.parse_args()
    
    # Install required packages
    try:
        import aiohttp
        from PIL import Image
    except ImportError:
        logger.info("❌ Missing required packages. Installing...")
        os.system("pip install aiohttp pillow requests")
        logger.info("✅ Packages installed. Please run the script again.")
        sys.exit(1)
    
    scraper = AdvancedAIWallpaperScraper()
    scraper.quality_threshold = args.quality_threshold
    
    # Run the async scraper
    asyncio.run(scraper.scrape_ai_category_advanced(args.category, args.count))

if __name__ == '__main__':
    main()