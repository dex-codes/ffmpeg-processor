"""
Core video processing functions for FFmpeg operations.
Extracted from ffmpeg_processor.py - contains only conversion and concatenation logic.

Functions:
- convert_video_format: Convert single video to standardized format
- convert_videos_parallel: Convert multiple videos in parallel
- concatenate_videos: Combine multiple videos into single output

Author: Extracted from original ffmpeg_processor.py
Date: 2025-01-06
"""

import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional


def convert_video_format(input_file: str, output_file: str, 
                        target_format: str = "mp4", 
                        video_codec: str = "libx264", 
                        audio_codec: str = "aac",
                        frame_width: int = 1080, 
                        frame_height: int = 1920, 
                        frame_rate: float = 29.97, 
                        bitrate: str = "6M") -> Optional[str]:
    """
    Convert a single video file to standardized format and specifications.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        target_format: Output format (default: "mp4")
        video_codec: Video codec (default: "libx264")
        audio_codec: Audio codec (default: "aac")
        frame_width: Output width in pixels (default: 1080)
        frame_height: Output height in pixels (default: 1920)
        frame_rate: Output frame rate (default: 29.97)
        bitrate: Video bitrate (default: "6M")
        
    Returns:
        Output file path if successful, None if failed
    """
    command = [
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", video_codec,
        "-c:a", audio_codec,
        "-vf", f"scale={frame_width}:{frame_height}",
        "-r", str(frame_rate),
        "-b:v", bitrate,
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        output_file
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[✓] Converted {input_file} -> {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"[✗] Conversion failed for {input_file}\nError: {e.stderr}")
        return None


def convert_videos_parallel(input_files: List[str], 
                           target_format: str = "mp4",
                           frame_width: int = 1080, 
                           frame_height: int = 1920,
                           frame_rate: float = 30, 
                           bitrate: str = "6M", 
                           max_workers: int = 4,
                           temp_prefix: str = "temp_clip") -> List[str]:
    """
    Convert multiple video files in parallel to standardized format.
    
    Args:
        input_files: List of input video file paths
        target_format: Output format (default: "mp4")
        frame_width: Output width in pixels (default: 1080)
        frame_height: Output height in pixels (default: 1920)
        frame_rate: Output frame rate (default: 30)
        bitrate: Video bitrate (default: "6M")
        max_workers: Maximum number of parallel workers (default: 4)
        temp_prefix: Prefix for temporary files (default: "temp_clip")
        
    Returns:
        List of successfully converted file paths
    """
    futures = []
    converted_files = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, input_file in enumerate(input_files):
            output_file = f"{temp_prefix}_{i}.{target_format}"
            future = executor.submit(
                convert_video_format,
                input_file, output_file, target_format,
                "libx264", "aac", frame_width, frame_height,
                frame_rate, bitrate
            )
            futures.append((future, output_file))

        for future, output_file in futures:
            result = future.result()
            if result:
                converted_files.append(result)
            else:
                print(f"[!] Skipping {output_file} due to conversion error.")

    return converted_files


def concatenate_videos(input_files: List[str], 
                      output_file: str = "combined_output.mp4",
                      frame_rate: float = 29.97, 
                      bitrate: str = "6M",
                      cleanup_temp: bool = True,
                      input_list_file: str = "input_files.txt") -> bool:
    """
    Concatenate multiple video files into a single output video.
    
    Args:
        input_files: List of video files to concatenate
        output_file: Path to output combined video (default: "combined_output.mp4")
        frame_rate: Output frame rate (default: 29.97)
        bitrate: Video bitrate (default: "6M")
        cleanup_temp: Whether to clean up temporary files (default: True)
        input_list_file: Temporary file list name (default: "input_files.txt")
        
    Returns:
        True if successful, False if failed
    """
    if not input_files:
        print("❌ Error: No input files provided for concatenation.")
        return False

    output_path = os.path.abspath(output_file)

    # Create input list file for FFmpeg concat
    try:
        with open(input_list_file, "w") as f:
            for input_file in input_files:
                f.write(f"file '{input_file}'\n")
    except Exception as e:
        print(f"❌ Could not create input list file: {e}")
        return False

    print(f"🎬 Concatenating {len(input_files)} videos...")

    # FFmpeg concat command
    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", input_list_file,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(frame_rate),
        "-b:v", bitrate,
        "-avoid_negative_ts", "make_zero",
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Successfully concatenated videos into {output_path}")
        success = True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg concatenation failed:\n{e.stderr}")
        success = False
    finally:
        # Cleanup temporary files
        if cleanup_temp:
            if os.path.exists(input_list_file):
                os.remove(input_list_file)
            for temp_file in input_files:
                if temp_file.startswith("temp_") and os.path.exists(temp_file):
                    os.remove(temp_file)

    return success


def process_video_sequence(input_files: List[str], 
                          output_file: str = "final_video.mp4",
                          frame_width: int = 1080, 
                          frame_height: int = 1920,
                          frame_rate: float = 29.97, 
                          bitrate: str = "6M",
                          max_workers: int = 4) -> bool:
    """
    Complete pipeline: convert multiple videos in parallel, then concatenate them.
    
    Args:
        input_files: List of input video file paths
        output_file: Final output video path (default: "final_video.mp4")
        frame_width: Output width in pixels (default: 1080)
        frame_height: Output height in pixels (default: 1920)
        frame_rate: Output frame rate (default: 29.97)
        bitrate: Video bitrate (default: "6M")
        max_workers: Maximum parallel workers (default: 4)
        
    Returns:
        True if entire process successful, False if any step failed
    """
    if not input_files:
        print("❌ Error: No input files provided.")
        return False

    print(f"🔄 Processing {len(input_files)} videos...")
    
    # Step 1: Convert all videos in parallel
    print("Step 1: Converting videos to standardized format...")
    converted_files = convert_videos_parallel(
        input_files=input_files,
        frame_width=frame_width,
        frame_height=frame_height,
        frame_rate=frame_rate,
        bitrate=bitrate,
        max_workers=min(max_workers, len(input_files))
    )

    if not converted_files:
        print("❌ No videos were successfully converted.")
        return False

    print(f"✅ Successfully converted {len(converted_files)}/{len(input_files)} videos")

    # Step 2: Concatenate converted videos
    print("Step 2: Concatenating videos...")
    success = concatenate_videos(
        input_files=converted_files,
        output_file=output_file,
        frame_rate=frame_rate,
        bitrate=bitrate,
        cleanup_temp=True
    )

    if success:
        print(f"🎉 Complete! Final video saved as: {output_file}")
    else:
        print("❌ Video processing pipeline failed.")

    return success


# Import configuration presets
try:
    from video_config import VIDEO_PRESETS, CODEC_PRESETS, PROCESSING_DEFAULTS
except ImportError:
    # Fallback presets if config file not available
    VIDEO_PRESETS = {
        "mobile_vertical": {
            "frame_width": 1080,
            "frame_height": 1920,
            "frame_rate": 30,
            "bitrate": "6M"
        }
    }


if __name__ == "__main__":
    # Example usage
    example_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
    
    # Use preset configuration
    preset = VIDEO_PRESETS["mobile_vertical"]
    
    success = process_video_sequence(
        input_files=example_files,
        output_file="my_compilation.mp4",
        **preset
    )
    
    if success:
        print("✅ Video processing completed successfully!")
    else:
        print("❌ Video processing failed.")
