#!/usr/bin/env python3
"""
Fix URLs in wallpaper metadata files
Replace incorrect Unsplash URLs with correct GitHub raw URLs
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class URLFixer:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.wallpapers_dir = self.base_dir / 'wallpapers'
        
        # GitHub repository configuration
        self.github_config = {
            'owner': 'ddh4r4m',
            'repo': 'wallpaper-collection', 
            'branch': 'main'
        }
        
        self.base_url = f"https://raw.githubusercontent.com/{self.github_config['owner']}/{self.github_config['repo']}/{self.github_config['branch']}"
        
        self.fixed_count = 0
        self.total_count = 0
    
    def fix_wallpaper_metadata(self, metadata_path: Path) -> bool:
        """Fix URLs in a single metadata file"""
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.total_count += 1
            changed = False
            
            category = metadata.get('category')
            filename = metadata.get('filename')
            
            if not category or not filename:
                logger.warning(f"Missing category or filename in {metadata_path}")
                return False
            
            # Fix download_url
            correct_download_url = f"{self.base_url}/wallpapers/{category}/{filename}"
            if metadata.get('download_url') != correct_download_url:
                metadata['download_url'] = correct_download_url
                changed = True
                logger.debug(f"Fixed download_url for {filename}")
            
            # Fix thumbnail_url
            correct_thumbnail_url = f"{self.base_url}/thumbnails/{category}/{filename}"
            if metadata.get('thumbnail_url') != correct_thumbnail_url:
                metadata['thumbnail_url'] = correct_thumbnail_url
                changed = True
                logger.debug(f"Fixed thumbnail_url for {filename}")
            
            # Save if changed
            if changed:
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                self.fixed_count += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to fix URLs for {metadata_path}: {e}")
            return False
    
    def fix_category_urls(self, category: str) -> int:
        """Fix all URLs in a category"""
        category_dir = self.wallpapers_dir / category
        
        if not category_dir.exists():
            logger.warning(f"Category directory does not exist: {category_dir}")
            return 0
        
        fixed_in_category = 0
        
        for metadata_file in category_dir.glob('*.json'):
            if self.fix_wallpaper_metadata(metadata_file):
                fixed_in_category += 1
        
        logger.info(f"Fixed {fixed_in_category} files in {category} category")
        return fixed_in_category
    
    def fix_all_urls(self):
        """Fix URLs in all categories"""
        logger.info("Starting URL fixing process...")
        
        categories = [
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk',
            'gaming', 'anime', 'movies', 'music', 'cars', 'sports',
            'technology', 'architecture', 'art', 'dark', 'neon',
            'pastel', 'vintage', 'gradient', 'seasonal'
        ]
        
        for category in categories:
            self.fix_category_urls(category)
        
        logger.info(f"URL fixing complete! Fixed {self.fixed_count} out of {self.total_count} metadata files")
        
        return self.fixed_count

def main():
    print("🔧 URL Fixer for WallCraft Collection")
    print("=" * 50)
    
    fixer = URLFixer()
    fixed_count = fixer.fix_all_urls()
    
    print(f"\n✅ Fixed {fixed_count} metadata files with incorrect URLs")
    print("All download_url and thumbnail_url fields now point to GitHub raw URLs")
    
    if fixed_count > 0:
        print("\nNext steps:")
        print("1. Regenerate collection index: python3 scripts/generate_index.py --update-all")
        print("2. Commit the fixed metadata files")

if __name__ == "__main__":
    main()