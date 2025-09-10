#!/usr/bin/env python3
"""
Simple script to process videos from initial-video-data.csv

Just modify the configuration section below and run!

Author: Simple Video Processor
Date: 2025-01-06
"""

from batch_video_processor import BatchVideoProcessor
from video_config import list_available_presets


def main():
    """Process videos with your configuration."""
    
    # 🎯 YOUR CONFIGURATION
    # =====================
    
    # CSV file with Category and FileID columns
    CSV_FILE = "initial-video-data.csv"
    
    # Directory where your source videos are located
    SOURCE_DIRECTORY = "."  # Current directory
    
    # Directory where processed videos will be saved
    DESTINATION_DIRECTORY = "processed_videos"
    
    # Video processing preset (see available presets below)
    VIDEO_PRESET = "mobile_vertical"  # Good default for mobile videos
    
    # Number of videos to process simultaneously (adjust based on your CPU)
    MAX_WORKERS = 4
    
    # =====================
    
    print("🎬 VIDEO PROCESSING SETUP")
    print("=" * 40)
    
    # Show available presets
    print("📺 Available video presets:")
    list_available_presets()
    
    print(f"\n🎯 Your Configuration:")
    print(f"   CSV File: {CSV_FILE}")
    print(f"   Source Directory: {SOURCE_DIRECTORY}")
    print(f"   Destination Directory: {DESTINATION_DIRECTORY}")
    print(f"   Video Preset: {VIDEO_PRESET}")
    print(f"   Max Workers: {MAX_WORKERS}")
    
    # Confirm before processing
    print(f"\n⚠️  This will process ALL videos in {CSV_FILE}")
    print(f"   Source videos will be searched in: {SOURCE_DIRECTORY}")
    print(f"   Processed videos will be saved to: {DESTINATION_DIRECTORY}")
    
    response = input("\nProceed? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    try:
        # Create processor
        processor = BatchVideoProcessor(
            source_directory=SOURCE_DIRECTORY,
            destination_directory=DESTINATION_DIRECTORY,
            preset=VIDEO_PRESET,
            max_workers=MAX_WORKERS
        )
        
        # Process all videos
        results = processor.process_all_videos(CSV_FILE)
        
        # Print results
        processor.print_results_summary(results)
        
        # Final status
        if results['successful'] > 0:
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"   ✅ {results['successful']} videos processed successfully")
            print(f"   ❌ {results['failed']} videos failed")
            print(f"   📁 Check '{DESTINATION_DIRECTORY}' folder for processed videos")
            
            # Show next steps
            print(f"\n📋 NEXT STEPS:")
            print(f"   1. Check processed videos in '{DESTINATION_DIRECTORY}'")
            print(f"   2. Use these processed videos for concatenation")
            print(f"   3. FileID-based filenames make it easy to reference")
        else:
            print(f"\n❌ NO VIDEOS PROCESSED SUCCESSFULLY")
            print(f"   Check that source videos exist in '{SOURCE_DIRECTORY}'")
            print(f"   Verify FileID values match actual filenames")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   - Check that {CSV_FILE} exists")
        print(f"   - Verify source directory contains video files")
        print(f"   - Ensure FFmpeg is installed")


if __name__ == "__main__":
    main()
