#!/usr/bin/env python3
"""
Select Best 40 Sports Wallpapers from Pinterest Collection
Quality-based selection with sport diversity
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SportsSelectorAgent:
    """Select best 40 sports wallpapers based on quality and diversity"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sport categories for diversity
        self.sport_categories = {
            'football': [],
            'basketball': [],
            'soccer': [],
            'tennis': [],
            'golf': [],
            'baseball': [],
            'general': []
        }
        
        # Target distribution (40 total)
        self.target_distribution = {
            'football': 6,
            'basketball': 6,
            'soccer': 6,
            'tennis': 4,
            'baseball': 4,
            'golf': 4,
            'general': 10
        }
    
    def load_and_analyze_images(self) -> List[Dict]:
        """Load all images and their metadata for analysis"""
        images = []
        
        for jpg_file in self.source_dir.glob("*.jpg"):
            json_file = jpg_file.with_suffix('.json')
            
            if not json_file.exists():
                logger.warning(f"No metadata for {jpg_file.name}")
                continue
            
            try:
                with open(json_file, 'r') as f:
                    metadata = json.load(f)
                
                # Calculate quality score
                file_size = jpg_file.stat().st_size
                quality_score = self.calculate_quality_score(metadata, file_size)
                
                image_info = {
                    'filename': jpg_file.name,
                    'json_filename': json_file.name,
                    'sport_type': metadata.get('sport_type', 'general'),
                    'file_size': file_size,
                    'quality_score': quality_score,
                    'metadata': metadata
                }
                
                images.append(image_info)
                
            except Exception as e:
                logger.error(f"Error processing {jpg_file.name}: {e}")
        
        logger.info(f"Loaded {len(images)} images for analysis")
        return images
    
    def calculate_quality_score(self, metadata: Dict, file_size: int) -> float:
        """Calculate quality score for an image"""
        score = 0.0
        
        # File size score (prefer 150KB - 800KB range)
        if 150000 <= file_size <= 800000:
            score += 3.0
        elif 100000 <= file_size <= 150000:
            score += 2.0
        elif file_size > 800000:
            score += 1.5
        else:
            score += 1.0
        
        # Query relevance (better search terms get higher scores)
        query = metadata.get('query', '').lower()
        if 'mobile' in query or 'phone' in query:
            score += 2.0
        if 'hd' in query or 'wallpaper' in query:
            score += 1.5
        if 'motivation' in query or 'action' in query:
            score += 1.0
        
        # Sport-specific bonus
        sport_type = metadata.get('sport_type', 'general')
        if sport_type != 'general':
            score += 1.0
        
        # Tag quality
        tags = metadata.get('tags', [])
        score += min(len(tags) * 0.2, 1.0)
        
        return score
    
    def categorize_images(self, images: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize images by sport type"""
        categorized = {cat: [] for cat in self.sport_categories.keys()}
        
        for image in images:
            sport_type = image['sport_type']
            if sport_type in categorized:
                categorized[sport_type].append(image)
            else:
                categorized['general'].append(image)
        
        # Sort each category by quality score
        for category in categorized:
            categorized[category].sort(key=lambda x: x['quality_score'], reverse=True)
        
        return categorized
    
    def select_best_40(self, categorized_images: Dict[str, List[Dict]]) -> List[Dict]:
        """Select best 40 images with sport diversity"""
        selected = []
        
        # First pass: Select based on target distribution
        for sport, target_count in self.target_distribution.items():
            available = categorized_images.get(sport, [])
            selected_count = min(target_count, len(available))
            
            selected.extend(available[:selected_count])
            logger.info(f"Selected {selected_count}/{target_count} {sport} images")
        
        # Second pass: Fill remaining slots with highest quality images
        current_count = len(selected)
        remaining_slots = 40 - current_count
        
        if remaining_slots > 0:
            # Get all remaining images
            remaining_images = []
            for sport, images in categorized_images.items():
                used_count = self.target_distribution.get(sport, 0)
                remaining_images.extend(images[used_count:])
            
            # Sort by quality and take the best
            remaining_images.sort(key=lambda x: x['quality_score'], reverse=True)
            selected.extend(remaining_images[:remaining_slots])
            
            logger.info(f"Added {min(remaining_slots, len(remaining_images))} additional high-quality images")
        
        # Final selection of exactly 40
        selected.sort(key=lambda x: x['quality_score'], reverse=True)
        final_selection = selected[:40]
        
        logger.info(f"Final selection: {len(final_selection)} images")
        return final_selection
    
    def copy_selected_images(self, selected_images: List[Dict]) -> Dict:
        """Copy selected images to output directory"""
        sport_counts = {cat: 0 for cat in self.sport_categories.keys()}
        copied_files = []
        
        for i, image in enumerate(selected_images, 1):
            # Create new filename
            sport_type = image['sport_type']
            original_filename = image['filename']
            new_filename = f"sports_{i:03d}_{sport_type}_{original_filename.split('_')[-1]}"
            
            # Copy image file
            source_jpg = self.source_dir / original_filename
            dest_jpg = self.output_dir / new_filename
            shutil.copy2(source_jpg, dest_jpg)
            
            # Copy and update JSON metadata
            source_json = self.source_dir / image['json_filename']
            dest_json = dest_jpg.with_suffix('.json')
            
            # Update metadata
            metadata = image['metadata'].copy()
            metadata['final_selection_rank'] = i
            metadata['quality_score'] = image['quality_score']
            metadata['selection_reason'] = f"Top 40 quality selection - {sport_type}"
            
            with open(dest_json, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            sport_counts[sport_type] += 1
            copied_files.append({
                'rank': i,
                'filename': new_filename,
                'sport': sport_type,
                'quality_score': image['quality_score'],
                'file_size': image['file_size']
            })
            
            logger.info(f"Copied #{i}: {new_filename} ({sport_type}, quality: {image['quality_score']:.2f})")
        
        return {
            'sport_distribution': sport_counts,
            'copied_files': copied_files
        }
    
    def create_final_report(self, selection_results: Dict, total_processed: int):
        """Create comprehensive final report"""
        report = {
            'agent': 'Agent 1 - Pinterest Sports Scraper Final Selection',
            'mission': 'Select exactly 40 high-quality sports wallpapers from Pinterest',
            'source_images': total_processed,
            'target_count': 40,
            'actual_selected': len(selection_results['copied_files']),
            'success': len(selection_results['copied_files']) == 40,
            
            'sport_distribution': selection_results['sport_distribution'],
            
            'quality_criteria': [
                'File size optimization (150KB - 800KB preferred)',
                'Search query relevance (mobile, HD, wallpaper terms)',
                'Sport categorization bonus',
                'Tag completeness',
                'Overall quality scoring'
            ],
            
            'diversity_strategy': {
                'target_distribution': self.target_distribution,
                'actual_distribution': selection_results['sport_distribution']
            },
            
            'top_10_images': selection_results['copied_files'][:10],
            
            'file_stats': {
                'avg_file_size': sum(f['file_size'] for f in selection_results['copied_files']) // len(selection_results['copied_files']),
                'min_file_size': min(f['file_size'] for f in selection_results['copied_files']),
                'max_file_size': max(f['file_size'] for f in selection_results['copied_files']),
                'avg_quality_score': sum(f['quality_score'] for f in selection_results['copied_files']) / len(selection_results['copied_files'])
            },
            
            'output_directory': str(self.output_dir),
            'mission_status': 'COMPLETED ✅' if len(selection_results['copied_files']) == 40 else 'PARTIAL ⚠️'
        }
        
        report_file = self.output_dir / 'final_selection_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    # Paths
    source_dir = "crawl_cache/pinterest/sports_40"
    output_dir = "crawl_cache/pinterest/sports_40_final"
    
    # Create selector
    selector = SportsSelectorAgent(source_dir, output_dir)
    
    try:
        print("🏈 AGENT 1 FINAL SELECTION - TOP 40 SPORTS WALLPAPERS")
        print("=" * 60)
        
        # Load and analyze all images
        images = selector.load_and_analyze_images()
        
        if len(images) < 40:
            print(f"❌ Only {len(images)} images available, need at least 40")
            return
        
        # Categorize by sport
        categorized = selector.categorize_images(images)
        
        print(f"\n📊 Available Images by Sport:")
        for sport, imgs in categorized.items():
            if imgs:
                print(f"  {sport.title()}: {len(imgs)} images")
        
        # Select best 40
        selected = selector.select_best_40(categorized)
        
        # Copy selected images
        results = selector.copy_selected_images(selected)
        
        # Create final report
        report = selector.create_final_report(results, len(images))
        
        print(f"\n🎯 MISSION ACCOMPLISHED!")
        print(f"✅ Selected: {len(selected)}/40 high-quality sports wallpapers")
        print(f"📁 Output: {output_dir}")
        
        print(f"\n🏆 Final Sport Distribution:")
        for sport, count in results['sport_distribution'].items():
            if count > 0:
                print(f"  {sport.title()}: {count} images")
        
        print(f"\n📊 Quality Statistics:")
        stats = report['file_stats']
        print(f"  Average file size: {stats['avg_file_size']:,} bytes")
        print(f"  Average quality score: {stats['avg_quality_score']:.2f}/10")
        
        print(f"\n🏅 Top 5 Selected Images:")
        for i, img in enumerate(results['copied_files'][:5], 1):
            print(f"  {i}. {img['filename']} ({img['sport']}, score: {img['quality_score']:.2f})")
        
        print(f"\n📋 Final Report: {output_dir}/final_selection_report.json")
        print(f"🎉 EXACTLY 40 SPORTS WALLPAPERS READY FOR COLLECTION!")
        
    except Exception as e:
        logger.error(f"Selection failed: {e}")
        print(f"❌ Selection failed: {e}")

if __name__ == "__main__":
    main()