#!/usr/bin/env python3
"""
Complete migration tool for moving ALL wallpapers from old structure to bulletproof collection.
Handles massive migration with progress tracking and error recovery.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
import hashlib

class CompleteMigrator:
    def __init__(self):
        self.base_dir = Path("/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection")
        self.old_dir = self.base_dir / "wallpapers"
        self.collection_dir = self.base_dir / "collection"
        self.new_wallpapers_dir = self.collection_dir / "wallpapers"
        self.new_thumbnails_dir = self.collection_dir / "thumbnails"
        self.new_metadata_dir = self.collection_dir / "metadata"
        
        # Track migration progress
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.total_count = 0
        
        # Categories to migrate
        self.categories = [
            "abstract", "anime", "architecture", "art", "cars", "cyberpunk", 
            "dark", "gaming", "minimal", "nature", "neon", "pastel", 
            "seasonal", "space", "technology", "vintage"
        ]
        
        print(f"🚀 Complete Migration Tool")
        print(f"📁 Source: {self.old_dir}")
        print(f"📁 Target: {self.new_wallpapers_dir}")
    
    def count_total_wallpapers(self):
        """Count total wallpapers to migrate"""
        total = 0
        for category in self.categories:
            old_category_dir = self.old_dir / category
            if old_category_dir.exists():
                jpg_files = list(old_category_dir.glob("*.jpg"))
                total += len(jpg_files)
                print(f"  📊 {category}: {len(jpg_files)} wallpapers")
        
        self.total_count = total
        print(f"\n🎯 Total wallpapers to migrate: {total}")
        return total
    
    def create_directories(self):
        """Create all necessary directories"""
        print(f"\n📁 Creating directory structure...")
        
        for category in self.categories:
            (self.new_wallpapers_dir / category).mkdir(parents=True, exist_ok=True)
            (self.new_thumbnails_dir / category).mkdir(parents=True, exist_ok=True)
            (self.new_metadata_dir / category).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {category}/ directories created")
    
    def get_image_hash(self, image_path):
        """Generate MD5 hash for image"""
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def resize_image(self, input_path, output_path, target_size=(1080, 1920)):
        """Resize image to mobile-optimized dimensions"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate resize dimensions maintaining aspect ratio
                img_ratio = img.width / img.height
                target_ratio = target_size[0] / target_size[1]
                
                if img_ratio > target_ratio:
                    # Image is wider, fit to height
                    new_height = target_size[1]
                    new_width = int(new_height * img_ratio)
                else:
                    # Image is taller, fit to width
                    new_width = target_size[0]
                    new_height = int(new_width / img_ratio)
                
                # Resize and crop to exact target size
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Crop to center if needed
                left = (new_width - target_size[0]) // 2
                top = (new_height - target_size[1]) // 2
                right = left + target_size[0]
                bottom = top + target_size[1]
                
                if left != 0 or top != 0:
                    img_resized = img_resized.crop((left, top, right, bottom))
                
                # Save with high quality
                img_resized.save(output_path, 'JPEG', quality=85, optimize=True)
                return True
        except Exception as e:
            print(f"    ❌ Resize error: {e}")
            return False
    
    def create_thumbnail(self, input_path, output_path, size=(400, 600)):
        """Create thumbnail for wallpaper"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(output_path, 'JPEG', quality=80, optimize=True)
                return True
        except Exception as e:
            print(f"    ❌ Thumbnail error: {e}")
            return False
    
    def create_metadata(self, category, sequential_id, original_path, new_path, thumbnail_path):
        """Create metadata JSON for wallpaper"""
        try:
            # Get image dimensions and file info
            with Image.open(new_path) as img:
                width, height = img.size
            
            file_size = os.path.getsize(new_path)
            image_hash = self.get_image_hash(new_path)
            
            # Create metadata
            metadata = {
                "id": f"{category}_{sequential_id:03d}",
                "category": category,
                "title": f"{category.title()} Wallpaper {sequential_id:03d}",
                "tags": [category, "wallpaper", "hd", "mobile"],
                "urls": {
                    "raw": f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/wallpapers/{category}/{sequential_id:03d}.jpg",
                    "thumb": f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/collection/thumbnails/{category}/{sequential_id:03d}.jpg"
                },
                "metadata": {
                    "dimensions": {
                        "width": width,
                        "height": height
                    },
                    "file_size": file_size,
                    "format": "JPEG",
                    "added_at": datetime.now().isoformat(),
                    "hash": image_hash,
                    "source": "migrated"
                }
            }
            
            # Save metadata
            metadata_path = self.new_metadata_dir / category / f"{sequential_id:03d}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return metadata
        except Exception as e:
            print(f"    ❌ Metadata error: {e}")
            return None
    
    def migrate_category(self, category):
        """Migrate all wallpapers in a category"""
        print(f"\n🔄 Migrating {category}...")
        
        old_category_dir = self.old_dir / category
        new_category_dir = self.new_wallpapers_dir / category
        thumbnail_category_dir = self.new_thumbnails_dir / category
        
        if not old_category_dir.exists():
            print(f"  ⚠️  Source directory doesn't exist: {old_category_dir}")
            return
        
        # Get all JPG files
        jpg_files = sorted(old_category_dir.glob("*.jpg"))
        if not jpg_files:
            print(f"  ⚠️  No wallpapers found in {category}")
            return
        
        print(f"  📊 Found {len(jpg_files)} wallpapers")
        
        # Check what's already migrated to avoid overwriting newer content
        existing_files = list(new_category_dir.glob("*.jpg"))
        start_index = len(existing_files) + 1
        
        if existing_files:
            print(f"  ℹ️  {len(existing_files)} wallpapers already exist, starting from {start_index:03d}")
        
        # Migrate each wallpaper
        for i, old_file in enumerate(jpg_files, start=start_index):
            try:
                sequential_id = i
                new_filename = f"{sequential_id:03d}.jpg"
                thumbnail_filename = f"{sequential_id:03d}.jpg"
                
                new_path = new_category_dir / new_filename
                thumbnail_path = thumbnail_category_dir / thumbnail_filename
                
                # Skip if already exists (avoid overwriting)
                if new_path.exists():
                    print(f"    ⏭️  Skipping {new_filename} (already exists)")
                    self.skipped_count += 1
                    continue
                
                print(f"    🔄 Processing {old_file.name} → {new_filename}")
                
                # Resize and copy wallpaper
                if self.resize_image(old_file, new_path):
                    print(f"      ✅ Wallpaper: {new_filename}")
                else:
                    print(f"      ❌ Failed to process wallpaper")
                    self.error_count += 1
                    continue
                
                # Create thumbnail
                if self.create_thumbnail(new_path, thumbnail_path):
                    print(f"      ✅ Thumbnail: {thumbnail_filename}")
                else:
                    print(f"      ⚠️  Thumbnail creation failed")
                
                # Create metadata
                metadata = self.create_metadata(category, sequential_id, old_file, new_path, thumbnail_path)
                if metadata:
                    print(f"      ✅ Metadata: {sequential_id:03d}.json")
                else:
                    print(f"      ⚠️  Metadata creation failed")
                
                self.migrated_count += 1
                
                # Progress update every 10 files
                if self.migrated_count % 10 == 0:
                    progress = (self.migrated_count / self.total_count) * 100
                    print(f"    📈 Progress: {self.migrated_count}/{self.total_count} ({progress:.1f}%)")
                
            except Exception as e:
                print(f"    ❌ Error processing {old_file.name}: {e}")
                self.error_count += 1
        
        print(f"  ✅ {category} migration complete")
    
    def run_migration(self):
        """Run complete migration process"""
        print(f"\n🚀 Starting complete migration...")
        
        # Count total wallpapers
        self.count_total_wallpapers()
        
        # Create directories
        self.create_directories()
        
        # Migrate each category
        for category in self.categories:
            self.migrate_category(category)
        
        # Final summary
        print(f"\n📊 Migration Summary:")
        print(f"  ✅ Migrated: {self.migrated_count} wallpapers")
        print(f"  ⏭️  Skipped: {self.skipped_count} wallpapers")
        print(f"  ❌ Errors: {self.error_count} wallpapers")
        print(f"  📁 Categories processed: {len(self.categories)}")
        
        success_rate = (self.migrated_count / (self.migrated_count + self.error_count)) * 100 if (self.migrated_count + self.error_count) > 0 else 100
        print(f"  🎯 Success rate: {success_rate:.1f}%")
        
        print(f"\n🎉 Migration complete! Ready to rebuild APIs.")

if __name__ == "__main__":
    migrator = CompleteMigrator()
    migrator.run_migration()