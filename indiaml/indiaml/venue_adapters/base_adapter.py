# adapters/base_adapter.py

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
import openreview

from ..models.dto import AuthorDTO

class AuthorInfo(BaseModel):
    author_name: str = Field(..., description="Full name of the paper author")
    affiliation: str = Field(..., description="Organization/institution name")
    location: str = Field(..., description="City, Country format for institution location")
    country: str = Field(..., description="3-letter ISO code (e.g., 'IND', 'USA')")

class AuthorList(BaseModel):
    authors: List[AuthorInfo] = Field(..., description="List of all authors.")

class PaperRecord(BaseModel):
    id: str
    title: str
    status: str
    pdf_url: str
    pdf_path: Optional[str] = None
    pdate: Optional[str] = None  # Publish date as ISO timestamp
    odate: Optional[str] = None  # Online date as ISO timestamp
    conference: str
    year: int
    track: str
    raw_authors: List[dict] = Field(default_factory=list)



class BaseAdapter(ABC):
    def __init__(self, config):
        self.config = config
        self.client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

    @abstractmethod
    def fetch_papers(self) -> List[PaperRecord]:
        """Fetches papers from the provider."""
        pass

    @abstractmethod
    def determine_status(self, venue_group: openreview.Group, venueid: str) -> str:
        """Determines the submission status based on venue-specific logic."""
        pass


    @abstractmethod
    def fetch_authors(self, author_ids: List[str]) -> List[AuthorDTO]:
        pass