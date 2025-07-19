#!/usr/bin/env python3
"""
Fix metadata files to include required fields for index generation
"""
import json
import os
from pathlib import Path

def fix_metadata_files():
    wallpapers_dir = Path("wallpapers")
    
    for category_dir in wallpapers_dir.iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        print(f"Processing {category} category...")
        
        for json_file in category_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    metadata = json.load(f)
                
                # Get the corresponding image filename
                image_file = json_file.stem + ".jpg"
                
                # Add required fields if missing
                if "filename" not in metadata:
                    metadata["filename"] = image_file
                
                if "title" not in metadata:
                    metadata["title"] = f"{category.title()} Wallpaper"
                
                if "width" not in metadata:
                    metadata["width"] = 1080
                    
                if "height" not in metadata:
                    metadata["height"] = 1920
                
                if "tags" not in metadata:
                    metadata["tags"] = [category, "wallpaper", "hd", "high resolution", "mobile"]
                
                if "description" not in metadata:
                    metadata["description"] = f"High-quality {category} wallpaper"
                
                # Save updated metadata
                with open(json_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
        
        count = len(list(category_dir.glob("*.jpg")))
        print(f"  Fixed {count} {category} wallpapers")

if __name__ == "__main__":
    fix_metadata_files()
    print("Metadata fixing complete!")