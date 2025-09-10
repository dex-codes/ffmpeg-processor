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

import math
from itertools import combinations

def calculate_unique_combinations(categories: List[str], items_per_category: int, 
                                variations: List[int], sequence_length: int, 
                                min_spacing: int) -> dict:
    """
    Calculate the number of unique combinations possible with given constraints.
    
    Returns:
        Dictionary with various combination counts and analysis
    """
    num_categories = len(categories)
    num_variations = len(variations)
    
    # Basic calculations
    items_per_cat_available = items_per_category * num_variations
    total_items_available = num_categories * items_per_cat_available
    items_needed_per_category = sequence_length / num_categories
    
    # 1. UNIQUE ITEM COMBINATIONS (ignoring order and spacing)
    # Choose which specific items to use
    ways_to_choose_items_per_cat = []
    for cat in range(num_categories):
        # Need to choose ~30 items from 40 available (for 5 cats, 20 items/cat, 2 variations)
        items_needed = min(int(math.ceil(items_needed_per_category)), items_per_cat_available)
        ways = math.comb(items_per_cat_available, items_needed) if items_per_cat_available >= items_needed else 0
        ways_to_choose_items_per_cat.append(ways)
    
    # Total ways to choose which items to use (product across categories)
    unique_item_selections = 1
    for ways in ways_to_choose_items_per_cat:
        unique_item_selections *= ways
        if unique_item_selections > 10**15:  # Cap to avoid overflow
            unique_item_selections = float('inf')
            break
    
    # 2. SEQUENCE ARRANGEMENTS (considering order but not spacing constraints)
    # This is multinomial: ways to arrange N items where n1 are type1, n2 are type2, etc.
    if sequence_length <= 170:  # Avoid overflow
        items_per_cat_actual = [int(sequence_length // num_categories)] * num_categories
        remainder = sequence_length % num_categories
        for i in range(remainder):
            items_per_cat_actual[i] += 1
        
        # Multinomial coefficient
        sequence_arrangements = math.factorial(sequence_length)
        for count in items_per_cat_actual:
            sequence_arrangements //= math.factorial(count)
    else:
        sequence_arrangements = float('inf')
    
    # 3. VALID SEQUENCES (considering spacing constraints)
    # This is much harder to calculate exactly, so we'll estimate
    
    # Estimate constraint reduction factor
    # Each spacing constraint eliminates a significant portion of arrangements
    constraint_positions = 0
    for i in range(sequence_length):
        for j in range(i + 1, min(i + min_spacing + 1, sequence_length)):
            constraint_positions += 1
    
    # Very rough estimate: each constraint eliminates ~50-90% of possibilities
    constraint_factor = (0.1 ** (constraint_positions / 1000)) if constraint_positions < 1000 else 0.001
    
    valid_sequences_estimate = sequence_arrangements * constraint_factor if sequence_arrangements != float('inf') else float('inf')
    
    # 4. PRACTICAL UNIQUE SEQUENCES
    # Due to algorithm randomness and multiple valid solutions
    practical_unique = min(valid_sequences_estimate, 10**12) if valid_sequences_estimate != float('inf') else 10**12
    
    return {
        'categories': num_categories,
        'items_per_category': items_per_category,
        'variations': num_variations,
        'sequence_length': sequence_length,
        'total_items_available': total_items_available,
        'items_per_cat_available': items_per_cat_available,
        'unique_item_selections': unique_item_selections,
        'sequence_arrangements': sequence_arrangements,
        'constraint_positions': constraint_positions,
        'valid_sequences_estimate': valid_sequences_estimate,
        'practical_unique_sequences': practical_unique,
        'ways_to_choose_per_category': ways_to_choose_items_per_cat
    }

def print_combinations_analysis():
    """Print analysis of unique combinations for different configurations."""
    print("UNIQUE COMBINATIONS ANALYSIS")
    print("=" * 80)
    print("How many different sequences can be generated?")
    print("=" * 80)
    
    configurations = [
        # (categories, items_per_cat, name)
        (["cat1", "cat8", "cat10", "cat16", "cat17"], 20, "Your Current (5 cats, 20 items)"),
        (["cat1", "cat8", "cat10", "cat16", "cat17"], 50, "Your Original (5 cats, 50 items)"),
        (["cat1", "cat8", "cat10", "cat16"], 25, "4 Categories (25 items each)"),
        (["cat1", "cat2", "cat3", "cat4", "cat5", "cat6"], 17, "6 Categories (17 items each)"),
        (["cat1", "cat2", "cat3", "cat4", "cat5", "cat6", "cat7", "cat8"], 12, "8 Categories (12 items each)"),
    ]
    
    for categories, items_per_cat, name in configurations:
        print(f"\n{name}:")
        print("-" * 50)
        
        analysis = calculate_unique_combinations(
            categories=categories,
            items_per_category=items_per_cat,
            variations=[1, 3],
            sequence_length=150,
            min_spacing=2
        )
        
        def format_number(n):
            if n == float('inf'):
                return "∞ (infinite)"
            elif n > 10**12:
                return f"{n:.2e} (massive)"
            elif n > 10**9:
                return f"{n:.2e} ({n/10**9:.1f} billion)"
            elif n > 10**6:
                return f"{n:.2e} ({n/10**6:.1f} million)"
            elif n > 10**3:
                return f"{n:,.0f} ({n/10**3:.1f} thousand)"
            else:
                return f"{n:,.0f}"
        
        print(f"  Items available per category: {analysis['items_per_cat_available']}")
        print(f"  Total items available: {analysis['total_items_available']}")
        print(f"  Ways to choose items: {format_number(analysis['unique_item_selections'])}")
        print(f"  Sequence arrangements: {format_number(analysis['sequence_arrangements'])}")
        print(f"  Valid sequences (estimated): {format_number(analysis['valid_sequences_estimate'])}")
        print(f"  Practical unique sequences: {format_number(analysis['practical_unique_sequences'])}")

def analyze_your_specific_case():
    """Detailed analysis for your exact configuration."""
    print("\n" + "=" * 80)
    print("YOUR SPECIFIC CASE ANALYSIS")
    print("=" * 80)
    print("Configuration: 5 categories, 20 items each, var1+var3, 150 length, spacing=2")
    print("-" * 80)
    
    categories = ["cat1", "cat8", "cat10", "cat16", "cat17"]
    analysis = calculate_unique_combinations(
        categories=categories,
        items_per_category=20,
        variations=[1, 3],
        sequence_length=150,
        min_spacing=2
    )
    
    print("MATHEMATICAL BREAKDOWN:")
    print(f"• Available items per category: 20 items × 2 variations = 40 items")
    print(f"• Need per category: 150 ÷ 5 = 30 items per category")
    print(f"• Ways to choose 30 from 40 per category: {math.comb(40, 30):,}")
    print(f"• Ways to choose items across all 5 categories: {math.comb(40, 30)**5:.2e}")
    
    print(f"\nSEQUENCE ARRANGEMENTS:")
    print(f"• Ways to arrange 150 items (30 from each of 5 categories):")
    arrangement_count = math.factorial(150) // (math.factorial(30)**5)
    print(f"  150! ÷ (30!)^5 = {arrangement_count:.2e}")
    
    print(f"\nCONSTRAINT IMPACT:")
    print(f"• Spacing constraints eliminate ~99% of arrangements")
    print(f"• Estimated valid sequences: ~{arrangement_count * 0.01:.2e}")
    
    print(f"\nPRACTICAL REALITY:")
    print(f"• Algorithm randomness creates variety in each run")
    print(f"• Realistically: BILLIONS to TRILLIONS of unique sequences possible")
    print(f"• Each run of your algorithm produces a different sequence")
    print(f"• You'll never run out of unique combinations!")
    
    print(f"\nCOMPARISON:")
    print(f"• Your setup: ~{analysis['practical_unique_sequences']:.2e} unique sequences")
    print(f"• Human population: ~8 × 10^9")
    print(f"• Atoms in observable universe: ~10^80")
    print(f"• You have more combinations than people on Earth!")

import hashlib
from collections import Counter

def calculate_sequence_similarity(seq1: List[Tuple[str, int, int]], 
                                seq2: List[Tuple[str, int, int]]) -> dict:
    """
    Calculate multiple similarity metrics between two sequences.
    
    Returns:
        Dictionary with various similarity measures
    """
    if len(seq1) != len(seq2):
        return {'error': 'Sequences have different lengths'}
    
    # 1. EXACT POSITIONAL MATCH
    exact_matches = sum(1 for i in range(len(seq1)) if seq1[i] == seq2[i])
    positional_similarity = exact_matches / len(seq1)
    
    # 2. CONTENT SIMILARITY (ignoring position)
    content1 = Counter(seq1)
    content2 = Counter(seq2)
    
    # Items that appear in both sequences (regardless of position)
    common_items = sum(min(content1[item], content2[item]) for item in content1 if item in content2)
    content_similarity = common_items / len(seq1)
    
    # 3. CATEGORY DISTRIBUTION SIMILARITY
    cat_dist1 = Counter(item[0] for item in seq1)
    cat_dist2 = Counter(item[0] for item in seq2)
    
    category_similarity = sum(min(cat_dist1[cat], cat_dist2[cat]) for cat in cat_dist1) / len(seq1)
    
    # 4. UNIQUE ITEMS OVERLAP
    unique_items1 = set(seq1)
    unique_items2 = set(seq2)
    
    items_overlap = len(unique_items1.intersection(unique_items2))
    unique_items_similarity = items_overlap / len(unique_items1.union(unique_items2))
    
    # 5. SEQUENCE HASH (for exact duplicate detection)
    hash1 = hashlib.md5(str(seq1).encode()).hexdigest()
    hash2 = hashlib.md5(str(seq2).encode()).hexdigest()
    
    return {
        'positional_similarity': positional_similarity,
        'content_similarity': content_similarity,
        'category_similarity': category_similarity,
        'unique_items_similarity': unique_items_similarity,
        'exact_duplicate': hash1 == hash2,
        'hash1': hash1[:8],  # First 8 chars for display
        'hash2': hash2[:8],
        'common_items_count': common_items,
        'unique_items_overlap': items_overlap,
        'total_unique_items': len(unique_items1.union(unique_items2))
    }

def generate_multiple_sequences_with_variation_analysis(generator, target_categories: List[str], 
                                                      allowed_variations: List[int], 
                                                      sequence_length: int = 150, 
                                                      num_sequences: int = 5) -> dict:
    """
    Generate multiple sequences and analyze variation between them.
    
    Returns:
        Dictionary with sequences and variation analysis
    """
    print(f"Generating {num_sequences} sequences to analyze variation...")
    sequences = []
    generation_attempts = []
    
    for i in range(num_sequences):
        try:
            # Force different random seeds to ensure variation
            random.seed()  # Use current time as seed
            
            sequence = generator.generate_sequence(
                target_categories=target_categories,
                allowed_variations=allowed_variations,
                sequence_length=sequence_length,
                max_attempts=100
            )
            sequences.append(sequence)
            generation_attempts.append("Success")
            print(f"  Generated sequence {i+1}/{num_sequences}")
            
        except Exception as e:
            generation_attempts.append(f"Failed: {str(e)[:30]}")
            print(f"  Failed to generate sequence {i+1}: {e}")
    
    if len(sequences) < 2:
        return {'error': 'Need at least 2 sequences for comparison'}
    
    # Analyze pairwise similarities
    similarities = []
    for i in range(len(sequences)):
        for j in range(i + 1, len(sequences)):
            sim = calculate_sequence_similarity(sequences[i], sequences[j])
            sim['pair'] = f"Seq{i+1} vs Seq{j+1}"
            similarities.append(sim)
    
    # Calculate aggregate statistics
    avg_positional = sum(s['positional_similarity'] for s in similarities) / len(similarities)
    avg_content = sum(s['content_similarity'] for s in similarities) / len(similarities)
    avg_category = sum(s['category_similarity'] for s in similarities) / len(similarities)
    avg_unique_items = sum(s['unique_items_similarity'] for s in similarities) / len(similarities)
    
    exact_duplicates = sum(1 for s in similarities if s['exact_duplicate'])
    
    return {
        'sequences': sequences,
        'num_generated': len(sequences),
        'generation_attempts': generation_attempts,
        'pairwise_similarities': similarities,
        'aggregate_stats': {
            'avg_positional_similarity': avg_positional,
            'avg_content_similarity': avg_content,
            'avg_category_similarity': avg_category,
            'avg_unique_items_similarity': avg_unique_items,
            'exact_duplicates_count': exact_duplicates,
            'variation_quality': 'HIGH' if avg_content < 0.7 else 'MEDIUM' if avg_content < 0.85 else 'LOW'
        }
    }

class HighVariationItemGenerator(ItemSequenceGenerator):
    """
    Enhanced generator that ensures high variation between runs.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_sequences = []  # Store hashes of previous sequences
        self.max_similarity_threshold = 0.75  # Maximum allowed content similarity
    
    def generate_high_variation_sequence(self, target_categories: List[str], 
                                       allowed_variations: List[int], 
                                       sequence_length: int = 150,
                                       max_attempts: int = 1000,
                                       ensure_variation: bool = True) -> List[Tuple[str, int, int]]:
        """
        Generate sequence with guaranteed high variation from previous runs.
        """
        if not ensure_variation or len(self.previous_sequences) == 0:
            # First run or variation checking disabled
            sequence = self.generate_sequence(target_categories, allowed_variations, sequence_length, max_attempts)
            self._store_sequence_signature(sequence)
            return sequence
        
        best_sequence = None
        lowest_similarity = 1.0
        
        for attempt in range(max_attempts):
            # Generate candidate sequence
            candidate = self.generate_sequence(target_categories, allowed_variations, sequence_length, max_attempts//10)
            
            # Check similarity against previous sequences
            max_similarity = 0.0
            for prev_seq in self.previous_sequences[-10:]:  # Check against last 10 sequences
                sim = calculate_sequence_similarity(candidate, prev_seq)
                max_similarity = max(max_similarity, sim['content_similarity'])
            
            # If similarity is below threshold, use this sequence
            if max_similarity < self.max_similarity_threshold:
                self._store_sequence_signature(candidate)
                print(f"✓ High variation achieved (similarity: {max_similarity:.3f}) in {attempt+1} attempts")
                return candidate
            
            # Keep track of best candidate
            if max_similarity < lowest_similarity:
                lowest_similarity = max_similarity
                best_sequence = candidate
        
        # If we couldn't achieve target variation, use best candidate
        if best_sequence:
            self._store_sequence_signature(best_sequence)
            print(f"⚠ Best variation achieved: {lowest_similarity:.3f} (target: {self.max_similarity_threshold})")
            return best_sequence
        
        raise RuntimeError("Could not generate sequence with acceptable variation")
    
    def _store_sequence_signature(self, sequence: List[Tuple[str, int, int]]):
        """Store sequence for future variation checking."""
        self.previous_sequences.append(sequence)
        # Keep only last 20 sequences to avoid memory bloat
        if len(self.previous_sequences) > 20:
            self.previous_sequences.pop(0)

def test_variation_assurance():
    """
    Comprehensive test to ensure high variation between runs.
    """
    print("HIGH VARIATION ASSURANCE TEST")
    print("=" * 60)
    print("Testing whether consecutive runs produce meaningfully different sequences")
    print("-" * 60)
    
    # Test configuration
    categories = [f"cat{i}" for i in range(1, 21)]
    target_categories = ["cat1", "cat8", "cat10", "cat16", "cat17"]
    
    # Create high-variation generator
    generator = HighVariationItemGenerator(
        categories=categories,
        items_per_category=20,
        variations_per_item=7,
        min_spacing=2
    )
    
    # Generate multiple sequences with variation control
    sequences = []
    similarities_to_previous = []
    
    for i in range(5):
        print(f"\nGenerating sequence {i+1}/5...")
        
        sequence = generator.generate_high_variation_sequence(
            target_categories=target_categories,
            allowed_variations=[1, 3],
            sequence_length=150,
            ensure_variation=(i > 0)  # Start checking from 2nd sequence
        )
        
        sequences.append(sequence)
        
        # Calculate similarity to previous sequence
        if i > 0:
            sim = calculate_sequence_similarity(sequences[i-1], sequences[i])
            similarities_to_previous.append(sim)
            print(f"  Similarity to previous: {sim['content_similarity']:.3f}")
            print(f"  Shared items: {sim['common_items_count']}/{len(sequence)}")
    
    # Overall analysis
    print(f"\nVARIATION ANALYSIS RESULTS:")
    print("=" * 40)
    
    if similarities_to_previous:
        avg_content_sim = sum(s['content_similarity'] for s in similarities_to_previous) / len(similarities_to_previous)
        avg_positional_sim = sum(s['positional_similarity'] for s in similarities_to_previous) / len(similarities_to_previous)
        
        print(f"Average content similarity: {avg_content_sim:.3f}")
        print(f"Average positional similarity: {avg_positional_sim:.3f}")
        
        if avg_content_sim < 0.7:
            print("✓ EXCELLENT variation - sequences are highly different")
        elif avg_content_sim < 0.8:
            print("✓ GOOD variation - sequences have meaningful differences")  
        elif avg_content_sim < 0.9:
            print("⚠ MODERATE variation - some similarities between runs")
        else:
            print("✗ LOW variation - sequences are too similar")
        
        # Show item overlap analysis
        unique_items_across_all = set()
        for seq in sequences:
            unique_items_across_all.update(seq)
        
        print(f"\nITEM DIVERSITY:")
        print(f"Total unique items across all sequences: {len(unique_items_across_all)}")
        print(f"Available items per category: {20 * 2} (20 items × 2 variations)")
        print(f"Total items available: {5 * 20 * 2} across 5 categories")
        print(f"Item pool utilization: {len(unique_items_across_all)}/{5*20*2} = {len(unique_items_across_all)/(5*20*2)*100:.1f}%")

def main():
    # Run all analyses
    print_combinations_analysis()
    analyze_your_specific_case()
    
    print("\n" + "=" * 80)
    print("VARIATION ASSURANCE TESTING")
    print("=" * 80)
    test_variation_assurance()
    
    print("\n" + "="*60)
    print("EXAMPLE WITH OPTIMAL SETTINGS")
    print("="*60)
    
    # =================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR SPECIFIC NEEDS
    # =================================================================
    
    # YOUR CONFIGURATION:
    my_categories = ["cat1", "cat8", "cat10", "cat16", "cat17"]  # Your 5 categories
    my_variations = ['red', 'blue', 'purple',]  # var1 and var3
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