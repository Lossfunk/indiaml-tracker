import re
from typing import List, Optional
from indiaml.pipeline_v2.author_extractor import map_authors
from indiaml.models.conference_schema import (
    EventResponse,
    ConferenceEvent,
    ConferenceEventMedia,
    PaperAuthor,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from indiaml.config.logging_config import get_logger
from indiaml.config.pipeline_v2_config import Config
from indiaml.models.models_v2 import Paper, VenueInfo, Author
from uuid import uuid4
from .paper_extractor import map_conference_event_to_paper
from functional import seq
from .institute_extractor import extract_institute_data

json_file = "./eda/icml-2025.json"
conference = "ICML"
year = "2025"
track = "Conference"
# purpose: resolve the appropriate pipeline runner based on the config


logger = get_logger(__name__)

logger.info("Loading configuration from %s", json_file)


json_contents = open(json_file, "r", encoding="utf-8").read()

# print(json_contents)

event_response = EventResponse.model_validate_json(json_contents)

logger.info("Parsed JSON data successfully")
logger.info("Conference: %s, Year: %s, Track: %s", conference, year, track)



insts = seq(event_response.results).map(lambda x: seq(x.authors).map(lambda y: y.institution)).flatten().distinct().to_list()
logger.info("Extracted Institutions: %s", insts)

# paper_data = list(filter(lambda x: isinstance(x, ConferenceEvent) and x.id == 45967, event_response.results))[0]



# venue_info = VenueInfo(
#     id=uuid4().int,  # Generate a unique ID for the venue
#     conference=conference,
#     year=year,
#     track=track,
# )


# paper = map_conference_event_to_paper(paper_data, venue_info)
# logger.info("Mapped Event to Paper: %s", paper)



# authors: List[Author] = (
#     seq(paper_data.authors)
#     .map(lambda author: map_authors(author, venue_info))
#     .to_list()
# )


# for author in paper_data.authors:
#     logger.info("Author: %s", author.fullname)
#     institution = author.institution or "Unknown"
#     logger.info("Author Institution: %s", institution)

#     logger.info("Extracting Paper name: %s", paper_data.name)
#     logger.info("Extracting Paper abstract: %s", paper_data.abstract)

#     details = extract_institute_data(institution)
#     logger.info("Extracted Institution Details: %s", details)
#     print()


