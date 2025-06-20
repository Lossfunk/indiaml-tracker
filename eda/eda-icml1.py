from indiaml.config.name2cc import affiliation_to_country
from dd import d
from rapidfuzz import fuzz, process
import time

def analyze_affiliation_matching(similarity_threshold=80, max_fuzzy_matches=5):
    """
    Analyze affiliation matching with fuzzy search fallback
    
    Args:
        similarity_threshold: Minimum similarity score for fuzzy matches (0-100)
        max_fuzzy_matches: Maximum number of fuzzy matches to consider
    """
    total = len(d)
    keys = list(affiliation_to_country.keys())
    
    # Exact matches
    exact_hits = 0
    fuzzy_hits = 0
    no_match = []
    fuzzy_matches_found = []
    
    print(f"Analyzing {total} affiliations...")
    print(f"Dictionary has {len(keys)} entries")
    print("-" * 50)
    
    start_time = time.time()
    
    for i, affiliation in enumerate(d):
        if i % 1000 == 0:  # Progress indicator
            print(f"Processed {i}/{total} affiliations...")
            
        # Check for exact match first
        if affiliation in affiliation_to_country:
            exact_hits += 1
        else:
            # Try fuzzy matching
            matches = process.extract(
                affiliation, 
                keys, 
                scorer=fuzz.token_sort_ratio,  # Good for handling word order differences
                limit=max_fuzzy_matches
            )
            
            # Check if any match meets our threshold
            best_match = matches[0] if matches else (None, 0)
            
            if best_match[1] >= similarity_threshold:
                fuzzy_hits += 1
                fuzzy_matches_found.append({
                    'original': affiliation,
                    'matched': best_match[0],
                    'score': best_match[1],
                    'country': affiliation_to_country[best_match[0]]
                })
            else:
                no_match.append(affiliation)
    
    end_time = time.time()
    
    # Results
    total_hits = exact_hits + fuzzy_hits
    
    print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
    print("=" * 50)
    print(f"Total affiliations: {total}")
    print(f"Exact matches: {exact_hits}")
    print(f"Fuzzy matches: {fuzzy_hits}")
    print(f"No matches: {len(no_match)}")
    print("-" * 30)
    print(f"Original hit rate: {exact_hits / total:.3f} ({exact_hits / total * 100:.1f}%)")
    print(f"Enhanced hit rate: {total_hits / total:.3f} ({total_hits / total * 100:.1f}%)")
    print(f"Improvement: +{fuzzy_hits / total * 100:.1f} percentage points")
    
    return {
        'exact_hits': exact_hits,
        'fuzzy_hits': fuzzy_hits,
        'total_hits': total_hits,
        'no_match': no_match,
        'fuzzy_matches': fuzzy_matches_found,
        'hit_rate': total_hits / total
    }

def show_fuzzy_examples(results, num_examples=10):
    """Show examples of fuzzy matches found"""
    print(f"\nSample fuzzy matches (showing {num_examples}):")
    print("-" * 70)
    
    for i, match in enumerate(results['fuzzy_matches'][:num_examples]):
        print(f"{i+1:2d}. Original: {match['original']}")
        print(f"    Matched:  {match['matched']} (score: {match['score']})")
        print(f"    Country:  {match['country']}")
        print()

def analyze_unmatched(results, num_examples=10):
    """Analyze unmatched affiliations"""
    print(f"\nSample unmatched affiliations (showing {num_examples}):")
    print("-" * 50)
    
    for i, affiliation in enumerate(results['no_match'][:num_examples]):
        print(f"{i+1:2d}. {affiliation}")

# Run the analysis with different thresholds
if __name__ == "__main__":
    print("Testing different similarity thresholds:")
    print("=" * 60)
    
    thresholds = [70, 75, 80, 85, 90]
    
    for threshold in thresholds:
        print(f"\n>>> Threshold: {threshold}")
        results = analyze_affiliation_matching(similarity_threshold=threshold)
        
    # Detailed analysis with threshold 80
    print("\n" + "="*60)
    print("DETAILED ANALYSIS (Threshold: 80)")
    print("="*60)
    
    results = analyze_affiliation_matching(similarity_threshold=80)
    show_fuzzy_examples(results, num_examples=15)
    analyze_unmatched(results, num_examples=15)
    
    # Try different scoring methods
    print("\n" + "="*60)
    print("COMPARING DIFFERENT FUZZY MATCHING METHODS")
    print("="*60)
    
    # You can experiment with different scorers:
    # fuzz.ratio - Simple ratio
    # fuzz.partial_ratio - Partial string matching
    # fuzz.token_sort_ratio - Sorts tokens before comparing
    # fuzz.token_set_ratio - Compares set of tokens