#!/usr/bin/env python3
"""
Parallel Category Processor - Process images correctly by category with duplicate detection
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParallelCategoryProcessor:
    """Process images by actual category with parallel execution and duplicate detection"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.approved_dir = self.repo_path / "review_system" / "approved"
        
        # All categories to process
        self.categories = [
            'abstract', 'nature', 'space', 'minimal', 'cyberpunk',
            'gaming', 'anime', 'movies', 'music', 'cars', 'sports',
            'technology', 'architecture', 'art', 'dark', 'neon',
            'pastel', 'vintage', 'gradient', 'seasonal'
        ]
        
        # Track processed hashes to avoid duplicates
        self.processed_hashes: Set[str] = set()
        self.category_files: Dict[str, List[Path]] = {}
        
    def load_existing_hashes(self):
        """Load hashes of existing processed images"""
        for category in self.categories:
            category_dir = self.repo_path / "wallpapers" / category
            if category_dir.exists():
                for json_file in category_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        if 'hash' in data:
                            self.processed_hashes.add(data['hash'])
                    except Exception as e:
                        logger.warning(f"Error loading hash from {json_file}: {e}")
    
    def categorize_approved_images(self):
        """Categorize approved images by their actual category"""
        if not self.approved_dir.exists():
            logger.error("Approved directory not found")
            return
        
        # Initialize category lists
        for category in self.categories:
            self.category_files[category] = []
        
        # Process each approved image
        for image_file in self.approved_dir.glob("*.jpg"):
            json_file = image_file.with_suffix('.json')
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Determine actual category from original metadata
                    actual_category = self.determine_actual_category(metadata)
                    if actual_category in self.categories:
                        self.category_files[actual_category].append(image_file)
                        logger.info(f"Categorized {image_file.name} as {actual_category}")
                    else:
                        logger.warning(f"Unknown category for {image_file.name}: {actual_category}")
                        
                except Exception as e:
                    logger.error(f"Error processing {image_file.name}: {e}")
    
    def determine_actual_category(self, metadata: Dict) -> str:
        """Determine actual category from metadata"""
        # Check original metadata first
        if 'original_metadata' in metadata:
            orig_category = metadata['original_metadata'].get('category', '')
            if orig_category:
                return orig_category
        
        # Check title for category hints
        title = metadata.get('title', '').lower()
        if 'nature' in title:
            return 'nature'
        elif 'space' in title:
            return 'space'
        elif 'abstract' in title:
            return 'abstract'
        elif 'minimal' in title:
            return 'minimal'
        elif 'technology' in title:
            return 'technology'
        
        # Check tags for category hints
        tags = metadata.get('tags', [])
        if isinstance(tags, list):
            tag_str = ' '.join(tags).lower()
            if 'nature' in tag_str or 'landscape' in tag_str:
                return 'nature'
            elif 'space' in tag_str or 'cosmic' in tag_str:
                return 'space'
            elif 'abstract' in tag_str or 'geometric' in tag_str:
                return 'abstract'
            elif 'minimal' in tag_str or 'clean' in tag_str:
                return 'minimal'
            elif 'technology' in tag_str or 'tech' in tag_str:
                return 'technology'
        
        # Default fallback
        return 'abstract'
    
    def get_image_hash(self, image_path: Path) -> str:
        """Calculate hash for image file"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error calculating hash for {image_path}: {e}")
            return ""
    
    def is_duplicate(self, image_path: Path) -> bool:
        """Check if image is duplicate based on hash"""
        image_hash = self.get_image_hash(image_path)
        if image_hash in self.processed_hashes:
            return True
        self.processed_hashes.add(image_hash)
        return False
    
    def process_single_category(self, category: str, max_images: int = 50) -> Dict:
        """Process a single category"""
        logger.info(f"Processing category: {category}")
        
        if category not in self.category_files:
            return {'category': category, 'processed': 0, 'duplicates': 0, 'errors': 0}
        
        category_images = self.category_files[category]
        if not category_images:
            logger.info(f"No images found for category: {category}")
            return {'category': category, 'processed': 0, 'duplicates': 0, 'errors': 0}
        
        # Create category directories
        wallpapers_dir = self.repo_path / "wallpapers" / category
        thumbnails_dir = self.repo_path / "thumbnails" / category
        wallpapers_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        processed = 0
        duplicates = 0
        errors = 0
        
        # Process images for this category
        for i, image_path in enumerate(category_images):
            if processed >= max_images:
                break
                
            try:
                # Check for duplicates
                if self.is_duplicate(image_path):
                    duplicates += 1
                    logger.info(f"Skipping duplicate: {image_path.name}")
                    continue
                
                # Load metadata
                json_path = image_path.with_suffix('.json')
                if not json_path.exists():
                    errors += 1
                    continue
                
                with open(json_path, 'r') as f:
                    metadata = json.load(f)
                
                # Generate new filename
                new_filename = f"{category}_{processed + 1:03d}.jpg"
                
                # Copy and process image
                dest_image = wallpapers_dir / new_filename
                dest_json = wallpapers_dir / f"{category}_{processed + 1:03d}.json"
                dest_thumb = thumbnails_dir / new_filename
                
                # Copy image
                shutil.copy2(image_path, dest_image)
                
                # Generate thumbnail (simple resize)
                try:
                    from PIL import Image
                    with Image.open(dest_image) as img:
                        img.thumbnail((300, 533), Image.Resampling.LANCZOS)
                        img.save(dest_thumb, 'JPEG', quality=85)
                except ImportError:
                    logger.warning("PIL not available, skipping thumbnail generation")
                    shutil.copy2(image_path, dest_thumb)
                
                # Update metadata
                updated_metadata = {
                    "id": f"{category}_{processed + 1:03d}",
                    "category": category,
                    "filename": new_filename,
                    "title": metadata.get('title', f'{category.title()} Wallpaper {processed + 1}'),
                    "width": metadata.get('width', 1080),
                    "height": metadata.get('height', 1920),
                    "file_size": dest_image.stat().st_size,
                    "hash": self.get_image_hash(dest_image),
                    "tags": self.generate_category_tags(category, metadata.get('tags', [])),
                    "download_url": f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/{category}/{new_filename}",
                    "thumbnail_url": f"https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/{category}/{new_filename}",
                    "processed_at": datetime.now().isoformat() + 'Z',
                    "processing_info": {
                        "optimized_for_mobile": True,
                        "original_size": 1080,
                        "compression_quality": 85
                    },
                    "original_metadata": metadata.get('original_metadata', {}),
                    "source": metadata.get('source', 'unknown'),
                    "description": metadata.get('description', f'High-quality {category} wallpaper')
                }
                
                # Save metadata
                with open(dest_json, 'w') as f:
                    json.dump(updated_metadata, f, indent=2)
                
                processed += 1
                logger.info(f"Processed {category} image {processed}/{max_images}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing {image_path.name}: {e}")
        
        return {
            'category': category,
            'processed': processed,
            'duplicates': duplicates,
            'errors': errors
        }
    
    def generate_category_tags(self, category: str, original_tags: List[str]) -> List[str]:
        """Generate appropriate tags for category"""
        base_tags = [category, 'wallpaper', 'hd', 'high resolution', 'mobile']
        
        # Category-specific tags
        category_tags = {
            'nature': ['landscape', 'natural', 'outdoor', 'scenic'],
            'space': ['cosmic', 'universe', 'astronomy', 'galaxy'],
            'abstract': ['geometric', 'modern', 'artistic', 'pattern'],
            'minimal': ['clean', 'simple', 'zen', 'monochrome'],
            'technology': ['tech', 'digital', 'futuristic', 'electronic'],
            'cyberpunk': ['neon', 'futuristic', 'digital', 'dystopian'],
            'gaming': ['game', 'gamer', 'esports', 'console'],
            'anime': ['manga', 'japanese', 'animation', 'kawaii'],
            'cars': ['automotive', 'racing', 'speed', 'vehicle'],
            'sports': ['athletic', 'fitness', 'competition', 'action'],
            'dark': ['gothic', 'mysterious', 'shadow', 'noir'],
            'neon': ['bright', 'colorful', 'synthwave', 'electric'],
            'vintage': ['retro', 'classic', 'nostalgic', 'old-school'],
            'gradient': ['color', 'blend', 'smooth', 'transition']
        }
        
        specific_tags = category_tags.get(category, [])
        
        # Combine all tags and remove duplicates
        all_tags = base_tags + specific_tags + [tag for tag in original_tags if tag not in base_tags]
        return list(dict.fromkeys(all_tags))  # Remove duplicates while preserving order
    
    def process_all_categories_parallel(self, max_images_per_category: int = 50, max_workers: int = 4) -> Dict:
        """Process all categories in parallel"""
        logger.info("Starting parallel category processing...")
        
        # Load existing hashes
        self.load_existing_hashes()
        
        # Categorize approved images
        self.categorize_approved_images()
        
        # Process categories in parallel
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit jobs for categories that have images
            future_to_category = {}
            for category in self.categories:
                if category in self.category_files and self.category_files[category]:
                    future = executor.submit(self.process_single_category, category, max_images_per_category)
                    future_to_category[future] = category
            
            # Collect results
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ {category}: {result['processed']} processed, {result['duplicates']} duplicates, {result['errors']} errors")
                except Exception as e:
                    logger.error(f"❌ {category} failed: {e}")
                    results.append({'category': category, 'processed': 0, 'duplicates': 0, 'errors': 1})
        
        return {
            'total_categories': len(results),
            'total_processed': sum(r['processed'] for r in results),
            'total_duplicates': sum(r['duplicates'] for r in results),
            'total_errors': sum(r['errors'] for r in results),
            'category_results': results
        }

def main():
    parser = argparse.ArgumentParser(description='Process approved images by category in parallel')
    parser.add_argument('--max-images', type=int, default=50, help='Max images per category')
    parser.add_argument('--max-workers', type=int, default=4, help='Max parallel workers')
    parser.add_argument('--repo', default='.', help='Repository path')
    
    args = parser.parse_args()
    
    processor = ParallelCategoryProcessor(args.repo)
    
    start_time = time.time()
    results = processor.process_all_categories_parallel(args.max_images, args.max_workers)
    processing_time = time.time() - start_time
    
    # Print results
    print(f"\n🎉 Parallel Processing Complete!")
    print(f"📊 Total Categories: {results['total_categories']}")
    print(f"✅ Total Processed: {results['total_processed']}")
    print(f"⏭️  Total Duplicates: {results['total_duplicates']}")
    print(f"❌ Total Errors: {results['total_errors']}")
    print(f"⏱️  Processing Time: {processing_time:.1f} seconds")
    
    print(f"\n📁 Category Breakdown:")
    for result in results['category_results']:
        print(f"   {result['category']:12} : {result['processed']:3d} processed, {result['duplicates']:2d} duplicates")
    
    print(f"\n🔄 Next steps:")
    print(f"1. Run: python scripts/generate_index_simple.py --update-all")
    print(f"2. Review wallpapers in wallpapers/ directories")
    print(f"3. Commit changes to Git")

if __name__ == "__main__":
    main()