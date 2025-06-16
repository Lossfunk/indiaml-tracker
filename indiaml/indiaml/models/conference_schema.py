import json
from typing import List, Optional
from pydantic import BaseModel, Field

# --- Pydantic Schemas for Data Validation ---
# These models represent the structure of your JSON data.
# These are compatible with ICML.cc, ICLR.cc, and NeurIPS.cc event data. scraped directly from their website

class Author(BaseModel):
    """Represents an author of a paper."""
    id: int
    fullname: str
    institution: Optional[str] = None


class EventMedia(BaseModel):
    """Represents a media item associated with an event."""
    id: int
    resourcetype: str
    uri: Optional[str] = None
    name: str


class Event(BaseModel):
    """Represents a single event, such as a poster or talk."""
    id: int
    uid: str
    name: str
    authors: List[Author]
    abstract: str
    eventtype: str
    session: Optional[str] = None
    # The 'related_events_ids' is an empty list in the example, 
    # but we'll define it to handle cases where it might have data.
    related_events_ids: List[int] 
    eventmedia: List[EventMedia]


class EventResponse(BaseModel):
    """Represents the top-level structure of the JSON file."""
    count: int
    results: List[Event]
