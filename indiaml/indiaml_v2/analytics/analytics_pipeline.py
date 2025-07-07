"""
Main analytics pipeline for generating comprehensive conference analytics.

This module orchestrates all analytics components to generate complete
analytics JSON files compatible with the v1 format but using v2 data.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ..models.models import Base
from .global_stats_generator import GlobalStatsGenerator
from .country_analyzer import CountryAnalyzer
from .institution_analyzer import InstitutionAnalyzer
from .config import (
    DEFAULT_CONFIG, COLOR_SCHEME, DASHBOARD_SECTIONS,
    COUNTRY_CODE_MAP
)

logger = logging.getLogger(__name__)


class AnalyticsPipeline:
    """Main analytics pipeline for generating conference analytics."""
    
    def __init__(self, db_path: str):
        """
        Initialize the analytics pipeline.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        
        # Create session
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize analyzers
        self.global_stats = GlobalStatsGenerator(self.session)
        self.country_analyzer = CountryAnalyzer(self.session)
        self.institution_analyzer = InstitutionAnalyzer(self.session)
    
    def generate_analytics(self, conference_name: str, year: int, 
                         focus_country_code: str = "IN",
                         track_name: str = None,
                         output_path: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive analytics for a conference.
        
        Args:
            conference_name: Name of the conference (e.g., "ICML")
            year: Conference year
            focus_country_code: ISO country code for focus country analysis
            track_name: Optional track name filter
            output_path: Optional path to save the analytics JSON
            
        Returns:
            Complete analytics dictionary
        """
        logger.info(f"Generating analytics for {conference_name} {year}, focus: {focus_country_code}")
        
        try:
            # Generate global statistics
            global_data = self.global_stats.generate_global_stats(
                conference_name, year, track_name
            )
            
            # Generate focus country analysis
            focus_country_data = self.country_analyzer.analyze_country(
                focus_country_code, conference_name, year, track_name
            )
            
            # Generate institution analysis for focus country
            institution_data = self.institution_analyzer.analyze_institutions(
                conference_name, year, focus_country_code, track_name
            )
            
            # Build complete analytics structure
            analytics = self._build_analytics_structure(
                global_data, focus_country_data, institution_data,
                conference_name, year, focus_country_code, track_name
            )
            
            # Add dashboard content
            analytics["dashboard"] = self._generate_dashboard_content(
                analytics, focus_country_code
            )
            
            # Save to file if path provided
            if output_path:
                self._save_analytics(analytics, output_path)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            raise
    
    def _build_analytics_structure(self, global_data: Dict, focus_country_data: Dict,
                                 institution_data: Dict, conference_name: str,
                                 year: int, focus_country_code: str,
                                 track_name: str = None) -> Dict[str, Any]:
        """Build the complete analytics structure."""
        
        focus_country_name = COUNTRY_CODE_MAP.get(focus_country_code, focus_country_code)
        
        # Calculate percentages and rankings
        global_countries = global_data["globalStats"]["countries"]
        total_papers = sum(c["paper_count"] for c in global_countries)
        
        # Find focus country in global stats
        focus_country_global = next(
            (c for c in global_countries if c["affiliation_country"] == focus_country_code),
            {"paper_count": 0, "author_count": 0, "spotlights": 0, "orals": 0}
        )
        
        # Calculate rank
        sorted_countries = sorted(global_countries, key=lambda x: x["paper_count"], reverse=True)
        focus_rank = next(
            (i + 1 for i, c in enumerate(sorted_countries) if c["affiliation_country"] == focus_country_code),
            len(sorted_countries) + 1
        )
        
        # Calculate percentages
        focus_percentage = (focus_country_global["paper_count"] / total_papers * 100) if total_papers > 0 else 0
        
        analytics = {
            "conference": conference_name,
            "year": year,
            "track": track_name or "Conference",
            "focus_country": focus_country_name,
            "focus_country_code": focus_country_code,
            "generated_at": self._get_timestamp(),
            
            # Global statistics
            "globalStats": {
                "totalPapers": total_papers,
                "totalAuthors": global_data["conferenceInfo"]["totalAcceptedAuthors"],
                "totalCountries": len(global_countries),
                "countries": global_countries
            },
            
            # Focus country summary
            "focusCountrySummary": {
                "country": focus_country_name,
                "country_code": focus_country_code,
                "rank": focus_rank,
                "paper_count": focus_country_global["paper_count"],
                "author_count": focus_country_data["total_authors"],
                "percentage": round(focus_percentage, 2),
                "spotlights": focus_country_data["total_spotlights"],
                "orals": focus_country_data["total_orals"],
                "institution_count": len(focus_country_data["institutions"]),
                "academic_institutions": focus_country_data["institution_types"]["academic"],
                "corporate_institutions": focus_country_data["institution_types"]["corporate"]
            },
            
            # Focus country detailed analysis
            "focusCountry": {
                "authorship": {
                    "at_least_one": focus_country_data["at_least_one_focus_country_author"],
                    "majority": focus_country_data["majority_focus_country_authors"],
                    "first_author": focus_country_data["first_focus_country_author"]
                },
                "institutions": focus_country_data["institutions"]
            },
            
            # Institution analysis
            "institutions": {
                "summary": institution_data["summary"],
                "top_institutions": institution_data["topInstitutions"][:20],  # Top 20
                "total_institutions": institution_data["totalInstitutions"]
            },
            
            # Configuration and styling
            "config": {
                "focus_country_code": focus_country_code,
                "focus_country_name": focus_country_name,
                "colors": COLOR_SCHEME
            }
        }
        
        return analytics
    
    def _generate_dashboard_content(self, analytics: Dict, focus_country_code: str) -> Dict[str, Any]:
        """Generate dashboard content with narrative descriptions."""
        focus_country_name = COUNTRY_CODE_MAP.get(focus_country_code, focus_country_code)
        
        # Extract key metrics
        summary = analytics["focusCountrySummary"]
        global_stats = analytics["globalStats"]
        
        # Calculate additional metrics
        spotlight_percentage = (summary["spotlights"] / summary["paper_count"] * 100) if summary["paper_count"] > 0 else 0
        first_author_percentage = (analytics["focusCountry"]["authorship"]["first_author"]["count"] / summary["paper_count"] * 100) if summary["paper_count"] > 0 else 0
        majority_percentage = (analytics["focusCountry"]["authorship"]["majority"]["count"] / summary["paper_count"] * 100) if summary["paper_count"] > 0 else 0
        
        # Get top countries for context
        top_countries = sorted(global_stats["countries"], key=lambda x: x["paper_count"], reverse=True)
        us_percentage = next((c["paper_count"] / global_stats["totalPapers"] * 100 for c in top_countries if c["affiliation_country"] == "US"), 0)
        cn_percentage = next((c["paper_count"] / global_stats["totalPapers"] * 100 for c in top_countries if c["affiliation_country"] == "CN"), 0)
        gb_percentage = next((c["paper_count"] / global_stats["totalPapers"] * 100 for c in top_countries if c["affiliation_country"] == "GB"), 0)
        de_percentage = next((c["paper_count"] / global_stats["totalPapers"] * 100 for c in top_countries if c["affiliation_country"] == "DE"), 0)
        
        # Get top institution info
        top_institution = analytics["institutions"]["top_institutions"][0] if analytics["institutions"]["top_institutions"] else None
        
        dashboard = {}
        
        # Generate content for each section
        for section_key, section_config in DASHBOARD_SECTIONS.items():
            dashboard[section_key] = {
                "title": section_config["title"].format(country=focus_country_name),
                "content": []
            }
            
            if "subtitle" in section_config:
                dashboard[section_key]["subtitle"] = section_config["subtitle"].format(country=focus_country_name)
            
            # Format template strings with actual data
            for template in section_config["template"]:
                try:
                    formatted_content = template.format(
                        country=focus_country_name,
                        conference=analytics["conference"],
                        year=analytics["year"],
                        paper_count=summary["paper_count"],
                        percentage=round(summary["percentage"], 1),
                        rank=summary["rank"],
                        first_author_percentage=round(first_author_percentage, 1),
                        spotlight_percentage=round(spotlight_percentage, 1),
                        spotlight_count=summary["spotlights"],
                        author_count=summary["author_count"],
                        institution_count=summary["institution_count"],
                        academic_count=summary["academic_institutions"],
                        corporate_count=summary["corporate_institutions"],
                        us_percentage=round(us_percentage, 1),
                        cn_percentage=round(cn_percentage, 1),
                        gb_percentage=round(gb_percentage, 1),
                        de_percentage=round(de_percentage, 1),
                        majority_percentage=round(majority_percentage, 1),
                        ratio=round(summary["paper_count"] / summary["author_count"], 2) if summary["author_count"] > 0 else 0,
                        top_institution=top_institution["name"] if top_institution else "Unknown",
                        top_papers=top_institution["paper_count"] if top_institution else 0,
                        top_authors=top_institution["author_count"] if top_institution else 0,
                        spotlight_info="spotlight paper" if summary["spotlights"] == 1 else f"{summary['spotlights']} spotlight papers",
                        academic_percentage=round(summary["academic_institutions"] / summary["institution_count"] * 100, 1) if summary["institution_count"] > 0 else 0,
                        corporate_percentage=round(summary["corporate_institutions"] / summary["institution_count"] * 100, 1) if summary["institution_count"] > 0 else 0,
                        total_institutions=summary["institution_count"]
                    )
                    dashboard[section_key]["content"].append(formatted_content)
                except KeyError as e:
                    logger.warning(f"Missing template variable {e} in section {section_key}")
                    dashboard[section_key]["content"].append(template)  # Use template as-is if formatting fails
        
        return dashboard
    
    def _save_analytics(self, analytics: Dict, output_path: str):
        """Save analytics to JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analytics saved to {output_path}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_batch_analytics(self, conferences: List[Dict[str, Any]], 
                                output_dir: str, focus_country_code: str = "IN") -> Dict[str, str]:
        """
        Generate analytics for multiple conferences.
        
        Args:
            conferences: List of conference dictionaries with 'name', 'year', 'track' keys
            output_dir: Output directory for analytics files
            focus_country_code: Focus country code
            
        Returns:
            Dictionary mapping conference keys to output file paths
        """
        output_files = {}
        
        for conf in conferences:
            try:
                conference_name = conf["name"]
                year = conf["year"]
                track_name = conf.get("track")
                
                # Generate filename
                filename = f"{conference_name.lower()}-{year}-analytics.json"
                if track_name:
                    filename = f"{conference_name.lower()}-{year}-{track_name.lower()}-analytics.json"
                
                output_path = Path(output_dir) / filename
                
                # Generate analytics
                analytics = self.generate_analytics(
                    conference_name, year, focus_country_code, track_name, str(output_path)
                )
                
                output_files[f"{conference_name}-{year}"] = str(output_path)
                logger.info(f"Generated analytics for {conference_name} {year}")
                
            except Exception as e:
                logger.error(f"Failed to generate analytics for {conf}: {e}")
                continue
        
        return output_files
    
    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
