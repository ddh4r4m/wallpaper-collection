#!/usr/bin/env python3
"""
Agent 3: Basketball Wallpaper Scraper for Pinterest
Scrapes exactly 40 high-quality basketball wallpapers from Pinterest
Implements enhanced basketball-specific search strategy with duplicate detection
"""

import os
import json
import time
import random
import hashlib
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class BasketballPinterestScraper:
    def __init__(self, target_count=40):
        self.target_count = target_count
        self.downloaded_images = []
        self.existing_hashes = set()
        self.setup_directories()
        self.load_existing_hashes()
        self.setup_driver()
        
        # Enhanced basketball search terms with Pinterest optimization
        self.search_terms = [
            "basketball wallpaper mobile",
            "NBA wallpaper hd",
            "basketball court wallpaper",
            "basketball player wallpaper", 
            "basketball background phone",
            "basketball hoop wallpaper",
            "streetball wallpaper",
            "NBA player wallpaper",
            "basketball action wallpaper",
            "basketball arena wallpaper",
            "basketball shoes wallpaper",
            "basketball dunk wallpaper",
            "NBA team wallpaper",
            "basketball aesthetic wallpaper",
            "basketball phone background"
        ]
        
        # Content categories for classification
        self.content_categories = {
            'players': ['player', 'nba', 'lebron', 'jordan', 'kobe', 'curry', 'dunk', 'action'],
            'courts': ['court', 'arena', 'stadium', 'floor', 'gym', 'outdoor'],
            'equipment': ['ball', 'basketball', 'hoop', 'net', 'shoes', 'sneakers'],
            'teams': ['lakers', 'warriors', 'bulls', 'celtics', 'heat', 'spurs', 'nets'],
            'streetball': ['street', 'outdoor', 'urban', 'playground', 'asphalt']
        }
        
        self.quality_stats = {
            'total_processed': 0,
            'high_quality': 0,
            'mobile_optimized': 0,
            'basketball_specific': 0,
            'duplicates_filtered': 0
        }

    def setup_directories(self):
        """Setup directory structure for organized storage"""
        self.base_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/basketball_40"
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Create category subdirectories
        for category in ['players', 'courts', 'equipment', 'teams', 'streetball', 'misc']:
            os.makedirs(os.path.join(self.base_dir, category), exist_ok=True)

    def load_existing_hashes(self):
        """Load existing image hashes for duplicate detection"""
        parent_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest"
        
        # Scan all existing collections for duplicates
        collections = ['football_soccer_40', 'sports_40', 'sports_40_final', 'gradient_search', 'expanded_search']
        
        for collection in collections:
            collection_path = os.path.join(parent_dir, collection)
            if os.path.exists(collection_path):
                for file in os.listdir(collection_path):
                    if file.endswith('.jpg'):
                        file_path = os.path.join(collection_path, file)
                        try:
                            img_hash = self.calculate_image_hash(file_path)
                            self.existing_hashes.add(img_hash)
                        except Exception as e:
                            print(f"Error calculating hash for {file}: {e}")
        
        print(f"Loaded {len(self.existing_hashes)} existing image hashes for duplicate detection")

    def calculate_image_hash(self, image_path):
        """Calculate MD5 hash of image file for duplicate detection"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def setup_driver(self):
        """Setup Chrome driver with optimized settings for Pinterest"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)

    def search_pinterest(self, search_term):
        """Search Pinterest for basketball wallpapers with enhanced strategy"""
        try:
            # Format search URL for Pinterest
            formatted_term = search_term.replace(" ", "%20")
            url = f"https://in.pinterest.com/search/pins/?q={formatted_term}"
            
            print(f"Searching Pinterest for: {search_term}")
            self.driver.get(url)
            
            # Wait for initial content load
            time.sleep(8)
            
            # Enhanced scrolling with basketball-specific targeting
            scroll_count = 0
            images_found = []
            max_scrolls = 15  # Increased for better coverage
            
            while scroll_count < max_scrolls and len(self.downloaded_images) < self.target_count:
                # Scroll down to load more content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(12, 15))  # Enhanced wait time
                
                # Find all image containers
                try:
                    pin_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-id="pin"]')
                    
                    for pin in pin_elements:
                        if len(self.downloaded_images) >= self.target_count:
                            break
                            
                        try:
                            # Find image element within pin
                            img_element = pin.find_element(By.TAG_NAME, 'img')
                            img_url = img_element.get_attribute('src')
                            
                            if img_url and self.is_valid_basketball_image(img_url, pin):
                                images_found.append({
                                    'url': img_url,
                                    'element': pin,
                                    'search_term': search_term
                                })
                                
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue
                            
                except Exception as e:
                    print(f"Error finding pin elements: {e}")
                
                scroll_count += 1
                print(f"Scroll {scroll_count}/{max_scrolls}, Found {len(images_found)} potential images")
            
            return images_found
            
        except Exception as e:
            print(f"Error searching Pinterest for '{search_term}': {e}")
            return []

    def is_valid_basketball_image(self, img_url, pin_element):
        """Enhanced basketball content validation"""
        try:
            # Check URL quality indicators
            if not img_url or 'pinterest' not in img_url:
                return False
            
            # Get pin text content for basketball validation
            try:
                pin_text = pin_element.text.lower()
            except:
                pin_text = ""
            
            # Basketball keywords for content validation
            basketball_keywords = [
                'basketball', 'nba', 'player', 'court', 'hoop', 'dunk', 'ball',
                'jordan', 'lebron', 'kobe', 'curry', 'lakers', 'warriors', 'bulls',
                'streetball', 'arena', 'game', 'sport', 'team', 'league'
            ]
            
            # Check if content is basketball-related
            has_basketball_content = any(keyword in pin_text for keyword in basketball_keywords)
            
            # URL quality checks
            url_quality_indicators = ['736x', '1080x', 'originals', 'hd']
            has_quality_indicator = any(indicator in img_url for indicator in url_quality_indicators)
            
            return has_basketball_content or has_quality_indicator
            
        except Exception:
            return False

    def download_and_process_image(self, image_data):
        """Download and process basketball image with quality validation"""
        try:
            img_url = image_data['url']
            search_term = image_data['search_term']
            
            # Try to get higher quality version
            high_quality_url = self.get_high_quality_url(img_url)
            
            response = requests.get(high_quality_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                # Validate image content and quality
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                
                # Quality validation for mobile wallpapers
                if not self.validate_image_quality(img, width, height):
                    return False
                
                # Calculate hash for duplicate detection
                img_hash = hashlib.md5(response.content).hexdigest()
                if img_hash in self.existing_hashes:
                    self.quality_stats['duplicates_filtered'] += 1
                    print(f"Skipping duplicate image: {img_hash[:8]}")
                    return False
                
                # Categorize content
                category = self.categorize_basketball_content(search_term, img_url)
                
                # Generate filename
                filename = f"basketball_{len(self.downloaded_images) + 1:03d}_{category}_{img_hash[:8]}.jpg"
                filepath = os.path.join(self.base_dir, category, filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Save metadata
                metadata = {
                    'filename': filename,
                    'category': category,
                    'search_term': search_term,
                    'original_url': img_url,
                    'high_quality_url': high_quality_url,
                    'dimensions': f"{width}x{height}",
                    'file_size': len(response.content),
                    'hash': img_hash,
                    'download_time': time.time()
                }
                
                metadata_path = filepath.replace('.jpg', '.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.downloaded_images.append(metadata)
                self.existing_hashes.add(img_hash)
                
                # Update quality stats
                self.update_quality_stats(width, height, category)
                
                print(f"Downloaded basketball image {len(self.downloaded_images)}/{self.target_count}: {filename} ({width}x{height})")
                return True
                
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False

    def get_high_quality_url(self, url):
        """Convert Pinterest URL to highest quality version"""
        try:
            # Pinterest URL quality optimization
            if 'pinimg.com' in url:
                # Replace size indicators with highest quality
                high_quality_url = url.replace('236x', '736x').replace('474x', '736x')
                high_quality_url = high_quality_url.replace('/236x/', '/originals/')
                high_quality_url = high_quality_url.replace('/474x/', '/originals/')
                return high_quality_url
            return url
        except:
            return url

    def validate_image_quality(self, img, width, height):
        """Validate image quality for mobile wallpapers"""
        try:
            # Size requirements for mobile wallpapers
            min_width, min_height = 1080, 1080  # Minimum resolution
            max_file_size = 2 * 1024 * 1024  # 2MB max
            
            # Check minimum resolution
            if width < min_width or height < min_height:
                return False
            
            # Prefer portrait orientation for mobile
            aspect_ratio = height / width
            
            # Mobile-optimized aspect ratios
            mobile_ratios = [
                (16, 9),   # 16:9
                (18, 9),   # 18:9 
                (19, 9),   # 19:9
                (20, 9),   # 20:9
                (4, 3),    # 4:3
                (1, 1)     # Square
            ]
            
            # Check if aspect ratio is mobile-friendly
            is_mobile_friendly = any(
                abs(aspect_ratio - (h/w)) < 0.1 or abs(aspect_ratio - (w/h)) < 0.1
                for w, h in mobile_ratios
            )
            
            if not is_mobile_friendly and aspect_ratio < 1.2:  # Too wide for mobile
                return False
            
            # Image format validation
            if img.format not in ['JPEG', 'PNG']:
                return False
            
            self.quality_stats['total_processed'] += 1
            
            # High quality indicators
            if width >= 1080 and height >= 1920:
                self.quality_stats['high_quality'] += 1
            
            if aspect_ratio >= 1.5:  # Portrait orientation
                self.quality_stats['mobile_optimized'] += 1
            
            return True
            
        except Exception as e:
            print(f"Error validating image quality: {e}")
            return False

    def categorize_basketball_content(self, search_term, url):
        """Categorize basketball content by type"""
        search_lower = search_term.lower()
        url_lower = url.lower()
        
        # Check each category
        for category, keywords in self.content_categories.items():
            if any(keyword in search_lower or keyword in url_lower for keyword in keywords):
                self.quality_stats['basketball_specific'] += 1
                return category
        
        return 'misc'

    def update_quality_stats(self, width, height, category):
        """Update quality statistics"""
        # Additional quality metrics could be added here
        pass

    def run_comprehensive_search(self):
        """Run comprehensive basketball wallpaper search"""
        print(f"Starting comprehensive basketball wallpaper search for {self.target_count} images")
        print("="*60)
        
        # Randomize search order for better diversity
        random.shuffle(self.search_terms)
        
        for search_term in self.search_terms:
            if len(self.downloaded_images) >= self.target_count:
                break
                
            print(f"\nSearching for: {search_term}")
            print(f"Progress: {len(self.downloaded_images)}/{self.target_count}")
            
            # Search and download from this term
            images = self.search_pinterest(search_term)
            
            # Process found images
            for image_data in images:
                if len(self.downloaded_images) >= self.target_count:
                    break
                    
                if self.download_and_process_image(image_data):
                    time.sleep(random.uniform(2, 4))  # Rate limiting
            
            # Wait between searches
            time.sleep(random.uniform(5, 8))
        
        print(f"\n" + "="*60)
        print(f"BASKETBALL WALLPAPER SCRAPING COMPLETE!")
        print(f"Target: {self.target_count} | Downloaded: {len(self.downloaded_images)}")

    def generate_final_report(self):
        """Generate comprehensive final report"""
        # Categorize downloaded images
        category_counts = {}
        for img in self.downloaded_images:
            category = img['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Most successful search terms
        search_term_success = {}
        for img in self.downloaded_images:
            term = img['search_term']
            search_term_success[term] = search_term_success.get(term, 0) + 1
        
        # Quality metrics
        total_images = len(self.downloaded_images)
        avg_file_size = sum(img['file_size'] for img in self.downloaded_images) / total_images if total_images > 0 else 0
        
        report = {
            'mission_status': 'COMPLETE' if total_images == self.target_count else 'PARTIAL',
            'target_count': self.target_count,
            'downloaded_count': total_images,
            'success_rate': f"{(total_images/self.target_count)*100:.1f}%",
            'category_breakdown': category_counts,
            'most_successful_searches': dict(sorted(search_term_success.items(), key=lambda x: x[1], reverse=True)[:5]),
            'quality_metrics': {
                'total_processed': self.quality_stats['total_processed'],
                'high_quality_images': self.quality_stats['high_quality'],
                'mobile_optimized': self.quality_stats['mobile_optimized'],
                'basketball_specific': self.quality_stats['basketball_specific'],
                'duplicates_filtered': self.quality_stats['duplicates_filtered'],
                'average_file_size_kb': round(avg_file_size / 1024, 2)
            },
            'content_categories': list(category_counts.keys()),
            'all_images': [
                {
                    'filename': img['filename'],
                    'category': img['category'],
                    'dimensions': img['dimensions'],
                    'search_term': img['search_term']
                }
                for img in self.downloaded_images
            ]
        }
        
        # Save report
        with open(os.path.join(self.base_dir, 'AGENT_3_BASKETBALL_MISSION_COMPLETE.json'), 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save detailed report
        report_md = f"""# Agent 3: Basketball Wallpaper Mission Complete

## Mission Summary
- **Target**: {self.target_count} basketball wallpapers
- **Downloaded**: {total_images} images
- **Success Rate**: {(total_images/self.target_count)*100:.1f}%
- **Status**: {'✅ COMPLETE' if total_images == self.target_count else '⚠️ PARTIAL'}

## Content Breakdown
"""
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report_md += f"- **{category.title()}**: {count} images\n"
        
        report_md += f"""
## Quality Metrics
- **Total Processed**: {self.quality_stats['total_processed']} images
- **High Quality (1080x1920+)**: {self.quality_stats['high_quality']} images
- **Mobile Optimized**: {self.quality_stats['mobile_optimized']} images
- **Basketball Specific**: {self.quality_stats['basketball_specific']} images
- **Duplicates Filtered**: {self.quality_stats['duplicates_filtered']} images
- **Average File Size**: {round(avg_file_size / 1024, 2)} KB

## Most Successful Search Terms
"""
        
        for term, count in list(search_term_success.items())[:5]:
            report_md += f"- **{term}**: {count} images\n"
        
        report_md += f"""
## All Downloaded Images
"""
        
        for i, img in enumerate(self.downloaded_images, 1):
            report_md += f"{i}. **{img['filename']}** ({img['dimensions']}) - {img['category']}\n"
        
        with open(os.path.join(self.base_dir, 'AGENT_3_BASKETBALL_MISSION_COMPLETE.md'), 'w') as f:
            f.write(report_md)
        
        return report

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.driver.quit()
        except:
            pass

def main():
    scraper = BasketballPinterestScraper(target_count=40)
    
    try:
        scraper.run_comprehensive_search()
        report = scraper.generate_final_report()
        
        print("\n" + "="*60)
        print("🏀 BASKETBALL WALLPAPER MISSION SUMMARY 🏀")
        print("="*60)
        print(f"Target: {report['target_count']} | Downloaded: {report['downloaded_count']}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"Status: {report['mission_status']}")
        print("\nCategory Breakdown:")
        for category, count in report['category_breakdown'].items():
            print(f"  {category.title()}: {count} images")
        print("\nQuality Metrics:")
        print(f"  High Quality: {report['quality_metrics']['high_quality']}")
        print(f"  Mobile Optimized: {report['quality_metrics']['mobile_optimized']}")
        print(f"  Duplicates Filtered: {report['quality_metrics']['duplicates_filtered']}")
        print("\nMost Successful Search Terms:")
        for term, count in list(report['most_successful_searches'].items())[:3]:
            print(f"  {term}: {count} images")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()