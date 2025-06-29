"""
Enhanced PaperlistsTransformer with comprehensive existence checking and one-by-one processing.
This version processes papers individually and checks for existence before every insert operation.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func, text
from indiaml_v2.models.models import *  # Import all the SQLAlchemy models

class PaperlistsTransformer:
    def __init__(self, database_url: str = "sqlite:///paperlists.db"):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        
        # Configure session with better settings
        Session = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False
        )
        self.session = Session()
        
        # Clear all caches - we'll rely on database queries for existence checks
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
            with self.engine.connect() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_institution_normalized_lookup ON institutions (normalized_name)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_institution_normalized_country ON institutions (normalized_name, country_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_author_orcid_lookup ON authors (orcid)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_author_openreview_lookup ON authors (openreview_id)"))
                conn.commit()
        except Exception as e:
            print(f"Index creation warning: {e}")
    
    def transform_paperlists_data(self, paperlists_json: List[Dict]):
        """Main transformation function - one paper at a time with individual commits"""
        successful_count = 0
        error_count = 0
        skipped_count = 0
        
        total_papers = len(paperlists_json)
        print(f"Starting to process {total_papers} papers one by one...")
        
        for i, paper_data in enumerate(paperlists_json):
            paper_id = paper_data.get('id', f'unknown_{i}')
            
            try:
                # Check if paper already exists
                if self.paper_exists(paper_id):
                    print(f"Paper {paper_id} already exists, skipping...")
                    skipped_count += 1
                    continue
                
                # Process single paper
                print(f"Processing paper {i+1}/{total_papers}: {paper_id}")
                self.process_single_paper_with_checks(paper_data)
                
                # Commit immediately after each paper
                self.session.commit()
                successful_count += 1
                
                if successful_count % 10 == 0:
                    print(f"Successfully processed {successful_count} papers...")
                    
            except Exception as e:
                print(f"Error processing paper {paper_id}: {e}")
                # Rollback this paper's changes
                self.session.rollback()
                error_count += 1
                continue
        
        print(f"Processing completed!")
        print(f"Successfully processed: {successful_count}")
        print(f"Errors: {error_count}")
        print(f"Skipped (already existed): {skipped_count}")
    
    def paper_exists(self, paper_id: str) -> bool:
        """Check if paper already exists in database"""
        try:
            existing = self.session.query(Paper).filter_by(id=paper_id).first()
            return existing is not None
        except Exception:
            return False
    
    def process_single_paper_with_checks(self, data: Dict):
        """Process a single paper with comprehensive existence checks"""
        
        # 1. Create Paper (with existence check)
        paper = self.create_paper_with_checks(data)
        if not paper:
            raise ValueError(f"Failed to create paper {data.get('id')}")
        
        # Add paper to session and flush to get ID
        self.session.add(paper)
        self.session.flush()
        
        # 2. Process Authors and Affiliations
        self.process_authors_and_affiliations_with_checks(paper, data)
        
        # 3. Process Keywords
        self.process_keywords_with_checks(paper, data)
        
        # 4. Process Reviews
        self.process_reviews_with_checks(paper, data)
        
        # 5. Process Citations
        self.process_citations_with_checks(paper, data)
    
    def create_paper_with_checks(self, data: Dict) -> Optional[Paper]:
        """Create Paper entity with comprehensive checks"""
        
        paper_id = data.get('id')
        if not paper_id:
            print(f"Skipping paper with missing ID")
            return None
        
        # Double-check existence
        if self.paper_exists(paper_id):
            print(f"Paper {paper_id} already exists during creation")
            return None
        
        # Get or create track (which includes conference)
        track = self.get_or_create_track_with_checks(data)
        if not track:
            print(f"Failed to create track for paper {paper_id}")
            return None
        
        return Paper(
            id=paper_id,
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
    
    def get_or_create_track_with_checks(self, paper_data: Dict) -> Optional[Track]:
        """Get or create track with comprehensive existence checks"""
        
        track_name = paper_data.get('track', 'main')
        conference_year = self.extract_conference_year(paper_data)
        conference_name = self.extract_conference_name(paper_data)
        
        # Get or create conference first
        conference = self.get_or_create_conference_with_checks(conference_name, conference_year)
        if not conference:
            return None
        
        # Check if track already exists
        existing_track = self.session.query(Track).filter_by(
            conference=conference,
            short_name=track_name
        ).first()
        
        if existing_track:
            return existing_track
        
        # Create new track
        track_type, full_name = self.classify_track(track_name)
        
        track = Track(
            conference=conference,
            name=full_name,
            short_name=track_name,
            track_type=track_type
        )
        
        self.session.add(track)
        self.session.flush()
        return track
    
    def get_or_create_conference_with_checks(self, conference_name: str, year: int) -> Optional[Conference]:
        """Get or create conference with existence checks"""
        
        # Check if conference already exists
        existing_conference = self.session.query(Conference).filter_by(
            name=conference_name,
            year=year
        ).first()
        
        if existing_conference:
            return existing_conference
        
        # Create new conference
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
        self.session.flush()
        return conference
    
    def process_authors_and_affiliations_with_checks(self, paper: Paper, data: Dict):
        """Process authors and affiliations with comprehensive existence checks"""
        
        # Parse all author-related data
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
        
        # Create institution mapping with checks
        institution_map = self.create_institution_mapping_with_checks(
            aff_unique_norms, aff_unique_deps, aff_unique_urls, aff_unique_abbrs,
            country_indices, country_names, campus_indices, campus_names
        )
        
        # Process each author
        for i, author_name in enumerate(authors):
            if not author_name.strip():
                continue
                
            try:
                # Get or create author with checks
                author = self.get_or_create_author_with_checks(
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
                
                if not author:
                    print(f"Failed to create author {author_name} for paper {paper.id}")
                    continue
                
                # Check if paper-author relationship already exists
                existing_paper_author = self.session.query(PaperAuthor).filter_by(
                    paper=paper, author=author
                ).first()
                
                if not existing_paper_author:
                    # Create paper-author relationship
                    paper_author = PaperAuthor(
                        paper=paper,
                        author=author,
                        author_order=i + 1,
                        affiliation_at_time=self.safe_get(raw_affs, i)
                    )
                    self.session.add(paper_author)
                    self.session.flush()
                
                # Process affiliations for this author
                aff_indices = self.safe_get(aff_unique_indices, i, '')
                if aff_indices:
                    self.process_author_affiliations_with_checks(
                        author, aff_indices, institution_map,
                        self.safe_get(positions, i),
                        self.safe_get(email_domains, i)
                    )
                    
            except Exception as e:
                print(f"Error processing author {author_name}: {e}")
                continue
    
    def create_institution_mapping_with_checks(self, aff_unique_norms: List[str], 
                                             aff_unique_deps: List[str],
                                             aff_unique_urls: List[str],
                                             aff_unique_abbrs: List[str],
                                             country_indices: List[str],
                                             country_names: List[str],
                                             campus_indices: List[str],
                                             campus_names: List[str]) -> Dict[str, Institution]:
        """Create institution mapping with comprehensive existence checks"""
        
        institution_map = {}
        
        for i, norm_name in enumerate(aff_unique_norms):
            if not norm_name or not norm_name.strip():
                continue
                
            try:
                # Get country with checks
                country_idx = self.safe_get(country_indices, i, '0')
                country_name = self.safe_get(country_names, self.parse_int(country_idx), 'Unknown')
                
                if not country_name or not country_name.strip():
                    country_name = 'Unknown'
                    
                country = self.get_or_create_country_with_checks(country_name)
                if not country:
                    print(f"Failed to create country {country_name}")
                    continue
                
                # Get campus
                campus_idx = self.safe_get(campus_indices, i, '')
                campus_name = self.safe_get(campus_names, self.parse_int(campus_idx), '') if campus_idx else ''
                
                # Create institution with checks
                institution = self.get_or_create_institution_with_checks(
                    name=norm_name,
                    normalized_name=norm_name,
                    abbreviation=self.safe_get(aff_unique_abbrs, i),
                    country=country,
                    campus=campus_name,
                    website_url=self.safe_get(aff_unique_urls, i),
                    department=self.safe_get(aff_unique_deps, i)
                )
                
                if institution:
                    institution_map[str(i)] = institution
                        
            except Exception as e:
                print(f"Error creating institution mapping for {norm_name}: {e}")
                continue
        
        return institution_map
    
    def get_or_create_country_with_checks(self, name: str) -> Optional[Country]:
        """Get or create country with existence checks"""
        
        if not name or not name.strip():
            name = 'Unknown'
            
        name = name.strip()
        
        # Check if country already exists
        existing_country = self.session.query(Country).filter_by(name=name).first()
        if existing_country:
            return existing_country
        
        try:
            # Create new country
            country = Country(name=name)
            self.session.add(country)
            self.session.flush()
            return country
        except Exception as e:
            print(f"Error creating country {name}: {e}")
            # Try to get it again in case it was created by another process
            return self.session.query(Country).filter_by(name=name).first()
    
    def get_or_create_institution_with_checks(self, name: str, normalized_name: str,
                                            country: Country, **kwargs) -> Optional[Institution]:
        """Get or create institution with comprehensive existence checks"""
        
        if not country:
            return None
        
        campus = kwargs.get('campus', '')
        
        # Check if institution already exists with exact match
        existing_institution = self.session.query(Institution).filter_by(
            normalized_name=normalized_name,
            country=country,
            campus=campus
        ).first()
        
        if existing_institution:
            return existing_institution
        
        try:
            # Create new institution
            institution = Institution(
                name=name,
                normalized_name=normalized_name,
                abbreviation=kwargs.get('abbreviation', ''),
                country=country,
                campus=campus,
                website_url=kwargs.get('website_url', ''),
                domain=self.extract_domain(kwargs.get('website_url', ''))
            )
            self.session.add(institution)
            self.session.flush()
            return institution
            
        except Exception as e:
            print(f"Error creating institution {name}: {e}")
            # Try to get it again in case it was created by another process
            return self.session.query(Institution).filter_by(
                normalized_name=normalized_name,
                country=country,
                campus=campus
            ).first()
    
    def get_or_create_author_with_checks(self, name: str, **kwargs) -> Optional[Author]:
        """Get or create author with comprehensive existence checks"""
        
        try:
            # Clean ORCID
            orcid = kwargs.get('orcid', '')
            orcid = orcid.strip() if orcid else ''
            orcid = None if not orcid else orcid
            
            # Try to find by ORCID first
            if orcid:
                existing_author = self.session.query(Author).filter_by(orcid=orcid).first()
                if existing_author:
                    return existing_author
            
            # Clean OpenReview profile
            or_profile = kwargs.get('or_profile', '')
            or_profile = or_profile.strip() if or_profile else ''
            or_profile = None if not or_profile else or_profile
            
            # Try to find by OpenReview profile
            if or_profile:
                existing_author = self.session.query(Author).filter_by(openreview_id=or_profile).first()
                if existing_author:
                    return existing_author
            
            # Generate unique author ID
            author_id = kwargs.get('author_id', '')
            author_id = author_id.strip() if author_id else self.generate_author_id(name)
            
            # Ensure author ID is unique
            base_id = author_id
            counter = 1
            while self.session.query(Author).filter_by(id=author_id).first():
                author_id = f"{base_id}_{counter}"
                counter += 1
                if counter > 1000:
                    import time
                    author_id = f"{base_id}_{int(time.time())}"
                    break
            
            # Clean other fields
            def clean_field(value):
                if value is None:
                    return None
                value = str(value).strip()
                return None if not value else value
            
            # Create new author
            author = Author(
                id=author_id,
                name=name,
                name_site=clean_field(kwargs.get('author_site')),
                openreview_id=or_profile,
                gender=clean_field(kwargs.get('gender')),
                homepage_url=clean_field(kwargs.get('homepage')),
                dblp_id=clean_field(kwargs.get('dblp')),
                google_scholar_url=clean_field(kwargs.get('google_scholar')),
                orcid=orcid,
                linkedin_url=clean_field(kwargs.get('linkedin'))
            )
            
            self.session.add(author)
            self.session.flush()
            return author
            
        except Exception as e:
            print(f"Error creating author {name}: {e}")
            return None
    
    def process_author_affiliations_with_checks(self, author: Author, aff_indices: str,
                                               institution_map: Dict[str, Institution],
                                               position: str, email_domain: str):
        """Process author affiliations with existence checks"""
        
        try:
            # Handle multi-affiliations
            if '+' in aff_indices:
                indices = aff_indices.split('+')
            else:
                indices = [aff_indices]
            
            # Handle multiple positions and domains
            positions = position.split('+') if position and '+' in position else [position]
            email_domains = email_domain.split('+') if email_domain and '+' in email_domain else [email_domain]
            
            for idx, aff_idx in enumerate(indices):
                if aff_idx.strip() and aff_idx in institution_map:
                    institution = institution_map[aff_idx]
                    
                    if institution:
                        # Check if affiliation already exists
                        existing_affiliation = self.session.query(Affiliation).filter_by(
                            author=author, institution=institution
                        ).first()
                        
                        if not existing_affiliation:
                            # Create new affiliation
                            affiliation = Affiliation(
                                author=author,
                                institution=institution,
                                position=self.safe_get(positions, idx, ''),
                                email_domain=self.safe_get(email_domains, idx, ''),
                                is_primary=(idx == 0)
                            )
                            self.session.add(affiliation)
                            self.session.flush()
                        
        except Exception as e:
            print(f"Error processing affiliations for author {author.name}: {e}")
    
    def process_keywords_with_checks(self, paper: Paper, data: Dict):
        """Process keywords with existence checks"""
        
        keywords_str = data.get('keywords', '')
        if not keywords_str:
            return
        
        keywords = [k.strip() for k in keywords_str.split(';') if k.strip()]
        
        for keyword_text in keywords:
            try:
                keyword = self.get_or_create_keyword_with_checks(keyword_text)
                if keyword:
                    # Check if paper-keyword relationship already exists
                    existing_paper_keyword = self.session.query(PaperKeyword).filter_by(
                        paper=paper, keyword=keyword
                    ).first()
                    
                    if not existing_paper_keyword:
                        paper_keyword = PaperKeyword(paper=paper, keyword=keyword)
                        self.session.add(paper_keyword)
                        self.session.flush()
                        
            except Exception as e:
                print(f"Error processing keyword {keyword_text}: {e}")
                continue
    
    def get_or_create_keyword_with_checks(self, text: str) -> Optional[Keyword]:
        """Get or create keyword with existence checks"""
        
        if not text or not text.strip():
            return None
            
        text = text.strip()
        normalized = text.lower().strip()
        
        # Check if keyword already exists
        existing_keyword = self.session.query(Keyword).filter_by(normalized_keyword=normalized).first()
        if existing_keyword:
            return existing_keyword
        
        try:
            # Create new keyword
            keyword = Keyword(keyword=text, normalized_keyword=normalized)
            self.session.add(keyword)
            self.session.flush()
            return keyword
        except Exception as e:
            print(f"Error creating keyword {text}: {e}")
            # Try to get it again in case it was created by another process
            return self.session.query(Keyword).filter_by(normalized_keyword=normalized).first()
    
    def process_reviews_with_checks(self, paper: Paper, data: Dict):
        """Process reviews with existence checks"""
        
        try:
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
            
            self.session.flush()
            
            # Create aggregated statistics
            self.create_review_statistics_with_checks(paper, data)
            
        except Exception as e:
            print(f"Error processing reviews for paper {paper.id}: {e}")
    
    def create_review_statistics_with_checks(self, paper: Paper, data: Dict):
        """Create review statistics with existence checks"""
        
        try:
            # Check if statistics already exist
            existing_stats = self.session.query(ReviewStatistics).filter_by(paper=paper).first()
            if existing_stats:
                return
            
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
            self.session.flush()
            
        except Exception as e:
            print(f"Error creating review statistics for paper {paper.id}: {e}")
    
    def process_citations_with_checks(self, paper: Paper, data: Dict):
        """Process citations with existence checks"""
        
        try:
            # Check if citations already exist
            existing_citation = self.session.query(Citation).filter_by(paper=paper).first()
            if existing_citation:
                return
            
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
            self.session.flush()
            
        except Exception as e:
            print(f"Error processing citations for paper {paper.id}: {e}")
    
    # Utility methods (unchanged from original)
    
    def parse_semicolon_field(self, field: str) -> List[str]:
        """Parse semicolon-separated fields"""
        if not field:
            return []
        return [item.strip() for item in field.split(';')]
    
    def parse_numeric_field(self, field: str) -> List[int]:
        """Parse semicolon-separated numeric fields"""
        items = self.parse_semicolon_field(field)
        result = []
        for item in items:
            if item.strip():
                parsed = self.parse_int(item)
                if parsed is not None:
                    result.append(parsed)
        return result
    
    def parse_int(self, value: str) -> Optional[int]:
        """Safely parse integer"""
        try:
            return int(value.strip()) if value and value.strip() else None
        except (ValueError, AttributeError):
            return None
    
    def safe_get(self, lst: List, index: int, default=None):
        """Safely get item from list"""
        try:
            if lst is None or index < 0 or index >= len(lst):
                return default
            return lst[index]
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
            if '://' not in url:
                if '.' in url:
                    url = 'http://' + url
                else:
                    return ''
            parsed = urlparse(url)
            if parsed.netloc and '.' in parsed.netloc:
                return parsed.netloc
            return ''
        except Exception:
            return ''
    
    def extract_conference_year(self, paper_data: Dict) -> int:
        """Extract conference year from paper data"""
        bibtex = paper_data.get('bibtex', '')
        if 'year={2025}' in bibtex:
            return 2025
        elif 'year={2024}' in bibtex:
            return 2024
        return 2025
    
    def extract_conference_name(self, paper_data: Dict) -> str:
        """Extract conference name from paper data"""
        bibtex = paper_data.get('bibtex', '')
        site = paper_data.get('site', '')
        
        if 'icml' in bibtex.lower() or 'icml.cc' in site:
            return "ICML"
        elif 'neurips' in bibtex.lower():
            return "NeurIPS"
        elif 'iclr' in bibtex.lower():
            return "ICLR"
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
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.session.close()
            self.engine.dispose()
        except Exception as e:
            print(f"Warning during cleanup: {e}")


# Usage example
def main():
    transformer = None
    try:
        # Load paperlists JSON data
        with open('paperlists_data.json', 'r') as f:
            paperlists_data = json.load(f)
        
        # Initialize transformer
        transformer = PaperlistsTransformer('sqlite:///paperlists.db')
        
        print(f"Processing {len(paperlists_data)} papers one by one...")
        
        # Transform data (one by one processing)
        transformer.transform_paperlists_data(paperlists_data)
        
        print("Database created at: paperlists.db")
        
    except FileNotFoundError:
        print("Error: paperlists_data.json file not found")
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        if transformer:
            transformer.cleanup()


if __name__ == "__main__":
    main()