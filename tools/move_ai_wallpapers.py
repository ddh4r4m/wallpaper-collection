#!/usr/bin/env python3
"""
Move all AI-generated wallpapers to a dedicated AI category
"""

import os
import json
import shutil
from pathlib import Path

def move_ai_wallpapers():
    """Move all AI-generated wallpapers to the AI category"""
    
    # Define the AI wallpapers to move (from our analysis)
    ai_wallpapers = {
        'abstract': list(range(220, 229)),  # 220-228 (9 files)
        'anime': list(range(117, 126)),     # 117-125 (9 files)
        'art': list(range(73, 81)),         # 073-080 (8 files)
        'cyberpunk': list(range(57, 62)),   # 057-061 (5 files)
        'dark': list(range(81, 86)),        # 081-085 (5 files)
        'minimal': list(range(57, 62)),     # 057-061 (5 files)
        'nature': list(range(285, 295)),    # 285-294 (10 files)
        'space': list(range(87, 95)),       # 087-094 (8 files)
    }
    
    base_dir = Path.cwd()
    ai_counter = 1
    moved_count = 0
    
    # Create AI directories
    ai_wallpapers_dir = base_dir / "collection" / "wallpapers" / "ai"
    ai_thumbnails_dir = base_dir / "collection" / "thumbnails" / "ai"
    ai_metadata_dir = base_dir / "collection" / "metadata" / "ai"
    
    ai_wallpapers_dir.mkdir(parents=True, exist_ok=True)
    ai_thumbnails_dir.mkdir(parents=True, exist_ok=True)
    ai_metadata_dir.mkdir(parents=True, exist_ok=True)
    
    print("🤖 Moving AI-generated wallpapers to dedicated AI category...")
    
    for category, file_numbers in ai_wallpapers.items():
        print(f"\n📂 Processing {category} category...")
        
        for file_num in file_numbers:
            file_id = f"{file_num:03d}"
            
            # Source paths
            src_wallpaper = base_dir / "collection" / "wallpapers" / category / f"{file_id}.jpg"
            src_thumbnail = base_dir / "collection" / "thumbnails" / category / f"{file_id}.jpg"
            src_metadata = base_dir / "collection" / "metadata" / category / f"{file_id}.json"
            
            # Check if files exist and contain AI metadata
            if not all([src_wallpaper.exists(), src_thumbnail.exists(), src_metadata.exists()]):
                print(f"⚠️  Skipping {category}_{file_id} - files missing")
                continue
            
            # Verify it's actually an AI wallpaper by checking metadata
            try:
                with open(src_metadata, 'r') as f:
                    metadata = json.load(f)
                
                if not metadata.get('ai_generated', False):
                    print(f"⚠️  Skipping {category}_{file_id} - not marked as AI-generated")
                    continue
                    
            except Exception as e:
                print(f"❌ Error reading metadata for {category}_{file_id}: {e}")
                continue
            
            # Destination paths with AI numbering
            ai_id = f"{ai_counter:03d}"
            dst_wallpaper = ai_wallpapers_dir / f"{ai_id}.jpg"
            dst_thumbnail = ai_thumbnails_dir / f"{ai_id}.jpg"
            dst_metadata = ai_metadata_dir / f"{ai_id}.json"
            
            try:
                # Move files
                shutil.move(str(src_wallpaper), str(dst_wallpaper))
                shutil.move(str(src_thumbnail), str(dst_thumbnail))
                
                # Update metadata for AI category
                metadata['original_category'] = category
                metadata['original_id'] = f"{category}_{file_id}"
                
                # Update tags - replace original category with 'ai'
                if 'tags' in metadata:
                    tags = metadata['tags']
                    if category in tags:
                        tags[tags.index(category)] = 'ai'
                    if 'ai' not in tags:
                        tags.insert(0, 'ai')
                    metadata['tags'] = tags
                
                # Save updated metadata
                with open(dst_metadata, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Remove old metadata file
                src_metadata.unlink()
                
                print(f"✅ Moved {category}_{file_id} → ai_{ai_id}")
                moved_count += 1
                ai_counter += 1
                
            except Exception as e:
                print(f"❌ Failed to move {category}_{file_id}: {e}")
                # Try to restore files if partially moved
                if dst_wallpaper.exists():
                    shutil.move(str(dst_wallpaper), str(src_wallpaper))
                if dst_thumbnail.exists():
                    shutil.move(str(dst_thumbnail), str(src_thumbnail))
    
    print(f"\n🎉 Successfully moved {moved_count} AI wallpapers to dedicated AI category!")
    print(f"📊 AI category now contains {ai_counter - 1} wallpapers")
    
    return moved_count

if __name__ == "__main__":
    move_ai_wallpapers()