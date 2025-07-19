# Flutter API Race Condition Implementation Guide

## Overview
This guide demonstrates how to implement a race condition where the UI updates as soon as the fastest API returns a response, rather than waiting for all APIs to complete.

## Core Implementation Approaches

### 1. Using Future.any() (Recommended)

```dart
class WallpaperService {
  final List<ApiProvider> _providers = [
    ApiProvider1(),
    ApiProvider2(),
    ApiProvider3(),
    ApiProvider4(),
  ];

  Future<List<WallpaperModel>> fetchWallpapers() async {
    // Create futures for all API calls
    final futures = _providers.map((provider) => provider.fetchWallpapers());
    
    // Return as soon as the first one completes
    return await Future.any(futures);
  }
}
```

### 2. Using Stream-Based Approach (More Control)

```dart
class WallpaperService {
  final List<ApiProvider> _providers = [
    ApiProvider1(),
    ApiProvider2(),
    ApiProvider3(),
    ApiProvider4(),
  ];

  Stream<List<WallpaperModel>> fetchWallpapersStream() {
    final StreamController<List<WallpaperModel>> controller = 
        StreamController<List<WallpaperModel>>();
    
    bool hasEmitted = false;
    
    for (final provider in _providers) {
      provider.fetchWallpapers().then((wallpapers) {
        if (!hasEmitted && !controller.isClosed) {
          hasEmitted = true;
          controller.add(wallpapers);
          controller.close();
        }
      }).catchError((error) {
        // Handle individual provider errors
        print('Provider ${provider.name} failed: $error');
      });
    }
    
    return controller.stream;
  }
}
```

### 3. Using Completer for Fine-Grained Control

```dart
class WallpaperService {
  Future<List<WallpaperModel>> fetchWallpapers() async {
    final Completer<List<WallpaperModel>> completer = Completer();
    final List<Future<List<WallpaperModel>>> futures = [];
    
    for (final provider in _providers) {
      final future = provider.fetchWallpapers();
      futures.add(future);
      
      future.then((result) {
        if (!completer.isCompleted) {
          completer.complete(result);
        }
      }).catchError((error) {
        print('Provider ${provider.name} failed: $error');
        // Don't complete with error unless all fail
      });
    }
    
    // Optional: Handle case where all APIs fail
    Future.wait(futures).catchError((error) {
      if (!completer.isCompleted) {
        completer.completeError('All providers failed');
      }
    });
    
    return completer.future;
  }
}
```

## UI Implementation

### Using FutureBuilder

```dart
class WallpaperScreen extends StatefulWidget {
  @override
  _WallpaperScreenState createState() => _WallpaperScreenState();
}

class _WallpaperScreenState extends State<WallpaperScreen> {
  final WallpaperService _wallpaperService = WallpaperService();
  late Future<List<WallpaperModel>> _wallpapersFuture;
  
  @override
  void initState() {
    super.initState();
    _wallpapersFuture = _wallpaperService.fetchWallpapers();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Wallpapers')),
      body: FutureBuilder<List<WallpaperModel>>(
        future: _wallpapersFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return _buildShimmerGrid();
          } else if (snapshot.hasError) {
            return _buildErrorWidget(snapshot.error.toString());
          } else if (snapshot.hasData) {
            return _buildWallpaperGrid(snapshot.data!);
          }
          return Container();
        },
      ),
    );
  }
  
  Widget _buildShimmerGrid() {
    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: 10, // Show 10 shimmer items
      itemBuilder: (context, index) => ShimmerContainer(),
    );
  }
}
```

### Using StreamBuilder (Recommended for Real-time Updates)

```dart
class WallpaperScreen extends StatefulWidget {
  @override
  _WallpaperScreenState createState() => _WallpaperScreenState();
}

class _WallpaperScreenState extends State<WallpaperScreen> {
  final WallpaperService _wallpaperService = WallpaperService();
  late Stream<List<WallpaperModel>> _wallpapersStream;
  
  @override
  void initState() {
    super.initState();
    _wallpapersStream = _wallpaperService.fetchWallpapersStream();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Wallpapers')),
      body: StreamBuilder<List<WallpaperModel>>(
        stream: _wallpapersStream,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return _buildShimmerGrid();
          } else if (snapshot.hasError) {
            return _buildErrorWidget(snapshot.error.toString());
          } else if (snapshot.hasData) {
            return _buildWallpaperGrid(snapshot.data!);
          }
          return Container();
        },
      ),
    );
  }
}
```

## Advanced Implementation with Fallback

```dart
class AdvancedWallpaperService {
  final List<ApiProvider> _providers = [
    ApiProvider1(),
    ApiProvider2(),
    ApiProvider3(),
    ApiProvider4(),
  ];
  
  Stream<WallpaperResult> fetchWallpapersWithFallback() async* {
    final StreamController<WallpaperResult> controller = 
        StreamController<WallpaperResult>();
    
    // Track completed providers
    final Set<String> completedProviders = {};
    final List<String> failedProviders = [];
    
    bool hasSuccessfulResponse = false;
    
    for (final provider in _providers) {
      provider.fetchWallpapers().then((wallpapers) {
        completedProviders.add(provider.name);
        
        if (!hasSuccessfulResponse) {
          hasSuccessfulResponse = true;
          yield WallpaperResult.success(
            wallpapers: wallpapers,
            provider: provider.name,
          );
        }
      }).catchError((error) {
        failedProviders.add(provider.name);
        
        // If all providers failed
        if (failedProviders.length == _providers.length) {
          yield WallpaperResult.failure(
            error: 'All providers failed',
            failedProviders: failedProviders,
          );
        }
      });
    }
  }
}

class WallpaperResult {
  final List<WallpaperModel>? wallpapers;
  final String? provider;
  final String? error;
  final List<String>? failedProviders;
  final bool isSuccess;
  
  WallpaperResult.success({
    required this.wallpapers,
    required this.provider,
  }) : isSuccess = true, error = null, failedProviders = null;
  
  WallpaperResult.failure({
    required this.error,
    required this.failedProviders,
  }) : isSuccess = false, wallpapers = null, provider = null;
}
```

## Error Handling and Edge Cases

### 1. Network Timeout Handling

```dart
class ApiProvider {
  final String baseUrl;
  final Duration timeout;
  
  ApiProvider({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 10),
  });
  
  Future<List<WallpaperModel>> fetchWallpapers() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/wallpapers'),
      ).timeout(timeout);
      
      if (response.statusCode == 200) {
        return parseWallpapers(response.body);
      } else {
        throw ApiException('HTTP ${response.statusCode}');
      }
    } on TimeoutException {
      throw ApiException('Request timeout');
    } on SocketException {
      throw ApiException('Network error');
    } catch (e) {
      throw ApiException('Unknown error: $e');
    }
  }
}
```

### 2. Progressive Loading with Background Updates

```dart
class ProgressiveWallpaperService {
  Stream<List<WallpaperModel>> fetchWallpapersProgressive() async* {
    final List<WallpaperModel> allWallpapers = [];
    final List<Future<List<WallpaperModel>>> futures = 
        _providers.map((p) => p.fetchWallpapers()).toList();
    
    // Yield results as they come in
    for (int i = 0; i < futures.length; i++) {
      try {
        final result = await futures[i];
        allWallpapers.addAll(result);
        yield List.from(allWallpapers);
      } catch (e) {
        print('Provider ${i + 1} failed: $e');
        // Continue with other providers
      }
    }
  }
}
```

### 3. Caching and Offline Support

```dart
class CachedWallpaperService {
  final SharedPreferences _prefs;
  final Duration cacheExpiry;
  
  CachedWallpaperService({
    required SharedPreferences prefs,
    this.cacheExpiry = const Duration(hours: 1),
  }) : _prefs = prefs;
  
  Future<List<WallpaperModel>> fetchWallpapers() async {
    // Check cache first
    final cachedData = _getCachedData();
    if (cachedData != null) {
      // Return cached data immediately
      return cachedData;
    }
    
    // Fetch from APIs
    final futures = _providers.map((p) => p.fetchWallpapers());
    final result = await Future.any(futures);
    
    // Cache the result
    _cacheData(result);
    
    return result;
  }
  
  List<WallpaperModel>? _getCachedData() {
    final cachedJson = _prefs.getString('wallpapers_cache');
    final cacheTime = _prefs.getInt('wallpapers_cache_time') ?? 0;
    
    if (cachedJson != null && 
        DateTime.now().millisecondsSinceEpoch - cacheTime < 
        cacheExpiry.inMilliseconds) {
      return parseWallpapers(cachedJson);
    }
    
    return null;
  }
  
  void _cacheData(List<WallpaperModel> wallpapers) {
    _prefs.setString('wallpapers_cache', jsonEncode(wallpapers));
    _prefs.setInt('wallpapers_cache_time', DateTime.now().millisecondsSinceEpoch);
  }
}
```

## Performance Optimizations

### 1. Image Preloading

```dart
class WallpaperGrid extends StatelessWidget {
  final List<WallpaperModel> wallpapers;
  
  const WallpaperGrid({Key? key, required this.wallpapers}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: wallpapers.length,
      itemBuilder: (context, index) {
        final wallpaper = wallpapers[index];
        return WallpaperTile(wallpaper: wallpaper);
      },
    );
  }
}

class WallpaperTile extends StatelessWidget {
  final WallpaperModel wallpaper;
  
  const WallpaperTile({Key? key, required this.wallpaper}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: CachedNetworkImage(
        imageUrl: wallpaper.thumbnailUrl,
        placeholder: (context, url) => ShimmerContainer(),
        errorWidget: (context, url, error) => Icon(Icons.error),
        fit: BoxFit.cover,
      ),
    );
  }
}
```

### 2. Lazy Loading

```dart
class LazyWallpaperGrid extends StatefulWidget {
  final List<WallpaperModel> wallpapers;
  
  const LazyWallpaperGrid({Key? key, required this.wallpapers}) : super(key: key);
  
  @override
  _LazyWallpaperGridState createState() => _LazyWallpaperGridState();
}

class _LazyWallpaperGridState extends State<LazyWallpaperGrid> {
  final ScrollController _scrollController = ScrollController();
  int _displayedItems = 20;
  
  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }
  
  void _onScroll() {
    if (_scrollController.position.pixels >= 
        _scrollController.position.maxScrollExtent * 0.8) {
      setState(() {
        _displayedItems = math.min(
          _displayedItems + 20,
          widget.wallpapers.length,
        );
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      controller: _scrollController,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: _displayedItems,
      itemBuilder: (context, index) {
        if (index < widget.wallpapers.length) {
          return WallpaperTile(wallpaper: widget.wallpapers[index]);
        }
        return ShimmerContainer();
      },
    );
  }
}
```

## Common Edge Cases and Solutions

### 1. All APIs Fail
```dart
Future<List<WallpaperModel>> fetchWallpapersWithFallback() async {
  final futures = _providers.map((p) => p.fetchWallpapers());
  
  try {
    return await Future.any(futures);
  } catch (e) {
    // Check if we have cached data
    final cachedData = await _getCachedData();
    if (cachedData != null) {
      return cachedData;
    }
    
    // Return empty list or throw
    throw Exception('No wallpapers available');
  }
}
```

### 2. Duplicate Images from Different APIs
```dart
List<WallpaperModel> removeDuplicates(List<WallpaperModel> wallpapers) {
  final seen = <String>{};
  return wallpapers.where((wallpaper) {
    final key = wallpaper.imageUrl;
    if (seen.contains(key)) {
      return false;
    }
    seen.add(key);
    return true;
  }).toList();
}
```

### 3. Invalid JSON Response
```dart
List<WallpaperModel> parseWallpapers(String jsonString) {
  try {
    final jsonData = jsonDecode(jsonString);
    if (jsonData is List) {
      return jsonData.map((item) => WallpaperModel.fromJson(item)).toList();
    } else if (jsonData is Map && jsonData.containsKey('wallpapers')) {
      final wallpapers = jsonData['wallpapers'] as List;
      return wallpapers.map((item) => WallpaperModel.fromJson(item)).toList();
    }
    return [];
  } catch (e) {
    print('JSON parsing error: $e');
    return [];
  }
}
```

## Testing Strategy

### Unit Tests
```dart
void main() {
  group('WallpaperService', () {
    test('should return fastest API response', () async {
      final service = WallpaperService();
      final result = await service.fetchWallpapers();
      expect(result, isA<List<WallpaperModel>>());
    });
    
    test('should handle API failures gracefully', () async {
      final service = WallpaperService();
      // Mock API failures
      expect(() => service.fetchWallpapers(), throwsA(isA<Exception>()));
    });
  });
}
```

### Integration Tests
```dart
void main() {
  testWidgets('WallpaperScreen shows content after API response', (tester) async {
    await tester.pumpWidget(MyApp());
    
    // Initially shows shimmer
    expect(find.byType(ShimmerContainer), findsWidgets);
    
    // Wait for API response
    await tester.pumpAndSettle();
    
    // Should show wallpapers
    expect(find.byType(WallpaperTile), findsWidgets);
  });
}
```

## Key Takeaways

1. **Use Future.any()** for simple race conditions
2. **Implement proper error handling** for each API
3. **Cache responses** to improve user experience
4. **Use shimmer loading** while waiting for the first response
5. **Consider network conditions** and timeouts
6. **Test thoroughly** with different network scenarios
7. **Handle edge cases** like all APIs failing or invalid responses
8. **Optimize for performance** with lazy loading and image caching
