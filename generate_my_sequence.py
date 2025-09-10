#!/usr/bin/env python3
"""
Simple script to generate your custom clip sequence.

Just modify the parameters below and run:
    python generate_my_sequence.py

The script will:
1. Show you what clips are available
2. Generate a randomized sequence
3. Save it to a CSV file

Author: Your Assistant
Date: 2025-01-06
"""

from sequence_generator import generate_custom_sequence, preview_available_clips

# 🔧 MODIFY THESE PARAMETERS FOR YOUR NEEDS
# ==========================================

# Categories you want (must match categories in your CSV)
CATEGORIES = ['cooking', 'sand', 'drink', 'foam', 'chemical']

# Colors you want (must match colors in your CSV)  
COLORS = ['red', 'blue', 'orange', 'rainbow']

# How many clips you want in total
SEQUENCE_LENGTH = 150

# Minimum spacing between clips of the same category (2 = at least 2 clips between)
MIN_SPACING = 2

# Input CSV file with your clip inventory
INPUT_CSV = 'sample_clips.csv'

# Output CSV file for the generated sequence
OUTPUT_CSV = 'final_sequence.csv'

# ==========================================
# DON'T MODIFY BELOW THIS LINE
# ==========================================

def main():
    print("🎬 GENERATING YOUR CUSTOM CLIP SEQUENCE")
    print("=" * 50)
    
    print(f"📋 Your Settings:")
    print(f"   Categories: {CATEGORIES}")
    print(f"   Colors: {COLORS}")
    print(f"   Sequence Length: {SEQUENCE_LENGTH}")
    print(f"   Min Spacing: {MIN_SPACING}")
    print(f"   Input File: {INPUT_CSV}")
    print(f"   Output File: {OUTPUT_CSV}")
    
    print(f"\n🔍 Step 1: Checking available clips...")
    print("-" * 30)
    
    # Preview what's available
    available = preview_available_clips(CATEGORIES, COLORS, INPUT_CSV)
    
    if not available:
        print("❌ Could not load clip inventory. Check your CSV file.")
        return
    
    # Check if we have enough clips
    total_available = sum(sum(cat_data.values()) for cat_data in available.values())
    
    if total_available < SEQUENCE_LENGTH:
        print(f"\n⚠️  WARNING: You only have {total_available} clips available,")
        print(f"   but you requested {SEQUENCE_LENGTH} clips.")
        print(f"   Consider reducing SEQUENCE_LENGTH or adding more categories/colors.")
        
        response = input(f"\n   Continue anyway? (y/n): ").lower().strip()
        if response != 'y':
            print("   Cancelled.")
            return
    
    print(f"\n🎲 Step 2: Generating randomized sequence...")
    print("-" * 30)
    
    # Generate the sequence
    success = generate_custom_sequence(
        categories=CATEGORIES,
        colors=COLORS,
        sequence_length=SEQUENCE_LENGTH,
        csv_file=INPUT_CSV,
        output_file=OUTPUT_CSV,
        min_spacing=MIN_SPACING
    )
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"   Your sequence has been saved to: {OUTPUT_CSV}")
        print(f"   The file contains {SEQUENCE_LENGTH} clips with:")
        print(f"   - item_no: Sequential number")
        print(f"   - name: Original clip name")
        print(f"   - link: Video link")
        print(f"\n   You can now use this CSV file with your FFMPEG processing!")
    else:
        print(f"\n❌ FAILED to generate sequence.")
        print(f"   Try adjusting the parameters:")
        print(f"   - Reduce SEQUENCE_LENGTH")
        print(f"   - Add more CATEGORIES or COLORS")
        print(f"   - Reduce MIN_SPACING")
        print(f"   - Check that your CSV file has clips matching your criteria")


if __name__ == "__main__":
    main()
