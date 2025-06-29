"""
Transformation script to convert paperlists JSON data to clean normalized schema.
This script demonstrates how to parse the complex affiliation system and create
proper relationships in the normalized database.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from indiaml_v2.models.models import *  # Import all the SQLAlchemy models

class PaperlistsTransformer:
    def __init__(self, database_url: str = "sqlite:///paperlists.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Cache for institutions and countries to avoid duplicates
        self.country_cache = {}
        self.institution_cache = {}
        self.keyword_cache = {}
        self.conference_cache = {}
        self.track_cache = {}
        
        # Create indexes explicitly for SQLite optimization
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure critical indexes exist for SQLite performance"""
        try:
            # SQLite doesn't automatically create indexes from table args in some cases
            with self.engine.connect() as conn:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_institution_normalized_lookup ON institutions (normalized_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_institution_normalized_country ON institutions (normalized_name, country_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_author_orcid_lookup ON authors (orcid)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_author_openreview_lookup ON authors (openreview_id)")
                conn.commit()
        except Exception as e:
            print(f"Index creation warning: {e}")
    
    def find_institution_by_normalized_name(self, normalized_name: str, country_name: str = None) -> Optional[Institution]:
        """Efficient lookup of institution by normalized name with optional country filter"""
        query = self.session.query(Institution).filter(Institution.normalized_name == normalized_name)
        
        if country_name:
            query = query.join(Country).filter(Country.name == country_name)
        
        return query.first()
    
    def transform_paperlists_data(self, paperlists_json: List[Dict]):
        """Main transformation function"""
        for paper_data in paperlists_json:
            try:
                self.process_paper(paper_data)
                self.session.commit()
            except Exception as e:
                print(f"Error processing paper {paper_data.get('id', 'unknown')}: {e}")
                self.session.rollback()
                continue
    
    def process_paper(self, data: Dict):
        """Process a single paper and all related entities"""
        
        # 1. Create Paper
        paper = self.create_paper(data)
        
        # 2. Process Authors and Affiliations
        self.process_authors_and_affiliations(paper, data)
        
        # 3. Process Keywords
        self.process_keywords(paper, data)
        
        # 4. Process Reviews
        self.process_reviews(paper, data)
        
        # 5. Process Citations
        self.process_citations(paper, data)
        
        self.session.add(paper)
    
    def create_paper(self, data: Dict) -> Paper:
        """Create Paper entity with track relationship"""
        
        # Get or create track (which includes conference)
        track = self.get_or_create_track(data)
        
        return Paper(
            id=data['id'],
            title=data.get('title', ''),
            status=data.get('status'),
            track=track,
            primary_area=data.get('primary_area'),
            abstract=data.get('abstract'),
            tldr=data.get('tldr'),
            supplementary_material=data.get('supplementary_material'),
            bibtex=data.get('bibtex'),
            site_url=data.get('site'),
            openreview_url=data.get('openreview'),
            pdf_url=data.get('pdf'),
            github_url=data.get('github'),
            project_url=data.get('project'),
            author_count=data.get('author_num', 0),
            pdf_size=data.get('pdf_size', 0)
        )
    
    def get_or_create_conference(self, conference_name: str = "ICML", year: int = 2025) -> Conference:
        """Get or create conference"""
        cache_key = f"{conference_name}_{year}"
        if cache_key in self.conference_cache:
            return self.conference_cache[cache_key]
        
        conference = self.session.query(Conference).filter_by(
            name=conference_name,
            year=year
        ).first()
        
        if not conference:
            # Set full name based on common conferences
            full_names = {
                "ICML": "International Conference on Machine Learning",
                "NeurIPS": "Conference on Neural Information Processing Systems",
                "ICLR": "International Conference on Learning Representations",
                "AAAI": "Association for the Advancement of Artificial Intelligence",
                "IJCAI": "International Joint Conference on Artificial Intelligence"
            }
            
            conference = Conference(
                name=conference_name,
                full_name=full_names.get(conference_name, conference_name),
                year=year
            )
            self.session.add(conference)
            self.session.flush()  # Get ID immediately
        
        self.conference_cache[cache_key] = conference
        return conference
    
    def get_or_create_track(self, paper_data: Dict) -> Track:
        """Get or create track based on paper data"""
        
        # Extract track information from paper data
        track_name = paper_data.get('track', 'main')
        
        # Determine conference (could be extracted from paper data or defaulted)
        conference_year = self.extract_conference_year(paper_data)
        conference_name = self.extract_conference_name(paper_data)
        
        conference = self.get_or_create_conference(conference_name, conference_year)
        
        cache_key = f"{conference.id}_{track_name}"
        if cache_key in self.track_cache:
            return self.track_cache[cache_key]
        
        track = self.session.query(Track).filter_by(
            conference=conference,
            short_name=track_name
        ).first()
        
        if not track:
            # Determine track type and full name
            track_type, full_name = self.classify_track(track_name)
            
            track = Track(
                conference=conference,
                name=full_name,
                short_name=track_name,
                track_type=track_type
            )
            self.session.add(track)
            self.session.flush()  # Get ID immediately
        
        self.track_cache[cache_key] = track
        return track
    
    def extract_conference_year(self, paper_data: Dict) -> int:
        """Extract conference year from paper data"""
        # Try to extract from bibtex
        bibtex = paper_data.get('bibtex', '')
        if 'year={2025}' in bibtex:
            return 2025
        elif 'year={2024}' in bibtex:
            return 2024
        
        # Default to 2025 for ICML
        return 2025
    
    def extract_conference_name(self, paper_data: Dict) -> str:
        """Extract conference name from paper data"""
        # Try to extract from bibtex or site URL
        bibtex = paper_data.get('bibtex', '')
        site = paper_data.get('site', '')
        
        if 'icml' in bibtex.lower() or 'icml.cc' in site:
            return "ICML"
        elif 'neurips' in bibtex.lower():
            return "NeurIPS"
        elif 'iclr' in bibtex.lower():
            return "ICLR"
        
        # Default to ICML
        return "ICML"
    
    def classify_track(self, track_name: str) -> Tuple[str, str]:
        """Classify track type and generate full name"""
        track_lower = track_name.lower()
        
        if track_lower == 'main':
            return 'main', 'Main Conference'
        elif track_lower == 'position':
            return 'position', 'Position Papers'
        elif 'workshop' in track_lower or 'ws' in track_lower:
            return 'workshop', f'Workshop: {track_name}'
        elif 'tutorial' in track_lower:
            return 'tutorial', f'Tutorial: {track_name}'
        elif 'demo' in track_lower:
            return 'demo', f'Demonstration: {track_name}'
        elif 'poster' in track_lower:
            return 'poster_session', f'Poster Session: {track_name}'
        else:
            return 'other', track_name
    
    def process_authors_and_affiliations(self, paper: Paper, data: Dict):
        """Process authors and their complex affiliation data"""
        
        # Parse author data
        authors = self.parse_semicolon_field(data.get('author', ''))
        author_sites = self.parse_semicolon_field(data.get('author_site', ''))
        author_ids = self.parse_semicolon_field(data.get('authorids', ''))
        genders = self.parse_semicolon_field(data.get('gender', ''))
        homepages = self.parse_semicolon_field(data.get('homepage', ''))
        dblp_ids = self.parse_semicolon_field(data.get('dblp', ''))
        google_scholars = self.parse_semicolon_field(data.get('google_scholar', ''))
        orcids = self.parse_semicolon_field(data.get('orcid', ''))
        linkedins = self.parse_semicolon_field(data.get('linkedin', ''))
        or_profiles = self.parse_semicolon_field(data.get('or_profile', ''))
        
        # Parse affiliation data
        raw_affs = self.parse_semicolon_field(data.get('aff', ''))
        positions = self.parse_semicolon_field(data.get('position', ''))
        email_domains = self.parse_semicolon_field(data.get('aff_domain', ''))
        
        # Parse normalized affiliation data
        aff_unique_indices = self.parse_semicolon_field(data.get('aff_unique_index', ''))
        aff_unique_norms = self.parse_semicolon_field(data.get('aff_unique_norm', ''))
        aff_unique_deps = self.parse_semicolon_field(data.get('aff_unique_dep', ''))
        aff_unique_urls = self.parse_semicolon_field(data.get('aff_unique_url', ''))
        aff_unique_abbrs = self.parse_semicolon_field(data.get('aff_unique_abbr', ''))
        
        # Parse country data
        country_indices = self.parse_semicolon_field(data.get('aff_country_unique_index', ''))
        country_names = self.parse_semicolon_field(data.get('aff_country_unique', ''))
        
        # Parse campus data
        campus_indices = self.parse_semicolon_field(data.get('aff_campus_unique_index', ''))
        campus_names = self.parse_semicolon_field(data.get('aff_campus_unique', ''))
        
        # Create mapping of unique indices to institutions
        institution_map = self.create_institution_mapping(
            aff_unique_norms, aff_unique_deps, aff_unique_urls, aff_unique_abbrs,
            country_indices, country_names, campus_indices, campus_names
        )
        
        # Process each author
        for i, author_name in enumerate(authors):
            if not author_name.strip():
                continue
                
            # Create or get author
            author = self.get_or_create_author(
                name=author_name,
                author_site=self.safe_get(author_sites, i),
                author_id=self.safe_get(author_ids, i),
                gender=self.safe_get(genders, i),
                homepage=self.safe_get(homepages, i),
                dblp=self.safe_get(dblp_ids, i),
                google_scholar=self.safe_get(google_scholars, i),
                orcid=self.safe_get(orcids, i),
                linkedin=self.safe_get(linkedins, i),
                or_profile=self.safe_get(or_profiles, i)
            )
            
            # Create paper-author relationship
            paper_author = PaperAuthor(
                paper=paper,
                author=author,
                author_order=i + 1,
                affiliation_at_time=self.safe_get(raw_affs, i)
            )
            
            # Process affiliations for this author
            aff_indices = self.safe_get(aff_unique_indices, i, '')
            if aff_indices:
                self.process_author_affiliations(
                    author, aff_indices, institution_map,
                    self.safe_get(positions, i),
                    self.safe_get(email_domains, i)
                )
    
    def create_institution_mapping(self, aff_unique_norms: List[str], 
                                 aff_unique_deps: List[str],
                                 aff_unique_urls: List[str],
                                 aff_unique_abbrs: List[str],
                                 country_indices: List[str],
                                 country_names: List[str],
                                 campus_indices: List[str],
                                 campus_names: List[str]) -> Dict[str, Institution]:
        """Create mapping from unique indices to Institution objects"""
        institution_map = {}
        
        for i, norm_name in enumerate(aff_unique_norms):
            if not norm_name.strip():
                continue
                
            # Get country
            country_idx = self.safe_get(country_indices, i, '0')
            country_name = self.safe_get(country_names, self.parse_int(country_idx), 'Unknown')
            country = self.get_or_create_country(country_name)
            
            # Get campus
            campus_idx = self.safe_get(campus_indices, i, '')
            campus_name = self.safe_get(campus_names, self.parse_int(campus_idx), '') if campus_idx else ''
            
            # Create institution
            institution = self.get_or_create_institution(
                name=norm_name,
                normalized_name=norm_name,
                abbreviation=self.safe_get(aff_unique_abbrs, i),
                country=country,
                campus=campus_name,
                website_url=self.safe_get(aff_unique_urls, i),
                department=self.safe_get(aff_unique_deps, i)
            )
            
            institution_map[str(i)] = institution
        
        return institution_map
    
    def process_author_affiliations(self, author: Author, aff_indices: str,
                                   institution_map: Dict[str, Institution],
                                   position: str, email_domain: str):
        """Process affiliations for a single author, handling multi-affiliations"""
        
        # Handle multi-affiliations (format: "3+0" means both index 3 and 0)
        if '+' in aff_indices:
            indices = aff_indices.split('+')
        else:
            indices = [aff_indices]
        
        # Handle multiple positions (format: "Research Team Lead+Associate Professor")
        positions = position.split('+') if position and '+' in position else [position]
        email_domains = email_domain.split('+') if email_domain and '+' in email_domain else [email_domain]
        
        for idx, aff_idx in enumerate(indices):
            if aff_idx.strip() and aff_idx in institution_map:
                institution = institution_map[aff_idx]
                
                # Create affiliation
                affiliation = Affiliation(
                    author=author,
                    institution=institution,
                    position=self.safe_get(positions, idx, ''),
                    email_domain=self.safe_get(email_domains, idx, ''),
                    is_primary=(idx == 0)  # First affiliation is primary
                )
                self.session.add(affiliation)
    
    def get_or_create_author(self, name: str, **kwargs) -> Author:
        """Get existing author or create new one"""
        
        # Try to find by ORCID first (most reliable)
        orcid = kwargs.get('orcid', '').strip()
        if orcid:
            author = self.session.query(Author).filter_by(orcid=orcid).first()
            if author:
                return author
        
        # Try to find by OpenReview profile
        or_profile = kwargs.get('or_profile', '').strip()
        if or_profile:
            author = self.session.query(Author).filter_by(openreview_id=or_profile).first()
            if author:
                return author
        
        # Create new author
        author_id = kwargs.get('author_id', '').strip() or self.generate_author_id(name)
        
        author = Author(
            id=author_id,
            name=name,
            name_site=kwargs.get('author_site', ''),
            openreview_id=or_profile,
            gender=kwargs.get('gender', ''),
            homepage_url=kwargs.get('homepage', ''),
            dblp_id=kwargs.get('dblp', ''),
            google_scholar_url=kwargs.get('google_scholar', ''),
            orcid=orcid,
            linkedin_url=kwargs.get('linkedin', '')
        )
        
        self.session.add(author)
        return author
    
    def get_or_create_country(self, name: str) -> Country:
        """Get existing country or create new one"""
        if name in self.country_cache:
            return self.country_cache[name]
        
        country = self.session.query(Country).filter_by(name=name).first()
        if not country:
            country = Country(name=name)
            self.session.add(country)
        
        self.country_cache[name] = country
        return country
    
    def get_or_create_institution(self, name: str, normalized_name: str,
                                 country: Country, **kwargs) -> Institution:
        """Get existing institution or create new one - optimized for normalized_name lookups"""
        
        cache_key = f"{normalized_name}:{country.name}:{kwargs.get('campus', '')}"
        if cache_key in self.institution_cache:
            return self.institution_cache[cache_key]
        
        # Use the optimized lookup method
        institution = self.find_institution_by_normalized_name(normalized_name, country.name)
        
        # If found, check for exact match including campus
        if institution and institution.campus == kwargs.get('campus', ''):
            self.institution_cache[cache_key] = institution
            return institution
        
        # If not found or campus doesn't match, check for exact match with all criteria
        institution = self.session.query(Institution).filter_by(
            normalized_name=normalized_name,
            country=country,
            campus=kwargs.get('campus', '')
        ).first()
        
        if not institution:
            institution = Institution(
                name=name,
                normalized_name=normalized_name,
                abbreviation=kwargs.get('abbreviation', ''),
                country=country,
                campus=kwargs.get('campus', ''),
                website_url=kwargs.get('website_url', ''),
                domain=self.extract_domain(kwargs.get('website_url', ''))
            )
            self.session.add(institution)
            self.session.flush()  # Get the ID immediately for caching
        
        self.institution_cache[cache_key] = institution
        return institution
    
    def process_keywords(self, paper: Paper, data: Dict):
        """Process paper keywords"""
        keywords_str = data.get('keywords', '')
        if not keywords_str:
            return
        
        keywords = [k.strip() for k in keywords_str.split(';') if k.strip()]
        
        for keyword_text in keywords:
            keyword = self.get_or_create_keyword(keyword_text)
            paper_keyword = PaperKeyword(paper=paper, keyword=keyword)
            self.session.add(paper_keyword)
    
    def get_or_create_keyword(self, text: str) -> Keyword:
        """Get existing keyword or create new one"""
        normalized = text.lower().strip()
        
        if normalized in self.keyword_cache:
            return self.keyword_cache[normalized]
        
        keyword = self.session.query(Keyword).filter_by(normalized_keyword=normalized).first()
        if not keyword:
            keyword = Keyword(keyword=text, normalized_keyword=normalized)
            self.session.add(keyword)
        
        self.keyword_cache[normalized] = keyword
        return keyword
    
    def process_reviews(self, paper: Paper, data: Dict):
        """Process review data"""
        
        # Individual review scores
        ratings = self.parse_numeric_field(data.get('rating', ''))
        confidences = self.parse_numeric_field(data.get('confidence', ''))
        recommendations = self.parse_numeric_field(data.get('recommendation', ''))
        
        reviewers = self.parse_semicolon_field(data.get('reviewers', ''))
        
        # Word counts
        wc_summaries = self.parse_numeric_field(data.get('wc_summary', ''))
        wc_strengths = self.parse_numeric_field(data.get('wc_strengths_and_weaknesses', ''))
        wc_questions = self.parse_numeric_field(data.get('wc_questions', ''))
        wc_reviews = self.parse_numeric_field(data.get('wc_review', ''))
        
        # Create individual review records
        for i in range(max(len(ratings), len(confidences), len(recommendations))):
            review = Review(
                paper=paper,
                reviewer_id=self.safe_get(reviewers, i),
                rating=self.safe_get(ratings, i),
                confidence=self.safe_get(confidences, i),
                recommendation=self.safe_get(recommendations, i),
                word_count_summary=self.safe_get(wc_summaries, i),
                word_count_strengths_weaknesses=self.safe_get(wc_strengths, i),
                word_count_questions=self.safe_get(wc_questions, i),
                word_count_total=self.safe_get(wc_reviews, i)
            )
            self.session.add(review)
        
        # Create aggregated statistics
        self.create_review_statistics(paper, data)
    
    def create_review_statistics(self, paper: Paper, data: Dict):
        """Create aggregated review statistics"""
        stats = ReviewStatistics(paper=paper)
        
        # Extract [mean, std] arrays
        for field_name in ['rating', 'confidence', 'support', 'significance']:
            avg_data = data.get(f'{field_name}_avg')
            if avg_data and len(avg_data) >= 2:
                setattr(stats, f'{field_name}_mean', avg_data[0])
                setattr(stats, f'{field_name}_std', avg_data[1])
        
        # Word count averages
        for wc_field in ['wc_summary', 'wc_review']:
            avg_data = data.get(f'{wc_field}_avg')
            if avg_data and len(avg_data) >= 2:
                field_base = wc_field.replace('wc_', 'word_count_')
                setattr(stats, f'{field_base}_mean', avg_data[0])
                setattr(stats, f'{field_base}_std', avg_data[1])
        
        # Correlation
        stats.rating_confidence_correlation = data.get('corr_rating_confidence')
        
        self.session.add(stats)
    
    def process_citations(self, paper: Paper, data: Dict):
        """Process citation data"""
        gs_citations = data.get('gs_citation', -1)
        if gs_citations == -1:
            gs_citations = 0
        
        citation = Citation(
            paper=paper,
            google_scholar_citations=gs_citations,
            google_scholar_url=data.get('gs_cited_by_link', ''),
            google_scholar_versions=data.get('gs_version_total', 0) if data.get('gs_version_total', -1) != -1 else 0
        )
        self.session.add(citation)
    
    # Utility methods
    
    def parse_semicolon_field(self, field: str) -> List[str]:
        """Parse semicolon-separated fields"""
        if not field:
            return []
        return [item.strip() for item in field.split(';')]
    
    def parse_numeric_field(self, field: str) -> List[int]:
        """Parse semicolon-separated numeric fields"""
        items = self.parse_semicolon_field(field)
        return [self.parse_int(item) for item in items if item.strip()]
    
    def parse_int(self, value: str) -> Optional[int]:
        """Safely parse integer"""
        try:
            return int(value.strip()) if value.strip() else None
        except (ValueError, AttributeError):
            return None
    
    def safe_get(self, lst: List, index: int, default=None):
        """Safely get item from list"""
        try:
            return lst[index] if index < len(lst) else default
        except (IndexError, TypeError):
            return default
    
    def generate_author_id(self, name: str) -> str:
        """Generate author ID from name"""
        return re.sub(r'[^a-zA-Z0-9]', '_', name.lower())[:50]
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ''
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ''
    
    def get_institution_stats(self):
        """Get statistics about institutions for debugging"""
        total_institutions = self.session.query(Institution).count()
        institutions_by_country = self.session.query(
            Country.name, 
            func.count(Institution.id)
        ).join(Institution).group_by(Country.name).all()
        
        print(f"Total institutions: {total_institutions}")
        print("Institutions by country:")
        for country, count in institutions_by_country:
            print(f"  {country}: {count}")

# Performance optimization for SQLite
def optimize_sqlite_connection(engine):
    """Apply SQLite-specific optimizations"""
    with engine.connect() as conn:
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Increase cache size (default is usually too small)
        conn.execute("PRAGMA cache_size=10000")
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        # Optimize for faster writes during bulk insert
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.commit()

# Usage example
def main():
    # Load paperlists JSON data
    with open('paperlists_data.json', 'r') as f:
        paperlists_data = json.load(f)
    
    # Initialize transformer with SQLite
    transformer = PaperlistsTransformer('sqlite:///paperlists.db')
    
    # Apply SQLite optimizations
    # optimize_sqlite_connection(transformer.engine)
    
    print(f"Processing {len(paperlists_data)} papers...")
    
    # Transform data
    transformer.transform_paperlists_data(paperlists_data)
    
    # Print statistics
    transformer.get_institution_stats()
    
    print("Transformation completed!")
    print(f"Database created at: paperlists.db")

if __name__ == "__main__":
    main()