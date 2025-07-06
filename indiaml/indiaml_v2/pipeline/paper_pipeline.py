import sqlite3
import json
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuration for the transformation pipeline"""
    # Weights for sorting algorithm
    first_author_weight: float = 3.0
    last_author_weight: float = 2.0
    middle_author_weight: float = 1.0
    
    # Status weights (higher = better)
    status_weights: Dict[str, float] = None
    
    # Output settings
    output_format: str = "json"  # "json" or "csv"
    include_review_details: bool = True
    include_citation_data: bool = True
    
    def __post_init__(self):
        if self.status_weights is None:
            self.status_weights = {
                'oral': 10.0,
                'spotlight': 8.0,
                'poster': 5.0,
                'unknown': 1.0
            }

class StatusNormalizer:
    """Normalizes paper status values to standard categories"""
    
    STATUS_MAPPING = {
        'oral': 'oral',
        'oral workshop': 'oral',
        'talk': 'oral',
        'top-5%': 'oral',
        
        'spotlight': 'spotlight',
        'top-25%': 'spotlight',
        
        'poster': 'poster',
        'poster workshop': 'poster',
        'active': 'poster',  # Assuming active means accepted as poster
        
        # Rejected/withdrawn papers
        'desk reject': 'rejected',
        'reject': 'rejected',
        'withdraw': 'withdrawn'
    }
    
    @classmethod
    def normalize_status(cls, status: str) -> str:
        """Normalize status to standard categories"""
        if not status:
            return 'unknown'
        
        status_clean = status.lower().strip()
        return cls.STATUS_MAPPING.get(status_clean, 'unknown')

class CountryCodeMapper:
    """Maps country names to 2-letter ISO codes"""
    
    COUNTRY_CODES = {
        'united states': 'US',
        'usa': 'US',
        'united states of america': 'US',
        'china': 'CN',
        'united kingdom': 'GB',
        'uk': 'GB',
        'germany': 'DE',
        'france': 'FR',
        'japan': 'JP',
        'canada': 'CA',
        'australia': 'AU',
        'india': 'IN',
        'south korea': 'KR',
        'korea': 'KR',
        'netherlands': 'NL',
        'switzerland': 'CH',
        'sweden': 'SE',
        'italy': 'IT',
        'spain': 'ES',
        'singapore': 'SG',
        'israel': 'IL',
        'brazil': 'BR',
        'russia': 'RU',
        'taiwan': 'TW',
        'hong kong': 'HK',
        'norway': 'NO',
        'denmark': 'DK',
        'finland': 'FI',
        'austria': 'AT',
        'belgium': 'BE',
        'portugal': 'PT',
        'czech republic': 'CZ',
        'poland': 'PL',
        'hungary': 'HU',
        'greece': 'GR',
        'turkey': 'TR',
        'mexico': 'MX',
        'argentina': 'AR',
        'chile': 'CL',
        'colombia': 'CO',
        'south africa': 'ZA',
        'new zealand': 'NZ',
        'ireland': 'IE',
        'thailand': 'TH',
        'malaysia': 'MY',
        'indonesia': 'ID',
        'philippines': 'PH',
        'vietnam': 'VN',
        'egypt': 'EG',
        'iran': 'IR',
        'saudi arabia': 'SA',
        'united arab emirates': 'AE',
        'uae': 'AE'
    }
    
    @classmethod
    def get_country_code(cls, country_name: str) -> str:
        """Get 2-letter country code from country name"""
        if not country_name:
            return 'UN'  # Unknown
        
        country_clean = country_name.lower().strip()
        return cls.COUNTRY_CODES.get(country_clean, 'UN')

class SortingCalculator:
    """Calculates sorting scores for papers based on author position and paper status"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    def calculate_author_position_weight(self, author_position: int, total_authors: int) -> float:
        """
        Calculate weight based on author position
        First author gets highest weight, last author gets second highest
        """
        # Handle edge cases
        if total_authors <= 0:
            raise ValueError("Total authors must be greater than 0")
        
        if author_position <= 0 or author_position > total_authors:
            raise ValueError(f"Author position {author_position} is invalid for {total_authors} total authors")
        
        if total_authors == 1:
            return self.config.first_author_weight
        
        if author_position == 1:  # First author
            return self.config.first_author_weight
        elif author_position == total_authors:  # Last author
            return self.config.last_author_weight
        else:  # Middle authors
            # Gradual decrease for middle authors
            middle_factor = 1 - ((author_position - 1) / (total_authors - 1))
            return self.config.middle_author_weight * middle_factor
    
    def calculate_paper_score(self, status: str, author_position: int, total_authors: int) -> float:
        """
        Calculate overall score for a paper-author combination
        Higher score = higher priority
        """
        normalized_status = StatusNormalizer.normalize_status(status)
        
        # Skip rejected/withdrawn papers
        if normalized_status in ['rejected', 'withdrawn']:
            return 0.0
        
        try:
            status_weight = self.config.status_weights.get(normalized_status, 1.0)
            author_weight = self.calculate_author_position_weight(author_position, total_authors)
            
            # Combine weights multiplicatively to emphasize both factors
            return status_weight * author_weight
            
        except ValueError as e:
            # Log the error but return 0 to handle gracefully in production
            import logging
            logging.warning(f"Invalid paper scoring inputs: status='{status}', position={author_position}, total={total_authors}. Error: {e}")
            return 0.0

class PaperDataPipeline:
    """Main pipeline for transforming academic paper data"""
    
    def __init__(self, db_path: str, config: PipelineConfig = None):
        self.db_path = db_path
        self.config = config or PipelineConfig()
        self.calculator = SortingCalculator(self.config)
        
    def get_database_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def get_focus_country_authors(self, focus_country: str) -> List[str]:
        """Get all author IDs who have at least one affiliation from focus country"""
        conn = self.get_database_connection()
        
        query = """
        SELECT DISTINCT a.id
        FROM authors a
        JOIN affiliations af ON a.id = af.author_id
        JOIN institutions i ON af.institution_id = i.id
        JOIN countries c ON i.country_id = c.id
        WHERE LOWER(c.name) = LOWER(?)
        """
        
        try:
            cursor = conn.execute(query, (focus_country,))
            author_ids = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(author_ids)} authors from {focus_country}")
            return author_ids
        finally:
            conn.close()
    
    def get_papers_by_conference(self, focus_country_authors: List[str]) -> Dict[str, List[Dict]]:
        """Get papers organized by conference, filtered by focus country authors"""
        if not focus_country_authors:
            return {}
        
        conn = self.get_database_connection()
        
        # Create placeholders for the IN clause
        placeholders = ','.join(['?' for _ in focus_country_authors])
        
        query = f"""
        SELECT DISTINCT
            conf.name as conference_name,
            conf.year as conference_year,
            t.name as track_name,
            p.id as paper_id,
            p.title,
            p.status,
            p.abstract,
            p.tldr,
            p.site_url,
            p.pdf_url,
            p.github_url,
            p.author_count,
            pa.author_order,
            pa.author_id,
            a.name as author_name,
            a.name_site as author_name_site,
            a.openreview_id as author_openreview_id,
            a.gender as author_gender,
            a.homepage_url as author_homepage,
            a.dblp_id as author_dblp_id,
            a.google_scholar_url as author_scholar,
            a.orcid as author_orcid,
            a.linkedin_url as author_linkedin,
            a.twitter_url as author_twitter,
            a.primary_email as author_email,
            GROUP_CONCAT(DISTINCT inst.name || ' (' || c.name || ')') as affiliations,
            GROUP_CONCAT(DISTINCT c.name) as countries,
            GROUP_CONCAT(DISTINCT c.code) as country_codes
        FROM papers p
        JOIN paper_authors pa ON p.id = pa.paper_id
        JOIN authors a ON pa.author_id = a.id
        JOIN tracks t ON p.track_id = t.id
        JOIN conferences conf ON t.conference_id = conf.id
        LEFT JOIN paper_author_affiliations paa ON pa.id = paa.paper_author_id
        LEFT JOIN affiliations af ON paa.affiliation_id = af.id
        LEFT JOIN institutions inst ON af.institution_id = inst.id
        LEFT JOIN countries c ON inst.country_id = c.id
        WHERE pa.author_id IN ({placeholders})
        GROUP BY p.id, pa.author_id, pa.author_order
        ORDER BY conf.year DESC, conf.name, p.id, pa.author_order
        """
        
        try:
            cursor = conn.execute(query, focus_country_authors)
            rows = cursor.fetchall()
            
            papers_by_conference = {}
            for row in rows:
                conf_key = f"{row['conference_name']} {row['conference_year']}"
                if conf_key not in papers_by_conference:
                    papers_by_conference[conf_key] = []
                
                # Add country codes
                countries = row['countries'].split(',') if row['countries'] else []
                country_codes = [CountryCodeMapper.get_country_code(c.strip()) for c in countries]
                
                paper_data = {
                    'paper_id': row['paper_id'],
                    'title': row['title'],
                    'status': row['status'],
                    'normalized_status': StatusNormalizer.normalize_status(row['status']),
                    'abstract': row['abstract'],
                    'tldr': row['tldr'],
                    'site_url': row['site_url'],
                    'pdf_url': row['pdf_url'],
                    'github_url': row['github_url'],
                    'total_authors': row['author_count'],
                    'track_name': row['track_name'],
                    'author': {
                        'id': row['author_id'],
                        'name': row['author_name'],
                        'name_site': row['author_name_site'],
                        'openreview_id': row['author_openreview_id'],
                        'position': row['author_order'],
                        'gender': row['author_gender'],
                        'homepage_url': row['author_homepage'],
                        'dblp_id': row['author_dblp_id'],
                        'google_scholar_url': row['author_scholar'],
                        'orcid': row['author_orcid'],
                        'linkedin_url': row['author_linkedin'],
                        'twitter_url': row['author_twitter'],
                        'primary_email': row['author_email'],
                        'affiliations': row['affiliations'],
                        'countries': countries,
                        'country_codes': list(set(country_codes))
                    },
                    'sort_score': self.calculator.calculate_paper_score(
                        row['status'], 
                        row['author_order'], 
                        row['author_count']
                    )
                }
                
                papers_by_conference[conf_key].append(paper_data)
            
            logger.info(f"Found papers in {len(papers_by_conference)} conferences")
            return papers_by_conference
            
        finally:
            conn.close()
    
    def get_review_data(self, paper_ids: List[str]) -> Dict[str, Dict]:
        """Get review statistics for papers"""
        if not paper_ids:
            return {}
        
        conn = self.get_database_connection()
        placeholders = ','.join(['?' for _ in paper_ids])
        
        query = f"""
        SELECT 
            rs.paper_id,
            rs.rating_mean,
            rs.rating_std,
            rs.confidence_mean,
            rs.confidence_std,
            rs.total_reviews,
            rs.total_reviewers,
            c.google_scholar_citations,
            c.semantic_scholar_citations
        FROM review_statistics rs
        LEFT JOIN citations c ON rs.paper_id = c.paper_id
        WHERE rs.paper_id IN ({placeholders})
        """
        
        try:
            cursor = conn.execute(query, paper_ids)
            reviews = {}
            for row in cursor.fetchall():
                reviews[row['paper_id']] = {
                    'rating_mean': row['rating_mean'],
                    'rating_std': row['rating_std'],
                    'confidence_mean': row['confidence_mean'],
                    'confidence_std': row['confidence_std'],
                    'total_reviews': row['total_reviews'],
                    'total_reviewers': row['total_reviewers'],
                    'google_scholar_citations': row['google_scholar_citations'] or 0,
                    'semantic_scholar_citations': row['semantic_scholar_citations'] or 0
                }
            return reviews
        finally:
            conn.close()
    
    def process_and_export(self, focus_country: str, output_dir: str) -> Dict[str, str]:
        """Main processing pipeline"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get focus country authors
        focus_authors = self.get_focus_country_authors(focus_country)
        if not focus_authors:
            raise ValueError(f"No authors found from {focus_country}")
        
        # Get papers by conference
        papers_by_conf = self.get_papers_by_conference(focus_authors)
        
        # Get all unique paper IDs for review data
        all_paper_ids = []
        for conf_papers in papers_by_conf.values():
            all_paper_ids.extend([p['paper_id'] for p in conf_papers])
        all_paper_ids = list(set(all_paper_ids))
        
        # Get review data
        review_data = self.get_review_data(all_paper_ids)
        
        # Process and sort papers for each conference
        output_files = {}
        
        for conf_name, papers in papers_by_conf.items():
            # Add review data to papers
            papers_with_reviews = []
            for paper in papers:
                paper_id = paper['paper_id']
                if paper_id in review_data:
                    paper['reviews'] = review_data[paper_id]
                papers_with_reviews.append(paper)
            
            # Sort papers by score (highest first)
            sorted_papers = sorted(papers_with_reviews, 
                                 key=lambda x: x['sort_score'], 
                                 reverse=True)
            
            # Create output
            output_data = {
                'conference': conf_name,
                'focus_country': focus_country,
                'total_papers': len(sorted_papers),
                'generated_at': datetime.now().isoformat(),
                'config': asdict(self.config),
                'papers': sorted_papers
            }
            
            # Save to file
            safe_conf_name = re.sub(r'[^\w\s-]', '', conf_name).strip()
            safe_conf_name = re.sub(r'[-\s]+', '_', safe_conf_name)
            
            if self.config.output_format == 'json':
                filename = f"{safe_conf_name}.json"
                filepath = output_path / filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
            else:  # CSV
                filename = f"{safe_conf_name}.csv"
                filepath = output_path / filename
                
                # Flatten data for CSV
                csv_data = []
                for paper in sorted_papers:
                    row = {
                        'paper_id': paper['paper_id'],
                        'title': paper['title'],
                        'status': paper['status'],
                        'normalized_status': paper['normalized_status'],
                        'sort_score': paper['sort_score'],
                        'author_name': paper['author']['name'],
                        'author_position': paper['author']['position'],
                        'total_authors': paper['total_authors'],
                        'affiliations': paper['author']['affiliations'],
                        'countries': ','.join(paper['author']['countries']),
                        'country_codes': ','.join(paper['author']['country_codes'])
                    }
                    
                    # Add review data if available
                    if 'reviews' in paper:
                        row.update({
                            'rating_mean': paper['reviews']['rating_mean'],
                            'total_reviews': paper['reviews']['total_reviews'],
                            'citations': paper['reviews']['google_scholar_citations']
                        })
                    
                    csv_data.append(row)
                
                df = pd.DataFrame(csv_data)
                df.to_csv(filepath, index=False)
            
            output_files[conf_name] = str(filepath)
            logger.info(f"Exported {len(sorted_papers)} papers for {conf_name} to {filepath}")
        
        return output_files

# Example usage and configuration
def create_example_config() -> PipelineConfig:
    """Create an example configuration with custom weights"""
    return PipelineConfig(
        first_author_weight=4.0,
        last_author_weight=2.5,
        middle_author_weight=1.0,
        status_weights={
            'oral': 15.0,
            'spotlight': 10.0,
            'poster': 6.0,
            'unknown': 1.0
        },
        output_format='json',
        include_review_details=True,
        include_citation_data=True
    )

if __name__ == "__main__":
    # Example usage
    config = create_example_config()
    pipeline = PaperDataPipeline("path/to/your/database.db", config)
    
    try:
        output_files = pipeline.process_and_export(
            focus_country="United States",
            output_dir="./output/usa_papers"
        )
        
        print("Processing completed successfully!")
        print("Output files:")
        for conf, filepath in output_files.items():
            print(f"  {conf}: {filepath}")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
