#!/usr/bin/env python3
"""
Fast Basketball Wallpaper Scraper - Agent 3
Optimized for quick completion of exactly 40 basketball wallpapers
"""

import os
import json
import time
import random
import hashlib
import requests
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FastBasketballScraper:
    def __init__(self):
        self.target_count = 40
        self.downloaded_images = []
        self.existing_hashes = set()
        self.setup_driver()
        
        # Focused basketball search terms
        self.search_terms = [
            "basketball wallpaper hd",
            "NBA player wallpaper",
            "basketball court mobile",
            "basketball phone background",
            "NBA wallpaper 1080p"
        ]

    def setup_driver(self):
        """Quick Chrome setup"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Faster without GUI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-images")  # Faster loading
        
        self.driver = webdriver.Chrome(options=chrome_options)

    def search_and_download(self, search_term, max_images=10):
        """Fast search and download for basketball images"""
        try:
            formatted_term = search_term.replace(" ", "%20")
            url = f"https://in.pinterest.com/search/pins/?q={formatted_term}"
            
            print(f"Searching: {search_term}")
            self.driver.get(url)
            time.sleep(5)
            
            # Quick scroll and collect
            for i in range(3):  # Reduced scrolls for speed
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            
            # Fast image collection
            images = self.driver.find_elements(By.TAG_NAME, 'img')[:50]  # Limit for speed
            
            downloaded = 0
            for img in images:
                if len(self.downloaded_images) >= self.target_count or downloaded >= max_images:
                    break
                    
                try:
                    img_url = img.get_attribute('src')
                    if img_url and 'pinimg.com' in img_url and '236x' not in img_url:
                        if self.quick_download(img_url, search_term):
                            downloaded += 1
                except:
                    continue
            
            return downloaded
            
        except Exception as e:
            print(f"Search error: {e}")
            return 0

    def quick_download(self, img_url, search_term):
        """Fast download with basic validation"""
        try:
            # Get higher quality URL
            high_url = img_url.replace('236x', '736x').replace('474x', '736x')
            
            response = requests.get(high_url, timeout=10)
            if response.status_code != 200:
                return False
            
            # Quick hash check
            img_hash = hashlib.md5(response.content).hexdigest()
            if img_hash in self.existing_hashes:
                return False
            
            # Basic image validation
            try:
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                
                # Must be reasonable size for mobile
                if width < 500 or height < 500:
                    return False
                    
            except:
                return False
            
            # Save image
            filename = f"basketball_{len(self.downloaded_images) + 1:03d}_{img_hash[:8]}.jpg"
            filepath = os.path.join("/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/basketball_40", filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Save metadata
            metadata = {
                'filename': filename,
                'search_term': search_term,
                'dimensions': f"{width}x{height}",
                'file_size': len(response.content),
                'hash': img_hash
            }
            
            metadata_path = filepath.replace('.jpg', '.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.downloaded_images.append(metadata)
            self.existing_hashes.add(img_hash)
            
            print(f"Downloaded {len(self.downloaded_images)}/{self.target_count}: {filename}")
            return True
            
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def run_fast_search(self):
        """Run fast basketball search"""
        print(f"Starting fast basketball search for {self.target_count} images")
        
        images_per_term = self.target_count // len(self.search_terms) + 2
        
        for search_term in self.search_terms:
            if len(self.downloaded_images) >= self.target_count:
                break
                
            downloaded = self.search_and_download(search_term, images_per_term)
            print(f"Got {downloaded} from '{search_term}'. Total: {len(self.downloaded_images)}")
            
            time.sleep(2)  # Brief pause
        
        print(f"\nFast search complete: {len(self.downloaded_images)}/{self.target_count}")

    def generate_report(self):
        """Generate final report"""
        report = {
            'agent': 'Agent 3 - Basketball Specialist',
            'target': self.target_count,
            'downloaded': len(self.downloaded_images),
            'success_rate': f"{(len(self.downloaded_images)/self.target_count)*100:.1f}%",
            'status': 'COMPLETE' if len(self.downloaded_images) == self.target_count else 'PARTIAL',
            'images': [img['filename'] for img in self.downloaded_images]
        }
        
        with open('/Users/dharamdhurandhar/Developer/AndroidApps/WallpaperCollection/crawl_cache/pinterest/basketball_40/AGENT_3_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

    def cleanup(self):
        """Cleanup"""
        try:
            self.driver.quit()
        except:
            pass

def main():
    scraper = FastBasketballScraper()
    
    try:
        scraper.run_fast_search()
        report = scraper.generate_report()
        
        print("\n" + "="*50)
        print("🏀 AGENT 3 BASKETBALL MISSION REPORT 🏀")
        print("="*50)
        print(f"Target: {report['target']}")
        print(f"Downloaded: {report['downloaded']}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"Status: {report['status']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()