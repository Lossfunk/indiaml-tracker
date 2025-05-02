import pandas as pd
import numpy as np
import sqlite3
import json
import pycountry
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate conference analytics with focus on Indian contributions')
    parser.add_argument('--db', type=str, required=True, help='Path to the SQLite database file')
    parser.add_argument('--conference', type=str, required=True, help='Conference name (e.g., NeurIPS)')
    parser.add_argument('--year', type=int, required=True, help='Conference year')
    parser.add_argument('--track', type=str, default='', help='Conference track (default: all tracks)')
    return parser.parse_args()

# Constants
INDIA_ISO_CODE = "IN"  # 2-letter ISO code for India

# Function to convert ISO codes to full country names
def iso_to_country_name(iso_code):
    try:
        country = pycountry.countries.get(alpha_2=iso_code)
        return country.name if country else iso_code
    except:
        return iso_code

# Function to convert country names to ISO Alpha-3 codes (for map visualization)
def country_to_iso3(iso_code):
    try:
        country = pycountry.countries.get(alpha_2=iso_code)
        return country.alpha_3 if country else None
    except:
        return None

def get_global_paper_analytics(conn, conf, year, track):
    """Get papers by country - count papers where at least one author is from each country"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        WITH paper_countries AS (
            SELECT p.id, pa.affiliation_country
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            AND pa.affiliation_country != 'UNK'
            GROUP BY p.id, pa.affiliation_country
        )
        SELECT affiliation_country, COUNT(DISTINCT id) as paper_count 
        FROM paper_countries
        GROUP BY affiliation_country
        ORDER BY paper_count DESC
    """
    paper_counts = pd.read_sql_query(query, conn)
    
    # Add ISO-3 codes and full country names
    paper_counts['iso_code'] = paper_counts['affiliation_country'].apply(country_to_iso3)
    paper_counts['country_name'] = paper_counts['affiliation_country'].apply(iso_to_country_name)
    
    return paper_counts

def get_global_author_analytics(conn, conf, year, track):
    """Count distinct authors by country"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND pa.affiliation_country != 'UNK' AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        SELECT pa.affiliation_country, COUNT(DISTINCT pa.author_id) as author_count 
        FROM paper_authors pa
        JOIN papers p ON pa.paper_id = p.id
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        {where_clause}
        GROUP BY pa.affiliation_country
        ORDER BY author_count DESC
    """
    author_counts = pd.read_sql_query(query, conn)
    
    # Add ISO-3 codes and full country names
    author_counts['iso_code'] = author_counts['affiliation_country'].apply(country_to_iso3)
    author_counts['country_name'] = author_counts['affiliation_country'].apply(iso_to_country_name)
    
    return author_counts

def get_first_author_countries(conn, conf, year, track):
    """Count papers where the first author (position=0) is from each country"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND pa.affiliation_country != 'UNK' AND pa.position = 0 AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        SELECT pa.affiliation_country, COUNT(DISTINCT p.id) as paper_count
        FROM papers p
        JOIN paper_authors pa ON p.id = pa.paper_id
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        {where_clause}
        GROUP BY pa.affiliation_country
        ORDER BY paper_count DESC
    """
    df = pd.read_sql_query(query, conn)
    df['iso_code'] = df['affiliation_country'].apply(country_to_iso3)
    df['country_name'] = df['affiliation_country'].apply(iso_to_country_name)
    return df

def get_majority_author_countries(conn, conf, year, track):
    """Get countries where majority of authors on papers are from that country"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"

    query = f"""
        WITH paper_country_stats AS (
            SELECT 
                p.id,
                pa.affiliation_country,
                COUNT(DISTINCT pa.author_id) as country_authors,
                (SELECT COUNT(DISTINCT author_id) FROM paper_authors WHERE paper_id = p.id) as total_authors
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            AND pa.affiliation_country != 'UNK'
            GROUP BY p.id, pa.affiliation_country
        )
        SELECT 
            affiliation_country, 
            COUNT(DISTINCT id) as paper_count
        FROM paper_country_stats
        WHERE country_authors > total_authors/2
        GROUP BY affiliation_country
        ORDER BY paper_count DESC
    """
    df = pd.read_sql_query(query, conn)
    df['iso_code'] = df['affiliation_country'].apply(country_to_iso3)
    df['country_name'] = df['affiliation_country'].apply(iso_to_country_name)
    return df

def get_papers_with_indian_authors(conn, conf, year, track):
    """Get papers with at least one Indian author"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        WITH paper_stats AS (
            SELECT 
                p.id,
                p.title,
                COUNT(DISTINCT pa.author_id) as total_authors,
                SUM(CASE WHEN pa.affiliation_country = '{INDIA_ISO_CODE}' THEN 1 ELSE 0 END) as indian_authors
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            GROUP BY p.id, p.title
        )
        SELECT id, title, total_authors, indian_authors
        FROM paper_stats
        WHERE indian_authors > 0
        ORDER BY indian_authors DESC, total_authors
    """
    return pd.read_sql_query(query, conn)

def get_papers_with_majority_indian_authors(conn, conf, year, track):
    """Get papers where majority of authors are from India"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        WITH paper_stats AS (
            SELECT 
                p.id,
                p.title,
                COUNT(DISTINCT pa.author_id) as total_authors,
                SUM(CASE WHEN pa.affiliation_country = '{INDIA_ISO_CODE}' THEN 1 ELSE 0 END) as indian_authors
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            GROUP BY p.id, p.title
        )
        SELECT id, title, total_authors, indian_authors
        FROM paper_stats
        WHERE indian_authors > total_authors / 2
        ORDER BY indian_authors DESC, total_authors
    """
    return pd.read_sql_query(query, conn)

def get_papers_with_first_indian_author(conn, conf, year, track):
    """Get papers where first author is from India"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND pa.affiliation_country = '{INDIA_ISO_CODE}' AND pa.position = 0 AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        SELECT p.id, p.title, a.full_name as first_author, pa.affiliation_name
        FROM papers p
        JOIN paper_authors pa ON p.id = pa.paper_id
        JOIN authors a ON pa.author_id = a.id
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        {where_clause}
        ORDER BY p.title
    """
    return pd.read_sql_query(query, conn)

def get_top_indian_institutions(conn, conf, year, track):
    """Get top Indian institutions by paper count"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND pa.affiliation_country = '{INDIA_ISO_CODE}' AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        WITH institutional_papers AS (
            SELECT p.id, pa.affiliation_name
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            AND pa.affiliation_name IS NOT NULL
            AND pa.affiliation_name != ''
            GROUP BY p.id, pa.affiliation_name
        )
        SELECT affiliation_name, COUNT(DISTINCT id) as paper_count
        FROM institutional_papers
        GROUP BY affiliation_name
        ORDER BY paper_count DESC
    """
    return pd.read_sql_query(query, conn)

def get_papers_by_indian_institution(conn, conf, year, track):
    """Get papers by Indian institution (inverted index)"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND pa.affiliation_country = '{INDIA_ISO_CODE}' AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        WITH institutional_papers AS (
            SELECT p.id, p.title, pa.affiliation_name
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            {where_clause}
            AND pa.affiliation_name IS NOT NULL
            AND pa.affiliation_name != ''
            GROUP BY p.id, p.title, pa.affiliation_name
        )
        SELECT affiliation_name, id, title
        FROM institutional_papers
        ORDER BY affiliation_name, title
    """
    df = pd.read_sql_query(query, conn)
    
    # Create inverted index with affiliation name as key and papers as values
    institution_papers = {}
    for _, row in df.iterrows():
        institution = row['affiliation_name']
        paper = {'id': row['id'], 'title': row['title']}
        
        if institution not in institution_papers:
            institution_papers[institution] = []
        
        # Check if this paper is already in the list to avoid duplicates
        if not any(p['id'] == paper['id'] for p in institution_papers[institution]):
            institution_papers[institution].append(paper)
    
    # Convert to format with count and papers list
    result = []
    for institution, papers in institution_papers.items():
        result.append({
            'institution': institution,
            'paper_count': len(papers),
            'papers': papers
        })
    
    # Sort by paper count descending
    result.sort(key=lambda x: x['paper_count'], reverse=True)
    
    return result

def get_total_papers(conn, conf, year, track):
    """Get total number of accepted papers"""
    # Build WHERE clause
    where_clause = f"WHERE vi.conference = '{conf}' AND vi.year = {year} AND p.status = 'accepted'"
    if track:
        where_clause += f" AND vi.track = '{track}'"
    
    query = f"""
        SELECT COUNT(DISTINCT p.id) as total_papers
        FROM papers p
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        {where_clause}
    """
    result = pd.read_sql_query(query, conn)
    return result['total_papers'].iloc[0] if not result.empty else 0

def verify_country_codes(conn):
    """Verify the country codes in the database"""
    query = "SELECT DISTINCT affiliation_country FROM paper_authors ORDER BY affiliation_country"
    countries = pd.read_sql_query(query, conn)
    
    print("\nCountry codes in database:")
    for idx, row in countries.head(20).iterrows():
        code = row['affiliation_country']
        name = iso_to_country_name(code)
        print(f"  {code}: {name}")
    
    if len(countries) > 20:
        print(f"  ... and {len(countries) - 20} more")
    
    # Check specifically for India
    if INDIA_ISO_CODE in countries['affiliation_country'].values:
        print(f"\nFound '{INDIA_ISO_CODE}' (India) in the database.")
    else:
        print(f"\nWARNING: '{INDIA_ISO_CODE}' (India) not found in country codes!")
        # Check for similar codes
        similar = [c for c in countries['affiliation_country'].values if 'IN' in c or 'IND' in c]
        if similar:
            print(f"Similar codes found: {similar}")

def generate_conference_analytics(db_path, conf, year, track):
    """Generate all analytics for a conference and save to JSON"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Verify country codes
        verify_country_codes(conn)
        
        # Get total accepted papers
        total_papers = get_total_papers(conn, conf, year, track)
        
        # Global analytics
        global_paper_analytics = get_global_paper_analytics(conn, conf, year, track)
        global_author_analytics = get_global_author_analytics(conn, conf, year, track)
        first_author_countries = get_first_author_countries(conn, conf, year, track)
        majority_author_countries = get_majority_author_countries(conn, conf, year, track)
        
        # India-specific analytics
        indian_author_papers = get_papers_with_indian_authors(conn, conf, year, track)
        majority_indian_papers = get_papers_with_majority_indian_authors(conn, conf, year, track)
        first_indian_author_papers = get_papers_with_first_indian_author(conn, conf, year, track)
        top_indian_institutions = get_top_indian_institutions(conn, conf, year, track)
        indian_institution_papers = get_papers_by_indian_institution(conn, conf, year, track)
        
        # Create analytics object
        analytics = {
            'conference': conf,
            'year': year,
            'track': track if track else 'all',
            'total_accepted_papers': int(total_papers),
            'global': {
                'paper_analytics': {
                    'countries': global_paper_analytics.to_dict(orient='records')
                },
                'author_analytics': {
                    'at_least_one_author': {
                        'countries': global_paper_analytics.to_dict(orient='records')
                    },
                    'authors_by_country': {
                        'countries': global_author_analytics.to_dict(orient='records')
                    },
                    'first_author': {
                        'countries': first_author_countries.to_dict(orient='records')
                    },
                    'majority_authors': {
                        'countries': majority_author_countries.to_dict(orient='records')
                    }
                }
            },
            'india': {
                'at_least_one_indian_author': {
                    'count': len(indian_author_papers),
                    'papers': indian_author_papers.to_dict(orient='records')
                },
                'majority_indian_authors': {
                    'count': len(majority_indian_papers),
                    'papers': majority_indian_papers.to_dict(orient='records')
                },
                'first_indian_author': {
                    'count': len(first_indian_author_papers),
                    'papers': first_indian_author_papers.to_dict(orient='records')
                },
                'institutions': {
                    'summary': top_indian_institutions.to_dict(orient='records'),
                    'detailed': indian_institution_papers
                }
            }
        }
        
        # Generate output filename
        track_str = f"-{track}" if track else ""
        output_file = f'{conf.lower()}-{year}{track_str}-analytics.json'
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        print(f"Analytics generated and saved to {output_file}")
        
        # Summary statistics
        print(f"\nSummary for {conf} {year}{' ' + track if track else ''}:")
        print(f"Total accepted papers: {total_papers}")
        print(f"Total countries with papers: {len(global_paper_analytics)}")
        
        if not global_paper_analytics.empty:
            print(f"Top 5 countries by paper count:")
            for _, row in global_paper_analytics.head(5).iterrows():
                country_name = row['country_name'] if 'country_name' in row else row['affiliation_country']
                print(f"  {row['affiliation_country']} ({country_name}): {row['paper_count']} papers")
        
        print(f"\nIndia-specific statistics:")
        print(f"  Papers with at least one Indian author: {len(indian_author_papers)}")
        print(f"  Papers with majority Indian authors: {len(majority_indian_papers)}")
        print(f"  Papers with first Indian author: {len(first_indian_author_papers)}")
        print(f"  Number of unique Indian institutions: {len(top_indian_institutions)}")
        
        if not top_indian_institutions.empty:
            print("\nTop 10 Indian institutions by paper count:")
            for _, row in top_indian_institutions.head(10).iterrows():
                print(f"  {row['affiliation_name']}: {row['paper_count']} papers")
        
        # Close database connection
        conn.close()
        
    except Exception as e:
        print(f"Error generating analytics: {str(e)}")
        raise

def main():
    args = parse_arguments()
    generate_conference_analytics(args.db, args.conference, args.year, args.track)

if __name__ == "__main__":
    main()