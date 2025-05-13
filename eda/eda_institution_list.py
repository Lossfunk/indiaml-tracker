import sqlite3
import argparse

def extract_country_affiliations(db_path, focus_country, output_file):
    """
    Extract all unique institution names for a specific country and 
    save them to a newline-delimited file.
    
    Args:
        db_path (str): Path to the SQLite database
        focus_country (str): Country code to focus on (e.g., "IN" for India)
        output_file (str): Path to save the output file
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    cursor = conn.cursor()
    
    # Query to get all unique affiliation names for the focus country
    query = """
    SELECT DISTINCT 
        pa.affiliation_name
    FROM 
        paper_authors pa
    JOIN
        papers p ON pa.paper_id = p.id
    WHERE 
        pa.affiliation_country = ? 
        AND p.status = 'accepted'
        AND pa.affiliation_name IS NOT NULL
        AND pa.affiliation_name != ''
    ORDER BY 
        pa.affiliation_name
    """
    
    cursor.execute(query, (focus_country.upper(),))
    affiliations = [row['affiliation_name'] for row in cursor.fetchall()]
    
    # Write the affiliations to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        for affiliation in affiliations:
            f.write(f"{affiliation}\n")
    
    print(f"Found {len(affiliations)} unique affiliations for country code {focus_country}")
    print(f"Affiliations saved to {output_file}")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Extract unique affiliations for a country')
    parser.add_argument('--db_path', help='Path to the SQLite database')
    parser.add_argument('--country_code', help='Country code to focus on (e.g., IN for India)')
    parser.add_argument('--output', '-o', default='affiliations.txt', 
                        help='Output file path (default: affiliations.txt)')
    
    args = parser.parse_args()
    extract_country_affiliations(args.db_path, args.country_code, args.output)

if __name__ == "__main__":
    main()