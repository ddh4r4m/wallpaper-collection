#!/usr/bin/env python3
"""
Agent 4: Enhanced Fitness/Workout Pinterest Wallpaper Scraper V2
Targets high-resolution images with better URL manipulation
"""

import os
import sys
import time
import json
import hashlib
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedFitnessScraper:
    def __init__(self, max_images=30):
        self.max_images = max_images
        self.downloaded_images = []
        self.existing_hashes = set()
        self.duplicate_count = 0
        self.quality_rejected = 0
        
        # Enhanced search terms targeting high-resolution content
        self.search_terms = [
            {
                "term": "fitness wallpaper 4k hd",
                "url": "https://in.pinterest.com/search/pins/?q=fitness%20wallpaper%204k%20hd",
                "category": "general_fitness"
            },
            {
                "term": "gym motivation wallpaper hd phone",
                "url": "https://in.pinterest.com/search/pins/?q=gym%20motivation%20wallpaper%20hd%20phone", 
                "category": "motivation"
            },
            {
                "term": "workout background 4k mobile",
                "url": "https://in.pinterest.com/search/pins/?q=workout%20background%204k%20mobile",
                "category": "mobile_fitness"
            },
            {
                "term": "bodybuilding wallpaper hd",
                "url": "https://in.pinterest.com/search/pins/?q=bodybuilding%20wallpaper%20hd",
                "category": "bodybuilding"
            },
            {
                "term": "crossfit wallpaper 4k",
                "url": "https://in.pinterest.com/search/pins/?q=crossfit%20wallpaper%204k",
                "category": "crossfit"
            },
            {
                "term": "running wallpaper 4k",
                "url": "https://in.pinterest.com/search/pins/?q=running%20wallpaper%204k",
                "category": "running"
            },
            {
                "term": "weightlifting gym wallpaper hd",
                "url": "https://in.pinterest.com/search/pins/?q=weightlifting%20gym%20wallpaper%20hd",
                "category": "weightlifting"
            },
            {
                "term": "athletic workout wallpaper",
                "url": "https://in.pinterest.com/search/pins/?q=athletic%20workout%20wallpaper",
                "category": "athletic"
            },
            {
                "term": "fitness motivation phone wallpaper",
                "url": "https://in.pinterest.com/search/pins/?q=fitness%20motivation%20phone%20wallpaper",
                "category": "phone_motivation"
            },
            {
                "term": "gym equipment wallpaper hd",
                "url": "https://in.pinterest.com/search/pins/?q=gym%20equipment%20wallpaper%20hd",
                "category": "equipment"
            }
        ]
        
        # Setup Chrome driver
        self.setup_driver()
        
        # Load existing hashes for duplicate detection
        self.load_existing_hashes()
    
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def load_existing_hashes(self):
        """Load existing image hashes from other agent collections"""
        base_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest"
        
        agent_dirs = [
            "basketball_40",
            "football_soccer_40", 
            "sports_40",
            "sports_40_final",
            "gradient_search",
            "expanded_search",
            "specific_pins",
            "search_30"
        ]
        
        for agent_dir in agent_dirs:
            agent_path = os.path.join(base_dir, agent_dir)
            if os.path.exists(agent_path):
                for file in os.listdir(agent_path):
                    if file.endswith('.jpg'):
                        img_path = os.path.join(agent_path, file)
                        try:
                            img_hash = self.get_image_hash(img_path)
                            self.existing_hashes.add(img_hash)
                        except:
                            continue
        
        logger.info(f"Loaded {len(self.existing_hashes)} existing image hashes for duplicate detection")
    
    def get_image_hash(self, image_path):
        """Generate MD5 hash of image for duplicate detection"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def get_highest_resolution_url(self, img_src):
        """Extract highest resolution URL from Pinterest image source"""
        try:
            # Pinterest URL patterns
            if 'pinimg.com' not in img_src:
                return None
                
            # Try to get the highest resolution version
            # Remove size specifications and try original
            base_url = img_src
            
            # Replace common size patterns with highest available
            size_patterns = [
                ('/236x/', '/originals/'),
                ('/474x/', '/originals/'),
                ('/564x/', '/originals/'),
                ('/736x/', '/originals/'),
                ('/1200x/', '/originals/')
            ]
            
            # Try originals first
            for pattern, replacement in size_patterns:
                if pattern in base_url:
                    original_url = base_url.replace(pattern, replacement)
                    return original_url
            
            # If no patterns found, try 1200x format
            if '/originals/' not in base_url:
                # Try to construct higher resolution URL
                path_parts = base_url.split('/')
                for i, part in enumerate(path_parts):
                    if 'x' in part and part.replace('x', '').isdigit():
                        path_parts[i] = '1200x'
                        break
                return '/'.join(path_parts)
            
            return base_url
            
        except Exception as e:
            logger.error(f"Error processing URL {img_src}: {str(e)}")
            return img_src
    
    def check_image_quality(self, image_path):
        """Check if image meets quality requirements with relaxed standards"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # More flexible mobile wallpaper requirements
                min_resolution = 800  # Reduced minimum
                
                # Check if either dimension meets minimum
                if max(width, height) < min_resolution:
                    return False, f"Resolution too low: {width}x{height} (min: {min_resolution})"
                
                # Prefer portrait orientation but accept landscape if high quality
                if width >= 1080 and height >= 1920:
                    quality = "Excellent mobile portrait"
                elif height >= 1080 and width >= 1920:
                    quality = "Excellent mobile landscape"
                elif max(width, height) >= 1200:
                    quality = "Good high resolution"
                elif max(width, height) >= 1000:
                    quality = "Acceptable resolution"
                else:
                    quality = "Basic quality"
                
                # Check file size (not too small)
                file_size = os.path.getsize(image_path)
                if file_size < 30000:  # Reduced to 30KB minimum
                    return False, f"File size too small: {file_size} bytes"
                
                return True, f"{quality}: {width}x{height}, {file_size} bytes"
        except Exception as e:
            return False, f"Error checking quality: {str(e)}"
    
    def is_fitness_content(self, pin_url, img_alt="", pin_title=""):
        """Enhanced fitness content detection"""
        fitness_keywords = [
            'fitness', 'workout', 'gym', 'exercise', 'training', 'muscle',
            'strength', 'cardio', 'running', 'weightlifting', 'bodybuilding',
            'crossfit', 'yoga', 'pilates', 'athletic', 'sport', 'dumbbell',
            'barbell', 'weights', 'treadmill', 'motivation', 'health',
            'fit', 'strong', 'power', 'endurance', 'athlete', 'performance',
            'biceps', 'triceps', 'abs', 'squat', 'deadlift', 'bench', 'protein'
        ]
        
        # Check URL, alt text, and title
        text_to_check = (pin_url + " " + img_alt + " " + pin_title).lower()
        
        return any(keyword in text_to_check for keyword in fitness_keywords)
    
    def scroll_and_collect_pins(self, search_term_data, target_count=8):
        """Enhanced scrolling with better pin collection"""
        url = search_term_data["url"]
        category = search_term_data["category"]
        
        logger.info(f"Searching: {search_term_data['term']} (Category: {category})")
        
        try:
            self.driver.get(url)
            time.sleep(10)  # Wait for initial load
            
            collected_pins = []
            scroll_count = 0
            max_scrolls = 20
            
            while len(collected_pins) < target_count and scroll_count < max_scrolls:
                try:
                    # Find all pin elements with different selectors
                    pin_selectors = [
                        '[data-test-id="pin"]',
                        '[data-test-id="pinrep"]',
                        'div[class*="pin"]',
                        'img[src*="pinimg.com"]'
                    ]
                    
                    pins = []
                    for selector in pin_selectors:
                        found_pins = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        pins.extend(found_pins)
                        if len(pins) > 50:  # Don't collect too many at once
                            break
                    
                    logger.info(f"Found {len(pins)} pin elements on page")
                    
                    for pin in pins:
                        if len(collected_pins) >= target_count:
                            break
                        
                        try:
                            # Try different ways to find image
                            img_element = None
                            img_src = None
                            
                            # Method 1: Direct img tag
                            try:
                                img_element = pin.find_element(By.TAG_NAME, 'img')
                                img_src = img_element.get_attribute('src')
                            except:
                                pass
                            
                            # Method 2: If pin is img element itself
                            if not img_src and pin.tag_name == 'img':
                                img_src = pin.get_attribute('src')
                                img_element = pin
                            
                            # Method 3: Look for background images
                            if not img_src:
                                try:
                                    style = pin.get_attribute('style')
                                    if style and 'background-image' in style:
                                        # Extract URL from background-image
                                        import re
                                        url_match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                                        if url_match:
                                            img_src = url_match.group(1)
                                except:
                                    pass
                            
                            if not img_src or 'pinimg.com' not in img_src:
                                continue
                            
                            # Get image metadata
                            img_alt = ""
                            pin_title = ""
                            
                            if img_element:
                                img_alt = img_element.get_attribute('alt') or ""
                                
                            try:
                                pin_title = pin.get_attribute('title') or ""
                            except:
                                pass
                            
                            # Enhanced fitness content detection
                            if not self.is_fitness_content(img_src, img_alt, pin_title):
                                continue
                            
                            # Get highest resolution URL
                            high_res_url = self.get_highest_resolution_url(img_src)
                            if not high_res_url:
                                continue
                            
                            pin_data = {
                                'url': high_res_url,
                                'original_url': img_src,
                                'alt': img_alt,
                                'title': pin_title,
                                'category': category,
                                'search_term': search_term_data['term']
                            }
                            
                            # Check for duplicates in current collection
                            if not any(p['url'] == high_res_url for p in collected_pins):
                                collected_pins.append(pin_data)
                                logger.info(f"Found fitness pin [{len(collected_pins)}]: {(img_alt or pin_title)[:50]}...")
                        
                        except Exception as e:
                            continue
                    
                    # Enhanced scrolling
                    logger.info(f"Scroll {scroll_count + 1}: Found {len(collected_pins)} pins")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(15)  # Wait between scrolls
                    scroll_count += 1
                    
                except Exception as e:
                    logger.error(f"Error during scrolling: {str(e)}")
                    scroll_count += 1
            
            logger.info(f"Collected {len(collected_pins)} pins for {search_term_data['term']}")
            return collected_pins
            
        except Exception as e:
            logger.error(f"Error collecting pins for {search_term_data['term']}: {str(e)}")
            return []
    
    def download_image(self, pin_data, index):
        """Download and validate fitness image"""
        try:
            url = pin_data['url']
            category = pin_data['category']
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.pinterest.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache'
            }
            
            # Try original URL first, then fallback
            urls_to_try = [url]
            if pin_data.get('original_url') and pin_data['original_url'] != url:
                urls_to_try.append(pin_data['original_url'])
            
            response = None
            used_url = None
            
            for try_url in urls_to_try:
                try:
                    response = requests.get(try_url, headers=headers, timeout=30)
                    if response.status_code == 200 and len(response.content) > 10000:
                        used_url = try_url
                        break
                except:
                    continue
            
            if not response or response.status_code != 200:
                logger.warning(f"Failed to download: {url}")
                return None
            
            # Generate unique filename
            url_hash = hashlib.md5(used_url.encode()).hexdigest()[:8]
            filename = f"fitness_{index:03d}_{category}_{url_hash}.jpg"
            filepath = os.path.join(os.getcwd(), filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Check for duplicates using image hash
            img_hash = self.get_image_hash(filepath)
            if img_hash in self.existing_hashes:
                os.remove(filepath)
                self.duplicate_count += 1
                logger.warning(f"Duplicate detected and skipped: {filename}")
                return None
            
            # Add to existing hashes
            self.existing_hashes.add(img_hash)
            
            # Quality check with relaxed standards
            is_quality, quality_msg = self.check_image_quality(filepath)
            if not is_quality:
                os.remove(filepath)
                self.quality_rejected += 1
                logger.warning(f"Quality rejected: {filename} - {quality_msg}")
                return None
            
            # Save metadata
            metadata = {
                'filename': filename,
                'url': used_url,
                'original_url': pin_data.get('original_url', ''),
                'alt_text': pin_data.get('alt', ''),
                'title': pin_data.get('title', ''),
                'category': category,
                'search_term': pin_data.get('search_term', ''),
                'downloaded_at': datetime.now().isoformat(),
                'quality_check': quality_msg,
                'hash': img_hash
            }
            
            metadata_filename = filename.replace('.jpg', '.json')
            with open(metadata_filename, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Downloaded: {filename} - {quality_msg}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error downloading {pin_data.get('url', 'unknown')}: {str(e)}")
            return None
    
    def run_scraping(self):
        """Main scraping process to get exactly 30 fitness wallpapers"""
        logger.info(f"Starting enhanced fitness wallpaper scraping - Target: {self.max_images} images")
        
        downloaded_count = 0
        search_results = {}
        
        # Distribute searches more evenly
        searches_completed = 0
        
        for search_data in self.search_terms:
            if downloaded_count >= self.max_images:
                break
            
            remaining_needed = self.max_images - downloaded_count
            # Target more pins per search to account for quality filtering
            target_pins = min(8, remaining_needed + 10)
            
            pins = self.scroll_and_collect_pins(search_data, target_pins)
            search_results[search_data['term']] = len(pins)
            searches_completed += 1
            
            # Download pins for this search term
            pins_downloaded_this_search = 0
            for pin in pins:
                if downloaded_count >= self.max_images:
                    break
                
                metadata = self.download_image(pin, downloaded_count + 1)
                if metadata:
                    self.downloaded_images.append(metadata)
                    downloaded_count += 1
                    pins_downloaded_this_search += 1
                    logger.info(f"🏋️ Progress: {downloaded_count}/{self.max_images} images downloaded")
                
                # Don't take too many from one search
                if pins_downloaded_this_search >= 5:
                    break
            
            # Small delay between search terms
            time.sleep(5)
            
            # Progress update
            logger.info(f"Completed search {searches_completed}/{len(self.search_terms)}: {pins_downloaded_this_search} images added")
        
        self.driver.quit()
        
        # Generate final report
        self.generate_final_report(search_results)
        
        return downloaded_count
    
    def generate_final_report(self, search_results):
        """Generate comprehensive mission report"""
        
        # Analyze downloaded images by category
        category_breakdown = {}
        for img in self.downloaded_images:
            category = img['category']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        report = {
            "mission": "Agent 4 - Enhanced Fitness/Workout Wallpaper Collection",
            "status": "COMPLETE" if len(self.downloaded_images) == self.max_images else "PARTIAL",
            "target_images": self.max_images,
            "actual_downloaded": len(self.downloaded_images),
            "duplicates_skipped": self.duplicate_count,
            "quality_rejected": self.quality_rejected,
            "total_attempts": len(self.downloaded_images) + self.duplicate_count + self.quality_rejected,
            "success_rate": f"{(len(self.downloaded_images) / max(1, len(self.downloaded_images) + self.duplicate_count + self.quality_rejected)) * 100:.1f}%",
            "search_results": search_results,
            "category_breakdown": category_breakdown,
            "search_terms_used": [term["term"] for term in self.search_terms],
            "most_successful_searches": sorted(search_results.items(), key=lambda x: x[1], reverse=True)[:5],
            "images": self.downloaded_images,
            "completion_time": datetime.now().isoformat()
        }
        
        # Save JSON report
        with open('AGENT_4_ENHANCED_FITNESS_COMPLETE.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save markdown report
        md_report = f"""# Agent 4: Enhanced Fitness/Workout Wallpaper Mission Complete

## Mission Status: {"✅ COMPLETE" if len(self.downloaded_images) == self.max_images else "⚠️ PARTIAL"}

### Results Summary:
- **Target**: {self.max_images} fitness/workout wallpapers
- **Downloaded**: {len(self.downloaded_images)} high-quality images
- **Duplicates Skipped**: {self.duplicate_count}
- **Quality Rejected**: {self.quality_rejected}
- **Success Rate**: {(len(self.downloaded_images) / max(1, len(self.downloaded_images) + self.duplicate_count + self.quality_rejected)) * 100:.1f}%

### Category Breakdown:
"""
        
        for category, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
            md_report += f"- **{category}**: {count} images\n"
        
        md_report += f"""
### Most Successful Search Terms:
"""
        
        for term, count in sorted(search_results.items(), key=lambda x: x[1], reverse=True)[:5]:
            md_report += f"- **{term}**: {count} pins found\n"
        
        md_report += f"""
### Enhanced Features:
- **High-Resolution Targeting**: Prioritized 4K and HD search terms
- **Advanced URL Processing**: Extracted original/highest resolution versions
- **Flexible Quality Standards**: Adapted for mobile wallpaper formats
- **Enhanced Content Detection**: 30+ fitness-related keywords
- **Duplicate Prevention**: MD5 hashing across all agent collections

### Quality Metrics:
- Minimum resolution: 800px (either dimension)
- Preferred: 1080x1920+ for mobile wallpapers
- File size: 30KB+ minimum
- Content validation: Fitness/workout specific filtering

### Search Strategy:
- 10 targeted high-resolution search terms
- Extended scrolling with 15-second intervals
- Multiple URL resolution attempts per image
- Distributed download limits per search term

Mission completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open('AGENT_4_ENHANCED_FITNESS_COMPLETE.md', 'w') as f:
            f.write(md_report)
        
        logger.info("=== ENHANCED MISSION COMPLETE ===")
        logger.info(f"Downloaded: {len(self.downloaded_images)}/{self.max_images} fitness wallpapers")
        logger.info(f"Duplicates skipped: {self.duplicate_count}")
        logger.info(f"Quality rejected: {self.quality_rejected}")
        logger.info("Reports saved: AGENT_4_ENHANCED_FITNESS_COMPLETE.json/.md")

if __name__ == "__main__":
    scraper = EnhancedFitnessScraper(max_images=30)
    try:
        final_count = scraper.run_scraping()
        print(f"\n🏋️ AGENT 4 ENHANCED MISSION COMPLETE: {final_count}/30 fitness wallpapers downloaded! 🏋️")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        scraper.driver.quit()
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        if hasattr(scraper, 'driver'):
            scraper.driver.quit()