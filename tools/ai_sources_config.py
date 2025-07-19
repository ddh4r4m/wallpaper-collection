#!/usr/bin/env python3
"""
Configuration for AI wallpaper sources
Add your API keys and advanced settings here
"""

import os

# API Keys (set as environment variables or update here)
API_KEYS = {
    'civitai': os.getenv('CIVITAI_API_KEY', ''),  # Optional, increases rate limits
    'huggingface': os.getenv('HUGGINGFACE_TOKEN', ''),  # For Hugging Face Spaces
    'reddit_client_id': os.getenv('REDDIT_CLIENT_ID', ''),  # For Reddit API
    'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
}

# Advanced AI source configurations
ADVANCED_AI_SOURCES = {
    'civitai': {
        'api_url': 'https://civitai.com/api/v1/images',
        'api_key_header': 'Authorization',
        'rate_limit': 1 if API_KEYS['civitai'] else 3,  # Faster with API key
        'max_per_request': 200 if API_KEYS['civitai'] else 100,
        'quality_filters': {
            'min_reactions': 5,
            'min_width': 1024,
            'min_height': 1024,
            'nsfw': False,
            'blocked_tags': ['nsfw', 'nude', 'explicit']
        }
    },
    
    'lexica': {
        'api_url': 'https://lexica.art/api/v1/search',
        'rate_limit': 1,
        'max_per_request': 50,
        'models': ['lexica-aperture-v2', 'stable-diffusion'],
        'quality_filters': {
            'min_width': 768,
            'min_height': 768
        }
    },
    
    'huggingface': {
        'spaces_url': 'https://huggingface.co/spaces',
        'api_url': 'https://huggingface.co/api/spaces',
        'rate_limit': 2,
        'featured_spaces': [
            'stabilityai/stable-diffusion',
            'runwayml/stable-diffusion-v1-5',
            'CompVis/stable-diffusion'
        ]
    },
    
    'reddit': {
        'oauth_url': 'https://www.reddit.com/api/v1/access_token',
        'api_url': 'https://oauth.reddit.com',
        'rate_limit': 2,
        'quality_filters': {
            'min_score': 100,
            'min_comments': 5,
            'image_domains': ['i.redd.it', 'imgur.com', 'i.imgur.com']
        }
    },
    
    'arthub': {
        'base_url': 'https://arthub.ai',
        'api_url': 'https://arthub.ai/api',
        'rate_limit': 3,
        'categories': {
            'abstract': 'abstract-art',
            'cyberpunk': 'cyberpunk',
            'nature': 'landscape',
            'space': 'space-art',
            'anime': 'anime-manga',
            'minimal': 'minimalism'
        }
    },
    
    'playground': {
        'base_url': 'https://playgroundai.com',
        'feed_url': 'https://playgroundai.com/feed',
        'rate_limit': 2,
        'quality_filters': {
            'min_likes': 10,
            'verified_users_only': False
        }
    }
}

# Category-specific AI prompts and configurations
ENHANCED_AI_CATEGORIES = {
    'abstract': {
        'primary_sources': ['civitai', 'lexica'],
        'fallback_sources': ['arthub', 'playground'],
        'civitai_tags': ['abstract art', 'geometric patterns', 'digital art', 'minimalist'],
        'lexica_prompts': [
            'abstract geometric wallpaper 4k',
            'minimalist abstract art wallpaper',
            'digital abstract patterns',
            'geometric abstract background'
        ],
        'quality_keywords': ['wallpaper', '4k', 'high resolution', 'clean'],
        'avoid_keywords': ['low quality', 'blurry', 'pixelated']
    },
    
    'cyberpunk': {
        'primary_sources': ['lexica', 'civitai'],
        'fallback_sources': ['reddit', 'arthub'],
        'civitai_tags': ['cyberpunk', 'neon city', 'futuristic', 'sci-fi landscape'],
        'lexica_prompts': [
            'cyberpunk city wallpaper 4k neon',
            'futuristic cyberpunk landscape',
            'neon cyberpunk cityscape wallpaper',
            'blade runner style wallpaper'
        ],
        'reddit_subreddits': ['Cyberpunk', 'outrun', 'vaporwave', 'StableDiffusion'],
        'quality_keywords': ['neon', 'high contrast', 'detailed', '4k'],
        'style_modifiers': ['cinematic', 'detailed', 'professional photography']
    },
    
    'nature': {
        'primary_sources': ['lexica', 'civitai'],
        'fallback_sources': ['huggingface', 'reddit'],
        'civitai_tags': ['landscape photography', 'nature', 'forest', 'mountain landscape'],
        'lexica_prompts': [
            'beautiful landscape wallpaper 4k',
            'fantasy forest wallpaper',
            'mountain landscape photography',
            'serene nature wallpaper'
        ],
        'reddit_subreddits': ['EarthPorn', 'LandscapePorn', 'NaturePorn', 'StableDiffusion'],
        'quality_keywords': ['landscape', 'photography', 'natural', 'scenic'],
        'style_modifiers': ['cinematic lighting', 'ultra detailed', 'masterpiece']
    },
    
    'space': {
        'primary_sources': ['lexica', 'civitai'],
        'fallback_sources': ['reddit', 'huggingface'],
        'civitai_tags': ['space art', 'cosmic landscape', 'nebula', 'galaxy'],
        'lexica_prompts': [
            'space wallpaper 4k cosmic',
            'nebula galaxy wallpaper',
            'cosmic landscape art',
            'universe space scene wallpaper'
        ],
        'reddit_subreddits': ['spaceporn', 'astrophotography', 'space', 'StableDiffusion'],
        'quality_keywords': ['cosmic', 'stellar', 'astronomical', 'deep space'],
        'style_modifiers': ['ultra detailed', 'cinematic', 'epic']
    },
    
    'anime': {
        'primary_sources': ['civitai', 'lexica'],
        'fallback_sources': ['arthub', 'reddit'],
        'civitai_tags': ['anime landscape', 'anime style', 'manga art', 'anime wallpaper'],
        'lexica_prompts': [
            'anime landscape wallpaper',
            'anime style background',
            'manga art wallpaper',
            'anime scenery 4k'
        ],
        'reddit_subreddits': ['anime', 'AnimeART', 'Animewallpaper', 'StableDiffusion'],
        'quality_keywords': ['anime style', 'detailed', 'high quality', 'wallpaper'],
        'style_modifiers': ['anime style', 'detailed illustration', 'studio quality']
    },
    
    'minimal': {
        'primary_sources': ['lexica', 'civitai'],
        'fallback_sources': ['arthub', 'playground'],
        'civitai_tags': ['minimalist design', 'clean', 'simple', 'geometric minimal'],
        'lexica_prompts': [
            'minimalist wallpaper 4k clean',
            'simple geometric wallpaper',
            'clean minimal design',
            'minimalist background'
        ],
        'reddit_subreddits': ['minimalism', 'MinimalWallpaper', 'StableDiffusion'],
        'quality_keywords': ['clean', 'simple', 'minimal', 'geometric'],
        'style_modifiers': ['clean design', 'minimalist', 'simple']
    },
    
    'ai': {
        'primary_sources': ['civitai', 'lexica'],
        'fallback_sources': ['reddit', 'arthub'],
        'civitai_tags': ['digital art', 'ai generated', 'concept art', 'illustration'],
        'lexica_prompts': [
            'ai generated wallpaper 4k',
            'digital art wallpaper',
            'ai artwork wallpaper',
            'generative art wallpaper',
            'stable diffusion wallpaper'
        ],
        'reddit_subreddits': ['StableDiffusion', 'midjourney', 'artificial', 'deepdream', 'MediaSynthesis'],
        'quality_keywords': ['ai-generated', 'digital art', 'high quality', '4k'],
        'style_modifiers': ['professional', 'high detail', 'artistic']
    }
}

# Quality scoring weights for different sources
QUALITY_SCORING = {
    'civitai': {
        'reaction_weight': 0.3,
        'download_weight': 0.2,
        'comment_weight': 0.1,
        'resolution_weight': 0.4
    },
    'lexica': {
        'model_weight': 0.3,  # Better models = higher quality
        'resolution_weight': 0.4,
        'prompt_quality_weight': 0.3
    },
    'reddit': {
        'score_weight': 0.4,
        'comment_weight': 0.2,
        'subreddit_weight': 0.2,
        'resolution_weight': 0.2
    }
}

# Source reliability and preference
SOURCE_RELIABILITY = {
    'civitai': {'reliability': 0.9, 'avg_quality': 0.85},
    'lexica': {'reliability': 0.9, 'avg_quality': 0.8},
    'arthub': {'reliability': 0.7, 'avg_quality': 0.7},
    'reddit': {'reliability': 0.6, 'avg_quality': 0.6},
    'huggingface': {'reliability': 0.8, 'avg_quality': 0.75},
    'playground': {'reliability': 0.7, 'avg_quality': 0.7}
}

# Rate limiting and retry configurations
RATE_LIMITING = {
    'base_delay': 1,  # Base delay between requests
    'exponential_backoff': True,
    'max_retries': 3,
    'retry_delay': 5,
    'concurrent_downloads': 3  # Number of simultaneous downloads
}

# Image processing preferences
IMAGE_PROCESSING = {
    'target_width': 1080,
    'target_height': 1920,
    'quality': 85,
    'thumbnail_size': (400, 600),
    'thumbnail_quality': 80,
    'min_file_size': 100000,  # 100KB minimum
    'max_file_size': 5000000,  # 5MB maximum
    'allowed_formats': ['JPEG', 'JPG', 'PNG'],
    'convert_to_jpeg': True
}

def get_source_config(source_name):
    """Get configuration for a specific source"""
    return ADVANCED_AI_SOURCES.get(source_name, {})

def get_category_config(category):
    """Get AI configuration for a specific category"""
    return ENHANCED_AI_CATEGORIES.get(category, {})

def get_api_headers(source_name):
    """Get API headers for authenticated requests"""
    headers = {
        'User-Agent': 'AI Wallpaper Scraper 2.0 (Educational/Research)'
    }
    
    if source_name == 'civitai' and API_KEYS['civitai']:
        headers['Authorization'] = f"Bearer {API_KEYS['civitai']}"
    elif source_name == 'huggingface' and API_KEYS['huggingface']:
        headers['Authorization'] = f"Bearer {API_KEYS['huggingface']}"
    
    return headers

def calculate_quality_score(source, item_data):
    """Calculate quality score for an item from a specific source"""
    scoring = QUALITY_SCORING.get(source, {})
    score = 0.0
    
    if source == 'civitai':
        stats = item_data.get('stats', {})
        score += stats.get('reactionCount', 0) * scoring.get('reaction_weight', 0)
        score += stats.get('downloadCount', 0) * scoring.get('download_weight', 0) * 0.1
        score += stats.get('commentCount', 0) * scoring.get('comment_weight', 0)
        
        # Resolution scoring
        width = item_data.get('width', 0)
        height = item_data.get('height', 0)
        resolution_score = min((width * height) / (1920 * 1080), 2.0)  # Max 2x score
        score += resolution_score * scoring.get('resolution_weight', 0) * 100
    
    elif source == 'reddit':
        score += item_data.get('score', 0) * scoring.get('score_weight', 0)
        score += item_data.get('num_comments', 0) * scoring.get('comment_weight', 0)
    
    return min(score, 100)  # Cap at 100

# Export commonly used configurations
__all__ = [
    'API_KEYS', 'ADVANCED_AI_SOURCES', 'ENHANCED_AI_CATEGORIES',
    'QUALITY_SCORING', 'SOURCE_RELIABILITY', 'RATE_LIMITING',
    'IMAGE_PROCESSING', 'get_source_config', 'get_category_config',
    'get_api_headers', 'calculate_quality_score'
]