#!/usr/bin/env python3
"""
Batch processor for wallpaper collection pipeline
Orchestrates the entire workflow from crawling to final processing
"""

import os
import sys
import json
import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    """Orchestrate the entire wallpaper collection pipeline"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.scripts_dir = self.repo_path / "scripts"
        self.crawl_cache_dir = self.repo_path / "crawl_cache"
        self.review_system_dir = self.repo_path / "review_system"
        
        # Pipeline configuration
        self.config = {
            'crawl_limit_per_source': 50,
            'total_limit_per_category': 100,
            'review_system_output': 'review_system',
            'enable_manual_review_processing': False,
            'cleanup_after_processing': True,
            'update_indexes_after_processing': True
        }
        
        # Source-category mapping (optimized for each category)
        self.source_mapping = {
            'nature': ['pinterest', 'unsplash', 'pexels', 'pixabay'],
            'gaming': ['pinterest', 'wallhaven'],
            'anime': ['pinterest', 'wallhaven'],
            'cars': ['pinterest', 'pexels', 'unsplash'],
            'sports': ['pinterest', 'pexels', 'unsplash'],
            'technology': ['pinterest', 'unsplash', 'pexels', 'wallhaven'],
            'space': ['pinterest', 'unsplash', 'pexels', 'pixabay'],
            'abstract': ['pinterest', 'pixabay', 'unsplash', 'pexels'],
            'architecture': ['pinterest', 'unsplash', 'pexels'],
            'art': ['pinterest', 'pixabay', 'unsplash'],
            'movies': ['pinterest', 'pixabay'],
            'music': ['pinterest', 'unsplash', 'pexels'],
            'cyberpunk': ['pinterest', 'wallhaven'],
            'minimal': ['pinterest', 'unsplash', 'pixabay'],
            'dark': ['pinterest', 'wallhaven'],
            'neon': ['pinterest', 'wallhaven'],
            'pastel': ['pinterest', 'pixabay', 'unsplash'],
            'vintage': ['pinterest', 'pixabay', 'unsplash'],
            'gradient': ['pinterest', 'pixabay', 'unsplash'],
            'seasonal': ['pinterest', 'unsplash', 'pexels']
        }
        
        # Processing statistics
        self.stats = {
            'total_categories': 0,
            'total_crawled': 0,
            'total_approved': 0,
            'total_rejected': 0,
            'total_manual_review': 0,
            'total_processed': 0,
            'processing_time': 0,
            'errors': []
        }
    
    def run_script(self, script_name: str, args: List[str]) -> Dict:
        """Run a Python script with arguments"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Build command
        cmd = [sys.executable, str(script_path)] + args
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully completed: {script_name}")
                return {
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                error_msg = f"Script {script_name} failed with return code {result.returncode}"
                logger.error(error_msg)
                logger.error(f"STDERR: {result.stderr}")
                return {
                    'success': False,
                    'error': error_msg,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Script {script_name} timed out"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Error running {script_name}: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def crawl_category(self, category: str, sources: List[str], limit: int) -> Dict:
        """Crawl images for a specific category"""
        logger.info(f"Starting crawl for category: {category}")
        
        total_images = 0
        all_summaries = []
        
        # Separate Pinterest from other sources since it uses a different scraper
        pinterest_sources = [s for s in sources if s == 'pinterest']
        other_sources = [s for s in sources if s != 'pinterest']
        
        # Handle Pinterest crawling separately
        if pinterest_sources:
            logger.info(f"Running Pinterest scraper for category: {category}")
            pinterest_limit = limit // len(sources) if len(sources) > 1 else min(25, limit)
            
            # Create Pinterest cache directory
            pinterest_cache = self.crawl_cache_dir / "pinterest"
            pinterest_cache.mkdir(parents=True, exist_ok=True)
            
            # Prepare Pinterest scraper arguments
            pinterest_args = [
                '--category', category,
                '--limit', str(pinterest_limit),
                '--output', str(pinterest_cache),
                '--headless'  # Run in headless mode for automation
            ]
            
            # Run Pinterest scraper
            pinterest_result = self.run_script('pinterest_scraper.py', pinterest_args)
            
            if pinterest_result['success']:
                # Check for Pinterest summary
                pinterest_summary_file = pinterest_cache / f"pinterest_{category}_summary.json"
                if pinterest_summary_file.exists():
                    try:
                        with open(pinterest_summary_file, 'r') as f:
                            pinterest_summary = json.load(f)
                            pinterest_count = pinterest_summary.get('high_res_downloaded', 0)
                            total_images += pinterest_count
                            all_summaries.append(pinterest_summary)
                            logger.info(f"Pinterest: {pinterest_count} high-res images downloaded")
                    except Exception as e:
                        logger.warning(f"Failed to parse Pinterest summary: {e}")
            else:
                self.stats['errors'].append(f"Pinterest crawl failed for {category}: {pinterest_result['error']}")
        
        # Handle other sources with the standard crawler
        if other_sources:
            logger.info(f"Running standard crawler for sources: {other_sources}")
            other_limit = limit - total_images if total_images > 0 else limit
            
            if other_limit > 0:
                # Prepare arguments for standard crawler
                args = [
                    '--category', category,
                    '--limit', str(other_limit),
                    '--output', str(self.crawl_cache_dir)
                ]
                
                args.extend(['--sources', ','.join(other_sources)])
                
                # Run standard crawler
                result = self.run_script('crawl_images.py', args)
                
                if result['success']:
                    # Parse crawl results
                    try:
                        # Look for crawl summary
                        summary_file = self.crawl_cache_dir / f"{category}_crawl_summary.json"
                        if summary_file.exists():
                            with open(summary_file, 'r') as f:
                                summary = json.load(f)
                                standard_count = summary.get('total_images', 0)
                                total_images += standard_count
                                all_summaries.append(summary)
                                logger.info(f"Standard sources: {standard_count} images downloaded")
                    except Exception as e:
                        logger.warning(f"Failed to parse standard crawl summary: {e}")
                else:
                    self.stats['errors'].append(f"Standard crawl failed for {category}: {result['error']}")
        
        # Update total stats
        self.stats['total_crawled'] += total_images
        
        # Create combined summary
        combined_summary = {
            'category': category,
            'sources': sources,
            'total_images': total_images,
            'pinterest_images': sum(s.get('high_res_downloaded', 0) for s in all_summaries if s.get('source') == 'pinterest' or 'pinterest' in str(s)),
            'standard_images': sum(s.get('total_images', 0) for s in all_summaries if s.get('source') != 'pinterest' and 'pinterest' not in str(s)),
            'crawl_time': datetime.utcnow().isoformat() + 'Z',
            'details': all_summaries
        }
        
        if total_images > 0:
            return {'success': True, 'summary': combined_summary}
        else:
            return {'success': False, 'error': f"No images downloaded for category {category}"}
    
    def review_images(self) -> Dict:
        """Run AI quality assessment on crawled images"""
        logger.info("Starting image quality assessment")
        
        # Prepare arguments
        args = [
            '--input', str(self.crawl_cache_dir),
            '--output', str(self.review_system_dir)
        ]
        
        # Run reviewer
        result = self.run_script('review_images.py', args)
        
        if result['success']:
            # Parse review results
            try:
                results_file = self.review_system_dir / 'assessment_results.json'
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        assessment_results = json.load(f)
                        summary = assessment_results.get('summary', {})
                        self.stats['total_approved'] += summary.get('approved', 0)
                        self.stats['total_rejected'] += summary.get('rejected', 0)
                        self.stats['total_manual_review'] += summary.get('manual_review', 0)
                        return {'success': True, 'summary': summary}
            except Exception as e:
                logger.warning(f"Failed to parse review results: {e}")
            
            return {'success': True, 'summary': {}}
        else:
            self.stats['errors'].append(f"Review failed: {result['error']}")
            return result
    
    def process_approved_images(self, category: str) -> Dict:
        """Process approved images for a category"""
        logger.info(f"Processing approved images for category: {category}")
        
        # Check if there are approved images
        approved_dir = self.review_system_dir / "approved"
        if not approved_dir.exists() or not any(approved_dir.iterdir()):
            logger.info(f"No approved images found for {category}")
            return {'success': True, 'processed': 0}
        
        # Prepare arguments
        args = [
            '--input', str(approved_dir),
            '--category', category,
            '--repo', str(self.repo_path)
        ]
        
        # Run processor
        result = self.run_script('process_approved.py', args)
        
        if result['success']:
            # Try to extract processed count from output
            try:
                # Look for processing summary in output
                lines = result['stdout'].split('\n')
                for line in lines:
                    if 'Processed:' in line:
                        processed_count = int(line.split('Processed:')[1].split()[0])
                        self.stats['total_processed'] += processed_count
                        return {'success': True, 'processed': processed_count}
            except Exception as e:
                logger.warning(f"Failed to parse processing results: {e}")
            
            return {'success': True, 'processed': 0}
        else:
            self.stats['errors'].append(f"Processing failed for {category}: {result['error']}")
            return result
    
    def process_manual_review(self, category: str) -> Dict:
        """Process manually reviewed images if enabled"""
        if not self.config['enable_manual_review_processing']:
            return {'success': True, 'processed': 0}
        
        logger.info(f"Processing manually reviewed images for category: {category}")
        
        # Check for manually approved images
        manual_approved_dir = self.review_system_dir / "manual_review"
        if not manual_approved_dir.exists():
            return {'success': True, 'processed': 0}
        
        # For now, we'll just log that manual review is needed
        manual_images = list(manual_approved_dir.glob('*'))
        if manual_images:
            logger.info(f"Found {len(manual_images)} images requiring manual review")
            print(f"\n⚠️  Manual review required for {len(manual_images)} images in {manual_approved_dir}")
            print("Please review these images and move approved ones to review_system/approved/")
        
        return {'success': True, 'processed': 0}
    
    def update_indexes(self) -> Dict:
        """Update master index after processing"""
        if not self.config['update_indexes_after_processing']:
            return {'success': True}
        
        logger.info("Updating master index")
        
        # Run index generator
        result = self.run_script('generate_index.py', ['--update-all'])
        
        if not result['success']:
            self.stats['errors'].append(f"Index update failed: {result['error']}")
        
        return result
    
    def cleanup_temp_files(self):
        """Clean up temporary files after processing"""
        if not self.config['cleanup_after_processing']:
            return
        
        logger.info("Cleaning up temporary files")
        
        try:
            # Clear crawl cache
            if self.crawl_cache_dir.exists():
                for item in self.crawl_cache_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
            
            # Clear review system (but keep structure)
            for subdir in ['approved', 'rejected', 'manual_review']:
                review_subdir = self.review_system_dir / subdir
                if review_subdir.exists():
                    for item in review_subdir.iterdir():
                        if item.is_file():
                            item.unlink()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def process_categories(self, categories: List[str], sources: List[str] = None) -> Dict:
        """Process multiple categories through the entire pipeline"""
        logger.info(f"Starting batch processing for categories: {', '.join(categories)}")
        
        start_time = time.time()
        self.stats['total_categories'] = len(categories)
        
        # Process each category
        for i, category in enumerate(categories, 1):
            logger.info(f"Processing category {i}/{len(categories)}: {category}")
            
            # Determine sources for this category
            category_sources = sources if sources else self.source_mapping.get(category, ['unsplash', 'pexels'])
            
            # Step 1: Crawl images
            crawl_result = self.crawl_category(
                category, 
                category_sources, 
                self.config['total_limit_per_category']
            )
            
            if not crawl_result['success']:
                logger.error(f"Crawl failed for {category}, skipping to next category")
                continue
            
            # Step 2: Review images (only if we have crawled images)
            if self.stats['total_crawled'] > 0:
                review_result = self.review_images()
                
                if not review_result['success']:
                    logger.error(f"Review failed for {category}, skipping to next category")
                    continue
                
                # Step 3: Process approved images
                process_result = self.process_approved_images(category)
                
                if not process_result['success']:
                    logger.error(f"Processing failed for {category}")
                    continue
                
                # Step 4: Handle manual review (optional)
                self.process_manual_review(category)
            
            logger.info(f"Completed processing for category: {category}")
        
        # Step 5: Update indexes
        self.update_indexes()
        
        # Step 6: Cleanup
        self.cleanup_temp_files()
        
        # Calculate final statistics
        self.stats['processing_time'] = time.time() - start_time
        
        return {
            'success': True,
            'stats': self.stats
        }
    
    def generate_report(self) -> str:
        """Generate a processing report"""
        report = f\"\"\"\n🎉 Batch Processing Complete!\n\n📊 Statistics:\n   Categories processed: {self.stats['total_categories']}\n   Images crawled: {self.stats['total_crawled']}\n   Images approved: {self.stats['total_approved']}\n   Images rejected: {self.stats['total_rejected']}\n   Manual review needed: {self.stats['total_manual_review']}\n   Images processed: {self.stats['total_processed']}\n   Processing time: {self.stats['processing_time']:.1f} seconds\n\n\"\"\"\n        \n        if self.stats['errors']:\n            report += f\"❌ Errors ({len(self.stats['errors'])}):\\n\"\n            for error in self.stats['errors']:\n                report += f\"   - {error}\\n\"\n        else:\n            report += \"✅ No errors encountered\\n\"\n        \n        report += f\"\"\"\n🔄 Next steps:\n1. Review wallpapers in wallpapers/ directories\n2. Check thumbnails in thumbnails/ directories\n3. Commit changes: git add . && git commit -m 'Add {self.stats["total_processed"]} wallpapers'\n4. Push to repository: git push origin main\n\"\"\"\n        \n        if self.stats['total_manual_review'] > 0:\n            report += f\"\\n⚠️  Manual review required for {self.stats['total_manual_review']} images\\n\"\n            report += \"   Check review_system/manual_review/ directory\\n\"\n        \n        return report

def main():
    parser = argparse.ArgumentParser(description='Batch process wallpaper collection pipeline')
    parser.add_argument('--categories', required=True, help='Comma-separated list of categories')
    parser.add_argument('--sources', help='Comma-separated list of sources (optional)')
    parser.add_argument('--limit', type=int, default=100, help='Max images per category')
    parser.add_argument('--repo', default='.', help='Repository root path')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup after processing')
    parser.add_argument('--no-index-update', action='store_true', help='Skip index update')
    parser.add_argument('--enable-manual-review', action='store_true', help='Enable manual review processing')
    
    args = parser.parse_args()
    
    # Parse categories
    categories = [cat.strip() for cat in args.categories.split(',')]
    
    # Parse sources
    sources = None
    if args.sources:
        sources = [src.strip() for src in args.sources.split(',')]
    
    # Create processor
    processor = BatchProcessor(args.repo)
    
    # Update configuration
    processor.config['total_limit_per_category'] = args.limit
    processor.config['cleanup_after_processing'] = not args.no_cleanup
    processor.config['update_indexes_after_processing'] = not args.no_index_update
    processor.config['enable_manual_review_processing'] = args.enable_manual_review
    
    # Process categories
    result = processor.process_categories(categories, sources)
    
    # Generate and display report
    report = processor.generate_report()
    print(report)
    
    # Save report to file
    report_file = Path(args.repo) / 'batch_processing_report.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()