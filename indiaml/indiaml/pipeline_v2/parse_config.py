from indiaml.models.conference_schema import EventResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from indiaml.config.logging_config import get_logger

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