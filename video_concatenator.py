#!/usr/bin/env python3
"""
Interactive Video Concatenation Script

This script will:
1. Ask you for the location of your processed videos
2. Ask you for the sequence list CSV file
3. Find videos based on the sequence list
4. Concatenate them in the specified order using FFmpeg

Author: Your Assistant
Date: 2025-01-06
"""

import csv
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def get_video_location() -> str:
    """Ask user for video directory and validate it exists."""
    while True:
        print("\n📁 VIDEO LOCATION SELECTION")
        print("-" * 30)
        video_dir = input("Enter path to your processed videos directory: ").strip()
        
        if not video_dir:
            print("❌ Please enter a directory path.")
            continue
            
        if not os.path.exists(video_dir):
            print(f"❌ Directory '{video_dir}' not found.")
            continue
            
        if not os.path.isdir(video_dir):
            print(f"❌ '{video_dir}' is not a directory.")
            continue
            
        # Check if directory has video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        video_files = []
        for file in os.listdir(video_dir):
            if Path(file).suffix.lower() in video_extensions:
                video_files.append(file)
        
        if not video_files:
            print(f"⚠️  No video files found in '{video_dir}'")
            response = input("Continue anyway? (y/n): ").lower().strip()
            if response != 'y':
                continue
        else:
            print(f"✅ Found {len(video_files)} video files in directory")
        
        return video_dir

def get_sequence_list() -> str:
    """Ask user for sequence list CSV file and validate it exists."""
    while True:
        print("\n📋 SEQUENCE LIST SELECTION")
        print("-" * 30)
        csv_file = input("Enter path to your sequence list CSV file: ").strip()
        
        if not csv_file:
            print("❌ Please enter a file path.")
            continue
            
        if not os.path.exists(csv_file):
            print(f"❌ File '{csv_file}' not found.")
            continue
            
        if not csv_file.lower().endswith('.csv'):
            print("❌ File must be a CSV file (.csv extension).")
            continue
            
        # Validate CSV structure
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames or []
                
                # Check for required columns
                required_columns = ['item_no', 'unique_id', 'name']
                missing_columns = [col for col in required_columns if col not in headers]
                
                if missing_columns:
                    print(f"❌ CSV missing required columns: {missing_columns}")
                    print(f"   Found columns: {headers}")
                    continue
                
                # Count rows
                rows = list(reader)
                print(f"✅ Valid sequence list with {len(rows)} items")
                return csv_file
                
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            continue

def load_sequence_list(csv_file: str) -> List[Dict]:
    """Load sequence list from CSV file."""
    sequence = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                sequence.append({
                    'item_no': int(row['item_no']),
                    'unique_id': row['unique_id'].strip(),
                    'name': row['name'].strip(),
                    'category': row.get('category', '').strip()
                })
        return sequence
    except Exception as e:
        print(f"❌ Error loading sequence: {e}")
        return []

def find_video_files(video_dir: str, sequence: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """
    Find video files matching the sequence list.
    
    Returns:
        Tuple of (found_videos, missing_items)
    """
    print(f"\n🔍 FINDING VIDEO FILES")
    print("-" * 30)
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    found_videos = []
    missing_items = []
    
    # Get all video files in directory
    all_video_files = {}
    for file in os.listdir(video_dir):
        if Path(file).suffix.lower() in video_extensions:
            # Use filename without extension as key
            name_key = Path(file).stem
            all_video_files[name_key] = file
    
    print(f"📁 Found {len(all_video_files)} video files in directory")
    
    # Match sequence items to video files
    for item in sequence:
        name = item['name']
        unique_id = item['unique_id']
        
        # Try different matching strategies
        video_file = None
        
        # Strategy 1: Exact name match
        if name in all_video_files:
            video_file = all_video_files[name]
        
        # Strategy 2: Exact unique_id match
        elif unique_id in all_video_files:
            video_file = all_video_files[unique_id]
        
        # Strategy 3: Partial name match
        else:
            for file_key, file_name in all_video_files.items():
                if name in file_key or file_key in name:
                    video_file = file_name
                    break
        
        # Strategy 4: Partial unique_id match
        if not video_file:
            for file_key, file_name in all_video_files.items():
                if unique_id in file_key or file_key in unique_id:
                    video_file = file_name
                    break
        
        if video_file:
            video_path = os.path.join(video_dir, video_file)
            found_videos.append(video_path)
            print(f"✅ {item['item_no']:3d}. Found: {video_file}")
        else:
            missing_items.append(item)
            print(f"❌ {item['item_no']:3d}. Missing: {name} (ID: {unique_id})")
    
    return found_videos, missing_items

def get_output_settings() -> Dict:
    """Get output file settings from user."""
    print(f"\n⚙️  OUTPUT SETTINGS")
    print("-" * 30)
    
    # Output filename
    while True:
        output_file = input("Output video filename (default: concatenated_video.mp4): ").strip()
        if not output_file:
            output_file = "concatenated_video.mp4"
        
        if not output_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            output_file += '.mp4'
        
        # Check if file exists
        if os.path.exists(output_file):
            response = input(f"File '{output_file}' exists. Overwrite? (y/n): ").lower().strip()
            if response == 'y':
                break
        else:
            break
    
    # Video quality settings
    print(f"\nVideo quality options:")
    print(f"   1. High quality (slower, larger file)")
    print(f"   2. Medium quality (balanced)")
    print(f"   3. Fast encoding (faster, larger file)")
    
    while True:
        choice = input("Select quality option (1-3, default: 2): ").strip()
        if not choice:
            choice = '2'
        
        if choice in ['1', '2', '3']:
            break
        print("❌ Please enter 1, 2, or 3")
    
    quality_settings = {
        '1': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '18'],
        '2': ['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'],
        '3': ['-c:v', 'libx264', '-preset', 'fast', '-crf', '23']
    }
    
    return {
        'output_file': output_file,
        'ffmpeg_args': quality_settings[choice]
    }

def concatenate_videos(video_files: List[str], output_settings: Dict) -> bool:
    """
    Concatenate videos using FFmpeg.
    
    Args:
        video_files: List of video file paths in order
        output_settings: Dictionary with output settings
        
    Returns:
        True if successful, False otherwise
    """
    if not video_files:
        print("❌ No video files to concatenate")
        return False
    
    print(f"\n🎬 CONCATENATING VIDEOS")
    print("-" * 30)
    print(f"📹 Processing {len(video_files)} videos...")
    print(f"📁 Output: {output_settings['output_file']}")
    
    try:
        # Create temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            for video_file in video_files:
                # Convert to absolute path and escape for FFmpeg
                abs_path = os.path.abspath(video_file)
                # Escape backslashes for Windows paths and single quotes
                escaped_path = abs_path.replace('\\', '/').replace("'", "'\"'\"'")
                temp_file.write(f"file '{escaped_path}'\n")
            temp_file_path = temp_file.name
        
        # Build FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_file_path,
        ] + output_settings['ffmpeg_args'] + [
            '-y',  # Overwrite output file
            output_settings['output_file']
        ]
        
        print(f"🔄 Running FFmpeg concatenation...")
        print(f"   Command: {' '.join(ffmpeg_cmd[:8])}... [truncated]")
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            print(f"✅ Successfully created: {output_settings['output_file']}")
            
            # Show file size
            if os.path.exists(output_settings['output_file']):
                file_size = os.path.getsize(output_settings['output_file'])
                size_mb = file_size / (1024 * 1024)
                print(f"📊 Output file size: {size_mb:.1f} MB")
            
            return True
        else:
            print(f"❌ FFmpeg failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg timed out after 1 hour")
        return False
    except Exception as e:
        print(f"❌ Error during concatenation: {e}")
        return False

def main():
    print("🎬 INTERACTIVE VIDEO CONCATENATOR")
    print("=" * 50)
    print("This tool will concatenate videos based on your sequence list.")
    
    # Step 1: Get video location
    video_dir = get_video_location()
    
    # Step 2: Get sequence list
    csv_file = get_sequence_list()
    
    # Step 3: Load sequence
    print(f"\n📊 LOADING SEQUENCE LIST")
    print("-" * 30)
    sequence = load_sequence_list(csv_file)
    
    if not sequence:
        print("❌ Failed to load sequence list")
        return
    
    print(f"✅ Loaded {len(sequence)} items from sequence list")
    
    # Step 4: Find video files
    found_videos, missing_items = find_video_files(video_dir, sequence)
    
    # Step 5: Show summary
    print(f"\n📋 MATCHING SUMMARY")
    print("-" * 30)
    print(f"✅ Found: {len(found_videos)} videos")
    print(f"❌ Missing: {len(missing_items)} videos")
    
    if missing_items:
        print(f"\n⚠️  Missing videos:")
        for item in missing_items[:10]:  # Show first 10
            print(f"   {item['item_no']:3d}. {item['name']} (ID: {item['unique_id']})")
        if len(missing_items) > 10:
            print(f"   ... and {len(missing_items) - 10} more")
    
    if not found_videos:
        print("❌ No videos found to concatenate")
        return
    
    # Step 6: Confirm and get output settings
    response = input(f"\nProceed with concatenating {len(found_videos)} videos? (y/n): ").lower().strip()
    if response != 'y':
        print("❌ Cancelled")
        return
    
    output_settings = get_output_settings()
    
    # Step 7: Concatenate videos
    success = concatenate_videos(found_videos, output_settings)
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"   Concatenated {len(found_videos)} videos")
        print(f"   Output saved as: {output_settings['output_file']}")
        print(f"   You can now play your custom video sequence!")
    else:
        print(f"\n❌ FAILED to concatenate videos")
        print(f"   Check FFmpeg installation and video file formats")

if __name__ == "__main__":
    main()
