#!/usr/bin/env python3
"""
Pinterest Gradient Scraper - Agent 1
Scrapes exactly 30 high-quality abstract gradient backgrounds from Pinterest
"""

import os
import time
import hashlib
import requests
import json
import re
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class PinterestGradientScraper:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.target_count = 30
        self.downloaded_hashes = set()
        self.downloaded_urls = set()
        self.downloaded_count = 0
        self.scroll_attempts = 0
        self.max_scroll_attempts = 150
        
        # Quality requirements for mobile wallpapers
        self.min_width = 1080
        self.min_height = 1920
        self.max_file_size = 15 * 1024 * 1024  # 15MB
        
        # Download session with retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.pinterest.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        })
        
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with optimal settings for Pinterest"""
        print("🚀 Setting up Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Use webdriver-manager to handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            raise

    def calculate_image_hash(self, image_content):
        """Calculate MD5 hash of image content for duplicate detection"""
        return hashlib.md5(image_content).hexdigest()

    def is_valid_gradient_image(self, image_content):
        """Validate if image is a high-quality gradient suitable for mobile wallpaper"""
        try:
            image = Image.open(BytesIO(image_content))
            width, height = image.size
            
            # Check minimum resolution for mobile wallpapers
            if width < self.min_width or height < self.min_height:
                return False, f"Resolution too low: {width}x{height} (need {self.min_width}x{self.min_height}+)"
            
            # Check file size
            if len(image_content) > self.max_file_size:
                return False, f"File too large: {len(image_content):,} bytes"
            
            # Check if image has gradient-like properties
            try:
                image_rgb = image.convert('RGB')
                # Sample pixels to check for color variation
                pixels = list(image_rgb.getdata())
                unique_colors = len(set(pixels[:min(10000, len(pixels))]))  # Sample first 10k pixels
                
                if unique_colors < 100:  # Too few colors for a gradient
                    return False, f"Insufficient color variation: {unique_colors} unique colors"
                
            except Exception:
                pass  # If color analysis fails, still proceed
            
            return True, f"Valid gradient: {width}x{height}, {len(image_content):,} bytes, {unique_colors if 'unique_colors' in locals() else 'N/A'} colors"
            
        except Exception as e:
            return False, f"Image validation error: {e}"

    def download_image(self, url, filename):
        """Download and validate a single image with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Check if we already have this image
                image_hash = self.calculate_image_hash(response.content)
                if image_hash in self.downloaded_hashes:
                    return False, f"Duplicate image (hash match, attempt {attempt + 1})"
                
                # Validate image quality
                is_valid, validation_msg = self.is_valid_gradient_image(response.content)
                if not is_valid:
                    return False, f"Quality check failed: {validation_msg}"
                
                # Save the image
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Track this download
                self.downloaded_hashes.add(image_hash)
                self.downloaded_urls.add(url)
                self.downloaded_count += 1
                
                return True, validation_msg
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Download attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2)
                    continue
                else:
                    return False, f"Download failed after {max_retries} attempts: {e}"

    def extract_pinterest_images(self):
        """Extract high-resolution image URLs from Pinterest pins"""
        image_urls = []
        
        try:
            # Wait for pins to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="pin"]'))
            )
            
            # Find all pin elements
            pins = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-id="pin"]')
            print(f"Found {len(pins)} pins on current view")
            
            for pin in pins:
                try:
                    # Look for image element within the pin
                    img_elements = pin.find_elements(By.TAG_NAME, 'img')
                    for img in img_elements:
                        src = img.get_attribute('src')
                        if src and ('pinimg.com' in src or 'pinterest' in src):
                            # Convert to high-resolution URL
                            high_res_url = self.get_high_res_url(src)
                            if high_res_url and high_res_url not in self.downloaded_urls and high_res_url not in image_urls:
                                image_urls.append(high_res_url)
                                
                except Exception as e:
                    continue
                    
        except TimeoutException:
            print("⚠️ Timeout waiting for pins to load")
        except Exception as e:
            print(f"⚠️ Error extracting images: {e}")
            
        return image_urls

    def get_high_res_url(self, original_url):
        """Convert Pinterest image URL to highest resolution version"""
        if not original_url:
            return None
            
        # Pinterest URL patterns for high resolution:
        if '/564x/' in original_url:
            return original_url.replace('/564x/', '/originals/')
        elif '/236x/' in original_url:
            return original_url.replace('/236x/', '/originals/')
        elif '/474x/' in original_url:
            return original_url.replace('/474x/', '/originals/')
        elif '/736x/' in original_url:
            return original_url.replace('/736x/', '/originals/')
        
        return original_url

    def enhanced_scroll(self):
        """Enhanced scrolling strategy with longer wait times"""
        try:
            # Get current page height
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down aggressively (8-12 page heights)
            scroll_amount = self.driver.execute_script("return window.innerHeight") * 10
            self.driver.execute_script(f"window.scrollTo(0, window.pageYOffset + {scroll_amount});")
            
            # Wait for content to load (6-8 seconds)
            time.sleep(7)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            self.scroll_attempts += 1
            
            if new_height > current_height:
                print(f"📈 Page height increased: {current_height:,} -> {new_height:,} (Scroll #{self.scroll_attempts})")
                return True
            else:
                print(f"📏 No new content loaded (Scroll #{self.scroll_attempts})")
                return False
                
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return False

    def scrape_pinterest_search(self, search_url):
        """Main scraping function with enhanced scrolling and retry logic"""
        print(f"🎯 TARGET: {self.target_count} high-quality gradient images")
        print(f"🔍 Scraping from: {search_url}")
        print(f"📁 Output directory: {self.output_dir}")
        
        try:
            # Navigate to Pinterest search
            print("🌐 Navigating to Pinterest...")
            self.driver.get(search_url)
            time.sleep(5)
            
            # Handle potential cookie/login popups
            try:
                # Dismiss any overlays
                overlay_selectors = [
                    '[aria-label="Close"]',
                    '[data-test-id="close-button"]',
                    '.close-button',
                    '[role="button"][aria-label="Close"]',
                    'button[aria-label="Close"]'
                ]
                
                for selector in overlay_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if button.is_displayed():
                                button.click()
                                time.sleep(1)
                                break
                    except:
                        pass
            except:
                pass
            
            consecutive_no_new_content = 0
            max_consecutive_fails = 7
            images_found_this_round = 0
            
            print("🔄 Starting image extraction process...")
            
            while self.downloaded_count < self.target_count and self.scroll_attempts < self.max_scroll_attempts:
                print(f"\n🔄 === SCROLL ROUND {self.scroll_attempts + 1}/{self.max_scroll_attempts} ===")
                print(f"📊 Progress: {self.downloaded_count}/{self.target_count} images downloaded")
                
                # Extract images from current view
                image_urls = self.extract_pinterest_images()
                new_images_found = 0
                
                print(f"🖼️  Found {len(image_urls)} potential image URLs")
                
                # Download new images
                for i, url in enumerate(image_urls):
                    if self.downloaded_count >= self.target_count:
                        print(f"🎉 TARGET REACHED! Downloaded {self.downloaded_count}/{self.target_count} images")
                        break
                        
                    filename = f"gradient_{self.downloaded_count + 1:03d}.jpg"
                    print(f"⬇️  Trying image {i+1}/{len(image_urls)}: {filename}")
                    
                    success, message = self.download_image(url, filename)
                    
                    if success:
                        new_images_found += 1
                        print(f"✅ Downloaded {filename}: {message}")
                    else:
                        print(f"❌ Skipped: {message}")
                
                # Update statistics
                images_found_this_round += new_images_found
                
                if new_images_found > 0:
                    consecutive_no_new_content = 0
                    print(f"🎉 Round summary: {new_images_found} new valid images downloaded!")
                else:
                    consecutive_no_new_content += 1
                    print(f"⚠️ No new valid images found ({consecutive_no_new_content}/{max_consecutive_fails})")
                
                # Check if we should continue scrolling
                if consecutive_no_new_content >= max_consecutive_fails:
                    print("🛑 Too many consecutive rounds without new content, stopping")
                    break
                
                # Check if we've reached our target
                if self.downloaded_count >= self.target_count:
                    print(f"🎯 SUCCESS! Target of {self.target_count} images achieved!")
                    break
                
                # Enhanced scroll to load more content
                scroll_success = self.enhanced_scroll()
                if not scroll_success:
                    consecutive_no_new_content += 1
            
            # Final summary
            print(f"\n🏁 === SCRAPING COMPLETE ===")
            print(f"📊 Final count: {self.downloaded_count}/{self.target_count} images")
            print(f"🔄 Total scroll attempts: {self.scroll_attempts}")
            print(f"📁 Images saved to: {self.output_dir}")
            
            if self.downloaded_count < self.target_count:
                print(f"⚠️ Warning: Only found {self.downloaded_count} images out of target {self.target_count}")
                print("💡 Consider running again or trying different search terms")
            else:
                print(f"✅ SUCCESS: Target of {self.target_count} images achieved!")
                
        except Exception as e:
            print(f"❌ Critical error during scraping: {e}")
        finally:
            self.driver.quit()
            print("🔒 Browser closed")

def main():
    """Main execution function"""
    output_dir = "/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/search_30"
    search_url = "https://in.pinterest.com/search/pins/?q=abstract%20gradient%20background&rs=ac&len=13&source_id=ac_li5uWglg&eq=abstract%20grad&etslf=7977"
    
    print("🚀 ======= PINTEREST GRADIENT SCRAPER - AGENT 1 =======")
    print(f"📁 Output directory: {output_dir}")
    print("🎯 Mission: Scrape exactly 30 high-quality gradient images")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize and run scraper
    scraper = PinterestGradientScraper(output_dir)
    scraper.scrape_pinterest_search(search_url)
    
    # Final report of downloaded files
    print(f"\n📋 === FINAL DOWNLOAD REPORT ===")
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        if files:
            print(f"📁 Total files downloaded: {len(files)}")
            print("📝 File list with details:")
            for i, filename in enumerate(sorted(files), 1):
                filepath = os.path.join(output_dir, filename)
                size = os.path.getsize(filepath)
                
                # Get image dimensions
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                        dimensions = f"{width}x{height}"
                except:
                    dimensions = "Unknown"
                
                print(f"  {i:2d}. {filename} ({size:,} bytes, {dimensions})")
                
            print(f"\n🎯 MISSION STATUS: {'✅ SUCCESS' if len(files) >= 30 else '⚠️ PARTIAL'}")
            print(f"📊 Achievement: {len(files)}/30 images downloaded")
        else:
            print("❌ No files were downloaded!")
    else:
        print("❌ Output directory not found!")

if __name__ == "__main__":
    main()