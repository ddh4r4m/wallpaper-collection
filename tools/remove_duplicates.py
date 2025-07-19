#!/usr/bin/env python3
"""
Find and remove duplicate images in wallpaper collection
Usage: python3 tools/remove_duplicates.py --category ai --dry-run
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from collections import defaultdict
import shutil

try:
    from PIL import Image
    import imagehash
except ImportError:
    print("Installing required packages...")
    os.system("python3 -m pip install --user Pillow imagehash --break-system-packages")
    from PIL import Image
    import imagehash

from add_wallpaper import WallpaperManager

class DuplicateRemover:
    def __init__(self):
        self.manager = WallpaperManager()
        self.duplicates_found = []
        
    def calculate_image_hash(self, image_path):
        """Calculate perceptual hash of an image"""
        try:
            with Image.open(image_path) as img:
                # Use average hash for better duplicate detection
                return str(imagehash.average_hash(img, hash_size=16))
        except Exception as e:
            print(f"❌ Error hashing {image_path}: {e}")
            return None
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of file content"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"❌ Error calculating file hash for {file_path}: {e}")
            return None
    
    def get_image_quality_score(self, image_path):
        """Calculate quality score based on resolution and file size"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = image_path.stat().st_size
                
                # Resolution score (higher is better)
                resolution_score = (width * height) / 1000000  # Convert to megapixels
                
                # File size score (not too small, not too large)
                size_score = min(file_size / 100000, 10)  # 100KB+ gets points, max at 1MB
                
                # Format score
                format_score = 2 if img.format == 'JPEG' else 1
                
                total_score = resolution_score + size_score + format_score
                return total_score
                
        except Exception as e:
            print(f"❌ Error calculating quality for {image_path}: {e}")
            return 0
    
    def find_duplicates_in_category(self, category):
        """Find all duplicate images in a category"""
        print(f"\n🔍 Scanning {category} category for duplicates...")
        
        category_dir = self.manager.wallpapers_dir / category
        if not category_dir.exists():
            print(f"❌ Category directory not found: {category}")
            return []
        
        # Get all image files
        image_files = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.jpeg")) + list(category_dir.glob("*.png"))
        print(f"📁 Found {len(image_files)} images to analyze")
        
        # Group by image hash
        hash_groups = defaultdict(list)
        file_hash_groups = defaultdict(list)
        
        for image_path in image_files:
            print(f"  🔍 Analyzing {image_path.name}...")
            
            # Calculate both perceptual and file hashes
            image_hash = self.calculate_image_hash(image_path)
            file_hash = self.calculate_file_hash(image_path)
            
            if image_hash:
                hash_groups[image_hash].append(image_path)
            
            if file_hash:
                file_hash_groups[file_hash].append(image_path)
        
        # Find duplicates
        duplicates = []
        
        # Check perceptual duplicates
        for img_hash, files in hash_groups.items():
            if len(files) > 1:
                quality_scores = []
                for file_path in files:
                    score = self.get_image_quality_score(file_path)
                    quality_scores.append((file_path, score))
                
                # Sort by quality (highest first)
                quality_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Keep the best quality, mark others as duplicates
                best_file = quality_scores[0][0]
                duplicate_files = [item[0] for item in quality_scores[1:]]
                
                duplicates.append({
                    'type': 'perceptual',
                    'hash': img_hash,
                    'keep': best_file,
                    'remove': duplicate_files,
                    'files': files
                })
        
        # Check exact file duplicates
        for file_hash, files in file_hash_groups.items():
            if len(files) > 1:
                # For exact duplicates, keep the one with the lowest number
                files_with_numbers = []
                for file_path in files:
                    try:
                        # Extract number from filename
                        number = int(file_path.stem)
                        files_with_numbers.append((file_path, number))
                    except ValueError:
                        # If can't extract number, use 9999 as fallback
                        files_with_numbers.append((file_path, 9999))
                
                # Sort by number (lowest first)
                files_with_numbers.sort(key=lambda x: x[1])
                
                # Keep the lowest numbered file
                best_file = files_with_numbers[0][0]
                duplicate_files = [item[0] for item in files_with_numbers[1:]]
                
                # Check if this isn't already covered by perceptual duplicates
                already_found = any(
                    best_file in dup['files'] or any(f in dup['files'] for f in duplicate_files)
                    for dup in duplicates
                )
                
                if not already_found:
                    duplicates.append({
                        'type': 'exact',
                        'hash': file_hash,
                        'keep': best_file,
                        'remove': duplicate_files,
                        'files': files
                    })
        
        print(f"🔍 Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def display_duplicates(self, duplicates, category):
        """Display found duplicates for user review"""
        if not duplicates:
            print(f"✅ No duplicates found in {category}")
            return
        
        print(f"\n📋 Found {len(duplicates)} duplicate groups in {category}:")
        
        total_to_remove = 0
        for i, dup_group in enumerate(duplicates, 1):
            print(f"\n🔍 Group {i} ({dup_group['type']} duplicate):")
            print(f"  📌 KEEP: {dup_group['keep'].name}")
            
            for remove_file in dup_group['remove']:
                quality_score = self.get_image_quality_score(remove_file)
                print(f"  ❌ REMOVE: {remove_file.name} (quality: {quality_score:.1f})")
                total_to_remove += 1
        
        print(f"\n📊 Summary:")
        print(f"  • Duplicate groups: {len(duplicates)}")
        print(f"  • Files to remove: {total_to_remove}")
        print(f"  • Files to keep: {len(duplicates)}")
        
        return total_to_remove
    
    def remove_duplicates(self, duplicates, category, dry_run=True):
        """Remove duplicate files and their associated data"""
        if not duplicates:
            return 0
        
        removed_count = 0
        backup_dir = Path("/tmp/duplicate_backups") / category
        
        if not dry_run:
            backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"📦 Backing up removed files to {backup_dir}")
        
        for dup_group in duplicates:
            keep_file = dup_group['keep']
            
            for remove_file in dup_group['remove']:
                if dry_run:
                    print(f"🔍 Would remove: {remove_file.name}")
                else:
                    try:
                        # Backup the file
                        backup_path = backup_dir / remove_file.name
                        shutil.copy2(remove_file, backup_path)
                        
                        # Remove main wallpaper
                        remove_file.unlink()
                        print(f"🗑️  Removed: {remove_file.name}")
                        
                        # Remove thumbnail if exists
                        thumb_path = self.manager.thumbnails_dir / category / remove_file.name
                        if thumb_path.exists():
                            thumb_backup = backup_dir / f"thumb_{remove_file.name}"
                            shutil.copy2(thumb_path, thumb_backup)
                            thumb_path.unlink()
                            print(f"🗑️  Removed thumbnail: {remove_file.name}")
                        
                        # Remove metadata if exists
                        metadata_path = self.manager.metadata_dir / category / f"{remove_file.stem}.json"
                        if metadata_path.exists():
                            metadata_backup = backup_dir / f"meta_{remove_file.stem}.json"
                            shutil.copy2(metadata_path, metadata_backup)
                            metadata_path.unlink()
                            print(f"🗑️  Removed metadata: {remove_file.stem}.json")
                        
                        removed_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error removing {remove_file.name}: {e}")
        
        if not dry_run:
            print(f"\n✅ Successfully removed {removed_count} duplicate files")
            print(f"📦 Backups saved to: {backup_dir}")
        
        return removed_count
    
    def renumber_category(self, category, dry_run=True):
        """Renumber files to fill gaps after removing duplicates"""
        print(f"\n🔢 Renumbering {category} category...")
        
        category_dir = self.manager.wallpapers_dir / category
        image_files = sorted(category_dir.glob("*.jpg"))
        
        # Get current numbers
        current_numbers = []
        for file_path in image_files:
            try:
                number = int(file_path.stem)
                current_numbers.append((number, file_path))
            except ValueError:
                print(f"⚠️  Skipping non-numeric file: {file_path.name}")
        
        current_numbers.sort()
        
        # Check if renumbering is needed
        expected_sequence = list(range(1, len(current_numbers) + 1))
        actual_sequence = [num for num, _ in current_numbers]
        
        if expected_sequence == actual_sequence:
            print(f"✅ No renumbering needed for {category}")
            return 0
        
        print(f"📋 Current sequence: {actual_sequence[:10]}{'...' if len(actual_sequence) > 10 else ''}")
        print(f"📋 Target sequence: {expected_sequence[:10]}{'...' if len(expected_sequence) > 10 else ''}")
        
        if dry_run:
            print(f"🔍 Would renumber {len(current_numbers)} files")
            return len(current_numbers)
        
        # Perform renumbering
        temp_dir = category_dir / "temp_renumber"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Move all files to temp directory with new names
            for new_number, (old_number, old_path) in enumerate(current_numbers, 1):
                new_name = f"{new_number:03d}.jpg"
                temp_path = temp_dir / new_name
                
                # Move main file
                shutil.move(old_path, temp_path)
                
                # Move thumbnail
                old_thumb = self.manager.thumbnails_dir / category / old_path.name
                new_thumb = self.manager.thumbnails_dir / category / new_name
                if old_thumb.exists():
                    new_thumb.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(old_thumb, new_thumb)
                
                # Move metadata
                old_meta = self.manager.metadata_dir / category / f"{old_path.stem}.json"
                new_meta = self.manager.metadata_dir / category / f"{new_number:03d}.json"
                if old_meta.exists():
                    new_meta.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(old_meta, new_meta)
            
            # Move files back from temp directory
            for temp_file in temp_dir.glob("*.jpg"):
                final_path = category_dir / temp_file.name
                shutil.move(temp_file, final_path)
            
            # Clean up temp directory
            temp_dir.rmdir()
            
            print(f"✅ Successfully renumbered {len(current_numbers)} files in {category}")
            return len(current_numbers)
            
        except Exception as e:
            print(f"❌ Error during renumbering: {e}")
            # Try to restore from temp if possible
            for temp_file in temp_dir.glob("*"):
                try:
                    shutil.move(temp_file, category_dir)
                except:
                    pass
            return 0

def main():
    parser = argparse.ArgumentParser(description='Find and remove duplicate wallpapers')
    parser.add_argument('--category', required=True, help='Category to check for duplicates')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually removing files')
    parser.add_argument('--renumber', action='store_true', help='Renumber files after removing duplicates')
    
    args = parser.parse_args()
    
    remover = DuplicateRemover()
    
    # Find duplicates
    duplicates = remover.find_duplicates_in_category(args.category)
    
    # Display results
    total_to_remove = remover.display_duplicates(duplicates, args.category)
    
    if total_to_remove > 0:
        if args.dry_run:
            print(f"\n🔍 DRY RUN: Run without --dry-run to actually remove {total_to_remove} duplicate files")
        else:
            # Auto-proceed with removal (since we're in automation mode)
            print(f"\n🔄 Proceeding to remove {total_to_remove} duplicate files...")
            removed = remover.remove_duplicates(duplicates, args.category, dry_run=False)
            
            if removed > 0 and args.renumber:
                # Renumber after removal
                remover.renumber_category(args.category, dry_run=False)
                
                # Rebuild API after changes
                print(f"\n🔄 Rebuilding API indexes...")
                os.system("python3 tools/build_api.py")

if __name__ == '__main__':
    main()