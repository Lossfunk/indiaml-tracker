# dto.py
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class AuthorDTO:
    name: str
    email: Optional[str] = None
    openreview_id: Optional[str] = None
    orcid: Optional[str] = None
    google_scholar_link: Optional[str] = None
    dblp: Optional[str] = None
    linkedin: Optional[str] = None
    homepage: Optional[str] = None
    history: Optional[List[Dict]] = None  # Added history field

@dataclass
class PaperDTO:
    id: str
    title: str
    status: str
    pdf_url: str
    pdate: Optional[str]  # ISO8601 string or None
    odate: Optional[str]  # ISO8601 string or None
    conference: str
    year: int
    track: str
    authors: List[AuthorDTO]
