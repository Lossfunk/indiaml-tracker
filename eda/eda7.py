import pandas as pd
import os
import sys
import ast

def extract_venue_and_year(filename):
    base = os.path.basename(filename)
    name, _ = os.path.splitext(base)
    venue, year = name.split('-')
    return venue.upper(), int(year)

def parse_author_list(author_str):
    try:
        return ast.literal_eval(author_str)
    except Exception as e:
        print(f"Error parsing author list: {e}")
        return []

def extract_first_author_name(author_str):
    authors = parse_author_list(author_str)
    return authors[0]['name'] if authors else 'Unknown'

def process_csv(csv_path):
    df = pd.read_csv(csv_path)

    # Filter: only oral or spotlight & top author from India
    valid_accept_types = ['oral', 'spotlight', 'poster']
    df = df[df['accept_type'].isin(valid_accept_types)]
    df = df[df['top_author_from_india'] == True]

    # Sort by accept_type
    accept_priority = {'oral': 0, 'spotlight': 1, 'poster': 2}
    df['accept_rank'] = df['accept_type'].map(accept_priority)
    df = df.sort_values(by='accept_rank')

    # Extract venue and year from filename
    df[['venue', 'year']] = df['filename'].apply(
        lambda fn: pd.Series(extract_venue_and_year(fn))
    )

    # Extract first author
    df['first_author'] = df['author_list'].apply(extract_first_author_name)

    # Final selected columns
    df_result = df[['accept_type', 'venue', 'year', 'paper_id', 'pdf_url', 'paper_title', 'first_author']]
    
    return df_result

if __name__ == "__main__":
    csv_path = sys.argv[1]
    df_final = process_csv(csv_path)
    df_final.to_csv("filtered.csv", index=False)
