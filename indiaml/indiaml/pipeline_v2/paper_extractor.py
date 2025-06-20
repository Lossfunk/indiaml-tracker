import re
from typing import Optional
from indiaml.models.conference_schema import ConferenceEvent
from indiaml.config.logging_config import get_logger
from indiaml.models.models_v2 import Paper, VenueInfo, Author
from uuid import uuid4


logger = get_logger(__name__)





def extract_status(raw_status: str) -> str:
    """Extracts the status from the raw decision string."""
    if "accept" in raw_status.lower():
        return "accepted"
    elif "reject" in raw_status.lower():
        return "rejected"
    else:
        return "unknown"


def extract_status_type(raw_status: str) -> str:
    """Extracts the status type from the raw decision string."""
    raw_status_lower = raw_status.lower()
    if "oral" in raw_status_lower:
        return "oral"
    elif "spotlight" in raw_status_lower:
        return "spotlight"
    elif "poster" in raw_status_lower:
        return "poster"
    else:
        return "other"


def extract_openreview_id(url: Optional[str]) -> Optional[str]:
    """Extracts the OpenReview ID from a URL."""
    if not url:
        return None
    match = re.search(r"id=([^&]+)", url)
    return match.group(1) if match else None





def map_conference_event_to_paper(event: ConferenceEvent, venue_info: VenueInfo) -> Paper:
    """
    Maps a Pydantic Event object to a SQLAlchemy Paper object.

    Args:
        event: The source Event object from the conference JSON.
        venue_info: The SQLAlchemy VenueInfo object for the current conference.

    Returns:
        A populated SQLAlchemy Paper object.
    """
    openreview_id = extract_openreview_id(event.paper_url) or event.uid

    paper_links = {
        "virtualsite_url": event.virtualsite_url,
        "source_url": event.sourceurl,
        "paper_url": event.paper_url,
        "event_url": event.url,
    }

    paper_model = Paper(
        id=openreview_id,
        venue_info_id=venue_info.id,
        title=event.name,
        status=extract_status(event.decision),
        status_type=extract_status_type(event.decision),
        pdf_url=event.paper_pdf_url,
        openreview_id=openreview_id,
        abstract=event.abstract,
        links=paper_links,
        raw_authors=[
            author.model_dump() for author in event.authors
        ],  # Store raw author data as JSON
    )
    return paper_model


