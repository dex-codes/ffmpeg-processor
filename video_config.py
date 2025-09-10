"""
Video processing configuration and presets.
Centralized place to manage all video processing settings.

Author: Configuration Module
Date: 2025-01-06
"""

# =============================================================================
# VIDEO PROCESSING PRESETS
# =============================================================================

# Standard presets for different platforms and use cases
VIDEO_PRESETS = {
    # Mobile/Vertical formats (9:16 aspect ratio)
    "mobile_vertical": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "6M",
        "description": "Standard mobile vertical video (1080x1920)"
    },
    
    "youtube_shorts": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "8M",
        "description": "YouTube Shorts optimized (1080x1920, higher bitrate)"
    },
    
    "tiktok": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "6M",
        "description": "TikTok optimized vertical video"
    },
    
    "instagram_story": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "5M",
        "description": "Instagram Stories format"
    },
    
    "instagram_reel": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "7M",
        "description": "Instagram Reels optimized"
    },
    
    # Horizontal formats (16:9 aspect ratio)
    "youtube_standard": {
        "frame_width": 1920,
        "frame_height": 1080,
        "frame_rate": 30,
        "bitrate": "8M",
        "description": "YouTube standard HD (1920x1080)"
    },
    
    "youtube_4k": {
        "frame_width": 3840,
        "frame_height": 2160,
        "frame_rate": 30,
        "bitrate": "45M",
        "description": "YouTube 4K (3840x2160) - high quality"
    },
    
    "facebook_video": {
        "frame_width": 1280,
        "frame_height": 720,
        "frame_rate": 30,
        "bitrate": "4M",
        "description": "Facebook video optimized (1280x720)"
    },
    
    "twitter_video": {
        "frame_width": 1280,
        "frame_height": 720,
        "frame_rate": 30,
        "bitrate": "5M",
        "description": "Twitter video format"
    },
    
    # Square formats (1:1 aspect ratio)
    "instagram_post": {
        "frame_width": 1080,
        "frame_height": 1080,
        "frame_rate": 30,
        "bitrate": "6M",
        "description": "Instagram square post (1080x1080)"
    },
    
    "facebook_square": {
        "frame_width": 1080,
        "frame_height": 1080,
        "frame_rate": 30,
        "bitrate": "5M",
        "description": "Facebook square video"
    },
    
    # Quality variants
    "high_quality": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 60,
        "bitrate": "12M",
        "description": "High quality vertical (60fps, high bitrate)"
    },
    
    "low_bandwidth": {
        "frame_width": 720,
        "frame_height": 1280,
        "frame_rate": 24,
        "bitrate": "2M",
        "description": "Low bandwidth friendly (720x1280, lower bitrate)"
    },
    
    "ultra_fast": {
        "frame_width": 1080,
        "frame_height": 1920,
        "frame_rate": 30,
        "bitrate": "4M",
        "description": "Fast processing preset (lower quality for speed)"
    }
}

# =============================================================================
# FFMPEG CODEC SETTINGS
# =============================================================================

CODEC_PRESETS = {
    "standard": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "veryfast",
        "crf": "23",
        "pixel_format": "yuv420p",
        "audio_bitrate": "128k"
    },
    
    "high_quality": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "slow",
        "crf": "18",
        "pixel_format": "yuv420p",
        "audio_bitrate": "192k"
    },
    
    "fast_encode": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "ultrafast",
        "crf": "28",
        "pixel_format": "yuv420p",
        "audio_bitrate": "96k"
    },
    
    "compatibility": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "medium",
        "crf": "23",
        "pixel_format": "yuv420p",
        "audio_bitrate": "128k"
    }
}

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================

PROCESSING_DEFAULTS = {
    "max_workers": 4,           # Parallel processing workers
    "temp_prefix": "temp_clip", # Temporary file prefix
    "cleanup_temp": True,       # Clean up temporary files
    "input_list_file": "input_files.txt"  # FFmpeg input list filename
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_preset_info(preset_name: str) -> dict:
    """Get detailed information about a preset."""
    if preset_name in VIDEO_PRESETS:
        preset = VIDEO_PRESETS[preset_name].copy()
        return preset
    else:
        raise ValueError(f"Unknown preset: {preset_name}")


def list_available_presets() -> None:
    """Print all available presets with descriptions."""
    print("📺 AVAILABLE VIDEO PRESETS")
    print("=" * 50)
    
    categories = {
        "Mobile/Vertical": ["mobile_vertical", "youtube_shorts", "tiktok", "instagram_story", "instagram_reel"],
        "Desktop/Horizontal": ["youtube_standard", "youtube_4k", "facebook_video", "twitter_video"],
        "Square": ["instagram_post", "facebook_square"],
        "Quality Variants": ["high_quality", "low_bandwidth", "ultra_fast"]
    }
    
    for category, presets in categories.items():
        print(f"\n{category}:")
        print("-" * len(category))
        for preset_name in presets:
            if preset_name in VIDEO_PRESETS:
                preset = VIDEO_PRESETS[preset_name]
                print(f"  {preset_name:<20} - {preset['description']}")
                print(f"  {'':<20}   {preset['frame_width']}x{preset['frame_height']}, {preset['frame_rate']}fps, {preset['bitrate']}")


def create_custom_preset(name: str, width: int, height: int, 
                        fps: float = 30, bitrate: str = "6M", 
                        description: str = "Custom preset") -> dict:
    """Create a custom video preset."""
    custom_preset = {
        "frame_width": width,
        "frame_height": height,
        "frame_rate": fps,
        "bitrate": bitrate,
        "description": description
    }
    
    VIDEO_PRESETS[name] = custom_preset
    print(f"✅ Created custom preset '{name}': {width}x{height}, {fps}fps, {bitrate}")
    return custom_preset


def get_aspect_ratio(width: int, height: int) -> str:
    """Calculate and return aspect ratio as a string."""
    from math import gcd
    
    # Calculate greatest common divisor
    common_divisor = gcd(width, height)
    ratio_w = width // common_divisor
    ratio_h = height // common_divisor
    
    # Common aspect ratios
    if ratio_w == 16 and ratio_h == 9:
        return "16:9 (Widescreen)"
    elif ratio_w == 9 and ratio_h == 16:
        return "9:16 (Vertical)"
    elif ratio_w == 1 and ratio_h == 1:
        return "1:1 (Square)"
    elif ratio_w == 4 and ratio_h == 3:
        return "4:3 (Standard)"
    else:
        return f"{ratio_w}:{ratio_h}"


if __name__ == "__main__":
    # Demo the configuration system
    print("🎬 VIDEO CONFIGURATION DEMO")
    print("=" * 40)
    
    # List all presets
    list_available_presets()
    
    # Show example preset details
    print(f"\n📋 Example preset details:")
    preset = get_preset_info("youtube_shorts")
    print(f"YouTube Shorts preset:")
    for key, value in preset.items():
        print(f"  {key}: {value}")
    
    # Create custom preset
    print(f"\n🔧 Creating custom preset...")
    create_custom_preset("my_custom", 1440, 1080, 25, "8M", "Custom 1440x1080 format")
    
    # Show aspect ratio calculation
    print(f"\n📐 Aspect ratio examples:")
    examples = [(1920, 1080), (1080, 1920), (1080, 1080), (1440, 1080)]
    for w, h in examples:
        ratio = get_aspect_ratio(w, h)
        print(f"  {w}x{h} = {ratio}")
