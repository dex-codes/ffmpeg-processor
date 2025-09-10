#!/usr/bin/env python3
"""
Batch video processor for initial-video-data.csv

This script:
1. Parses initial-video-data.csv (Category, FileID columns)
2. Processes each video through FFmpeg standardization
3. Stores standardized videos in destination folder with FileID-based filenames
4. No concatenation - just individual video processing

Author: Batch Video Processor
Date: 2025-01-06
"""

import csv
import os
import shutil
import gdown
import tempfile
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Set
from ffmpeg_processor import convert_video_format


class BatchVideoProcessor:
    """
    Processes videos in batches based on CSV data.
    """
    
    def __init__(self, source_directory: str = "downloads",
                 destination_directory: str = "processed_videos",
                 frame_width: int = 1080,
                 frame_height: int = 1920,
                 frame_rate: float = 29.97,
                 bitrate: str = "6M",
                 max_workers: int = 1,
                 min_delay: float = 5.0,
                 max_delay: float = 30.0,
                 batch_size: int = 50,
                 batch_pause_min: int = 10,
                 batch_pause_max: int = 15):
        """
        Initialize the batch processor with smart throttling for Google Drive downloads.

        Args:
            source_directory: Directory for temporary downloads (default: "downloads")
            destination_directory: Directory to store processed videos
            frame_width: Video width in pixels (default: 1080)
            frame_height: Video height in pixels (default: 1920)
            frame_rate: Video frame rate (default: 29.97)
            bitrate: Video bitrate (default: "6M")
            max_workers: Set to 1 for sequential processing (no parallel downloads)
            min_delay: Minimum delay between downloads in seconds (default: 5.0)
            max_delay: Maximum delay between downloads in seconds (default: 30.0)
            batch_size: Number of downloads before taking a batch pause (default: 50)
            batch_pause_min: Minimum batch pause in minutes (default: 10)
            batch_pause_max: Maximum batch pause in minutes (default: 15)
        """
        self.source_directory = Path(source_directory)
        self.destination_directory = Path(destination_directory)
        self.max_workers = max_workers

        # Smart throttling parameters
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.batch_size = batch_size
        self.batch_pause_min = batch_pause_min
        self.batch_pause_max = batch_pause_max
        self.downloads_in_current_batch = 0

        # Track failed downloads to avoid retrying
        self.failed_downloads: Set[str] = set()

        # Track retry attempts for exponential backoff
        self.retry_attempts: Dict[str, int] = {}
        self.failure_backoff_minutes = [5, 10, 15, 20]  # Progressive wait times

        # Create persistent gdown session for reuse across downloads
        self.gdown_session = None

        # Video processing configuration
        self.video_config = {
            'frame_width': frame_width,
            'frame_height': frame_height,
            'frame_rate': frame_rate,
            'bitrate': bitrate
        }

        # Create directories if they don't exist
        self.source_directory.mkdir(parents=True, exist_ok=True)
        self.destination_directory.mkdir(parents=True, exist_ok=True)

        print(f"📁 Download directory: {self.source_directory}")
        print(f"📁 Output directory: {self.destination_directory}")
        print(f"🎬 Video config: {frame_width}x{frame_height}, {frame_rate}fps, {bitrate}")
        print(f"⏱️  Smart throttling: {min_delay}-{max_delay}s delays, batch pause every {batch_size} downloads")

    def initialize_gdown_session(self):
        """Initialize a persistent gdown session by patching gdown's internal session."""
        try:
            import requests
            import gdown

            # Create a persistent session
            self.gdown_session = requests.Session()

            # Set up session with appropriate headers to mimic browser behavior
            self.gdown_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            # Patch gdown to use our persistent session
            # This replaces gdown's internal session creation with our persistent one
            if hasattr(gdown, 'download'):
                # Store original session creation method
                self._original_requests_session = requests.Session

                # Replace requests.Session with our persistent session
                def get_persistent_session(*args, **kwargs):
                    return self.gdown_session

                # Monkey patch requests.Session for gdown
                requests.Session = get_persistent_session

                print(f"🔗 Initialized persistent download session with session reuse")
                return True
            else:
                print(f"⚠️  gdown not properly imported")
                return False

        except Exception as e:
            print(f"⚠️  Could not initialize persistent session: {e}")
            print(f"   Will use regular gdown downloads")
            self.gdown_session = None
            return False

    def get_smart_delay(self) -> float:
        """Get a randomized delay between min_delay and max_delay seconds."""
        delay = random.uniform(self.min_delay, self.max_delay)
        return round(delay, 1)

    def should_take_batch_pause(self) -> bool:
        """Check if we should take a batch pause."""
        return self.downloads_in_current_batch >= self.batch_size

    def take_batch_pause(self):
        """Take a batch pause to mimic natural usage patterns."""
        if self.downloads_in_current_batch == 0:
            return  # No downloads yet, no need to pause

        pause_minutes = random.uniform(self.batch_pause_min, self.batch_pause_max)
        pause_seconds = pause_minutes * 60

        print(f"\n🛑 BATCH PAUSE ({self.downloads_in_current_batch} downloads completed)")
        print(f"   Taking a {pause_minutes:.1f} minute break to mimic natural usage...")
        print(f"   This helps avoid Google Drive rate limiting")

        # Show countdown for long pauses
        if pause_seconds > 60:
            remaining = int(pause_seconds)
            while remaining > 0:
                mins, secs = divmod(remaining, 60)
                print(f"   ⏳ Resuming in {mins:02d}:{secs:02d}...", end='\r')
                time.sleep(1)
                remaining -= 1
            print(f"   ✅ Break complete! Resuming downloads...")
        else:
            time.sleep(pause_seconds)
            print(f"   ✅ Break complete! Resuming downloads...")

        # Reset batch counter
        self.downloads_in_current_batch = 0

    def should_retry_failed_download(self, file_id: str) -> bool:
        """Check if we should retry a failed download based on attempt count."""
        attempts = self.retry_attempts.get(file_id, 0)
        return attempts < len(self.failure_backoff_minutes)

    def handle_download_failure(self, file_id: str) -> bool:
        """Handle download failure with exponential backoff. Returns True if should retry."""
        # Increment retry count
        self.retry_attempts[file_id] = self.retry_attempts.get(file_id, 0) + 1
        attempts = self.retry_attempts[file_id]

        if attempts <= len(self.failure_backoff_minutes):
            # Get wait time for this attempt
            wait_minutes = self.failure_backoff_minutes[attempts - 1]
            wait_seconds = wait_minutes * 60

            print(f"\n⚠️  DOWNLOAD FAILURE #{attempts} for {file_id}")
            print(f"   Taking {wait_minutes} minute backoff before retry...")
            print(f"   This helps handle temporary rate limiting or network issues")

            # Show countdown for the wait
            remaining = int(wait_seconds)
            while remaining > 0:
                mins, secs = divmod(remaining, 60)
                print(f"   ⏳ Retrying in {mins:02d}:{secs:02d}...", end='\r')
                time.sleep(1)
                remaining -= 1

            print(f"   🔄 Backoff complete! Attempting retry #{attempts + 1}...")
            return True
        else:
            # Max retries reached
            print(f"\n❌ PERMANENT FAILURE for {file_id}")
            print(f"   Tried {attempts} times with progressive backoff")
            print(f"   Adding to permanent failure list - will not retry again")
            self.failed_downloads.add(file_id)
            return False
    
    def load_video_data(self, csv_file: str) -> List[Dict[str, str]]:
        """
        Load video data from CSV file.
        
        Args:
            csv_file: Path to CSV file with Category and FileID columns
            
        Returns:
            List of dictionaries with video data
        """
        video_data = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    video_data.append({
                        'category': row['Category'].strip(),
                        'file_id': row['FileID'].strip()
                    })
        
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file {csv_file} not found")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")
        
        print(f"📋 Loaded {len(video_data)} video entries from {csv_file}")
        return video_data

    def check_existing_files(self, csv_file: str) -> Dict[str, any]:
        """
        Check which files already exist (processed videos and downloads).

        Args:
            csv_file: Path to CSV file

        Returns:
            Dictionary with existing file statistics
        """
        video_data = self.load_video_data(csv_file)

        existing_processed = []
        existing_downloads = []
        need_processing = []

        for data in video_data:
            file_id = data['file_id']

            # Check if processed video exists
            output_path = self.destination_directory / f"{file_id}.mp4"
            if output_path.exists():
                existing_processed.append(file_id)
                continue

            # Check if download exists
            download_patterns = [
                self.source_directory / f"{file_id}.mp4",
                self.source_directory / f"{file_id}.mov",
                self.source_directory / f"{file_id}_temp.mp4"
            ]

            found_download = False
            for pattern in download_patterns:
                if pattern.exists():
                    existing_downloads.append(file_id)
                    found_download = True
                    break

            if not found_download:
                need_processing.append(file_id)

        return {
            'total': len(video_data),
            'existing_processed': len(existing_processed),
            'existing_downloads': len(existing_downloads),
            'need_download': len(need_processing),
            'processed_files': existing_processed,
            'download_files': existing_downloads,
            'need_processing_files': need_processing
        }

    def download_video_from_drive(self, file_id: str) -> Optional[str]:
        """
        Download video from Google Drive using persistent session with delay and failure tracking.

        Args:
            file_id: Google Drive FileID

        Returns:
            Path to downloaded video file if successful, None otherwise
        """
        # Check if this FileID has already failed permanently
        if file_id in self.failed_downloads:
            print(f"⏭️  Skipping {file_id} (permanently failed after retries)")
            return None

        try:
            # Check if we need a batch pause
            if self.should_take_batch_pause():
                self.take_batch_pause()

            # Add randomized delay before download to mimic natural usage
            delay = self.get_smart_delay()
            print(f"⏱️  Smart delay: {delay}s (randomized {self.min_delay}-{self.max_delay}s)...")
            time.sleep(delay)

            # Create temporary file for download
            temp_file = self.source_directory / f"{file_id}_temp.mp4"

            # Construct Google Drive URL
            drive_url = f"https://drive.google.com/uc?id={file_id}"

            # Download using gdown with persistent session (via monkey patching)
            if self.gdown_session:
                print(f"📥 Downloading {file_id} (using persistent session)...")
            else:
                print(f"📥 Downloading {file_id}...")

            # gdown will automatically use our persistent session due to monkey patching
            output_path = gdown.download(drive_url, str(temp_file), quiet=False, use_cookies=True)

            if output_path and os.path.exists(output_path):
                print(f"✅ Download successful: {file_id}")
                # Increment batch counter for successful downloads
                self.downloads_in_current_batch += 1
                return output_path
            else:
                print(f"❌ Download failed: {file_id} (no output file - likely rate limiting)")
                # Treat as potential rate limiting - use exponential backoff
                if self.should_retry_failed_download(file_id):
                    should_retry = self.handle_download_failure(file_id)
                    if should_retry:
                        # Recursive retry
                        return self.download_video_from_drive(file_id)
                else:
                    self.failed_downloads.add(file_id)
                return None

        except Exception as e:
            print(f"❌ Download failed for {file_id}: {e}")

            # Treat ALL failures as potential rate limiting - use exponential backoff
            error_str = str(e).lower()
            if "permission" in error_str or "public link" in error_str or "cannot retrieve" in error_str:
                print(f"🔒 Potential rate limiting (disguised as permission issue)")

            # Use exponential backoff for ALL failures
            if self.should_retry_failed_download(file_id):
                should_retry = self.handle_download_failure(file_id)
                if should_retry:
                    # Recursive retry
                    return self.download_video_from_drive(file_id)
            else:
                self.failed_downloads.add(file_id)

            return None

    def find_or_download_video(self, file_id: str) -> Optional[str]:
        """
        Find existing video file or download from Google Drive.

        Args:
            file_id: FileID to search for or download

        Returns:
            Path to video file if found/downloaded, None otherwise
        """
        # First, check if file already exists locally (including temp files)
        local_patterns = [
            self.source_directory / f"{file_id}.mp4",
            self.source_directory / f"{file_id}.mov",
            self.source_directory / f"{file_id}_temp.mp4"
        ]

        for pattern in local_patterns:
            if pattern.exists():
                print(f"✅ Found local download: {pattern.name}")
                return str(pattern)

        # If not found locally, try to download from Google Drive
        print(f"📥 Need to download: {file_id}")
        return self.download_video_from_drive(file_id)
    
    def process_single_video(self, video_data: Dict[str, str]) -> Tuple[bool, str, str]:
        """
        Process a single video sequentially: download → process → cleanup.
        Complete entire workflow before returning.

        Args:
            video_data: Dictionary with 'category' and 'file_id'

        Returns:
            Tuple of (success, input_file, output_file)
        """
        file_id = video_data['file_id']
        category = video_data['category']

        print(f"🎬 Starting complete workflow for: {file_id}")

        # Create output filename based on FileID
        output_filename = f"{file_id}.mp4"
        output_path = self.destination_directory / output_filename

        # Check if processed video already exists
        if output_path.exists():
            print(f"✅ Already processed: {file_id} (skipping)")
            return True, "already_exists", str(output_path)

        # Step 1: Find or download source video
        print(f"📥 Step 1: Finding or downloading video...")
        source_path = self.find_or_download_video(file_id)
        if not source_path:
            print(f"❌ Step 1 failed: Could not download {file_id}")
            return False, f"FileID: {file_id}", f"Download/find failed"
        print(f"✅ Step 1 complete: Video available")

        # Step 2: Process video through FFmpeg
        print(f"🔄 Step 2: Processing through FFmpeg...")
        try:
            result = convert_video_format(
                input_file=source_path,
                output_file=str(output_path),
                **self.video_config
            )

            # Step 3: Clean up temporary download file if it was downloaded
            if "_temp.mp4" in source_path:
                print(f"🧹 Step 3: Cleaning up temporary file...")
                try:
                    os.remove(source_path)
                    print(f"✅ Step 3 complete: Cleaned up {Path(source_path).name}")
                except:
                    print(f"⚠️  Step 3 warning: Could not clean up {Path(source_path).name}")
            else:
                print(f"ℹ️  Step 3: No cleanup needed (using existing file)")

            if result:
                print(f"✅ Step 2 complete: FFmpeg processing successful")
                print(f"🎉 Complete workflow finished for: {file_id}")
                return True, source_path, str(output_path)
            else:
                print(f"❌ Step 2 failed: FFmpeg conversion failed")
                return False, source_path, "FFmpeg conversion failed"

        except Exception as e:
            # Clean up temp file on error too
            if source_path and "_temp.mp4" in source_path and os.path.exists(source_path):
                try:
                    os.remove(source_path)
                except:
                    pass
            return False, source_path, f"Processing error: {str(e)}"
    
    def process_all_videos(self, csv_file: str) -> Dict[str, any]:
        """
        Process all videos from CSV file.

        Args:
            csv_file: Path to CSV file

        Returns:
            Dictionary with processing results and statistics
        """
        print("🎬 BATCH VIDEO PROCESSING")
        print("=" * 50)
        print(f"Source directory: {self.source_directory}")
        print(f"Destination directory: {self.destination_directory}")
        print(f"Video config: {self.video_config}")
        print(f"Max workers: {self.max_workers}")

        # Check existing files first
        print(f"\n🔍 CHECKING EXISTING FILES...")
        existing_check = self.check_existing_files(csv_file)

        print(f"📊 FILE STATUS:")
        print(f"   Total videos: {existing_check['total']}")
        print(f"   ✅ Already processed: {existing_check['existing_processed']}")
        print(f"   📁 Already downloaded: {existing_check['existing_downloads']}")
        print(f"   📥 Need download: {existing_check['need_download']}")

        if existing_check['existing_processed'] > 0:
            print(f"\n⚡ OPTIMIZATION: {existing_check['existing_processed']} videos already processed (will skip)")

        if existing_check['existing_downloads'] > 0:
            print(f"⚡ OPTIMIZATION: {existing_check['existing_downloads']} videos already downloaded (will reuse)")

        # Load video data
        video_data = self.load_video_data(csv_file)

        # Initialize persistent gdown session for better performance
        print(f"\n🔗 Setting up persistent download session...")
        self.initialize_gdown_session()

        # Process videos sequentially (no parallel processing)
        successful = []
        failed = []

        print(f"\n🚀 Starting sequential processing with smart throttling...")
        print(f"   Processing {len(video_data)} videos one at a time")
        print(f"   Each video: Download → Process → Cleanup → Next video")
        print(f"   Using persistent session + randomized delays + batch pauses")
        print(f"   Throttling: {self.min_delay}-{self.max_delay}s delays, pause every {self.batch_size} downloads")

        for i, data in enumerate(video_data, 1):
            file_id = data['file_id']
            category = data['category']

            print(f"\n📹 Processing video {i}/{len(video_data)}: {file_id}")
            print(f"   Category: {category}")

            try:
                # Process single video completely before moving to next
                success, input_path, output_path = self.process_single_video(data)

                if success:
                    successful.append({
                        'file_id': file_id,
                        'category': category,
                        'input_path': input_path,
                        'output_path': output_path
                    })
                    print(f"✅ {file_id} completed successfully")
                else:
                    failed.append({
                        'file_id': file_id,
                        'category': category,
                        'error': output_path
                    })
                    print(f"❌ {file_id} failed: {output_path}")

            except Exception as e:
                failed.append({
                    'file_id': file_id,
                    'category': category,
                    'error': str(e)
                })
                print(f"❌ {file_id} exception: {e}")

            # Show progress after each video
            completed = len(successful) + len(failed)
            print(f"📊 Progress: {completed}/{len(video_data)} ({completed/len(video_data)*100:.1f}%)")
            print(f"   ✅ Successful: {len(successful)} | ❌ Failed: {len(failed)}")
        
        # Results summary
        results = {
            'total': len(video_data),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(video_data) * 100 if video_data else 0,
            'successful_items': successful,
            'failed_items': failed
        }
        
        # Clean up session
        self.cleanup_session()

        return results

    def cleanup_session(self):
        """Clean up the persistent gdown session and restore original behavior."""
        if self.gdown_session:
            try:
                # Restore original requests.Session if we patched it
                if hasattr(self, '_original_requests_session'):
                    import requests
                    requests.Session = self._original_requests_session
                    print(f"🔗 Restored original session behavior")

                # Close our persistent session
                self.gdown_session.close()
                print(f"🔗 Closed persistent download session")
            except Exception as e:
                print(f"⚠️  Error during session cleanup: {e}")

            self.gdown_session = None
    
    def print_results_summary(self, results: Dict[str, any]):
        """Print processing results summary."""
        print(f"\n📊 PROCESSING RESULTS")
        print("=" * 50)
        print(f"Total videos: {results['total']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {results['success_rate']:.1f}%")

        # Show failed downloads summary
        if self.failed_downloads:
            print(f"\n🔒 PERMANENT FAILURES ({len(self.failed_downloads)} videos):")
            print(f"   These FileIDs failed after exponential backoff retries:")
            failed_list = sorted(self.failed_downloads)
            for i, file_id in enumerate(failed_list):
                if i < 10:  # Show first 10
                    attempts = self.retry_attempts.get(file_id, 1)
                    print(f"   {file_id} (tried {attempts} times)")
                elif i == 10:
                    print(f"   ... and {len(self.failed_downloads) - 10} more")
                    break
            print(f"   💡 These videos were permanently skipped after multiple retry attempts")

        if results['failed_items']:
            print(f"\n❌ PROCESSING FAILURES:")
            for item in results['failed_items'][:10]:  # Show first 10 failures
                print(f"  {item['file_id']} - {item['error']}")
            if len(results['failed_items']) > 10:
                print(f"  ... and {len(results['failed_items']) - 10} more")

        if results['successful_items']:
            print(f"\n✅ SAMPLE SUCCESSFUL VIDEOS:")
            for item in results['successful_items'][:5]:  # Show first 5 successes
                print(f"  {item['file_id']} -> {Path(item['output_path']).name}")


def main():
    """Main execution function."""

    # 🔧 CONFIGURATION - Modify these parameters
    # ==========================================

    CSV_FILE = "initial-video-data.csv"
    DOWNLOAD_DIRECTORY = "downloads"  # Temporary download directory
    DESTINATION_DIRECTORY = "processed_videos"  # Where to store processed videos

    # Video processing configuration (matching your ffmpeg_processor defaults)
    FRAME_WIDTH = 1080
    FRAME_HEIGHT = 1920
    FRAME_RATE = 29.97
    BITRATE = "6M"
    MAX_WORKERS = 1  # Sequential processing only (no parallel downloads)

    # Smart throttling configuration (mimics natural usage patterns)
    MIN_DELAY = 5.0   # Minimum delay between downloads (seconds)
    MAX_DELAY = 30.0  # Maximum delay between downloads (seconds)
    BATCH_SIZE = 50   # Downloads before taking a batch pause
    BATCH_PAUSE_MIN = 10  # Minimum batch pause (minutes)
    BATCH_PAUSE_MAX = 15  # Maximum batch pause (minutes)

    # ==========================================
    
    print("🎯 Configuration:")
    print(f"   CSV File: {CSV_FILE}")
    print(f"   Download Directory: {DOWNLOAD_DIRECTORY}")
    print(f"   Destination Directory: {DESTINATION_DIRECTORY}")
    print(f"   Video Config: {FRAME_WIDTH}x{FRAME_HEIGHT}, {FRAME_RATE}fps, {BITRATE}")
    print(f"   Max Workers: {MAX_WORKERS}")
    print(f"   Smart Throttling: {MIN_DELAY}-{MAX_DELAY}s delays, pause every {BATCH_SIZE} downloads")

    try:
        # Create processor with smart throttling
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
        
        # Process all videos
        results = processor.process_all_videos(CSV_FILE)
        
        # Print results
        processor.print_results_summary(results)
        
        if results['successful'] > 0:
            print(f"\n🎉 SUCCESS!")
            print(f"   {results['successful']} videos processed successfully")
            print(f"   Check '{DESTINATION_DIRECTORY}' folder for processed videos")
        else:
            print(f"\n❌ NO VIDEOS PROCESSED")
            print(f"   Check source directory and file paths")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
