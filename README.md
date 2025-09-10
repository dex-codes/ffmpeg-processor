# FFMPEG Clip Sequence Generator

A Python tool that generates randomized sequences of video clips from your inventory, with intelligent spacing constraints to ensure variety.

## Features

- 📁 **CSV-based inventory**: Reads your clip inventory from a CSV file
- 🎯 **Category & Color filtering**: Select specific categories and colors you want
- 🔄 **Smart randomization**: Ensures minimum spacing between clips of the same category
- 📊 **Feasibility analysis**: Checks if your request is possible before generating
- 📝 **CSV output**: Generates a sequence file with item numbers, names, and links
- 🔍 **Preview mode**: Check available clips before generating sequences

## Quick Start

### 1. Prepare your CSV file

Your CSV should have these columns:
```
clip name,category,color,video link
clip_0001,cooking,red,https://drive.google.com/file/d/123/view
clip_0002,sand,blue,https://drive.google.com/file/d/456/view
...
```

### 2. Basic Usage

```python
from sequence_generator import generate_custom_sequence

# Define what you want
categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
colors = ['red', 'blue', 'orange', 'rainbow']

# Generate sequence
success = generate_custom_sequence(
    categories=categories,
    colors=colors,
    sequence_length=150,
    output_file='my_sequence.csv'
)
```

### 3. Preview Available Clips

```python
from sequence_generator import preview_available_clips

# Check what's available before generating
preview_available_clips(
    categories=['cooking', 'sand', 'drink'],
    colors=['red', 'blue', 'orange']
)
```

## Examples

### Example 1: Your Original Request
```python
categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
colors = ['red', 'blue', 'orange', 'rainbow']
generate_custom_sequence(categories, colors, 150, 'output.csv')
```

### Example 2: Different Parameters
```python
categories = ['toys', 'slime', 'bubbles']
colors = ['green', 'pink', 'yellow']
generate_custom_sequence(
    categories=categories, 
    colors=colors, 
    sequence_length=100,
    min_spacing=3  # More spacing between same categories
)
```

## Function Reference

### `generate_custom_sequence()`
Main function to generate sequences.

**Parameters:**
- `categories`: List of category names to include
- `colors`: List of color names to include  
- `sequence_length`: Target number of items (default: 150)
- `csv_file`: Path to your clip inventory CSV (default: 'sample_clips.csv')
- `output_file`: Output CSV filename (default: 'generated_sequence.csv')
- `min_spacing`: Minimum items between same category (default: 2)

**Returns:** `True` if successful, `False` if failed

### `preview_available_clips()`
Preview what clips are available for given criteria.

**Parameters:**
- `categories`: List of category names to check
- `colors`: List of color names to check
- `csv_file`: Path to your clip inventory CSV

**Returns:** Dictionary with clip counts per category/color

## Output Format

The generated CSV has these columns:
- `item_no`: Sequential number (1, 2, 3, ...)
- `name`: Original clip name from your inventory
- `link`: Video link from your inventory

Example output:
```csv
item_no,name,link
1,clip_0133,https://drive.google.com/file/d/2000000133/view
2,clip_2462,https://drive.google.com/file/d/2000002462/view
3,clip_0552,https://drive.google.com/file/d/2000000552/view
...
```

## Running Examples

```bash
# Run the main examples
python usage_example.py

# Or run the sequence generator directly
python sequence_generator.py
```

## How It Works

1. **Load Inventory**: Reads your CSV and filters by categories/colors
2. **Feasibility Check**: Analyzes if enough clips exist for your request
3. **Smart Generation**: Creates randomized sequence with spacing constraints
4. **Export**: Saves the sequence to CSV with original clip names and links

## Troubleshooting

### "Not enough clips" error
- Reduce `sequence_length`
- Add more categories or colors
- Check if your CSV has clips matching your criteria

### "Spacing violations" warning
- Increase `min_spacing` for more variety
- Add more categories to distribute load
- Reduce `sequence_length`

### "Feasibility: RISKY" warning
- The system will try but might fail
- Consider adjusting parameters for better success rate

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Files

- `sequence_generator.py`: Main generator class and functions
- `usage_example.py`: Example usage scripts
- `sample_clips.csv`: Your clip inventory (modify this)
- `README.md`: This documentation
