import pandas as pd
import sqlite3
import pycountry
import json
import os

OUTPUT_DIR = "../ui/indiaml-tracker/public/tracker"


def connect_to_database(db_path="venues.db"):
    """Connect to the SQLite database"""
    return sqlite3.connect(db_path)

def country_to_iso(country_name):
    """Convert country names to ISO Alpha-3 codes"""
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        return country.alpha_3
    except:
        return None

def process_papers(ddf, cc='IN'):
    """Process paper data and extract information about authors from a specific country"""
    filtered_papers = []
    
    # Group by paper_id to process each paper individually
    grouped = ddf.groupby('paper_id')
    
    for paper_id, group in grouped:
        paper_title = group['title'].iloc[0]
        pdf_url = group['pdf_url'].iloc[0]
        paper_id = group['paper_id'].iloc[0]
        authors = group[['full_name', 'openreview_id', 'affiliation_name', 'affiliation_domain', 'affiliation_country', 'position']].drop_duplicates()
        
        # Filter authors from specified country
        authors_from_country = authors[authors['affiliation_country'] == cc]
        
        if not authors_from_country.empty:
            # Create author list
            author_list = authors.apply(lambda row: {
                'name': row['full_name'],
                'openreview_id': row['openreview_id'],
                'affiliation_name': row['affiliation_name'],
                'affiliation_domain': row['affiliation_domain'],
                'affiliation_country': row['affiliation_country']
            }, axis=1).tolist()
            
            # Check if top author is from specified country
            top_author_from_country = (authors.sort_values(by='position').iloc[0]['affiliation_country'] == cc)
            
            # Check if majority authors are from specified country
            majority_authors_from_country = len(authors_from_country) / len(authors) >= 0.5
            
            filtered_papers.append({
                'paper_title': paper_title,
                'paper_id': paper_id,
                'pdf_url': pdf_url,
                'author_list': author_list,
                'top_author_from_india': top_author_from_country,
                'majority_authors_from_india': majority_authors_from_country
            })
    
    return pd.DataFrame(filtered_papers)

def get_venue_years(conn):
    """Get all unique venue-year combinations from the database"""
    query = """
    SELECT DISTINCT conference, year 
    FROM venue_infos 
    ORDER BY conference, year
    """
    return pd.read_sql_query(query, conn)

def process_venue_year(conn, conference, year, country_code='IN', output_dir=OUTPUT_DIR):
    """Process papers for a specific venue and year"""
    print(f"Processing {conference}-{year}...")
    
    query = f"""
    SELECT title, paper_id, pdf_url, full_name, position, openreview_id, 
           affiliation_name, affiliation_domain, affiliation_country 
    FROM (
        SELECT * 
        FROM paper_authors 
        JOIN authors ON author_id = authors.id 
        JOIN papers ON paper_id = papers.id 
        JOIN venue_infos ON papers.venue_info_id = venue_infos.id
    )
    WHERE conference = '{conference}'
    AND year = '{year}'
    AND track = 'Conference'
    AND status = 'accepted';
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print(f"No data found for {conference}-{year}")
        return None
    
    # Add prefix to pdf_url
    df["pdf_url"] = "https://openreview.net" + df["pdf_url"]
    
    # Process papers
    processed_df = process_papers(df, country_code)
    
    if processed_df.empty:
        print(f"No papers with authors from {country_code} found for {conference}-{year}")
        return None
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON
    filename = f"{conference.lower()}-{year}.json"
    output_file = os.path.join(output_dir, filename)
    processed_df.to_json(output_file, orient="records")
    print(f"Generated {output_file}")
    
    return {
        "label": f"{conference} {year}",
        "file": filename
    }

def update_index_file(processed_venues, output_dir=OUTPUT_DIR):
    """Update or create the index.json file"""
    index_file = os.path.join(output_dir, 'index.json')
    index_data = []
    
    # Check if index file already exists
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            print(f"Loaded existing index file with {len(index_data)} entries")
        except json.JSONDecodeError:
            print("Error reading index file. Creating a new one.")
            index_data = []
    
    # Get existing file entries
    existing_files = {entry['file'] for entry in index_data}
    
    # Add new entries
    for venue in processed_venues:
        if venue is not None and venue['file'] not in existing_files:
            index_data.append(venue)
            print(f"Added {venue['label']} to index")
    
    # Write updated index file
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"Updated index file with {len(index_data)} entries")

def main():
    # Connect to database
    conn = connect_to_database()
    output_dir = OUTPUT_DIR
    
    try:
        # Get all venue-year combinations
        venue_years = get_venue_years(conn)
        
        if venue_years.empty:
            print("No venue-year combinations found in the database")
            return
        
        print(f"Found {len(venue_years)} venue-year combinations")
        
        # Process each venue-year combination
        processed_venues = []
        for _, row in venue_years.iterrows():
            conference = row['conference']
            year = row['year']
            venue_info = process_venue_year(conn, conference, year, output_dir=output_dir)
            if venue_info:
                processed_venues.append(venue_info)
        
        # Update the index file
        update_index_file(processed_venues, output_dir=output_dir)
        
        print("All JSON files generated successfully!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()