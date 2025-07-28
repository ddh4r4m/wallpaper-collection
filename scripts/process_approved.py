#!/usr/bin/env python3
"""
Process approved images for wallpaper collection
Handles image optimization, thumbnail generation, and metadata enhancement
"""

import os
import sys
import json
import argparse
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageFilter, ImageEnhance
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_approved.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ApprovedImageProcessor:
    """Process approved images for wallpaper collection"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        # Use WallCraft API structure
        self.collection_dir = self.repo_path / "collection"
        self.wallpapers_dir = self.collection_dir / "wallpapers"
        self.thumbnails_dir = self.collection_dir / "thumbnails"
        self.api_dir = self.collection_dir / "api" / "v1"
        
        # Create directories if they don't exist
        for directory in [self.wallpapers_dir, self.thumbnails_dir, self.api_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Processing settings
        self.settings = {
            'target_width': 1080,
            'target_height': 1920,
            'quality': 85,
            'thumbnail_width': 400,
            'thumbnail_height': 600,
            'thumbnail_quality': 80,
            'optimize': True,
            'progressive': True
        }
        
        # Supported formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # Counter for unique IDs
        self.processed_count = 0
    
    def get_next_number(self, category: str) -> int:
        """Get next available number for this category"""
        category_dir = self.wallpapers_dir / category
        if not category_dir.exists():
            category_dir.mkdir(parents=True, exist_ok=True)
            return 1
        
        existing_files = []
        for ext in ['.jpg', '.jpeg', '.png']:
            existing_files.extend(category_dir.glob(f"*{ext}"))
        
        if not existing_files:
            return 1
        
        # Extract numbers from existing files (WallCraft API uses sequential numbering)
        numbers = []
        for filepath in existing_files:
            try:
                # Extract number from filename like "001.jpg", "002.jpg"
                stem = filepath.stem
                if stem.isdigit():
                    numbers.append(int(stem))
            except (ValueError, IndexError):
                continue
        
        return max(numbers) + 1 if numbers else 1
    
    def generate_file_hash(self, filepath: Path) -> str:
        """Generate SHA-256 hash of file for integrity checking"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]  # First 16 chars
    
    def optimize_for_mobile(self, image: Image.Image) -> Image.Image:
        """Optimize image for mobile wallpaper use"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = image.size
        target_width = self.settings['target_width']
        target_height = self.settings['target_height']
        
        # Calculate aspect ratios
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        # Resize to fit mobile screen while maintaining aspect ratio
        if original_aspect > target_aspect:
            # Image is wider, fit to height
            new_height = target_height
            new_width = int(original_aspect * new_height)
        else:
            # Image is taller, fit to width
            new_width = target_width
            new_height = int(new_width / original_aspect)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # If image is larger than target, crop to fit
        if new_width > target_width or new_height > target_height:
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            resized = resized.crop((left, top, right, bottom))
        
        # Apply subtle sharpening
        resized = resized.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=0))
        
        return resized
    
    def create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create thumbnail from image"""
        # Create thumbnail maintaining aspect ratio
        thumbnail = image.copy()
        thumbnail.thumbnail(
            (self.settings['thumbnail_width'], self.settings['thumbnail_height']),
            Image.Resampling.LANCZOS
        )
        
        # Apply slight enhancement for better preview
        enhancer = ImageEnhance.Sharpness(thumbnail)
        thumbnail = enhancer.enhance(1.1)
        
        return thumbnail
    
    def enhance_metadata(self, original_metadata: Dict, image_path: Path, 
                        optimized_image: Image.Image, category: str, 
                        new_filename: str) -> Dict:
        """Enhance metadata with processing information"""
        
        # Get final image info
        final_width, final_height = optimized_image.size
        file_size = image_path.stat().st_size
        file_hash = self.generate_file_hash(image_path)
        
        # Generate title and tags
        title = self.generate_title(original_metadata, category, new_filename)
        tags = self.generate_tags(original_metadata, category)
        
        # Create enhanced metadata (WallCraft API format)
        enhanced_metadata = {
            'id': f"{category}_{new_filename.split('.')[0]}",
            'category': category,
            'title': title,
            'tags': tags,
            'urls': {
                'raw': f"https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/wallpapers/{category}/{new_filename}",
                'thumb': f"https://media.githubusercontent.com/media/ddh4r4m/wallpaper-collection/main/collection/thumbnails/{category}/{new_filename}"
            },
            'metadata': {
                'dimensions': {
                    'width': final_width,
                    'height': final_height
                },
                'file_size': file_size,
                'format': 'JPEG',
                'added_at': datetime.utcnow().isoformat(),
                'photographer': original_metadata.get('photographer', 'Pinterest Curated')
            }
        }
        
        # Preserve original metadata
        if original_metadata:
            enhanced_metadata['original_metadata'] = original_metadata
            
            # Copy useful fields from original
            if 'photographer' in original_metadata:
                enhanced_metadata['photographer'] = original_metadata['photographer']
            if 'source' in original_metadata:
                enhanced_metadata['source'] = original_metadata['source']
            if 'description' in original_metadata:
                enhanced_metadata['description'] = original_metadata['description']
            if 'created_at' in original_metadata:
                enhanced_metadata['created_at'] = original_metadata['created_at']
            if 'prompt' in original_metadata:
                enhanced_metadata['prompt'] = original_metadata['prompt']
        
        return enhanced_metadata
    
    def generate_title(self, metadata: Dict, category: str, filename: str) -> str:
        """Generate human-readable title"""
        if metadata and 'title' in metadata and metadata['title']:
            return metadata['title']
        
        # Extract number from filename (WallCraft API format: 001.jpg)
        try:
            number = filename.split('.')[0]
            return f"{category.title()} Wallpaper {number}"
        except (IndexError, ValueError):
            return f"{category.title()} Wallpaper"
    
    def generate_tags(self, metadata: Dict, category: str) -> List[str]:
        """Generate tags for the image"""
        tags = [category]
        
        # Add tags from original metadata
        if metadata and 'tags' in metadata:
            original_tags = metadata['tags']
            if isinstance(original_tags, list):
                tags.extend(original_tags)
            elif isinstance(original_tags, str):
                tags.extend([tag.strip() for tag in original_tags.split(',')])
        
        # Add category-specific tags
        category_tags = {
            'abstract': ['abstract', 'geometric', 'pattern', 'modern', 'artistic'],
            'nature': ['nature', 'landscape', 'outdoor', 'scenic', 'natural'],
            'space': ['space', 'cosmic', 'astronomy', 'galaxy', 'universe'],
            'gaming': ['gaming', 'video games', 'digital', 'entertainment'],
            'anime': ['anime', 'manga', 'japanese', 'animation', 'cartoon'],
            'cars': ['cars', 'automotive', 'vehicles', 'transportation'],
            'sports': ['sports', 'athletic', 'fitness', 'competition'],
            'technology': ['technology', 'tech', 'digital', 'modern', 'innovation'],
            'architecture': ['architecture', 'building', 'structure', 'design'],
            'art': ['art', 'artistic', 'creative', 'design', 'visual'],
            'cyberpunk': ['cyberpunk', 'futuristic', 'neon', 'sci-fi', 'digital'],
            'minimal': ['minimal', 'clean', 'simple', 'modern', 'elegant'],
            'dark': ['dark', 'gothic', 'mysterious', 'black', 'shadow'],
            'neon': ['neon', 'bright', 'colorful', 'electric', 'vibrant'],
            'pastel': ['pastel', 'soft', 'gentle', 'light', 'subtle'],
            'vintage': ['vintage', 'retro', 'classic', 'old', 'nostalgic'],
            'gradient': ['gradient', 'color', 'smooth', 'transition', 'blend'],
            'seasonal': ['seasonal', 'holiday', 'celebration', 'festive']
        }
        
        if category in category_tags:
            tags.extend(category_tags[category])
        
        # Add mobile-specific tags
        tags.extend(['mobile', 'wallpaper', 'hd', 'high resolution'])
        
        # Remove duplicates and empty tags
        tags = list(set([tag.strip().lower() for tag in tags if tag.strip()]))
        
        return tags
    
    def process_image(self, image_path: Path, category: str) -> Optional[Dict]:
        """Process a single approved image"""
        logger.info(f"Processing image: {image_path.name}")
        
        # Check if file is supported
        if image_path.suffix.lower() not in self.supported_formats:
            logger.warning(f"Unsupported format: {image_path.suffix}")
            return None
        
        try:
            # Load image
            with Image.open(image_path) as image:
                # Load original metadata
                metadata_path = image_path.with_suffix('.json')
                original_metadata = {}
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        original_metadata = json.load(f)
                
                # Get next number for this category (WallCraft API uses sequential numbering)
                next_number = self.get_next_number(category)
                new_filename = f"{next_number:03d}.jpg"
                
                # Optimize for mobile
                optimized_image = self.optimize_for_mobile(image)
                
                # Save optimized image
                output_path = self.wallpapers_dir / category / new_filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                optimized_image.save(
                    output_path,
                    'JPEG',
                    quality=self.settings['quality'],
                    optimize=self.settings['optimize'],
                    progressive=self.settings['progressive']
                )
                
                # Create and save thumbnail
                thumbnail = self.create_thumbnail(optimized_image)
                thumbnail_path = self.thumbnails_dir / category / new_filename
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                
                thumbnail.save(
                    thumbnail_path,
                    'JPEG',
                    quality=self.settings['thumbnail_quality'],
                    optimize=True
                )
                
                # Generate enhanced metadata
                enhanced_metadata = self.enhance_metadata(
                    original_metadata, output_path, optimized_image, 
                    category, new_filename
                )
                
                # Save metadata
                metadata_output_path = output_path.with_suffix('.json')
                with open(metadata_output_path, 'w') as f:
                    json.dump(enhanced_metadata, f, indent=2)
                
                logger.info(f"Successfully processed: {new_filename}")
                self.processed_count += 1
                
                return enhanced_metadata
                
        except Exception as e:
            logger.error(f"Failed to process {image_path}: {e}")
            return None
    
    def update_category_index(self, category: str, new_images: List[Dict]):
        """Update the category-specific JSON index (WallCraft API format)"""
        category_file = self.api_dir / f"{category}.json"
        
        # Load existing index or create new
        if category_file.exists():
            try:
                with open(category_file, 'r') as f:
                    category_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing category file: {e}")
                category_data = {}
        else:
            category_data = {}
        
        # Initialize WallCraft API structure if needed
        if 'meta' not in category_data:
            category_data['meta'] = {}
        if 'data' not in category_data:
            category_data['data'] = []
        
        # Add new images to data array
        category_data['data'].extend(new_images)
        
        # Update meta information
        category_data['meta'].update({
            'version': '1.0',
            'generated_at': datetime.utcnow().isoformat(),
            'category': category,
            'total_count': len(category_data['data'])
        })
        
        # Save updated index
        with open(category_file, 'w') as f:
            json.dump(category_data, f, indent=2)
        
        logger.info(f"Updated category index: {category} ({category_data['meta']['total_count']} wallpapers)")
    
    def get_category_description(self, category: str) -> str:
        """Get description for category"""
        descriptions = {
            'abstract': 'Abstract AI-generated patterns and shapes',
            'nature': 'Natural landscapes and wildlife photography',
            'space': 'Cosmic scenes, galaxies, and astronomical imagery',
            'gaming': 'Video game screenshots and gaming-related artwork',
            'anime': 'Anime characters and Japanese animation art',
            'cars': 'Automotive photography and car-related imagery',
            'sports': 'Sports photography and athletic imagery',
            'technology': 'Tech gadgets and futuristic technology themes',
            'architecture': 'Buildings, structures, and architectural photography',
            'art': 'Digital art, illustrations, and artistic photography',
            'cyberpunk': 'Futuristic neon cityscapes and cyberpunk aesthetics',
            'minimal': 'Clean, simple, and minimalist designs',
            'dark': 'Dark themes and mysterious atmospheres',
            'neon': 'Neon lights and vibrant electric aesthetics',
            'pastel': 'Soft colors and gentle aesthetic themes',
            'vintage': 'Retro designs and nostalgic themes',
            'gradient': 'Color transitions and gradient effects',
            'seasonal': 'Holiday themes and seasonal imagery'
        }
        return descriptions.get(category, f'{category.title()} themed wallpapers')
    
    def process_directory(self, input_dir: Path, category: str) -> Dict:
        """Process all approved images in a directory"""
        logger.info(f"Processing directory: {input_dir} for category: {category}")
        
        # Find all image files
        image_files = []
        for ext in self.supported_formats:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.warning(f"No image files found in {input_dir}")
            return {'processed': 0, 'failed': 0}
        
        logger.info(f"Found {len(image_files)} images to process")
        
        processed_images = []
        failed_count = 0
        
        # Process each image
        for i, image_path in enumerate(image_files, 1):
            logger.info(f"Processing {i}/{len(image_files)}: {image_path.name}")
            
            result = self.process_image(image_path, category)
            if result:
                processed_images.append(result)
                
                # Remove original file after successful processing
                try:
                    image_path.unlink()
                    metadata_path = image_path.with_suffix('.json')
                    if metadata_path.exists():
                        metadata_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove original file {image_path}: {e}")
            else:
                failed_count += 1
        
        # Update category index
        if processed_images:
            self.update_category_index(category, processed_images)
        
        return {
            'processed': len(processed_images),
            'failed': failed_count,
            'total': len(image_files)
        }

def main():
    parser = argparse.ArgumentParser(description='Process approved images')
    parser.add_argument('--input', required=True, help='Input directory with approved images')
    parser.add_argument('--category', required=True, help='Category for the images')
    parser.add_argument('--repo', default='.', help='Repository root path')
    
    args = parser.parse_args()
    
    # Create processor
    processor = ApprovedImageProcessor(args.repo)
    
    # Process images
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    results = processor.process_directory(input_dir, args.category)
    
    print(f"\n🎉 Processing complete!")
    print(f"📊 Processed: {results['processed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📁 Category: {args.category}")
    print(f"\n🔄 Next steps:")
    print(f"1. Review wallpapers in wallpapers/{args.category}/")
    print(f"2. Check thumbnails in thumbnails/{args.category}/")
    print(f"3. Update master index: python scripts/generate_index.py")
    print(f"4. Commit changes: git add . && git commit -m 'Add {results['processed']} {args.category} wallpapers'")

if __name__ == "__main__":
    main()