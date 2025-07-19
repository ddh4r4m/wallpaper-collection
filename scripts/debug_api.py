#!/usr/bin/env python3
"""
Debug Unsplash API response
"""

import requests

def debug_unsplash_api():
    url = "https://unsplash.com/napi/search/photos"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://unsplash.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    params = {
        'query': '4k wallpaper',
        'orientation': 'portrait',
        'order_by': 'curated',
        'page': 1,
        'per_page': 5,
        'plus': 'none'
    }
    
    try:
        print(f"Testing URL: {url}")
        print(f"Params: {params}")
        
        # Remove Accept-Encoding to avoid compression issues
        headers_no_encoding = headers.copy()
        del headers_no_encoding['Accept-Encoding']
        
        response = requests.get(url, params=params, headers=headers_no_encoding, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content Length: {len(response.text)}")
        print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
        
        print("\n=== RESPONSE CONTENT ===")
        print(response.text[:500])
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n=== JSON PARSED SUCCESSFULLY ===")
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                if 'results' in data:
                    print(f"Results count: {len(data['results'])}")
            except Exception as e:
                print(f"\n=== JSON PARSE ERROR ===")
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    debug_unsplash_api()