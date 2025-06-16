from indiaml.models.conference_schema import EventResponse
from functional import seq
from typing import Set

def filter_posters(file_path: str) -> int:
    """
    Loads event data, filters for posters using a functional approach,
    and returns the count.

    Args:
        file_path: The path to the input JSON file.

    Returns:
        The total count of events with eventtype 'Poster'.
    """
    print(f"Loading data from '{file_path}'...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate and parse the data using the Pydantic model
    event_data = EventResponse.model_validate(data)
    
    # Using pyfunctional, we create a sequence from the results list.
    # We then apply a filter and get the length of the resulting sequence.
    # This is more declarative and reads like a data processing pipeline.
    poster_count = (
        seq(event_data.results)
        .filter(lambda event: event.eventtype == "Poster")
        .len()
    )
            
    return poster_count



def analyze_event_data(file_path: str) -> (int, Set[str]):
    """
    Loads and analyzes event data from a JSON file.

    Args:
        file_path: The path to the input JSON file.

    Returns:
        A tuple containing:
        - The total count of events with eventtype 'Poster'.
        - A set of unique eventtype strings for all non-poster events.
    """
    print(f"Loading data from '{file_path}'...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate and parse the data using the Pydantic model
    event_data = EventResponse.model_validate(data)
    
    # Create a sequence from the results for efficient processing
    results_seq = seq(event_data.results)
    
    # 1. Count the number of posters
    poster_count = (
        results_seq
        .filter(lambda event: event.eventtype == "Poster")
        .len()
    )

    oral_count = (
        results_seq
        .filter(lambda event: event.eventtype == "Oral")
        .len()
    )
    
            
    return poster_count, oral_count, event_data




if __name__ == "__main__":
    import json
    from typing import List, Optional
    from pydantic import BaseModel, Field

    
    import sys
    # if len(sys.argv) != 2:
    #     print("Usage: python eda-icml-2025.py <path_to_json_file>")
    #     sys.exit(1)

    file_path = sys.argv[1]
    # count = filter_posters(file_path)
    # print(f"Total number of posters: {count}")

    final_poster_count, oral_count, evt = analyze_event_data(file_path)    
    print("\n--- Event Analysis Results ---")
    print(f"Total items in original file: {evt.count}")
    print(f"Count of items after filtering for 'Poster': {final_poster_count}")
    print(f"Count of items after filtering for 'Oral': {oral_count}")
    print(f"Oral + Poster': {final_poster_count + oral_count}")
