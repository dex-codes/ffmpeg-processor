#!/usr/bin/env python3
"""
Analyze video inventory and CSV matching.

This script helps you understand:
1. What video files you have
2. How they match with your CSV FileIDs
3. What might be missing or mismatched

Author: Video Inventory Analyzer
Date: 2025-01-06
"""

import csv
import os
from pathlib import Path
from collections import defaultdict, Counter


def load_csv_data(csv_file: str):
    """Load FileIDs and categories from CSV."""
    data = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append({
                    'category': row['Category'].strip(),
                    'file_id': row['FileID'].strip()
                })
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []
    
    return data


def find_video_files(directory: str):
    """Find all video files in directory."""
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm', '.flv']
    video_files = []
    
    directory_path = Path(directory)
    
    for ext in video_extensions:
        video_files.extend(directory_path.glob(f"*{ext}"))
        video_files.extend(directory_path.glob(f"*{ext.upper()}"))
    
    return [str(f) for f in video_files]


def analyze_matching(csv_data, video_files):
    """Analyze how CSV FileIDs match with actual video files."""
    
    print("🔍 MATCHING ANALYSIS")
    print("=" * 40)
    
    # Extract just filenames from full paths
    video_filenames = [Path(f).name for f in video_files]
    video_stems = [Path(f).stem for f in video_files]  # Without extension
    
    matched = []
    unmatched = []
    
    for item in csv_data:
        file_id = item['file_id']
        category = item['category']
        
        # Try different matching strategies
        found = False
        match_type = ""
        matched_file = ""
        
        # Strategy 1: Exact filename match (with extension)
        for video_file in video_filenames:
            if file_id in video_file:
                found = True
                match_type = "filename_contains"
                matched_file = video_file
                break
        
        # Strategy 2: Exact stem match (without extension)
        if not found:
            for i, stem in enumerate(video_stems):
                if file_id == stem:
                    found = True
                    match_type = "exact_stem"
                    matched_file = video_filenames[i]
                    break
        
        # Strategy 3: FileID contained in stem
        if not found:
            for i, stem in enumerate(video_stems):
                if file_id in stem:
                    found = True
                    match_type = "stem_contains"
                    matched_file = video_filenames[i]
                    break
        
        if found:
            matched.append({
                'file_id': file_id,
                'category': category,
                'matched_file': matched_file,
                'match_type': match_type
            })
        else:
            unmatched.append({
                'file_id': file_id,
                'category': category
            })
    
    return matched, unmatched


def print_analysis_results(csv_data, video_files, matched, unmatched):
    """Print comprehensive analysis results."""
    
    print("📊 INVENTORY ANALYSIS RESULTS")
    print("=" * 50)
    
    # Basic counts
    print(f"📋 CSV Entries: {len(csv_data)}")
    print(f"📁 Video Files Found: {len(video_files)}")
    print(f"✅ Matched: {len(matched)}")
    print(f"❌ Unmatched: {len(unmatched)}")
    
    if csv_data:
        match_rate = len(matched) / len(csv_data) * 100
        print(f"📈 Match Rate: {match_rate:.1f}%")
    
    # Category breakdown
    print(f"\n📂 CATEGORIES IN CSV:")
    category_counts = Counter(item['category'] for item in csv_data)
    for category, count in category_counts.most_common():
        print(f"   {category}: {count} items")
    
    # Match type breakdown
    if matched:
        print(f"\n🎯 MATCH TYPES:")
        match_types = Counter(item['match_type'] for item in matched)
        for match_type, count in match_types.items():
            print(f"   {match_type}: {count} matches")
    
    # Show sample matches
    if matched:
        print(f"\n✅ SAMPLE SUCCESSFUL MATCHES:")
        for item in matched[:10]:
            print(f"   {item['file_id']} -> {item['matched_file']} ({item['match_type']})")
        if len(matched) > 10:
            print(f"   ... and {len(matched) - 10} more")
    
    # Show unmatched items
    if unmatched:
        print(f"\n❌ UNMATCHED ITEMS:")
        for item in unmatched[:15]:
            print(f"   {item['file_id']} ({item['category']})")
        if len(unmatched) > 15:
            print(f"   ... and {len(unmatched) - 15} more")
    
    # Show sample video files
    print(f"\n📁 SAMPLE VIDEO FILES FOUND:")
    for video_file in video_files[:10]:
        filename = Path(video_file).name
        print(f"   {filename}")
    if len(video_files) > 10:
        print(f"   ... and {len(video_files) - 10} more")


def suggest_improvements(matched, unmatched, video_files):
    """Suggest improvements for better matching."""
    
    print(f"\n💡 SUGGESTIONS FOR IMPROVEMENT:")
    print("=" * 40)
    
    if len(unmatched) > 0:
        print(f"🔧 To improve matching:")
        print(f"   1. Check if unmatched FileIDs correspond to actual video files")
        print(f"   2. Verify video file naming conventions")
        print(f"   3. Consider renaming video files to match FileIDs exactly")
        
        # Analyze unmatched FileIDs for patterns
        unmatched_ids = [item['file_id'] for item in unmatched]
        if unmatched_ids:
            print(f"\n🔍 Unmatched FileID patterns:")
            # Check if they look like Google Drive IDs
            google_drive_pattern = all(len(id) > 20 and '-' in id for id in unmatched_ids[:5])
            if google_drive_pattern:
                print(f"   - FileIDs look like Google Drive IDs")
                print(f"   - You may need to download videos with these IDs as filenames")
    
    if len(matched) > 0:
        print(f"\n✅ Good news:")
        print(f"   - {len(matched)} videos can be processed immediately")
        print(f"   - Batch processing will work for matched items")
    
    print(f"\n📋 NEXT STEPS:")
    if len(matched) >= len(unmatched):
        print(f"   1. Run batch processing on matched videos")
        print(f"   2. Handle unmatched videos separately")
    else:
        print(f"   1. Fix video file naming/location issues first")
        print(f"   2. Then run batch processing")


def main():
    """Main analysis function."""
    
    # Configuration
    CSV_FILE = "initial-video-data.csv"
    VIDEO_DIRECTORY = "."  # Current directory
    
    print("🔍 VIDEO INVENTORY ANALYSIS")
    print("=" * 50)
    print(f"CSV File: {CSV_FILE}")
    print(f"Video Directory: {VIDEO_DIRECTORY}")
    
    # Load data
    print(f"\n📋 Loading CSV data...")
    csv_data = load_csv_data(CSV_FILE)
    
    print(f"📁 Scanning for video files...")
    video_files = find_video_files(VIDEO_DIRECTORY)
    
    if not csv_data:
        print(f"❌ No CSV data loaded. Check {CSV_FILE}")
        return
    
    if not video_files:
        print(f"❌ No video files found in {VIDEO_DIRECTORY}")
        return
    
    # Analyze matching
    matched, unmatched = analyze_matching(csv_data, video_files)
    
    # Print results
    print_analysis_results(csv_data, video_files, matched, unmatched)
    
    # Suggestions
    suggest_improvements(matched, unmatched, video_files)


if __name__ == "__main__":
    main()
