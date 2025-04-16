import openreview
import json
import time
import logging
import os

# --- Configuration ---
IO_DIR = "../ui/indiaml-tracker/public/tracker"  # Input/Output Directory
INDEX_FILENAME = "index.json"
VALID_VENUES = {"oral", "poster", "spotlight"}

# Configure logging
# Use INFO for general progress, DEBUG for detailed API call info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Function to Fetch and Process Venue (Now takes client) ---
def get_and_process_venue(client, paper_data):
    """
    Fetches venue for a paper ID using the provided client.
    Returns the processed venue type if it's one of the VALID_VENUES.
    Handles potential errors.
    Returns (paper_id, venue_type or None, error_message or None)
    """
    paper_id = paper_data.get("paper_id")
    if not paper_id:
        return None, None, "Missing paper_id in source data"

    # Check if venue already exists and is valid
    current_venue = paper_data.get("venue")
    if isinstance(current_venue, str) and current_venue.lower() in VALID_VENUES:
        # logging.debug(f"Skipping {paper_id}: Already has valid venue '{current_venue}'.")
        return paper_id, None, "Already processed"

    # Ensure client is valid
    if not client:
         logging.error(f"OpenReview client object is invalid for {paper_id}.")
         return paper_id, None, "OpenReview client invalid"

    try:
        # logging.debug(f"Fetching venue for {paper_id}...")
        # Add a small delay *before* each API call to be polite
        time.sleep(0.5) # 500ms delay
        note = client.get_note(paper_id)

        # Defensive checks for note structure
        if note and note.content and "venue" in note.content and "value" in note.content["venue"]:
            raw_venue = note.content["venue"]["value"]
            if raw_venue and isinstance(raw_venue, str):
                 venue_lower = raw_venue.lower()
                 for v_type in VALID_VENUES:
                     if f' {v_type} ' in f' {venue_lower} ' or \
                        venue_lower.startswith(f'{v_type} ') or \
                        venue_lower.endswith(f' {v_type}') or \
                        venue_lower == v_type:
                         # logging.debug(f"Found valid venue '{v_type}' for {paper_id} from raw '{raw_venue}'")
                         return paper_id, v_type, None
                 # logging.debug(f"Venue '{raw_venue}' for {paper_id} is not one of {VALID_VENUES}.")
                 return paper_id, None, "Venue not oral/poster/spotlight"
            else:
                # logging.debug(f"Empty or invalid venue value found for {paper_id}.")
                return paper_id, None, "Empty/invalid venue value"
        else:
            # logging.debug(f"Venue information missing or incomplete in note structure for {paper_id}.")
            return paper_id, None, "Venue structure incomplete"

    except openreview.OpenReviewException as e:
        error_str = str(e).lower()
        if "not found" in error_str:
             # logging.debug(f"Note Not Found for {paper_id}")
             return paper_id, None, "Note Not Found"
        logging.warning(f"OpenReview API error for {paper_id}: {e}")
        return paper_id, None, f"OpenReview API error: {e}"
    except Exception as e:
        logging.warning(f"Unexpected error fetching venue for {paper_id}: {e}")
        return paper_id, None, f"Unexpected error: {e}"


# --- Main Processing Logic for a list of papers (Now takes client, single-threaded) ---
def update_papers_with_venues(client, papers_list):
    """
    Updates a list of paper dictionaries with venue information sequentially.
    Modifies the list in-place. Returns the number of updates made.
    """
    if not isinstance(papers_list, list):
        logging.error("Invalid input: update_papers_with_venues expects a list.")
        return 0

    papers_to_process = []
    # Identify papers needing processing
    for paper in papers_list:
        if not isinstance(paper, dict):
             logging.warning(f"Skipping non-dictionary item in papers list: {paper}")
             continue

        paper_id = paper.get("paper_id")
        if not paper_id:
            logging.warning(f"Skipping paper with missing 'paper_id': {paper.get('paper_title', 'No Title')}")
            continue

        current_venue = paper.get("venue")
        if not (isinstance(current_venue, str) and current_venue.lower() in VALID_VENUES):
            papers_to_process.append(paper) # Add the dictionary reference

    if not papers_to_process:
        logging.info("No papers require venue fetching/update in this list.")
        return 0 # No updates made

    logging.info(f"Found {len(papers_to_process)} papers potentially needing venue fetching. Processing sequentially...")

    update_count = 0
    processed_count = 0
    total_to_process = len(papers_to_process)

    # Process papers one by one
    for paper in papers_to_process:
        processed_count += 1
        paper_id = paper.get("paper_id") # We already checked this exists

        # Optional: Progress update
        if processed_count % 10 == 0 or processed_count == total_to_process:
             logging.info(f"Venue fetch progress: {processed_count}/{total_to_process}")

        p_id, venue_type, error_msg = get_and_process_venue(client, paper)

        if venue_type: # Successfully fetched a valid venue
            paper["venue"] = venue_type
            update_count += 1
            # logging.debug(f"Updated {p_id} with venue: {venue_type}")
        elif error_msg and error_msg not in ["Already processed", "Note Not Found", "Venue not oral/poster/spotlight", "Venue structure incomplete", "Empty/invalid venue value"]:
             # Log more significant errors
             logging.warning(f"Processing {p_id}: {error_msg}")
        # else: skip logging for common non-update cases

    logging.info(f"Finished sequential fetching. Applied updates to {update_count} paper entries.")
    return update_count


# --- Top-Level Function to Orchestrate File Processing (Now takes client) ---
def process_files_from_index(client, base_dir, index_filename):
    """
    Reads an index file, then processes each data file listed within it sequentially.
    """
    index_file_path = os.path.join(base_dir, index_filename)
    logging.info(f"Attempting to read index file: {index_file_path}")

    try:
        with open(index_file_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        logging.info(f"Successfully read index file: {index_file_path}")
    except FileNotFoundError:
        logging.error(f"Index file not found: {index_file_path}")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from index file {index_file_path}: {e}")
        return
    except Exception as e:
        logging.error(f"Error reading index file {index_file_path}: {e}")
        return

    if not isinstance(index_data, list):
         logging.error(f"Index file {index_file_path} does not contain a valid JSON list.")
         return

    total_updates_all_files = 0

    for entry in index_data:
        if not isinstance(entry, dict) or "file" not in entry or "label" not in entry:
            logging.warning(f"Skipping invalid entry in index file: {entry}")
            continue

        data_filename = entry["file"]
        data_filepath = os.path.join(base_dir, data_filename) # Files are in the same directory
        label = entry["label"]
        logging.info(f"--- Processing file for '{label}': {data_filename} ---")

        papers_data = None # Initialize papers_data
        try:
            # Read the existing data
            logging.info(f"Reading data file: {data_filepath}")
            with open(data_filepath, 'r', encoding='utf-8') as f:
                papers_data = json.load(f)

            if not isinstance(papers_data, list):
                 logging.warning(f"Data file {data_filepath} for '{label}' does not contain a list. Skipping.")
                 continue
            logging.info(f"Read {len(papers_data)} paper entries from {data_filepath}")

        except FileNotFoundError:
            logging.warning(f"Data file not found: {data_filepath} for '{label}'. Skipping.")
            continue
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from data file {data_filepath} for '{label}': {e}. Skipping.")
            continue
        except Exception as e:
            logging.error(f"Error reading data file {data_filepath} for '{label}': {e}. Skipping.")
            continue

        # Process the papers from this file
        start_time = time.time()
        # Pass the client to the processing function
        num_updates = update_papers_with_venues(client, papers_data)
        end_time = time.time()
        logging.info(f"Finished venue processing for '{label}'. Updates made: {num_updates}. Time taken: {end_time - start_time:.2f} seconds.")

        # Save the updated data back to the same file ONLY if updates were made
        if num_updates > 0:
            try:
                logging.info(f"Attempting to save updated data back to: {data_filepath}")
                with open(data_filepath, 'w', encoding='utf-8') as f:
                    # Use indent=2 for readability, ensure_ascii=False for potential unicode chars
                    json.dump(papers_data, f, indent=2, ensure_ascii=False)
                logging.info(f"Successfully saved updated data ({num_updates} changes) to: {data_filepath}")
                total_updates_all_files += num_updates
            except Exception as e:
                logging.error(f"Error writing updated data to file {data_filepath} for '{label}': {e}")
        else:
             logging.info(f"No updates made to '{label}', skipping save for {data_filepath}")


        logging.info(f"--- Finished processing for '{label}' ---")

    logging.info(f"Total updates across all files: {total_updates_all_files}")


# --- Main Execution ---
if __name__ == "__main__":
    overall_start_time = time.time()
    logging.info("=== Starting Script (Single-Threaded) ===")

    # Initialize OpenReview client here
    client = None
    try:
        # Use anonymous client. Replace with credentials if needed.
        # client = openreview.Client(baseurl='https://api2.openreview.net', username='YOUR_EMAIL', password='YOUR_PASSWORD')
        client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
        logging.info(f"OpenReview client initialized successfully for {client.baseurl}")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to initialize OpenReview client: {e}")
        logging.error("Script cannot proceed without a client. Exiting.")
        exit(1) # Exit if client initialization fails

    # Pass the initialized client to the main processing function
    process_files_from_index(client, IO_DIR, INDEX_FILENAME)

    overall_end_time = time.time()
    logging.info(f"=== All processing complete. Total time: {overall_end_time - overall_start_time:.2f} seconds ===")

