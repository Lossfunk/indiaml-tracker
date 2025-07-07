"""
Global statistics generator for conference analytics.

This module generates global country-level statistics from the v2 database schema,
including paper counts, author counts, and acceptance type distributions.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from ..models.models import (
    Paper, Author, Country, Institution, Affiliation, 
    PaperAuthor, PaperAuthorAffiliation, Conference, Track
)
from .config import COUNTRY_CODE_MAP, STATUS_MAPPINGS

logger = logging.getLogger(__name__)


class GlobalStatsGenerator:
    """Generates global statistics for conference analytics."""
    
    def __init__(self, session: Session):
        """
        Initialize the global stats generator.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def generate_global_stats(self, conference_name: str, year: int, track_name: str = None) -> Dict[str, Any]:
        """
        Generate global statistics for a conference.
        
        Args:
            conference_name: Name of the conference (e.g., "ICML")
            year: Conference year
            track_name: Optional track name filter
            
        Returns:
            Dictionary containing global statistics
        """
        logger.info(f"Generating global stats for {conference_name} {year}")
        
        # Get conference and track info
        conference_info = self._get_conference_info(conference_name, year, track_name)
        
        # Generate country-level statistics
        country_stats = self._generate_country_stats(conference_name, year, track_name)
        
        return {
            "conferenceInfo": conference_info,
            "globalStats": {
                "countries": country_stats
            }
        }
    
    def _get_conference_info(self, conference_name: str, year: int, track_name: str = None) -> Dict[str, Any]:
        """Get basic conference information."""
        # Query for conference and track
        query = self.session.query(Conference).filter(
            Conference.name.ilike(f"%{conference_name}%"),
            Conference.year == year
        )
        
        conference = query.first()
        if not conference:
            logger.warning(f"Conference {conference_name} {year} not found")
            return {
                "name": conference_name,
                "year": year,
                "track": track_name or "Conference",
                "totalAcceptedPapers": 0,
                "totalAcceptedAuthors": 0
            }
        
        # Get track if specified
        track = None
        if track_name:
            track = self.session.query(Track).filter(
                Track.conference_id == conference.id,
                Track.name.ilike(f"%{track_name}%")
            ).first()
        
        # Count total papers and authors
        papers_query = self.session.query(Paper).join(Track).filter(
            Track.conference_id == conference.id
        )
        
        if track:
            papers_query = papers_query.filter(Paper.track_id == track.id)
        
        total_papers = papers_query.count()
        
        # Count unique authors
        authors_query = self.session.query(distinct(PaperAuthor.author_id)).join(Paper).join(Track).filter(
            Track.conference_id == conference.id
        )
        
        if track:
            authors_query = authors_query.filter(Paper.track_id == track.id)
        
        total_authors = authors_query.count()
        
        return {
            "name": conference_name,
            "year": year,
            "track": track.name if track else "Conference",
            "totalAcceptedPapers": total_papers,
            "totalAcceptedAuthors": total_authors
        }
    
    def _generate_country_stats(self, conference_name: str, year: int, track_name: str = None) -> List[Dict[str, Any]]:
        """Generate country-level statistics."""
        # Base query for papers in the conference
        base_query = self.session.query(Paper).join(Track).join(Conference).filter(
            Conference.name.ilike(f"%{conference_name}%"),
            Conference.year == year
        )
        
        if track_name:
            base_query = base_query.join(Track).filter(Track.name.ilike(f"%{track_name}%"))
        
        # Query for basic country statistics using country names since codes are None
        country_stats_query = self.session.query(
            Country.name.label('country_name'),
            func.count(distinct(Paper.id)).label('paper_count'),
            func.count(distinct(Author.id)).label('author_count')
        ).select_from(Paper)\
         .join(Track)\
         .join(Conference)\
         .join(PaperAuthor)\
         .join(Author)\
         .join(PaperAuthorAffiliation)\
         .join(Affiliation)\
         .join(Institution)\
         .join(Country)\
         .filter(
             Conference.name.ilike(f"%{conference_name}%"),
             Conference.year == year
         )
        
        if track_name:
            country_stats_query = country_stats_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        country_stats_query = country_stats_query.group_by(Country.name)\
                                                 .order_by(func.count(distinct(Paper.id)).desc())
        
        results = country_stats_query.all()
        
        country_stats = []
        for result in results:
            country_name = result.country_name or "Unknown"
            
            # Map country name to country code
            country_code = self._find_country_code_by_name(country_name)
            
            # Count spotlights and orals separately for this country
            spotlight_count = self._count_status_papers_by_name(conference_name, year, country_name, 'spotlight', track_name)
            oral_count = self._count_status_papers_by_name(conference_name, year, country_name, 'oral', track_name)
            
            country_stats.append({
                "affiliation_country": country_code,
                "paper_count": int(result.paper_count or 0),
                "author_count": int(result.author_count or 0),
                "spotlights": spotlight_count,
                "orals": oral_count
            })
        
        return country_stats
    
    def _count_status_papers(self, conference_name: str, year: int, country_code: str, status_type: str, track_name: str = None) -> int:
        """Count papers with specific status for a country."""
        query = self.session.query(func.count(distinct(Paper.id)))\
                           .select_from(Paper)\
                           .join(Track)\
                           .join(Conference)\
                           .join(PaperAuthor)\
                           .join(Author)\
                           .join(PaperAuthorAffiliation)\
                           .join(Affiliation)\
                           .join(Institution)\
                           .join(Country)\
                           .filter(
                               Conference.name.ilike(f"%{conference_name}%"),
                               Conference.year == year,
                               Country.code == country_code,
                               func.lower(Paper.status).like(f'%{status_type}%')
                           )
        
        if track_name:
            query = query.filter(Track.name.ilike(f"%{track_name}%"))
        
        result = query.scalar()
        return int(result or 0)
    
    def _count_status_papers_by_name(self, conference_name: str, year: int, country_name: str, status_type: str, track_name: str = None) -> int:
        """Count papers with specific status for a country by name."""
        query = self.session.query(func.count(distinct(Paper.id)))\
                           .select_from(Paper)\
                           .join(Track)\
                           .join(Conference)\
                           .join(PaperAuthor)\
                           .join(Author)\
                           .join(PaperAuthorAffiliation)\
                           .join(Affiliation)\
                           .join(Institution)\
                           .join(Country)\
                           .filter(
                               Conference.name.ilike(f"%{conference_name}%"),
                               Conference.year == year,
                               Country.name == country_name,
                               func.lower(Paper.status).like(f'%{status_type}%')
                           )
        
        if track_name:
            query = query.filter(Track.name.ilike(f"%{track_name}%"))
        
        result = query.scalar()
        return int(result or 0)
    
    def _find_country_code_by_name(self, country_name: str) -> str:
        """Find country code by country name."""
        country_name_lower = country_name.lower()
        
        # Direct lookup in reverse mapping
        for code, name in COUNTRY_CODE_MAP.items():
            if name.lower() == country_name_lower:
                return code
        
        # Partial matching for common variations
        country_mappings = {
            "united states": "US",
            "usa": "US",
            "america": "US",
            "china": "CN",
            "united kingdom": "GB",
            "uk": "GB",
            "britain": "GB",
            "germany": "DE",
            "france": "FR",
            "canada": "CA",
            "australia": "AU",
            "japan": "JP",
            "south korea": "KR",
            "korea": "KR",
            "singapore": "SG",
            "hong kong": "HK",
            "switzerland": "CH",
            "netherlands": "NL",
            "sweden": "SE",
            "denmark": "DK",
            "norway": "NO",
            "finland": "FI",
            "austria": "AT",
            "belgium": "BE",
            "italy": "IT",
            "spain": "ES",
            "portugal": "PT",
            "israel": "IL",
            "india": "IN",
            "russia": "RU",
            "brazil": "BR",
            "mexico": "MX",
            "argentina": "AR",
            "chile": "CL",
            "colombia": "CO",
            "south africa": "ZA",
            "egypt": "EG",
            "turkey": "TR",
            "iran": "IR",
            "saudi arabia": "SA",
            "uae": "AE",
            "united arab emirates": "AE",
            "thailand": "TH",
            "vietnam": "VN",
            "indonesia": "ID",
            "malaysia": "MY",
            "philippines": "PH",
            "taiwan": "TW",
            "new zealand": "NZ",
            "ireland": "IE",
            "poland": "PL",
            "czech republic": "CZ",
            "hungary": "HU",
            "romania": "RO",
            "bulgaria": "BG",
            "croatia": "HR",
            "slovenia": "SI",
            "slovakia": "SK",
            "estonia": "EE",
            "latvia": "LV",
            "lithuania": "LT",
            "greece": "GR",
            "cyprus": "CY",
            "malta": "MT",
            "luxembourg": "LU"
        }
        
        return country_mappings.get(country_name_lower, "UNK")
    
    def _normalize_status(self, status: str) -> str:
        """Normalize paper status to standard categories."""
        if not status:
            return "unknown"
        
        status_lower = status.lower().strip()
        
        for normalized_status, variations in STATUS_MAPPINGS.items():
            for variation in variations:
                if variation and variation.lower() in status_lower:
                    return normalized_status
        
        return "unknown"
    
    def get_conference_summary(self, conference_name: str, year: int) -> Dict[str, Any]:
        """Get a summary of the conference."""
        conference_info = self._get_conference_info(conference_name, year)
        country_stats = self._generate_country_stats(conference_name, year)
        
        # Calculate top countries
        top_countries = sorted(country_stats, key=lambda x: x['paper_count'], reverse=True)[:10]
        
        # Calculate total spotlights and orals
        total_spotlights = sum(c['spotlights'] for c in country_stats)
        total_orals = sum(c['orals'] for c in country_stats)
        
        return {
            "conference": conference_info,
            "topCountries": top_countries,
            "totalSpotlights": total_spotlights,
            "totalOrals": total_orals,
            "totalCountries": len(country_stats)
        }
