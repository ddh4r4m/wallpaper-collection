#!/usr/bin/env python3
"""
Simple index generator for wallpaper collection
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleIndexGenerator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.wallpapers_dir = self.repo_path / "wallpapers"
        self.categories_dir = self.repo_path / "categories"
        self.github_owner = "ddh4r4m"
        self.github_repo = "wallpaper-collection"
        
    def generate_master_index(self):
        """Generate master index from category files"""
        logger.info("Generating master index")
        
        categories = []
        total_wallpapers = 0
        featured = []
        
        # Scan category files
        if self.categories_dir.exists():
            for category_file in self.categories_dir.glob("*.json"):
                try:
                    with open(category_file, 'r') as f:
                        category_data = json.load(f)
                    
                    category_info = {
                        "id": category_data.get("category", ""),
                        "name": category_data.get("name", ""),
                        "count": category_data.get("count", 0),
                        "description": category_data.get("description", "")
                    }
                    categories.append(category_info)
                    total_wallpapers += category_info["count"]
                    
                    # Add some wallpapers to featured
                    wallpapers = category_data.get("wallpapers", [])
                    if wallpapers:
                        featured.extend(wallpapers[:2])  # Add first 2 from each category
                        
                except Exception as e:
                    logger.error(f"Error processing {category_file}: {e}")
        
        # Create master index
        master_index = {
            "version": "2.0.0",
            "lastUpdated": datetime.now().isoformat() + "Z",
            "totalWallpapers": total_wallpapers,
            "categories": categories,
            "featured": featured[:10],  # Limit featured to 10
            "statistics": {
                "totalCategories": len(categories),
                "averagePerCategory": total_wallpapers / len(categories) if categories else 0,
                "generatedAt": datetime.now().isoformat() + "Z"
            }
        }
        
        # Save master index
        master_file = self.repo_path / "index.json"
        with open(master_file, 'w') as f:
            json.dump(master_index, f, indent=2)
        
        logger.info(f"Generated master index with {total_wallpapers} wallpapers")
        return master_index

def main():
    parser = argparse.ArgumentParser(description='Generate wallpaper collection indexes')
    parser.add_argument('--update-all', action='store_true', help='Update all indexes')
    parser.add_argument('--repo', default='.', help='Repository root path')
    
    args = parser.parse_args()
    
    generator = SimpleIndexGenerator(args.repo)
    
    if args.update_all:
        master_index = generator.generate_master_index()
        print(f"✅ Generated master index with {master_index['totalWallpapers']} wallpapers")
        print(f"📊 Categories: {master_index['statistics']['totalCategories']}")
        print(f"🌟 Featured: {len(master_index['featured'])}")
    else:
        generator.generate_master_index()
        print("✅ Generated master index")

if __name__ == "__main__":
    main()