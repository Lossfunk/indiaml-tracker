import re
from typing import Optional
from indiaml.models.conference_schema import ConferenceEvent, PaperAuthor
from indiaml.config.logging_config import get_logger
from indiaml.models.models_v2 import Paper, VenueInfo, Author
from uuid import uuid4





def map_authors(authors: PaperAuthor, venue_info: VenueInfo) -> Author:
    """
    Maps a Pydantic PaperAuthor object to a SQLAlchemy Author object.

    Args:
        authors: The source PaperAuthor object from the conference JSON.

    Returns:
        A populated SQLAlchemy Author object.
    """
    author = Author(
        # id=authors.id,
        full_name=authors.fullname,
        openreview_id=None,  # Assuming URL is used as OpenReview ID
        orcid=None,  # ORCID is not provided in the schema
        google_scholar_link=None,  # Google Scholar link is not provided in the schema
        # picture_url=authors.picture_url,
        bio=authors.bio,
        # usertimezone=authors.usertimezone
    )

    if venue_info.conference == "ICML":
        author.icml_id = authors.id
    elif venue_info.conference == "ICLR":
        author.iclr_id = authors.id
    elif venue_info.conference == "NeurIPS":
        author.neurips_id = authors.id

    return author


##################################