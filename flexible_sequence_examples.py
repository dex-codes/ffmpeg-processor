#!/usr/bin/env python3
"""
Examples demonstrating the flexible sequence generator.

This script shows how to use the new flexible variable system that can handle:
1. Single level (just categories)
2. Two levels (category + color)
3. Multiple levels (category + color + size + texture, etc.)

Author: Flexible Sequence Examples
Date: 2025-01-06
"""

from sequence_generator import RealWorldItemGenerator


def example_single_level():
    """Example 1: Single level - just categories (no other variables)."""
    print("🎯 EXAMPLE 1: SINGLE LEVEL (Categories Only)")
    print("=" * 50)
    
    generator = RealWorldItemGenerator(min_spacing=2)
    
    # Single level: just categories
    variable_filters = {
        'category': ['cooking', 'sand', 'drink', 'foam', 'chemical']
    }
    
    try:
        sequence = generator.generate_sequence_flexible(
            variable_filters=variable_filters,
            sequence_length=20,
            csv_file='sample_clips.csv'
        )
        
        print(f"✅ Generated {len(sequence)} items")
        print("First 10 items:")
        for i, item in enumerate(sequence[:10], 1):
            print(f"  {i}: {item}")
        
        # Export to CSV
        generator.export_sequence_to_csv_flexible(sequence, 'single_level_sequence.csv')
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_two_levels():
    """Example 2: Two levels - category + color."""
    print("\n🎯 EXAMPLE 2: TWO LEVELS (Category + Color)")
    print("=" * 50)
    
    generator = RealWorldItemGenerator(min_spacing=2)
    
    # Two levels: category and color
    variable_filters = {
        'category': ['cooking', 'sand', 'drink'],
        'color': ['red', 'blue', 'orange']
    }
    
    try:
        sequence = generator.generate_sequence_flexible(
            variable_filters=variable_filters,
            sequence_length=15,
            csv_file='sample_clips.csv'
        )
        
        print(f"✅ Generated {len(sequence)} items")
        print("First 10 items:")
        for i, item in enumerate(sequence[:10], 1):
            category, color, item_id = item
            print(f"  {i}: {category} - {color} (item {item_id})")
        
        # Export to CSV
        generator.export_sequence_to_csv_flexible(sequence, 'two_level_sequence.csv')
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_three_levels():
    """Example 3: Three levels - category + color + hypothetical size."""
    print("\n🎯 EXAMPLE 3: THREE LEVELS (Category + Color + Size)")
    print("=" * 50)
    
    # Note: This example assumes your CSV has a 'size' column
    # If not, it will fail gracefully
    
    generator = RealWorldItemGenerator(min_spacing=2)
    
    # Three levels: category, color, and size
    variable_filters = {
        'category': ['cooking', 'drink'],
        'color': ['red', 'blue'],
        'size': ['small', 'large']  # This column might not exist in your CSV
    }
    
    try:
        sequence = generator.generate_sequence_flexible(
            variable_filters=variable_filters,
            sequence_length=10,
            csv_file='sample_clips.csv'
        )
        
        print(f"✅ Generated {len(sequence)} items")
        print("First 5 items:")
        for i, item in enumerate(sequence[:5], 1):
            category, color, size, item_id = item
            print(f"  {i}: {category} - {color} - {size} (item {item_id})")
        
        # Export to CSV
        generator.export_sequence_to_csv_flexible(sequence, 'three_level_sequence.csv')
        
    except Exception as e:
        print(f"❌ Error (expected if 'size' column doesn't exist): {e}")


def example_custom_variables():
    """Example 4: Custom variable combinations."""
    print("\n🎯 EXAMPLE 4: CUSTOM VARIABLES")
    print("=" * 50)
    
    generator = RealWorldItemGenerator(min_spacing=3)  # More spacing
    
    # Custom combination - you can use any columns from your CSV
    variable_filters = {
        'category': ['foam', 'chemical', 'bubbles'],
        'color': ['rainbow', 'green', 'pink']
    }
    
    try:
        sequence = generator.generate_sequence_flexible(
            variable_filters=variable_filters,
            sequence_length=12,
            csv_file='sample_clips.csv'
        )
        
        print(f"✅ Generated {len(sequence)} items")
        print("All items:")
        for i, item in enumerate(sequence, 1):
            category, color, item_id = item
            print(f"  {i}: {category} ({color}) - item {item_id}")
        
        # Export to CSV
        generator.export_sequence_to_csv_flexible(sequence, 'custom_sequence.csv')
        
    except Exception as e:
        print(f"❌ Error: {e}")


def demonstrate_flexibility():
    """Demonstrate the flexibility of the system."""
    print("\n🔧 FLEXIBILITY DEMONSTRATION")
    print("=" * 50)
    
    examples = [
        {
            "name": "Minimal (1 category, 1 color)",
            "filters": {'category': ['cooking'], 'color': ['red']},
            "length": 5
        },
        {
            "name": "Broad (5 categories, 4 colors)",
            "filters": {'category': ['cooking', 'sand', 'drink', 'foam', 'chemical'], 
                       'color': ['red', 'blue', 'orange', 'rainbow']},
            "length": 30
        },
        {
            "name": "Specific subset",
            "filters": {'category': ['slime', 'bubbles'], 'color': ['green', 'pink']},
            "length": 8
        }
    ]
    
    for example in examples:
        print(f"\n📋 {example['name']}:")
        print(f"   Filters: {example['filters']}")
        
        generator = RealWorldItemGenerator(min_spacing=2)
        
        try:
            sequence = generator.generate_sequence_flexible(
                variable_filters=example['filters'],
                sequence_length=example['length'],
                csv_file='sample_clips.csv'
            )
            
            print(f"   ✅ Success: {len(sequence)} items generated")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:50]}...")


def compare_old_vs_new():
    """Compare old method vs new flexible method."""
    print("\n🔄 OLD vs NEW METHOD COMPARISON")
    print("=" * 50)
    
    generator = RealWorldItemGenerator(min_spacing=2)
    
    categories = ['cooking', 'drink', 'foam']
    colors = ['red', 'blue', 'orange']
    
    print("🔸 OLD METHOD (backward compatibility):")
    try:
        old_data = generator.load_clips_from_csv('sample_clips.csv', categories, colors)
        print(f"   ✅ Loaded data: {len(old_data)} categories")
        print(f"   Structure: {list(old_data.keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🔸 NEW FLEXIBLE METHOD:")
    try:
        variable_filters = {'category': categories, 'color': colors}
        new_data = generator.load_clips_from_csv_flexible('sample_clips.csv', variable_filters)
        print(f"   ✅ Loaded data with flexible structure")
        print(f"   Categories: {list(new_data.keys())}")
        if new_data:
            first_cat = list(new_data.keys())[0]
            print(f"   Colors in '{first_cat}': {list(new_data[first_cat].keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    """Run all examples."""
    print("🎬 FLEXIBLE SEQUENCE GENERATOR EXAMPLES")
    print("=" * 60)
    
    # Run examples
    example_single_level()
    example_two_levels()
    example_three_levels()
    example_custom_variables()
    demonstrate_flexibility()
    compare_old_vs_new()
    
    print("\n" + "=" * 60)
    print("🎉 EXAMPLES COMPLETE!")
    print("\nGenerated files:")
    print("- single_level_sequence.csv")
    print("- two_level_sequence.csv") 
    print("- three_level_sequence.csv (if successful)")
    print("- custom_sequence.csv")
    
    print("\n📖 Key Benefits of Flexible System:")
    print("✅ Handle any number of variable levels")
    print("✅ Use any columns from your CSV")
    print("✅ Backward compatible with existing code")
    print("✅ Flexible export with variable columns")
    print("✅ Same spacing constraints apply")


if __name__ == "__main__":
    main()
