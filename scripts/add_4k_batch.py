#!/usr/bin/env python3
"""
Add downloaded 4K wallpapers to bulletproof collection system
"""

import os
import sys
import json
import shutil
from pathlib import Path
from PIL import Image

def main():
    # Paths
    source_dir = Path("4k_final_batch")
    collection_dir = Path("collection")
    wallpapers_dir = collection_dir / "wallpapers" / "4k"
    thumbnails_dir = collection_dir / "thumbnails" / "4k"
    metadata_dir = collection_dir / "metadata" / "4k"
    
    # Create directories
    for directory in [wallpapers_dir, thumbnails_dir, metadata_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Find current highest number
    current_files = list(wallpapers_dir.glob("*.jpg"))
    if current_files:
        numbers = []
        for f in current_files:
            try:
                num = int(f.stem.split('.')[0])
                numbers.append(num)
            except:
                continue
        start_num = max(numbers) + 1 if numbers else 1
    else:
        start_num = 1
    
    print(f"🚀 Starting from number: {start_num:03d}")
    
    # Process all downloaded images
    source_images = sorted([f for f in source_dir.glob("4k_*.jpg")])
    processed = 0
    
    for source_image in source_images:
        try:
            # Target files
            target_num = start_num + processed
            target_image = wallpapers_dir / f"{target_num:03d}.jpg"
            target_thumb = thumbnails_dir / f"{target_num:03d}.jpg"
            target_meta = metadata_dir / f"{target_num:03d}.json"
            
            # Skip if already exists
            if target_image.exists():
                print(f"⏭️  Skipping {target_num:03d} (already exists)")
                processed += 1
                continue
            
            # Copy and optimize image
            with Image.open(source_image) as img:
                # Resize to mobile-friendly dimensions while maintaining aspect ratio
                img.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
                img.save(target_image, "JPEG", quality=85, optimize=True)
                
                # Generate thumbnail
                img.thumbnail((400, 600), Image.Resampling.LANCZOS)
                img.save(target_thumb, "JPEG", quality=80, optimize=True)
            
            # Load and enhance metadata
            source_meta_file = source_dir / f"{source_image.stem}.json"
            source_meta = {}
            if source_meta_file.exists():
                try:
                    with open(source_meta_file) as f:
                        source_meta = json.load(f)
                except:
                    pass
            
            # Enhanced metadata for bulletproof system
            enhanced_meta = {
                "id": f"4k_{target_num:03d}",
                "filename": f"{target_num:03d}.jpg",
                "title": source_meta.get("description", f"4K Wallpaper {target_num:03d}"),
                "photographer": source_meta.get("photographer", "Unknown"),
                "source": "unsplash",
                "source_id": source_meta.get("id", ""),
                "source_url": source_meta.get("source_url", ""),
                "tags": source_meta.get("tags", []),
                "color": source_meta.get("color", "#000000"),
                "created_at": source_meta.get("created_at", ""),
                "download_url": f"https://raw.githubusercontent.com/username/wallpaper-collection/main/collection/wallpapers/4k/{target_num:03d}.jpg",
                "thumbnail_url": f"https://raw.githubusercontent.com/username/wallpaper-collection/main/collection/thumbnails/4k/{target_num:03d}.jpg",
            }
            
            with open(target_meta, 'w') as f:
                json.dump(enhanced_meta, f, indent=2)
            
            print(f"✅ Added: {target_num:03d}.jpg ({source_meta.get('photographer', 'Unknown')})")
            processed += 1
            
        except Exception as e:
            print(f"❌ Error processing {source_image}: {e}")
            continue
    
    print(f"\n🎉 Processed {processed} wallpapers!")
    
    # Rebuild APIs
    print("🔄 Rebuilding APIs...")
    os.system("python3 scripts/build_api.py")
    
if __name__ == "__main__":
    main()