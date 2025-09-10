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
                 max_workers: int = 2,
                 download_delay: float = 2.0):
        """
        Initialize the batch processor with Google Drive download capability.

        Args:
            source_directory: Directory for temporary downloads (default: "downloads")
            destination_directory: Directory to store processed videos
            frame_width: Video width in pixels (default: 1080)
            frame_height: Video height in pixels (default: 1920)
            frame_rate: Video frame rate (default: 29.97)
            bitrate: Video bitrate (default: "6M")
            max_workers: Maximum parallel processing workers (reduced default for downloads)
            download_delay: Delay in seconds between download requests (default: 2.0)
        """
        self.source_directory = Path(source_directory)
        self.destination_directory = Path(destination_directory)
        self.max_workers = max_workers
        self.download_delay = download_delay

        # Track failed downloads to avoid retrying
        self.failed_downloads: Set[str] = set()

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
        print(f"⏱️  Download delay: {download_delay}s between requests")
    
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
        Download video from Google Drive using gdown with delay and failure tracking.

        Args:
            file_id: Google Drive FileID

        Returns:
            Path to downloaded video file if successful, None otherwise
        """
        # Check if this FileID has already failed
        if file_id in self.failed_downloads:
            print(f"⏭️  Skipping {file_id} (previously failed)")
            return None

        try:
            # Add delay before download to respect rate limits
            if self.download_delay > 0:
                print(f"⏱️  Waiting {self.download_delay}s before download...")
                time.sleep(self.download_delay)

            # Create temporary file for download
            temp_file = self.source_directory / f"{file_id}_temp.mp4"

            # Construct Google Drive URL
            drive_url = f"https://drive.google.com/uc?id={file_id}"

            # Download using gdown
            print(f"📥 Downloading {file_id}...")
            output_path = gdown.download(drive_url, str(temp_file), quiet=False)

            if output_path and os.path.exists(output_path):
                print(f"✅ Download successful: {file_id}")
                return output_path
            else:
                print(f"❌ Download failed: {file_id} (no output file)")
                self.failed_downloads.add(file_id)
                return None

        except Exception as e:
            print(f"❌ Download failed for {file_id}: {e}")
            # Add to failed downloads to avoid retrying
            self.failed_downloads.add(file_id)

            # Check for specific permission errors
            error_str = str(e).lower()
            if "permission" in error_str or "public link" in error_str or "cannot retrieve" in error_str:
                print(f"🔒 Permission issue detected - will not retry {file_id}")

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
        Process a single video file (download from Google Drive if needed, then process).

        Args:
            video_data: Dictionary with 'category' and 'file_id'

        Returns:
            Tuple of (success, input_file, output_file)
        """
        file_id = video_data['file_id']
        category = video_data['category']

        # Create output filename based on FileID
        output_filename = f"{file_id}.mp4"
        output_path = self.destination_directory / output_filename

        # Check if processed video already exists
        if output_path.exists():
            print(f"✅ Already processed: {file_id} (skipping)")
            return True, "already_exists", str(output_path)

        # Find or download source video
        source_path = self.find_or_download_video(file_id)
        if not source_path:
            return False, f"FileID: {file_id}", f"Download/find failed"

        # Process video through FFmpeg
        try:
            print(f"🔄 Processing {file_id} ({category})...")
            result = convert_video_format(
                input_file=source_path,
                output_file=str(output_path),
                **self.video_config
            )

            # Clean up temporary download file if it was downloaded
            if "_temp.mp4" in source_path:
                try:
                    os.remove(source_path)
                    print(f"🧹 Cleaned up temp file: {Path(source_path).name}")
                except:
                    pass  # Don't fail if cleanup fails

            if result:
                return True, source_path, str(output_path)
            else:
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
        
        # Process videos in parallel
        successful = []
        failed = []
        
        print(f"\n🔄 Processing {len(video_data)} videos...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_data = {
                executor.submit(self.process_single_video, data): data 
                for data in video_data
            }
            
            # Process results as they complete
            for future in as_completed(future_to_data):
                video_data_item = future_to_data[future]
                file_id = video_data_item['file_id']
                category = video_data_item['category']
                
                try:
                    success, input_path, output_path = future.result()
                    
                    if success:
                        successful.append({
                            'file_id': file_id,
                            'category': category,
                            'input_path': input_path,
                            'output_path': output_path
                        })
                        print(f"✅ {file_id} ({category})")
                    else:
                        failed.append({
                            'file_id': file_id,
                            'category': category,
                            'error': output_path
                        })
                        print(f"❌ {file_id} ({category}) - {output_path}")
                        
                except Exception as e:
                    failed.append({
                        'file_id': file_id,
                        'category': category,
                        'error': str(e)
                    })
                    print(f"❌ {file_id} ({category}) - Exception: {e}")
        
        # Results summary
        results = {
            'total': len(video_data),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(video_data) * 100 if video_data else 0,
            'successful_items': successful,
            'failed_items': failed
        }
        
        return results
    
    def print_results_summary(self, results: Dict[str, any]):
        """Print processing results summary."""
        print(f"\n📊 PROCESSING RESULTS")
        print("=" * 50)
        print(f"Total videos: {results['total']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {results['success_rate']:.1f}%")
        
        if results['failed_items']:
            print(f"\n❌ Failed videos:")
            for item in results['failed_items'][:10]:  # Show first 10 failures
                print(f"  {item['file_id']} - {item['error']}")
            if len(results['failed_items']) > 10:
                print(f"  ... and {len(results['failed_items']) - 10} more")
        
        if results['successful_items']:
            print(f"\n✅ Sample successful videos:")
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
    MAX_WORKERS = 2  # Parallel workers (reduced for downloads + processing)
    DOWNLOAD_DELAY = 3.0  # Seconds between download requests (helps with rate limits)

    # ==========================================
    
    print("🎯 Configuration:")
    print(f"   CSV File: {CSV_FILE}")
    print(f"   Download Directory: {DOWNLOAD_DIRECTORY}")
    print(f"   Destination Directory: {DESTINATION_DIRECTORY}")
    print(f"   Video Config: {FRAME_WIDTH}x{FRAME_HEIGHT}, {FRAME_RATE}fps, {BITRATE}")
    print(f"   Max Workers: {MAX_WORKERS}")
    print(f"   Download Delay: {DOWNLOAD_DELAY}s")

    try:
        # Create processor
        processor = BatchVideoProcessor(
            source_directory=DOWNLOAD_DIRECTORY,
            destination_directory=DESTINATION_DIRECTORY,
            frame_width=FRAME_WIDTH,
            frame_height=FRAME_HEIGHT,
            frame_rate=FRAME_RATE,
            bitrate=BITRATE,
            max_workers=MAX_WORKERS,
            download_delay=DOWNLOAD_DELAY
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
