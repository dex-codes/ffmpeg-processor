import random
import math
import csv
from collections import defaultdict, Counter
from typing import List, Tuple, Dict

class RealWorldItemGenerator:
    """
    Generator that handles real-world sparse data where each category has
    different numbers of items for each variation.
    """

    def __init__(self, min_spacing: int = 2):
        """
        Initialize the generator.

        Args:
            min_spacing: Minimum spacing between items of same category
        """
        self.min_spacing = min_spacing
        self.category_data = {}  # Will store actual available items per category per variation
        self.clip_inventory = {}  # Will store actual clip data: {(category, color, item_id): {'name': ..., 'link': ...}}
        self.previous_sequences = []
        self.max_similarity_threshold = 0.75

    def load_clips_from_csv_flexible(self, csv_file: str, variable_filters: Dict[str, List[str]]) -> Dict:
        """
        Flexible CSV loader that can handle any number of variable levels.

        Args:
            csv_file: Path to the CSV file
            variable_filters: Dictionary mapping column names to allowed values
                            e.g., {'category': ['cooking', 'sand'], 'color': ['red', 'blue']}
                            or just {'category': ['cooking', 'sand']} for single level

        Returns:
            Nested dictionary structure based on the variable levels provided
        """
        print(f"Loading clips from {csv_file}...")
        print(f"Variable filters: {variable_filters}")

        # Get the variable names and their order
        variable_names = list(variable_filters.keys())
        print(f"Variable levels: {variable_names}")

        # Read CSV and filter clips
        filtered_clips = []
        self.clip_inventory = {}

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Check if this row matches all variable filters
                    matches_all = True
                    clip_data = {'name': row['clip name'].strip()}

                    # Add link if it exists
                    if 'video link' in row:
                        clip_data['link'] = row['video link'].strip()

                    # Check each variable level
                    for var_name, allowed_values in variable_filters.items():
                        if var_name in row:
                            value = row[var_name].strip()
                            if value in allowed_values:
                                clip_data[var_name] = value
                            else:
                                matches_all = False
                                break
                        else:
                            # Variable column doesn't exist in CSV
                            matches_all = False
                            break

                    if matches_all:
                        filtered_clips.append(clip_data)

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file {csv_file} not found")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")

        print(f"Found {len(filtered_clips)} clips matching criteria")

        # Build nested data structure
        nested_data = self._build_nested_structure(filtered_clips, variable_names, variable_filters)

        # Store variable configuration for later use
        self.variable_names = variable_names
        self.variable_filters = variable_filters

        return nested_data

    def _build_nested_structure(self, filtered_clips: List[Dict], variable_names: List[str], variable_filters: Dict[str, List[str]]) -> Dict:
        """
        Build nested data structure based on variable levels.

        Args:
            filtered_clips: List of clip data dictionaries
            variable_names: Ordered list of variable names (e.g., ['category', 'color'])
            variable_filters: Dictionary of variable filters

        Returns:
            Nested dictionary structure with counts
        """
        # Initialize nested structure
        nested_data = {}

        # Create all possible combinations
        def create_nested_dict(names, filters, level=0):
            if level >= len(names):
                return 0  # Leaf level - will store count

            result = {}
            var_name = names[level]
            for value in filters[var_name]:
                result[value] = create_nested_dict(names, filters, level + 1)
            return result

        nested_data = create_nested_dict(variable_names, variable_filters)

        # Count clips and store inventory
        for clip in filtered_clips:
            # Navigate to the correct position in nested structure
            current_level = nested_data
            variable_path = []

            # Build path through the nested structure
            for var_name in variable_names[:-1]:  # All but last level
                value = clip[var_name]
                variable_path.append(value)
                current_level = current_level[value]

            # Handle the last level (where we store counts)
            if variable_names:  # If we have variables
                last_var = variable_names[-1]
                last_value = clip[last_var]
                variable_path.append(last_value)

                # Increment count
                current_level[last_value] += 1
                item_id = current_level[last_value]

                # Store clip details for later retrieval
                # Use tuple of all variable values plus item_id as key
                key = tuple(variable_path + [item_id])
                self.clip_inventory[key] = {
                    'name': clip['name'],
                    'link': clip.get('link', ''),
                    **{var_name: clip[var_name] for var_name in variable_names}
                }
            else:
                # No variables - just category level
                # This shouldn't happen with current structure, but handle gracefully
                pass

        return nested_data

    def load_clips_from_csv(self, csv_file: str, target_categories: List[str], target_colors: List[str]) -> Dict[str, Dict[int, int]]:
        """
        Backward compatibility method - converts to new flexible format.
        """
        variable_filters = {
            'category': target_categories,
            'color': target_colors
        }

        nested_data = self.load_clips_from_csv_flexible(csv_file, variable_filters)

        # Convert back to old format for compatibility
        category_data = {}
        color_to_index = {color: idx + 1 for idx, color in enumerate(target_colors)}

        for category in target_categories:
            category_data[category] = {}
            for color in target_colors:
                color_index = color_to_index[color]
                count = nested_data.get(category, {}).get(color, 0)
                category_data[category][color_index] = count

        # Store mappings for compatibility
        self.color_index_map = color_to_index
        self.index_color_map = {idx: color for color, idx in color_to_index.items()}

        return category_data

    def generate_sequence_flexible(self, variable_filters: Dict[str, List[str]],
                                 sequence_length: int = 150,
                                 max_attempts: int = 1000,
                                 csv_file: str = 'sample_clips.csv') -> List[Tuple]:
        """
        Generate sequence with flexible variable levels.

        Args:
            variable_filters: Dictionary mapping variable names to allowed values
                            e.g., {'category': ['cooking', 'sand']} for single level
                            or {'category': ['cooking', 'sand'], 'color': ['red', 'blue']} for two levels
            sequence_length: Target length of sequence
            max_attempts: Maximum attempts to generate valid sequence
            csv_file: Path to CSV file

        Returns:
            List of tuples representing the sequence. Tuple structure depends on variable levels.
        """
        print("FLEXIBLE SEQUENCE GENERATION")
        print("=" * 40)
        print(f"Variable filters: {variable_filters}")
        print(f"Target length: {sequence_length}")

        # Load data with flexible structure
        nested_data = self.load_clips_from_csv_flexible(csv_file, variable_filters)

        # Generate available items
        available_items = self._generate_available_items_flexible(nested_data, variable_filters)

        if len(available_items) < sequence_length:
            raise ValueError(f"Not enough total items: have {len(available_items)}, need {sequence_length}")

        # Generate sequence with spacing constraints
        for attempt in range(max_attempts):
            sequence = []
            remaining_items = available_items.copy()
            random.shuffle(remaining_items)

            # Track usage by primary category (first variable level)
            primary_var = list(variable_filters.keys())[0]
            category_counts = defaultdict(int)
            target_per_category = sequence_length // len(variable_filters[primary_var])

            while len(sequence) < sequence_length and remaining_items:
                placed = False

                # Sort by primary category usage (prefer less-used categories)
                remaining_items.sort(key=lambda x: (
                    category_counts[x[0]],  # Primary category usage
                    random.random()         # Randomize within same usage level
                ))

                # Try to place an item
                for i, item in enumerate(remaining_items):
                    primary_category = item[0]

                    # Skip if this category is over-represented
                    if category_counts[primary_category] >= target_per_category + 2:
                        continue

                    if self._can_place_item_flexible(sequence, item):
                        sequence.append(item)
                        remaining_items.pop(i)
                        category_counts[primary_category] += 1
                        placed = True
                        break

                if not placed:
                    break

            if len(sequence) == sequence_length:
                return sequence

        raise RuntimeError(f"Could not generate valid sequence after {max_attempts} attempts")

    def _generate_available_items_flexible(self, nested_data: Dict, variable_filters: Dict[str, List[str]]) -> List[Tuple]:
        """
        Generate list of available items from flexible nested structure.

        Args:
            nested_data: Nested dictionary with counts
            variable_filters: Variable configuration

        Returns:
            List of tuples representing available items
        """
        available_items = []
        variable_names = list(variable_filters.keys())

        def traverse_nested(data, current_path, level):
            if level >= len(variable_names):
                # We're at a count level
                count = data
                for item_id in range(1, count + 1):
                    item_tuple = tuple(current_path + [item_id])
                    available_items.append(item_tuple)
                return

            var_name = variable_names[level]
            for value in variable_filters[var_name]:
                if value in data:
                    traverse_nested(data[value], current_path + [value], level + 1)

        traverse_nested(nested_data, [], 0)
        return available_items

    def _can_place_item_flexible(self, sequence: List[Tuple], candidate_item: Tuple) -> bool:
        """
        Check if an item can be placed with flexible variable levels.
        Uses primary category (first element) for spacing constraints.
        """
        if len(sequence) == 0:
            return True

        candidate_primary = candidate_item[0]  # Primary category

        # Check last min_spacing items for same primary category
        for i in range(max(0, len(sequence) - self.min_spacing), len(sequence)):
            if sequence[i][0] == candidate_primary:
                return False

        return True

    def set_category_data(self, category_data: Dict[str, Dict[int, int]]):
        """
        Set the real data for each category and variation.
        
        Args:
            category_data: Dict like {
                'cat1': {1: 5, 4: 3, 6: 2},  # cat1 has 5 var1s, 3 var4s, 2 var6s
                'cat2': {1: 8, 4: 1, 6: 7},  # cat2 has 8 var1s, 1 var4, 7 var6s
                ...
            }
        """
        self.category_data = category_data
        print("CATEGORY DATA LOADED:")
        print("=" * 50)
        
        total_available = 0
        for category, variations in category_data.items():
            cat_total = sum(variations.values())
            total_available += cat_total
            print(f"{category}: {cat_total} items total")
            for var, count in sorted(variations.items()):
                print(f"  var{var}: {count} items")
        
        print(f"\nTotal items available across all categories: {total_available}")
        return total_available
    
    def analyze_feasibility(self, target_categories: List[str], 
                          allowed_variations: List[int], 
                          sequence_length: int) -> Dict:
        """
        Analyze if the requested sequence is feasible with real data.
        """
        if not self.category_data:
            return {'error': 'No category data loaded'}
        
        # Calculate available items per category
        available_per_category = {}
        total_available = 0
        
        for category in target_categories:
            if category not in self.category_data:
                return {'error': f'Category {category} not found in data'}
            
            available = sum(
                self.category_data[category].get(var, 0) 
                for var in allowed_variations
            )
            available_per_category[category] = available
            total_available += available
        
        # Calculate requirements
        num_categories = len(target_categories)
        items_needed_per_category = sequence_length / num_categories
        total_needed = sequence_length
        
        # Check basic feasibility
        basic_feasible = total_available >= total_needed
        
        # Check per-category feasibility (accounting for spacing)
        max_per_category_with_spacing = sequence_length // (self.min_spacing + 1) + 1
        
        category_feasibility = {}
        bottleneck_categories = []
        
        for category in target_categories:
            available = available_per_category[category]
            needed = items_needed_per_category
            max_possible = min(available, max_per_category_with_spacing)
            
            feasible = available >= needed
            category_feasibility[category] = {
                'available': available,
                'needed': needed,
                'max_possible_with_spacing': max_possible,
                'feasible': feasible,
                'safety_ratio': available / needed if needed > 0 else float('inf')
            }
            
            if not feasible:
                bottleneck_categories.append(category)
        
        # Overall assessment
        all_categories_feasible = len(bottleneck_categories) == 0
        
        return {
            'basic_feasible': basic_feasible,
            'all_categories_feasible': all_categories_feasible,
            'total_available': total_available,
            'total_needed': total_needed,
            'items_needed_per_category': items_needed_per_category,
            'available_per_category': available_per_category,
            'category_feasibility': category_feasibility,
            'bottleneck_categories': bottleneck_categories,
            'recommendation': self._get_feasibility_recommendation(
                all_categories_feasible, bottleneck_categories, category_feasibility
            )
        }
    
    def _get_feasibility_recommendation(self, feasible, bottlenecks, category_data):
        """Generate recommendations based on feasibility analysis."""
        if feasible:
            min_safety = min(data['safety_ratio'] for data in category_data.values())
            if min_safety > 2.0:
                return "EXCELLENT - Plenty of items available"
            elif min_safety > 1.5:
                return "GOOD - Adequate items with safety margin"
            elif min_safety > 1.2:
                return "MARGINAL - Should work but little room for error"
            else:
                return "RISKY - May fail due to spacing constraints"
        else:
            return f"IMPOSSIBLE - Bottleneck categories: {', '.join(bottlenecks)}"
    
    def _generate_available_items(self, target_categories: List[str], 
                                allowed_variations: List[int]) -> List[Tuple[str, int, int]]:
        """Generate list of all available items based on real data."""
        available_items = []
        
        for category in target_categories:
            if category in self.category_data:
                for variation in allowed_variations:
                    count = self.category_data[category].get(variation, 0)
                    for item_id in range(1, count + 1):
                        available_items.append((category, item_id, variation))
        
        return available_items
    
    def _can_place_item(self, sequence: List[Tuple[str, int, int]], 
                       candidate_item: Tuple[str, int, int]) -> bool:
        """Check if an item can be placed at the end of current sequence."""
        if len(sequence) == 0:
            return True
        
        candidate_category = candidate_item[0]
        
        # Check last min_spacing items for same category
        for i in range(max(0, len(sequence) - self.min_spacing), len(sequence)):
            if sequence[i][0] == candidate_category:
                return False
        
        return True
    
    def generate_sequence(self, target_categories: List[str], 
                         allowed_variations: List[int], 
                         sequence_length: int = 150,
                         max_attempts: int = 1000) -> List[Tuple[str, int, int]]:
        """
        Generate sequence with real-world sparse data constraints.
        """
        # First check feasibility
        feasibility = self.analyze_feasibility(target_categories, allowed_variations, sequence_length)
        
        if not feasibility['all_categories_feasible']:
            raise ValueError(f"Sequence not feasible: {feasibility['recommendation']}")
        
        # Generate available items based on real data
        available_items = self._generate_available_items(target_categories, allowed_variations)
        
        if len(available_items) < sequence_length:
            raise ValueError(f"Not enough total items: have {len(available_items)}, need {sequence_length}")
        
        # Attempt to generate valid sequence
        for attempt in range(max_attempts):
            sequence = []
            remaining_items = available_items.copy()
            random.shuffle(remaining_items)
            
            # Track category usage to maintain balance
            category_counts = defaultdict(int)
            target_per_category = sequence_length // len(target_categories)
            
            while len(sequence) < sequence_length and remaining_items:
                placed = False
                
                # Sort remaining items by category priority (prefer underused categories)
                remaining_items.sort(key=lambda x: (
                    category_counts[x[0]],  # Primary: prefer less-used categories
                    random.random()         # Secondary: randomize within same usage level
                ))
                
                # Try to place an item
                for i, item in enumerate(remaining_items):
                    category = item[0]
                    
                    # Skip if this category is already over-represented
                    if category_counts[category] >= target_per_category + 2:
                        continue
                    
                    if self._can_place_item(sequence, item):
                        sequence.append(item)
                        remaining_items.pop(i)
                        category_counts[category] += 1
                        placed = True
                        break
                
                if not placed:
                    # If we can't place any item, restart
                    break
            
            if len(sequence) == sequence_length:
                return sequence
        
        raise RuntimeError(f"Could not generate valid sequence after {max_attempts} attempts")
    
    def print_sequence_analysis(self, sequence: List[Tuple[str, int, int]], 
                              target_categories: List[str], 
                              allowed_variations: List[int]):
        """Print detailed analysis of generated sequence."""
        print("\nSEQUENCE ANALYSIS")
        print("=" * 50)
        
        # Category distribution
        category_counts = Counter(item[0] for item in sequence)
        print("Category distribution:")
        for category in target_categories:
            count = category_counts[category]
            print(f"  {category}: {count} items")
        
        # Variation distribution
        variation_counts = Counter(item[2] for item in sequence)
        print(f"\nVariation distribution:")
        for var in sorted(allowed_variations):
            count = variation_counts[var]
            print(f"  var{var}: {count} items")
        
        # Utilization per category per variation
        print(f"\nUtilization by category and variation:")
        for category in target_categories:
            print(f"  {category}:")
            for var in sorted(allowed_variations):
                used = len([item for item in sequence if item[0] == category and item[2] == var])
                available = self.category_data.get(category, {}).get(var, 0)
                percentage = (used / available * 100) if available > 0 else 0
                print(f"    var{var}: {used}/{available} ({percentage:.1f}%)")
        
        # Check spacing violations
        violations = self._check_spacing_violations(sequence)
        print(f"\nSpacing violations: {len(violations)}")
        
        if len(violations) == 0:
            print("✓ All spacing constraints satisfied!")
        else:
            print("✗ Spacing violations found:")
            for i, (pos1, pos2, category) in enumerate(violations[:5]):
                print(f"  {category} at positions {pos1+1} and {pos2+1}")
            if len(violations) > 5:
                print(f"  ... and {len(violations)-5} more")
    
    def _check_spacing_violations(self, sequence: List[Tuple[str, int, int]]) -> List[Tuple[int, int, str]]:
        """Check for spacing constraint violations."""
        violations = []
        for i in range(len(sequence)):
            category = sequence[i][0]
            for j in range(i + 1, min(i + self.min_spacing + 1, len(sequence))):
                if sequence[j][0] == category:
                    violations.append((i, j, category))
        return violations

    def export_sequence_to_csv(self, sequence: List[Tuple[str, int, int]], output_file: str):
        """
        Export generated sequence to CSV with item_no, name, link columns.

        Args:
            sequence: Generated sequence of (category, item_id, variation) tuples
            output_file: Path to output CSV file
        """
        print(f"\nExporting sequence to {output_file}...")

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['item_no', 'name', 'link'])  # Header

                for item_no, (category, item_id, variation) in enumerate(sequence, 1):
                    key = (category, variation, item_id)
                    if key in self.clip_inventory:
                        clip_data = self.clip_inventory[key]
                        writer.writerow([item_no, clip_data['name'], clip_data['link']])
                    else:
                        # Fallback if clip not found (shouldn't happen with proper data)
                        color = self.index_color_map.get(variation, f"var{variation}")
                        writer.writerow([item_no, f"{category}_item{item_id:02d}_{color}", ""])

            print(f"✓ Successfully exported {len(sequence)} items to {output_file}")

        except Exception as e:
            print(f"✗ Error exporting to CSV: {e}")

    def export_sequence_to_csv_flexible(self, sequence: List[Tuple], output_file: str):
        """
        Export flexible sequence to CSV with item_no, name, link, and variable columns.

        Args:
            sequence: Generated sequence of variable tuples
            output_file: Path to output CSV file
        """
        print(f"\nExporting flexible sequence to {output_file}...")

        if not hasattr(self, 'variable_names') or not self.variable_names:
            print("❌ No variable configuration found. Use load_clips_from_csv_flexible first.")
            return

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                # Create header with variable columns
                header = ['item_no', 'name', 'link'] + self.variable_names
                writer = csv.writer(file)
                writer.writerow(header)

                for item_no, item_tuple in enumerate(sequence, 1):
                    # item_tuple format: (var1_value, var2_value, ..., item_id)
                    variable_values = item_tuple[:-1]  # All but last (item_id)
                    item_id = item_tuple[-1]           # Last element is item_id

                    # Look up clip data
                    if item_tuple in self.clip_inventory:
                        clip_data = self.clip_inventory[item_tuple]
                        row = [
                            item_no,
                            clip_data['name'],
                            clip_data.get('link', '')
                        ] + list(variable_values)
                        writer.writerow(row)
                    else:
                        # Fallback if clip not found
                        fallback_name = "_".join([str(v) for v in variable_values]) + f"_item{item_id:02d}"
                        row = [item_no, fallback_name, ""] + list(variable_values)
                        writer.writerow(row)

            print(f"✅ Successfully exported {len(sequence)} items to {output_file}")

        except Exception as e:
            print(f"✗ Error exporting flexible sequence to CSV: {e}")


def create_example_data() -> Dict[str, Dict[int, int]]:
    """
    Create example realistic data where categories have different numbers 
    of items for each variation.
    """
    # Simulate real-world scenario where availability varies significantly
    example_data = {
        'cat1': {1: 15, 4: 8, 6: 12},   # 35 total items
        'cat2': {1: 22, 4: 3, 6: 5},    # 30 total items  
        'cat3': {1: 10, 4: 18, 6: 2},   # 30 total items
        'cat4': {1: 7, 4: 12, 6: 20},   # 39 total items
        'cat5': {1: 25, 4: 5, 6: 8},    # 38 total items
    }
    return example_data 


def main_csv_example():
    """
    Example using CSV file with user-specified categories and colors.
    """
    print("CSV-BASED CLIP SEQUENCE GENERATOR")
    print("=" * 60)

    # Create generator
    generator = RealWorldItemGenerator(min_spacing=2)

    # User-specified categories and colors
    target_categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
    target_colors = ['red', 'blue', 'orange', 'rainbow']

    print(f"User request:")
    print(f"Categories: {target_categories}")
    print(f"Colors: {target_colors}")

    try:
        # Load clips from CSV based on user criteria
        category_data = generator.load_clips_from_csv(
            csv_file='sample_clips.csv',
            target_categories=target_categories,
            target_colors=target_colors
        )

        # Set the category data
        total_available = generator.set_category_data(category_data)

        # Configuration for sequence generation
        sequence_length = 150
        allowed_variations = list(range(1, len(target_colors) + 1))  # All color variations

        print(f"\nSEQUENCE GENERATION:")
        print(f"Target length: {sequence_length}")
        print(f"Color variations: {[f'var{i}({generator.index_color_map[i]})' for i in allowed_variations]}")

        # Analyze feasibility
        print(f"\nFEASIBILITY ANALYSIS:")
        print("-" * 30)
        feasibility = generator.analyze_feasibility(target_categories, allowed_variations, sequence_length)

        print(f"Total available: {feasibility['total_available']}")
        print(f"Total needed: {feasibility['total_needed']}")
        print(f"Recommendation: {feasibility['recommendation']}")

        if feasibility['bottleneck_categories']:
            print(f"⚠ Bottleneck categories: {feasibility['bottleneck_categories']}")

        print(f"\nPer-category analysis:")
        for category, data in feasibility['category_feasibility'].items():
            status = "✓" if data['feasible'] else "✗"
            print(f"  {status} {category}: {data['available']} available, "
                  f"{data['needed']:.1f} needed (safety: {data['safety_ratio']:.2f}x)")

        # Generate sequence if feasible
        if feasibility['all_categories_feasible']:
            print(f"\nGENERATING SEQUENCE...")
            print("-" * 30)

            sequence = generator.generate_sequence(
                target_categories=target_categories,
                allowed_variations=allowed_variations,
                sequence_length=sequence_length
            )

            print(f"✓ Successfully generated {len(sequence)} items!")

            # Show first 10 items with actual clip names
            print(f"\nFirst 10 items:")
            for i in range(min(10, len(sequence))):
                category, item_id, variation = sequence[i]
                key = (category, variation, item_id)
                if key in generator.clip_inventory:
                    clip_data = generator.clip_inventory[key]
                    color = clip_data['color']
                    print(f"{i+1:3d}: {clip_data['name']} ({category}, {color})")
                else:
                    color = generator.index_color_map.get(variation, f"var{variation}")
                    print(f"{i+1:3d}: {category}_item{item_id:02d}_{color}")

            # Analyze the sequence
            generator.print_sequence_analysis(sequence, target_categories, allowed_variations)

            # Export to CSV
            output_file = 'generated_sequence.csv'
            generator.export_sequence_to_csv(sequence, output_file)

        else:
            print(f"\nSequence generation skipped due to feasibility issues.")
            print("Suggestions:")
            print("- Reduce sequence_length")
            print("- Add more categories")
            print("- Include more colors")
            print("- Check if you have enough clips in bottleneck categories")

    except Exception as e:
        print(f"Error: {e}")


def main():
    print("REALISTIC ITEM GENERATOR WITH SPARSE DATA")
    print("=" * 60)

    # Create generator
    generator = RealWorldItemGenerator(min_spacing=2)

    # Load example realistic data
    category_data = create_example_data()
    total_available = generator.set_category_data(category_data)
    
    # Configuration
    target_categories = ['cat1', 'cat2', 'cat3', 'cat4', 'cat5']
    allowed_variations = [1, 4, 6]  # var1, var4, var6
    sequence_length = 150
    
    print(f"\nREQUEST:")
    print(f"Categories: {target_categories}")
    print(f"Variations: {allowed_variations}")
    print(f"Target length: {sequence_length}")
    
    # Analyze feasibility
    print(f"\nFEASIBILITY ANALYSIS:")
    print("-" * 30)
    feasibility = generator.analyze_feasibility(target_categories, allowed_variations, sequence_length)
    
    print(f"Total available: {feasibility['total_available']}")
    print(f"Total needed: {feasibility['total_needed']}")
    print(f"Recommendation: {feasibility['recommendation']}")
    
    if feasibility['bottleneck_categories']:
        print(f"⚠ Bottleneck categories: {feasibility['bottleneck_categories']}")
    
    print(f"\nPer-category analysis:")
    for category, data in feasibility['category_feasibility'].items():
        status = "✓" if data['feasible'] else "✗"
        print(f"  {status} {category}: {data['available']} available, "
              f"{data['needed']:.1f} needed (safety: {data['safety_ratio']:.2f}x)")
    
    # Generate sequence if feasible
    if feasibility['all_categories_feasible']:
        print(f"\nGENERATING SEQUENCE...")
        print("-" * 30)
        
        try:
            sequence = generator.generate_sequence(
                target_categories=target_categories,
                allowed_variations=allowed_variations,
                sequence_length=sequence_length
            )
            
            print(f"✓ Successfully generated {len(sequence)} items!")
            
            # Show first 15 items
            print(f"\nFirst 15 items:")
            for i in range(min(15, len(sequence))):
                category, item_id, variation = sequence[i]
                print(f"{i+1:3d}: {category}_item{item_id:02d}_var{variation}")
            
            # Analyze the sequence
            generator.print_sequence_analysis(sequence, target_categories, allowed_variations)
            
        except Exception as e:
            print(f"✗ Generation failed: {e}")
    
    else:
        print(f"\nSequence generation skipped due to feasibility issues.")
        print("Suggestions:")
        print("- Reduce sequence_length")
        print("- Add more categories") 
        print("- Include more variations")
        print("- Increase items in bottleneck categories")


def generate_custom_sequence(categories: List[str], colors: List[str],
                           sequence_length: int = 150,
                           csv_file: str = 'sample_clips.csv',
                           output_file: str = 'generated_sequence.csv',
                           min_spacing: int = 2) -> bool:
    """
    Generate a custom sequence based on user-specified categories and colors.

    Args:
        categories: List of categories to include (e.g., ['cooking', 'sand', 'drink'])
        colors: List of colors to include (e.g., ['red', 'blue', 'orange', 'rainbow'])
        sequence_length: Target length of sequence (default: 150)
        csv_file: Path to CSV file with clip inventory (default: 'sample_clips.csv')
        output_file: Path to output CSV file (default: 'generated_sequence.csv')
        min_spacing: Minimum spacing between items of same category (default: 2)

    Returns:
        True if sequence was successfully generated, False otherwise
    """
    print("CUSTOM CLIP SEQUENCE GENERATOR")
    print("=" * 50)
    print(f"Categories: {categories}")
    print(f"Colors: {colors}")
    print(f"Target length: {sequence_length}")
    print(f"Min spacing: {min_spacing}")

    try:
        # Create generator
        generator = RealWorldItemGenerator(min_spacing=min_spacing)

        # Load clips from CSV
        category_data = generator.load_clips_from_csv(csv_file, categories, colors)
        generator.set_category_data(category_data)

        # All color variations
        allowed_variations = list(range(1, len(colors) + 1))

        # Check feasibility
        feasibility = generator.analyze_feasibility(categories, allowed_variations, sequence_length)
        print(f"\nFeasibility: {feasibility['recommendation']}")

        if not feasibility['all_categories_feasible']:
            print("Cannot generate sequence with current parameters.")
            return False

        # Generate sequence
        sequence = generator.generate_sequence(categories, allowed_variations, sequence_length)
        print(f"✓ Generated {len(sequence)} items successfully!")

        # Export to CSV
        generator.export_sequence_to_csv(sequence, output_file)
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def preview_available_clips(categories: List[str], colors: List[str],
                          csv_file: str = 'sample_clips.csv') -> Dict[str, Dict[str, int]]:
    """
    Preview what clips are available for given categories and colors without generating a sequence.

    Args:
        categories: List of categories to check
        colors: List of colors to check
        csv_file: Path to CSV file with clip inventory

    Returns:
        Dictionary showing available clips per category per color
    """
    print("CLIP INVENTORY PREVIEW")
    print("=" * 40)
    print(f"Categories: {categories}")
    print(f"Colors: {colors}")

    # Create temporary generator to load data
    generator = RealWorldItemGenerator()

    try:
        category_data = generator.load_clips_from_csv(csv_file, categories, colors)

        # Convert back to color names for display
        preview_data = {}
        for category in categories:
            preview_data[category] = {}
            for color in colors:
                color_index = generator.color_index_map[color]
                count = category_data[category].get(color_index, 0)
                preview_data[category][color] = count

        # Display results
        print(f"\nAvailable clips:")
        print("-" * 40)
        for category in categories:
            total = sum(preview_data[category].values())
            print(f"{category}: {total} clips total")
            for color in colors:
                count = preview_data[category][color]
                print(f"  {color}: {count} clips")

        total_clips = sum(sum(cat_data.values()) for cat_data in preview_data.values())
        print(f"\nTotal clips available: {total_clips}")

        return preview_data

    except Exception as e:
        print(f"Error: {e}")
        return {}


if __name__ == "__main__":
    # Example usage - you can modify these parameters
    example_categories = ['cooking', 'sand', 'drink', 'foam', 'chemical']
    example_colors = ['red', 'blue', 'orange', 'rainbow']

    # Generate sequence with example parameters
    success = generate_custom_sequence(
        categories=example_categories,
        colors=example_colors,
        sequence_length=150,
        output_file='my_sequence.csv'
    )

    if success:
        print(f"\n🎉 Success! Check 'my_sequence.csv' for your generated sequence.")
    else:
        print(f"\n❌ Failed to generate sequence. Check the parameters and try again.")

    # Uncomment the line below to run the detailed example instead
    # main_csv_example()

    # Uncomment the line below to run the original example instead
    # main()


def generate_flexible_sequence(variable_filters: Dict[str, List[str]],
                             sequence_length: int = 150,
                             csv_file: str = 'sample_clips.csv',
                             output_file: str = 'flexible_sequence.csv',
                             min_spacing: int = 2) -> bool:
    """
    Easy-to-use function for generating flexible sequences.

    Args:
        variable_filters: Dictionary mapping variable names to allowed values
                         Examples:
                         - {'category': ['cooking', 'sand']} for single level
                         - {'category': ['cooking', 'sand'], 'color': ['red', 'blue']} for two levels
                         - {'category': ['cooking'], 'color': ['red'], 'size': ['large']} for three levels
        sequence_length: Target number of items (default: 150)
        csv_file: Path to CSV file with clip inventory (default: 'sample_clips.csv')
        output_file: Output CSV filename (default: 'flexible_sequence.csv')
        min_spacing: Minimum items between same primary category (default: 2)

    Returns:
        True if successful, False if failed
    """
    print("🎬 FLEXIBLE SEQUENCE GENERATOR")
    print("=" * 40)
    print(f"Variable filters: {variable_filters}")
    print(f"Target length: {sequence_length}")
    print(f"Min spacing: {min_spacing}")

    try:
        # Create generator
        generator = RealWorldItemGenerator(min_spacing=min_spacing)

        # Generate sequence
        sequence = generator.generate_sequence_flexible(
            variable_filters=variable_filters,
            sequence_length=sequence_length,
            csv_file=csv_file
        )

        print(f"✅ Generated {len(sequence)} items successfully!")

        # Show first few items
        print(f"\nFirst 5 items:")
        for i, item in enumerate(sequence[:5], 1):
            print(f"  {i}: {item}")

        # Export to CSV
        generator.export_sequence_to_csv_flexible(sequence, output_file)
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False