#!/usr/bin/env python3
"""
AI-powered image quality assessment system for wallpaper collection
Uses multiple metrics to evaluate image quality and appropriateness
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageStat
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('review_images.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageQualityAssessor:
    """AI-powered image quality assessment system"""
    
    def __init__(self, output_dir: str = "review_system"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output subdirectories
        self.approved_dir = self.output_dir / "approved"
        self.rejected_dir = self.output_dir / "rejected"
        self.manual_review_dir = self.output_dir / "manual_review"
        
        for directory in [self.approved_dir, self.rejected_dir, self.manual_review_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Quality thresholds
        self.thresholds = {
            'auto_approve': 8.0,    # Auto-approve if score >= 8.0
            'auto_reject': 4.0,     # Auto-reject if score < 4.0
            'min_resolution': (800, 600),  # Minimum resolution
            'max_file_size': 10 * 1024 * 1024,  # 10MB max file size
            'min_aspect_ratio': 0.3,  # Minimum aspect ratio (width/height)
            'max_aspect_ratio': 3.0   # Maximum aspect ratio
        }
        
        # Assessment weights
        self.weights = {
            'sharpness': 0.25,
            'contrast': 0.15,
            'brightness': 0.10,
            'color_quality': 0.15,
            'composition': 0.15,
            'technical_quality': 0.20
        }
        
        # Results tracking
        self.results = {
            'approved': [],
            'rejected': [],
            'manual_review': []
        }
    
    def load_image(self, image_path: Path) -> Tuple[Optional[np.ndarray], Optional[Image.Image]]:
        """Load image using both OpenCV and PIL"""
        try:
            # Load with OpenCV for analysis
            cv_image = cv2.imread(str(image_path))
            if cv_image is None:
                return None, None
            
            # Load with PIL for metadata
            pil_image = Image.open(image_path)
            
            return cv_image, pil_image
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None, None
    
    def assess_sharpness(self, image: np.ndarray) -> float:
        """Assess image sharpness using Laplacian variance"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            # Normalize to 0-10 scale
            # Values above 100 are considered sharp
            score = min(10.0, variance / 20.0)
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error assessing sharpness: {e}")
            return 0.0
    
    def assess_contrast(self, image: np.ndarray) -> float:
        """Assess image contrast using standard deviation"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            std_dev = np.std(gray)
            
            # Normalize to 0-10 scale
            # Good contrast typically has std_dev > 50
            score = min(10.0, std_dev / 8.0)
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error assessing contrast: {e}")
            return 0.0
    
    def assess_brightness(self, image: np.ndarray) -> float:
        """Assess image brightness distribution"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            # Optimal brightness is around 127 (middle of 0-255)
            # Score decreases as brightness deviates from optimal
            deviation = abs(mean_brightness - 127)
            score = 10.0 - (deviation / 12.7)
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error assessing brightness: {e}")
            return 0.0
    
    def assess_color_quality(self, pil_image: Image.Image) -> float:
        """Assess color quality and saturation"""
        try:
            # Convert to HSV to analyze saturation
            hsv_image = pil_image.convert('HSV')
            stat = ImageStat.Stat(hsv_image)
            
            # Get saturation statistics
            saturation_mean = stat.mean[1]  # Saturation channel
            saturation_std = stat.stddev[1]
            
            # Good images have moderate saturation with some variation
            saturation_score = min(10.0, saturation_mean / 25.5)
            variation_score = min(10.0, saturation_std / 25.5)
            
            # Combine scores
            score = (saturation_score + variation_score) / 2
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error assessing color quality: {e}")
            return 0.0
    
    def assess_composition(self, image: np.ndarray) -> float:
        """Assess image composition using edge detection"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Count edge pixels
            edge_pixels = np.sum(edges > 0)
            total_pixels = edges.shape[0] * edges.shape[1]
            edge_ratio = edge_pixels / total_pixels
            
            # Good composition has moderate edge density
            # Too many edges = noise, too few = boring
            optimal_ratio = 0.05  # 5% edge pixels
            deviation = abs(edge_ratio - optimal_ratio)
            score = 10.0 - (deviation * 100)
            
            return max(0.0, min(10.0, score))
            
        except Exception as e:
            logger.error(f"Error assessing composition: {e}")
            return 0.0
    
    def assess_technical_quality(self, image: np.ndarray, pil_image: Image.Image) -> float:
        """Assess technical aspects like noise and artifacts"""
        try:
            # Check image resolution
            height, width = image.shape[:2]
            resolution_score = 10.0 if width >= 1080 and height >= 1920 else 5.0
            
            # Check for noise using blur detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_level = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
            
            # Lower noise is better
            noise_score = max(0.0, 10.0 - noise_level / 2.0)
            
            # Check file format and quality
            format_score = 10.0 if pil_image.format in ['JPEG', 'PNG', 'WEBP'] else 5.0
            
            # Combine technical scores
            score = (resolution_score + noise_score + format_score) / 3
            return max(0.0, min(10.0, score))
            
        except Exception as e:
            logger.error(f"Error assessing technical quality: {e}")
            return 0.0
    
    def check_basic_requirements(self, image_path: Path, pil_image: Image.Image) -> Tuple[bool, List[str]]:
        """Check basic requirements for wallpaper images"""
        issues = []
        
        # Check file size
        file_size = image_path.stat().st_size
        if file_size > self.thresholds['max_file_size']:
            issues.append(f"File too large: {file_size / (1024*1024):.1f}MB")
        
        # Check resolution
        width, height = pil_image.size
        min_width, min_height = self.thresholds['min_resolution']
        if width < min_width or height < min_height:
            issues.append(f"Resolution too low: {width}x{height}")
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < self.thresholds['min_aspect_ratio'] or aspect_ratio > self.thresholds['max_aspect_ratio']:
            issues.append(f"Aspect ratio out of range: {aspect_ratio:.2f}")
        
        # Check for mobile optimization (portrait preferred)
        if height < width:  # Landscape
            issues.append("Landscape orientation (portrait preferred for mobile)")
        
        return len(issues) == 0, issues
    
    def detect_watermarks(self, image: np.ndarray) -> float:
        """Detect potential watermarks or logos"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check corners for watermarks (common locations)
            h, w = gray.shape
            corner_size = min(h, w) // 10
            
            corners = [
                gray[0:corner_size, 0:corner_size],  # Top-left
                gray[0:corner_size, w-corner_size:w],  # Top-right
                gray[h-corner_size:h, 0:corner_size],  # Bottom-left
                gray[h-corner_size:h, w-corner_size:w]  # Bottom-right
            ]
            
            # Check for text-like patterns in corners
            watermark_score = 0.0
            for corner in corners:
                # Use template matching or edge detection
                edges = cv2.Canny(corner, 50, 150)
                edge_density = np.sum(edges > 0) / (corner.shape[0] * corner.shape[1])
                
                # High edge density in corners suggests watermarks
                if edge_density > 0.1:
                    watermark_score += 2.5
            
            # Return penalty score (lower is better)
            return min(10.0, watermark_score)
            
        except Exception as e:
            logger.error(f"Error detecting watermarks: {e}")
            return 0.0
    
    def assess_mobile_suitability(self, pil_image: Image.Image) -> float:
        """Assess how suitable the image is for mobile wallpaper"""
        try:
            width, height = pil_image.size
            aspect_ratio = width / height
            
            # Mobile wallpapers work best in portrait orientation
            if aspect_ratio < 1.0:  # Portrait
                orientation_score = 10.0
            elif aspect_ratio == 1.0:  # Square
                orientation_score = 7.0
            else:  # Landscape
                orientation_score = 3.0
            
            # Check if resolution is mobile-optimized
            if width >= 1080 and height >= 1920:
                resolution_score = 10.0
            elif width >= 720 and height >= 1280:
                resolution_score = 7.0
            else:
                resolution_score = 4.0
            
            # Combine scores
            score = (orientation_score + resolution_score) / 2
            return max(0.0, min(10.0, score))
            
        except Exception as e:
            logger.error(f"Error assessing mobile suitability: {e}")
            return 0.0
    
    def calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score"""
        total_score = 0.0
        for metric, score in scores.items():
            weight = self.weights.get(metric, 0.0)
            total_score += score * weight
        
        return min(10.0, total_score)
    
    def assess_image(self, image_path: Path) -> Dict:
        """Perform comprehensive image assessment"""
        logger.info(f"Assessing image: {image_path.name}")
        
        # Load image
        cv_image, pil_image = self.load_image(image_path)
        if cv_image is None or pil_image is None:
            return {
                'path': str(image_path),
                'status': 'error',
                'error': 'Failed to load image',
                'overall_score': 0.0
            }
        
        # Check basic requirements
        passes_basic, issues = self.check_basic_requirements(image_path, pil_image)
        
        # Perform quality assessments
        scores = {
            'sharpness': self.assess_sharpness(cv_image),
            'contrast': self.assess_contrast(cv_image),
            'brightness': self.assess_brightness(cv_image),
            'color_quality': self.assess_color_quality(pil_image),
            'composition': self.assess_composition(cv_image),
            'technical_quality': self.assess_technical_quality(cv_image, pil_image)
        }
        
        # Additional assessments
        watermark_penalty = self.detect_watermarks(cv_image)
        mobile_suitability = self.assess_mobile_suitability(pil_image)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(scores)
        
        # Apply penalties
        overall_score -= watermark_penalty * 0.1
        overall_score = max(0.0, overall_score)
        
        # Add mobile suitability bonus
        overall_score += mobile_suitability * 0.05
        overall_score = min(10.0, overall_score)
        
        # Determine status
        if not passes_basic:
            status = 'rejected'
            reason = f"Basic requirements failed: {'; '.join(issues)}"
        elif overall_score >= self.thresholds['auto_approve']:
            status = 'approved'
            reason = 'High quality image'
        elif overall_score < self.thresholds['auto_reject']:
            status = 'rejected'
            reason = 'Low quality image'
        else:
            status = 'manual_review'
            reason = 'Requires manual assessment'
        
        # Load metadata if available
        metadata_path = image_path.with_suffix('.json')
        metadata = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata for {image_path}: {e}")
        
        return {
            'path': str(image_path),
            'filename': image_path.name,
            'status': status,
            'reason': reason,
            'overall_score': round(overall_score, 2),
            'detailed_scores': {k: round(v, 2) for k, v in scores.items()},
            'watermark_penalty': round(watermark_penalty, 2),
            'mobile_suitability': round(mobile_suitability, 2),
            'basic_requirements': passes_basic,
            'issues': issues,
            'metadata': metadata,
            'assessed_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def move_image(self, image_path: Path, assessment: Dict):
        """Move image to appropriate directory based on assessment"""
        status = assessment['status']
        
        if status == 'approved':
            dest_dir = self.approved_dir
        elif status == 'rejected':
            dest_dir = self.rejected_dir
        elif status == 'manual_review':
            dest_dir = self.manual_review_dir
        else:
            logger.error(f"Unknown status: {status}")
            return
        
        # Move image file
        dest_path = dest_dir / image_path.name
        try:
            shutil.move(str(image_path), str(dest_path))
            
            # Move metadata file if it exists
            metadata_path = image_path.with_suffix('.json')
            if metadata_path.exists():
                dest_metadata_path = dest_dir / metadata_path.name
                shutil.move(str(metadata_path), str(dest_metadata_path))
            
            # Save assessment result
            assessment_path = dest_dir / f"{image_path.stem}_assessment.json"
            with open(assessment_path, 'w') as f:
                json.dump(assessment, f, indent=2)
            
            logger.info(f"Moved {image_path.name} to {status} directory")
            
        except Exception as e:
            logger.error(f"Failed to move {image_path}: {e}")
    
    def process_directory(self, input_dir: Path, metrics: List[str] = None) -> Dict:
        """Process all images in a directory"""
        logger.info(f"Processing directory: {input_dir}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.warning(f"No image files found in {input_dir}")
            return {'total': 0, 'approved': 0, 'rejected': 0, 'manual_review': 0}
        
        logger.info(f"Found {len(image_files)} images to process")
        
        # Process each image
        for i, image_path in enumerate(image_files, 1):
            logger.info(f"Processing {i}/{len(image_files)}: {image_path.name}")
            
            assessment = self.assess_image(image_path)
            
            # Move image to appropriate directory
            self.move_image(image_path, assessment)
            
            # Track results
            status = assessment['status']
            if status in self.results:
                self.results[status].append(assessment)
        
        # Generate summary report
        summary = {
            'total_processed': len(image_files),
            'approved': len(self.results['approved']),
            'rejected': len(self.results['rejected']),
            'manual_review': len(self.results['manual_review']),
            'processing_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Save detailed results
        results_file = self.output_dir / 'assessment_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'summary': summary,
                'detailed_results': self.results
            }, f, indent=2)
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='AI image quality assessment')
    parser.add_argument('--input', required=True, help='Input directory with images')
    parser.add_argument('--output', default='review_system', help='Output directory')
    parser.add_argument('--metrics', help='Specific metrics to use (comma-separated)')
    
    args = parser.parse_args()
    
    # Parse metrics
    metrics = None
    if args.metrics:
        metrics = [m.strip() for m in args.metrics.split(',')]
    
    # Create assessor
    assessor = ImageQualityAssessor(args.output)
    
    # Process images
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    summary = assessor.process_directory(input_dir, metrics)
    
    print(f"\n🎉 Assessment complete!")
    print(f"📊 Total processed: {summary['total_processed']}")
    print(f"✅ Approved: {summary['approved']}")
    print(f"❌ Rejected: {summary['rejected']}")
    print(f"🔍 Manual review: {summary['manual_review']}")
    print(f"\n📁 Results saved to: {args.output}")
    print(f"\n🔄 Next steps:")
    print(f"1. Review manually flagged images in {args.output}/manual_review/")
    print(f"2. Move approved images to {args.output}/approved/")
    print(f"3. Run: python scripts/process_approved.py")

if __name__ == "__main__":
    main()