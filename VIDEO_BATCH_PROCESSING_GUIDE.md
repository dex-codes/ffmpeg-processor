# 🎬 Video Batch Processing Guide

## Overview

This system processes videos from your `initial-video-data.csv` file through FFmpeg standardization. Each video gets processed individually (no concatenation yet) and stored with FileID-based filenames.

## 📋 Your Current Setup

- **CSV File**: `initial-video-data.csv` (431 video entries)
- **Columns**: Category, FileID
- **Categories**: 4 - pouring Slime, 7 - Hand playing with object, 14 - Pressing, 6 - Cutting, 2 - pouring Liquid

## 🔧 Files Created

1. **`batch_video_processor.py`** - Main processing engine
2. **`process_my_videos.py`** - Simple configuration script
3. **`analyze_video_inventory.py`** - Analyze video files vs CSV
4. **`VIDEO_BATCH_PROCESSING_GUIDE.md`** - This guide

## 📁 File Structure Expected

```
your-project-folder/
├── initial-video-data.csv          # Your CSV file ✅
├── batch_video_processor.py        # Processing engine ✅
├── process_my_videos.py            # Simple config script ✅
├── video_files/                    # Your source videos (NEEDED)
│   ├── 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4
│   ├── 1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ.mp4
│   └── ... (more video files)
└── processed_videos/               # Output folder (auto-created)
    ├── 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4
    ├── 1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ.mp4
    └── ... (processed videos)
```

## 🚀 Step-by-Step Usage

### Step 1: Prepare Your Video Files

You need to have your actual video files available. The FileIDs in your CSV look like Google Drive IDs:
- `11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_`
- `1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ`
- etc.

**Options:**
1. **Download videos** with FileID as filename (e.g., `11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4`)
2. **Rename existing videos** to match FileIDs
3. **Place videos in a folder** and update the source directory path

### Step 2: Analyze Your Inventory

```bash
python analyze_video_inventory.py
```

This will:
- Show how many videos you have
- Check which FileIDs match actual video files
- Identify missing videos
- Suggest improvements

### Step 3: Configure Processing

Edit `process_my_videos.py` and modify these settings:

```python
# Directory where your source videos are located
SOURCE_DIRECTORY = "video_files"  # Change this to your video folder

# Directory where processed videos will be saved
DESTINATION_DIRECTORY = "processed_videos"

# Video processing preset
VIDEO_PRESET = "mobile_vertical"  # Good for mobile/vertical videos
```

### Step 4: Run Processing

```bash
python process_my_videos.py
```

This will:
- Process all videos from your CSV
- Standardize them using FFmpeg
- Save them with FileID-based names
- Show progress and results

## 🎛️ Video Presets Available

- **`mobile_vertical`** - 1080x1920, 30fps, 6M bitrate (good default)
- **`youtube_shorts`** - 1080x1920, 30fps, 8M bitrate (higher quality)
- **`tiktok`** - 1080x1920, 30fps, 6M bitrate (TikTok optimized)
- **`youtube_standard`** - 1920x1080, 30fps, 8M bitrate (horizontal)
- **`high_quality`** - 1080x1920, 60fps, 12M bitrate (premium)
- **`low_bandwidth`** - 720x1280, 24fps, 2M bitrate (smaller files)

## 🔍 Troubleshooting

### Problem: "No video files found"
**Solution**: 
- Check that your video files exist
- Verify the `SOURCE_DIRECTORY` path
- Ensure video files have recognizable extensions (.mp4, .mov, etc.)

### Problem: "FileID not found"
**Solution**:
- Video filename should contain the FileID
- Example: `11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4`
- Or rename videos to match FileIDs exactly

### Problem: "FFmpeg not found"
**Solution**:
- Install FFmpeg: https://ffmpeg.org/download.html
- Add FFmpeg to your system PATH
- Test with: `ffmpeg -version`

### Problem: Processing fails
**Solution**:
- Check video file corruption
- Verify sufficient disk space
- Reduce `MAX_WORKERS` if system overloaded

## 📊 Expected Output

After successful processing:

```
📊 PROCESSING RESULTS
==================================================
Total videos: 431
Successful: 425
Failed: 6
Success rate: 98.6%

✅ Sample successful videos:
  11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_ -> 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4
  1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ -> 1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ.mp4
  ...
```

## 🔄 Integration with Sequence Generator

After batch processing, you can use the processed videos with your sequence generator:

1. **Processed videos** are in `processed_videos/` folder
2. **FileID-based names** make them easy to reference
3. **Standardized format** ensures consistent concatenation
4. **Ready for sequence generation** and final video creation

## 📋 Next Steps After Processing

1. **Verify processed videos** - Check a few samples
2. **Update sequence generator** - Point it to processed videos folder
3. **Generate sequences** - Use your existing sequence generation system
4. **Concatenate videos** - Use processed videos for final compilation

## 🎯 Performance Tips

- **Parallel Processing**: Adjust `MAX_WORKERS` based on your CPU (4-8 typical)
- **Disk Space**: Ensure 2x source video size available for processing
- **Memory**: Close other applications during batch processing
- **SSD**: Use SSD for faster processing if available

## 🔧 Advanced Configuration

For custom processing, modify `batch_video_processor.py`:

```python
# Custom video settings
custom_config = {
    'frame_width': 1080,
    'frame_height': 1920,
    'frame_rate': 30,
    'bitrate': '8M'
}
```

## 📞 Support

If you encounter issues:
1. Run `analyze_video_inventory.py` first
2. Check the error messages carefully
3. Verify FFmpeg installation
4. Ensure video files are accessible
5. Check disk space and permissions

---

**Ready to process your 431 videos? Start with Step 1! 🚀**
