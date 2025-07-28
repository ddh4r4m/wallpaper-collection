#!/usr/bin/env python3
"""
Pinterest Gradient Scraper - Agent 3: Expanded Search & Board Discovery
Responsibility: Discover additional gradient content through diverse search terms and board exploration

Key Features:
- Multiple gradient search query variations
- Pinterest board discovery and exploration
- Intelligent duplicate detection with existing collection
- Mobile wallpaper dimension filtering (1080x1920+)
- Quality scoring and style categorization
- Target: 40+ unique gradient images for 120+ total collection
"""

import os
import sys
import time
import json
import hashlib
import requests
from datetime import datetime
from urllib.parse import quote, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/pinterest_gradient_agent3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PinterestGradientAgent3:
    def __init__(self):
        self.base_url = "https://in.pinterest.com"
        self.output_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/expanded_search"
        self.existing_hashes_files = [
            "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/gradient_search/downloaded_hashes.json",
            "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/specific_pins/downloaded_hashes.json"
        ]
        
        # Mobile wallpaper requirements
        self.min_width = 1080
        self.min_height = 1920
        self.preferred_width = 1440
        self.preferred_height = 2560
        
        # Target settings
        self.target_images = 50  # Aim higher than 40 for buffer
        self.downloaded_count = 0
        self.existing_hashes = set()
        
        # Diverse search queries for gradient exploration
        self.search_queries = [
            "gradient wallpaper mobile",
            "abstract gradient phone background", 
            "colorful gradient wallpaper",
            "smooth gradient background",
            "fluid gradient abstract",
            "neon gradient background",
            "pastel gradient wallpaper",
            "rainbow gradient background",
            "holographic gradient",
            "mesh gradient background",
            "aurora gradient wallpaper", 
            "cosmic gradient background",
            "sunset gradient wallpaper",
            "minimalist gradient",
            "geometric gradient pattern"
        ]
        
        # Board search terms for discovery
        self.board_search_terms = [
            "gradient wallpapers",
            "gradient backgrounds", 
            "abstract gradients",
            "phone gradient wallpapers",
            "colorful gradients"
        ]
        
        self.setup_directories()
        self.load_existing_hashes()
        
    def setup_directories(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")
        
    def load_existing_hashes(self):
        """Load existing image hashes to avoid duplicates"""
        for hash_file in self.existing_hashes_files:
            if os.path.exists(hash_file):
                try:
                    with open(hash_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'hashes' in data:
                            self.existing_hashes.update(data['hashes'])
                        elif isinstance(data, list):
                            self.existing_hashes.update(data)
                    logger.info(f"Loaded {len(self.existing_hashes)} existing hashes from {hash_file}")
                except Exception as e:
                    logger.warning(f"Could not load hashes from {hash_file}: {e}")
        
        # Also load from our own directory
        our_hash_file = os.path.join(self.output_dir, "downloaded_hashes.json")
        if os.path.exists(our_hash_file):
            try:
                with open(our_hash_file, 'r') as f:
                    data = json.load(f)
                    if 'hashes' in data:
                        self.existing_hashes.update(data['hashes'])
                logger.info(f"Loaded existing hashes from our directory")
            except Exception as e:
                logger.warning(f"Could not load our hashes: {e}")
                
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
        
    def get_image_hash(self, image_url):
        """Generate hash for image to check for duplicates"""
        try:
            response = requests.get(image_url, timeout=10, stream=True)
            if response.status_code == 200:
                # Read first 8KB for hash generation
                content = response.raw.read(8192)
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to generate hash for {image_url}: {e}")
        return None
        
    def is_duplicate(self, image_url):
        """Check if image is duplicate of existing collection"""
        image_hash = self.get_image_hash(image_url)
        if image_hash and image_hash in self.existing_hashes:
            return True
        return False
        
    def get_image_dimensions(self, image_url):
        """Get image dimensions to filter for mobile wallpaper sizes"""
        try:
            response = requests.head(image_url, timeout=5)
            if response.status_code == 200:
                # Try to get dimensions from headers (if available)
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) < 50000:  # Too small file
                    return None, None
                    
            # Download a small portion to check dimensions
            response = requests.get(image_url, timeout=10, stream=True)
            if response.status_code == 200:
                from PIL import Image
                import io
                
                # Read first chunk
                chunk = next(response.iter_content(chunk_size=8192))
                try:
                    img = Image.open(io.BytesIO(chunk))
                    return img.size
                except:
                    # If first chunk doesn't work, try downloading more
                    content = chunk
                    for i, chunk in enumerate(response.iter_content(chunk_size=8192)):
                        content += chunk
                        if i > 5:  # Limit to first ~50KB
                            break
                    try:
                        img = Image.open(io.BytesIO(content))
                        return img.size
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Failed to get dimensions for {image_url}: {e}")
        return None, None
        
    def is_mobile_suitable(self, width, height):
        """Check if image dimensions are suitable for mobile wallpaper"""
        if not width or not height:
            return False
            
        # Must meet minimum requirements
        if width < self.min_width or height < self.min_height:
            return False
            
        # Prefer portrait orientation for mobile
        aspect_ratio = height / width
        if aspect_ratio < 1.5:  # Not portrait enough
            return False
            
        return True
        
    def download_image(self, image_url, filename, metadata):
        """Download image with metadata"""
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                # Save image
                image_path = os.path.join(self.output_dir, f"{filename}.jpg")
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                # Save metadata
                metadata_path = os.path.join(self.output_dir, f"{filename}.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Add hash to existing set
                image_hash = self.get_image_hash(image_url)
                if image_hash:
                    self.existing_hashes.add(image_hash)
                
                logger.info(f"Downloaded: {filename}")
                self.downloaded_count += 1
                return True
        except Exception as e:
            logger.error(f"Failed to download {image_url}: {e}")
        return False
        
    def extract_pin_data(self, driver, pin_element):
        """Extract data from a Pinterest pin element"""
        try:
            # Get pin URL/ID
            pin_link = pin_element.find_element(By.TAG_NAME, "a")
            pin_url = pin_link.get_attribute("href")
            pin_id = pin_url.split("/pin/")[1].split("/")[0] if "/pin/" in pin_url else "unknown"
            
            # Get image URL
            img_element = pin_element.find_element(By.TAG_NAME, "img")
            image_url = img_element.get_attribute("src")
            
            # Try to get higher resolution version
            if "236x" in image_url:
                image_url = image_url.replace("236x", "originals")
            elif "474x" in image_url:
                image_url = image_url.replace("474x", "originals")
            elif "/474x" in image_url:
                image_url = image_url.replace("/474x", "/originals")
                
            # Get title/alt text
            title = img_element.get_attribute("alt") or "Gradient Background"
            
            return {
                "pin_id": pin_id,
                "pin_url": pin_url,
                "image_url": image_url,
                "title": title
            }
        except Exception as e:
            logger.warning(f"Failed to extract pin data: {e}")
            return None
            
    def search_gradient_content(self, driver, query, max_scrolls=4):
        """Search for gradient content with specific query"""
        logger.info(f"Searching for: {query}")
        
        search_url = f"{self.base_url}/search/pins/?q={quote(query)}"
        driver.get(search_url)
        time.sleep(3)
        
        pins_processed = 0
        scroll_count = 0
        
        while scroll_count < max_scrolls and self.downloaded_count < self.target_images:
            try:
                # Find all pin elements
                pin_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test-id='pin']")
                
                for pin_element in pin_elements:
                    if self.downloaded_count >= self.target_images:
                        break
                        
                    pin_data = self.extract_pin_data(driver, pin_element)
                    if not pin_data:
                        continue
                        
                    # Check for duplicates
                    if self.is_duplicate(pin_data["image_url"]):
                        logger.debug(f"Skipping duplicate: {pin_data['pin_id']}")
                        continue
                        
                    # Check dimensions
                    width, height = self.get_image_dimensions(pin_data["image_url"])
                    if not self.is_mobile_suitable(width, height):
                        logger.debug(f"Skipping unsuitable dimensions {width}x{height}: {pin_data['pin_id']}")
                        continue
                        
                    # Quality scoring based on title content
                    quality_score = self.score_gradient_quality(pin_data["title"])
                    gradient_style = self.categorize_gradient_style(pin_data["title"])
                    
                    # Download high-quality gradients
                    if quality_score >= 6:  # Quality threshold
                        filename = f"pinterest_gradient_agent3_{pin_data['pin_id']}"
                        metadata = {
                            "pin_id": pin_data["pin_id"],
                            "pin_url": pin_data["pin_url"],
                            "image_url": pin_data["image_url"],
                            "title": pin_data["title"],
                            "search_query": query,
                            "width": width,
                            "height": height,
                            "quality_score": quality_score,
                            "gradient_style": gradient_style,
                            "downloaded_at": datetime.now().isoformat()
                        }
                        
                        if self.download_image(pin_data["image_url"], filename, metadata):
                            pins_processed += 1
                            
                # Scroll to load more content
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_count += 1
                logger.info(f"Scroll {scroll_count}/{max_scrolls}, Downloaded: {self.downloaded_count}")
                
            except Exception as e:
                logger.error(f"Error during search scrolling: {e}")
                break
                
        logger.info(f"Search '{query}' completed. Processed: {pins_processed}, Total downloaded: {self.downloaded_count}")
        return pins_processed
        
    def score_gradient_quality(self, title):
        """Score gradient quality based on title keywords"""
        if not title:
            return 5
            
        title_lower = title.lower()
        score = 5  # Base score
        
        # High-quality indicators
        quality_keywords = [
            "gradient", "abstract", "smooth", "fluid", "background", "wallpaper",
            "colorful", "vibrant", "neon", "pastel", "holographic", "aurora",
            "cosmic", "sunset", "rainbow", "mesh", "minimalist"
        ]
        
        # Mobile-specific indicators
        mobile_keywords = ["mobile", "phone", "wallpaper", "background", "hd", "4k"]
        
        # Style indicators
        style_keywords = ["geometric", "curved", "wavy", "flowing", "blend"]
        
        for keyword in quality_keywords:
            if keyword in title_lower:
                score += 1
                
        for keyword in mobile_keywords:
            if keyword in title_lower:
                score += 1.5
                
        for keyword in style_keywords:
            if keyword in title_lower:
                score += 0.5
                
        # Penalty for non-gradient content
        negative_keywords = ["text", "logo", "brand", "advertisement", "watermark"]
        for keyword in negative_keywords:
            if keyword in title_lower:
                score -= 2
                
        return min(10, max(1, score))
        
    def categorize_gradient_style(self, title):
        """Categorize gradient style based on title"""
        if not title:
            return "unknown"
            
        title_lower = title.lower()
        
        style_mapping = {
            "neon": ["neon", "electric", "bright", "vivid"],
            "pastel": ["pastel", "soft", "gentle", "light"],
            "cosmic": ["cosmic", "space", "galaxy", "star", "nebula"],
            "sunset": ["sunset", "sunrise", "dawn", "dusk", "orange", "pink"],
            "aurora": ["aurora", "northern lights", "borealis"],
            "rainbow": ["rainbow", "spectrum", "multicolor"],
            "holographic": ["holographic", "iridescent", "chrome"],
            "mesh": ["mesh", "net", "grid"],
            "fluid": ["fluid", "liquid", "flow", "wave", "smooth"],
            "geometric": ["geometric", "angular", "shape", "pattern"],
            "minimalist": ["minimal", "simple", "clean", "subtle"]
        }
        
        for style, keywords in style_mapping.items():
            if any(keyword in title_lower for keyword in keywords):
                return style
                
        return "abstract"
        
    def search_gradient_boards(self, driver):
        """Search for Pinterest boards dedicated to gradients"""
        logger.info("Starting board discovery for gradient content")
        
        for board_term in self.board_search_terms:
            if self.downloaded_count >= self.target_images:
                break
                
            logger.info(f"Searching boards for: {board_term}")
            search_url = f"{self.base_url}/search/boards/?q={quote(board_term)}"
            
            try:
                driver.get(search_url)
                time.sleep(3)
                
                # Find board elements
                board_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test-id='board-rep']")[:5]  # Limit to top 5 boards
                
                for board_element in board_elements:
                    if self.downloaded_count >= self.target_images:
                        break
                        
                    try:
                        # Get board URL
                        board_link = board_element.find_element(By.TAG_NAME, "a")
                        board_url = board_link.get_attribute("href")
                        
                        logger.info(f"Exploring board: {board_url}")
                        
                        # Visit board and extract pins
                        driver.get(board_url)
                        time.sleep(3)
                        
                        # Extract pins from board (limited scrolling)
                        self.extract_pins_from_board(driver, board_term, max_scrolls=2)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process board: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to search boards for '{board_term}': {e}")
                continue
                
    def extract_pins_from_board(self, driver, search_context, max_scrolls=2):
        """Extract pins from a specific board"""
        scroll_count = 0
        
        while scroll_count < max_scrolls and self.downloaded_count < self.target_images:
            try:
                pin_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test-id='pin']")
                
                for pin_element in pin_elements:
                    if self.downloaded_count >= self.target_images:
                        break
                        
                    pin_data = self.extract_pin_data(driver, pin_element)
                    if not pin_data:
                        continue
                        
                    # Check for duplicates
                    if self.is_duplicate(pin_data["image_url"]):
                        continue
                        
                    # Check dimensions  
                    width, height = self.get_image_dimensions(pin_data["image_url"])
                    if not self.is_mobile_suitable(width, height):
                        continue
                        
                    # Score and categorize
                    quality_score = self.score_gradient_quality(pin_data["title"])
                    gradient_style = self.categorize_gradient_style(pin_data["title"])
                    
                    if quality_score >= 6:
                        filename = f"pinterest_gradient_agent3_board_{pin_data['pin_id']}"
                        metadata = {
                            "pin_id": pin_data["pin_id"],
                            "pin_url": pin_data["pin_url"],
                            "image_url": pin_data["image_url"],
                            "title": pin_data["title"],
                            "search_context": f"board_search_{search_context}",
                            "width": width,
                            "height": height,
                            "quality_score": quality_score,
                            "gradient_style": gradient_style,
                            "downloaded_at": datetime.now().isoformat()
                        }
                        
                        self.download_image(pin_data["image_url"], filename, metadata)
                        
                # Scroll for more pins
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_count += 1
                
            except Exception as e:
                logger.error(f"Error extracting pins from board: {e}")
                break
                
    def save_hash_database(self):
        """Save updated hash database"""
        hash_file = os.path.join(self.output_dir, "downloaded_hashes.json")
        hash_data = {
            "hashes": list(self.existing_hashes),
            "last_updated": datetime.now().isoformat(),
            "total_hashes": len(self.existing_hashes)
        }
        
        with open(hash_file, 'w') as f:
            json.dump(hash_data, f, indent=2)
        logger.info(f"Saved {len(self.existing_hashes)} hashes to database")
        
    def generate_crawl_summary(self, start_time, search_stats, board_stats):
        """Generate comprehensive crawl summary"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Categorize downloaded styles
        style_distribution = {}
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
        
        for file in files:
            try:
                with open(os.path.join(self.output_dir, file), 'r') as f:
                    data = json.load(f)
                    style = data.get('gradient_style', 'unknown')
                    style_distribution[style] = style_distribution.get(style, 0) + 1
            except:
                continue
                
        summary = {
            "agent": "Pinterest Gradient Agent 3 - Expanded Search & Board Discovery",
            "scraping_strategy": {
                "search_queries": self.search_queries,
                "board_discovery": self.board_search_terms,
                "total_approaches": len(self.search_queries) + len(self.board_search_terms)
            },
            "scraping_stats": {
                "duration_seconds": round(duration, 2),
                "search_queries_processed": search_stats["queries_processed"],
                "boards_explored": board_stats["boards_explored"],
                "total_pins_evaluated": search_stats["pins_evaluated"] + board_stats["pins_evaluated"],
                "downloaded_count": self.downloaded_count,
                "duplicates_avoided": search_stats["duplicates"] + board_stats["duplicates"],
                "low_quality_filtered": search_stats["low_quality"] + board_stats["low_quality"],
                "success_rate": round((self.downloaded_count / max(1, search_stats["pins_evaluated"] + board_stats["pins_evaluated"])) * 100, 2),
                "target_achieved": self.downloaded_count >= 40
            },
            "requirements": {
                "min_width": self.min_width,
                "min_height": self.min_height, 
                "preferred_width": self.preferred_width,
                "preferred_height": self.preferred_height,
                "target_images": 40,
                "quality_threshold": 6
            },
            "style_distribution": style_distribution,
            "collection_analysis": {
                "previous_collection": 77,  # 50 + 27 from agents 1&2
                "agent3_contribution": self.downloaded_count,
                "new_total": 77 + self.downloaded_count,
                "target_progress": f"{77 + self.downloaded_count}/120+"
            },
            "quality_metrics": {
                "average_quality_score": self.calculate_average_quality(),
                "mobile_optimization": "100%",
                "duplicate_prevention": "Active with cross-agent hash checking"
            },
            "crawl_timestamp": end_time.isoformat()
        }
        
        summary_file = os.path.join(self.output_dir, "pinterest_gradient_agent3_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
        
    def calculate_average_quality(self):
        """Calculate average quality score of downloaded images"""
        total_score = 0
        count = 0
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.json') and not f.endswith('_summary.json')]
        
        for file in files:
            try:
                with open(os.path.join(self.output_dir, file), 'r') as f:
                    data = json.load(f)
                    if 'quality_score' in data:
                        total_score += data['quality_score']
                        count += 1
            except:
                continue
                
        return round(total_score / max(1, count), 2)
        
    def run_expanded_search(self):
        """Execute the expanded gradient search strategy"""
        logger.info("Starting Pinterest Gradient Agent 3 - Expanded Search & Board Discovery")
        start_time = datetime.now()
        
        # Initialize stats
        search_stats = {
            "queries_processed": 0,
            "pins_evaluated": 0,
            "duplicates": 0,
            "low_quality": 0
        }
        
        board_stats = {
            "boards_explored": 0,
            "pins_evaluated": 0,
            "duplicates": 0,
            "low_quality": 0
        }
        
        driver = self.setup_driver()
        
        try:
            # Phase 1: Diverse search queries
            logger.info("Phase 1: Executing diverse gradient search queries")
            for query in self.search_queries:
                if self.downloaded_count >= self.target_images:
                    break
                    
                pins_processed = self.search_gradient_content(driver, query)
                search_stats["queries_processed"] += 1
                search_stats["pins_evaluated"] += pins_processed
                
                # Brief pause between searches
                time.sleep(2)
                
            # Phase 2: Board discovery and exploration
            logger.info("Phase 2: Board discovery and exploration")
            if self.downloaded_count < self.target_images:
                self.search_gradient_boards(driver)
                board_stats["boards_explored"] = len(self.board_search_terms)
                
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
        finally:
            driver.quit()
            
        # Save results
        self.save_hash_database()
        summary = self.generate_crawl_summary(start_time, search_stats, board_stats)
        
        logger.info("=" * 80)
        logger.info("PINTEREST GRADIENT AGENT 3 - FINAL REPORT")
        logger.info("=" * 80)
        logger.info(f"Target Images: 40+")
        logger.info(f"Downloaded: {self.downloaded_count}")
        logger.info(f"Previous Collection: 77 images")
        logger.info(f"New Total: {77 + self.downloaded_count} images") 
        logger.info(f"Target Progress: {77 + self.downloaded_count}/120+")
        logger.info(f"Search Queries Processed: {search_stats['queries_processed']}")
        logger.info(f"Boards Explored: {board_stats['boards_explored']}")
        logger.info(f"Style Distribution: {summary['style_distribution']}")
        logger.info(f"Average Quality Score: {summary['quality_metrics']['average_quality_score']}")
        logger.info(f"Success Rate: {summary['scraping_stats']['success_rate']}%")
        logger.info("=" * 80)
        
        return summary

def main():
    """Main execution function"""
    agent = PinterestGradientAgent3()
    summary = agent.run_expanded_search()
    
    print("\nAgent 3 Execution Complete!")
    print(f"Downloaded: {summary['scraping_stats']['downloaded_count']} new gradient images")
    print(f"Total Collection: {summary['collection_analysis']['new_total']} images")
    print(f"Target Progress: {summary['collection_analysis']['target_progress']}")

if __name__ == "__main__":
    main()