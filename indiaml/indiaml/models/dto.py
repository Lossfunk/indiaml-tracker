from typing import Dict, Optional, List
from dataclasses import dataclass



@dataclass
class AuthorDTO:
    canonical_id: str
    name: str # Preferred name of the author

    alternate_names = Optional[List[str]]  # List of alternate names
    email: Optional[str] = None

    openreview_id: Optional[str] = None
    orcid: Optional[str] = None
    google_scholar_link: Optional[str] = None
    arxiv_id: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None

    icml_id: Optional[str] = None
    iclr_id: Optional[str] = None
    neurips_id: Optional[str] = None

    researchgate_id: Optional[str] = None
    dblp_id: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

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
