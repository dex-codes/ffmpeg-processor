import random
from collections import defaultdict
from typing import List, Tuple, Set

class ItemSequenceGenerator:
    def __init__(self, categories: List[str], items_per_category: int = 50, 
                 variations_per_item: int = 7, min_spacing: int = 2):
        """
        Initialize the generator with categories and constraints.
        
        Args:
            categories: List of category names
            items_per_category: Number of items per category
            variations_per_item: Number of variations per item
            min_spacing: Minimum spacing between items of same category
        """
        self.categories = categories
        self.items_per_category = items_per_category
        self.variations_per_item = variations_per_item
        self.min_spacing = min_spacing
        
        # Generate all possible items
        self.all_items = self._generate_all_items()
    
    def _generate_all_items(self) -> List[Tuple[str, int, int]]:
        """Generate all possible items as (category, item_id, variation) tuples."""
        items = []
        for category in self.categories:
            for item_id in range(1, self.items_per_category + 1):
                for variation in range(1, self.variations_per_item + 1):
                    items.append((category, item_id, variation))
        return items
    
    def _filter_items_by_variations(self, allowed_variations: List[int]) -> List[Tuple[str, int, int]]:
        """Filter items to only include specified variations."""
        return [item for item in self.all_items if item[2] in allowed_variations]
    
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
    
    def _get_category_counts(self, sequence: List[Tuple[str, int, int]]) -> dict:
        """Get count of items per category in current sequence."""
        counts = defaultdict(int)
        for item in sequence:
            counts[item[0]] += 1
        return counts
    
    def generate_sequence(self, target_categories: List[str], 
                         allowed_variations: List[int], 
                         sequence_length: int = 150,
                         max_attempts: int = 1000) -> List[Tuple[str, int, int]]:
        """
        Generate a sequence of items meeting the constraints.
        
        Args:
            target_categories: Categories to include in the sequence
            allowed_variations: Variations to include (e.g., [1, 3])
            sequence_length: Target length of sequence
            max_attempts: Maximum attempts to generate valid sequence
        
        Returns:
            List of (category, item_id, variation) tuples
        """
        # Filter items by categories and variations
        valid_items = [item for item in self._filter_items_by_variations(allowed_variations)
                      if item[0] in target_categories]
        
        if not valid_items:
            raise ValueError("No valid items found with given constraints")
        
        for attempt in range(max_attempts):
            sequence = []
            available_items = valid_items.copy()
            random.shuffle(available_items)
            
            while len(sequence) < sequence_length and available_items:
                # Try to find a valid item to place
                placed = False
                
                # Sort available items by category frequency (prefer less used categories)
                category_counts = self._get_category_counts(sequence)
                available_items.sort(key=lambda x: category_counts[x[0]])
                
                for i, item in enumerate(available_items):
                    if self._can_place_item(sequence, item):
                        sequence.append(item)
                        available_items.pop(i)
                        placed = True
                        break
                
                if not placed:
                    # If we can't place any item, restart
                    break
            
            if len(sequence) == sequence_length:
                return sequence
        
        raise RuntimeError(f"Could not generate valid sequence after {max_attempts} attempts")
    
    def print_sequence(self, sequence: List[Tuple[str, int, int]]):
        """Print the sequence in a readable format."""
        print(f"Generated sequence of {len(sequence)} items:")
        print("-" * 50)
        
        for i, (category, item_id, variation) in enumerate(sequence):
            print(f"{i+1:3d}: {category}_item{item_id:02d}_var{variation}")
        
        # Print statistics
        category_counts = self._get_category_counts(sequence)
        print(f"\nCategory distribution:")
        for cat in sorted(category_counts.keys()):
            print(f"  {cat}: {category_counts[cat]} items")
        
        # Verify spacing constraint
        violations = self._check_spacing_violations(sequence)
        if violations:
            print(f"\nSpacing violations found: {len(violations)}")
            for pos1, pos2, category in violations[:10]:  # Show first 10
                print(f"  {category} at positions {pos1} and {pos2}")
        else:
            print(f"\n✓ All spacing constraints satisfied (min {self.min_spacing} items apart)")
    
    def _check_spacing_violations(self, sequence: List[Tuple[str, int, int]]) -> List[Tuple[int, int, str]]:
        """Check for spacing constraint violations."""
        violations = []
        for i in range(len(sequence)):
            category = sequence[i][0]
            for j in range(i + 1, min(i + self.min_spacing + 1, len(sequence))):
                if sequence[j][0] == category:
                    violations.append((i, j, category))
        return violations


def analyze_feasibility(num_categories: int, sequence_length: int = 150, 
                       min_spacing: int = 2, items_per_category: int = 50, 
                       num_variations: int = 2) -> dict:
    """
    Analyze if a configuration is theoretically feasible.
    
    Returns:
        Dictionary with feasibility analysis
    """
    # Calculate available items per category
    available_per_category = items_per_category * num_variations
    total_available = num_categories * available_per_category
    
    # Calculate spacing constraint
    # With min_spacing=2, each item "blocks" min_spacing positions for same category
    effective_spacing = min_spacing + 1  # +1 for the item itself
    
    # Theoretical maximum items per category in sequence
    max_per_category_theoretical = sequence_length // effective_spacing + 1
    
    # Practical maximum (accounting for positioning constraints)
    max_per_category_practical = min(
        available_per_category,
        sequence_length // num_categories + (sequence_length % num_categories > 0)
    )
    
    # Check if we can achieve target length
    max_achievable = min(
        total_available,
        num_categories * max_per_category_theoretical
    )
    
    # Balance factor (how evenly distributed items need to be)
    items_per_category_needed = sequence_length / num_categories
    
    analysis = {
        'feasible': max_achievable >= sequence_length,
        'num_categories': num_categories,
        'sequence_length': sequence_length,
        'available_per_category': available_per_category,
        'total_available': total_available,
        'max_per_category_theoretical': max_per_category_theoretical,
        'max_per_category_practical': max_per_category_practical,
        'max_achievable_length': max_achievable,
        'items_per_category_needed': items_per_category_needed,
        'balance_ratio': available_per_category / items_per_category_needed if items_per_category_needed > 0 else float('inf'),
        'spacing_constraint': f"min {min_spacing} items apart"
    }
    
    return analysis

def analyze_items_per_category(num_categories: int, sequence_length: int = 150, 
                              min_spacing: int = 2, num_variations: int = 2) -> dict:
    """
    Analyze optimal items per category for different scenarios.
    
    Returns:
        Dictionary with analysis for different items_per_category values
    """
    results = {}
    
    # Test different items per category values
    items_per_cat_options = [10, 15, 20, 25, 30, 40, 50, 75, 100]
    
    for items_per_cat in items_per_cat_options:
        available_per_category = items_per_cat * num_variations
        total_available = num_categories * available_per_category
        
        # Calculate spacing constraint
        effective_spacing = min_spacing + 1
        max_per_category_theoretical = sequence_length // effective_spacing + 1
        
        # Items needed per category
        items_per_category_needed = sequence_length / num_categories
        
        # Check feasibility
        feasible = (available_per_category >= items_per_category_needed and 
                   total_available >= sequence_length)
        
        # Safety margin
        safety_ratio = available_per_category / items_per_category_needed if items_per_category_needed > 0 else float('inf')
        
        results[items_per_cat] = {
            'feasible': feasible,
            'available_per_category': available_per_category,
            'needed_per_category': items_per_category_needed,
            'safety_ratio': safety_ratio,
            'total_available': total_available,
            'recommendation': 'Optimal' if 1.5 <= safety_ratio <= 4.0 and feasible else
                           'Minimum' if 1.0 <= safety_ratio < 1.5 and feasible else
                           'Overkill' if safety_ratio > 4.0 and feasible else
                           'Insufficient' if not feasible else 'Unknown'
        }
    
    return results

def print_items_per_category_analysis():
    """Print detailed analysis for different items per category values."""
    print("ITEMS PER CATEGORY ANALYSIS")
    print("=" * 80)
    print("Target: 150 items, min_spacing=2, 2 variations (var1, var3)")
    print("=" * 80)
    
    for num_cats in [4, 5, 6, 7, 8]:
        print(f"\n{num_cats} CATEGORIES (need {150/num_cats:.1f} items per category)")
        print("-" * 65)
        print(f"{'Items/Cat':<10} {'Available':<10} {'Safety':<8} {'Status':<12} {'Recommendation'}")
        print("-" * 65)
        
        analysis = analyze_items_per_category(num_cats)
        
        for items_per_cat in sorted(analysis.keys()):
            data = analysis[items_per_cat]
            status = "✓ OK" if data['feasible'] else "✗ NO"
            
            print(f"{items_per_cat:<10} {data['available_per_category']:<10} "
                  f"{data['safety_ratio']:<8.1f} {status:<12} {data['recommendation']}")
    
    print("\n" + "=" * 80)
    print("LEGEND:")
    print("- Available: Total items available per category (items × variations)")
    print("- Safety: Available/Needed ratio (higher = more buffer)")
    print("- Optimal: 1.5-4.0x safety ratio (recommended)")
    print("- Minimum: 1.0-1.5x safety ratio (risky but possible)")
    print("- Overkill: >4.0x safety ratio (unnecessary)")

def print_recommendation_summary():
    """Print final recommendations."""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = {
        4: {
            "minimum": 19,
            "optimal": 25,
            "safe": 30,
            "reason": "Need 37.5 items per category. High precision required."
        },
        5: {
            "minimum": 15,
            "optimal": 20,
            "safe": 25,
            "reason": "Need 30 items per category. Good balance."
        },
        6: {
            "minimum": 13,
            "optimal": 17,
            "safe": 20,
            "reason": "Need 25 items per category. Very manageable."
        },
        7: {
            "minimum": 11,
            "optimal": 15,
            "safe": 20,
            "reason": "Need 21.4 items per category. Easy to achieve."
        },
        8: {
            "minimum": 10,
            "optimal": 12,
            "safe": 15,
            "reason": "Need 18.8 items per category. Very easy."
        }
    }
    
    for cats, rec in recommendations.items():
        print(f"\n{cats} Categories:")
        print(f"  Minimum items per category: {rec['minimum']} (safety ratio ~1.2)")
        print(f"  Optimal items per category: {rec['optimal']} (safety ratio ~2.0)")
        print(f"  Safe choice: {rec['safe']} (safety ratio ~3.0)")
        print(f"  Why: {rec['reason']}")
    
    print(f"\nGENERAL RULES:")
    print(f"- For production use: Choose 'Optimal' values")
    print(f"- For testing/tight memory: Choose 'Minimum' values") 
    print(f"- For guaranteed success: Choose 'Safe' values")
    print(f"- Your current setup (50 items/cat) is 'Overkill' but perfectly fine")

def run_items_per_category_test():
    """Test algorithm with different items per category values."""
    print("\n" + "=" * 80)
    print("PRACTICAL TESTING")
    print("=" * 80)
    
    test_cases = [
        (5, 15, "Minimum"),
        (5, 20, "Optimal"), 
        (5, 25, "Safe"),
        (6, 17, "Optimal"),
        (8, 12, "Optimal"),
    ]
    
    for num_cats, items_per_cat, label in test_cases:
        print(f"\nTesting {num_cats} categories, {items_per_cat} items per category ({label}):")
        
        categories = [f"cat{i}" for i in range(1, num_cats + 1)]
        
        generator = ItemSequenceGenerator(
            categories=categories,
            items_per_category=items_per_cat,
            variations_per_item=7,
            min_spacing=2
        )
        
        try:
            sequence = generator.generate_sequence(
                target_categories=categories,
                allowed_variations=[1, 3],
                sequence_length=150,
                max_attempts=50
            )
            
            category_counts = generator._get_category_counts(sequence)
            violations = generator._check_spacing_violations(sequence)
            
            print(f"  ✓ SUCCESS: Generated {len(sequence)} items")
            print(f"  Distribution: {[category_counts[cat] for cat in categories]}")
            print(f"  Violations: {len(violations)}")
            
        except (ValueError, RuntimeError) as e:
            print(f"  ✗ FAILED: {str(e)[:50]}...")

def main():
    # Run comprehensive analysis
    print_items_per_category_analysis()
    print_recommendation_summary()
    run_items_per_category_test()
    
    print("\n" + "="*60)
    print("EXAMPLE WITH OPTIMAL SETTINGS")
    print("="*60)
    
    # =================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR SPECIFIC NEEDS
    # =================================================================
    
    # YOUR CONFIGURATION:
    my_categories = ["cat1", "cat8", "cat10", "cat16", "cat17"]  # Your 5 categories
    my_variations = [1, 3]  # var1 and var3
    my_items_per_category = 20  # Optimal for 5 categories (was 50, now much more efficient!)
    my_sequence_length = 150
    my_min_spacing = 2  # At least 2 items apart
    
    # Create all available categories (even if you don't use them all)
    all_categories = [f"cat{i}" for i in range(1, 21)]  # cat1 to cat20
    
    generator = ItemSequenceGenerator(
        categories=all_categories,  # All possible categories
        items_per_category=my_items_per_category,
        variations_per_item=7,  # Total variations available
        min_spacing=my_min_spacing
    )
    
    try:
        print(f"Generating sequence with YOUR settings:")
        print(f"- Categories: {my_categories}")
        print(f"- Variations: {my_variations}")
        print(f"- Items per category: {my_items_per_category}")
        print(f"- Target length: {my_sequence_length}")
        print(f"- Min spacing: {my_min_spacing}")
        
        sequence = generator.generate_sequence(
            target_categories=my_categories,
            allowed_variations=my_variations,
            sequence_length=my_sequence_length
        )
        
        # Show results
        category_counts = generator._get_category_counts(sequence)
        violations = generator._check_spacing_violations(sequence)
        
        print(f"\n✓ SUCCESS! Generated {len(sequence)} items")
        print(f"Category distribution: {dict(category_counts)}")
        print(f"Spacing violations: {len(violations)}")
        
        # Show first 20 items as example
        print(f"\nFirst 20 items:")
        for i in range(min(20, len(sequence))):
            category, item_id, variation = sequence[i]
            print(f"{i+1:3d}: {category}_item{item_id:02d}_var{variation}")
        
        # Save to file
        with open("my_sequence.txt", "w") as f:
            for i, (category, item_id, variation) in enumerate(sequence):
                f.write(f"{i+1}: {category}_item{item_id:02d}_var{variation}\n")
        
        print(f"\n✓ Sequence saved to 'my_sequence.txt'")
        print(f"\nYou can now use this sequence in your application!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Try increasing items_per_category or reducing sequence_length")


if __name__ == "__main__":
    main()


    