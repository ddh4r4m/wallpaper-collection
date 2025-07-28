#!/usr/bin/env python3
"""
Generate thumbnails for anime wallpapers
Creates 400x600 thumbnails from wallpapers while maintaining aspect ratio
"""

import os
from PIL import Image
import sys

def generate_thumbnail(source_path, thumbnail_path, size=(400, 600), quality=80):
    """Generate a thumbnail from source image"""
    try:
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (handles RGBA, P mode images)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratio preserving resize
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG with specified quality
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"Error processing {source_path}: {e}")
        return False

def main():
    # Paths
    wallpapers_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/collection/wallpapers/anime"
    thumbnails_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/collection/thumbnails/anime"
    
    # Ensure thumbnails directory exists
    os.makedirs(thumbnails_dir, exist_ok=True)
    
    # Get all wallpaper files (001.jpg to 139.jpg)
    wallpaper_files = []
    for i in range(1, 140):  # 001 to 139
        filename = f"{i:03d}.jpg"
        source_path = os.path.join(wallpapers_dir, filename)
        if os.path.exists(source_path):
            wallpaper_files.append((filename, source_path))
    
    print(f"Found {len(wallpaper_files)} wallpaper files to process")
    
    # Generate thumbnails
    success_count = 0
    for filename, source_path in wallpaper_files:
        thumbnail_path = os.path.join(thumbnails_dir, filename)
        
        if generate_thumbnail(source_path, thumbnail_path):
            success_count += 1
            print(f"✅ Generated thumbnail: {filename}")
        else:
            print(f"❌ Failed to generate thumbnail: {filename}")
    
    print(f"\n🎉 Successfully generated {success_count}/{len(wallpaper_files)} thumbnails")
    
    if success_count == len(wallpaper_files):
        print("✅ All thumbnails generated successfully!")
        return 0
    else:
        print(f"⚠️  {len(wallpaper_files) - success_count} thumbnails failed to generate")
        return 1

if __name__ == "__main__":
    sys.exit(main())