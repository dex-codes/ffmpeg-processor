#!/usr/bin/env python3
"""
Check the status of video files without processing.

This script shows:
1. How many videos are already processed
2. How many videos are already downloaded
3. How many videos need to be downloaded
4. Detailed file lists

Author: Video Status Checker
Date: 2025-01-06
"""

from batch_video_processor import BatchVideoProcessor
import os


def main():
    """Check video processing status."""
    
    # Configuration (should match your processing settings)
    CSV_FILE = "initial-video-data.csv"
    DOWNLOAD_DIRECTORY = "downloads"
    DESTINATION_DIRECTORY = "processed_videos"
    
    print("🔍 VIDEO PROCESSING STATUS CHECK")
    print("=" * 50)
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ {CSV_FILE} not found")
        return
    
    try:
        # Create processor for checking
        processor = BatchVideoProcessor(
            source_directory=DOWNLOAD_DIRECTORY,
            destination_directory=DESTINATION_DIRECTORY,
            frame_width=1080,
            frame_height=1920,
            frame_rate=29.97,
            bitrate="6M",
            max_workers=1,
            download_delay=0.0  # No delay for status checking
        )
        
        # Check existing files
        print(f"\n📊 ANALYZING FILES...")
        existing_check = processor.check_existing_files(CSV_FILE)
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   Total videos in CSV: {existing_check['total']}")
        print(f"   ✅ Already processed: {existing_check['existing_processed']}")
        print(f"   📁 Already downloaded: {existing_check['existing_downloads']}")
        print(f"   📥 Need to download: {existing_check['need_download']}")
        
        # Progress calculation
        if existing_check['total'] > 0:
            processed_percent = (existing_check['existing_processed'] / existing_check['total']) * 100
            downloaded_percent = (existing_check['existing_downloads'] / existing_check['total']) * 100
            
            print(f"\n📈 PROGRESS:")
            print(f"   Processing: {processed_percent:.1f}% complete")
            print(f"   Downloads: {downloaded_percent:.1f}% available")
        
        # Work remaining
        videos_to_process = existing_check['existing_downloads'] + existing_check['need_download']
        videos_to_download = existing_check['need_download']
        
        print(f"\n⚡ WORK REMAINING:")
        print(f"   Videos to download: {videos_to_download}")
        print(f"   Videos to process: {videos_to_process}")
        
        # Time estimates
        if videos_to_download > 0:
            download_time_min = videos_to_download * 0.5  # 30 seconds per video (optimistic)
            download_time_max = videos_to_download * 3    # 3 minutes per video (with limits)
            print(f"   Estimated download time: {download_time_min:.0f}-{download_time_max:.0f} minutes")
        
        if videos_to_process > 0:
            process_time_min = videos_to_process * 1      # 1 minute per video (optimistic)
            process_time_max = videos_to_process * 3      # 3 minutes per video (conservative)
            print(f"   Estimated processing time: {process_time_min:.0f}-{process_time_max:.0f} minutes")
        
        # Show sample files
        if existing_check['existing_processed']:
            print(f"\n✅ SAMPLE PROCESSED FILES:")
            for file_id in existing_check['processed_files'][:5]:
                print(f"   {file_id}.mp4")
            if len(existing_check['processed_files']) > 5:
                print(f"   ... and {len(existing_check['processed_files']) - 5} more")
        
        if existing_check['existing_downloads']:
            print(f"\n📁 SAMPLE DOWNLOADED FILES:")
            for file_id in existing_check['download_files'][:5]:
                print(f"   {file_id}")
            if len(existing_check['download_files']) > 5:
                print(f"   ... and {len(existing_check['download_files']) - 5} more")
        
        if existing_check['need_download']:
            print(f"\n📥 SAMPLE FILES NEEDING DOWNLOAD:")
            for file_id in existing_check['need_processing_files'][:5]:
                print(f"   {file_id}")
            if len(existing_check['need_processing_files']) > 5:
                print(f"   ... and {len(existing_check['need_processing_files']) - 5} more")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if existing_check['existing_processed'] == existing_check['total']:
            print("   🎉 All videos are processed! You're ready for sequence generation.")
        elif videos_to_process == 0:
            print("   ⚠️  No videos need processing. Check your file paths.")
        elif videos_to_download > 100:
            print("   📋 Large batch detected. Consider processing in smaller chunks.")
            print("   🕐 Process during off-peak hours to avoid Google Drive limits.")
        elif videos_to_download > 0:
            print("   🚀 Ready to download and process. Run: python download_and_process.py")
        else:
            print("   ⚡ All videos downloaded. Ready for processing only.")
        
        # Disk space check
        try:
            import shutil
            total, used, free = shutil.disk_usage(DESTINATION_DIRECTORY if os.path.exists(DESTINATION_DIRECTORY) else ".")
            free_gb = free / (1024**3)
            
            # Estimate space needed (assume ~50MB per processed video)
            space_needed_gb = videos_to_process * 0.05
            
            print(f"\n💾 DISK SPACE:")
            print(f"   Available: {free_gb:.1f} GB")
            print(f"   Estimated needed: {space_needed_gb:.1f} GB")
            
            if free_gb < space_needed_gb * 2:  # Need 2x for temp files
                print("   ⚠️  Low disk space! Consider freeing up space first.")
            else:
                print("   ✅ Sufficient disk space available")
                
        except:
            print(f"\n💾 DISK SPACE: Unable to check")
        
        # Next steps
        print(f"\n📋 NEXT STEPS:")
        if existing_check['existing_processed'] == existing_check['total']:
            print("   1. All done! Use processed videos for sequence generation")
        elif videos_to_process > 0:
            print("   1. Run: python download_and_process.py")
            print("   2. Wait for processing to complete")
            print("   3. Check results in processed_videos/ folder")
        else:
            print("   1. Check file paths and CSV data")
            print("   2. Verify Google Drive FileIDs are accessible")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
