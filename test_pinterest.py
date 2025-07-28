#!/usr/bin/env python3
"""
Test script for Pinterest scraper functionality
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_pinterest_scraper():
    """Test Pinterest scraper with a small sample"""
    print("🧪 Testing Pinterest scraper...")
    
    # Create test directory
    test_dir = Path("pinterest_test")
    test_dir.mkdir(exist_ok=True)
    
    # Test with a simple category and low limit
    test_category = "nature"
    test_limit = 3
    
    print(f"📊 Testing category: {test_category}")
    print(f"📊 Testing limit: {test_limit} images")
    print(f"📁 Output directory: {test_dir}")
    
    try:
        # Run Pinterest scraper
        cmd = [
            sys.executable,
            "scripts/pinterest_scraper.py",
            "--category", test_category,
            "--limit", str(test_limit),
            "--output", str(test_dir),
            "--headless",
            "--min-width", "1920",
            "--min-height", "1080"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Pinterest scraper completed successfully!")
            print(f"📝 Output: {result.stdout}")
            
            # Check for downloaded files
            downloaded_files = list(test_dir.glob("*.jpg"))
            metadata_files = list(test_dir.glob("*.json"))
            
            print(f"📊 Downloaded images: {len(downloaded_files)}")
            print(f"📊 Metadata files: {len(metadata_files)}")
            
            if downloaded_files:
                print("🎉 Test passed! Pinterest scraper is working.")
                for file in downloaded_files:
                    print(f"  📸 {file.name}")
            else:
                print("⚠️  Warning: No images downloaded, but scraper ran without errors.")
                
        else:
            print("❌ Pinterest scraper failed!")
            print(f"📝 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Pinterest scraper test timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    return True

def test_batch_processor():
    """Test batch processor with Pinterest integration"""
    print("\n🧪 Testing batch processor with Pinterest...")
    
    test_category = "abstract"
    test_limit = 5
    
    try:
        cmd = [
            sys.executable,
            "scripts/batch_processor.py",
            "--categories", test_category,
            "--sources", "pinterest",
            "--limit", str(test_limit)
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Batch processor with Pinterest completed successfully!")
            print(f"📝 Output: {result.stdout}")
            return True
        else:
            print("❌ Batch processor failed!")
            print(f"📝 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Batch processor test timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Batch processor test failed with exception: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 Pinterest Scraper Test Suite")
    print("=" * 50)
    
    # Check dependencies
    try:
        import selenium
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ Dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return
    
    # Test 1: Pinterest scraper standalone
    test1_passed = test_pinterest_scraper()
    
    # Test 2: Batch processor integration (if test 1 passed)
    test2_passed = False
    if test1_passed:
        test2_passed = test_batch_processor()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"  Pinterest Scraper: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Batch Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Pinterest scraping is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()