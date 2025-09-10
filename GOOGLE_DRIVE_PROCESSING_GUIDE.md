# 🎬 Google Drive Video Processing Guide

## Overview

This system downloads videos directly from Google Drive using FileIDs and processes them through FFmpeg standardization. Perfect for your `initial-video-data.csv` with Google Drive FileIDs!

## 🚀 Quick Start

### 1. Install Requirements

```bash
pip install gdown
```

Or install from requirements file:
```bash
pip install -r requirements.txt
```

### 2. Verify Setup

```bash
python download_and_process.py test
```

This will test downloading and processing a single video.

### 3. Process All Videos

```bash
python download_and_process.py
```

This will download and process all 429 videos from your CSV.

## 📋 Your Current Data

- **CSV File**: `initial-video-data.csv` (429 videos)
- **FileID Format**: Google Drive IDs (e.g., `11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_`)
- **Categories**: 
  - 4 - pouring Slime
  - 7 - Hand playing with object  
  - 14 - Pressing
  - 6 - Cutting
  - 2 - pouring Liquid

## 🔧 How It Works

1. **Read CSV** → Load FileIDs and categories
2. **Download** → Use `gdown` to download from Google Drive
3. **Process** → Standardize through FFmpeg
4. **Save** → Store with FileID-based names
5. **Cleanup** → Remove temporary downloads

## 📁 File Structure

```
your-project/
├── initial-video-data.csv          # Your CSV ✅
├── download_and_process.py         # Main script ✅
├── downloads/                      # Temp downloads (auto-created)
│   ├── 11IyaICOMHcR...temp.mp4    # Temporary files
│   └── ...
└── processed_videos/               # Final output (auto-created)
    ├── 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4
    ├── 1uLBuF1uTPruteJUqaN0zkUwG46kobXgJ.mp4
    └── ... (429 processed videos)
```

## ⚙️ Configuration

Edit `download_and_process.py` to customize:

```python
# CSV file with Category and FileID columns
CSV_FILE = "initial-video-data.csv"

# Directory for temporary downloads
DOWNLOAD_DIRECTORY = "downloads"

# Directory where processed videos will be saved
DESTINATION_DIRECTORY = "processed_videos"

# Video processing preset
VIDEO_PRESET = "mobile_vertical"  # or "youtube_shorts", "tiktok", etc.

# Number of simultaneous downloads/processing
MAX_WORKERS = 2  # Keep low to avoid Google Drive limits
```

## 🎛️ Video Presets

- **`mobile_vertical`** - 1080x1920, 30fps, 6M (good default)
- **`youtube_shorts`** - 1080x1920, 30fps, 8M (higher quality)
- **`tiktok`** - 1080x1920, 30fps, 6M (TikTok optimized)
- **`youtube_standard`** - 1920x1080, 30fps, 8M (horizontal)
- **`high_quality`** - 1080x1920, 60fps, 12M (premium)

## 📊 Expected Performance

- **Download Speed**: Depends on Google Drive limits and video sizes
- **Processing Speed**: ~30-60 seconds per video (depends on length/quality)
- **Total Time**: 3-8 hours for 429 videos (estimate)
- **Disk Space**: ~2x original video size during processing

## 🔍 Troubleshooting

### Problem: "gdown not installed"
```bash
pip install gdown
```

### Problem: "Download failed"
**Causes**:
- Google Drive download limits reached
- FileID not public/accessible
- Network issues

**Solutions**:
- Wait and retry later
- Check FileID accessibility
- Reduce MAX_WORKERS to 1

### Problem: "FFmpeg not found"
**Solution**: Install FFmpeg from https://ffmpeg.org/download.html

### Problem: "Disk space"
**Solution**: Ensure 2x video collection size available

### Problem: "Processing slow"
**Solutions**:
- Reduce MAX_WORKERS
- Use faster preset like "ultra_fast"
- Process in smaller batches

## 🎯 Google Drive Limits

Google Drive has download quotas:
- **Daily limit**: ~750GB per day
- **Rate limit**: Varies by file size
- **Concurrent**: Limited simultaneous downloads

**Tips**:
- Keep MAX_WORKERS low (1-3)
- Process during off-peak hours
- Split large batches if needed

## 📋 Batch Processing Tips

### Small Test First
```bash
python download_and_process.py test
```

### Process in Chunks
Edit CSV to process subsets:
1. Copy first 50 rows to `test-batch.csv`
2. Update CSV_FILE in script
3. Process small batch first

### Monitor Progress
- Watch console output for progress
- Check `processed_videos/` folder
- Monitor disk space usage

## 🔄 Integration Workflow

After processing:

1. **Verify Videos** → Check samples in `processed_videos/`
2. **Update Sequence Generator** → Point to processed videos
3. **Generate Sequences** → Use your existing system
4. **Concatenate** → Create final compilations

## 📊 Expected Output

```
🎉 PROCESSING COMPLETE!
   ✅ 425 videos processed successfully
   ❌ 4 videos failed
   📁 Processed videos are in 'processed_videos'
   💾 Processed videos size: 12.5 GB

📋 NEXT STEPS:
   1. Check processed videos in 'processed_videos'
   2. Videos are standardized and ready for concatenation
   3. Use sequence generator to create video compilations
   4. FileID-based names make referencing easy
```

## 🚨 Important Notes

1. **Backup**: Keep original CSV safe
2. **Space**: Monitor disk usage during processing
3. **Interruption**: Can resume by rerunning (skips existing files)
4. **Cleanup**: Temporary files auto-deleted after processing
5. **Limits**: Respect Google Drive quotas

## 🎬 Ready to Start?

1. **Install gdown**: `pip install gdown`
2. **Test single video**: `python download_and_process.py test`
3. **Process all videos**: `python download_and_process.py`
4. **Wait for completion** (3-8 hours estimated)
5. **Check results** in `processed_videos/` folder

---

**Your 429 Google Drive videos will be downloaded, standardized, and ready for sequence generation! 🚀**
