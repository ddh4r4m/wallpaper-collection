#!/usr/bin/env python3
"""
Migrate existing wallpaper collection to new bulletproof structure
Usage: ./tools/migrate_collection.py [options]

This tool:
1. Scans existing wallpapers/ directory
2. Copies images to new collection/wallpapers/ with sequential numbering
3. Migrates metadata from existing JSON files
4. Generates thumbnails for all images
5. Builds new APIs with correct URLs
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import hashlib

class CollectionMigrator:
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        
        # Old structure
        self.old_wallpapers_dir = self.repo_root / "wallpapers"
        self.old_categories_dir = self.repo_root / "categories"
        self.old_thumbnails_dir = self.repo_root / "thumbnails"
        
        # Valid categories
        self.valid_categories = {
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk', 'gaming', 
            'anime', 'movies', 'music', 'cars', 'sports', 'technology', 
            'architecture', 'art', 'dark', 'neon', 'pastel', 'vintage', 
            'gradient', 'seasonal'
        }
        
        # New structure
        self.collection_root = self.repo_root / "collection"
        self.new_wallpapers_dir = self.collection_root / "wallpapers"
        self.new_thumbnails_dir = self.collection_root / "thumbnails"
        self.new_metadata_dir = self.collection_root / "metadata"
        self.api_dir = self.collection_root / "api" / "v1"
        
        # Settings
        self.thumb_size = (400, 600)
        self.thumb_quality = 80
        
        # Ensure new directories exist
        for cat_dir in [self.new_wallpapers_dir, self.new_thumbnails_dir, self.new_metadata_dir]:
            for category in self.valid_categories:
                (cat_dir / category).mkdir(parents=True, exist_ok=True)
        
        self.api_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_thumbnail(self, image_path, thumb_path):
        """Generate thumbnail for image"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')
                
                # Auto-rotate based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail
                img.thumbnail(self.thumb_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(thumb_path, 'JPEG', quality=self.thumb_quality, optimize=True)
                
                return True
        except Exception as e:
            print(f"    Warning: Failed to generate thumbnail for {image_path}: {e}")
            return False
    
    def load_old_metadata(self, category):
        """Load metadata from old category JSON file"""
        category_file = self.old_categories_dir / f"{category}.json"
        
        if not category_file.exists():
            return {}
        
        try:
            with open(category_file) as f:
                data = json.load(f)
            
            # Build lookup by filename
            metadata_lookup = {}
            for wallpaper in data.get('wallpapers', []):
                filename = wallpaper.get('filename', '')
                if filename:
                    metadata_lookup[filename] = wallpaper
            
            return metadata_lookup
        except Exception as e:
            print(f"    Warning: Failed to load metadata for {category}: {e}")
            return {}
    
    def migrate_category(self, category):
        """Migrate a single category"""
        old_category_dir = self.old_wallpapers_dir / category
        
        if not old_category_dir.exists():
            print(f"  Skipping {category} (no directory)")
            return 0
        
        print(f"  Migrating {category}...")
        
        # Load old metadata
        old_metadata = self.load_old_metadata(category)
        
        # Find all images
        image_files = list(old_category_dir.glob("*.jpg")) + list(old_category_dir.glob("*.png"))
        
        if not image_files:
            print(f"    No images found in {category}")
            return 0
        
        migrated_count = 0
        
        # Sort by filename for consistent ordering
        for image_file in sorted(image_files):
            # Generate new sequential ID
            new_id = f"{migrated_count + 1:03d}"
            
            # Determine new paths
            new_image_path = self.new_wallpapers_dir / category / f"{new_id}.jpg"
            new_thumb_path = self.new_thumbnails_dir / category / f"{new_id}.jpg"
            new_metadata_path = self.new_metadata_dir / category / f"{new_id}.json"
            
            try:
                # Copy image (convert to JPEG if needed)
                if image_file.suffix.lower() == '.jpg':
                    shutil.copy2(image_file, new_image_path)
                else:
                    # Convert to JPEG
                    with Image.open(image_file) as img:
                        if img.mode in ['RGBA', 'P']:
                            img = img.convert('RGB')
                        img = ImageOps.exif_transpose(img)
                        img.save(new_image_path, 'JPEG', quality=85, optimize=True)
                
                # Generate thumbnail
                self.generate_thumbnail(new_image_path, new_thumb_path)
                
                # Create metadata
                old_meta = old_metadata.get(image_file.name, {})
                
                # Extract basic info
                with Image.open(new_image_path) as img:
                    width, height = img.size
                
                new_metadata = {
                    'id': f"{category}_{new_id}",
                    'category': category,
                    'title': old_meta.get('title', f"{category.title()} Wallpaper {new_id}"),
                    'tags': old_meta.get('tags', [category]),
                    'metadata': {
                        'dimensions': {
                            'width': width,
                            'height': height
                        },
                        'file_size': new_image_path.stat().st_size,
                        'added_at': old_meta.get('createdAt', datetime.now().isoformat()),
                        'migrated_from': str(image_file)
                    }
                }
                
                # Add optional fields if available
                if 'photographer' in old_meta:
                    new_metadata['metadata']['photographer'] = old_meta['photographer']
                
                # Save metadata
                with open(new_metadata_path, 'w') as f:
                    json.dump(new_metadata, f, indent=2)
                
                migrated_count += 1
                
            except Exception as e:
                print(f"    Error migrating {image_file.name}: {e}")
                continue
        
        print(f"    Migrated {migrated_count} wallpapers")
        return migrated_count
    
    def migrate_all(self):
        """Migrate entire collection"""
        print("Starting collection migration...")
        
        total_migrated = 0
        
        for category in sorted(self.valid_categories):
            count = self.migrate_category(category)
            total_migrated += count
        
        print(f"\n✅ Migration complete: {total_migrated} wallpapers migrated")
        
        # Build APIs
        print("\nBuilding new APIs...")
        from tools.build_api import APIBuilder
        builder = APIBuilder(self.repo_root)
        builder.build_all_apis()
        
        return total_migrated
    
    def verify_migration(self):
        """Verify migration was successful"""
        print("\nVerifying migration...")
        
        issues = []
        
        for category in self.valid_categories:
            category_dir = self.new_wallpapers_dir / category
            thumb_dir = self.new_thumbnails_dir / category
            meta_dir = self.new_metadata_dir / category
            
            if not category_dir.exists():
                continue
            
            # Check each image has thumbnail and metadata
            for image_file in category_dir.glob("*.jpg"):
                image_id = image_file.stem
                thumb_file = thumb_dir / f"{image_id}.jpg"
                meta_file = meta_dir / f"{image_id}.json"
                
                if not thumb_file.exists():
                    issues.append(f"Missing thumbnail: {category}/{image_id}")
                
                if not meta_file.exists():
                    issues.append(f"Missing metadata: {category}/{image_id}")
                else:
                    # Verify metadata is valid JSON
                    try:
                        with open(meta_file) as f:
                            json.load(f)
                    except:
                        issues.append(f"Invalid metadata: {category}/{image_id}")
        
        if issues:
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"   {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more")
        else:
            print("✅ Migration verification passed")
        
        return len(issues) == 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate collection to new structure')
    parser.add_argument('--verify-only', action='store_true', help='Only verify migration')
    parser.add_argument('--category', help='Migrate specific category only')
    
    args = parser.parse_args()
    
    migrator = CollectionMigrator()
    
    if args.verify_only:
        migrator.verify_migration()
        return
    
    try:
        if args.category:
            if args.category not in migrator.valid_categories:
                print(f"❌ Invalid category: {args.category}")
                return
            
            count = migrator.migrate_category(args.category)
            print(f"✅ Migrated {count} wallpapers from {args.category}")
        else:
            total = migrator.migrate_all()
            print(f"🎉 Migration complete: {total} total wallpapers")
            
            # Verify
            migrator.verify_migration()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()