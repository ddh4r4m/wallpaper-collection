# Flutter Integration Guide for WallCraft API

Complete Flutter integration guide for the WallCraft wallpaper collection with examples, best practices, and production-ready code.

## 📚 Table of Contents

1. [Setup and Dependencies](#setup-and-dependencies)
2. [Data Models](#data-models)
3. [API Service](#api-service)
4. [State Management with BLoC](#state-management-with-bloc)
5. [UI Components](#ui-components)
6. [Caching and Performance](#caching-and-performance)
7. [Download and Set Wallpaper](#download-and-set-wallpaper)
8. [Complete Example App](#complete-example-app)

## 🚀 Setup and Dependencies

### pubspec.yaml
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP and networking
  http: ^1.1.0
  dio: ^5.3.0
  
  # State management
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  
  # UI and images
  cached_network_image: ^3.3.0
  flutter_staggered_grid_view: ^0.7.0
  shimmer: ^3.0.0
  
  # Storage and caching
  shared_preferences: ^2.2.2
  path_provider: ^2.1.1
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # File handling
  permission_handler: ^11.0.1
  path: ^1.8.3
  gallery_saver: ^2.3.2
  
  # Utils
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

dev_dependencies:
  # Code generation
  build_runner: ^2.4.7
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  hive_generator: ^2.0.1
```

## 📄 Data Models

### Core Models with Freezed
```dart
// lib/models/wallpaper.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'wallpaper.freezed.dart';
part 'wallpaper.g.dart';

@freezed
class Wallpaper with _$Wallpaper {
  const factory Wallpaper({
    required String id,
    required String title,
    required String description,
    required int width,
    required int height,
    required List<String> tags,
    @JsonKey(name: 'download_url') required String downloadUrl,
    @JsonKey(name: 'thumbnail_url') required String thumbnailUrl,
    @JsonKey(name: 'file_size') required int fileSize,
    required String filename,
    required String category,
    String? photographer,
    @JsonKey(name: 'alt_text') String? altText,
    @JsonKey(name: 'scraped_at') String? scrapedAt,
  }) = _Wallpaper;

  factory Wallpaper.fromJson(Map<String, dynamic> json) =>
      _$WallpaperFromJson(json);
}

// lib/models/category.dart
@freezed
class Category with _$Category {
  const factory Category({
    required String id,
    required String name,
    required int count,
    required String description,
  }) = _Category;

  factory Category.fromJson(Map<String, dynamic> json) =>
      _$CategoryFromJson(json);
}

// lib/models/api_response.dart
@freezed
class CategoryResponse with _$CategoryResponse {
  const factory CategoryResponse({
    required String category,
    required String name,
    required String description,
    required int count,
    @JsonKey(name: 'lastUpdated') required String lastUpdated,
    required List<Wallpaper> wallpapers,
  }) = _CategoryResponse;

  factory CategoryResponse.fromJson(Map<String, dynamic> json) =>
      _$CategoryResponseFromJson(json);
}

@freezed
class IndexResponse with _$IndexResponse {
  const factory IndexResponse({
    required String version,
    @JsonKey(name: 'lastUpdated') required String lastUpdated,
    @JsonKey(name: 'totalWallpapers') required int totalWallpapers,
    required List<Category> categories,
    required List<Wallpaper> featured,
  }) = _IndexResponse;

  factory IndexResponse.fromJson(Map<String, dynamic> json) =>
      _$IndexResponseFromJson(json);
}
```

## 🌐 API Service

### HTTP Service with Dio
```dart
// lib/services/wallpaper_api_service.dart
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../models/models.dart';

class WallpaperApiService {
  static const String _baseUrl = 
    'https://raw.githubusercontent.com/ddh4r4m/wallpaper-collection/main/';
  
  late final Dio _dio;
  
  WallpaperApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => debugPrint(obj.toString()),
      ));
    }
  }
  
  Future<IndexResponse> getIndex() async {
    try {
      final response = await _dio.get('index.json');
      return IndexResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Future<CategoryResponse> getCategoryWallpapers(String category) async {
    try {
      final response = await _dio.get('categories/$category.json');
      return CategoryResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Future<List<Wallpaper>> searchWallpapers({
    required String query,
    List<String>? categories,
  }) async {
    try {
      // Get available categories if not provided
      final searchCategories = categories ?? 
        (await getIndex()).categories.map((c) => c.id).toList();
      
      final List<Wallpaper> results = [];
      
      // Search across all specified categories
      for (final category in searchCategories) {
        try {
          final categoryResponse = await getCategoryWallpapers(category);
          final matches = categoryResponse.wallpapers.where((wallpaper) {
            final queryLower = query.toLowerCase();
            return wallpaper.title.toLowerCase().contains(queryLower) ||
                wallpaper.description.toLowerCase().contains(queryLower) ||
                wallpaper.tags.any((tag) => tag.toLowerCase().contains(queryLower));
          }).toList();
          
          results.addAll(matches);
        } catch (e) {
          debugPrint('Error searching category $category: $e');
        }
      }
      
      return results;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Exception _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return Exception('Connection timeout. Please check your internet connection.');
      case DioExceptionType.badResponse:
        return Exception('Server error: ${error.response?.statusCode}');
      case DioExceptionType.unknown:
        return Exception('Network error. Please try again.');
      default:
        return Exception('Something went wrong. Please try again.');
    }
  }
}
```

## 📦 State Management with BLoC

### Wallpaper BLoC
```dart
// lib/blocs/wallpaper/wallpaper_event.dart
import 'package:equatable/equatable.dart';

abstract class WallpaperEvent extends Equatable {
  const WallpaperEvent();

  @override
  List<Object?> get props => [];
}

class LoadCategories extends WallpaperEvent {}

class LoadCategoryWallpapers extends WallpaperEvent {
  final String category;
  
  const LoadCategoryWallpapers(this.category);
  
  @override
  List<Object> get props => [category];
}

class SearchWallpapers extends WallpaperEvent {
  final String query;
  final List<String>? categories;
  
  const SearchWallpapers(this.query, {this.categories});
  
  @override
  List<Object?> get props => [query, categories];
}

class LoadRandomWallpapers extends WallpaperEvent {
  final int count;
  
  const LoadRandomWallpapers({this.count = 20});
  
  @override
  List<Object> get props => [count];
}

class RefreshData extends WallpaperEvent {}

// lib/blocs/wallpaper/wallpaper_state.dart
import 'package:equatable/equatable.dart';
import '../../models/models.dart';

abstract class WallpaperState extends Equatable {
  const WallpaperState();

  @override
  List<Object?> get props => [];
}

class WallpaperInitial extends WallpaperState {}

class WallpaperLoading extends WallpaperState {}

class WallpaperLoaded extends WallpaperState {
  final List<Category> categories;
  final List<Wallpaper> wallpapers;
  final String? currentCategory;
  final String? searchQuery;
  
  const WallpaperLoaded({
    required this.categories,
    required this.wallpapers,
    this.currentCategory,
    this.searchQuery,
  });
  
  @override
  List<Object?> get props => [categories, wallpapers, currentCategory, searchQuery];
  
  WallpaperLoaded copyWith({
    List<Category>? categories,
    List<Wallpaper>? wallpapers,
    String? currentCategory,
    String? searchQuery,
  }) {
    return WallpaperLoaded(
      categories: categories ?? this.categories,
      wallpapers: wallpapers ?? this.wallpapers,
      currentCategory: currentCategory ?? this.currentCategory,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class WallpaperError extends WallpaperState {
  final String message;
  
  const WallpaperError(this.message);
  
  @override
  List<Object> get props => [message];
}

// lib/blocs/wallpaper/wallpaper_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/wallpaper_api_service.dart';
import '../../services/cache_service.dart';
import 'wallpaper_event.dart';
import 'wallpaper_state.dart';

class WallpaperBloc extends Bloc<WallpaperEvent, WallpaperState> {
  final WallpaperApiService _apiService;
  final CacheService _cacheService;
  
  WallpaperBloc({
    required WallpaperApiService apiService,
    required CacheService cacheService,
  })  : _apiService = apiService,
        _cacheService = cacheService,
        super(WallpaperInitial()) {
    
    on<LoadCategories>(_onLoadCategories);
    on<LoadCategoryWallpapers>(_onLoadCategoryWallpapers);
    on<SearchWallpapers>(_onSearchWallpapers);
    on<LoadRandomWallpapers>(_onLoadRandomWallpapers);
    on<RefreshData>(_onRefreshData);
  }
  
  Future<void> _onLoadCategories(
    LoadCategories event,
    Emitter<WallpaperState> emit,
  ) async {
    emit(WallpaperLoading());
    
    try {
      // Try cache first
      var indexResponse = await _cacheService.getCachedIndex();
      
      if (indexResponse == null) {
        indexResponse = await _apiService.getIndex();
        await _cacheService.cacheIndex(indexResponse);
      }
      
      emit(WallpaperLoaded(
        categories: indexResponse.categories,
        wallpapers: indexResponse.featured,
      ));
    } catch (e) {
      emit(WallpaperError(e.toString()));
    }
  }
  
  Future<void> _onLoadCategoryWallpapers(
    LoadCategoryWallpapers event,
    Emitter<WallpaperState> emit,
  ) async {
    if (state is! WallpaperLoaded) return;
    
    final currentState = state as WallpaperLoaded;
    emit(WallpaperLoading());
    
    try {
      // Try cache first
      var wallpapers = await _cacheService.getCachedCategoryWallpapers(event.category);
      
      if (wallpapers == null) {
        final response = await _apiService.getCategoryWallpapers(event.category);
        wallpapers = response.wallpapers;
        await _cacheService.cacheCategoryWallpapers(event.category, wallpapers);
      }
      
      emit(currentState.copyWith(
        wallpapers: wallpapers,
        currentCategory: event.category,
        searchQuery: null,
      ));
    } catch (e) {
      emit(WallpaperError(e.toString()));
    }
  }
  
  Future<void> _onSearchWallpapers(
    SearchWallpapers event,
    Emitter<WallpaperState> emit,
  ) async {
    if (state is! WallpaperLoaded) return;
    
    final currentState = state as WallpaperLoaded;
    emit(WallpaperLoading());
    
    try {
      final results = await _apiService.searchWallpapers(
        query: event.query,
        categories: event.categories,
      );
      
      emit(currentState.copyWith(
        wallpapers: results,
        currentCategory: null,
        searchQuery: event.query,
      ));
    } catch (e) {
      emit(WallpaperError(e.toString()));
    }
  }
  
  Future<void> _onLoadRandomWallpapers(
    LoadRandomWallpapers event,
    Emitter<WallpaperState> emit,
  ) async {
    if (state is! WallpaperLoaded) return;
    
    final currentState = state as WallpaperLoaded;
    emit(WallpaperLoading());
    
    try {
      final indexResponse = await _apiService.getIndex();
      final shuffled = List<Wallpaper>.from(indexResponse.featured)..shuffle();
      final random = shuffled.take(event.count).toList();
      
      emit(currentState.copyWith(
        wallpapers: random,
        currentCategory: null,
        searchQuery: null,
      ));
    } catch (e) {
      emit(WallpaperError(e.toString()));
    }
  }
  
  Future<void> _onRefreshData(
    RefreshData event,
    Emitter<WallpaperState> emit,
  ) async {
    await _cacheService.clearCache();
    add(LoadCategories());
  }
}
```

## 💾 Caching Service

### Hive-based Caching
```dart
// lib/services/cache_service.dart
import 'package:hive_flutter/hive_flutter.dart';
import '../models/models.dart';

class CacheService {
  static const String _indexBoxName = 'index_cache';
  static const String _categoryBoxName = 'category_cache';
  static const Duration _cacheExpiration = Duration(minutes: 10);
  
  late Box<Map> _indexBox;
  late Box<Map> _categoryBox;
  
  Future<void> init() async {
    await Hive.initFlutter();
    
    _indexBox = await Hive.openBox<Map>(_indexBoxName);
    _categoryBox = await Hive.openBox<Map>(_categoryBoxName);
  }
  
  Future<IndexResponse?> getCachedIndex() async {
    try {
      final cached = _indexBox.get('index');
      if (cached == null) return null;
      
      final timestamp = DateTime.parse(cached['cached_at'] as String);
      if (DateTime.now().difference(timestamp) > _cacheExpiration) {
        await _indexBox.delete('index');
        return null;
      }
      
      return IndexResponse.fromJson(Map<String, dynamic>.from(cached['data']));
    } catch (e) {
      return null;
    }
  }
  
  Future<void> cacheIndex(IndexResponse index) async {
    try {
      await _indexBox.put('index', {
        'data': index.toJson(),
        'cached_at': DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // Ignore cache errors
    }
  }
  
  Future<List<Wallpaper>?> getCachedCategoryWallpapers(String category) async {
    try {
      final cached = _categoryBox.get(category);
      if (cached == null) return null;
      
      final timestamp = DateTime.parse(cached['cached_at'] as String);
      if (DateTime.now().difference(timestamp) > _cacheExpiration) {
        await _categoryBox.delete(category);
        return null;
      }
      
      final wallpapersJson = List<Map<String, dynamic>>.from(cached['data']);
      return wallpapersJson.map((json) => Wallpaper.fromJson(json)).toList();
    } catch (e) {
      return null;
    }
  }
  
  Future<void> cacheCategoryWallpapers(String category, List<Wallpaper> wallpapers) async {
    try {
      await _categoryBox.put(category, {
        'data': wallpapers.map((w) => w.toJson()).toList(),
        'cached_at': DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // Ignore cache errors
    }
  }
  
  Future<void> clearCache() async {
    try {
      await _indexBox.clear();
      await _categoryBox.clear();
    } catch (e) {
      // Ignore errors
    }
  }
}
```

## 🎨 UI Components

### Main Gallery Screen
```dart
// lib/screens/wallpaper_gallery_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/wallpaper/wallpaper_bloc.dart';
import '../blocs/wallpaper/wallpaper_event.dart';
import '../blocs/wallpaper/wallpaper_state.dart';
import '../widgets/wallpaper_grid.dart';
import '../widgets/category_chips.dart';
import '../widgets/search_bar.dart';

class WallpaperGalleryScreen extends StatefulWidget {
  const WallpaperGalleryScreen({super.key});

  @override
  State<WallpaperGalleryScreen> createState() => _WallpaperGalleryScreenState();
}

class _WallpaperGalleryScreenState extends State<WallpaperGalleryScreen> {
  final TextEditingController _searchController = TextEditingController();
  
  @override
  void initState() {
    super.initState();
    context.read<WallpaperBloc>().add(LoadCategories());
  }
  
  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WallCraft'),
        actions: [
          IconButton(
            icon: const Icon(Icons.shuffle),
            onPressed: () {
              context.read<WallpaperBloc>().add(const LoadRandomWallpapers());
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<WallpaperBloc>().add(RefreshData());
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: CustomSearchBar(
              controller: _searchController,
              onSearch: (query) {
                if (query.isNotEmpty) {
                  context.read<WallpaperBloc>().add(SearchWallpapers(query));
                }
              },
              onClear: () {
                _searchController.clear();
                context.read<WallpaperBloc>().add(LoadCategories());
              },
            ),
          ),
          
          // Content
          Expanded(
            child: BlocBuilder<WallpaperBloc, WallpaperState>(
              builder: (context, state) {
                if (state is WallpaperLoading) {
                  return const Center(
                    child: CircularProgressIndicator(),
                  );
                }
                
                if (state is WallpaperError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.error_outline,
                          size: 64,
                          color: Theme.of(context).colorScheme.error,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Error: ${state.message}',
                          style: Theme.of(context).textTheme.titleMedium,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () {
                            context.read<WallpaperBloc>().add(LoadCategories());
                          },
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }
                
                if (state is WallpaperLoaded) {
                  return Column(
                    children: [
                      // Category chips
                      if (state.searchQuery == null)
                        CategoryChips(
                          categories: state.categories,
                          selectedCategory: state.currentCategory,
                          onCategorySelected: (category) {
                            context.read<WallpaperBloc>().add(
                              LoadCategoryWallpapers(category.id),
                            );
                          },
                        ),
                      
                      // Results info
                      if (state.searchQuery != null)
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16.0),
                          child: Row(
                            children: [
                              Text(
                                'Search results for "${state.searchQuery}"',
                                style: Theme.of(context).textTheme.titleSmall,
                              ),
                              const Spacer(),
                              Text(
                                '${state.wallpapers.length} found',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      
                      // Wallpaper grid
                      Expanded(
                        child: WallpaperGrid(
                          wallpapers: state.wallpapers,
                        ),
                      ),
                    ],
                  );
                }
                
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
    );
  }
}
```

### Wallpaper Grid Component
```dart
// lib/widgets/wallpaper_grid.dart
import 'package:flutter/material.dart';
import 'package:flutter_staggered_grid_view/flutter_staggered_grid_view.dart';
import '../models/wallpaper.dart';
import '../widgets/wallpaper_card.dart';

class WallpaperGrid extends StatelessWidget {
  final List<Wallpaper> wallpapers;
  final ScrollController? scrollController;
  
  const WallpaperGrid({
    super.key,
    required this.wallpapers,
    this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    if (wallpapers.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.image_not_supported_outlined,
              size: 64,
              color: Colors.grey,
            ),
            SizedBox(height: 16),
            Text(
              'No wallpapers found',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      );
    }
    
    return MasonryGridView.count(
      controller: scrollController,
      crossAxisCount: 2,
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      padding: const EdgeInsets.all(16),
      itemCount: wallpapers.length,
      itemBuilder: (context, index) {
        return WallpaperCard(
          wallpaper: wallpapers[index],
          onTap: () => _showWallpaperDetail(context, wallpapers[index]),
        );
      },
    );
  }
  
  void _showWallpaperDetail(BuildContext context, Wallpaper wallpaper) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => WallpaperDetailScreen(wallpaper: wallpaper),
      ),
    );
  }
}
```

### Wallpaper Card Component
```dart
// lib/widgets/wallpaper_card.dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:shimmer/shimmer.dart';
import '../models/wallpaper.dart';

class WallpaperCard extends StatelessWidget {
  final Wallpaper wallpaper;
  final VoidCallback? onTap;
  
  const WallpaperCard({
    super.key,
    required this.wallpaper,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image
            CachedNetworkImage(
              imageUrl: wallpaper.thumbnailUrl,
              fit: BoxFit.cover,
              placeholder: (context, url) => _buildShimmerPlaceholder(),
              errorWidget: (context, url, error) => _buildErrorWidget(),
            ),
            
            // Info
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    wallpaper.title,
                    style: Theme.of(context).textTheme.titleSmall,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${wallpaper.width}×${wallpaper.height}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 4,
                    runSpacing: 4,
                    children: wallpaper.tags.take(3).map((tag) {
                      return Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          tag,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildShimmerPlaceholder() {
    return Shimmer.fromColors(
      baseColor: Colors.grey[300]!,
      highlightColor: Colors.grey[100]!,
      child: Container(
        height: 200,
        decoration: const BoxDecoration(
          color: Colors.white,
        ),
      ),
    );
  }
  
  Widget _buildErrorWidget() {
    return Container(
      height: 200,
      color: Colors.grey[200],
      child: const Center(
        child: Icon(
          Icons.broken_image,
          size: 48,
          color: Colors.grey,
        ),
      ),
    );
  }
}
```

### Category Chips Component
```dart
// lib/widgets/category_chips.dart
import 'package:flutter/material.dart';
import '../models/category.dart';

class CategoryChips extends StatelessWidget {
  final List<Category> categories;
  final String? selectedCategory;
  final void Function(Category) onCategorySelected;
  
  const CategoryChips({
    super.key,
    required this.categories,
    required this.onCategorySelected,
    this.selectedCategory,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: categories.length,
        itemBuilder: (context, index) {
          final category = categories[index];
          final isSelected = selectedCategory == category.id;
          
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text('${category.name} (${category.count})'),
              selected: isSelected,
              onSelected: (_) => onCategorySelected(category),
              showCheckmark: false,
              selectedColor: Theme.of(context).colorScheme.primaryContainer,
              backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
              labelStyle: TextStyle(
                color: isSelected 
                  ? Theme.of(context).colorScheme.onPrimaryContainer
                  : Theme.of(context).colorScheme.onSurfaceVariant,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          );
        },
      ),
    );
  }
}
```

### Custom Search Bar
```dart
// lib/widgets/search_bar.dart
import 'package:flutter/material.dart';

class CustomSearchBar extends StatefulWidget {
  final TextEditingController controller;
  final void Function(String) onSearch;
  final VoidCallback? onClear;
  final String? hintText;
  
  const CustomSearchBar({
    super.key,
    required this.controller,
    required this.onSearch,
    this.onClear,
    this.hintText,
  });

  @override
  State<CustomSearchBar> createState() => _CustomSearchBarState();
}

class _CustomSearchBarState extends State<CustomSearchBar> {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        color: Theme.of(context).colorScheme.surfaceVariant,
      ),
      child: TextField(
        controller: widget.controller,
        decoration: InputDecoration(
          hintText: widget.hintText ?? 'Search wallpapers...',
          prefixIcon: const Icon(Icons.search),
          suffixIcon: widget.controller.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    widget.controller.clear();
                    widget.onClear?.call();
                    setState(() {});
                  },
                )
              : null,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 16,
          ),
        ),
        onSubmitted: widget.onSearch,
        onChanged: (_) => setState(() {}),
      ),
    );
  }
}
```

## 📱 Download and Set Wallpaper

### Wallpaper Service
```dart
// lib/services/wallpaper_service.dart
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:gallery_saver/gallery_saver.dart';
import 'package:dio/dio.dart';
import '../models/wallpaper.dart';

class WallpaperService {
  static const MethodChannel _channel = MethodChannel('wallpaper_setter');
  final Dio _dio = Dio();
  
  Future<bool> requestPermissions() async {
    if (Platform.isAndroid) {
      final status = await Permission.storage.request();
      return status.isGranted;
    }
    return true;
  }
  
  Future<String> downloadWallpaper(Wallpaper wallpaper) async {
    try {
      // Get downloads directory
      final directory = await getApplicationDocumentsDirectory();
      final wallpaperDir = Directory('${directory.path}/wallpapers');
      
      if (!await wallpaperDir.exists()) {
        await wallpaperDir.create(recursive: true);
      }
      
      // Download file
      final filePath = '${wallpaperDir.path}/${wallpaper.filename}';
      await _dio.download(wallpaper.downloadUrl, filePath);
      
      return filePath;
    } catch (e) {
      throw Exception('Failed to download wallpaper: $e');
    }
  }
  
  Future<void> saveToGallery(String filePath) async {
    try {
      final bool hasPermission = await requestPermissions();
      if (!hasPermission) {
        throw Exception('Storage permission denied');
      }
      
      final result = await GallerySaver.saveImage(filePath);
      if (result != true) {
        throw Exception('Failed to save to gallery');
      }
    } catch (e) {
      throw Exception('Failed to save to gallery: $e');
    }
  }
  
  Future<void> setAsWallpaper(String filePath, {
    WallpaperLocation location = WallpaperLocation.both,
  }) async {
    try {
      final result = await _channel.invokeMethod('setWallpaper', {
        'filePath': filePath,
        'location': location.index,
      });
      
      if (result != true) {
        throw Exception('Failed to set wallpaper');
      }
    } on PlatformException catch (e) {
      throw Exception('Platform error: ${e.message}');
    }
  }
  
  Future<void> downloadAndSetWallpaper(
    Wallpaper wallpaper, {
    WallpaperLocation location = WallpaperLocation.both,
    bool saveToGallery = true,
  }) async {
    try {
      // Download wallpaper
      final filePath = await downloadWallpaper(wallpaper);
      
      // Save to gallery if requested
      if (saveToGallery) {
        await this.saveToGallery(filePath);
      }
      
      // Set as wallpaper
      await setAsWallpaper(filePath, location: location);
    } catch (e) {
      rethrow;
    }
  }
}

enum WallpaperLocation {
  homeScreen,
  lockScreen,
  both,
}
```

### Android Native Code (android/app/src/main/kotlin/...)
```kotlin
// MainActivity.kt
import androidx.annotation.NonNull
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.app.WallpaperManager
import android.graphics.BitmapFactory
import java.io.File

class MainActivity: FlutterActivity() {
    private val CHANNEL = "wallpaper_setter"

    override fun configureFlutterEngine(@NonNull flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "setWallpaper" -> {
                    val filePath = call.argument<String>("filePath")
                    val location = call.argument<Int>("location") ?: 2
                    
                    if (filePath != null) {
                        try {
                            setWallpaper(filePath, location)
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("WALLPAPER_ERROR", e.message, null)
                        }
                    } else {
                        result.error("INVALID_ARGUMENT", "File path is required", null)
                    }
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }
    
    private fun setWallpaper(filePath: String, location: Int) {
        val wallpaperManager = WallpaperManager.getInstance(this)
        val bitmap = BitmapFactory.decodeFile(filePath)
        
        when (location) {
            0 -> { // Home screen only
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.N) {
                    wallpaperManager.setBitmap(bitmap, null, true, WallpaperManager.FLAG_SYSTEM)
                } else {
                    wallpaperManager.setBitmap(bitmap)
                }
            }
            1 -> { // Lock screen only
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.N) {
                    wallpaperManager.setBitmap(bitmap, null, true, WallpaperManager.FLAG_LOCK)
                } else {
                    wallpaperManager.setBitmap(bitmap)
                }
            }
            2 -> { // Both
                wallpaperManager.setBitmap(bitmap)
            }
        }
    }
}
```

## 🎯 Complete Example App

### Main App Setup
```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'services/wallpaper_api_service.dart';
import 'services/cache_service.dart';
import 'services/wallpaper_service.dart';
import 'blocs/wallpaper/wallpaper_bloc.dart';
import 'screens/wallpaper_gallery_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize cache service
  final cacheService = CacheService();
  await cacheService.init();
  
  runApp(WallCraftApp(cacheService: cacheService));
}

class WallCraftApp extends StatelessWidget {
  final CacheService cacheService;
  
  const WallCraftApp({
    super.key,
    required this.cacheService,
  });

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider(create: (_) => WallpaperApiService()),
        RepositoryProvider(create: (_) => cacheService),
        RepositoryProvider(create: (_) => WallpaperService()),
      ],
      child: BlocProvider(
        create: (context) => WallpaperBloc(
          apiService: context.read<WallpaperApiService>(),
          cacheService: context.read<CacheService>(),
        ),
        child: MaterialApp(
          title: 'WallCraft',
          theme: ThemeData(
            useMaterial3: true,
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          ),
          home: const WallpaperGalleryScreen(),
        ),
      ),
    );
  }
}
```

### Usage Example
```dart
// Example of using the wallpaper service in a widget
class WallpaperDetailScreen extends StatelessWidget {
  final Wallpaper wallpaper;
  
  const WallpaperDetailScreen({
    super.key,
    required this.wallpaper,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(wallpaper.title),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) => _handleMenuAction(context, value),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'download',
                child: Row(
                  children: [
                    Icon(Icons.download),
                    SizedBox(width: 8),
                    Text('Download'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'set_home',
                child: Row(
                  children: [
                    Icon(Icons.home),
                    SizedBox(width: 8),
                    Text('Set as Home Screen'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'set_lock',
                child: Row(
                  children: [
                    Icon(Icons.lock),
                    SizedBox(width: 8),
                    Text('Set as Lock Screen'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'set_both',
                child: Row(
                  children: [
                    Icon(Icons.wallpaper),
                    SizedBox(width: 8),
                    Text('Set as Both'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Full image
            CachedNetworkImage(
              imageUrl: wallpaper.downloadUrl,
              fit: BoxFit.cover,
              placeholder: (context, url) => const Center(
                child: CircularProgressIndicator(),
              ),
            ),
            
            // Details
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    wallpaper.title,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    wallpaper.description,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Resolution: ${wallpaper.width}×${wallpaper.height}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: wallpaper.tags.map((tag) {
                      return Chip(label: Text(tag));
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  void _handleMenuAction(BuildContext context, String action) async {
    final wallpaperService = context.read<WallpaperService>();
    
    try {
      switch (action) {
        case 'download':
          final filePath = await wallpaperService.downloadWallpaper(wallpaper);
          await wallpaperService.saveToGallery(filePath);
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Wallpaper saved to gallery')),
            );
          }
          break;
          
        case 'set_home':
          await wallpaperService.downloadAndSetWallpaper(
            wallpaper,
            location: WallpaperLocation.homeScreen,
          );
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Wallpaper set as home screen')),
            );
          }
          break;
          
        case 'set_lock':
          await wallpaperService.downloadAndSetWallpaper(
            wallpaper,
            location: WallpaperLocation.lockScreen,
          );
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Wallpaper set as lock screen')),
            );
          }
          break;
          
        case 'set_both':
          await wallpaperService.downloadAndSetWallpaper(
            wallpaper,
            location: WallpaperLocation.both,
          );
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Wallpaper set as wallpaper')),
            );
          }
          break;
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
}
```

This comprehensive Flutter integration guide provides everything needed to build a production-ready wallpaper app using the WallCraft API, including proper state management, caching, error handling, and native wallpaper setting functionality.