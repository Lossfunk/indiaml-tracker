#!/usr/bin/env python3
import json
import argparse
import sqlite3
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import os
from dataclasses import dataclass, field, asdict

@dataclass
class Institution:
    institute: str  # Should store the canonical institution name
    total_paper_count: int = 0
    unique_paper_count: int = 0
    author_count: int = 0
    spotlights: int = 0
    orals: int = 0
    type: str = "academic"
    papers: List[Dict] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)

@dataclass
class CountryStats:
    affiliation_country: str
    paper_count: int = 0
    author_count: int = 0
    spotlights: int = 0
    orals: int = 0

@dataclass
class FocusCountryData:
    country_code: str
    country_name: str
    total_authors: int = 0
    total_spotlights: int = 0
    total_orals: int = 0
    institution_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int)) # Use defaultdict
    at_least_one_focus_country_author: Dict = field(default_factory=lambda: {"count": 0, "papers": []})
    majority_focus_country_authors: Dict = field(default_factory=lambda: {"count": 0, "papers": []})
    first_focus_country_author: Dict = field(default_factory=lambda: {"count": 0, "papers": []})
    institutions: List[Institution] = field(default_factory=list)

def load_institution_mapping(mapping_file: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load institution mapping from a JSON file and create lookup mappings.
    
    Args:
        mapping_file: Path to the JSON file with institution variations.
        
    Returns:
        Tuple of (variation_to_canonical, canonical_to_type) dictionaries.
    """
    if not mapping_file or not os.path.exists(mapping_file):
        print("Warning: Institution mapping file not provided or not found. Normalization will be limited.")
        return {}, {}
        
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    variation_to_canonical = {}
    canonical_to_type = {}
    
    for canonical_name, info in mapping_data.items():
        # Store type, default to 'academic' if not specified
        inst_type = info.get('type', 'academic')
        if not inst_type: # Handle cases where type might be empty string
            inst_type = 'academic'
        canonical_to_type[canonical_name] = inst_type
        
        # Map the canonical name to itself (important for direct lookups)
        variation_to_canonical[canonical_name.strip()] = canonical_name
        
        # Map all variations to the canonical name
        for variation in info.get('variations', []):
            variation_to_canonical[variation.strip()] = canonical_name # Store stripped variations
    
    return variation_to_canonical, canonical_to_type

def normalize_institution_name(name: str, variation_to_canonical: Dict[str, str], sorted_variation_keys_for_partial_match: List[str]) -> str:
    """
    Normalize an institution name using the mapping.
    Prioritizes exact matches, then case-insensitive matches.
    A refined partial match (checking if a known variation is part of the input name) is used as a fallback.
    
    Args:
        name: The institution name to normalize.
        variation_to_canonical: Mapping from variations (and canonical names) to canonical names.
        sorted_variation_keys_for_partial_match: Variation keys sorted by length (desc) for partial matching.
        
    Returns:
        The canonical institution name if found, otherwise the cleaned original name.
    """
    if not name:
        return ""  # Return empty string for None or empty input, consistent with "empty institutes"

    cleaned_name = name.strip()
    if not cleaned_name:
        return ""

    # 1. Exact match with a variation key (keys in variation_to_canonical include canonical names themselves)
    if cleaned_name in variation_to_canonical:
        return variation_to_canonical[cleaned_name]

    # 2. Case-insensitive match with a variation key
    cleaned_name_lower = cleaned_name.lower()
    for var_key, canonical_val in variation_to_canonical.items():
        if var_key.lower() == cleaned_name_lower:
            return canonical_val

    # 3. Partial match: if a known variation (var_key) is part of the cleaned_name_lower.
    #    Uses pre-sorted keys (longest first) to make partial matching more robust.
    if variation_to_canonical: # Only attempt if map exists
        for var_key_for_partial in sorted_variation_keys_for_partial_match:
            var_key_lower = var_key_for_partial.lower() 
            if var_key_lower in cleaned_name_lower:
                return variation_to_canonical[var_key_for_partial]

    # 4. If no mapping found after all attempts, return the original cleaned name.
    return cleaned_name


def get_country_name(country_code: str) -> str:
    """Get the full country name from a country code."""
    country_map = {
        "US": "United States", "CN": "China", "GB": "United Kingdom", "UK": "United Kingdom",
        "IN": "India", "CA": "Canada", "HK": "Hong Kong", "SG": "Singapore",
        "DE": "Germany", "CH": "Switzerland", "KR": "South Korea", "JP": "Japan",
        "AU": "Australia", "IL": "Israel", "FR": "France", "NL": "Netherlands",
    }
    return country_map.get(country_code.upper(), country_code) 

def generate_dashboard_data(db_path: str, conference: str, year: int, focus_country: str = "IN", institution_mapping_file: str = None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    
    variation_to_canonical, canonical_to_type = load_institution_mapping(institution_mapping_file)
    sorted_variation_keys_for_partial = sorted(variation_to_canonical.keys(), key=len, reverse=True)

    # Check if 'accept_type' column exists in the 'papers' table
    cursor.execute("PRAGMA table_info(papers)")
    table_columns_info = cursor.fetchall()
    paper_column_names = [info['name'] for info in table_columns_info] # sqlite3.Row allows dict-like access
    has_actual_accept_type_column = 'accept_type' in paper_column_names

    if has_actual_accept_type_column:
        accept_type_select_expression = "p.accept_type"
        print("INFO: Found 'accept_type' column in 'papers' table. Will use it for oral/spotlight status.")
    else:
        # If the specific 'accept_type' column doesn't exist, select NULL.
        # This means oral/spotlight info will be unavailable from this source.
        accept_type_select_expression = "NULL" 
        print("WARNING: 'accept_type' column not found in 'papers' table. Oral/spotlight information will be treated as unavailable (counts will be 0 unless p.status implies them).")

    # Query to fetch papers.
    # It's crucial that p.status = 'accepted' correctly filters for accepted papers.
    # The 'accept_type_from_query' will hold the value from p.accept_type or NULL.
    papers_query = f"""
        SELECT p.id, p.title, {accept_type_select_expression} AS accept_type_from_query, p.raw_authors, vi.track
        FROM papers p
        LEFT JOIN venue_infos vi ON p.venue_info_id = vi.id
        WHERE vi.conference = ? AND vi.year = ? AND p.status = 'accepted' 
    """
    cursor.execute(papers_query, (conference, year))
    all_papers = cursor.fetchall()
    total_papers = len(all_papers)
    
    country_stats = defaultdict(lambda: CountryStats(affiliation_country=""))
    institution_stats = defaultdict(lambda: Institution(institute="")) 
    
    focus_country_data = FocusCountryData(
        country_code=focus_country,
        country_name=get_country_name(focus_country)
    )
    
    # Query to fetch author details for all accepted papers in the conference/year
    cursor.execute("""
        SELECT a.id AS author_db_id, a.full_name, pa.affiliation_country, pa.affiliation_name, pa.paper_id, pa.position
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        JOIN papers p ON pa.paper_id = p.id
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        WHERE vi.conference = ? AND vi.year = ? AND p.status = 'accepted'
    """, (conference, year))
    
    authors_data = cursor.fetchall()
    
    paper_authors_details = defaultdict(list)
    processed_authors_for_country_stats = set() 

    for author_row in authors_data:
        author_db_id = author_row["author_db_id"]
        author_name = author_row["full_name"]
        raw_country = author_row["affiliation_country"]
        raw_institution = author_row["affiliation_name"]
        paper_id = author_row["paper_id"]
        position = author_row["position"]

        author_country = raw_country.strip() if raw_country else "UNK"
        normalized_canonical_institution = normalize_institution_name(raw_institution, variation_to_canonical, sorted_variation_keys_for_partial)
        
        paper_authors_details[paper_id].append({
            "id": author_db_id, "name": author_name, "country": author_country,
            "institution": normalized_canonical_institution, "position": position
        })
        
        if author_country and (author_db_id, author_country) not in processed_authors_for_country_stats:
            if author_country not in country_stats:
                 country_stats[author_country] = CountryStats(affiliation_country=author_country)
            country_stats[author_country].author_count += 1
            processed_authors_for_country_stats.add((author_db_id, author_country))
            
        if author_country == focus_country:
            inst_key = normalized_canonical_institution
            inst_type = canonical_to_type.get(inst_key, "academic") 
            if not inst_type: inst_type = "academic"

            if not institution_stats[inst_key].institute: 
                 institution_stats[inst_key].institute = inst_key
                 institution_stats[inst_key].type = inst_type
            
            if author_name and author_name not in institution_stats[inst_key].authors:
                institution_stats[inst_key].authors.append(author_name)
                institution_stats[inst_key].author_count +=1

    focus_country_paper_ids = {"at_least_one": set(), "majority": set(), "first_author": set()}
    
    for paper_row in all_papers:
        paper_id = paper_row["id"]
        title = paper_row["title"]
        # This value comes from p.accept_type (if column exists) or NULL
        accept_type_value = paper_row["accept_type_from_query"] 
        
        authors_for_this_paper = paper_authors_details.get(paper_id, [])
        if not authors_for_this_paper:
            continue
        
        # Determine if paper is spotlight or oral based on accept_type_value
        # This handles None correctly (e.g., None and "spotlight" in None.lower() is False)
        is_spotlight = isinstance(accept_type_value, str) and "spotlight" in accept_type_value.lower()
        is_oral = isinstance(accept_type_value, str) and "oral" in accept_type_value.lower()

        unique_countries_in_paper = set(a["country"] for a in authors_for_this_paper if a["country"])
        for country_code in unique_countries_in_paper:
            country_stats[country_code].paper_count += 1
            if is_spotlight:
                country_stats[country_code].spotlights += 1
            if is_oral: 
                country_stats[country_code].orals += 1
        
        focus_country_authors_on_paper = [a for a in authors_for_this_paper if a["country"] == focus_country]
        num_focus_country_authors = len(focus_country_authors_on_paper)
        
        if num_focus_country_authors > 0:
            focus_country_paper_ids["at_least_one"].add(paper_id)
            
            first_author = next((a for a in authors_for_this_paper if a["position"] == 0), None)
            if first_author and first_author["country"] == focus_country:
                focus_country_paper_ids["first_author"].add(paper_id)
            
            if len(authors_for_this_paper) > 0 and num_focus_country_authors > len(authors_for_this_paper) / 2:
                focus_country_paper_ids["majority"].add(paper_id)
                
            unique_institutions_for_paper_in_focus_country = set()
            for author in focus_country_authors_on_paper:
                canonical_institution_name = author["institution"]
                if canonical_institution_name: 
                    unique_institutions_for_paper_in_focus_country.add(canonical_institution_name)
                    current_paper_details = {
                        "id": paper_id, "title": title,
                        "isSpotlight": is_spotlight, "isOral": is_oral # Correctly reflects status
                    }
                    if paper_id not in [p["id"] for p in institution_stats[canonical_institution_name].papers]:
                        institution_stats[canonical_institution_name].papers.append(current_paper_details)
                        institution_stats[canonical_institution_name].unique_paper_count += 1

            for inst_name_key in unique_institutions_for_paper_in_focus_country:
                institution_stats[inst_name_key].total_paper_count += 1
                if is_spotlight:
                    institution_stats[inst_name_key].spotlights += 1
                if is_oral:
                    institution_stats[inst_name_key].orals += 1
    
    focus_country_data.total_authors = country_stats[focus_country].author_count
    focus_country_data.total_spotlights = country_stats[focus_country].spotlights
    focus_country_data.total_orals = country_stats[focus_country].orals
    
    for inst_name, inst_data in institution_stats.items():
        if inst_data.type: 
             focus_country_data.institution_types[inst_data.type] += 1
        else: 
             focus_country_data.institution_types["academic"] += 1

    focus_country_data.at_least_one_focus_country_author["count"] = len(focus_country_paper_ids["at_least_one"])
    focus_country_data.majority_focus_country_authors["count"] = len(focus_country_paper_ids["majority"])
    focus_country_data.first_focus_country_author["count"] = len(focus_country_paper_ids["first_author"])
    
    valid_institutions = [
        inst_obj for inst_key, inst_obj in institution_stats.items() 
        if inst_key and inst_obj.institute and (inst_obj.unique_paper_count > 0 or inst_obj.author_count > 0)
    ]

    sorted_institutions = sorted(
        valid_institutions, key=lambda x: (x.unique_paper_count, x.author_count), reverse=True
    )
    focus_country_data.institutions = [asdict(inst) for inst in sorted_institutions]
    
    global_country_stats_list = [
        asdict(stats) for country_code, stats in country_stats.items() 
        if stats.paper_count > 0 or stats.author_count > 0
    ]
    sorted_global_country_stats = sorted(
        global_country_stats_list, key=lambda x: (x['paper_count'], x['author_count']), reverse=True
    )

    dashboard_data = {
        "conferenceInfo": {
            "name": conference, "year": year, "track": "Conference", "totalAcceptedPapers": total_papers
        },
        "globalStats": {"countries": sorted_global_country_stats},
        "focusCountry": asdict(focus_country_data),
        "configuration": generate_configuration(focus_country, conference, year)
    }
    
    conn.close()
    return dashboard_data

def generate_configuration(focus_country: str, conference: str, year: int) -> Dict:
    country_name = get_country_name(focus_country)
    dashboard_title = f"{country_name} @ {conference} {year}"
    dashboard_subtitle = f"{country_name}'s Contributions, Global Context & Institutional Landscape"
    
    config = {
        "countryMap": {
            "US": "United States", "CN": "China", "GB": "United Kingdom", "UK": "United Kingdom", 
            "IN": "India", "CA": "Canada", "HK": "Hong Kong", "SG": "Singapore", 
            "DE": "Germany", "CH": "Switzerland", "KR": "South Korea", "JP": "Japan", 
            "AU": "Australia", "IL": "Israel", "FR": "France", "NL": "Netherlands"
        },
        "apacCountries": ["CN", "IN", "HK", "SG", "JP", "KR", "AU"],
        "colorScheme": {
            "us": "hsl(221, 83%, 53%)", "cn": "hsl(0, 84%, 60%)",
            "focusCountry": "hsl(36, 96%, 50%)", "primary": "hsl(var(--primary))",
            "secondary": "hsl(var(--secondary-foreground))", "academic": "hsl(221, 83%, 53%)",
            "corporate": "hsl(330, 80%, 60%)", "spotlight": "hsl(48, 96%, 50%)",
            "oral": "hsl(142, 71%, 45%)"
        },
        "dashboardTitle": dashboard_title,
        "dashboardSubtitle": dashboard_subtitle,
        "sections": {
            "summary": {
                "title": "Executive Summary: Impact at a Glance",
                "insights": [
                    f"{country_name}'s ML researchers are making their mark with papers at {conference} {year}, including spotlight and oral presentations that demonstrate the quality of research.",
                    f"Positioned globally, {country_name} contributes to the body of work at {conference} {year}.",
                    "Analysis of first authorship and majority authorship collaborations reveals trends in research leadership and international collaboration.",
                    f"The {country_name}n ML research landscape shows a mix of academic and corporate contributions, with leading institutions demonstrating significant research impact."
                ]
            },
             "context": {
                "title": "Global & APAC Context: India's Standing",
                "subtitle": "Comparing India's research output with global and regional peers.",
                "insights": [
                    "Within the selected APAC group's papers, the focus country contributes papers and authors.",
                    "China dominates volume with papers, while the focus country's spotlight papers demonstrate quality-focused research.",
                    "The focus country ranks among APAC nations in total papers, but demonstrates strong academic-corporate collaboration."
                ]
            },
            "focusCountry": {
                "title": f"{country_name} Deep Dive",
                "subtitle": "Analyzing authorship, collaboration, and institutional contributions.",
                "insights": [
                    f"Researchers from {country_name} are increasingly taking lead authorship roles.",
                    f"A notable portion of papers with {country_name}n authors feature a majority of authors from {country_name}, signaling strong domestic research groups.",
                    "Academic institutions are the primary drivers of paper volume, with corporate labs also making significant high-quality contributions."
                ]
            },
            "institutions": {
                "title": "Institutions: Internal Ecosystem",
                "subtitle": "Analyzing the performance and impact of individual institutions within " + country_name + ".",
                "insights": [
                    "Leading institutions produce the most papers and have a high concentration of authors, often securing spotlight/oral presentations.",
                    "The top few institutions account for a significant percentage of the country's total papers.",
                    "Corporate research labs show strong performance, complementing the output from top academic institutions.",
                    "The institutional landscape highlights the distribution of research talent across various organizations."
                ]
            }
        }
    }
    return config

def main():
    parser = argparse.ArgumentParser(
        description='Generate dashboard data from SQLite database for a specific conference and year.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('db_path', help='Path to the SQLite database file.')
    parser.add_argument('--conference', default='ICLR', help='Conference name (e.g., ICLR, NeurIPS).')
    parser.add_argument('--year', type=int, default=2025, help='Conference year.')
    parser.add_argument('--focus_country', default='IN', 
                        help='Two-letter country code for the focus country (e.g., IN, US, CN).')
    parser.add_argument('--output', default='dashboard_data.json', 
                        help='Path for the output JSON file.')
    parser.add_argument('--institution_mapping', 
                        help='Optional path to the JSON file for institution name mapping (e.g., inverted-index.json). Highly recommended for better accuracy.')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db_path):
        print(f"Error: Database file not found at {args.db_path}")
        return

    if args.institution_mapping and not os.path.exists(args.institution_mapping):
        print(f"Warning: Institution mapping file specified but not found at {args.institution_mapping}. Proceeding without normalization from file.")
            
    print(f"Generating dashboard data for {args.conference} {args.year}, focusing on {args.focus_country}.")
    print(f"Using database: {args.db_path}")
    if args.institution_mapping and os.path.exists(args.institution_mapping): # Check again if it exists before printing
        print(f"Using institution mapping: {args.institution_mapping}")
    else:
        print("No institution mapping file provided or file not found. Institution names will be based on raw data and basic cleaning. Oral/spotlight data might be affected if 'accept_type' column is also missing.")

    dashboard_data = generate_dashboard_data(
        args.db_path, 
        args.conference, 
        args.year, 
        args.focus_country,
        args.institution_mapping
    )
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        print(f"Dashboard data successfully written to {args.output}")
    except IOError as e:
        print(f"Error writing dashboard data to {args.output}: {e}")
    except TypeError as e:
        print(f"Error serializing dashboard data to JSON: {e}. This might be due to non-serializable data types.")

if __name__ == "__main__":
    main()
