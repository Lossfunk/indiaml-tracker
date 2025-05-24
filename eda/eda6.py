import orjson as json
from openreview.api import OpenReviewClient
import csv
import sys

def process_papers(filenames, output_csv):
    client = OpenReviewClient(baseurl="https://api2.openreview.net")
    all_paper_data = []

    for filename in filenames:
        try:
            with open(filename, 'r') as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            print(f"Error: File not found: {filename}")
            continue
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from file: {filename}")
            continue

        for item in data:
            paper_info = {}
            paper_info['filename'] = filename
            paper_info.update(item)  # Add all available info from the JSON

            pid = item.get("paper_id")
            if pid:
                try:
                    note = client.get_note(pid)
                    if note and note.content and note.content.get("venue") and note.content["venue"].get("value"):
                        venue_parts = note.content["venue"]["value"].lower().split()
                        if venue_parts:
                            accept_type = venue_parts[-1]
                            paper_info['accept_type'] = accept_type
                        else:
                            paper_info['accept_type'] = ''
                    else:
                        paper_info['accept_type'] = ''
                except Exception as e:
                    print(f"Error fetching note for paper ID {pid} from file {filename}: {e}")
                    paper_info['accept_type'] = ''
            else:
                paper_info['accept_type'] = ''

            all_paper_data.append(paper_info)

    if all_paper_data:
        # Determine all unique fields to use as CSV headers
        fieldnames = set()
        for paper in all_paper_data:
            fieldnames.update(paper.keys())
        fieldnames = sorted(list(fieldnames)) # Sort for consistent order

        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for paper in all_paper_data:
                writer.writerow(paper)
        print(f"Successfully wrote data to {output_csv}")
    else:
        print("No data to write to CSV.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <json_file1> [json_file2 ...] <output.csv>")
        sys.exit(1)

    input_files = sys.argv[1:-1]
    output_file = sys.argv[-1]

    process_papers(input_files, output_file)

# Sample usage
# python eda/eda6.py ui/indiaml-tracker/public/tracker/iclr-2025.json ui/indiaml-tracker/public/tracker/icml-2024.json ui/indiaml-tracker/public/tracker/neurips-2024.json ui/indiaml-tracker/public/tracker/iclr-2024.json output.csv