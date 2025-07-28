#!/usr/bin/env python3
"""
Organize Downloaded Gradients
Move collected gradient wallpapers to the main collection
"""

import os
import sys
import json
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def organize_gradients():
    """Organize gradient wallpapers into the main collection"""
    
    # Source directories (our downloaded gradients)
    source_dirs = [
        Path("gradient_collection"),
        Path("gradient_wallpapers"),
        Path("premium_gradient_cache")
    ]
    
    # Destination directory
    dest_dir = Path("wallpapers/gradient")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Also create thumbnails directory
    thumb_dir = Path("thumbnails/gradient")
    thumb_dir.mkdir(parents=True, exist_ok=True)
    
    organized_count = 0
    gradient_metadata = []
    
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
            
        logger.info(f"📂 Processing {source_dir}/")
        
        # Find all gradient images
        jpg_files = list(source_dir.glob("*.jpg"))
        
        for jpg_file in jpg_files:
            try:
                # Check for corresponding metadata
                json_file = jpg_file.with_suffix('.json')
                metadata = {}
                
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                
                # Create new standardized filename
                organized_count += 1
                new_filename = f"gradient_{organized_count:03d}.jpg"
                new_filepath = dest_dir / new_filename
                
                # Copy image to destination
                shutil.copy2(jpg_file, new_filepath)
                
                # Create standardized metadata
                standard_metadata = {
                    "id": f"gradient_{organized_count:03d}",
                    "filename": new_filename,
                    "title": metadata.get('title', f"Abstract Gradient {organized_count}"),
                    "description": metadata.get('description', "High-quality abstract gradient background for mobile"),
                    "category": "gradient",
                    "tags": ["gradient", "abstract", "background", "mobile", "wallpaper"],
                    "source": metadata.get('source', 'pinterest'),
                    "width": 1080,  # Estimated mobile width
                    "height": 1920,  # Estimated mobile height
                    "file_size": new_filepath.stat().st_size,
                    "download_url": f"https://raw.githubusercontent.com/username/wallpaper-collection/main/wallpapers/gradient/{new_filename}",
                    "thumbnail_url": f"https://raw.githubusercontent.com/username/wallpaper-collection/main/thumbnails/gradient/{new_filename}",
                    "gradient_type": metadata.get('gradient_type', 'abstract'),
                    "mobile_optimized": True,
                    "quality": "high",
                    "created_at": metadata.get('downloaded_at', metadata.get('crawled_at', '2025-01-20T20:40:00Z'))
                }
                
                # Save standardized metadata
                metadata_file = new_filepath.with_suffix('.json')
                with open(metadata_file, 'w') as f:
                    json.dump(standard_metadata, f, indent=2)
                
                gradient_metadata.append(standard_metadata)
                
                logger.info(f"✅ Organized: {jpg_file.name} → {new_filename}")
                
            except Exception as e:
                logger.error(f"❌ Failed to organize {jpg_file.name}: {e}")
    
    # Create gradient category index
    create_gradient_index(gradient_metadata, dest_dir.parent.parent)
    
    logger.info(f"🎉 Organization complete!")
    logger.info(f"📊 Organized {organized_count} gradient wallpapers")
    logger.info(f"📁 Location: {dest_dir}/")
    
    return organized_count

def create_gradient_index(gradient_metadata, repo_root):
    """Create gradient category index file"""
    
    categories_dir = repo_root / "categories"
    categories_dir.mkdir(exist_ok=True)
    
    gradient_index = {
        "category": "gradient",
        "name": "Gradient",
        "description": "Abstract gradient backgrounds and smooth color transitions for mobile wallpapers",
        "count": len(gradient_metadata),
        "lastUpdated": "2025-01-20T20:40:00Z",
        "tags": ["gradient", "abstract", "mobile", "colors", "smooth", "backgrounds"],
        "wallpapers": gradient_metadata
    }
    
    index_file = categories_dir / "gradient.json"
    with open(index_file, 'w') as f:
        json.dump(gradient_index, f, indent=2)
    
    logger.info(f"📋 Created gradient index: {index_file}")

def update_master_index(repo_root, gradient_count):
    """Update master index.json with gradient category"""
    
    index_file = repo_root / "index.json"
    
    # Load existing index or create new one
    if index_file.exists():
        with open(index_file, 'r') as f:
            master_index = json.load(f)
    else:
        master_index = {
            "version": "1.0.0",
            "lastUpdated": "2025-01-20T20:40:00Z",
            "totalWallpapers": 0,
            "categories": [],
            "featured": []
        }
    
    # Update gradient category
    gradient_category = {
        "id": "gradient",
        "name": "Gradient",
        "count": gradient_count,
        "description": "Abstract gradient backgrounds and smooth color transitions"
    }
    
    # Update or add gradient category
    categories = master_index.get("categories", [])
    gradient_exists = False
    
    for i, cat in enumerate(categories):
        if cat.get("id") == "gradient":
            categories[i] = gradient_category
            gradient_exists = True
            break
    
    if not gradient_exists:
        categories.append(gradient_category)
    
    master_index["categories"] = categories
    master_index["totalWallpapers"] = sum(cat.get("count", 0) for cat in categories)
    master_index["lastUpdated"] = "2025-01-20T20:40:00Z"
    
    # Save updated index
    with open(index_file, 'w') as f:
        json.dump(master_index, f, indent=2)
    
    logger.info(f"📋 Updated master index: {index_file}")

def main():
    """Main organization function"""
    logger.info("🎨 Starting gradient wallpaper organization...")
    
    try:
        # Organize gradients
        organized_count = organize_gradients()
        
        if organized_count > 0:
            # Update master index
            update_master_index(Path("."), organized_count)
            
            print(f"\n🎉 Gradient organization complete!")
            print(f"📊 Organized: {organized_count} gradient wallpapers")
            print(f"📁 Main collection: wallpapers/gradient/")
            print(f"📋 Category index: categories/gradient.json")
            print(f"📋 Master index: index.json")
            
            print(f"\n🔄 Next steps:")
            print(f"1. Review gradients in wallpapers/gradient/")
            print(f"2. Generate thumbnails if needed")
            print(f"3. Commit to repository")
            print(f"4. Update any app integrations")
            
            # Show organized files
            gradient_files = list(Path("wallpapers/gradient").glob("*.jpg"))
            if gradient_files:
                print(f"\n📸 Organized gradient wallpapers:")
                for i, file in enumerate(gradient_files, 1):
                    size = file.stat().st_size
                    print(f"  {i}. {file.name} ({size//1024} KB)")
        else:
            print("⚠️  No gradient wallpapers found to organize")
            
    except Exception as e:
        logger.error(f"Organization failed: {e}")

if __name__ == "__main__":
    main()