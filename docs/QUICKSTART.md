# WallCraft API - Quickstart Guide

Get up and running with the WallCraft wallpaper collection in 5 minutes!

## 🚀 Instant Access

No API keys, no authentication, no rate limits. Just start fetching wallpapers!

### 1. Test the API
```bash
# Get collection overview
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json

# Get nature wallpapers
curl https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json

# Download a wallpaper
curl -o nature_wallpaper.jpg "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/nature/nature_001.jpg"
```

### 2. Basic Integration

#### JavaScript (5 lines)
```javascript
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json')
  .then(response => response.json())
  .then(data => {
    const randomWallpaper = data.wallpapers[Math.floor(Math.random() * data.wallpapers.length)];
    console.log('Random wallpaper:', randomWallpaper.download_url);
  });
```

#### Python (6 lines)
```python
import requests
response = requests.get('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/abstract.json')
data = response.json()
random_wallpaper = data['wallpapers'][0]
print(f"Wallpaper: {random_wallpaper['title']} - {random_wallpaper['download_url']}")
```

#### Swift (iOS)
```swift
let url = URL(string: "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/space.json")!
URLSession.shared.dataTask(with: url) { data, response, error in
    if let data = data {
        // Parse JSON and use wallpapers
        print("Downloaded space wallpapers data")
    }
}.resume()
```

#### Kotlin (Android)
```kotlin
val url = "https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/gaming.json"
// Use Retrofit, OkHttp, or any HTTP library
```

## 📊 What You Get

- **1,244 wallpapers** across 20 categories
- **High resolution**: 1080×1920 (perfect for mobile)
- **Fast thumbnails**: 300×533 for quick loading
- **Rich metadata**: titles, tags, descriptions, photographer credits
- **Zero cost**: Hosted on GitHub, no server costs

## 🎯 Popular Categories

| Category | Count | Best For |
|----------|-------|----------|
| **Nature** | 284 | Landscape apps, meditation apps |
| **Architecture** | 275 | Design apps, urban photography |
| **Abstract** | 217 | Art apps, creative tools |
| **Space** | 86 | Science apps, astronomy |
| **Gaming** | 76 | Gaming apps, entertainment |

## 🔗 Essential Endpoints

```
# Master index (start here)
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json

# Category wallpapers  
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/{category}.json

# High-res image
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/wallpapers/{category}/{filename}

# Thumbnail
https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/thumbnails/{category}/{filename}
```

## 📱 Mobile App Examples

### React Native (Expo)
```jsx
import React, { useState, useEffect } from 'react';
import { View, Image, ScrollView } from 'react-native';

export default function WallpaperGallery() {
  const [wallpapers, setWallpapers] = useState([]);

  useEffect(() => {
    fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/nature.json')
      .then(response => response.json())
      .then(data => setWallpapers(data.wallpapers));
  }, []);

  return (
    <ScrollView>
      {wallpapers.map(wallpaper => (
        <Image
          key={wallpaper.id}
          source={{ uri: wallpaper.thumbnail_url }}
          style={{ width: 200, height: 355 }}
        />
      ))}
    </ScrollView>
  );
}
```

### Flutter
```dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class WallpaperGallery extends StatefulWidget {
  @override
  _WallpaperGalleryState createState() => _WallpaperGalleryState();
}

class _WallpaperGalleryState extends State<WallpaperGallery> {
  List wallpapers = [];

  @override
  void initState() {
    super.initState();
    fetchWallpapers();
  }

  fetchWallpapers() async {
    final response = await http.get(Uri.parse(
      'https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/abstract.json'
    ));
    
    if (response.statusCode == 200) {
      setState(() {
        wallpapers = json.decode(response.body)['wallpapers'];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 9/16,
      ),
      itemCount: wallpapers.length,
      itemBuilder: (context, index) {
        return Image.network(
          wallpapers[index]['thumbnail_url'],
          fit: BoxFit.cover,
        );
      },
    );
  }
}
```

## 🎨 Web Examples

### HTML + JavaScript
```html
<!DOCTYPE html>
<html>
<head>
    <title>WallCraft Gallery</title>
    <style>
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
        .wallpaper { aspect-ratio: 9/16; border-radius: 8px; overflow: hidden; }
        .wallpaper img { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>
    <div class="gallery" id="gallery"></div>

    <script>
        fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/cyberpunk.json')
            .then(response => response.json())
            .then(data => {
                const gallery = document.getElementById('gallery');
                data.wallpapers.forEach(wallpaper => {
                    const div = document.createElement('div');
                    div.className = 'wallpaper';
                    div.innerHTML = `<img src="${wallpaper.thumbnail_url}" alt="${wallpaper.title}">`;
                    gallery.appendChild(div);
                });
            });
    </script>
</body>
</html>
```

### Vue.js
```vue
<template>
  <div class="gallery">
    <div v-for="wallpaper in wallpapers" :key="wallpaper.id" class="wallpaper">
      <img :src="wallpaper.thumbnail_url" :alt="wallpaper.title" />
      <p>{{ wallpaper.title }}</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  setup() {
    const wallpapers = ref([])

    onMounted(async () => {
      const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/gaming.json')
      const data = await response.json()
      wallpapers.value = data.wallpapers
    })

    return { wallpapers }
  }
}
</script>

<style>
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.wallpaper img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
}
</style>
```

## 🔧 Advanced Features

### Search Across Categories
```javascript
async function searchWallpapers(query) {
  const categories = ['nature', 'abstract', 'space', 'architecture'];
  const results = [];
  
  for (const category of categories) {
    const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
    const data = await response.json();
    
    const matches = data.wallpapers.filter(wallpaper =>
      wallpaper.title.toLowerCase().includes(query.toLowerCase()) ||
      wallpaper.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    );
    
    results.push(...matches);
  }
  
  return results;
}

// Usage
searchWallpapers('mountain').then(results => {
  console.log(`Found ${results.length} mountain wallpapers`);
});
```

### Random Wallpaper Picker
```javascript
async function getRandomWallpaper(category = null) {
  let wallpapers;
  
  if (category) {
    const response = await fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${category}.json`);
    const data = await response.json();
    wallpapers = data.wallpapers;
  } else {
    const response = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json');
    const data = await response.json();
    wallpapers = data.featured;
  }
  
  return wallpapers[Math.floor(Math.random() * wallpapers.length)];
}

// Get random nature wallpaper
getRandomWallpaper('nature').then(wallpaper => {
  console.log('Random nature wallpaper:', wallpaper.title);
});
```

### Lazy Loading with Intersection Observer
```javascript
function setupLazyLoading() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.remove('lazy');
        observer.unobserve(img);
      }
    });
  });

  document.querySelectorAll('img[data-src]').forEach(img => {
    observer.observe(img);
  });
}
```

## 📈 Performance Tips

### 1. Use Thumbnails First
```javascript
// Load thumbnail immediately, full image later
function progressiveLoad(wallpaper) {
  const img = new Image();
  img.src = wallpaper.thumbnail_url; // Fast load
  
  // Load full resolution in background
  const fullImg = new Image();
  fullImg.onload = () => img.src = fullImg.src;
  fullImg.src = wallpaper.download_url;
  
  return img;
}
```

### 2. Cache API Responses
```javascript
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function cachedFetch(url) {
  const cached = cache.get(url);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  
  const response = await fetch(url);
  const data = await response.json();
  cache.set(url, { data, timestamp: Date.now() });
  return data;
}
```

### 3. Batch Load Categories
```javascript
async function loadAllCategories() {
  const index = await fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json')
    .then(r => r.json());
  
  const promises = index.categories.map(cat =>
    fetch(`https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/categories/${cat.id}.json`)
      .then(r => r.json())
  );
  
  const results = await Promise.all(promises);
  return results.reduce((acc, data) => {
    acc[data.category] = data.wallpapers;
    return acc;
  }, {});
}
```

## 🎯 Next Steps

1. **Explore the full API**: Check out [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)
2. **Flutter developers**: See [FLUTTER_INTEGRATION.md](./FLUTTER_INTEGRATION.md) 
3. **Add to your app**: Start with thumbnails, add full-res downloads
4. **Contribute**: Report issues or suggest new categories
5. **Star the repo**: Help others discover this resource

## 🤝 Support

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Integration help and showcases
- **Examples**: Share your implementations

---

**Ready to build something amazing? Start with one API call and grow from there!**

```javascript
// Your journey starts here 🚀
fetch('https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/index.json')
  .then(response => response.json())
  .then(data => console.log(`${data.totalWallpapers} wallpapers ready to use!`));
```