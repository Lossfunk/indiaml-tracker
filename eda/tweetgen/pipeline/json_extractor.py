"""
JSON Data Extractor for Tweet Generation Pipeline

Extracts papers and authors from JSON files instead of SQLite database.
Uses the curated JSON data as the source of truth.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class JSONExtractor:
    """Extracts data from JSON files."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
    
    def extract_data(self, json_file: str) -> Dict[str, Any]:
        """Extract papers and authors from JSON file."""
        print(f"🔍 Extracting data from {json_file}...")
        
        # Check if already extracted
        if self.state_manager.checkpoint_exists("raw_papers.json") and \
           self.state_manager.checkpoint_exists("raw_authors.json"):
            print("  ✅ Data already extracted, loading from checkpoint...")
            papers = self.state_manager.load_checkpoint("raw_papers.json")
            authors = self.state_manager.load_checkpoint("raw_authors.json")
            return {"papers": papers, "authors": authors}
        
        # Load JSON data
        json_path = self.config.get_json_path()
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        print(f"  📄 Loaded {len(raw_data)} papers from JSON")
        
        # Process papers and authors
        papers = self._process_papers(raw_data)
        authors = self._process_authors(raw_data)
        
        print(f"  📄 Processed {len(papers)} papers with Indian involvement")
        print(f"  👥 Found {len(authors)} unique authors")
        
        # Save checkpoints
        self.state_manager.save_checkpoint("raw_papers.json", papers)
        self.state_manager.save_checkpoint("raw_authors.json", authors)
        
        # Update progress
        self.state_manager.update_progress(
            total_papers=len(papers),
            total_authors=len(authors)
        )
        
        return {"papers": papers, "authors": authors}
    
    def _process_papers(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process papers from JSON data."""
        papers = []
        
        for i, paper_data in enumerate(raw_data):
            # Convert JSON format to our internal format
            paper = {
                "id": paper_data.get("paper_id", f"paper_{i}"),
                "title": paper_data.get("paper_title", ""),
                "status": "accepted",  # All papers in JSON are accepted
                "pdf_url": paper_data.get("pdf_url", ""),
                "pdf_path": None,
                "pdate": None,
                "odate": None,
                "raw_authors": None,
                "conference": self._extract_conference_from_config(),
                "year": self._extract_year_from_config(),
                "track": None,
                "top_author_from_india": paper_data.get("top_author_from_india", False),
                "majority_authors_from_india": paper_data.get("majority_authors_from_india", False),
                "paper_content": paper_data.get("paper_content", ""),
                "authors": self._process_paper_authors(paper_data.get("author_list", []), i)
            }
            papers.append(paper)
        
        return papers
    
    def _process_paper_authors(self, author_list: List[Dict[str, Any]], paper_index: int) -> List[Dict[str, Any]]:
        """Process authors for a specific paper."""
        authors = []
        
        for pos, author_data in enumerate(author_list):
            author = {
                "author_id": f"author_{paper_index}_{pos}",  # Generate unique ID
                "position": pos,
                "full_name": author_data.get("name", ""),
                "affiliation_name": author_data.get("affiliation_name", ""),
                "affiliation_domain": author_data.get("affiliation_domain", ""),
                "affiliation_country": author_data.get("affiliation_country", ""),
                "openreview_id": author_data.get("openreview_id", ""),
                "google_scholar_link": None,
                "linkedin": None,
                "homepage": None
            }
            authors.append(author)
        
        return authors
    
    def _process_authors(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process unique authors from all papers."""
        authors_dict = {}
        
        for paper_index, paper_data in enumerate(raw_data):
            author_list = paper_data.get("author_list", [])
            
            for pos, author_data in enumerate(author_list):
                # Create a unique key based on name and affiliation
                name = author_data.get("name", "").strip()
                affiliation = author_data.get("affiliation_name", "").strip()
                
                # Skip empty names
                if not name:
                    continue
                
                author_key = f"{name}_{affiliation}"
                
                if author_key not in authors_dict:
                    author_id = f"author_{paper_index}_{pos}"
                    authors_dict[author_key] = {
                        "id": author_id,
                        "full_name": name,
                        "email": None,
                        "openreview_id": author_data.get("openreview_id", ""),
                        "orcid": None,
                        "google_scholar_link": None,
                        "linkedin": None,
                        "homepage": None,
                        "affiliation_history": None,
                        "papers": []
                    }
                
                # Add paper information to author
                paper_info = {
                    "paper_id": paper_data.get("paper_id", f"paper_{paper_index}"),
                    "position": pos,
                    "affiliation_name": affiliation,
                    "affiliation_domain": author_data.get("affiliation_domain", ""),
                    "affiliation_state_province": None,
                    "affiliation_country": author_data.get("affiliation_country", "")
                }
                
                authors_dict[author_key]["papers"].append(paper_info)
        
        return list(authors_dict.values())
    
    def get_conference_info(self, json_file: str) -> Dict[str, Any]:
        """Extract conference information from config."""
        return {
            "conference": self._extract_conference_from_config(),
            "year": self._extract_year_from_config(),
            "track": None
        }
    
    def get_paper_statistics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the papers."""
        total_papers = len(papers)
        
        # Count papers by different criteria
        first_author_indian = sum(1 for p in papers if p.get("top_author_from_india", False))
        majority_indian = sum(1 for p in papers if p.get("majority_authors_from_india", False))
        
        # Count unique Indian authors
        indian_authors = set()
        for paper in papers:
            for author in paper.get("authors", []):
                if author.get("affiliation_country") == "IN":
                    # Use name + affiliation as unique key
                    author_key = f"{author['full_name']}_{author['affiliation_name']}"
                    indian_authors.add(author_key)
        
        return {
            "total_papers": total_papers,
            "total_indian_authors": len(indian_authors),
            "first_author_indian": first_author_indian,
            "majority_indian": majority_indian,
            "status_distribution": {"accepted": total_papers}  # All papers are accepted
        }
    
    def _extract_conference_from_config(self) -> str:
        """Extract conference name from config."""
        conference = self.config.conference.upper()
        if "ICML" in conference:
            return "ICML"
        elif "ICLR" in conference:
            return "ICLR"
        elif "NEURIPS" in conference:
            return "NeurIPS"
        else:
            return conference.split("-")[0]
    
    def _extract_year_from_config(self) -> int:
        """Extract year from config."""
        conference = self.config.conference
        # Extract year from conference string like "icml-2025"
        parts = conference.split("-")
        for part in parts:
            if part.isdigit() and len(part) == 4:
                return int(part)
        return 2025  # Default fallback
