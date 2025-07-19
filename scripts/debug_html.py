#!/usr/bin/env python3
"""
Debug HTML structure from Unsplash
"""

import requests
from bs4 import BeautifulSoup

def debug_unsplash_html():
    url = "https://unsplash.com/s/photos/wallpaper-4k?order_by=curated&orientation=portrait"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")
    
    # Save HTML to file for inspection
    with open('unsplash_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for various image elements
    print("\n=== IMG TAGS ===")
    img_tags = soup.find_all('img')
    print(f"Total img tags found: {len(img_tags)}")
    
    for i, img in enumerate(img_tags[:5]):  # Show first 5
        print(f"Img {i+1}:")
        print(f"  src: {img.get('src', 'None')}")
        print(f"  data-src: {img.get('data-src', 'None')}")
        print(f"  srcset: {img.get('srcset', 'None')}")
        print(f"  alt: {img.get('alt', 'None')}")
        print()
    
    # Look for data attributes that might contain image URLs
    print("=== ELEMENTS WITH UNSPLASH URLS ===")
    all_elements = soup.find_all(True)
    unsplash_elements = []
    
    for element in all_elements:
        for attr_name, attr_value in element.attrs.items():
            if isinstance(attr_value, str) and 'images.unsplash.com' in attr_value:
                unsplash_elements.append((element.name, attr_name, attr_value))
    
    print(f"Found {len(unsplash_elements)} elements with Unsplash URLs")
    for elem_name, attr_name, attr_value in unsplash_elements[:10]:  # Show first 10
        print(f"<{elem_name}> {attr_name}: {attr_value[:100]}...")
    
    # Look for script tags that might contain JSON data
    print("\n=== SCRIPT TAGS WITH JSON ===")
    script_tags = soup.find_all('script')
    json_scripts = []
    
    for script in script_tags:
        if script.string and ('images.unsplash.com' in script.string or 'photo' in script.string):
            json_scripts.append(script.string[:200])
    
    print(f"Found {len(json_scripts)} script tags with potential JSON data")
    for i, script_content in enumerate(json_scripts[:3]):  # Show first 3
        print(f"Script {i+1}: {script_content}...")
    
    # Look for specific class names that might indicate image containers
    print("\n=== COMMON IMAGE CONTAINER CLASSES ===")
    common_classes = ['photo', 'image', 'wallpaper', 'grid', 'card', 'item']
    
    for class_name in common_classes:
        elements = soup.find_all(class_=lambda x: x and class_name in str(x).lower())
        if elements:
            print(f"Elements with '{class_name}' in class: {len(elements)}")

if __name__ == '__main__':
    debug_unsplash_html()