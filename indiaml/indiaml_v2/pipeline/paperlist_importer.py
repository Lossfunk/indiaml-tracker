"""
Enhanced PaperlistsTransformer with comprehensive existence checking, detailed logging, and verification.
This version processes papers individually with extensive logging, time metrics, and post-import verification.
"""

import argparse
import json
import re
import random
import time
import sys
import os
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func, text
from indiaml_v2.models.models import *  # Import all the SQLAlchemy models
from indiaml_v2.models.models import PaperAuthorAffiliation  # Explicitly import the new model
from indiaml_v2.logging_config import get_logger
from indiaml_v2.config import ImporterConfig, load_config

# Import rating validator from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from indiaml_v2.pipeline.rating_validator import validate_and_normalize_rating, validate_confidence

class PaperlistsTransformer:
    def __init__(self, config: ImporterConfig = None, database_url: str = None, conference_year: int = None, conference_name: str = None):
        # Load configuration
        self.config = config or ImporterConfig()
        
        # Override database URL if provided
        if database_url:
            self.config.database_url = database_url
        
        # Store externally provided conference year and name
        self.conference_year = conference_year
        self.conference_name = conference_name
        
        # Initialize comprehensive logging
        self.logger = get_logger("paperlist_importer", self.config.log_directory)
        self.logger.start_operation("initializing_transformer", database_url=self.config.database_url)
        
        # Database setup
        self.engine = create_engine(self.config.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        
        # Configure session with better settings
        Session = sessionmaker(
            bind=self.engine,
            autoflush=self.config.session_autoflush,
            expire_on_commit=self.config.session_expire_on_commit
        )
        self.session = Session()
        
        # Clear all caches - we'll rely on database queries for existence checks
        self.country_cache = {}
        self.institution_cache = {}
        self.keyword_cache = {}
        self.conference_cache = {}
        self.track_cache = {}
        
        # Statistics tracking
        self.stats = {
            'papers_processed': 0,
            'papers_skipped': 0,
            'papers_failed': 0,
            'authors_created': 0,
            'institutions_created': 0,
            'countries_created': 0,
            'keywords_created': 0,
            'reviews_created': 0,
            'citations_created': 0,
            'start_time': time.time()
        }
        
        # Create indexes explicitly for SQLite optimization
        self._ensure_indexes()
        
        self.logger.end_operation("initializing_transformer", success=True)
        self.logger.success("PaperlistsTransformer initialized successfully")
    
    def _ensure_indexes(self):
        """Ensure critical indexes exist for SQLite performance"""
        self.logger.start_operation("creating_database_indexes")
        try:
            with self.engine.connect() as conn:
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_institution_normalized_lookup ON institutions (normalized_name)",
                    "CREATE INDEX IF NOT EXISTS idx_institution_normalized_country ON institutions (normalized_name, country_id)",
                    "CREATE INDEX IF NOT EXISTS idx_author_orcid_lookup ON authors (orcid)",
                    "CREATE INDEX IF NOT EXISTS idx_author_openreview_lookup ON authors (openreview_id)",
                    "CREATE INDEX IF NOT EXISTS idx_paper_id_lookup ON papers (id)",
                    "CREATE INDEX IF NOT EXISTS idx_keyword_normalized_lookup ON keywords (normalized_keyword)"
                ]
                
                for index_sql in indexes:
                    conn.execute(text(index_sql))
                    
                conn.commit()
                self.logger.success(f"Created {len(indexes)} database indexes for performance optimization")
                
        except Exception as e:
            self.logger.error(f"Index creation warning: {e}")
        finally:
            self.logger.end_operation("creating_database_indexes", success=True)
    
    def transform_paperlists_data(self, paperlists_json: List[Dict]):
        """Main transformation function with comprehensive logging and time metrics"""
        self.logger.start_operation("transform_paperlists_data", total_papers=len(paperlists_json))
        
        successful_count = 0
        error_count = 0
        skipped_count = 0
        
        total_papers = len(paperlists_json)
        self.logger.info(f"Starting to process {total_papers} papers one by one with detailed logging")
        
        # Track processing time for batches
        batch_start_time = time.time()
        batch_size = self.config.batch_size
        
        for i, paper_data in enumerate(paperlists_json):
            paper_id = paper_data.get('id', f'unknown_{i}')
            paper_title = paper_data.get('title', 'Unknown Title')[:50] + "..."
            
            # Start timing this paper
            paper_start_time = time.time()
            
            try:
                # Check if paper already exists
                if self.paper_exists(paper_id):
                    self.logger.info(f"Paper {paper_id} already exists, skipping", 
                                   paper_id=paper_id, title=paper_title)
                    skipped_count += 1
                    self.stats['papers_skipped'] += 1
                    continue
                
                # Process single paper with detailed logging
                self.logger.info(f"Processing paper {i+1}/{total_papers}: {paper_id}", 
                               paper_id=paper_id, title=paper_title, progress=f"{i+1}/{total_papers}")
                
                self.process_single_paper_with_checks(paper_data)
                
                # Commit immediately after each paper
                self.session.commit()
                successful_count += 1
                self.stats['papers_processed'] += 1
                
                # Log paper processing time
                paper_duration = time.time() - paper_start_time
                self.logger.success(f"Paper {paper_id} processed successfully in {paper_duration:.3f}s",
                                  paper_id=paper_id, duration=paper_duration)
                
                # Log batch progress
                if successful_count % batch_size == 0:
                    batch_duration = time.time() - batch_start_time
                    avg_time_per_paper = batch_duration / batch_size
                    estimated_remaining = (total_papers - i - 1) * avg_time_per_paper
                    
                    self.logger.progress(f"Batch completed: {successful_count} papers processed", 
                                       batch_size=batch_size, 
                                       batch_duration=batch_duration,
                                       avg_time_per_paper=avg_time_per_paper,
                                       estimated_remaining_time=estimated_remaining)
                    
                    batch_start_time = time.time()
                    
            except Exception as e:
                paper_duration = time.time() - paper_start_time
                self.logger.error(f"Error processing paper {paper_id} after {paper_duration:.3f}s: {e}",
                                paper_id=paper_id, title=paper_title, duration=paper_duration, error=str(e))
                
                # Rollback this paper's changes
                self.session.rollback()
                error_count += 1
                self.stats['papers_failed'] += 1
                continue
        
        # Final statistics
        total_duration = time.time() - self.stats['start_time']
        
        self.logger.success("Processing completed successfully!")
        self.logger.log_data_stats("final_processing_stats", 
                                 total_papers, 
                                 successful=successful_count,
                                 errors=error_count, 
                                 skipped=skipped_count,
                                 total_duration=total_duration,
                                 avg_time_per_paper=total_duration/max(1, successful_count))
        
        # Perform post-import verification
        self.verify_import_success(paperlists_json, successful_count)
        
        self.logger.end_operation("transform_paperlists_data", success=True)
    
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
        
        # Handle author_num being None - calculate from actual authors if needed
        author_num = data.get('author_num')
        if author_num is None:
            # Calculate from actual author field
            authors = self.parse_semicolon_field(data.get('author', ''))
            author_num = len(authors)
        
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
            author_count=author_num or 0,
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
        
        # Create new conference using config
        conference = Conference(
            name=conference_name,
            full_name=self.config.conference_full_names.get(conference_name, conference_name),
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
                        raw_affiliation_text=self.safe_get(raw_affs, i)
                    )
                    self.session.add(paper_author)
                    self.session.flush()
                else:
                    paper_author = existing_paper_author
                
                # Process affiliations for this author-paper combination
                aff_indices = self.safe_get(aff_unique_indices, i, '')
                if aff_indices:
                    self.process_paper_author_affiliations_with_checks(
                        paper_author, author, aff_indices, institution_map,
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
                if counter > self.config.max_author_id_attempts:
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
    
    def process_paper_author_affiliations_with_checks(self, paper_author: PaperAuthor, author: Author, 
                                                     aff_indices: str, institution_map: Dict[str, Institution],
                                                     position: str, email_domain: str):
        """Process paper-author affiliations with multi-affiliation support and deduplication"""
        
        try:
            # Handle multi-affiliations (+ delimited)
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
                        # Get or create deduplicated affiliation
                        affiliation = self.get_or_create_affiliation_with_deduplication(
                            author=author,
                            institution=institution,
                            position=self.safe_get(positions, idx, ''),
                            email_domain=self.safe_get(email_domains, idx, '')
                        )
                        
                        if affiliation:
                            # Check if paper-author-affiliation relationship already exists
                            existing_paa = self.session.query(PaperAuthorAffiliation).filter_by(
                                paper_author=paper_author,
                                affiliation=affiliation
                            ).first()
                            
                            if not existing_paa:
                                # Create new paper-author-affiliation relationship
                                paper_author_affiliation = PaperAuthorAffiliation(
                                    paper_author=paper_author,
                                    affiliation=affiliation,
                                    position=self.safe_get(positions, idx, ''),
                                    email_domain=self.safe_get(email_domains, idx, ''),
                                    is_primary=(idx == 0)  # First affiliation is primary
                                )
                                self.session.add(paper_author_affiliation)
                                self.session.flush()
                        
        except Exception as e:
            print(f"Error processing paper-author affiliations for author {author.name}: {e}")
    
    def get_or_create_affiliation_with_deduplication(self, author: Author, institution: Institution,
                                                   position: str = '', email_domain: str = '') -> Optional[Affiliation]:
        """Get or create affiliation with proper deduplication based on author-institution combination"""
        
        try:
            # Check if affiliation already exists (deduplication based on author + institution)
            existing_affiliation = self.session.query(Affiliation).filter_by(
                author=author,
                institution=institution
            ).first()
            
            if existing_affiliation:
                # Update position and email_domain if they're more specific/complete
                updated = False
                if position and not existing_affiliation.position:
                    existing_affiliation.position = position
                    updated = True
                if email_domain and not existing_affiliation.email_domain:
                    existing_affiliation.email_domain = email_domain
                    updated = True
                
                if updated:
                    self.session.flush()
                
                return existing_affiliation
            
            # Create new affiliation
            affiliation = Affiliation(
                author=author,
                institution=institution,
                position=position,
                email_domain=email_domain,
                is_primary=False  # Will be set at paper-author-affiliation level
            )
            
            self.session.add(affiliation)
            self.session.flush()
            return affiliation
            
        except Exception as e:
            print(f"Error creating/getting affiliation for {author.name} at {institution.name}: {e}")
            # Try to get existing one in case of race condition
            return self.session.query(Affiliation).filter_by(
                author=author,
                institution=institution
            ).first()

    def process_author_affiliations_with_checks(self, author: Author, aff_indices: str,
                                               institution_map: Dict[str, Institution],
                                               position: str, email_domain: str):
        """Legacy method - kept for backward compatibility but redirects to new logic"""
        
        # This method is now deprecated in favor of process_paper_author_affiliations_with_checks
        # but kept for any legacy code that might still call it
        print(f"Warning: process_author_affiliations_with_checks is deprecated. Use process_paper_author_affiliations_with_checks instead.")
        
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
                        # Use the new deduplication method
                        self.get_or_create_affiliation_with_deduplication(
                            author=author,
                            institution=institution,
                            position=self.safe_get(positions, idx, ''),
                            email_domain=self.safe_get(email_domains, idx, '')
                        )
                        
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
        """Process reviews with existence checks and rating normalization"""
        
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
            
            # Create individual review records with rating validation
            for i in range(max(len(ratings), len(confidences), len(recommendations))):
                reviewer_id = self.safe_get(reviewers, i)
                
                # Validate and normalize ratings and confidence
                original_rating = self.safe_get(ratings, i)
                original_confidence = self.safe_get(confidences, i)
                original_recommendation = self.safe_get(recommendations, i)
                
                # Apply validation and normalization
                validated_rating = validate_and_normalize_rating(
                    original_rating, 
                    paper_id=paper.id, 
                    reviewer_id=reviewer_id,
                    logger=self.logger.logger
                )
                
                validated_confidence = validate_confidence(
                    original_confidence,
                    paper_id=paper.id,
                    reviewer_id=reviewer_id,
                    logger=self.logger.logger
                )
                
                # For recommendations, apply same normalization as ratings (assuming same scale)
                validated_recommendation = validate_and_normalize_rating(
                    original_recommendation,
                    paper_id=paper.id,
                    reviewer_id=reviewer_id,
                    logger=self.logger.logger
                ) if original_recommendation is not None else None
                
                review = Review(
                    paper=paper,
                    reviewer_id=reviewer_id,
                    rating=validated_rating,
                    confidence=validated_confidence,
                    recommendation=validated_recommendation,
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
            self.logger.error(f"Error processing reviews for paper {paper.id}: {e}")
            raise  # Re-raise to trigger rollback
    
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
        """Extract conference year from paper data or use externally provided year"""
        # If year was provided externally, use that
        if self.conference_year is not None:
            return self.conference_year
        
        # Fallback to parsing from bibtex (for backward compatibility)
        bibtex = paper_data.get('bibtex', '')
        if 'year={2025}' in bibtex:
            return 2025
        elif 'year={2024}' in bibtex:
            return 2024
        return 2025
    
    def extract_conference_name(self, paper_data: Dict) -> str:
        """Extract conference name from paper data - prioritize externally provided name"""
        # If conference name was provided externally (from filename), use that
        if self.conference_name is not None:
            return self.conference_name
        
        # Fallback to existing bibtex parsing logic
        bibtex = paper_data.get('bibtex', '')
        site = paper_data.get('site', '')
        
        if 'icml' in bibtex.lower() or 'icml.cc' in site:
            return "ICML"
        elif 'neurips' in bibtex.lower():
            return "NeurIPS"
        elif 'iclr' in bibtex.lower():
            return "ICLR"
        return "ICML"  # Default fallback
    
    def classify_track(self, track_name: str) -> Tuple[str, str]:
        """Classify track type and generate full name using configuration"""
        track_lower = track_name.lower()
        
        # Check exact matches first
        if track_lower in self.config.track_classifications:
            track_type = self.config.track_classifications[track_lower]
            full_name = self.config.default_track_names.get(track_type, track_name)
            return track_type, full_name
        
        # Check partial matches for special cases
        if 'workshop' in track_lower or 'ws' in track_lower:
            return 'workshop', f'Workshop: {track_name}'
        elif 'tutorial' in track_lower:
            return 'tutorial', f'Tutorial: {track_name}'
        elif 'demo' in track_lower:
            return 'demo', f'Demonstration: {track_name}'
        elif 'poster' in track_lower:
            return 'poster_session', f'Poster Session: {track_name}'
        else:
            return 'other', track_name
    
    def verify_import_success(self, original_data: List[Dict], expected_count: int):
        """Verify import success by randomly sampling and comparing data"""
        self.logger.start_operation("post_import_verification", expected_count=expected_count)
        
        try:
            # Get actual count from database
            actual_count = self.session.query(Paper).count()
            self.logger.info(f"Database contains {actual_count} papers, expected {expected_count}")
            
            if actual_count < expected_count:
                self.logger.warning(f"Paper count mismatch: expected {expected_count}, got {actual_count}")
            
            # Randomly sample papers for verification
            sample_size = min(self.config.verification_sample_size, len(original_data), actual_count)
            if sample_size == 0:
                self.logger.warning("No papers to verify")
                return
            
            self.logger.info(f"Randomly sampling {sample_size} papers for verification")
            
            # Get random sample from original data
            sampled_papers = random.sample(original_data, sample_size)
            verification_results = {
                'verified': 0,
                'failed': 0,
                'missing': 0,
                'data_mismatches': []
            }
            
            for i, original_paper in enumerate(sampled_papers):
                paper_id = original_paper.get('id')
                if not paper_id:
                    continue
                
                self.logger.debug(f"Verifying paper {i+1}/{sample_size}: {paper_id}")
                
                # Check if paper exists in database
                db_paper = self.session.query(Paper).filter_by(id=paper_id).first()
                if not db_paper:
                    verification_results['missing'] += 1
                    self.logger.error(f"Paper {paper_id} missing from database", paper_id=paper_id)
                    continue
                
                # Verify paper data
                verification_success = self._verify_paper_data(original_paper, db_paper, verification_results)
                
                if verification_success:
                    verification_results['verified'] += 1
                    self.logger.success(f"Paper {paper_id} verification passed", paper_id=paper_id)
                else:
                    verification_results['failed'] += 1
                    self.logger.error(f"Paper {paper_id} verification failed", paper_id=paper_id)
            
            # Log verification summary
            self.logger.log_data_stats("verification_results", 
                                     sample_size,
                                     verified=verification_results['verified'],
                                     failed=verification_results['failed'],
                                     missing=verification_results['missing'],
                                     success_rate=verification_results['verified']/max(1, sample_size))
            
            # Log database statistics
            self._log_database_statistics()
            
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
        finally:
            self.logger.end_operation("post_import_verification", success=True)
    
    def _verify_paper_data(self, original: Dict, db_paper: Paper, results: Dict) -> bool:
        """Verify individual paper data matches between original and database"""
        mismatches = []
        paper_id = db_paper.id
        
        # Handle author_num being None in original data - calculate from authors if needed
        original_author_num = original.get('author_num')
        if original_author_num is None:
            # Calculate from actual author field like we do during import
            authors = self.parse_semicolon_field(original.get('author', ''))
            original_author_num = len(authors)
        
        # Check basic paper fields
        checks = [
            ('title', original.get('title', ''), db_paper.title),
            ('status', original.get('status'), db_paper.status),
            ('primary_area', original.get('primary_area'), db_paper.primary_area),
            ('author_count', original_author_num or 0, db_paper.author_count)
        ]
        
        for field_name, original_value, db_value in checks:
            # Fix the comparison logic to handle None and 0 correctly
            original_str = str(original_value if original_value is not None else '').strip()
            db_str = str(db_value if db_value is not None else '').strip()
            
            if original_str != db_str:
                mismatch = {
                    'field': field_name,
                    'original': original_value,
                    'database': db_value
                }
                mismatches.append(mismatch)
                self.logger.error(f"Field mismatch in {field_name}: expected '{original_value}', got '{db_value}'", 
                                paper_id=paper_id, field=field_name, expected=original_value, actual=db_value)
        
        # Check author count by querying relationships
        actual_author_count = self.session.query(PaperAuthor).filter_by(paper=db_paper).count()
        expected_author_count = len(self.parse_semicolon_field(original.get('author', '')))
        
        if actual_author_count != expected_author_count:
            mismatch = {
                'field': 'actual_author_count',
                'original': expected_author_count,
                'database': actual_author_count
            }
            mismatches.append(mismatch)
            self.logger.error(f"Author count mismatch: expected {expected_author_count}, got {actual_author_count}", 
                            paper_id=paper_id, expected_authors=expected_author_count, actual_authors=actual_author_count)
        
        # Check keywords
        original_keywords = set(k.strip().lower() for k in original.get('keywords', '').split(';') if k.strip())
        db_keywords = set(pk.keyword.normalized_keyword for pk in 
                         self.session.query(PaperKeyword).filter_by(paper=db_paper).all())
        
        if original_keywords != db_keywords:
            missing_keywords = original_keywords - db_keywords
            extra_keywords = db_keywords - original_keywords
            
            mismatch = {
                'field': 'keywords',
                'original': len(original_keywords),
                'database': len(db_keywords),
                'missing_keywords': list(missing_keywords),
                'extra_keywords': list(extra_keywords)
            }
            mismatches.append(mismatch)
            
            self.logger.error(f"Keywords mismatch: expected {len(original_keywords)}, got {len(db_keywords)}", 
                            paper_id=paper_id, 
                            expected_count=len(original_keywords), 
                            actual_count=len(db_keywords),
                            missing_keywords=list(missing_keywords),
                            extra_keywords=list(extra_keywords))
        
        # Check reviews existence
        review_count = self.session.query(Review).filter_by(paper=db_paper).count()
        original_ratings = self.parse_numeric_field(original.get('rating', ''))
        expected_review_count = len(original_ratings)
        
        if review_count != expected_review_count:
            mismatch = {
                'field': 'review_count',
                'original': expected_review_count,
                'database': review_count
            }
            mismatches.append(mismatch)
            self.logger.error(f"Review count mismatch: expected {expected_review_count}, got {review_count}", 
                            paper_id=paper_id, expected_reviews=expected_review_count, actual_reviews=review_count)
        
        # Check citations existence
        citation_exists = self.session.query(Citation).filter_by(paper=db_paper).first() is not None
        original_has_citations = original.get('gs_citation', -1) != -1
        
        if original_has_citations and not citation_exists:
            mismatch = {
                'field': 'citations_missing',
                'original': 'citations_expected',
                'database': 'no_citations'
            }
            mismatches.append(mismatch)
            self.logger.error(f"Citations missing: expected citation data but none found in database", 
                            paper_id=paper_id, original_citations=original.get('gs_citation', -1))
        
        # Check track and conference
        if db_paper.track:
            original_track = original.get('track', 'main')
            if db_paper.track.short_name != original_track:
                mismatch = {
                    'field': 'track',
                    'original': original_track,
                    'database': db_paper.track.short_name
                }
                mismatches.append(mismatch)
                self.logger.error(f"Track mismatch: expected '{original_track}', got '{db_paper.track.short_name}'", 
                                paper_id=paper_id, expected_track=original_track, actual_track=db_paper.track.short_name)
        else:
            mismatch = {
                'field': 'track_missing',
                'original': original.get('track', 'main'),
                'database': 'no_track'
            }
            mismatches.append(mismatch)
            self.logger.error(f"Track missing: paper has no track assigned", 
                            paper_id=paper_id, expected_track=original.get('track', 'main'))
        
        if mismatches:
            results['data_mismatches'].append({
                'paper_id': db_paper.id,
                'mismatches': mismatches
            })
            
            # Log summary of all mismatches for this paper
            mismatch_fields = [m['field'] for m in mismatches]
            self.logger.error(f"Paper verification failed with {len(mismatches)} mismatches in fields: {', '.join(mismatch_fields)}", 
                            paper_id=paper_id, mismatch_count=len(mismatches), failed_fields=mismatch_fields)
            return False
        
        return True
    
    def _log_database_statistics(self):
        """Log comprehensive database statistics"""
        try:
            stats = {
                'papers': self.session.query(Paper).count(),
                'authors': self.session.query(Author).count(),
                'institutions': self.session.query(Institution).count(),
                'countries': self.session.query(Country).count(),
                'keywords': self.session.query(Keyword).count(),
                'reviews': self.session.query(Review).count(),
                'citations': self.session.query(Citation).count(),
                'affiliations': self.session.query(Affiliation).count(),
                'paper_authors': self.session.query(PaperAuthor).count(),
                'paper_keywords': self.session.query(PaperKeyword).count()
            }
            
            self.logger.info("📊 Final Database Statistics:")
            for entity, count in stats.items():
                self.logger.info(f"  {entity.title()}: {count:,}")
            
            # Log top countries and institutions
            top_countries = self.session.query(Country.name, func.count(Institution.id))\
                .join(Institution)\
                .group_by(Country.name)\
                .order_by(func.count(Institution.id).desc())\
                .limit(self.config.top_countries_limit).all()
            
            self.logger.info("🌍 Top 5 Countries by Institution Count:")
            for country, count in top_countries:
                self.logger.info(f"  {country}: {count} institutions")
            
            # Log processing performance
            total_time = time.time() - self.stats['start_time']
            papers_per_second = self.stats['papers_processed'] / max(1, total_time)
            
            self.logger.info("⚡ Performance Metrics:")
            self.logger.info(f"  Total processing time: {total_time:.2f} seconds")
            self.logger.info(f"  Papers processed per second: {papers_per_second:.2f}")
            self.logger.info(f"  Average time per paper: {total_time/max(1, self.stats['papers_processed']):.3f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to log database statistics: {e}")
    
    def cleanup(self):
        """Clean up resources with logging"""
        self.logger.start_operation("cleanup_resources")
        try:
            self.session.close()
            self.engine.dispose()
            self.logger.success("Resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Warning during cleanup: {e}")
        finally:
            self.logger.end_operation("cleanup_resources", success=True)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Import paperlist JSON data into SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python paperlist_importer.py data.json
  python paperlist_importer.py data.json --database custom.db
  python paperlist_importer.py data.json --config config.json --log-level DEBUG
        """
    )
    
    parser.add_argument(
        'json_file',
        help='Path to the JSON file containing paperlist data'
    )
    
    parser.add_argument(
        '--database', '-d',
        default=None,
        help='Path to SQLite database file (default: from config or paperlists.db)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to configuration JSON file (optional)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    return parser.parse_args()


def main():
    """Main function with CLI argument support and enhanced logging"""
    transformer = None
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_config(args.config)
        
        # Override database URL if provided via CLI
        if args.database:
            config.database_url = f'sqlite:///{args.database}'
        
        # Initialize logger with config
        logger = get_logger("paperlist_importer_main", config.log_directory)
        
        # Set log level
        import logging
        logger.logger.setLevel(getattr(logging, args.log_level))
        
        logger.start_operation("main_import_process", 
                             json_file=args.json_file,
                             database=config.database_url,
                             log_level=args.log_level)
        
        # Load JSON data
        logger.info(f"Loading data from: {args.json_file}")
        
        try:
            with open(args.json_file, 'r') as f:
                paperlists_data = json.load(f)
            
            logger.log_file_operation("read", args.json_file, 
                                    size=len(json.dumps(paperlists_data)), 
                                    success=True)
            logger.log_data_stats("loaded_data", len(paperlists_data))
            
        except FileNotFoundError:
            logger.error(f"JSON file not found: {args.json_file}")
            return 1
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {args.json_file}: {e}")
            return 1
        
        # Initialize transformer with config
        logger.info("Initializing PaperlistsTransformer with configuration...")
        transformer = PaperlistsTransformer(config)
        
        logger.info(f"Starting to process {len(paperlists_data)} papers...")
        
        # Transform data
        start_time = time.time()
        transformer.transform_paperlists_data(paperlists_data)
        total_time = time.time() - start_time
        
        logger.success(f"Import process completed successfully in {total_time:.2f} seconds")
        logger.log_file_operation("created", config.database_url.replace('sqlite:///', ''), success=True)
        logger.info(f"Database created at: {config.database_url.replace('sqlite:///', '')}")
        logger.info(f"Check the '{config.log_directory}' directory for detailed processing logs")
        
        return 0
        
    except KeyboardInterrupt:
        if 'logger' in locals():
            logger.warning("Import process interrupted by user")
        else:
            print("Import process interrupted by user")
        return 1
    except Exception as e:
        if 'logger' in locals():
            logger.log_exception(e, "main import process")
            logger.error("Import process failed - check logs for details")
        else:
            print(f"Import process failed: {e}")
        return 1
    finally:
        if transformer:
            if 'logger' in locals():
                logger.info("Cleaning up resources...")
            transformer.cleanup()
        
        if 'logger' in locals():
            logger.end_operation("main_import_process", success=True)
            logger.info("🎯 Import process finished. Check logs for detailed analysis.")


def main_with_custom_file(json_file: str, db_file: str = "paperlists.db"):
    """Legacy function for backward compatibility - use main() with CLI args instead"""
    import sys
    print("Warning: main_with_custom_file is deprecated. Use CLI arguments instead:")
    print(f"python {sys.argv[0]} {json_file} --database {db_file}")
    
    # For backward compatibility, still support this function
    config = ImporterConfig()
    config.database_url = f'sqlite:///{db_file}'
    
    transformer = None
    logger = get_logger("paperlist_importer_custom", config.log_directory)
    
    try:
        logger.start_operation("custom_import_process", 
                             json_file=json_file, 
                             db_file=db_file)
        
        with open(json_file, 'r') as f:
            paperlists_data = json.load(f)
        
        logger.log_file_operation("read", json_file, 
                                size=len(json.dumps(paperlists_data)), 
                                success=True)
        logger.log_data_stats("loaded_custom_data", len(paperlists_data))
        
        transformer = PaperlistsTransformer(config)
        
        start_time = time.time()
        transformer.transform_paperlists_data(paperlists_data)
        total_time = time.time() - start_time
        
        logger.success(f"Custom import completed in {total_time:.2f} seconds")
        logger.log_file_operation("created", db_file, success=True)
        
    except Exception as e:
        logger.log_exception(e, "custom import process")
    finally:
        if transformer:
            transformer.cleanup()
        
        logger.end_operation("custom_import_process", success=True)


if __name__ == "__main__":
    import sys
    sys.exit(main())
