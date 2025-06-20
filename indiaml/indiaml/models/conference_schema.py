import json
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Pydantic Schemas for Data Validation ---
# These models represent the structure of your JSON data.
# These are compatible with ICML.cc, ICLR.cc, and NeurIPS.cc event data scraped directly from their website

class PaperAuthor(BaseModel):
    """Represents an author of a paper."""
    id: int
    fullname: str
    url: Optional[str] = None
    bio: Optional[str] = None  # Can be empty string, null, or actual bio
    institution: Optional[str] = None
    picture_url: Optional[str] = None
    usertimezone: Optional[str] = None  # Only some authors have this field

class ConferenceEventMedia(BaseModel):
    """Represents a media item associated with an event."""
    id: int
    modified: str  # ISO datetime string
    display_section: int
    type: str  # e.g., "URL"
    name: str
    visible: bool
    sortkey: int
    is_live_content: bool
    uri: Optional[str] = None
    resourcetype: str  # e.g., "UriEventmedia"

class ConferenceEvent(BaseModel):
    """Represents a single event, such as a poster or talk."""
    id: int
    uid: str
    name: str
    authors: List[PaperAuthor]
    abstract: str
    topic: Optional[str] = None  # Can be null or something like "Deep Learning->Theory"
    keywords: List[Any] = Field(default_factory=list)  # Appears to be empty lists in examples
    decision: str  # e.g., "Accept (poster)", "Accept (spotlight poster)", "Accept (oral)"
    session: Optional[str] = None  # e.g., "Poster Session 6"
    eventtype: str  # e.g., "Poster"
    event_type: str  # e.g., "Poster", "Spotlight Poster"
    room_name: Optional[str] = None
    virtualsite_url: Optional[str] = None  # e.g., "/virtual/2025/poster/45010"
    url: Optional[str] = None
    sourceid: int
    sourceurl: str  # e.g., "https://openreview.net/group?id=ICML.cc/2025/Conference"
    starttime: Optional[str]  # ISO datetime string
    endtime: Optional[str]  # ISO datetime string
    starttime2: Optional[str] = None
    endtime2: Optional[str] = None
    diversity_event: Optional[str] = None
    paper_url: Optional[str] = None  # e.g., "https://openreview.net/forum?id=WZlq625BWD"
    paper_pdf_url: Optional[str] = None
    children_url: Optional[str] = None
    children: List[Any] = Field(default_factory=list)  # Appears to be empty in examples
    children_ids: List[int] = Field(default_factory=list)
    parent1: Optional[str] = None  # URL to parent event
    parent2: Optional[str] = None
    parent2_id: Optional[int] = None
    eventmedia: List[ConferenceEventMedia] = Field(default_factory=list)
    show_in_schedule_overview: bool = False
    visible: bool = True
    poster_position: Optional[str] = None
    schedule_html: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    related_events: List[str] = Field(default_factory=list)  # List of URLs
    related_events_ids: List[int] = Field(default_factory=list)

class EventResponse(BaseModel):
    """Represents the top-level structure of the JSON file."""
    count: int
    next: Optional[str] = None  # For pagination
    previous: Optional[str] = None  # For pagination
    results: List[ConferenceEvent]