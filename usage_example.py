#!/usr/bin/env python3
"""
Usage example for the CSV-based clip sequence generator.

This script demonstrates how to:
1. Preview available clips for given categories and colors
2. Generate a randomized sequence with spacing constraints
3. Export the sequence to CSV

Author: Your Name
Date: 2025-01-06
"""

from sequence_generator import generate_custom_sequence, preview_available_clips

def main():
    print("🎬 FFMPEG CLIP SEQUENCE GENERATOR")
    print("=" * 50)
    
    # Example 1: Your original request
    print("\n📋 EXAMPLE 1: Your Original Request")
    print("-" * 30)
    
    categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
    colors = ['red', 'blue', 'orange', 'rainbow']
    
    # First, preview what's available
    print("Step 1: Checking available clips...")
    preview_available_clips(categories, colors)
    
    # Generate sequence
    print("\nStep 2: Generating sequence...")
    success = generate_custom_sequence(
        categories=categories,
        colors=colors,
        sequence_length=150,
        output_file='example1_sequence.csv'
    )
    
    if success:
        print("✅ Example 1 completed! Check 'example1_sequence.csv'")
    else:
        print("❌ Example 1 failed")
    
    # Example 2: Different parameters
    print("\n\n📋 EXAMPLE 2: Different Parameters")
    print("-" * 30)
    
    categories2 = ['toys', 'slime', 'bubbles', 'ice cream']
    colors2 = ['green', 'pink', 'yellow', 'white']
    
    print("Step 1: Checking available clips...")
    preview_available_clips(categories2, colors2)
    
    print("\nStep 2: Generating shorter sequence...")
    success2 = generate_custom_sequence(
        categories=categories2,
        colors=colors2,
        sequence_length=100,  # Shorter sequence
        output_file='example2_sequence.csv',
        min_spacing=3  # More spacing between same categories
    )
    
    if success2:
        print("✅ Example 2 completed! Check 'example2_sequence.csv'")
    else:
        print("❌ Example 2 failed")
    
    # Example 3: Show what happens with limited clips
    print("\n\n📋 EXAMPLE 3: Limited Clips Scenario")
    print("-" * 30)
    
    categories3 = ['woodwork', 'paint']  # Categories with fewer clips
    colors3 = ['black', 'white']
    
    print("Step 1: Checking available clips...")
    preview_available_clips(categories3, colors3)
    
    print("\nStep 2: Attempting to generate sequence...")
    success3 = generate_custom_sequence(
        categories=categories3,
        colors=colors3,
        sequence_length=50,  # Much shorter sequence
        output_file='example3_sequence.csv'
    )
    
    if success3:
        print("✅ Example 3 completed! Check 'example3_sequence.csv'")
    else:
        print("❌ Example 3 failed - not enough clips available")
    
    print("\n" + "=" * 50)
    print("🎉 All examples completed!")
    print("\nGenerated files:")
    print("- example1_sequence.csv (your original request)")
    print("- example2_sequence.csv (different categories/colors)")
    print("- example3_sequence.csv (limited clips scenario)")
    print("\nEach CSV has columns: item_no, name, link")


def custom_generation():
    """
    Function to easily customize your own generation.
    Modify the parameters below and run this function.
    """
    print("🎯 CUSTOM GENERATION")
    print("=" * 30)
    
    # 🔧 MODIFY THESE PARAMETERS FOR YOUR NEEDS
    my_categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
    my_colors = ['red', 'blue', 'orange', 'rainbow']
    my_sequence_length = 150
    my_output_file = 'my_custom_sequence.csv'
    my_min_spacing = 2
    
    # Preview first
    print("Checking what's available...")
    preview_available_clips(my_categories, my_colors)
    
    # Generate
    print(f"\nGenerating {my_sequence_length} items...")
    success = generate_custom_sequence(
        categories=my_categories,
        colors=my_colors,
        sequence_length=my_sequence_length,
        output_file=my_output_file,
        min_spacing=my_min_spacing
    )
    
    if success:
        print(f"✅ Success! Check '{my_output_file}'")
    else:
        print("❌ Failed - try adjusting parameters")


if __name__ == "__main__":
    # Run the main examples
    main()
    
    # Uncomment the line below to run your custom generation
    # custom_generation()
