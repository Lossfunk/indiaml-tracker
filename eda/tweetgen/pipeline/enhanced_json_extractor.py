"""
Enhanced JSON Data Extractor for Tweet Generation Pipeline

Automatically detects and adapts to different JSON schemas.
Provides flexible field mapping and robust error handling.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from .state_manager import StateManager


class EnhancedJSONExtractor:
    """Enhanced JSON extractor with automatic schema detection."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        self.detected_schema = None
        
        # Field mapping for different naming conventions
        self.field_mappings = {
            'title': ['title', 'paper_title', 'name', 'paper_name'],
            'authors': ['authors', 'author_list', 'paper_authors'],
            'conference': ['conference', 'venue', 'conference_name'],
            'year': ['year', 'conference_year', 'publication_year'],
            'presentation_type': ['presentation_type', 'paper_type', 'type', 'category'],
            'paper_id': ['paper_id', 'id', 'paper_identifier', 'openreview_id'],
            'pdf_url': ['pdf_url', 'pdf_link', 'paper_url', 'url'],
            'abstract': ['abstract', 'summary', 'description'],
            'keywords': ['keywords', 'tags', 'categories'],
            'track': ['track', 'session', 'area']
        }
        
        # Author field mappings
        self.author_field_mappings = {
            'name': ['name', 'full_name', 'author_name', 'first_name', 'last_name'],
            'affiliation': ['affiliation', 'affiliation_name', 'institution', 'organization'],
            'affiliation_country': ['affiliation_country', 'country', 'country_code'],
            'affiliation_domain': ['affiliation_domain', 'domain', 'email_domain'],
            'email': ['email', 'email_address', 'contact_email'],
            'homepage': ['homepage', 'website', 'personal_page', 'url'],
            'google_scholar': ['google_scholar', 'scholar_url', 'scholar_link'],
            'linkedin': ['linkedin', 'linkedin_url', 'linkedin_profile'],
            'twitter': ['twitter', 'twitter_handle', 'twitter_url'],
            'orcid': ['orcid', 'orcid_id', 'orcid_url'],
            'openreview_id': ['openreview_id', 'openreview', 'or_id'],
            'flag': ['flag', 'country_flag', 'emoji_flag']
        }
    
    def extract_data(self, json_file: str) -> Dict[str, Any]:
        """Extract papers and authors from JSON file with automatic schema detection."""
        print(f"🔍 Enhanced extraction from {json_file}...")
        
        # Check if already extracted
        if self.state_manager.checkpoint_exists("raw_papers.json") and \
           self.state_manager.checkpoint_exists("raw_authors.json"):
            print("  ✅ Data already extracted, loading from checkpoint...")
            papers = self.state_manager.load_checkpoint("raw_papers.json")
            authors = self.state_manager.load_checkpoint("raw_authors.json")
            return {"papers": papers, "authors": authors}
        
        # Load and detect JSON schema
        json_path = self.config.get_json_path()
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Detect and validate schema
        self.detected_schema = self._detect_schema(raw_data)
        print(f"  📋 Detected schema: {self.detected_schema['type']}")
        print(f"  📊 Found {self.detected_schema['paper_count']} papers")
        
        # Extract papers based on detected schema
        papers_data = self._extract_papers_by_schema(raw_data)
        
        # Process papers and authors
        papers = self._process_papers(papers_data)
        authors = self._process_authors(papers_data)
        
        print(f"  📄 Processed {len(papers)} papers")
        print(f"  👥 Found {len(authors)} unique authors")
        
        # Save checkpoints
        self.state_manager.save_checkpoint("raw_papers.json", papers)
        self.state_manager.save_checkpoint("raw_authors.json", authors)
        self.state_manager.save_checkpoint("detected_schema.json", self.detected_schema)
        
        # Update progress
        self.state_manager.update_progress(
            total_papers=len(papers),
            total_authors=len(authors)
        )
        
        return {"papers": papers, "authors": authors}
    
    def _detect_schema(self, raw_data: Any) -> Dict[str, Any]:
        """Automatically detect the JSON schema structure."""
        schema_info = {
            'type': 'unknown',
            'paper_count': 0,
            'has_authors': False,
            'author_structure': 'unknown',
            'field_mappings': {},
            'confidence': 0.0
        }
        
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and isinstance(raw_data[0], dict):
                # Array of paper objects
                schema_info['type'] = 'paper_array'
                schema_info['paper_count'] = len(raw_data)
                schema_info['field_mappings'] = self._analyze_paper_fields(raw_data[0])
                schema_info['has_authors'] = self._detect_authors_in_paper(raw_data[0])
                if schema_info['has_authors']:
                    schema_info['author_structure'] = self._analyze_author_structure(raw_data[0])
                schema_info['confidence'] = 0.9
            else:
                schema_info['type'] = 'simple_array'
                schema_info['paper_count'] = len(raw_data)
                schema_info['confidence'] = 0.3
        
        elif isinstance(raw_data, dict):
            # Check for common container keys
            container_keys = ['papers', 'data', 'results', 'items', 'documents']
            for key in container_keys:
                if key in raw_data and isinstance(raw_data[key], list):
                    schema_info['type'] = f'object_with_{key}'
                    schema_info['paper_count'] = len(raw_data[key])
                    if raw_data[key]:
                        schema_info['field_mappings'] = self._analyze_paper_fields(raw_data[key][0])
                        schema_info['has_authors'] = self._detect_authors_in_paper(raw_data[key][0])
                        if schema_info['has_authors']:
                            schema_info['author_structure'] = self._analyze_author_structure(raw_data[key][0])
                    schema_info['confidence'] = 0.8
                    break
            
            if schema_info['type'] == 'unknown':
                # Single paper object
                if self._looks_like_paper(raw_data):
                    schema_info['type'] = 'single_paper'
                    schema_info['paper_count'] = 1
                    schema_info['field_mappings'] = self._analyze_paper_fields(raw_data)
                    schema_info['has_authors'] = self._detect_authors_in_paper(raw_data)
                    if schema_info['has_authors']:
                        schema_info['author_structure'] = self._analyze_author_structure(raw_data)
                    schema_info['confidence'] = 0.7
        
        return schema_info
    
    def _analyze_paper_fields(self, paper_sample: Dict[str, Any]) -> Dict[str, str]:
        """Analyze paper fields and create mapping."""
        field_mapping = {}
        
        for standard_field, possible_names in self.field_mappings.items():
            for possible_name in possible_names:
                if possible_name in paper_sample:
                    field_mapping[standard_field] = possible_name
                    break
        
        return field_mapping
    
    def _detect_authors_in_paper(self, paper_sample: Dict[str, Any]) -> bool:
        """Check if paper contains author information."""
        for possible_name in self.field_mappings['authors']:
            if possible_name in paper_sample:
                authors_data = paper_sample[possible_name]
                return isinstance(authors_data, list) and len(authors_data) > 0
        return False
    
    def _analyze_author_structure(self, paper_sample: Dict[str, Any]) -> str:
        """Analyze the structure of author data."""
        for possible_name in self.field_mappings['authors']:
            if possible_name in paper_sample:
                authors_data = paper_sample[possible_name]
                if isinstance(authors_data, list) and len(authors_data) > 0:
                    first_author = authors_data[0]
                    if isinstance(first_author, dict):
                        return 'object_array'
                    elif isinstance(first_author, str):
                        return 'string_array'
        return 'unknown'
    
    def _looks_like_paper(self, obj: Dict[str, Any]) -> bool:
        """Check if an object looks like a paper."""
        # Look for common paper fields
        paper_indicators = ['title', 'paper_title', 'authors', 'author_list']
        found_indicators = sum(1 for indicator in paper_indicators if indicator in obj)
        return found_indicators >= 1
    
    def _extract_papers_by_schema(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Extract papers based on detected schema."""
        schema_type = self.detected_schema['type']
        
        if schema_type == 'paper_array':
            return raw_data
        elif schema_type.startswith('object_with_'):
            container_key = schema_type.split('_')[-1]
            return raw_data[container_key]
        elif schema_type == 'single_paper':
            return [raw_data]
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")
    
    def _process_papers(self, papers_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process papers using detected field mappings."""
        papers = []
        field_mapping = self.detected_schema['field_mappings']
        
        for i, paper_data in enumerate(papers_data):
            paper = {
                "id": self._get_mapped_field(paper_data, 'paper_id', field_mapping) or f"paper_{i}",
                "title": self._get_mapped_field(paper_data, 'title', field_mapping) or "Untitled",
                "status": "accepted",  # Assume all papers are accepted
                "pdf_url": self._get_mapped_field(paper_data, 'pdf_url', field_mapping),
                "pdf_path": None,
                "pdate": None,
                "odate": None,
                "raw_authors": None,
                "conference": self._get_mapped_field(paper_data, 'conference', field_mapping) or self._extract_conference_from_config(),
                "year": self._get_mapped_field(paper_data, 'year', field_mapping) or self._extract_year_from_config(),
                "track": self._get_mapped_field(paper_data, 'track', field_mapping),
                "presentation_type": self._get_mapped_field(paper_data, 'presentation_type', field_mapping) or "Research Paper",
                "abstract": self._get_mapped_field(paper_data, 'abstract', field_mapping),
                "keywords": self._get_mapped_field(paper_data, 'keywords', field_mapping),
                "top_author_from_india": self._check_indian_first_author(paper_data, field_mapping),
                "majority_authors_from_india": self._check_majority_indian_authors(paper_data, field_mapping),
                "authors": self._process_paper_authors(paper_data, field_mapping, i)
            }
            papers.append(paper)
        
        return papers
    
    def _get_mapped_field(self, data: Dict[str, Any], field_name: str, field_mapping: Dict[str, str]) -> Any:
        """Get field value using mapping."""
        mapped_name = field_mapping.get(field_name)
        if mapped_name and mapped_name in data:
            return data[mapped_name]
        return None
    
    def _process_paper_authors(self, paper_data: Dict[str, Any], field_mapping: Dict[str, str], paper_index: int) -> List[Dict[str, Any]]:
        """Process authors for a specific paper."""
        authors = []
        authors_data = self._get_mapped_field(paper_data, 'authors', field_mapping)
        
        if not authors_data:
            return authors
        
        author_structure = self.detected_schema['author_structure']
        
        for pos, author_data in enumerate(authors_data):
            if author_structure == 'string_array':
                # Simple string array
                author = {
                    "author_id": f"author_{paper_index}_{pos}",
                    "position": pos,
                    "full_name": str(author_data),
                    "affiliation_name": "",
                    "affiliation_domain": "",
                    "affiliation_country": "",
                    "openreview_id": "",
                    "google_scholar_link": None,
                    "linkedin": None,
                    "homepage": None,
                    "flag": None
                }
            else:
                # Object array
                author = {
                    "author_id": f"author_{paper_index}_{pos}",
                    "position": pos,
                    "full_name": self._get_author_field(author_data, 'name'),
                    "affiliation_name": self._get_author_field(author_data, 'affiliation'),
                    "affiliation_domain": self._get_author_field(author_data, 'affiliation_domain'),
                    "affiliation_country": self._get_author_field(author_data, 'affiliation_country'),
                    "openreview_id": self._get_author_field(author_data, 'openreview_id'),
                    "google_scholar_link": self._get_author_field(author_data, 'google_scholar'),
                    "linkedin": self._get_author_field(author_data, 'linkedin'),
                    "homepage": self._get_author_field(author_data, 'homepage'),
                    "email": self._get_author_field(author_data, 'email'),
                    "orcid": self._get_author_field(author_data, 'orcid'),
                    "twitter": self._get_author_field(author_data, 'twitter'),
                    "flag": self._get_author_field(author_data, 'flag')
                }
            
            authors.append(author)
        
        return authors
    
    def _get_author_field(self, author_data: Union[Dict[str, Any], str], field_name: str) -> Optional[str]:
        """Get author field value using mapping."""
        if isinstance(author_data, str):
            return author_data if field_name == 'name' else None
        
        if not isinstance(author_data, dict):
            return None
        
        possible_names = self.author_field_mappings.get(field_name, [])
        for possible_name in possible_names:
            if possible_name in author_data:
                return author_data[possible_name]
        return None
    
    def _check_indian_first_author(self, paper_data: Dict[str, Any], field_mapping: Dict[str, str]) -> bool:
        """Check if first author is from India."""
        authors_data = self._get_mapped_field(paper_data, 'authors', field_mapping)
        if authors_data and len(authors_data) > 0:
            first_author = authors_data[0]
            country = self._get_author_field(first_author, 'affiliation_country')
            flag = self._get_author_field(first_author, 'flag')
            return country == 'IN' or country == 'India' or flag == '🇮🇳'
        return False
    
    def _check_majority_indian_authors(self, paper_data: Dict[str, Any], field_mapping: Dict[str, str]) -> bool:
        """Check if majority of authors are from India."""
        authors_data = self._get_mapped_field(paper_data, 'authors', field_mapping)
        if not authors_data:
            return False
        
        indian_count = 0
        for author in authors_data:
            country = self._get_author_field(author, 'affiliation_country')
            flag = self._get_author_field(author, 'flag')
            if country == 'IN' or country == 'India' or flag == '🇮🇳':
                indian_count += 1
        
        return indian_count > len(authors_data) / 2
    
    def _process_authors(self, papers_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process unique authors from all papers."""
        authors_dict = {}
        field_mapping = self.detected_schema['field_mappings']
        
        for paper_index, paper_data in enumerate(papers_data):
            authors_data = self._get_mapped_field(paper_data, 'authors', field_mapping)
            if not authors_data:
                continue
            
            for pos, author_data in enumerate(authors_data):
                name = self._get_author_field(author_data, 'name') or ""
                affiliation = self._get_author_field(author_data, 'affiliation') or ""
                
                if not name.strip():
                    continue
                
                # Create unique key
                author_key = f"{name.strip()}_{affiliation.strip()}"
                
                if author_key not in authors_dict:
                    author_id = f"author_{paper_index}_{pos}"
                    authors_dict[author_key] = {
                        "id": author_id,
                        "full_name": name.strip(),
                        "email": self._get_author_field(author_data, 'email'),
                        "openreview_id": self._get_author_field(author_data, 'openreview_id'),
                        "orcid": self._get_author_field(author_data, 'orcid'),
                        "google_scholar_link": self._get_author_field(author_data, 'google_scholar'),
                        "linkedin": self._get_author_field(author_data, 'linkedin'),
                        "homepage": self._get_author_field(author_data, 'homepage'),
                        "twitter": self._get_author_field(author_data, 'twitter'),
                        "affiliation_history": None,
                        "papers": []
                    }
                
                # Add paper information
                paper_info = {
                    "paper_id": self._get_mapped_field(paper_data, 'paper_id', field_mapping) or f"paper_{paper_index}",
                    "position": pos,
                    "affiliation_name": affiliation,
                    "affiliation_domain": self._get_author_field(author_data, 'affiliation_domain'),
                    "affiliation_state_province": None,
                    "affiliation_country": self._get_author_field(author_data, 'affiliation_country')
                }
                
                authors_dict[author_key]["papers"].append(paper_info)
        
        return list(authors_dict.values())
    
    def get_conference_info(self, json_file: str) -> Dict[str, Any]:
        """Extract conference information."""
        return {
            "conference": self._extract_conference_from_config(),
            "year": self._extract_year_from_config(),
            "track": None
        }
    
    def get_paper_statistics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the papers."""
        total_papers = len(papers)
        first_author_indian = sum(1 for p in papers if p.get("top_author_from_india", False))
        majority_indian = sum(1 for p in papers if p.get("majority_authors_from_india", False))
        
        # Count unique Indian authors
        indian_authors = set()
        for paper in papers:
            for author in paper.get("authors", []):
                country = author.get("affiliation_country", "")
                if country == "IN" or country == "India":
                    author_key = f"{author['full_name']}_{author['affiliation_name']}"
                    indian_authors.add(author_key)
        
        return {
            "total_papers": total_papers,
            "total_indian_authors": len(indian_authors),
            "first_author_indian": first_author_indian,
            "majority_indian": majority_indian,
            "status_distribution": {"accepted": total_papers},
            "schema_info": self.detected_schema
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
        parts = conference.split("-")
        for part in parts:
            if part.isdigit() and len(part) == 4:
                return int(part)
        return 2025
