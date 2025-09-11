#!/usr/bin/env python3
"""
Download videos from Google Drive and process them through FFmpeg.

This script:
1. Reads FileIDs from initial-video-data.csv
2. Downloads videos from Google Drive using gdown
3. Processes each video through FFmpeg standardization
4. Saves processed videos with FileID-based names
5. Cleans up temporary downloads

Author: Download and Process
Date: 2025-01-06
"""

from batch_video_processor import BatchVideoProcessor
import os


def check_gdown_installation():
    """Check if gdown is installed."""
    try:
        import gdown
        print("✅ gdown is available")
        return True
    except ImportError:
        print("❌ gdown not installed")
        print("   Install with: pip install gdown")
        return False


def main():
    """Download and process videos from Google Drive."""
    
    # 🎯 YOUR CONFIGURATION
    # =====================
    
    # CSV file with Category and FileID columns
    CSV_FILE = "11092025-video-list.csv"
    
    # Directory for temporary downloads (will be created)
    DOWNLOAD_DIRECTORY = "downloads"
    
    # Directory where processed videos will be saved (will be created)
    DESTINATION_DIRECTORY = "processed_videos"

    # Video processing configuration (matching your ffmpeg_processor)
    FRAME_WIDTH = 1080      # Video width
    FRAME_HEIGHT = 1920     # Video height (vertical format)
    FRAME_RATE = 29.97      # Frame rate
    BITRATE = "6M"          # Video bitrate

    # Sequential processing only (no parallel downloads)
    # Each video: Download → Process → Cleanup → Next video
    MAX_WORKERS = 1

    # Smart throttling configuration (mimics natural usage patterns)
    MIN_DELAY = 5.0   # Minimum delay between downloads (seconds)
    MAX_DELAY = 30.0  # Maximum delay between downloads (seconds)
    BATCH_SIZE = 50   # Downloads before taking a batch pause
    BATCH_PAUSE_MIN = 10  # Minimum batch pause (minutes)
    BATCH_PAUSE_MAX = 15  # Maximum batch pause (minutes)
    
    # =====================
    
    print("🎬 GOOGLE DRIVE VIDEO PROCESSING")
    print("=" * 50)
    
    # Check requirements
    if not check_gdown_installation():
        print("\n❌ Cannot proceed without gdown")
        print("   Run: pip install gdown")
        return
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ {CSV_FILE} not found")
        return
    
    print(f"\n🎯 Your Configuration:")
    print(f"   CSV File: {CSV_FILE}")
    print(f"   Download Directory: {DOWNLOAD_DIRECTORY}")
    print(f"   Destination Directory: {DESTINATION_DIRECTORY}")
    print(f"   Video Config: {FRAME_WIDTH}x{FRAME_HEIGHT}, {FRAME_RATE}fps, {BITRATE}")
    print(f"   Max Workers: {MAX_WORKERS}")
    print(f"   Smart Throttling: {MIN_DELAY}-{MAX_DELAY}s delays, pause every {BATCH_SIZE} downloads")

    # Create processor to check existing files
    try:
        processor = BatchVideoProcessor(
            source_directory=DOWNLOAD_DIRECTORY,
            destination_directory=DESTINATION_DIRECTORY,
            frame_width=FRAME_WIDTH,
            frame_height=FRAME_HEIGHT,
            frame_rate=FRAME_RATE,
            bitrate=BITRATE,
            max_workers=MAX_WORKERS,
            min_delay=MIN_DELAY,
            max_delay=MAX_DELAY,
            batch_size=BATCH_SIZE,
            batch_pause_min=BATCH_PAUSE_MIN,
            batch_pause_max=BATCH_PAUSE_MAX
        )

        # Check existing files
        print(f"\n🔍 CHECKING EXISTING FILES...")
        existing_check = processor.check_existing_files(CSV_FILE)

        print(f"\n📊 CURRENT STATUS:")
        print(f"   Total videos in CSV: {existing_check['total']}")
        print(f"   ✅ Already processed: {existing_check['existing_processed']}")
        print(f"   📁 Already downloaded: {existing_check['existing_downloads']}")
        print(f"   📥 Need to download: {existing_check['need_download']}")

        videos_to_process = existing_check['existing_downloads'] + existing_check['need_download']
        videos_to_download = existing_check['need_download']

        print(f"\n⚡ WORK NEEDED:")
        print(f"   Videos to download: {videos_to_download}")
        print(f"   Videos to process: {videos_to_process}")
        print(f"   Videos to skip: {existing_check['existing_processed']}")

    except Exception as e:
        print(f"   Error checking files: {e}")
        return
    
    # Warning about Google Drive limits
    print(f"\n⚠️  IMPORTANT NOTES:")
    if videos_to_download > 0:
        print(f"   - Will download {videos_to_download} NEW videos from Google Drive")
        print(f"   - Will reuse {existing_check['existing_downloads']} already downloaded videos")
    else:
        print(f"   - No new downloads needed! All videos already available")

    if videos_to_process > 0:
        print(f"   - Will process {videos_to_process} videos through FFmpeg")
        print(f"   - Will skip {existing_check['existing_processed']} already processed videos")
    else:
        print(f"   - All videos already processed! Nothing to do")
        return

    print(f"   - Google Drive has download limits - process may be slow")
    print(f"   - Temporary files will be stored in '{DOWNLOAD_DIRECTORY}'")
    print(f"   - Final videos will be in '{DESTINATION_DIRECTORY}'")
    print(f"   - Each video will be downloaded, processed, then temp file deleted")

    # Confirm before processing
    if videos_to_download > 0:
        response = input(f"\nProceed with downloading {videos_to_download} and processing {videos_to_process} videos? (y/N): ").strip().lower()
    else:
        response = input(f"\nProceed with processing {videos_to_process} already downloaded videos? (y/N): ").strip().lower()

    if response != 'y':
        print("❌ Cancelled by user")
        return

    try:
        # Use the processor we already created for checking
        
        print(f"\n🚀 Starting download and processing...")
        print(f"   This may take a while depending on video sizes and Google Drive limits")
        
        # Process all videos (download + convert)
        results = processor.process_all_videos(CSV_FILE)
        
        # Print results
        processor.print_results_summary(results)
        
        # Final status
        if results['successful'] > 0:
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"   ✅ {results['successful']} videos processed successfully")
            print(f"   ❌ {results['failed']} videos failed")
            print(f"   📁 Processed videos are in '{DESTINATION_DIRECTORY}'")
            
            # Show disk usage
            try:
                import shutil
                total, used, free = shutil.disk_usage(DESTINATION_DIRECTORY)
                processed_size = sum(
                    os.path.getsize(os.path.join(DESTINATION_DIRECTORY, f))
                    for f in os.listdir(DESTINATION_DIRECTORY)
                    if os.path.isfile(os.path.join(DESTINATION_DIRECTORY, f))
                )
                print(f"   💾 Processed videos size: {processed_size / (1024**3):.2f} GB")
            except:
                pass
            
            # Show next steps
            print(f"\n📋 NEXT STEPS:")
            print(f"   1. Check processed videos in '{DESTINATION_DIRECTORY}'")
            print(f"   2. Videos are standardized and ready for concatenation")
            print(f"   3. Use sequence generator to create video compilations")
            print(f"   4. FileID-based names make referencing easy")
            
        else:
            print(f"\n❌ NO VIDEOS PROCESSED SUCCESSFULLY")
            print(f"   Common issues:")
            print(f"   - Google Drive download limits reached")
            print(f"   - FileIDs are not public/accessible")
            print(f"   - Network connectivity issues")
            print(f"   - FFmpeg not installed")
            
        # Cleanup info
        download_files = []
        if os.path.exists(DOWNLOAD_DIRECTORY):
            download_files = [f for f in os.listdir(DOWNLOAD_DIRECTORY) if f.endswith('_temp.mp4')]
        
        if download_files:
            print(f"\n🧹 CLEANUP:")
            print(f"   {len(download_files)} temporary files remain in '{DOWNLOAD_DIRECTORY}'")
            cleanup = input("   Delete temporary download files? (y/N): ").strip().lower()
            if cleanup == 'y':
                for file in download_files:
                    try:
                        os.remove(os.path.join(DOWNLOAD_DIRECTORY, file))
                        print(f"   ✅ Deleted {file}")
                    except:
                        print(f"   ❌ Failed to delete {file}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  INTERRUPTED BY USER")
        print(f"   Partial processing may have occurred")
        print(f"   Check '{DESTINATION_DIRECTORY}' for any completed videos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   - Check internet connection")
        print(f"   - Verify Google Drive FileIDs are accessible")
        print(f"   - Ensure sufficient disk space")
        print(f"   - Check that FFmpeg is installed")


def test_single_download():
    """Test downloading a single video - finds first unprocessed video."""
    print("🧪 TESTING SINGLE VIDEO DOWNLOAD")
    print("=" * 40)

    try:
        # Create processor with faster settings for testing
        processor = BatchVideoProcessor(
            source_directory="test_downloads",
            destination_directory="test_processed",
            frame_width=1080,
            frame_height=1920,
            frame_rate=29.97,
            bitrate="6M",
            max_workers=1,
            min_delay=5.0,    # Minimum delay for testing
            max_delay=30.0,   # Maximum delay for testing
            batch_size=5,     # Smaller batches for testing
            batch_pause_min=1,  # Shorter pauses for testing
            batch_pause_max=2   # Shorter pauses for testing
        )

        # Initialize persistent session for testing
        print("🔗 Setting up persistent download session for testing...")
        processor.initialize_gdown_session()

        # Try multiple videos until we find one that works
        import csv
        videos_checked = 0
        max_attempts = 10  # Try up to 10 videos

        print("🔍 Looking for unprocessed video to test...")

        with open("initial-video-data.csv", 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                file_id = row['FileID'].strip()
                category = row['Category'].strip()
                videos_checked += 1

                # Check if this video is already processed
                output_path = processor.destination_directory / f"{file_id}.mp4"
                if output_path.exists():
                    print(f"⏭️  Skipping {file_id} (already processed)")
                    continue

                print(f"\n🎯 Attempting test {videos_checked}:")
                print(f"   FileID: {file_id}")
                print(f"   Category: {category}")

                # Test this video
                test_data = {'file_id': file_id, 'category': category}
                success, input_file, output_file = processor.process_single_video(test_data)

                if success:
                    print(f"\n✅ TEST SUCCESSFUL!")
                    print(f"   Input: {input_file}")
                    print(f"   Output: {output_file}")

                    # Verify the output file exists
                    from pathlib import Path
                    if Path(output_file).exists():
                        file_size = Path(output_file).stat().st_size / (1024*1024)  # MB
                        print(f"   File size: {file_size:.2f} MB")
                        print(f"   ✅ Video successfully downloaded and processed!")
                    else:
                        print(f"   ⚠️  Output file not found at expected location")
                    return  # Success - exit the test
                else:
                    print(f"❌ Test failed: {output_file}")
                    if "Download/find failed" in output_file:
                        print(f"   Likely Google Drive permissions issue - trying next video...")

                    # Stop if we've tried enough videos
                    if videos_checked >= max_attempts:
                        print(f"\n⚠️  Tried {max_attempts} videos without success")
                        print(f"   This may indicate Google Drive permission issues")
                        print(f"   Consider checking FileID accessibility or trying manual download")
                        return

        # If we get here, we've checked all videos
        if videos_checked == 0:
            print("🎉 All videos are already processed! Nothing to test.")
            print("   Delete some files from test_processed/ to test download functionality")
        else:
            print(f"\n⚠️  Checked {videos_checked} videos but none could be downloaded")
            print(f"   This suggests Google Drive permission issues with the FileIDs")

    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_single_download()
    else:
        main()
