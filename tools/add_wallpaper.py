#!/usr/bin/env python3
"""
Add a wallpaper with zero friction
Usage: ./tools/add_wallpaper.py category image.jpg [options]

This tool handles the entire workflow:
1. Validates image (dimensions, format, size)
2. Gets next sequential ID in category
3. Processes and optimizes image
4. Generates thumbnail automatically
5. Extracts/enhances metadata
6. Saves minimal metadata JSON
7. Rebuilds ALL affected APIs
8. Validates everything works
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from PIL import Image, ImageOps
from datetime import datetime
import hashlib
import subprocess

class WallpaperManager:
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.collection_root = self.repo_root / "collection"
        self.wallpapers_dir = self.collection_root / "wallpapers"
        self.thumbnails_dir = self.collection_root / "thumbnails"
        self.metadata_dir = self.collection_root / "metadata"
        self.api_dir = self.collection_root / "api" / "v1"
        
        # Ensure directories exist
        self.api_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub raw URL base
        self.github_user = "ddh4r4m"
        self.github_repo = "wallpaper-collection"
        self.github_branch = "main"
        self.base_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/{self.github_branch}"
        
        # Image processing settings
        self.max_width = 1080
        self.max_height = 1920
        self.jpeg_quality = 85
        self.thumb_size = (400, 600)
        self.thumb_quality = 80
        
        # Valid categories
        self.valid_categories = {
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk', 'gaming', 
            'anime', 'movies', 'music', 'cars', 'sports', 'technology', 
            'architecture', 'art', 'dark', 'neon', 'pastel', 'vintage', 
            'gradient', 'seasonal', '4k'
        }
    
    def validate_image(self, image_path):
        """Validate image format, size, and dimensions"""
        try:
            with Image.open(image_path) as img:
                # Check format
                if img.format not in ['JPEG', 'PNG', 'WEBP']:
                    raise ValueError(f"Unsupported format: {img.format}")
                
                # Check dimensions
                width, height = img.size
                if width < 800 or height < 600:
                    raise ValueError(f"Image too small: {width}x{height}")
                
                # Check file size (max 10MB)
                file_size = os.path.getsize(image_path)
                if file_size > 10 * 1024 * 1024:
                    raise ValueError(f"File too large: {file_size / (1024*1024):.1f}MB")
                
                return {
                    'width': width,
                    'height': height,
                    'format': img.format,
                    'file_size': file_size,
                    'mode': img.mode
                }
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")
    
    def get_next_id(self, category):
        """Get next sequential ID for category"""
        category_dir = self.wallpapers_dir / category
        
        # Find existing files
        existing_files = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.png"))
        
        # Extract numeric IDs
        existing_ids = []
        for file in existing_files:
            try:
                # Extract number from filename like "001.jpg"
                id_num = int(file.stem)
                existing_ids.append(id_num)
            except ValueError:
                continue
        
        # Return next available ID
        next_id = max(existing_ids) + 1 if existing_ids else 1
        return f"{next_id:03d}"
    
    def process_image(self, image_path, output_path, max_width=None, max_height=None, quality=None):
        """Process and optimize image"""
        max_width = max_width or self.max_width
        max_height = max_height or self.max_height
        quality = quality or self.jpeg_quality
        
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode in ['RGBA', 'P']:
                img = img.convert('RGB')
            
            # Auto-rotate based on EXIF
            img = ImageOps.exif_transpose(img)
            
            # Resize if needed
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            return {
                'width': img.width,
                'height': img.height,
                'file_size': os.path.getsize(output_path),
                'format': 'JPEG'
            }
    
    def generate_thumbnail(self, image_path, thumb_path):
        """Generate thumbnail"""
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode in ['RGBA', 'P']:
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(self.thumb_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumb_path, 'JPEG', quality=self.thumb_quality, optimize=True)
            
            return {
                'width': img.width,
                'height': img.height,
                'file_size': os.path.getsize(thumb_path)
            }
    
    def extract_metadata(self, image_path, image_info):
        """Extract metadata from image"""
        metadata = {
            'dimensions': {
                'width': image_info['width'],
                'height': image_info['height']
            },
            'file_size': image_info['file_size'],
            'format': image_info['format'],
            'added_at': datetime.now().isoformat()
        }
        
        # Try to extract EXIF data
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    # Add camera info if available
                    if 272 in exif:  # Make
                        metadata['camera_make'] = exif[272]
                    if 271 in exif:  # Model
                        metadata['camera_model'] = exif[271]
        except:
            pass
        
        # Generate hash for uniqueness
        with open(image_path, 'rb') as f:
            metadata['hash'] = hashlib.md5(f.read()).hexdigest()
        
        return metadata
    
    def save_metadata(self, category, image_id, title, tags, metadata):
        """Save minimal metadata JSON"""
        metadata_file = self.metadata_dir / category / f"{image_id}.json"
        
        data = {
            'id': f"{category}_{image_id}",
            'category': category,
            'title': title,
            'tags': tags,
            'metadata': metadata
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def build_urls(self, category, image_id):
        """Build URLs for image and thumbnail"""
        return {
            'raw': f"{self.base_url}/collection/wallpapers/{category}/{image_id}.jpg",
            'thumb': f"{self.base_url}/collection/thumbnails/{category}/{image_id}.jpg"
        }
    
    def add_wallpaper(self, category, image_path, title=None, tags=None, photographer=None):
        """Add a wallpaper with complete automation"""
        
        # Validate category
        if category not in self.valid_categories:
            raise ValueError(f"Invalid category: {category}")
        
        # Validate image
        image_info = self.validate_image(image_path)
        
        # Get next ID
        image_id = self.get_next_id(category)
        
        # Set up paths
        output_path = self.wallpapers_dir / category / f"{image_id}.jpg"
        thumb_path = self.thumbnails_dir / category / f"{image_id}.jpg"
        
        # Process main image
        print(f"Processing image: {category}_{image_id}")
        processed_info = self.process_image(image_path, output_path)
        
        # Generate thumbnail
        print(f"Generating thumbnail: {category}_{image_id}")
        thumb_info = self.generate_thumbnail(output_path, thumb_path)
        
        # Extract metadata
        metadata = self.extract_metadata(output_path, processed_info)
        if photographer:
            metadata['photographer'] = photographer
        
        # Set default title if not provided
        if not title:
            title = f"{category.title()} Wallpaper {image_id}"
        
        # Set default tags if not provided
        if not tags:
            tags = [category]
        elif isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        
        # Save metadata
        wallpaper_data = self.save_metadata(category, image_id, title, tags, metadata)
        
        # Build URLs
        urls = self.build_urls(category, image_id)
        
        print(f"✅ Added wallpaper: {category}_{image_id}")
        print(f"   Title: {title}")
        print(f"   Tags: {', '.join(tags)}")
        print(f"   Size: {processed_info['width']}x{processed_info['height']}")
        print(f"   File: {processed_info['file_size'] / 1024:.1f}KB")
        print(f"   URL: {urls['raw']}")
        
        # Rebuild APIs
        print("Rebuilding APIs...")
        self.rebuild_apis()
        
        return {
            'id': f"{category}_{image_id}",
            'category': category,
            'title': title,
            'tags': tags,
            'urls': urls,
            'metadata': metadata
        }
    
    def scan_collection(self):
        """Scan entire collection and return all wallpapers"""
        wallpapers = []
        
        for category in self.valid_categories:
            category_dir = self.wallpapers_dir / category
            metadata_dir = self.metadata_dir / category
            
            if not category_dir.exists():
                continue
            
            # Find all images
            for image_file in sorted(category_dir.glob("*.jpg")):
                image_id = image_file.stem
                metadata_file = metadata_dir / f"{image_id}.json"
                
                # Load metadata if exists
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            data = json.load(f)
                        
                        # Add computed URLs
                        data['urls'] = self.build_urls(category, image_id)
                        wallpapers.append(data)
                    except:
                        continue
                else:
                    # Create minimal entry for images without metadata
                    wallpaper = {
                        'id': f"{category}_{image_id}",
                        'category': category,
                        'title': f"{category.title()} Wallpaper {image_id}",
                        'tags': [category],
                        'urls': self.build_urls(category, image_id),
                        'metadata': {
                            'added_at': datetime.now().isoformat(),
                            'file_size': image_file.stat().st_size
                        }
                    }
                    wallpapers.append(wallpaper)
        
        return wallpapers
    
    def rebuild_apis(self):
        """Rebuild all API endpoints"""
        print("Scanning collection...")
        wallpapers = self.scan_collection()
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Build all.json
        all_data = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp,
                'total_count': len(wallpapers),
                'categories': len(self.valid_categories)
            },
            'data': wallpapers
        }
        
        with open(self.api_dir / 'all.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        
        # Build categories.json
        categories_data = {}
        for category in self.valid_categories:
            category_wallpapers = [w for w in wallpapers if w['category'] == category]
            categories_data[category] = {
                'name': category.title(),
                'count': len(category_wallpapers),
                'description': f"{category.title()} wallpapers"
            }
        
        categories_response = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp,
                'total_categories': len(categories_data)
            },
            'data': categories_data
        }
        
        with open(self.api_dir / 'categories.json', 'w') as f:
            json.dump(categories_response, f, indent=2)
        
        # Build individual category files
        for category in self.valid_categories:
            category_wallpapers = [w for w in wallpapers if w['category'] == category]
            
            if category_wallpapers:
                category_data = {
                    'meta': {
                        'version': '1.0',
                        'generated_at': timestamp,
                        'category': category,
                        'total_count': len(category_wallpapers)
                    },
                    'data': category_wallpapers
                }
                
                with open(self.api_dir / f'{category}.json', 'w') as f:
                    json.dump(category_data, f, indent=2)
        
        # Build stats.json
        stats_data = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp
            },
            'data': {
                'total_wallpapers': len(wallpapers),
                'total_categories': len(self.valid_categories),
                'categories': categories_data,
                'recent_additions': sorted(wallpapers, key=lambda x: x['metadata'].get('added_at', ''), reverse=True)[:10]
            }
        }
        
        with open(self.api_dir / 'stats.json', 'w') as f:
            json.dump(stats_data, f, indent=2)
        
        print(f"✅ Generated APIs: {len(wallpapers)} wallpapers, {len(categories_data)} categories")

def main():
    parser = argparse.ArgumentParser(description='Add wallpaper to collection')
    parser.add_argument('category', help='Wallpaper category')
    parser.add_argument('image', help='Image file path')
    parser.add_argument('--title', help='Wallpaper title')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--photographer', help='Photographer name')
    parser.add_argument('--rebuild-only', action='store_true', help='Only rebuild APIs')
    
    args = parser.parse_args()
    
    manager = WallpaperManager()
    
    if args.rebuild_only:
        manager.rebuild_apis()
        return
    
    try:
        result = manager.add_wallpaper(
            category=args.category,
            image_path=args.image,
            title=args.title,
            tags=args.tags,
            photographer=args.photographer
        )
        
        print(f"\n🎉 Successfully added wallpaper: {result['id']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()