import json
import os
import argparse  # Import argparse
from openreview.api import OpenReviewClient

def process_papers(client, input_filename, output_filename):
    """
    Processes papers from an input JSON file, fetches author profiles from OpenReview,
    and saves the results to an output JSON file.

    Args:
        client: An initialized OpenReviewClient instance.
        input_filename (str): Path to the input JSON file.
        output_filename (str): Path to the output JSON file.
    """
    # Load input JSON data
    try:
        with open(input_filename, 'r') as f:
            papers = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from input file '{input_filename}'.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the input file: {e}")
        return

    output = []
    print(f"Processing papers from '{input_filename}'...")

    # Filter papers with Indian first author
    for paper in papers:
        # Check if 'top_author_from_india' key exists and is True
        if paper.get('top_author_from_india') is True: # Explicitly check for True
            entry = {
                'paper_title': paper.get('paper_title', 'N/A'), # Use .get for safety
                'pdf_url': paper.get('pdf_url', 'N/A'),
                'paper_summary': paper.get('paper_content', 'N/A'),
                'authors': []
            }
            # Fetch profiles for each author
            for author in paper.get('author_list', []):
                openreview_id = author.get('openreview_id')
                if not openreview_id:
                    continue # Skip author if no openreview_id

                links = {}
                try:
                    # Attempt to fetch the profile
                    profile = client.get_profile(openreview_id)
                    content = getattr(profile, 'content', {}) or {} # Ensure content is a dict

                    # Known social link fields in API2
                    for field in ['linkedin', 'github', 'orcid', 'gscholar', 'homepage']:
                        value = content.get(field)
                        if value: # Only add if value exists and is not empty
                            links[field] = value
                except Exception as e:
                    # Profile may not exist, access denied, or other API error
                    # print(f"Warning: Could not fetch profile for {openreview_id}. Error: {e}") # Optional: Log warning
                    links = {} # Reset links on error
                    print(e)

                entry['authors'].append({
                    'name': author.get('name', 'N/A'), # Use .get for safety
                    'openreview_id': openreview_id,
                    'links': links
                })

            # Only add the entry if it has authors processed
            if entry['authors']:
                 output.append(entry)
        # else: # Optional: Log skipped papers
            # print(f"Skipping paper '{paper.get('paper_title', 'N/A')}' - 'top_author_from_india' is not True.")


    # Save the output JSON
    try:
        with open(output_filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Successfully processed {len(output)} papers. Output saved to '{output_filename}'.")
    except IOError as e:
        print(f"Error: Could not write to output file '{output_filename}'. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing the output file: {e}")


def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description='Fetch OpenReview author profiles for papers with Indian first authors.')
    parser.add_argument(
        '--input-file',
        required=True,
        help='Path to the input JSON file containing paper data.'
    )
    parser.add_argument(
        '--output-file',
        default='output_profiles.json', # Provide a default output filename
        help='Path to save the output JSON file with author profiles (default: output_profiles.json).'
    )
    # Optional: Add arguments for OpenReview credentials if needed later
    # parser.add_argument('--openreview-username', help='OpenReview username.')
    # parser.add_argument('--openreview-password', help='OpenReview password.')

    args = parser.parse_args()
    # --- End Argument Parsing ---

    # Initialize OpenReview API2 client
    # Use environment variables for base URL, potentially add user/pass later if needed
    client = OpenReviewClient(
        baseurl=os.environ.get('OPENREVIEW_BASEURL', 'https://api2.openreview.net'),
        # username=args.openreview_username or os.environ.get('OPENREVIEW_USERNAME'), # Example if using args
        # password=args.openreview_password or os.environ.get('OPENREVIEW_PASSWORD')
    )

    # Call the processing function with parsed arguments
    process_papers(client, args.input_file, args.output_file)

if __name__ == '__main__':
    main()
