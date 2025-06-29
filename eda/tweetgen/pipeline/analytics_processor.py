"""
Analytics Processor for Tweet Generation Pipeline

Processes analytics data to generate insights for tweet content.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class AnalyticsProcessor:
    """Processes analytics data for tweet generation."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
    
    def process_analytics(self, analytics_file: str, conference_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process analytics data and generate insights."""
        print(f"📊 Processing analytics from {analytics_file}...")
        
        # Check if already processed
        if self.state_manager.checkpoint_exists("processed_analytics.json"):
            print("  ✅ Analytics already processed, loading from checkpoint...")
            return self.state_manager.load_checkpoint("processed_analytics.json")
        
        analytics_path = self.config.get_analytics_path()
        if not analytics_path.exists():
            raise FileNotFoundError(f"Analytics file not found: {analytics_path}")
        
        with open(analytics_path, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)
        
        # Process analytics
        processed = self._process_analytics_data(analytics_data, conference_info)
        
        # Save checkpoint
        self.state_manager.save_checkpoint("processed_analytics.json", processed)
        
        return processed
    
    def _process_analytics_data(self, analytics: Dict[str, Any], conference_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw analytics data into tweet-ready insights."""
        conference_info_data = analytics.get("conferenceInfo", {})
        global_stats = analytics.get("globalStats", {})
        focus_country = analytics.get("focusCountry", {})
        
        # Extract basic conference info
        conference_name = conference_info_data.get("name", conference_info.get("conference", "Unknown"))
        year = conference_info_data.get("year", conference_info.get("year", "Unknown"))
        total_papers = conference_info_data.get("totalAcceptedPapers", 0)
        total_authors = conference_info_data.get("totalAcceptedAuthors", 0)
        
        # Process global rankings
        countries = global_stats.get("countries", [])
        global_rankings = self._calculate_global_rankings(countries)
        
        # Process India-specific data
        india_data = self._process_india_data(focus_country, countries)
        
        # Calculate APAC rankings
        apac_rankings = self._calculate_apac_rankings(countries, analytics.get("configuration", {}).get("apacCountries", []))
        
        # Generate insights
        insights = self._generate_insights(
            conference_name, year, total_papers, total_authors,
            global_rankings, india_data, apac_rankings
        )
        
        processed = {
            "conference": {
                "name": conference_name,
                "year": year,
                "total_papers": total_papers,
                "total_authors": total_authors
            },
            "global_rankings": global_rankings,
            "india_data": india_data,
            "apac_rankings": apac_rankings,
            "insights": insights,
            "raw_analytics": analytics
        }
        
        return processed
    
    def _calculate_global_rankings(self, countries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate global rankings and statistics."""
        # Sort countries by paper count
        sorted_countries = sorted(countries, key=lambda x: x.get("paper_count", 0), reverse=True)
        
        # Find India's position
        india_rank = None
        india_data = None
        
        for i, country in enumerate(sorted_countries):
            if country.get("affiliation_country") == "IN":
                india_rank = i + 1
                india_data = country
                break
        
        # Calculate top countries
        top_5 = sorted_countries[:5]
        top_10 = sorted_countries[:10]
        
        # Calculate US + China combined percentage
        us_papers = next((c["paper_count"] for c in countries if c["affiliation_country"] == "US"), 0)
        cn_papers = next((c["paper_count"] for c in countries if c["affiliation_country"] == "CN"), 0)
        total_papers = sum(c["paper_count"] for c in countries)
        
        us_cn_percentage = ((us_papers + cn_papers) / total_papers * 100) if total_papers > 0 else 0
        
        return {
            "india_rank": india_rank,
            "india_data": india_data,
            "top_5_countries": top_5,
            "top_10_countries": top_10,
            "us_cn_combined": {
                "papers": us_papers + cn_papers,
                "percentage": us_cn_percentage
            },
            "total_countries": len(countries)
        }
    
    def _process_india_data(self, focus_country: Dict[str, Any], countries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process India-specific data."""
        # Get India's data from global stats
        india_global = next((c for c in countries if c["affiliation_country"] == "IN"), {})
        
        # Count spotlights and orals only for papers with Indian first authors
        spotlights_first_author = 0
        orals_first_author = 0
        
        # Get papers from focus country data
        focus_papers = focus_country.get("first_focus_country_author", {}).get("papers", [])
        
        for paper in focus_papers:
            if paper.get("isSpotlight", False):
                spotlights_first_author += 1
            if paper.get("isOral", False):
                orals_first_author += 1
        
        # Combine focus country data with global data
        india_data = {
            "total_papers": focus_country.get("at_least_one_focus_country_author", {}).get("count", 0),
            "total_authors": focus_country.get("total_authors", 0),
            "spotlights": spotlights_first_author,  # Only count when first author is Indian
            "orals": orals_first_author,  # Only count when first author is Indian
            "first_author_papers": focus_country.get("first_focus_country_author", {}).get("count", 0),
            "majority_author_papers": focus_country.get("majority_focus_country_authors", {}).get("count", 0),
            "institutions": {
                "academic": focus_country.get("institution_types", {}).get("academic", 0),
                "corporate": focus_country.get("institution_types", {}).get("corporate", 0),
                "total": len(focus_country.get("institutions", []))
            },
            "top_institutions": focus_country.get("institutions", [])[:5],
            "global_papers": india_global.get("paper_count", 0),
            "global_authors": india_global.get("author_count", 0)
        }
        
        return india_data
    
    def _calculate_apac_rankings(self, countries: List[Dict[str, Any]], apac_countries: List[str]) -> Dict[str, Any]:
        """Calculate APAC region rankings."""
        # Filter APAC countries
        apac_data = [c for c in countries if c.get("affiliation_country") in apac_countries]
        apac_sorted = sorted(apac_data, key=lambda x: x.get("paper_count", 0), reverse=True)
        
        # Find India's APAC rank
        india_apac_rank = None
        for i, country in enumerate(apac_sorted):
            if country.get("affiliation_country") == "IN":
                india_apac_rank = i + 1
                break
        
        # Calculate APAC totals
        apac_total_papers = sum(c["paper_count"] for c in apac_data)
        apac_total_authors = sum(c["author_count"] for c in apac_data)
        
        return {
            "india_rank": india_apac_rank,
            "top_apac_countries": apac_sorted[:5],
            "total_apac_papers": apac_total_papers,
            "total_apac_authors": apac_total_authors,
            "apac_countries_count": len(apac_data)
        }
    
    def _generate_insights(self, conference_name: str, year: int, total_papers: int, total_authors: int,
                          global_rankings: Dict[str, Any], india_data: Dict[str, Any], 
                          apac_rankings: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tweet-ready insights."""
        
        # Calculate acceptance rate for India
        india_acceptance_rate = (india_data["total_papers"] / total_papers * 100) if total_papers > 0 else 0
        
        # Generate opening tweet content
        opening_tweet = (
            f"🇮🇳 India @ {conference_name} {year} Thread 🧵\n\n"
            f"India had {india_data['total_papers']} papers accepted, "
            f"ranking #{global_rankings['india_rank']} globally with {india_acceptance_rate:.1f}% of total papers."
        )
        
        if apac_rankings["india_rank"]:
            opening_tweet += f" In APAC, India ranks #{apac_rankings['india_rank']}."
        
        if global_rankings["us_cn_combined"]["percentage"] > 0:
            opening_tweet += f"\n\nUS and China together had {global_rankings['us_cn_combined']['percentage']:.1f}% of papers."
        
        opening_tweet += "\n\nLet's dive into India's contributions! 👇"
        
        # Generate summary insights
        summary_insights = []
        
        if india_data["spotlights"] > 0 or india_data["orals"] > 0:
            quality_text = f"Quality highlights: {india_data['spotlights']} spotlights"
            if india_data["orals"] > 0:
                quality_text += f" and {india_data['orals']} oral presentations"
            summary_insights.append(quality_text)
        
        if india_data["first_author_papers"] > 0:
            summary_insights.append(f"{india_data['first_author_papers']} papers with Indian first authors")
        
        if india_data["majority_author_papers"] > 0:
            summary_insights.append(f"{india_data['majority_author_papers']} papers with majority Indian authors")
        
        # Institution insights
        if india_data["institutions"]["total"] > 0:
            inst_text = f"{india_data['institutions']['total']} institutions contributed"
            if india_data["institutions"]["academic"] > 0:
                inst_text += f" ({india_data['institutions']['academic']} academic"
                if india_data["institutions"]["corporate"] > 0:
                    inst_text += f", {india_data['institutions']['corporate']} corporate)"
                else:
                    inst_text += ")"
            summary_insights.append(inst_text)
        
        return {
            "opening_tweet": opening_tweet,
            "summary_insights": summary_insights,
            "acceptance_rate": india_acceptance_rate,
            "global_context": {
                "rank": global_rankings["india_rank"],
                "total_countries": global_rankings["total_countries"],
                "us_cn_dominance": global_rankings["us_cn_combined"]["percentage"]
            },
            "apac_context": {
                "rank": apac_rankings["india_rank"],
                "total_apac_countries": apac_rankings["apac_countries_count"]
            },
            "quality_metrics": {
                "spotlights": india_data["spotlights"],
                "orals": india_data["orals"],
                "total_quality": india_data["spotlights"] + india_data["orals"]
            }
        }
