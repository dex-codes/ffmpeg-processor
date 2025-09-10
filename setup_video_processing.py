#!/usr/bin/env python3
"""
Setup script for video batch processing.

This script helps you:
1. Check your current setup
2. Verify requirements
3. Guide you through the process
4. Test with sample videos

Author: Setup Script
Date: 2025-01-06
"""

import os
import csv
import subprocess
from pathlib import Path


def check_csv_file():
    """Check if CSV file exists and analyze it."""
    csv_file = "initial-video-data.csv"
    
    print("📋 CHECKING CSV FILE")
    print("=" * 30)
    
    if not os.path.exists(csv_file):
        print(f"❌ {csv_file} not found")
        return False
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
        print(f"✅ {csv_file} found")
        print(f"   Entries: {len(rows)}")
        
        if rows:
            print(f"   Columns: {list(rows[0].keys())}")
            print(f"   Sample FileID: {rows[0].get('FileID', 'N/A')}")
            print(f"   Sample Category: {rows[0].get('Category', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    print("\n🔧 CHECKING FFMPEG")
    print("=" * 30)
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version_line}")
            return True
        else:
            print("❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found")
        print("   Install from: https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking FFmpeg: {e}")
        return False


def check_video_files():
    """Check for video files in common locations."""
    print("\n📁 CHECKING VIDEO FILES")
    print("=" * 30)
    
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']
    
    # Check current directory
    current_dir = Path(".")
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(current_dir.glob(f"*{ext}"))
        video_files.extend(current_dir.glob(f"*{ext.upper()}"))
    
    if video_files:
        print(f"✅ Found {len(video_files)} video files in current directory")
        for i, video_file in enumerate(video_files[:5]):
            print(f"   {i+1}. {video_file.name}")
        if len(video_files) > 5:
            print(f"   ... and {len(video_files) - 5} more")
        return True
    else:
        print("❌ No video files found in current directory")
        
        # Suggest common video folder locations
        common_folders = ["videos", "video_files", "source_videos", "Downloads"]
        print("\n💡 Check these common locations:")
        for folder in common_folders:
            folder_path = Path(folder)
            if folder_path.exists():
                folder_videos = []
                for ext in video_extensions:
                    folder_videos.extend(folder_path.glob(f"*{ext}"))
                if folder_videos:
                    print(f"   📁 {folder}: {len(folder_videos)} videos found")
                else:
                    print(f"   📁 {folder}: exists but no videos")
            else:
                print(f"   📁 {folder}: doesn't exist")
        
        return False


def check_required_files():
    """Check if all required processing files exist."""
    print("\n📄 CHECKING REQUIRED FILES")
    print("=" * 30)
    
    required_files = [
        "batch_video_processor.py",
        "process_my_videos.py", 
        "video_processor.py",
        "video_config.py",
        "analyze_video_inventory.py"
    ]
    
    all_present = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            all_present = False
    
    return all_present


def suggest_next_steps(csv_ok, ffmpeg_ok, videos_ok, files_ok):
    """Suggest next steps based on current status."""
    print("\n📋 NEXT STEPS")
    print("=" * 30)
    
    if not csv_ok:
        print("🔴 CRITICAL: Fix CSV file first")
        print("   - Ensure initial-video-data.csv exists")
        print("   - Check CSV format (Category, FileID columns)")
        return
    
    if not files_ok:
        print("🔴 CRITICAL: Missing required processing files")
        print("   - Re-run the setup to create missing files")
        return
    
    if not ffmpeg_ok:
        print("🟡 IMPORTANT: Install FFmpeg")
        print("   1. Download from: https://ffmpeg.org/download.html")
        print("   2. Add to system PATH")
        print("   3. Test with: ffmpeg -version")
        print("   4. Then continue with video processing")
        return
    
    if not videos_ok:
        print("🟡 IMPORTANT: Prepare your video files")
        print("   1. Download/locate your video files")
        print("   2. Name them with FileIDs from CSV")
        print("   3. Place in a folder (e.g., 'video_files')")
        print("   4. Update SOURCE_DIRECTORY in process_my_videos.py")
        print("\n   Example video naming:")
        print("   - FileID: 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_")
        print("   - Filename: 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4")
        return
    
    # All good!
    print("🟢 READY TO PROCESS!")
    print("   1. Run: python analyze_video_inventory.py")
    print("   2. Check the matching results")
    print("   3. Run: python process_my_videos.py")
    print("   4. Wait for processing to complete")
    print("   5. Check processed_videos/ folder")


def create_sample_video_structure():
    """Create sample directory structure."""
    print("\n📁 CREATING SAMPLE STRUCTURE")
    print("=" * 30)
    
    # Create directories
    directories = ["video_files", "processed_videos"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create sample README in video_files
    readme_content = """# Video Files Directory

Place your source video files here.

Naming convention:
- Use FileID from CSV as filename
- Add appropriate extension (.mp4, .mov, etc.)

Example:
- FileID: 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_
- Filename: 11IyaICOMHcR-tx8A3h8c-ori_z-kCIp_.mp4

After placing videos here, update SOURCE_DIRECTORY in process_my_videos.py to "video_files"
"""
    
    with open("video_files/README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created video_files/README.md with instructions")


def main():
    """Main setup function."""
    print("🎬 VIDEO PROCESSING SETUP")
    print("=" * 50)
    
    # Run all checks
    csv_ok = check_csv_file()
    ffmpeg_ok = check_ffmpeg()
    videos_ok = check_video_files()
    files_ok = check_required_files()
    
    # Summary
    print(f"\n📊 SETUP STATUS")
    print("=" * 30)
    print(f"CSV File: {'✅' if csv_ok else '❌'}")
    print(f"FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"Video Files: {'✅' if videos_ok else '❌'}")
    print(f"Required Files: {'✅' if files_ok else '❌'}")
    
    # Create sample structure
    if csv_ok and files_ok:
        create_sample_video_structure()
    
    # Suggest next steps
    suggest_next_steps(csv_ok, ffmpeg_ok, videos_ok, files_ok)
    
    print(f"\n📖 For detailed instructions, see:")
    print(f"   VIDEO_BATCH_PROCESSING_GUIDE.md")


if __name__ == "__main__":
    main()
