#!/usr/bin/env python3
"""
Generate master index and category indexes for wallpaper collection
Supports all 20+ categories with comprehensive metadata
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('generate_index.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IndexGenerator:
    """Generate comprehensive JSON indexes for wallpaper collection"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.wallpapers_dir = self.repo_path / "wallpapers"
        self.thumbnails_dir = self.repo_path / "thumbnails"
        self.categories_dir = self.repo_path / "categories"
        
        # Create directories if they don't exist
        self.categories_dir.mkdir(parents=True, exist_ok=True)
        
        # All supported categories
        self.categories = [
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk',
            'gaming', 'anime', 'movies', 'music', 'cars', 'sports',
            'technology', 'architecture', 'art', 'dark', 'neon',
            'pastel', 'vintage', 'gradient', 'seasonal'
        ]
        
        # Category descriptions
        self.category_descriptions = {
            'abstract': 'Abstract AI-generated patterns, geometric shapes, and mathematical visualizations',
            'nature': 'Natural landscapes, mountains, forests, oceans, wildlife, and botanical photography',
            'space': 'Galaxies, nebulae, planets, astronauts, cosmic scenes, and stellar photography',
            'minimal': 'Clean designs, simple patterns, monochromatic themes, and zen aesthetics',
            'cyberpunk': 'Neon cities, futuristic themes, sci-fi aesthetics, and digital dystopia',
            'gaming': 'Video game screenshots, concept art, characters, and gaming environments',
            'anime': 'Anime characters, Studio Ghibli art, manga illustrations, and Japanese animation',
            'movies': 'Film posters, movie scenes, cinematic art, and movie characters',
            'music': 'Album covers, music visualizations, instruments, and concert photography',
            'cars': 'Sports cars, classic cars, automotive photography, and racing scenes',
            'sports': 'Football, basketball, extreme sports, fitness, and athletic photography',
            'technology': 'Gadgets, circuits, futuristic tech, AI themes, and digital interfaces',
            'architecture': 'Buildings, bridges, modern/classic structures, and urban photography',
            'art': 'Digital art, paintings, illustrations, creative designs, and artistic photography',
            'dark': 'Dark themes, gothic aesthetics, mysterious atmospheres, and low-light photography',
            'neon': 'Neon lights, synthwave, retro-futuristic vibes, and electric aesthetics',
            'pastel': 'Soft colors, kawaii aesthetics, gentle themes, and dream-like imagery',
            'vintage': 'Retro designs, old-school aesthetics, nostalgic themes, and classic photography',
            'gradient': 'Color transitions, smooth blends, modern gradients, and abstract flows',
            'seasonal': 'Holiday themes, seasonal changes, celebrations, and weather phenomena'
        }
        
        # GitHub repository configuration
        self.github_config = {
            'owner': 'ddh4r4m',
            'repo': 'wallpaper-collection',
            'branch': 'main'
        }
        
        # Master index data
        self.master_index = {
            'version': '2.0.0',
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'totalWallpapers': 0,
            'categories': [],
            'featured': [],
            'statistics': {
                'totalCategories': len(self.categories),
                'averagePerCategory': 0,
                'totalFileSize': 0,
                'processingHistory': []
            }
        }
    
    def load_wallpaper_metadata(self, wallpaper_path: Path) -> Optional[Dict]:
        """Load metadata for a wallpaper image"""
        metadata_path = wallpaper_path.with_suffix('.json')
        
        if not metadata_path.exists():
            logger.warning(f"No metadata found for {wallpaper_path.name}")
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Validate required fields
            required_fields = ['id', 'category', 'filename', 'title', 'width', 'height']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required field '{field}' in metadata for {wallpaper_path.name}")
                    return None
            
            # Ensure download URLs are present
            if 'download_url' not in metadata:
                category = metadata['category']
                filename = metadata['filename']
                base_url = f"https://raw.githubusercontent.com/{self.github_config['owner']}/{self.github_config['repo']}/{self.github_config['branch']}"
                metadata['download_url'] = f"{base_url}/wallpapers/{category}/{filename}"
            
            if 'thumbnail_url' not in metadata:
                category = metadata['category']
                filename = metadata['filename']
                base_url = f"https://raw.githubusercontent.com/{self.github_config['owner']}/{self.github_config['repo']}/{self.github_config['branch']}"
                metadata['thumbnail_url'] = f"{base_url}/thumbnails/{category}/{filename}"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata for {wallpaper_path.name}: {e}")
            return None
    
    def scan_category_wallpapers(self, category: str) -> List[Dict]:
        """Scan all wallpapers in a category directory"""
        category_dir = self.wallpapers_dir / category
        
        if not category_dir.exists():
            logger.warning(f"Category directory does not exist: {category_dir}")
            return []
        
        wallpapers = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        
        for file_path in category_dir.iterdir():
            if file_path.suffix.lower() in image_extensions:
                metadata = self.load_wallpaper_metadata(file_path)
                if metadata:
                    # Add file system information
                    try:
                        file_stats = file_path.stat()
                        metadata['file_size'] = file_stats.st_size
                        metadata['file_modified'] = datetime.fromtimestamp(file_stats.st_mtime).isoformat() + 'Z'
                    except Exception as e:
                        logger.warning(f"Failed to get file stats for {file_path}: {e}")
                    
                    wallpapers.append(metadata)
        
        # Sort by ID for consistent ordering
        wallpapers.sort(key=lambda x: x.get('id', ''))
        
        logger.info(f"Found {len(wallpapers)} wallpapers in category: {category}")
        return wallpapers
    
    def generate_category_index(self, category: str) -> Dict:
        """Generate index for a specific category"""
        logger.info(f"Generating index for category: {category}")
        
        # Scan wallpapers
        wallpapers = self.scan_category_wallpapers(category)
        
        # Calculate statistics
        total_size = sum(w.get('file_size', 0) for w in wallpapers)
        avg_width = sum(w.get('width', 0) for w in wallpapers) / len(wallpapers) if wallpapers else 0
        avg_height = sum(w.get('height', 0) for w in wallpapers) / len(wallpapers) if wallpapers else 0
        
        # Count by source
        source_counts = {}
        for wallpaper in wallpapers:
            source = wallpaper.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Extract unique tags
        all_tags = set()
        for wallpaper in wallpapers:
            if 'tags' in wallpaper and isinstance(wallpaper['tags'], list):
                all_tags.update(wallpaper['tags'])
        
        # Create category index
        category_index = {
            'category': category,
            'name': category.title(),
            'description': self.category_descriptions.get(category, f'{category.title()} themed wallpapers'),
            'count': len(wallpapers),
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'statistics': {
                'totalFileSize': total_size,
                'averageWidth': int(avg_width),
                'averageHeight': int(avg_height),
                'sourceBreakdown': source_counts,
                'uniqueTags': sorted(list(all_tags))
            },
            'wallpapers': wallpapers
        }
        
        # Save category index
        category_file = self.categories_dir / f"{category}.json"
        with open(category_file, 'w') as f:
            json.dump(category_index, f, indent=2)
        
        logger.info(f"Generated category index: {category} ({len(wallpapers)} wallpapers)")
        return category_index
    
    def select_featured_wallpapers(self, all_wallpapers: List[Dict], count: int = 20) -> List[Dict]:
        """Select featured wallpapers from all categories"""
        if not all_wallpapers:
            return []
        
        # Sort by quality score if available, otherwise by recent processing
        featured_candidates = []
        
        for wallpaper in all_wallpapers:
            # Calculate feature score
            score = 0
            
            # Bonus for high resolution
            if wallpaper.get('width', 0) >= 1080 and wallpaper.get('height', 0) >= 1920:
                score += 2
            
            # Bonus for specific sources (known for quality)
            if wallpaper.get('source') in ['unsplash', 'pexels']:
                score += 1
            
            # Bonus for having photographer info
            if wallpaper.get('photographer'):
                score += 1
            
            # Bonus for having tags
            if wallpaper.get('tags') and len(wallpaper['tags']) > 3:
                score += 1
            
            # Bonus for recently processed
            if wallpaper.get('processed_at'):
                try:
                    processed_time = datetime.fromisoformat(wallpaper['processed_at'].replace('Z', '+00:00'))
                    days_ago = (datetime.utcnow() - processed_time.replace(tzinfo=None)).days
                    if days_ago < 7:  # Within last week
                        score += 1
                except:
                    pass
            
            featured_candidates.append({
                'wallpaper': wallpaper,
                'score': score
            })
        
        # Sort by score and select top wallpapers
        featured_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Select diverse featured wallpapers (max 2 per category)
        featured = []
        category_counts = {}
        
        for candidate in featured_candidates:
            if len(featured) >= count:
                break
            
            wallpaper = candidate['wallpaper']
            category = wallpaper.get('category', 'unknown')
            
            if category_counts.get(category, 0) < 2:
                featured.append(wallpaper)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return featured
    
    def generate_master_index(self) -> Dict:
        """Generate master index with all categories"""
        logger.info("Generating master index")
        
        all_wallpapers = []
        category_summaries = []
        total_file_size = 0
        
        # Process each category
        for category in self.categories:
            category_index = self.generate_category_index(category)
            
            # Add to master statistics
            wallpapers = category_index['wallpapers']
            all_wallpapers.extend(wallpapers)
            total_file_size += category_index['statistics']['totalFileSize']
            
            # Create category summary for master index
            category_summary = {
                'id': category,
                'name': category_index['name'],
                'count': category_index['count'],
                'description': category_index['description']
            }
            category_summaries.append(category_summary)
        
        # Select featured wallpapers
        featured_wallpapers = self.select_featured_wallpapers(all_wallpapers)
        
        # Calculate overall statistics
        total_wallpapers = len(all_wallpapers)
        avg_per_category = total_wallpapers / len(self.categories) if self.categories else 0
        
        # Update master index
        self.master_index.update({
            'totalWallpapers': total_wallpapers,
            'categories': category_summaries,
            'featured': featured_wallpapers,
            'statistics': {
                'totalCategories': len(self.categories),
                'averagePerCategory': round(avg_per_category, 1),
                'totalFileSize': total_file_size,
                'generatedAt': datetime.utcnow().isoformat() + 'Z'
            }
        })
        
        # Save master index
        master_file = self.repo_path / 'index.json'
        with open(master_file, 'w') as f:
            json.dump(self.master_index, f, indent=2)
        
        logger.info(f"Generated master index with {total_wallpapers} wallpapers across {len(self.categories)} categories")
        return self.master_index
    
    def validate_indexes(self) -> bool:
        """Validate generated indexes"""
        logger.info("Validating generated indexes")
        
        errors = []
        
        # Check master index
        master_file = self.repo_path / 'index.json'
        if not master_file.exists():
            errors.append("Master index file not found")
        else:
            try:
                with open(master_file, 'r') as f:
                    master_data = json.load(f)
                
                # Validate structure
                required_fields = ['version', 'lastUpdated', 'totalWallpapers', 'categories', 'featured']
                for field in required_fields:
                    if field not in master_data:
                        errors.append(f"Missing field '{field}' in master index")
                
            except Exception as e:
                errors.append(f"Invalid master index JSON: {e}")
        
        # Check category indexes
        for category in self.categories:
            category_file = self.categories_dir / f"{category}.json"
            if not category_file.exists():
                errors.append(f"Category index not found: {category}")
            else:
                try:
                    with open(category_file, 'r') as f:
                        category_data = json.load(f)
                    
                    # Validate structure
                    required_fields = ['category', 'name', 'count', 'wallpapers']
                    for field in required_fields:
                        if field not in category_data:
                            errors.append(f"Missing field '{field}' in category index: {category}")
                
                except Exception as e:
                    errors.append(f"Invalid category index JSON for {category}: {e}")
        
        if errors:
            logger.error("Validation errors found:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        else:
            logger.info("All indexes validated successfully")
            return True
    
    def generate_statistics_report(self) -> str:
        """Generate a comprehensive statistics report"""
        total_wallpapers = self.master_index.get('totalWallpapers', 0)
        total_categories = len(self.categories)
        
        report = f"""📊 Wallpaper Collection Statistics

🎯 Overview:
   Total wallpapers: {total_wallpapers:,}
   Total categories: {total_categories}
   Average per category: {total_wallpapers / total_categories:.1f}

📁 Categories:
"""
        
        for category_summary in self.master_index.get('categories', []):
            count = category_summary.get('count', 0)
            percentage = (count / total_wallpapers * 100) if total_wallpapers > 0 else 0
            report += f"   {category_summary['name']:12} : {count:4d} wallpapers ({percentage:5.1f}%)\n"
        
        report += f"""
🌟 Featured wallpapers: {len(self.master_index.get('featured', []))}

📈 File information:
   Total file size: {self.master_index['statistics']['totalFileSize'] / (1024*1024):.1f} MB
   Generated at: {self.master_index['statistics']['generatedAt']}

🔗 API endpoints:
   Master index: https://raw.githubusercontent.com/{self.github_config['owner']}/{self.github_config['repo']}/{self.github_config['branch']}/index.json
   Category index: https://raw.githubusercontent.com/{self.github_config['owner']}/{self.github_config['repo']}/{self.github_config['branch']}/categories/{{category}}.json
"""
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Generate wallpaper collection indexes')
    parser.add_argument('--category', help='Generate index for specific category only')
    parser.add_argument('--update-master', action='store_true', help='Update master index only')
    parser.add_argument('--update-all', action='store_true', help='Update all indexes')
    parser.add_argument('--validate', action='store_true', help='Validate existing indexes')
    parser.add_argument('--repo', default='.', help='Repository root path')
    parser.add_argument('--github-owner', help='GitHub repository owner')
    parser.add_argument('--github-repo', help='GitHub repository name')
    
    args = parser.parse_args()
    
    # Create generator
    generator = IndexGenerator(args.repo)
    
    # Update GitHub configuration if provided
    if args.github_owner:
        generator.github_config['owner'] = args.github_owner
    if args.github_repo:
        generator.github_config['repo'] = args.github_repo
    
    # Execute based on arguments
    if args.validate:
        # Validate existing indexes
        is_valid = generator.validate_indexes()
        sys.exit(0 if is_valid else 1)
    
    elif args.category:
        # Generate specific category index
        generator.generate_category_index(args.category)
        print(f"✅ Generated index for category: {args.category}")
    
    elif args.update_master:
        # Update master index only
        generator.generate_master_index()
        print("✅ Updated master index")
    
    elif args.update_all:
        # Update all indexes
        generator.generate_master_index()
        generator.validate_indexes()
        
        # Generate statistics report
        report = generator.generate_statistics_report()
        print(report)
        
        # Save report
        report_file = Path(args.repo) / 'collection_statistics.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\\n📄 Report saved to: {report_file}")
    
    else:
        # Default: generate master index
        generator.generate_master_index()
        print("✅ Generated master index")

if __name__ == "__main__":
    main()