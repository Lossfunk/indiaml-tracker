import json
import argparse
from collections import defaultdict

def process_institute_data(data_file, name_mapping_file):
    """
    Process institute data by grouping different spellings of the same institute,
    aggregating their paper counts, and sorting them by total count.
    
    Args:
        data_file: Path to JSON file containing conference data
        name_mapping_file: Path to JSON file containing institute name mappings
        
    Returns:
        List of dictionaries with grouped institute data
    """
    # Load the data
    with open(data_file, 'r') as f:
        conference_data = json.load(f)
    
    with open(name_mapping_file, 'r') as f:
        name_mapping = json.load(f)
    
    # Create a reverse mapping from variants to canonical names
    reverse_mapping = {}
    for canonical_name, variants in name_mapping.items():
        for variant in variants:
            reverse_mapping[variant] = canonical_name
    
    # Extract institutions data
    institutions = conference_data["india"]["institutions"]["detailed"]
    
    # Count papers for each canonical institution
    paper_counts = defaultdict(int)
    institute_papers = defaultdict(list)
    unique_paper_ids = defaultdict(set)
    
    for institution_data in institutions:
        institute_name = institution_data["institution"]
        paper_count = institution_data["paper_count"]
        
        # Find canonical name if it exists
        canonical_name = reverse_mapping.get(institute_name, institute_name)
        
        # Add to counts
        paper_counts[canonical_name] += paper_count
        
        # Track the papers and ensure uniqueness
        for paper in institution_data["papers"]:
            paper_id = paper["id"]
            if paper_id not in unique_paper_ids[canonical_name]:
                unique_paper_ids[canonical_name].add(paper_id)
                institute_papers[canonical_name].append({
                    "id": paper_id,
                    "title": paper["title"]
                })
    
    # Create final sorted result
    result = []
    for institute, count in sorted(paper_counts.items(), key=lambda x: x[1], reverse=True):
        result.append({
            "institute": institute,
            "total_paper_count": count,
            "unique_paper_count": len(unique_paper_ids[institute]),
            "papers": sorted(institute_papers[institute], key=lambda x: x["title"])
        })
    
    return result

def generate_summary(grouped_data):
    """
    Generate a summary of the institute data
    
    Args:
        grouped_data: Processed institute data
        
    Returns:
        String containing a summary of the data
    """
    summary = "# Summary of Indian Institute Contributions to ICLR 2025\n\n"
    summary += "## Top Institutes by Paper Count\n\n"
    
    for i, institute in enumerate(grouped_data[:10], 1):
        summary += f"{i}. {institute['institute']}: {institute['total_paper_count']} total contributions ({institute['unique_paper_count']} unique papers)\n"
    
    total_institutes = len(grouped_data)
    total_contributions = sum(inst["total_paper_count"] for inst in grouped_data)
    total_unique_papers = sum(inst["unique_paper_count"] for inst in grouped_data)
    
    summary += f"\n## Statistics\n\n"
    summary += f"- Total Institutes: {total_institutes}\n"
    summary += f"- Total Contributions: {total_contributions}\n"
    summary += f"- Total Unique Papers: {total_unique_papers}\n"
    
    return summary

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Process institute data from conference JSON files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data', 
        dest='data_file',
        required=True,
        help='Path to the JSON file containing conference data'
    )
    
    parser.add_argument(
        '--mapping', 
        dest='mapping_file',
        required=True,
        help='Path to the JSON file containing institute name mappings'
    )
    
    parser.add_argument(
        '--output', 
        dest='output_file',
        default='grouped_institutes.json',
        help='Path to save the grouped institute data (JSON format)'
    )
    
    parser.add_argument(
        '--summary', 
        dest='summary_file',
        default='institute_summary.md',
        help='Path to save the summary report (Markdown format)'
    )
    
    parser.add_argument(
        '--no-print', 
        dest='print_summary',
        action='store_false',
        help='Disable printing summary to console'
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Process the data
    result = process_institute_data(args.data_file, args.mapping_file)
    
    # Save the grouped data
    with open(args.output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Generate summary
    summary = generate_summary(result)
    
    # Print summary if requested
    if args.print_summary:
        print(summary)
    
    # Save the summary
    with open(args.summary_file, 'w') as f:
        f.write(summary)