import os
import json
import tempfile
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
import requests
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from sqlalchemy import create_engine
from ..models.models import Base, VenueInfo, Paper, Author, PaperAuthor
from ..models.dto import AuthorDTO, PaperDTO
import pymupdf4llm
import openai
import logging
import re
import dotenv
dotenv.load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Database setup
db_path = "sqlite:///venues.db"  # Replace with your actual SQLite file path

# Create a database engine
engine = create_engine(db_path)


# Create all tables (if not already created)
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

logger.info("AK:::: " + os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."))

client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)

# Define Pydantic Schema for Structured Response
class AffiliationSchema(BaseModel):
    openreview_id: str = Field(..., description="The openreview id that is likely as per the author input data for correlation")
    author_name: Optional[str] = Field(..., description="The author name corresponding to a given affiliation entry")
    affiliation_name: Optional[str] = Field(..., description="The affiliation name for a given author, set to 'Unknown' if not sure or ambiguous")
    affiliation_domain: Optional[str] = Field(..., description="The affiliation domain (DNS) for a given author, set to empty string if not sure or ambiguous")
    affiliation_state_province: Optional[str] = Field(..., description="The state/province address, set to UNK if not sure or ambiguous")
    affiliation_country: Optional[str] = Field(..., description="2 letter ISO country code for the country, set to UNK if not sure or ambiguous")


class AffiliationResponse(BaseModel):
    affiliations: List[AffiliationSchema] = Field(..., description="List of relevant found affiliations based on the author information and the paper")


# Function to get paper authors with unknown affiliation
def get_paper_authors_with_unknown_affiliation():
    """
    Retrieve all PaperAuthor entries where the affiliation is unknown.
    """
    logger.info("Querying paper_authors with unknown affiliation...")
    results = (
        session.query(PaperAuthor)
        .options(
            joinedload(PaperAuthor.paper)
            .joinedload(Paper.authors)
            .joinedload(PaperAuthor.author)
        )
        .filter(
            PaperAuthor.affiliation_name == "Unknown",
            PaperAuthor.affiliation_country == "UNK",
        )
        .all()
    )
    logger.info(f"Found {len(results)} entries with unknown affiliations.")
    return results


# Function to download PDF
def download_pdf(pdf_url):
    """
    Download the PDF from the given URL.
    """
    logger.info(f"Downloading PDF from {pdf_url}...")
    response = requests.get("https://openreview.net" + pdf_url)
    response.raise_for_status()
    return BytesIO(response.content)


# Function to convert PDF to Markdown using pymupdf4llm
def convert_pdf_to_markdown(pdf_stream, num_pages=3):
    """
    Convert the first `num_pages` of the PDF to Markdown using pymupdf4llm.
    """
    logger.info("Converting PDF to Markdown using pymupdf4llm...")
    # Create a temporary file to save the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_stream.read())
        temp_pdf_path = temp_pdf.name
    try:
        # Call the to_markdown function with the temporary file path
        markdown = pymupdf4llm.to_markdown(temp_pdf_path, pages=range(0, num_pages))
    finally:
        # Clean up the temporary file
        os.remove(temp_pdf_path)
    return markdown



def extract_json(markdown_string):
    """
    Extracts the JSON string between ```json start and ``` end tags.
    
    Args:
    markdown_string (str): The markdown string containing the JSON data.
    
    Returns:
    str: The extracted JSON string, including curly braces.
    """
    pattern = r"```json\s*({.*})\s*```"
    match = re.search(pattern, markdown_string, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None


def extract_unknown_authors(paper_author_entries):
    """
    Extract authors with unknown affiliation from PaperAuthor entries.
    """
    logger.info("Extracting authors with unknown affiliations...")
    authors_data = []
    for pa in paper_author_entries:
        author = pa.author
        authors_data.append(
            {"name": author.full_name, "openreview_id": author.openreview_id}
        )
    logger.info(f"Extracted {len(authors_data)} authors with unknown affiliations.")
    return authors_data


# Function to extract authors with UNK affiliation
def prepare_openai_messages(paper_title, authors, markdown_content):
    """
    Prepare the prompt messages for OpenAI ChatCompletion.
    Incorporates the markdown content to provide context for affiliation extraction.
    """
    logger.info("Preparing messages for OpenAI...")
    author_list = "\n".join(
        [
            f"- {author['name']} (OpenReview ID: {author['openreview_id']})"
            for author in authors
        ]
    )
    prompt = f"""You are a helpful assistant that enriches author affiliation information based on the provided document content.

Paper Title: "{paper_title}"

Authors with unknown affiliations:
{author_list}

Document Content (First {len(markdown_content.splitlines())} lines):

---
First think through and reason from the document and the context about the JSON response and then use a code block to respond with this JSON format.
Ensure you articulate your thoughts clearly before starting the JSON markdown tags, and ensure only one JSON code block in markdown format is elicited for the ease of parsing.
Ensure adherence to provided JSON schema

```json
{{"affiliations": ...}}
```

Here is the JSON Schema for the expected result:
{AffiliationResponse.model_json_schema()}
---
{markdown_content}
---

If the affiliation details is not evident, please skip them, do not infer from the document or your own knowledge, strictly stick to the document.
If you cannot determine a particular field, set fields to "UNK".
"""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that enriches author affiliation information based on provided document content.",
        },
        {"role": "user", "content": prompt},
    ]
    return messages


# Function to call OpenAI API and parse response
def get_affiliation_details(messages, expected_count, authors):
    """
    Call OpenAI's ChatCompletion API and parse the response using Pydantic.
    Ensures that the number of affiliations returned matches the expected count.
    """
    logger.info("Calling OpenAI API for affiliation details...")
    try:
        # response = client.beta.chat.completions.parse(
        #     model="openai/gpt-4o",  # Update to the appropriate model
        #     messages=messages,
        #     max_tokens=4096,
        #     n=1,
        #     temperature=0.1,
        #     response_format=AffiliationResponse
        # )
        # response = client.beta.chat.completions.parse(
        #     model="anthropic/claude-3.5-sonnet",
        #     messages=messages,
        #     max_tokens=4096,
        # )
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-haiku",
            messages=messages,
            max_tokens=4096,
            temperature=0.1
        )

        raw_response = response.choices[0].message.content
        

        logger.debug(f"Raw OpenAI response: {raw_response}")
        extracted_json = extract_json(raw_response)
        logger.debug(f"JSON response: {extracted_json}")
        affiliation_response = AffiliationResponse.model_validate_json(extracted_json)

        if len(affiliation_response.affiliations) != expected_count:
            logger.error(
                f"Expected {expected_count} affiliations, but got {len(affiliation_response.affiliations)}."
            )
            raise ValueError(
                "Mismatch in the number of affiliations returned by the LLM."
            )

        logger.info("Successfully parsed affiliation details from OpenAI response.")
        return affiliation_response.affiliations
    except (ValidationError, ValueError) as ve:
        logger.error(f"Validation error: {ve}")
        # Return default UNK affiliations if parsing fails
        return [
            AffiliationSchema(openreview_id=author["openreview_id"])
            for author in authors
        ]
    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {e}")
        # Return default UNK affiliations if an unexpected error occurs
        return [
            AffiliationSchema(openreview_id=author["openreview_id"])
            for author in authors
        ]


# Function to update PaperAuthor entries
def update_paper_author_affiliations(paper_authors, affiliations):
    """
    Update the PaperAuthor entries with the provided affiliation details.
    Mapping is done using the OpenReview ID.
    """
    logger.info("Updating PaperAuthor entries with new affiliation details...")
    openreview_to_pa = {
        pa.author.openreview_id: pa for pa in paper_authors if pa.author.openreview_id
    }

    for aff in affiliations:
        pa = openreview_to_pa.get(aff.openreview_id)
        if not pa:
            logger.warning(
                f"No PaperAuthor entry found for OpenReview ID: {aff.openreview_id}. Skipping."
            )
            continue

        logger.info(aff)
        pa.affiliation_name = aff.affiliation_name or "UNK"
        pa.affiliation_domain = aff.affiliation_domain or "UNK"
        pa.affiliation_state_province = aff.affiliation_state_province or "UNK"
        pa.affiliation_country = aff.affiliation_country or "UNK"
        session.add(pa)

    session.commit()
    logger.info("Affiliation details updated successfully.")


# Main processing function
def process_paper_authors():
    """
    Main function to process PaperAuthor entries with unknown affiliations.
    """
    paper_authors = get_paper_authors_with_unknown_affiliation()

    # Group PaperAuthors by Paper to minimize PDF downloads
    papers_dict = {}
    for pa in paper_authors:
        paper = pa.paper
        if paper.id not in papers_dict:
            papers_dict[paper.id] = {"paper": paper, "authors": []}
        papers_dict[paper.id]["authors"].append(pa)

    logger.info(
        f"Processing {len(papers_dict)} papers with unknown author affiliations."
    )

    for paper_id, data in papers_dict.items():
        paper = data["paper"]
        authors = data["authors"]

        try:
            pdf_url = paper.pdf_url
            if not pdf_url:
                logger.warning(
                    f"Paper ID {paper_id} does not have a PDF URL. Skipping."
                )
                continue

            # Download PDF
            pdf_stream = download_pdf(pdf_url)

            # Convert PDF to Markdown
            markdown = convert_pdf_to_markdown(pdf_stream)
            # Optionally, limit the number of lines to avoid sending excessively long content

            # Extract authors with unknown affiliation
            unknown_authors = extract_unknown_authors(authors)
            if not unknown_authors:
                logger.info(
                    f"No authors with unknown affiliations for Paper ID {paper_id}."
                )
                continue

            # Prepare messages for OpenAI
            messages = prepare_openai_messages(
                paper.title, unknown_authors, markdown
            )
            # Get affiliation details from OpenAI
            affiliations = get_affiliation_details(
                messages,
                expected_count=len(unknown_authors),
                authors=unknown_authors,  # Pass authors here
            )

            # Update PaperAuthor entries
            update_paper_author_affiliations(authors, affiliations)

        except Exception as e:
            logger.error(f"Error processing Paper ID {paper_id}: {e}")

    logger.info("Pipeline processing completed.")


if __name__ == "__main__":
    process_paper_authors()
