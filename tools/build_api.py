#!/usr/bin/env python3
"""
Rebuild all API endpoints from current collection
Usage: ./tools/build_api.py [options]

This tool scans the collection and generates all API files:
- all.json - Complete wallpaper list
- categories.json - Category metadata
- {category}.json - Individual category endpoints
- stats.json - Collection statistics
- featured.json - Featured wallpapers
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image
import hashlib

class APIBuilder:
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.collection_root = self.repo_root / "collection"
        self.wallpapers_dir = self.collection_root / "wallpapers"
        self.thumbnails_dir = self.collection_root / "thumbnails"
        self.metadata_dir = self.collection_root / "metadata"
        self.api_dir = self.collection_root / "api" / "v1"
        
        # Ensure API directory exists
        self.api_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub raw URL base
        self.github_user = "ddh4r4m"
        self.github_repo = "wallpaper-collection"
        self.github_branch = "main"
        self.base_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/{self.github_branch}"
        
        # Valid categories
        self.valid_categories = {
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk', 'gaming', 
            'anime', 'movies', 'music', 'cars', 'sports', 'technology', 
            'architecture', 'art', 'dark', 'neon', 'pastel', 'vintage', 
            'gradient', 'seasonal', '4k'
        }
        
        # Category descriptions
        self.category_descriptions = {
            'abstract': 'Abstract patterns, geometric designs, and artistic visualizations',
            'nature': 'Landscapes, wildlife, forests, mountains, and natural scenes',
            'space': 'Galaxies, nebulae, planets, stars, and cosmic photography',
            'minimal': 'Clean, simple designs with minimalist aesthetics',
            'cyberpunk': 'Futuristic cityscapes, neon lights, and sci-fi themes',
            'gaming': 'Video game characters, scenes, and gaming-inspired artwork',
            'anime': 'Anime characters, manga art, and Japanese animation styles',
            'movies': 'Film posters, movie scenes, and cinematic artwork',
            'music': 'Musical instruments, concert photography, and audio visualizations',
            'cars': 'Automotive photography, sports cars, and vehicle designs',
            'sports': 'Athletic photography, sports action, and fitness themes',
            'technology': 'Gadgets, circuits, futuristic tech, and digital interfaces',
            'architecture': 'Buildings, bridges, modern structures, and urban photography',
            'art': 'Digital art, paintings, illustrations, and creative designs',
            'dark': 'Dark themes, gothic aesthetics, and mysterious atmospheres',
            'neon': 'Neon lighting, synthwave aesthetics, and electric themes',
            'pastel': 'Soft colors, gentle aesthetics, and dream-like themes',
            'vintage': 'Retro designs, nostalgic themes, and classic aesthetics',
            'gradient': 'Color transitions, smooth blends, and abstract flows',
            'seasonal': 'Holiday themes, seasonal changes, and weather phenomena',
            '4k': 'Ultra high-definition wallpapers optimized for 4K displays'
        }
    
    def build_urls(self, category, image_id):
        """Build URLs for image and thumbnail"""
        return {
            'raw': f"{self.base_url}/collection/wallpapers/{category}/{image_id}.jpg",
            'thumb': f"{self.base_url}/collection/thumbnails/{category}/{image_id}.jpg"
        }
    
    def get_image_info(self, image_path):
        """Get basic image information"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
        except:
            return None
    
    def scan_collection(self):
        """Scan entire collection and return all wallpapers"""
        wallpapers = []
        print("Scanning collection...")
        
        for category in sorted(self.valid_categories):
            category_dir = self.wallpapers_dir / category
            metadata_dir = self.metadata_dir / category
            
            if not category_dir.exists():
                print(f"  Skipping {category} (no directory)")
                continue
            
            category_count = 0
            
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
                        
                        # Ensure required fields
                        if 'id' not in data:
                            data['id'] = f"{category}_{image_id}"
                        if 'category' not in data:
                            data['category'] = category
                        
                        wallpapers.append(data)
                        category_count += 1
                    except Exception as e:
                        print(f"    Warning: Failed to load metadata for {category}_{image_id}: {e}")
                        continue
                else:
                    # Create minimal entry for images without metadata
                    image_info = self.get_image_info(image_file)
                    
                    wallpaper = {
                        'id': f"{category}_{image_id}",
                        'category': category,
                        'title': f"{category.title()} Wallpaper {image_id}",
                        'tags': [category],
                        'urls': self.build_urls(category, image_id),
                        'metadata': {
                            'added_at': datetime.fromtimestamp(image_file.stat().st_mtime).isoformat(),
                            'file_size': image_file.stat().st_size
                        }
                    }
                    
                    if image_info:
                        wallpaper['metadata']['dimensions'] = {
                            'width': image_info['width'],
                            'height': image_info['height']
                        }
                    
                    wallpapers.append(wallpaper)
                    category_count += 1
            
            if category_count > 0:
                print(f"  {category}: {category_count} wallpapers")
        
        print(f"Total: {len(wallpapers)} wallpapers")
        return wallpapers
    
    def build_all_apis(self):
        """Build all API endpoints"""
        print("Building APIs...")
        
        # Scan collection
        wallpapers = self.scan_collection()
        
        if not wallpapers:
            print("No wallpapers found. Make sure images are in collection/wallpapers/")
            return
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Build all.json
        print("  Building all.json...")
        all_data = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp,
                'total_count': len(wallpapers),
                'categories': len([c for c in self.valid_categories if any(w['category'] == c for w in wallpapers)])
            },
            'data': wallpapers
        }
        
        with open(self.api_dir / 'all.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        
        # Build categories.json
        print("  Building categories.json...")
        categories_data = {}
        for category in self.valid_categories:
            category_wallpapers = [w for w in wallpapers if w['category'] == category]
            if category_wallpapers:  # Only include categories with wallpapers
                categories_data[category] = {
                    'name': category.title(),
                    'count': len(category_wallpapers),
                    'description': self.category_descriptions.get(category, f"{category.title()} wallpapers")
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
        print("  Building category endpoints...")
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
        
        # Build featured.json (most recent 20 wallpapers)
        print("  Building featured.json...")
        featured_wallpapers = sorted(
            wallpapers, 
            key=lambda x: x.get('metadata', {}).get('added_at', '') if isinstance(x, dict) and 'metadata' in x else x.get('created_at', ''), 
            reverse=True
        )[:20]
        
        featured_data = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp,
                'total_count': len(featured_wallpapers)
            },
            'data': featured_wallpapers
        }
        
        with open(self.api_dir / 'featured.json', 'w') as f:
            json.dump(featured_data, f, indent=2)
        
        # Build stats.json
        print("  Building stats.json...")
        stats_data = {
            'meta': {
                'version': '1.0',
                'generated_at': timestamp
            },
            'data': {
                'total_wallpapers': len(wallpapers),
                'total_categories': len(categories_data),
                'categories': categories_data,
                'recent_additions': featured_wallpapers[:10],
                'popular_tags': self.get_popular_tags(wallpapers),
                'file_stats': self.get_file_stats(wallpapers)
            }
        }
        
        with open(self.api_dir / 'stats.json', 'w') as f:
            json.dump(stats_data, f, indent=2)
        
        print(f"✅ Generated APIs:")
        print(f"   - all.json: {len(wallpapers)} wallpapers")
        print(f"   - categories.json: {len(categories_data)} categories")
        print(f"   - {len(categories_data)} category endpoints")
        print(f"   - featured.json: {len(featured_wallpapers)} featured")
        print(f"   - stats.json: Complete statistics")
        
        # Display API URLs
        print(f"\n🔗 API URLs:")
        print(f"   All wallpapers: {self.base_url}/collection/api/v1/all.json")
        print(f"   Categories: {self.base_url}/collection/api/v1/categories.json")
        print(f"   Featured: {self.base_url}/collection/api/v1/featured.json")
        print(f"   Stats: {self.base_url}/collection/api/v1/stats.json")
        
        return {
            'total_wallpapers': len(wallpapers),
            'total_categories': len(categories_data),
            'apis_generated': 4 + len(categories_data)
        }
    
    def get_popular_tags(self, wallpapers):
        """Get most popular tags"""
        tag_counts = {}
        for wallpaper in wallpapers:
            tags = wallpaper.get('tags', [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Return top 20 tags
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    
    def get_file_stats(self, wallpapers):
        """Get file statistics"""
        total_size = 0
        dimensions = []
        
        for wallpaper in wallpapers:
            metadata = wallpaper.get('metadata', {})
            
            # File size
            file_size = metadata.get('file_size', 0)
            total_size += file_size
            
            # Dimensions
            dims = metadata.get('dimensions', {})
            if dims.get('width') and dims.get('height'):
                dimensions.append((dims['width'], dims['height']))
        
        # Calculate average dimensions
        avg_width = sum(d[0] for d in dimensions) / len(dimensions) if dimensions else 0
        avg_height = sum(d[1] for d in dimensions) / len(dimensions) if dimensions else 0
        
        return {
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'average_file_size_kb': round(total_size / len(wallpapers) / 1024, 2) if wallpapers else 0,
            'average_dimensions': {
                'width': round(avg_width),
                'height': round(avg_height)
            } if dimensions else None,
            'total_files': len(wallpapers)
        }

def main():
    parser = argparse.ArgumentParser(description='Build all API endpoints')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    builder = APIBuilder()
    
    try:
        result = builder.build_all_apis()
        
        print(f"\n🎉 Successfully built APIs:")
        print(f"   {result['total_wallpapers']} wallpapers")
        print(f"   {result['total_categories']} categories")
        print(f"   {result['apis_generated']} API files generated")
        
    except Exception as e:
        print(f"❌ Error building APIs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()