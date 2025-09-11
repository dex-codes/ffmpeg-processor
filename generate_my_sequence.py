#!/usr/bin/env python3
"""
Interactive script to generate your custom clip sequence.

This script will:
1. Ask you to specify your CSV file
2. Analyze the CSV structure and ask which fields to use for:
   - 1st level category (primary grouping)
   - 2nd level category (secondary grouping, optional)
   - 3rd level category (tertiary grouping, optional)
   - Name field (clip name/title)
   - Unique identifier field (primary key)
3. Show you what clips are available
4. Generate a randomized sequence
5. Save it to a CSV file

Author: Your Assistant
Date: 2025-01-06
"""

import csv
import os
import random
from typing import Dict, List, Optional, Tuple
from sequence_generator import RealWorldItemGenerator

def generate_sequence_with_custom_mapping(
    csv_file: str,
    field_mapping: Dict[str, str],
    category_filters: Dict[str, List[str]],
    sequence_length: int,
    min_spacing: int,
    output_file: str
) -> bool:
    """
    Generate a sequence using custom field mappings.

    Args:
        csv_file: Path to input CSV file
        field_mapping: Dictionary mapping field types to column names
        category_filters: Dictionary mapping column names to selected values
        sequence_length: Number of clips in sequence
        min_spacing: Minimum spacing between same category clips
        output_file: Path to output CSV file

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"📊 Loading clips from {csv_file}...")

        # Load and filter clips based on category selections
        clips = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Check if this clip matches our category filters
                matches = True
                for column_name, allowed_values in category_filters.items():
                    if column_name in row:
                        if row[column_name].strip() not in allowed_values:
                            matches = False
                            break
                    else:
                        matches = False
                        break

                if matches:
                    clips.append({
                        'unique_id': row[field_mapping['unique_id']].strip(),
                        'name': row[field_mapping['name']].strip(),
                        'category': row[field_mapping['category_1']].strip()
                    })

        print(f"✅ Found {len(clips)} clips matching your criteria")

        if len(clips) < sequence_length:
            print(f"⚠️  Warning: Only {len(clips)} clips available, but {sequence_length} requested")
            print(f"   Generating sequence with available clips...")
            sequence_length = len(clips)

        # Group clips by category
        clips_by_category = {}
        for clip in clips:
            category = clip['category']
            if category not in clips_by_category:
                clips_by_category[category] = []
            clips_by_category[category].append(clip)

        print(f"📋 Clips by category:")
        for category, category_clips in clips_by_category.items():
            print(f"   {category}: {len(category_clips)} clips")

        # Generate sequence with spacing constraints
        print(f"🎲 Generating randomized sequence with {min_spacing} minimum spacing...")
        sequence = generate_spaced_sequence(clips_by_category, sequence_length, min_spacing)

        if not sequence:
            print(f"❌ Could not generate sequence with current constraints")
            return False

        # Write output CSV
        print(f"💾 Writing sequence to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write header
            writer.writerow(['item_no', 'unique_id', 'name', 'category'])

            # Write sequence
            for i, clip in enumerate(sequence, 1):
                writer.writerow([
                    i,
                    clip['unique_id'],
                    clip['name'],
                    clip['category']
                ])

        print(f"✅ Successfully generated {len(sequence)} clip sequence!")
        return True

    except Exception as e:
        print(f"❌ Error generating sequence: {e}")
        return False

def generate_spaced_sequence(clips_by_category: Dict[str, List], target_length: int, min_spacing: int) -> List[Dict]:
    """
    Generate a sequence with minimum spacing between same categories.

    Args:
        clips_by_category: Dictionary mapping categories to lists of clips
        target_length: Target sequence length
        min_spacing: Minimum spacing between same category clips

    Returns:
        List of clips in sequence order
    """
    if not clips_by_category:
        return []

    # Create a pool of all clips
    all_clips = []
    for category_clips in clips_by_category.values():
        all_clips.extend(category_clips)

    if len(all_clips) < target_length:
        target_length = len(all_clips)

    # Simple approach: try multiple times to generate a valid sequence
    for attempt in range(100):  # Try up to 100 times
        sequence = []
        available_clips = all_clips.copy()
        random.shuffle(available_clips)

        for _ in range(target_length):
            # Find a clip that satisfies spacing constraint
            for i, clip in enumerate(available_clips):
                if can_place_clip(sequence, clip, min_spacing):
                    sequence.append(clip)
                    available_clips.pop(i)
                    break
            else:
                # No valid clip found, try next attempt
                break

        if len(sequence) == target_length:
            return sequence

    # If we couldn't generate full sequence with spacing, generate without strict spacing
    print(f"⚠️  Could not maintain {min_spacing} spacing for all clips, using best effort...")
    random.shuffle(all_clips)
    return all_clips[:target_length]

def can_place_clip(sequence: List[Dict], clip: Dict, min_spacing: int) -> bool:
    """Check if a clip can be placed at the end of sequence with spacing constraint."""
    if not sequence:
        return True

    category = clip['category']

    # Check last min_spacing positions
    check_positions = min(len(sequence), min_spacing)
    for i in range(check_positions):
        if sequence[-(i+1)]['category'] == category:
            return False

    return True

def analyze_csv_structure(csv_file: str) -> Tuple[List[str], List[Dict]]:
    """
    Analyze CSV file structure and return column names and sample data.

    Returns:
        Tuple of (column_names, sample_rows)
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []

            # Read first few rows as samples
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 3:  # Only show first 3 rows
                    break
                sample_rows.append(row)

            return columns, sample_rows
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return [], []

def get_csv_file() -> str:
    """Ask user for CSV file path and validate it exists."""
    while True:
        print("\n📁 CSV FILE SELECTION")
        print("-" * 30)
        csv_file = input("Enter path to your CSV file: ").strip()

        if not csv_file:
            print("❌ Please enter a file path.")
            continue

        if not os.path.exists(csv_file):
            print(f"❌ File '{csv_file}' not found.")
            continue

        if not csv_file.lower().endswith('.csv'):
            print("❌ File must be a CSV file (.csv extension).")
            continue

        return csv_file

def show_csv_preview(columns: List[str], sample_rows: List[Dict]):
    """Show CSV structure and sample data."""
    print(f"\n📊 CSV STRUCTURE ANALYSIS")
    print("-" * 30)
    print(f"Found {len(columns)} columns:")

    for i, col in enumerate(columns, 1):
        print(f"   {i:2d}. {col}")

    if sample_rows:
        print(f"\n📋 Sample Data (first {len(sample_rows)} rows):")
        print("-" * 50)

        for i, row in enumerate(sample_rows, 1):
            print(f"Row {i}:")
            for col in columns[:5]:  # Show first 5 columns
                value = row.get(col, '')
                if len(str(value)) > 30:
                    value = str(value)[:27] + "..."
                print(f"   {col}: {value}")
            if len(columns) > 5:
                print(f"   ... and {len(columns) - 5} more columns")
            print()

def get_field_mapping(columns: List[str]) -> Dict[str, str]:
    """
    Interactive field mapping selection with back navigation and validation.

    Returns:
        Dictionary mapping field types to column names
    """
    mapping = {}
    used_columns = set()

    print(f"\n🎯 FIELD MAPPING")
    print("-" * 30)
    print("Now let's map your CSV columns to the sequence generator fields.")
    print("You can skip optional fields by pressing Enter.")
    print("Type 'back' to go back to the previous step.")

    # Step 1: Primary key / unique identifier
    while True:
        print(f"\n1️⃣  UNIQUE IDENTIFIER FIELD (Required)")
        print("   This should be a unique ID for each clip (e.g., 'FileID', 'ID', 'clip_id')")
        result = select_column(columns, required=True, used_columns=used_columns, allow_back=False)
        if result == 'back':
            continue  # Can't go back from first field
        mapping['unique_id'] = result
        used_columns.add(result)
        break

    # Step 2: Name field
    while True:
        print(f"\n2️⃣  NAME FIELD (Required)")
        print("   This should contain the clip name/title (e.g., 'clip name', 'title', 'name')")
        print("   Note: This can be the same as unique identifier if you don't have separate names")
        result = select_column(columns, required=True, used_columns=set(), allow_back=True)  # Allow reusing columns for name
        if result == 'back':
            used_columns.remove(mapping['unique_id'])
            del mapping['unique_id']
            continue
        mapping['name'] = result
        break

    # Step 3: Primary category
    while True:
        print(f"\n3️⃣  PRIMARY CATEGORY FIELD (Required)")
        print("   Main grouping field (e.g., 'Category', 'type', 'genre')")
        result = select_column(columns, required=True, used_columns=used_columns, allow_back=True)
        if result == 'back':
            del mapping['name']
            continue
        mapping['category_1'] = result
        used_columns.add(result)
        break

    # Step 4: Secondary category
    while True:
        print(f"\n4️⃣  SECONDARY CATEGORY FIELD (Optional)")
        print("   Secondary grouping field (e.g., 'color', 'style', 'subcategory')")
        print("   This must be different from your primary category field")
        result = select_column(columns, required=False, used_columns=used_columns, allow_back=True)
        if result == 'back':
            used_columns.remove(mapping['category_1'])
            del mapping['category_1']
            continue
        if result:
            mapping['category_2'] = result
            used_columns.add(result)
        break

    # Step 5: Tertiary category
    if mapping.get('category_2'):
        while True:
            print(f"\n5️⃣  TERTIARY CATEGORY FIELD (Optional)")
            print("   Third-level grouping field (e.g., 'size', 'duration', 'quality')")
            print("   This must be different from your other category fields")
            result = select_column(columns, required=False, used_columns=used_columns, allow_back=True)
            if result == 'back':
                used_columns.remove(mapping['category_2'])
                del mapping['category_2']
                continue
            if result:
                mapping['category_3'] = result
                used_columns.add(result)
            break

    return mapping

def select_column(columns: List[str], required: bool = True, used_columns: set = None, allow_back: bool = False) -> Optional[str]:
    """
    Let user select a column from the available columns with validation and back navigation.

    Args:
        columns: List of available column names
        required: Whether this field is required
        used_columns: Set of already used column names to exclude
        allow_back: Whether to allow going back to previous step

    Returns:
        Selected column name, None if skipped, or 'back' if going back
    """
    if used_columns is None:
        used_columns = set()

    while True:
        print(f"\nAvailable columns:")
        available_columns = []
        for i, col in enumerate(columns, 1):
            if col in used_columns:
                print(f"   {i:2d}. {col} [ALREADY USED]")
            else:
                print(f"   {i:2d}. {col}")
                available_columns.append((i, col))

        option_num = len(columns) + 1
        if not required:
            print(f"   {option_num:2d}. [Skip this field]")
            option_num += 1

        if allow_back:
            print(f"   {option_num:2d}. [Go back to previous step]")

        try:
            choice = input(f"\nSelect column number (or type 'back'): ").strip().lower()

            if choice == 'back' and allow_back:
                return 'back'

            if not choice:
                if required:
                    print("❌ This field is required. Please select a column.")
                    continue
                else:
                    return None

            choice_num = int(choice)

            # Check if it's a valid column selection
            if 1 <= choice_num <= len(columns):
                selected = columns[choice_num - 1]
                if selected in used_columns:
                    print(f"❌ Column '{selected}' is already used. Please select a different column.")
                    continue
                print(f"✅ Selected: {selected}")
                return selected

            # Check if it's skip option
            elif not required and choice_num == len(columns) + 1:
                print("⏭️  Skipped")
                return None

            # Check if it's back option
            elif allow_back and choice_num == len(columns) + (2 if not required else 1):
                return 'back'

            else:
                max_option = len(columns) + (1 if not required else 0) + (1 if allow_back else 0)
                print(f"❌ Please enter a number between 1 and {max_option}")

        except ValueError:
            if choice == 'back' and allow_back:
                return 'back'
            print("❌ Please enter a valid number or 'back'.")

def get_sequence_parameters() -> Dict:
    """Get sequence generation parameters from user with validation and back navigation."""
    print(f"\n⚙️  SEQUENCE PARAMETERS")
    print("-" * 30)
    print("Type 'back' to return to category selection.")

    params = {}

    # Get sequence length
    while True:
        try:
            length_input = input("How many clips do you want in your sequence? (default: 150): ").strip().lower()
            if length_input == 'back':
                return 'back'
            elif not length_input:
                params['sequence_length'] = 150
                break
            else:
                length = int(length_input)
                if length > 0:
                    params['sequence_length'] = length
                    break
                else:
                    print("❌ Please enter a positive number.")
        except ValueError:
            print("❌ Please enter a valid number or 'back'.")

    # Get minimum spacing
    while True:
        try:
            spacing_input = input("Minimum spacing between same category clips? (default: 2): ").strip().lower()
            if spacing_input == 'back':
                return 'back'
            elif not spacing_input:
                params['min_spacing'] = 2
                break
            else:
                spacing = int(spacing_input)
                if spacing >= 0:
                    params['min_spacing'] = spacing
                    break
                else:
                    print("❌ Please enter a non-negative number.")
        except ValueError:
            print("❌ Please enter a valid number or 'back'.")

    # Get output file
    while True:
        output_input = input("Output CSV filename? (default: generated_sequence.csv): ").strip().lower()
        if output_input == 'back':
            return 'back'
        elif not output_input:
            params['output_file'] = "generated_sequence.csv"
            break
        else:
            # Validate filename
            if not output_input.endswith('.csv'):
                output_input += '.csv'
            params['output_file'] = output_input
            break

    return params

def get_category_values(field_mapping: Dict[str, str], csv_file: str):
    """
    Analyze CSV and let user select which values to include for each category field.

    Returns:
        Dictionary mapping field names to selected values, or 'back' if user wants to go back
    """
    print(f"\n🎯 CATEGORY VALUE SELECTION")
    print("-" * 30)
    print("Type 'back' to return to field mapping.")

    category_filters = {}

    # Analyze unique values for each category field
    for field_type in ['category_1', 'category_2', 'category_3']:
        if field_type not in field_mapping or not field_mapping[field_type]:
            continue

        column_name = field_mapping[field_type]
        unique_values = get_unique_values(csv_file, column_name)

        if not unique_values:
            continue

        level_name = {'category_1': 'Primary', 'category_2': 'Secondary', 'category_3': 'Tertiary'}[field_type]

        print(f"\n{level_name} Category Field: '{column_name}'")
        print(f"Available values: {sorted(unique_values)}")

        # Let user select values
        result = select_category_values(unique_values, level_name)
        if result == 'back':
            return 'back'
        elif result:
            category_filters[column_name] = result

    return category_filters

def get_unique_values(csv_file: str, column_name: str) -> List[str]:
    """Get unique values from a specific column in CSV."""
    unique_values = set()
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if column_name in row and row[column_name].strip():
                    unique_values.add(row[column_name].strip())
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

    return sorted(list(unique_values))

def select_category_values(available_values: List[str], level_name: str):
    """Let user select which category values to include with back navigation."""
    print(f"\nSelect {level_name} category values to include:")
    print("Enter numbers separated by commas (e.g., 1,3,5), 'all' for all values, or 'back' to go back:")

    for i, value in enumerate(available_values, 1):
        print(f"   {i:2d}. {value}")

    while True:
        choice = input(f"\nYour selection: ").strip().lower()

        if choice == 'back':
            return 'back'

        if choice == 'all':
            print(f"✅ Selected all {len(available_values)} values")
            return available_values

        if not choice:
            print("❌ Please make a selection, type 'all', or 'back'")
            continue

        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in choice.split(',')]
            selected = []

            for idx in indices:
                if 1 <= idx <= len(available_values):
                    selected.append(available_values[idx - 1])
                else:
                    print(f"❌ Invalid number: {idx}. Please use numbers 1-{len(available_values)}")
                    break
            else:
                # All indices were valid
                if selected:
                    print(f"✅ Selected {len(selected)} values: {selected}")
                    return selected
                else:
                    print("❌ No values selected. Please select at least one value.")

        except ValueError:
            print("❌ Please enter numbers separated by commas, 'all', or 'back'")

def main():
    print("🎬 INTERACTIVE CLIP SEQUENCE GENERATOR")
    print("=" * 50)
    print("This tool will help you create a custom video sequence from your CSV data.")

    # Step 1: Get CSV file
    csv_file = get_csv_file()

    # Step 2: Analyze CSV structure
    print(f"\n🔍 ANALYZING CSV STRUCTURE...")
    columns, sample_rows = analyze_csv_structure(csv_file)

    if not columns:
        print("❌ Could not analyze CSV file. Please check the file format.")
        return

    # Step 3: Show CSV preview
    show_csv_preview(columns, sample_rows)

    # Main workflow with back navigation
    field_mapping = None
    category_filters = None
    params = None

    # Step 4: Get field mapping (with back navigation)
    while field_mapping is None:
        field_mapping = get_field_mapping(columns)

    # Step 5: Get category value selections (with back navigation)
    while category_filters is None:
        result = get_category_values(field_mapping, csv_file)
        if result == 'back':
            field_mapping = None
            continue
        elif not result:
            print("❌ No category fields selected. Cannot generate sequence.")
            return
        else:
            category_filters = result

    # Step 6: Get sequence parameters (with back navigation)
    while params is None:
        result = get_sequence_parameters()
        if result == 'back':
            category_filters = None
            continue
        else:
            params = result

    # Step 7: Show summary and confirm
    while True:
        print(f"\n📋 GENERATION SUMMARY")
        print("-" * 30)
        print(f"Input File: {csv_file}")
        print(f"Output File: {params['output_file']}")
        print(f"Sequence Length: {params['sequence_length']}")
        print(f"Min Spacing: {params['min_spacing']}")
        print(f"Field Mapping:")
        for field_type, column_name in field_mapping.items():
            if column_name:
                print(f"   {field_type}: {column_name}")
        print(f"Category Filters:")
        for field_name, values in category_filters.items():
            print(f"   {field_name}: {values}")

        confirm = input(f"\nProceed with generation? (y/n/back): ").lower().strip()
        if confirm == 'y':
            break
        elif confirm == 'back':
            params = None
            break
        elif confirm == 'n':
            print("❌ Cancelled.")
            return
        else:
            print("❌ Please enter 'y' for yes, 'n' for no, or 'back' to modify parameters.")

    # If we got here and params is None, user went back
    if params is None:
        # Restart the parameter collection loop
        main()
        return

    # Step 8: Generate sequence with custom field mapping
    print(f"\n🎲 GENERATING SEQUENCE...")
    print("-" * 30)

    try:
        success = generate_sequence_with_custom_mapping(
            csv_file=csv_file,
            field_mapping=field_mapping,
            category_filters=category_filters,
            sequence_length=params['sequence_length'],
            min_spacing=params['min_spacing'],
            output_file=params['output_file']
        )

        if success:
            print(f"\n🎉 SUCCESS!")
            print(f"   Your sequence has been saved to: {params['output_file']}")
            print(f"   The file contains {params['sequence_length']} clips with:")
            print(f"   - Sequential numbering")
            print(f"   - {field_mapping['unique_id']} as unique identifier")
            print(f"   - {field_mapping['name']} as clip name")
            print(f"   - Randomized order with {params['min_spacing']} minimum spacing between same categories")
            print(f"\n   You can now use this CSV file for your video processing!")
        else:
            print(f"\n❌ FAILED to generate sequence.")
            print(f"   Check that you have enough clips matching your criteria.")

    except Exception as e:
        print(f"\n❌ ERROR during sequence generation: {e}")
        print(f"   Please check your CSV file and try again.")


if __name__ == "__main__":
    main()
