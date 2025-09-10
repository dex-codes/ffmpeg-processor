#!/usr/bin/env python3
"""
Integration script that combines the sequence generator with video processor.

This script:
1. Generates a sequence using your CSV-based generator
2. Maps the sequence to actual video files
3. Processes and combines them into a final video

Usage:
    python sequence_to_video.py

Author: Integration Script
Date: 2025-01-06
"""

import csv
import os
from sequence_generator import generate_custom_sequence
from video_processor import process_video_sequence, VIDEO_PRESETS


def csv_to_video_files(csv_file: str, video_directory: str = ".") -> list:
    """
    Convert CSV sequence to list of video file paths.
    
    Args:
        csv_file: Path to CSV file with sequence (item_no, name, link)
        video_directory: Directory containing video files
        
    Returns:
        List of video file paths in sequence order
    """
    video_files = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                clip_name = row['name']
                
                # Try different video file extensions
                for ext in ['.mp4', '.mov', '.avi', '.mkv']:
                    video_path = os.path.join(video_directory, f"{clip_name}{ext}")
                    if os.path.exists(video_path):
                        video_files.append(video_path)
                        break
                else:
                    print(f"⚠️  Warning: Video file not found for {clip_name}")
    
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []
    
    return video_files


def generate_and_process_video(categories: list, colors: list, 
                              sequence_length: int = 150,
                              video_directory: str = ".",
                              output_video: str = "final_compilation.mp4",
                              preset: str = "mobile_vertical",
                              max_workers: int = 4) -> bool:
    """
    Complete pipeline: Generate sequence → Process videos → Create final video.
    
    Args:
        categories: List of categories for sequence generation
        colors: List of colors for sequence generation
        sequence_length: Number of clips in sequence
        video_directory: Directory containing video files
        output_video: Final output video filename
        preset: Video processing preset (see VIDEO_PRESETS)
        max_workers: Number of parallel processing workers
        
    Returns:
        True if successful, False if failed
    """
    print("🎬 SEQUENCE TO VIDEO PIPELINE")
    print("=" * 50)
    
    # Step 1: Generate sequence
    print("📋 Step 1: Generating clip sequence...")
    temp_csv = "temp_sequence.csv"
    
    success = generate_custom_sequence(
        categories=categories,
        colors=colors,
        sequence_length=sequence_length,
        output_file=temp_csv
    )
    
    if not success:
        print("❌ Failed to generate sequence")
        return False
    
    # Step 2: Convert CSV to video file list
    print("\n📁 Step 2: Mapping sequence to video files...")
    video_files = csv_to_video_files(temp_csv, video_directory)
    
    if not video_files:
        print("❌ No video files found")
        return False
    
    print(f"✅ Found {len(video_files)} video files")
    
    # Step 3: Process videos
    print(f"\n🎥 Step 3: Processing videos with '{preset}' preset...")
    
    if preset not in VIDEO_PRESETS:
        print(f"❌ Unknown preset '{preset}'. Available: {list(VIDEO_PRESETS.keys())}")
        return False
    
    preset_config = VIDEO_PRESETS[preset]
    
    success = process_video_sequence(
        input_files=video_files,
        output_file=output_video,
        max_workers=max_workers,
        **preset_config
    )
    
    # Cleanup
    if os.path.exists(temp_csv):
        os.remove(temp_csv)
    
    return success


def main():
    """Example usage of the complete pipeline."""
    
    # 🔧 CONFIGURATION - Modify these parameters
    # ==========================================
    
    # Sequence generation parameters
    CATEGORIES = ['cooking', 'sand', 'drink', 'foam', 'chemical']
    COLORS = ['red', 'blue', 'orange', 'rainbow']
    SEQUENCE_LENGTH = 20  # Start small for testing
    
    # Video processing parameters
    VIDEO_DIRECTORY = "."  # Directory containing your video files
    OUTPUT_VIDEO = "my_compilation.mp4"
    PRESET = "mobile_vertical"  # Options: mobile_vertical, youtube_shorts, tiktok, etc.
    MAX_WORKERS = 4  # Parallel processing workers
    
    # ==========================================
    
    print("🎯 Configuration:")
    print(f"   Categories: {CATEGORIES}")
    print(f"   Colors: {COLORS}")
    print(f"   Sequence Length: {SEQUENCE_LENGTH}")
    print(f"   Video Directory: {VIDEO_DIRECTORY}")
    print(f"   Output Video: {OUTPUT_VIDEO}")
    print(f"   Preset: {PRESET}")
    print(f"   Workers: {MAX_WORKERS}")
    
    # Run the complete pipeline
    success = generate_and_process_video(
        categories=CATEGORIES,
        colors=COLORS,
        sequence_length=SEQUENCE_LENGTH,
        video_directory=VIDEO_DIRECTORY,
        output_video=OUTPUT_VIDEO,
        preset=PRESET,
        max_workers=MAX_WORKERS
    )
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"   Your final video is ready: {OUTPUT_VIDEO}")
        print(f"   The video contains {SEQUENCE_LENGTH} clips processed with {PRESET} settings")
    else:
        print(f"\n❌ PIPELINE FAILED")
        print(f"   Check the error messages above for details")


def quick_test():
    """Quick test with minimal parameters."""
    print("🧪 QUICK TEST MODE")
    print("=" * 30)
    
    # Test with just a few clips
    success = generate_and_process_video(
        categories=['cooking', 'drink'],
        colors=['red', 'blue'],
        sequence_length=5,  # Very small for testing
        output_video="test_compilation.mp4",
        preset="mobile_vertical"
    )
    
    if success:
        print("✅ Quick test passed!")
    else:
        print("❌ Quick test failed!")


if __name__ == "__main__":
    # Run the main pipeline
    main()
    
    # Uncomment to run quick test instead
    # quick_test()
