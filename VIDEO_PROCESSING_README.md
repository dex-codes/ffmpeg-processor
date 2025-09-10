# 🎬 Video Processing System

A clean, modular video processing system extracted from your original `ffmpeg_processor.py`. This system provides core video conversion and concatenation functions without any file preparation or pipeline sorting logic.

## 📁 Files Overview

### Core Files
- **`video_processor.py`** - Main processing functions (conversion, concatenation)
- **`video_config.py`** - Configuration presets and settings
- **`sequence_to_video.py`** - Integration with your sequence generator

### Original Files (for reference)
- **`ffmpeg_processor.py`** - Your original processor (kept for reference)

## 🎯 What Was Extracted

### ✅ **Kept (Core Video Processing)**
- `convert_video_format()` - Single video conversion
- `convert_videos_parallel()` - Parallel video processing  
- `concatenate_videos()` - Video concatenation
- `process_video_sequence()` - Complete pipeline
- Video format standardization
- FFmpeg command construction
- Error handling and logging

### ❌ **Removed (Pipeline/Sorting Logic)**
- `generate_variables()` - Random number generation
- File naming conventions (`Clip (X).mp4`)
- Random selection logic
- Pipeline sorting and preparation
- Main execution logic

## 🚀 Quick Start

### Basic Usage
```python
from video_processor import process_video_sequence

# Process a list of video files
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]

success = process_video_sequence(
    input_files=video_files,
    output_file="final_compilation.mp4",
    frame_width=1080,
    frame_height=1920,
    frame_rate=30,
    bitrate="6M"
)
```

### Using Presets
```python
from video_processor import process_video_sequence
from video_config import VIDEO_PRESETS

# Use a preset configuration
preset = VIDEO_PRESETS["youtube_shorts"]

success = process_video_sequence(
    input_files=video_files,
    output_file="youtube_compilation.mp4",
    **preset
)
```

### Integration with Sequence Generator
```python
from sequence_to_video import generate_and_process_video

# Complete pipeline: Generate sequence → Process videos
success = generate_and_process_video(
    categories=['cooking', 'sand', 'drink'],
    colors=['red', 'blue', 'orange'],
    sequence_length=50,
    output_video="my_compilation.mp4",
    preset="mobile_vertical"
)
```

## 📋 Core Functions

### `convert_video_format()`
Converts a single video to standardized format.
```python
result = convert_video_format(
    input_file="input.mp4",
    output_file="output.mp4",
    frame_width=1080,
    frame_height=1920,
    frame_rate=30,
    bitrate="6M"
)
```

### `convert_videos_parallel()`
Processes multiple videos simultaneously.
```python
converted_files = convert_videos_parallel(
    input_files=["vid1.mp4", "vid2.mp4"],
    max_workers=4
)
```

### `concatenate_videos()`
Combines multiple videos into one.
```python
success = concatenate_videos(
    input_files=converted_files,
    output_file="combined.mp4"
)
```

### `process_video_sequence()`
Complete pipeline: convert → concatenate.
```python
success = process_video_sequence(
    input_files=video_list,
    output_file="final.mp4"
)
```

## 🎛️ Configuration Presets

### Available Presets
- **`mobile_vertical`** - Standard 1080x1920 vertical
- **`youtube_shorts`** - YouTube Shorts optimized
- **`tiktok`** - TikTok format
- **`instagram_story`** - Instagram Stories
- **`youtube_standard`** - 1920x1080 horizontal
- **`instagram_post`** - 1080x1080 square

### View All Presets
```python
from video_config import list_available_presets
list_available_presets()
```

### Create Custom Preset
```python
from video_config import create_custom_preset

create_custom_preset(
    name="my_format",
    width=1440,
    height=1080,
    fps=25,
    bitrate="8M"
)
```

## ⚙️ Technical Specifications

### Default Settings
- **Video Codec**: H.264 (libx264)
- **Audio Codec**: AAC
- **Pixel Format**: yuv420p
- **Preset**: veryfast (speed vs quality)
- **CRF**: 23 (good quality)
- **Audio Bitrate**: 128k

### FFmpeg Commands Generated

**Single Conversion:**
```bash
ffmpeg -y -i input.mp4 -c:v libx264 -c:a aac 
       -vf scale=1080:1920 -r 30 -b:v 6M 
       -pix_fmt yuv420p -preset veryfast output.mp4
```

**Concatenation:**
```bash
ffmpeg -y -f concat -safe 0 -i input_list.txt 
       -c:v libx264 -preset veryfast -crf 23 
       -pix_fmt yuv420p -c:a aac -b:a 128k 
       -r 30 -b:v 6M output.mp4
```

## 📦 Requirements

### Software
- **Python 3.6+**
- **FFmpeg** (installed and in PATH)

### Python Modules (Built-in)
- `subprocess`
- `os`
- `concurrent.futures`
- `typing`

### Installation Check
```bash
# Check if FFmpeg is installed
ffmpeg -version

# Check Python version
python --version
```

## 🔧 Integration Examples

### With Your Sequence Generator
```python
# 1. Generate sequence CSV
from sequence_generator import generate_custom_sequence

generate_custom_sequence(
    categories=['cooking', 'drink'],
    colors=['red', 'blue'],
    sequence_length=20,
    output_file='sequence.csv'
)

# 2. Convert CSV to video files list
video_files = csv_to_video_files('sequence.csv', 'videos/')

# 3. Process videos
from video_processor import process_video_sequence

process_video_sequence(
    input_files=video_files,
    output_file='final.mp4',
    **VIDEO_PRESETS['mobile_vertical']
)
```

### Batch Processing
```python
# Process multiple sequences with different presets
sequences = [
    (['cooking', 'sand'], ['red', 'blue'], 'cooking_compilation.mp4'),
    (['drink', 'foam'], ['green', 'yellow'], 'drink_compilation.mp4')
]

for categories, colors, output in sequences:
    generate_and_process_video(
        categories=categories,
        colors=colors,
        sequence_length=30,
        output_video=output,
        preset='youtube_shorts'
    )
```

## 🎯 Benefits of This Extraction

### ✅ **Advantages**
- **Modular**: Use only what you need
- **Clean**: No random generation or file sorting logic
- **Flexible**: Works with any file list
- **Configurable**: Easy preset system
- **Integrable**: Works with your sequence generator
- **Maintainable**: Clear separation of concerns

### 🔄 **Migration from Original**
Your original `ffmpeg_processor.py` workflow:
```python
# OLD: Random selection + processing
variables = generate_variables(10)
combine_videos_ffmpeg(variables)
```

New modular workflow:
```python
# NEW: Your sequence + processing
video_files = get_files_from_your_sequence()
process_video_sequence(video_files, "output.mp4")
```

## 🚀 Next Steps

1. **Test the system** with a small sequence
2. **Configure presets** for your target platforms
3. **Integrate** with your sequence generator
4. **Scale up** to full-length compilations

The system is now ready to work with your CSV-based sequence generator! 🎉
