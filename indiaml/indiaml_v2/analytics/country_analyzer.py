"""
Country-specific analytics generator.

This module generates detailed analytics for a specific focus country,
including authorship patterns, collaboration analysis, and paper categorization.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_, or_

from ..models.models import (
    Paper, Author, Country, Institution, Affiliation, 
    PaperAuthor, PaperAuthorAffiliation, Conference, Track
)
from .config import COUNTRY_CODE_MAP, STATUS_MAPPINGS, ACADEMIC_KEYWORDS, CORPORATE_KEYWORDS

logger = logging.getLogger(__name__)


class CountryAnalyzer:
    """Analyzes conference data for a specific focus country."""
    
    def __init__(self, session: Session):
        """
        Initialize the country analyzer.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def analyze_country(self, country_code: str, conference_name: str, year: int, 
                       track_name: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive analytics for a focus country.
        
        Args:
            country_code: ISO country code (e.g., "IN" for India)
            conference_name: Name of the conference
            year: Conference year
            track_name: Optional track name filter
            
        Returns:
            Dictionary containing country-specific analytics
        """
        logger.info(f"Analyzing country {country_code} for {conference_name} {year}")
        
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        # Get basic country statistics
        basic_stats = self._get_basic_country_stats(country_code, conference_name, year, track_name)
        
        # Analyze authorship patterns
        authorship_analysis = self._analyze_authorship_patterns(country_code, conference_name, year, track_name)
        
        # Get institution analysis
        institution_analysis = self._analyze_institutions(country_code, conference_name, year, track_name)
        
        return {
            "country_code": country_code,
            "country_name": country_name,
            "total_authors": basic_stats["total_authors"],
            "total_spotlights": basic_stats["total_spotlights"],
            "total_orals": basic_stats["total_orals"],
            "institution_types": basic_stats["institution_types"],
            **authorship_analysis,
            "institutions": institution_analysis
        }
    
    def _get_basic_country_stats(self, country_code: str, conference_name: str, 
                                year: int, track_name: str = None) -> Dict[str, Any]:
        """Get basic statistics for the country."""
        # Map country code to country name for database lookup
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        # Count unique authors from the country
        authors_query = self.session.query(distinct(Author.id))\
            .join(PaperAuthor)\
            .join(Paper)\
            .join(Track)\
            .join(Conference)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Country)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            authors_query = authors_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        total_authors = authors_query.count()
        
        # Count spotlights and orals for papers with country authors
        papers_with_country_authors = self.session.query(Paper)\
            .join(PaperAuthor)\
            .join(Author)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Country)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            papers_with_country_authors = papers_with_country_authors.filter(
                Track.name.ilike(f"%{track_name}%")
            )
        
        papers_list = papers_with_country_authors.all()
        
        total_spotlights = sum(1 for p in papers_list if self._is_spotlight(p.status))
        total_orals = sum(1 for p in papers_list if self._is_oral(p.status))
        
        # Analyze institution types
        institution_types = self._analyze_institution_types(country_code, conference_name, year, track_name)
        
        return {
            "total_authors": total_authors,
            "total_spotlights": total_spotlights,
            "total_orals": total_orals,
            "institution_types": institution_types
        }
    
    def _analyze_authorship_patterns(self, country_code: str, conference_name: str, 
                                   year: int, track_name: str = None) -> Dict[str, Any]:
        """Analyze different authorship patterns for the country."""
        # Get papers with at least one author from the country
        at_least_one_papers = self._get_papers_with_at_least_one_author(
            country_code, conference_name, year, track_name
        )
        
        # Get papers with majority authors from the country
        majority_papers = self._get_papers_with_majority_authors(
            country_code, conference_name, year, track_name
        )
        
        # Get papers with first author from the country
        first_author_papers = self._get_papers_with_first_author(
            country_code, conference_name, year, track_name
        )
        
        return {
            "at_least_one_focus_country_author": {
                "count": len(at_least_one_papers),
                "papers": [self._format_paper_info(p) for p in at_least_one_papers]
            },
            "majority_focus_country_authors": {
                "count": len(majority_papers),
                "papers": [self._format_paper_info(p) for p in majority_papers]
            },
            "first_focus_country_author": {
                "count": len(first_author_papers),
                "papers": [self._format_paper_info(p) for p in first_author_papers]
            }
        }
    
    def _get_papers_with_at_least_one_author(self, country_code: str, conference_name: str, 
                                           year: int, track_name: str = None) -> List[Paper]:
        """Get papers with at least one author from the focus country."""
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        query = self.session.query(Paper).distinct()\
            .join(PaperAuthor)\
            .join(Author)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Country)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            query = query.filter(Track.name.ilike(f"%{track_name}%"))
        
        return query.all()
    
    def _get_papers_with_majority_authors(self, country_code: str, conference_name: str, 
                                        year: int, track_name: str = None) -> List[Paper]:
        """Get papers where majority of authors are from the focus country."""
        # This is a complex query - we need to count authors per paper and filter
        papers_with_at_least_one = self._get_papers_with_at_least_one_author(
            country_code, conference_name, year, track_name
        )
        
        majority_papers = []
        for paper in papers_with_at_least_one:
            total_authors = self.session.query(PaperAuthor).filter(
                PaperAuthor.paper_id == paper.id
            ).count()
            
            country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
            country_authors = self.session.query(PaperAuthor)\
                .join(Author)\
                .join(PaperAuthorAffiliation)\
                .join(Affiliation)\
                .join(Institution)\
                .join(Country)\
                .filter(
                    PaperAuthor.paper_id == paper.id,
                    Country.name.ilike(f"%{country_name}%")
                ).count()
            
            if country_authors > total_authors / 2:
                majority_papers.append(paper)
        
        return majority_papers
    
    def _get_papers_with_first_author(self, country_code: str, conference_name: str, 
                                    year: int, track_name: str = None) -> List[Paper]:
        """Get papers where the first author is from the focus country."""
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        query = self.session.query(Paper).distinct()\
            .join(PaperAuthor)\
            .join(Author)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Country)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                PaperAuthor.author_order == 1,  # First author
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            query = query.filter(Track.name.ilike(f"%{track_name}%"))
        
        return query.all()
    
    def _analyze_institutions(self, country_code: str, conference_name: str, 
                            year: int, track_name: str = None) -> List[Dict[str, Any]]:
        """Analyze institutions from the focus country."""
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        # Get all institutions from the country that have papers
        institutions_query = self.session.query(Institution)\
            .join(Country)\
            .join(Affiliation)\
            .join(PaperAuthorAffiliation)\
            .join(PaperAuthor)\
            .join(Paper)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            institutions_query = institutions_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        institutions = institutions_query.distinct().all()
        
        institution_stats = []
        for institution in institutions:
            stats = self._get_institution_stats(institution, conference_name, year, track_name)
            if stats["total_paper_count"] > 0:  # Only include institutions with papers
                institution_stats.append(stats)
        
        # Sort by total paper count
        institution_stats.sort(key=lambda x: x["total_paper_count"], reverse=True)
        
        return institution_stats
    
    def _get_institution_stats(self, institution: Institution, conference_name: str, 
                             year: int, track_name: str = None) -> Dict[str, Any]:
        """Get statistics for a specific institution."""
        # Get papers associated with this institution
        papers_query = self.session.query(Paper).distinct()\
            .join(PaperAuthor)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Affiliation.institution_id == institution.id,
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            papers_query = papers_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        papers = papers_query.all()
        
        # Count unique papers (some papers might have multiple authors from same institution)
        unique_papers = list({p.id: p for p in papers}.values())
        
        # Get authors from this institution
        authors_query = self.session.query(Author).distinct()\
            .join(PaperAuthor)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Paper)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Affiliation.institution_id == institution.id,
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            authors_query = authors_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        authors = authors_query.all()
        
        # Count spotlights and orals
        spotlights = sum(1 for p in papers if self._is_spotlight(p.status))
        orals = sum(1 for p in papers if self._is_oral(p.status))
        
        # Determine institution type
        institution_type = self._classify_institution_type(institution.name)
        
        return {
            "institute": institution.name,
            "total_paper_count": len(papers),
            "unique_paper_count": len(unique_papers),
            "author_count": len(authors),
            "spotlights": spotlights,
            "orals": orals,
            "type": institution_type,
            "papers": [self._format_paper_info(p) for p in unique_papers],
            "authors": [author.name for author in authors]
        }
    
    def _analyze_institution_types(self, country_code: str, conference_name: str, 
                                 year: int, track_name: str = None) -> Dict[str, int]:
        """Analyze the distribution of institution types."""
        country_name = COUNTRY_CODE_MAP.get(country_code, country_code)
        
        institutions_query = self.session.query(Institution)\
            .join(Country)\
            .join(Affiliation)\
            .join(PaperAuthorAffiliation)\
            .join(PaperAuthor)\
            .join(Paper)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Country.name.ilike(f"%{country_name}%"),
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            institutions_query = institutions_query.filter(Track.name.ilike(f"%{track_name}%"))
        
        institutions = institutions_query.distinct().all()
        
        academic_count = 0
        corporate_count = 0
        
        for institution in institutions:
            inst_type = self._classify_institution_type(institution.name)
            if inst_type == "academic":
                academic_count += 1
            elif inst_type == "corporate":
                corporate_count += 1
        
        return {
            "academic": academic_count,
            "corporate": corporate_count
        }
    
    def _classify_institution_type(self, institution_name: str) -> str:
        """Classify institution as academic or corporate."""
        name_lower = institution_name.lower()
        
        # Check for academic keywords
        for keyword in ACADEMIC_KEYWORDS:
            if keyword in name_lower:
                return "academic"
        
        # Check for corporate keywords
        for keyword in CORPORATE_KEYWORDS:
            if keyword in name_lower:
                return "corporate"
        
        # Default to academic if unclear
        return "academic"
    
    def _format_paper_info(self, paper: Paper) -> Dict[str, Any]:
        """Format paper information for output."""
        return {
            "id": paper.id,
            "title": paper.title,
            "isSpotlight": self._is_spotlight(paper.status),
            "isOral": self._is_oral(paper.status)
        }
    
    def _is_spotlight(self, status: str) -> bool:
        """Check if paper status indicates spotlight."""
        if not status:
            return False
        return "spotlight" in status.lower()
    
    def _is_oral(self, status: str) -> bool:
        """Check if paper status indicates oral presentation."""
        if not status:
            return False
        return "oral" in status.lower()
    
    def _get_base_query(self, conference_name: str, year: int, track_name: str = None):
        """Get base query for papers in the conference."""
        query = self.session.query(Paper)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            query = query.filter(Track.name.ilike(f"%{track_name}%"))
        
        return query
