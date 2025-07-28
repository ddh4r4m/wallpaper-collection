#!/usr/bin/env python3
"""
Enhanced Basketball Scraper - Agent 3 (Phase 2)
Complete the basketball collection to exactly 40 images
Adding more reliable sources and enhanced basketball content
"""

import requests
import json
import hashlib
import time
import os
from datetime import datetime, timezone
import random
from typing import List, Dict, Set

class EnhancedBasketballScraper:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        })
        
        # Load existing images to avoid duplicates
        self.existing_images = self.load_existing_images()
        self.target_count = 40
        self.current_count = len(self.existing_images)
        self.needed_count = self.target_count - self.current_count
        
        print(f"Current collection: {self.current_count} images")
        print(f"Need {self.needed_count} more basketball images")
        
        # Enhanced basketball URLs from multiple reliable sources
        self.basketball_urls = [
            # NBA official and sports sites
            "https://cdn.nba.com/headshots/nba/latest/1040x760/201939.png",
            "https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png",
            "https://cdn.nba.com/headshots/nba/latest/1040x760/977.png",
            
            # Sports illustrated and ESPN
            "https://www.si.com/.image/c_fill%2Ccs_srgb%2Cfl_progressive%2Ch_1200%2Cq_auto:good%2Cw_1200/MTY4NDYwNTQ1ODc5OTAwNDg1/basketball-court.jpg",
            
            # High-quality basketball stock photos
            "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1546519638-68e109498ffc?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1577223625816-7546f13df25d?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1594736797933-d0f7f6d0f3b1?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1559827260-dc66d52bef19?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?q=80&w=1080&h=1920&fit=crop",
            
            # Pexels basketball collection
            "https://images.pexels.com/photos/1752757/pexels-photo-1752757.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/2291004/pexels-photo-2291004.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/358042/pexels-photo-358042.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/1187079/pexels-photo-1187079.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/1552252/pexels-photo-1552252.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/2104152/pexels-photo-2104152.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/1263348/pexels-photo-1263348.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/2250799/pexels-photo-2250799.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            
            # Additional basketball wallpaper sources
            "https://wallpapershome.com/images/wallpapers/basketball-1920x1080-4k-5k-sport-11662.jpg",
            "https://wallpapershome.com/images/wallpapers/basketball-1920x1080-sport-nba-736.jpg",
            "https://wallpapershome.com/images/wallpapers/basketball-court-1920x1080-4k-sport-15785.jpg",
            
            # Basketball equipment and courts
            "https://images.pexels.com/photos/1308713/pexels-photo-1308713.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/3683121/pexels-photo-3683121.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/8007153/pexels-photo-8007153.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            "https://images.pexels.com/photos/2116469/pexels-photo-2116469.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop",
            
            # More Unsplash basketball content
            "https://images.unsplash.com/photo-1608245449230-4ac19066d2d0?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1515523110800-9415d13b84a8?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1627627256672-027a4613d028?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1606107557583-c9ab4a4d3eb5?q=80&w=1080&h=1920&fit=crop",
            "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?q=80&w=1080&h=1920&fit=crop",
        ]
        
        # Add some programmatically generated URLs
        self.add_generated_urls()
        
        # Shuffle for randomization
        random.shuffle(self.basketball_urls)
        
        self.downloaded_images = []
        self.failed_urls = set()

    def load_existing_images(self) -> List[str]:
        """Load existing images to avoid duplicates"""
        existing = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.endswith('.jpg'):
                    existing.append(file)
        return existing

    def add_generated_urls(self):
        """Add programmatically generated basketball URLs"""
        
        # Basketball-specific image IDs for different platforms
        basketball_patterns = [
            # More Unsplash basketball images
            "photo-1574623452334-1e0ac2b3ccb4",
            "photo-1594736797933-d0f7f6d0f3b1", 
            "photo-1609800738916-ff3d5ca75e3d",
            "photo-1517649763962-0c623066013b",
            "photo-1612198188060-c7c2a3b66eae",
            
            # Pexels basketball collection
            "photos/4019409/pexels-photo-4019409.jpeg",
            "photos/3621104/pexels-photo-3621104.jpeg",
            "photos/2116932/pexels-photo-2116932.jpeg",
            "photos/1263348/pexels-photo-1263348.jpeg",
        ]
        
        # Generate Unsplash URLs
        for photo_id in basketball_patterns[:5]:
            if photo_id.startswith("photo-"):
                url = f"https://images.unsplash.com/{photo_id}?q=80&w=1080&h=1920&fit=crop"
                self.basketball_urls.append(url)
        
        # Generate Pexels URLs  
        for photo_path in basketball_patterns[5:]:
            if photo_path.startswith("photos/"):
                url = f"https://images.pexels.com/{photo_path}?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop"
                self.basketball_urls.append(url)

    def calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate hash for duplicate detection"""
        return hashlib.md5(image_data).hexdigest()

    def validate_basketball_image(self, image_data: bytes) -> bool:
        """Enhanced basketball image validation"""
        try:
            from PIL import Image
            import io
            
            # Size validation
            if len(image_data) < 5000:  # Too small
                return False
            
            if len(image_data) > 10 * 1024 * 1024:  # Too large (>10MB)
                return False
            
            # Try to open as image
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
            
            # Minimum resolution
            if width < 600 or height < 600:
                return False
            
            # Aspect ratio check
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 4.0:  # Too extreme
                return False
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def download_basketball_image(self, url: str, attempt: int = 1) -> bool:
        """Enhanced download with retry logic"""
        if url in self.failed_urls:
            return False
        
        try:
            print(f"Downloading basketball image {self.current_count + len(self.downloaded_images) + 1}/40: {url[:80]}...")
            
            response = self.session.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                image_data = response.content
                
                # Validate image
                if not self.validate_basketball_image(image_data):
                    print(f"❌ Validation failed")
                    return False
                
                # Check hash for duplicates
                image_hash = self.calculate_image_hash(image_data)
                
                # Check against existing files
                existing_hashes = []
                for existing_file in self.existing_images:
                    try:
                        existing_path = os.path.join(self.output_dir, existing_file)
                        with open(existing_path, 'rb') as f:
                            existing_hash = hashlib.md5(f.read()).hexdigest()
                            existing_hashes.append(existing_hash)
                    except:
                        pass
                
                if image_hash in existing_hashes:
                    print(f"❌ Duplicate detected")
                    return False
                
                # Generate filename
                new_number = self.current_count + len(self.downloaded_images) + 1
                category = self.categorize_basketball_content(url)
                filename = f"basketball_{new_number:03d}_{category}_{image_hash[:8]}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # Create metadata
                dimensions = self.get_image_dimensions(image_data)
                metadata = {
                    'filename': filename,
                    'category': category,
                    'source_url': url,
                    'file_size': len(image_data),
                    'hash': image_hash,
                    'dimensions': dimensions,
                    'download_time': datetime.now(timezone.utc).isoformat()
                }
                
                # Save metadata
                metadata_path = filepath.replace('.jpg', '.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.downloaded_images.append(metadata)
                print(f"✅ Downloaded: {filename} ({dimensions})")
                return True
                
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
            # Retry for timeouts
            if attempt < 2 and "timeout" in str(e).lower():
                print(f"🔄 Retrying...")
                time.sleep(3)
                return self.download_basketball_image(url, attempt + 1)
        
        self.failed_urls.add(url)
        return False

    def categorize_basketball_content(self, url: str) -> str:
        """Categorize basketball content"""
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['player', 'nba', 'lebron', 'jordan']):
            return 'nba_players'
        elif any(keyword in url_lower for keyword in ['court', 'arena', 'stadium']):
            return 'basketball_courts'
        elif any(keyword in url_lower for keyword in ['ball', 'hoop', 'equipment']):
            return 'basketball_equipment'
        elif any(keyword in url_lower for keyword in ['team', 'lakers', 'warriors']):
            return 'nba_teams'
        elif any(keyword in url_lower for keyword in ['street', 'outdoor']):
            return 'streetball'
        else:
            return 'general_basketball'

    def get_image_dimensions(self, image_data: bytes) -> str:
        """Get image dimensions"""
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            return f"{img.width}x{img.height}"
        except:
            return "unknown"

    def complete_basketball_collection(self):
        """Complete the basketball collection to 40 images"""
        print("🏀 Completing Basketball Collection - Agent 3 Phase 2")
        print(f"Target: {self.target_count} | Current: {self.current_count} | Need: {self.needed_count}")
        print("=" * 60)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Download remaining images
        for url in self.basketball_urls:
            if len(self.downloaded_images) >= self.needed_count:
                break
            
            if self.download_basketball_image(url):
                # Brief pause between downloads
                time.sleep(random.uniform(1, 2))
        
        final_count = self.current_count + len(self.downloaded_images)
        print(f"\n🏀 Basketball collection update complete!")
        print(f"Total images: {final_count}/{self.target_count}")
        print(f"New downloads: {len(self.downloaded_images)}")
        
        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate enhanced completion report"""
        final_count = self.current_count + len(self.downloaded_images)
        
        # Analyze new downloads
        category_breakdown = {}
        for img in self.downloaded_images:
            category = img['category']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        report = {
            'agent': 'Agent 3 - Basketball Specialist (Enhanced)',
            'mission_phase': 'Phase 2 - Collection Completion',
            'initial_count': self.current_count,
            'new_downloads': len(self.downloaded_images),
            'final_count': final_count,
            'target_count': self.target_count,
            'completion_rate': f"{(final_count / self.target_count) * 100:.1f}%",
            'status': 'COMPLETE' if final_count == self.target_count else 'PARTIAL',
            'new_categories': category_breakdown,
            'new_images': [
                {
                    'filename': img['filename'],
                    'category': img['category'],
                    'dimensions': img['dimensions'],
                    'size_kb': round(img['file_size'] / 1024, 2)
                }
                for img in self.downloaded_images
            ]
        }
        
        # Save enhanced report
        report_path = os.path.join(self.output_dir, 'AGENT_3_ENHANCED_COMPLETION_REPORT.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    output_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/basketball_40"
    
    scraper = EnhancedBasketballScraper(output_dir)
    
    try:
        report = scraper.complete_basketball_collection()
        
        print("\n" + "=" * 60)
        print("🏀 AGENT 3 ENHANCED BASKETBALL MISSION REPORT 🏀")
        print("=" * 60)
        print(f"Initial Images: {report['initial_count']}")
        print(f"New Downloads: {report['new_downloads']}")
        print(f"Final Total: {report['final_count']}/{report['target_count']}")
        print(f"Completion Rate: {report['completion_rate']}")
        print(f"Status: {report['status']}")
        
        if report['new_categories']:
            print("\nNew Basketball Categories:")
            for category, count in report['new_categories'].items():
                print(f"  {category.replace('_', ' ').title()}: {count}")
        
        print(f"\n✅ Basketball collection {'COMPLETE' if report['status'] == 'COMPLETE' else 'UPDATED'}!")
        
    except Exception as e:
        print(f"❌ Error during enhanced collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()