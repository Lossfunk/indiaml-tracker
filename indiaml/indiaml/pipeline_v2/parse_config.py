from indiaml.models.conference_schema import EventResponse, Event, EventMedia
from pydantic_settings import BaseSettings, SettingsConfigDict
from indiaml.config.logging_config import get_logger
from indiaml.models.models_v2 import Paper, VenueInfo, Author
from uuid import uuid4

json_file = "./eda/icml-2025.json"
conference = "ICML"
year = "2025"
track = "Conference"
# purpose: resolve the appropriate pipeline runner based on the config

class Config(BaseSettings):
    output_directory: str = "./output"
    logs_directory: str = "./logs"

logger = get_logger(__name__)

logger.info("Loading configuration from %s", json_file) 


json_contents = open(json_file, 'r', encoding='utf-8').read()

# print(json_contents)

event_response = EventResponse.model_validate_json(json_contents)

logger.info("Parsed JSON data successfully")
logger.info("Conference: %s, Year: %s, Track: %s", conference, year, track)

# logger.info(parsed_json)

event_response.results[0]

print(event_response.results[0])




paper_data = event_response.results[0]

def extract_status(raw_status: str) -> str:
    """Extracts the status from the raw status string."""
    if "accept" in raw_status.lower():
        return "accepted"
    elif "reject" in raw_status.lower():
        return "rejected"
    else:
        return "unknown"



def extract_status_type(raw_status: str) -> str:
    """Extracts the status type from the raw status string."""
    if "oral" in raw_status.lower():
        return "oral"
    elif "spotlight" in raw_status.lower():
        return "spotlight"
    elif "poster" in raw_status.lower():
        return "poster"
    else:
        return "other"


paper_model = Paper(
    id = uuid4().hex,
    title = paper_data.name,
    status = extract_status(paper_data.eventtype),
    status_type = extract_status_type(paper_data.event_type),
    pdf_url = paper_data.paper_pdf_url, 
)