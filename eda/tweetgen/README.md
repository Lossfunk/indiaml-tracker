# Tweet Thread Generator for Research Papers

This tool processes research papers from JSON files, finds Twitter profiles for authors using the Exa API, generates tweet threads, and creates visual cards for each paper.

## Features

- 🔍 **Author Twitter Discovery**: Uses Exa API to find Twitter/X profiles for paper authors
- 🎨 **Visual Card Generation**: Creates beautiful paper cards using the existing card.py functionality
- 🧵 **Tweet Thread Creation**: Generates engaging 3-tweet threads for each paper
- 📄 **Markdown Output**: Compiles all tweets into a single markdown file
- ⚡ **Batch Processing**: Handles multiple papers efficiently with rate limiting

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get an Exa API key from [https://exa.ai](https://exa.ai)

## Usage

### Basic Usage

```bash
python tweet_generator.py ui/indiaml-tracker/public/tracker/icml-2025.json --exa-api-key YOUR_EXA_API_KEY
```

### Advanced Usage

```bash
python tweet_generator.py ui/indiaml-tracker/public/tracker/icml-2025.json \
  --exa-api-key YOUR_EXA_API_KEY \
  --output-dir ./icml_2025_tweets/ \
  --output-file icml_2025_threads.md \
  --limit 5
```

### Command Line Arguments

- `input_json`: Path to the JSON file containing paper data
- `--exa-api-key`: Your Exa API key (required)
- `--output-dir`: Directory for generated card images (default: `tweet_output/`)
- `--output-file`: Output markdown file name (default: `tweets.md`)
- `--limit`: Limit number of papers to process (useful for testing)

## Input Format

The script expects a JSON file with the following structure (as used in the IndiaML tracker):

```json
[
  {
    "paper_title": "Paper Title Here",
    "paper_id": "unique_id",
    "pdf_url": "https://openreview.net/pdf/...",
    "author_list": [
      {
        "name": "Author Name",
        "openreview_id": "~Author_Name1",
        "affiliation_name": "University Name",
        "affiliation_domain": "university.edu",
        "affiliation_country": "US"
      }
    ],
    "paper_content": "Brief description of the paper..."
  }
]
```

## Output

The script generates:

1. **Card Images**: PNG files for each paper in the output directory
2. **Markdown File**: Contains all tweet threads with metadata

### Example Tweet Thread Format

```markdown
## Paper 1: Example Paper Title

**Card Image:** `paper_001_example_paper_title.png`

**Twitter Profiles Found:**
- John Doe: @johndoe
- Jane Smith: @janesmith

**Tweet Thread:**

## Example Paper Title

**Tweet 1/3** 🧵
📄 New paper at #ICML2025: "Example Paper Title"

This paper investigates...

🧵 Thread below 👇

**Tweet 2/3**
👥 Authors: @johndoe, @janesmith

🔬 This work explores...

**Tweet 3/3**
📊 Key insights from this research:
...

📖 Read the full paper: https://openreview.net/pdf/...
🖼️ Paper card: paper_001_example_paper_title.png

#MachineLearning #AI #Research #IndiaML
```

## Features in Detail

### Twitter Profile Discovery

- Uses Exa API's neural search to find Twitter/X profiles
- Searches with author name + affiliation for better accuracy
- Extracts usernames from found URLs
- Includes rate limiting to respect API limits

### Card Generation

- Reuses the existing `card.py` functionality
- Generates SVG cards and converts to PNG
- Includes author flags based on country codes
- Handles up to 8 authors per card

### Tweet Thread Structure

- **Tweet 1**: Paper title, brief description, thread indicator
- **Tweet 2**: Author mentions, research focus
- **Tweet 3**: Key insights, paper link, card reference, hashtags

## Rate Limiting

The script includes a 1-second delay between Twitter profile searches to be respectful to the Exa API. For large datasets, consider running in batches.

## Error Handling

- Graceful handling of API failures
- Continues processing even if some Twitter profiles aren't found
- Validates input file format
- Provides detailed progress logging

## Testing

For testing with a subset of papers:

```bash
python tweet_generator.py ui/indiaml-tracker/public/tracker/icml-2025.json \
  --exa-api-key YOUR_EXA_API_KEY \
  --limit 3
```

This will process only the first 3 papers.

## Dependencies

- `requests`: For Exa API calls
- `pillow`: Image processing
- `cairosvg`: SVG to PNG conversion
- `reportlab`: PDF generation (inherited from card.py)

## Notes

- The script handles missing author names by extracting from OpenReview IDs
- Country codes are mapped to emoji flags for card generation
- Tweet threads are designed to fit Twitter's character limits
- All generated content is saved in UTF-8 encoding
