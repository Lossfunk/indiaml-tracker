from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)


from sqlalchemy.orm import relationship, backref, declarative_base
from datetime import datetime

Base = declarative_base()

# Core Paper Table
class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(String(50), primary_key=True)  # e.g., "3vjsUgCsZ4"
    title = Column(Text, nullable=False)
    status = Column(String(20))  # "Poster", "Oral", "Spotlight"
    track_id = Column(Integer, ForeignKey('tracks.id'))  # Link to track
    primary_area = Column(String(100))
    
    # Content
    abstract = Column(Text)
    tldr = Column(Text)
    supplementary_material = Column(Text)
    bibtex = Column(Text)
    
    # URLs
    site_url = Column(String(500))  # Conference presentation URL
    openreview_url = Column(String(500))
    pdf_url = Column(String(500))
    github_url = Column(String(500))
    project_url = Column(String(500))
    
    # Metrics
    author_count = Column(Integer)
    pdf_size = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    track = relationship("Track", back_populates="papers")
    paper_authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("PaperKeyword", back_populates="paper", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="paper", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_paper_status', 'status'),
        Index('idx_paper_primary_area', 'primary_area'),
        Index('idx_paper_track', 'track_id'),
    )

# Author Table
class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(String(100), primary_key=True)  # Derived from authorids or generated
    name = Column(String(200), nullable=False)
    name_site = Column(String(200))  # Name as it appears on site
    openreview_id = Column(String(100))  # From or_profile
    gender = Column(String(20))  # "M", "F", "Unspecified", etc.
    
    # External Profiles
    homepage_url = Column(String(500))
    dblp_id = Column(String(200))
    google_scholar_url = Column(String(500))
    orcid = Column(String(50))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))  # Additional metadata
    
    # Contact
    primary_email = Column(String(200))  # Full email if available
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper_authors = relationship("PaperAuthor", back_populates="author")
    affiliations = relationship("Affiliation", back_populates="author", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_author_name', 'name'),
        Index('idx_author_orcid', 'orcid'),
        UniqueConstraint('orcid', name='uq_author_orcid'),
    )

# Country Table
class Country(Base):
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(3))  # ISO country code if available
    
    # Relationships
    institutions = relationship("Institution", back_populates="country")
    
    __table_args__ = (
        Index('idx_country_name', 'name'),
    )

# Institution Table (Normalized)
class Institution(Base):
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    normalized_name = Column(String(300), nullable=False)  # Clean, canonical name
    abbreviation = Column(String(50))
    
    # Location
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    campus = Column(String(200))  # e.g., "San Diego", "Shenzhen"
    
    # Contact/Web
    domain = Column(String(200))  # Primary email domain
    website_url = Column(String(500))
    
    # Metadata
    institution_type = Column(String(50))  # "University", "Company", "Research Institute"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="institutions")
    affiliations = relationship("Affiliation", back_populates="institution")
    
    __table_args__ = (
        Index('idx_institution_normalized_name', 'normalized_name'),  # Primary lookup index
        Index('idx_institution_normalized_name_country', 'normalized_name', 'country_id'),  # Compound index for location-specific lookups
        Index('idx_institution_domain', 'domain'),
        Index('idx_institution_country', 'country_id'),
        UniqueConstraint('normalized_name', 'country_id', 'campus', name='uq_institution_location'),
    )

# Affiliation Table (Links Authors to Institutions with Roles)
class Affiliation(Base):
    __tablename__ = 'affiliations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    
    # Role/Position information
    position = Column(String(200))  # "PhD student", "Full Professor", etc.
    department = Column(String(200))  # Department within institution
    email_domain = Column(String(200))  # Specific email domain for this affiliation
    
    # Validity period (if known)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_primary = Column(Boolean, default=False)  # Is this the primary affiliation?
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("Author", back_populates="affiliations")
    institution = relationship("Institution", back_populates="affiliations")
    
    __table_args__ = (
        Index('idx_affiliation_author', 'author_id'),
        Index('idx_affiliation_institution', 'institution_id'),
        Index('idx_affiliation_position', 'position'),
    )

# Paper-Author Junction Table
class PaperAuthor(Base):
    __tablename__ = 'paper_authors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    author_order = Column(Integer, nullable=False)  # 1st author, 2nd author, etc.
    
    # Specific affiliation for this paper (if different from primary)
    affiliation_at_time = Column(Text)  # Raw affiliation string as it appeared in paper
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="paper_authors")
    author = relationship("Author", back_populates="paper_authors")
    
    __table_args__ = (
        UniqueConstraint('paper_id', 'author_id', name='uq_paper_author'),
        UniqueConstraint('paper_id', 'author_order', name='uq_paper_author_order'),
        Index('idx_paper_author_paper', 'paper_id'),
        Index('idx_paper_author_author', 'author_id'),
    )

# Keywords Table
class Keyword(Base):
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, unique=True)
    normalized_keyword = Column(String(200))  # Lowercase, trimmed version
    
    # Relationships
    papers = relationship("PaperKeyword", back_populates="keyword")
    
    __table_args__ = (
        Index('idx_keyword_normalized', 'normalized_keyword'),
    )

# Paper-Keyword Junction Table
class PaperKeyword(Base):
    __tablename__ = 'paper_keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    
    # Relationships
    paper = relationship("Paper", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="papers")
    
    __table_args__ = (
        UniqueConstraint('paper_id', 'keyword_id', name='uq_paper_keyword'),
        Index('idx_paper_keyword_paper', 'paper_id'),
        Index('idx_paper_keyword_keyword', 'keyword_id'),
    )

# Review Process Table
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    reviewer_id = Column(String(100))  # Anonymous reviewer ID
    
    # Overall scores
    recommendation = Column(Integer)  # 1-5 scale
    rating = Column(Integer)  # 1-5 scale
    confidence = Column(Integer)  # 1-5 scale
    
    # Position paper specific metrics
    support = Column(Integer)
    significance = Column(Integer)
    discussion_potential = Column(Integer)
    argument_clarity = Column(Integer)
    related_work = Column(Integer)
    
    # Word counts for different sections
    word_count_summary = Column(Integer)
    word_count_strengths_weaknesses = Column(Integer)
    word_count_questions = Column(Integer)
    word_count_total = Column(Integer)
    
    # Reply counts
    reviewer_replies = Column(Integer, default=0)
    author_replies = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="reviews")
    
    __table_args__ = (
        Index('idx_review_paper', 'paper_id'),
        Index('idx_review_rating', 'rating'),
        Index('idx_review_recommendation', 'recommendation'),
        CheckConstraint('recommendation >= 1 AND recommendation <= 5', name='ck_review_recommendation'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating'),
    )

# Citation Data Table
class Citation(Base):
    __tablename__ = 'citations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False, unique=True)
    
    # Google Scholar metrics
    google_scholar_citations = Column(Integer, default=0)
    google_scholar_url = Column(String(500))
    google_scholar_versions = Column(Integer, default=0)
    
    # Other citation metrics can be added here
    semantic_scholar_citations = Column(Integer)
    semantic_scholar_url = Column(String(500))
    
    # Update tracking
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="citations")
    
    __table_args__ = (
        Index('idx_citation_gs_count', 'google_scholar_citations'),
    )

# Review Statistics (Aggregated Data)
class ReviewStatistics(Base):
    __tablename__ = 'review_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False, unique=True)
    
    # Average scores with standard deviations
    rating_mean = Column(Float)
    rating_std = Column(Float)
    confidence_mean = Column(Float)
    confidence_std = Column(Float)
    support_mean = Column(Float)
    support_std = Column(Float)
    significance_mean = Column(Float)
    significance_std = Column(Float)
    
    # Word count averages
    word_count_summary_mean = Column(Float)
    word_count_summary_std = Column(Float)
    word_count_review_mean = Column(Float)
    word_count_review_std = Column(Float)
    
    # Correlation metrics
    rating_confidence_correlation = Column(Float)
    
    # Total counts
    total_reviews = Column(Integer)
    total_reviewers = Column(Integer)
    
    # Update tracking
    last_calculated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_review_stats_rating_mean', 'rating_mean'),
    )

# External Profile Links (Flexible for additional platforms)
class ExternalProfile(Base):
    __tablename__ = 'external_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # "twitter", "researchgate", "academia", etc.
    profile_url = Column(String(500), nullable=False)
    profile_id = Column(String(200))  # Platform-specific ID if available
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("Author", backref="external_profiles")
    
    __table_args__ = (
        UniqueConstraint('author_id', 'platform', name='uq_author_platform'),
        Index('idx_external_profile_author', 'author_id'),
        Index('idx_external_profile_platform', 'platform'),
    )

# Conference/Venue Information
class Conference(Base):
    __tablename__ = 'conferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # "ICML"
    full_name = Column(String(500))  # "International Conference on Machine Learning"
    year = Column(Integer, nullable=False)
    
    # Location
    location = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # URLs
    website_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tracks = relationship("Track", back_populates="conference", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('name', 'year', name='uq_conference_year'),
        Index('idx_conference_year', 'year'),
        Index('idx_conference_name', 'name'),
    )

# Track Table (workshops, main conference, tutorials, etc.)
class Track(Base):
    __tablename__ = 'tracks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conference_id = Column(Integer, ForeignKey('conferences.id'), nullable=False)
    
    # Track identification
    name = Column(String(300), nullable=False)  # "Main Conference", "Workshop on AI Safety", etc.
    short_name = Column(String(100))  # "main", "ai-safety-ws", etc.
    track_type = Column(String(50))  # "main", "workshop", "tutorial", "demo", "poster_session"
    
    # Track details
    description = Column(Text)
    organizers = Column(Text)  # Could be JSON or separate table for complex cases
    
    # URLs and identifiers
    website_url = Column(String(500))
    submission_url = Column(String(500))
    
    # Dates (tracks may have different deadlines within same conference)
    submission_deadline = Column(DateTime)
    notification_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conference = relationship("Conference", back_populates="tracks")
    papers = relationship("Paper", back_populates="track")
    
    __table_args__ = (
        UniqueConstraint('conference_id', 'short_name', name='uq_conference_track'),
        Index('idx_track_conference', 'conference_id'),
        Index('idx_track_type', 'track_type'),
        Index('idx_track_name', 'name'),
    )