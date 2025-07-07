"""
Institution-specific analytics generator.

This module provides detailed analysis of institutional contributions,
rankings, and research patterns within conference data.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from ..models.models import (
    Paper, Author, Country, Institution, Affiliation, 
    PaperAuthor, PaperAuthorAffiliation, Conference, Track
)
from .config import ACADEMIC_KEYWORDS, CORPORATE_KEYWORDS

logger = logging.getLogger(__name__)


class InstitutionAnalyzer:
    """Analyzes institutional contributions to conferences."""
    
    def __init__(self, session: Session):
        """
        Initialize the institution analyzer.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def analyze_institutions(self, conference_name: str, year: int, 
                           country_code: str = None, track_name: str = None,
                           top_n: int = 50) -> Dict[str, Any]:
        """
        Analyze institutional contributions to a conference.
        
        Args:
            conference_name: Name of the conference
            year: Conference year
            country_code: Optional country filter
            track_name: Optional track name filter
            top_n: Number of top institutions to return
            
        Returns:
            Dictionary containing institutional analysis
        """
        logger.info(f"Analyzing institutions for {conference_name} {year}")
        
        # Get institutional statistics
        institution_stats = self._get_institution_statistics(
            conference_name, year, country_code, track_name
        )
        
        # Sort by paper count and take top N
        top_institutions = sorted(
            institution_stats, 
            key=lambda x: x["paper_count"], 
            reverse=True
        )[:top_n]
        
        # Generate summary statistics
        summary = self._generate_summary_statistics(institution_stats)
        
        return {
            "summary": summary,
            "topInstitutions": top_institutions,
            "totalInstitutions": len(institution_stats)
        }
    
    def _get_institution_statistics(self, conference_name: str, year: int,
                                  country_code: str = None, track_name: str = None) -> List[Dict[str, Any]]:
        """Get statistics for all institutions in the conference."""
        # Base query for institutions with papers
        institutions_query = self.session.query(Institution).distinct()\
            .join(Affiliation)\
            .join(PaperAuthorAffiliation)\
            .join(PaperAuthor)\
            .join(Paper)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if country_code:
            institutions_query = institutions_query.join(Country).filter(
                Country.code == country_code
            )
        
        if track_name:
            institutions_query = institutions_query.filter(
                Track.name.ilike(f"%{track_name}%")
            )
        
        institutions = institutions_query.all()
        
        institution_stats = []
        for institution in institutions:
            stats = self._get_single_institution_stats(
                institution, conference_name, year, track_name
            )
            if stats["paper_count"] > 0:
                institution_stats.append(stats)
        
        return institution_stats
    
    def _get_single_institution_stats(self, institution: Institution, 
                                    conference_name: str, year: int,
                                    track_name: str = None) -> Dict[str, Any]:
        """Get statistics for a single institution."""
        # Count papers from this institution
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
        
        # Count unique authors from this institution
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
        
        # Count first author papers
        first_author_papers = self.session.query(Paper).distinct()\
            .join(PaperAuthor)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Affiliation.institution_id == institution.id,
                PaperAuthor.author_order == 1,  # First author
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if track_name:
            first_author_papers = first_author_papers.filter(Track.name.ilike(f"%{track_name}%"))
        
        first_author_count = first_author_papers.count()
        
        # Count spotlights and orals
        spotlights = sum(1 for p in papers if self._is_spotlight(p.status))
        orals = sum(1 for p in papers if self._is_oral(p.status))
        
        # Classify institution type
        institution_type = self._classify_institution_type(institution.name)
        
        # Calculate productivity metrics
        papers_per_author = len(papers) / len(authors) if authors else 0
        
        return {
            "institution_id": institution.id,
            "name": institution.name,
            "normalized_name": institution.normalized_name,
            "country": institution.country.name if institution.country else "Unknown",
            "country_code": institution.country.code if institution.country else "UNK",
            "type": institution_type,
            "paper_count": len(papers),
            "author_count": len(authors),
            "first_author_papers": first_author_count,
            "spotlights": spotlights,
            "orals": orals,
            "papers_per_author": round(papers_per_author, 2),
            "spotlight_rate": round(spotlights / len(papers) * 100, 1) if papers else 0,
            "oral_rate": round(orals / len(papers) * 100, 1) if papers else 0,
            "first_author_rate": round(first_author_count / len(papers) * 100, 1) if papers else 0
        }
    
    def _generate_summary_statistics(self, institution_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics across all institutions."""
        if not institution_stats:
            return {
                "total_institutions": 0,
                "academic_institutions": 0,
                "corporate_institutions": 0,
                "total_papers": 0,
                "total_authors": 0,
                "avg_papers_per_institution": 0,
                "avg_authors_per_institution": 0
            }
        
        academic_count = sum(1 for inst in institution_stats if inst["type"] == "academic")
        corporate_count = sum(1 for inst in institution_stats if inst["type"] == "corporate")
        
        total_papers = sum(inst["paper_count"] for inst in institution_stats)
        total_authors = sum(inst["author_count"] for inst in institution_stats)
        
        # Top institutions by different metrics
        top_by_papers = sorted(institution_stats, key=lambda x: x["paper_count"], reverse=True)[:5]
        top_by_authors = sorted(institution_stats, key=lambda x: x["author_count"], reverse=True)[:5]
        top_by_spotlights = sorted(institution_stats, key=lambda x: x["spotlights"], reverse=True)[:5]
        
        return {
            "total_institutions": len(institution_stats),
            "academic_institutions": academic_count,
            "corporate_institutions": corporate_count,
            "total_papers": total_papers,
            "total_authors": total_authors,
            "avg_papers_per_institution": round(total_papers / len(institution_stats), 1),
            "avg_authors_per_institution": round(total_authors / len(institution_stats), 1),
            "top_by_papers": [{"name": inst["name"], "count": inst["paper_count"]} for inst in top_by_papers],
            "top_by_authors": [{"name": inst["name"], "count": inst["author_count"]} for inst in top_by_authors],
            "top_by_spotlights": [{"name": inst["name"], "count": inst["spotlights"]} for inst in top_by_spotlights]
        }
    
    def get_institution_rankings(self, conference_name: str, year: int,
                               country_code: str = None, track_name: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get institution rankings by different metrics."""
        institution_stats = self._get_institution_statistics(
            conference_name, year, country_code, track_name
        )
        
        return {
            "by_paper_count": sorted(institution_stats, key=lambda x: x["paper_count"], reverse=True),
            "by_author_count": sorted(institution_stats, key=lambda x: x["author_count"], reverse=True),
            "by_spotlights": sorted(institution_stats, key=lambda x: x["spotlights"], reverse=True),
            "by_orals": sorted(institution_stats, key=lambda x: x["orals"], reverse=True),
            "by_first_author_rate": sorted(institution_stats, key=lambda x: x["first_author_rate"], reverse=True),
            "by_spotlight_rate": sorted(institution_stats, key=lambda x: x["spotlight_rate"], reverse=True)
        }
    
    def compare_institutions(self, institution_names: List[str], 
                           conference_name: str, year: int,
                           track_name: str = None) -> Dict[str, Any]:
        """Compare specific institutions."""
        comparison_data = []
        
        for name in institution_names:
            institution = self.session.query(Institution).filter(
                Institution.name.ilike(f"%{name}%")
            ).first()
            
            if institution:
                stats = self._get_single_institution_stats(
                    institution, conference_name, year, track_name
                )
                comparison_data.append(stats)
        
        return {
            "institutions": comparison_data,
            "comparison_metrics": self._generate_comparison_metrics(comparison_data)
        }
    
    def _generate_comparison_metrics(self, institutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comparison metrics between institutions."""
        if not institutions:
            return {}
        
        metrics = {}
        
        # Find leaders in each category
        metrics["most_papers"] = max(institutions, key=lambda x: x["paper_count"])["name"]
        metrics["most_authors"] = max(institutions, key=lambda x: x["author_count"])["name"]
        metrics["most_spotlights"] = max(institutions, key=lambda x: x["spotlights"])["name"]
        metrics["highest_spotlight_rate"] = max(institutions, key=lambda x: x["spotlight_rate"])["name"]
        
        # Calculate averages
        metrics["avg_papers"] = round(sum(inst["paper_count"] for inst in institutions) / len(institutions), 1)
        metrics["avg_authors"] = round(sum(inst["author_count"] for inst in institutions) / len(institutions), 1)
        metrics["avg_spotlight_rate"] = round(sum(inst["spotlight_rate"] for inst in institutions) / len(institutions), 1)
        
        return metrics
    
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
    
    def get_collaboration_analysis(self, conference_name: str, year: int,
                                 country_code: str = None) -> Dict[str, Any]:
        """Analyze collaboration patterns between institutions."""
        # Get papers with multiple institutional affiliations
        multi_institution_papers = self.session.query(Paper)\
            .join(PaperAuthor)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            )
        
        if country_code:
            multi_institution_papers = multi_institution_papers.join(Country).filter(
                Country.code == country_code
            )
        
        # This would require more complex analysis to identify collaboration patterns
        # For now, return basic collaboration statistics
        
        total_papers = multi_institution_papers.distinct().count()
        
        # Count papers with international collaboration
        international_papers = self.session.query(Paper).distinct()\
            .join(PaperAuthor)\
            .join(PaperAuthorAffiliation)\
            .join(Affiliation)\
            .join(Institution)\
            .join(Country)\
            .join(Track)\
            .join(Conference)\
            .filter(
                Conference.name.ilike(f"%{conference_name}%"),
                Conference.year == year
            ).group_by(Paper.id)\
            .having(func.count(distinct(Country.code)) > 1).count()
        
        return {
            "total_papers": total_papers,
            "international_collaborations": international_papers,
            "international_collaboration_rate": round(international_papers / total_papers * 100, 1) if total_papers > 0 else 0
        }
