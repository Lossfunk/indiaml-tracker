# SQLAlchemy Models Documentation

This document provides detailed documentation for the SQLAlchemy models used in the IndiaML v2 database schema.

## Overview

The models are defined in `indiaml_v2/models/models.py` and represent the complete database schema for storing and analyzing academic paper data. All models inherit from SQLAlchemy's `declarative_base()` and include comprehensive relationships, indexes, and constraints.

## Base Configuration

```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

All models inherit from this base class and are automatically mapped to database tables.

## Core Entity Models

### Paper Model

**Primary entity representing academic papers**

```python
class Paper(Base):
    __tablename__ = 'papers'
    
    # Primary identification
    id = Column(String(50), primary_key=True)  # e.g., "3vjsUgCsZ4"
    title = Column(Text, nullable=False)
    
    # Conference and categorization
    status = Column(String(20))  # "Poster", "Oral", "Spotlight"
    track_id = Column(Integer, ForeignKey('tracks.id'))
    primary_area = Column(String(100))
    
    # Content fields
    abstract = Column(Text)
    tldr = Column(Text)  # Too Long; Didn't Read summary
    supplementary_material = Column(Text)
    bibtex = Column(Text)
    
    # URLs and external links
    site_url = Column(String(500))      # Conference presentation URL
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
```

**Relationships:**
- `track`: Many-to-one with Track
- `paper_authors`: One-to-many with PaperAuthor (cascade delete)
- `keywords`: One-to-many with PaperKeyword (cascade delete)
- `reviews`: One-to-many with Review (cascade delete)
- `citations`: One-to-one with Citation (cascade delete)
- `review_statistics`: One-to-one with ReviewStatistics (cascade delete)

**Indexes:**
- `idx_paper_status` on `status`
- `idx_paper_primary_area` on `primary_area`
- `idx_paper_track` on `track_id`

### Author Model

**Represents individual researchers and their profiles**

```python
class Author(Base):
    __tablename__ = 'authors'
    
    # Primary identification
    id = Column(String(100), primary_key=True)  # Generated or from authorids
    name = Column(String(200), nullable=False)
    name_site = Column(String(200))  # Name as displayed on conference site
    
    # Profile identifiers
    openreview_id = Column(String(100))  # From or_profile field
    gender = Column(String(20))  # "M", "F", "Unspecified"
    
    # External profiles and links
    homepage_url = Column(String(500))
    dblp_id = Column(String(200))
    google_scholar_url = Column(String(500))
    orcid = Column(String(50))  # ORCID identifier
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    
    # Contact information
    primary_email = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- `paper_authors`: One-to-many with PaperAuthor
- `affiliations`: One-to-many with Affiliation (cascade delete)
- `external_profiles`: One-to-many with ExternalProfile (backref)

**Constraints:**
- `UNIQUE(orcid)` - ORCID must be unique when provided

**Indexes:**
- `idx_author_name` on `name`
- `idx_author_orcid` on `orcid`

### Institution Model

**Represents academic and research institutions**

```python
class Institution(Base):
    __tablename__ = 'institutions'
    
    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)  # Original institution name
    normalized_name = Column(String(300), nullable=False)  # Canonical name
    abbreviation = Column(String(50))
    
    # Geographic location
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    campus = Column(String(200))  # e.g., "San Diego", "Shenzhen"
    
    # Contact and web presence
    domain = Column(String(200))  # Primary email domain
    website_url = Column(String(500))
    
    # Classification
    institution_type = Column(String(50))  # "University", "Company", "Research Institute"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- `country`: Many-to-one with Country
- `affiliations`: One-to-many with Affiliation

**Constraints:**
- `UNIQUE(normalized_name, country_id, campus)` - Prevents duplicate institutions

**Indexes:**
- `idx_institution_normalized_name` on `normalized_name`
- `idx_institution_normalized_name_country` on `(normalized_name, country_id)`
- `idx_institution_domain` on `domain`
- `idx_institution_country` on `country_id`

### Country Model

**Represents countries for geographic analysis**

```python
class Country(Base):
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(3))  # ISO country code if available
```

**Relationships:**
- `institutions`: One-to-many with Institution

**Indexes:**
- `idx_country_name` on `name`

## Relationship Models

### PaperAuthor Model

**Junction table linking papers to authors with ordering**

```python
class PaperAuthor(Base):
    __tablename__ = 'paper_authors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    author_order = Column(Integer, nullable=False)  # 1st, 2nd, 3rd author, etc.
    
    # Affiliation context for this specific paper
    affiliation_at_time = Column(Text)  # Raw affiliation string from paper
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Relationships:**
- `paper`: Many-to-one with Paper
- `author`: Many-to-one with Author

**Constraints:**
- `UNIQUE(paper_id, author_id)` - One relationship per paper-author pair
- `UNIQUE(paper_id, author_order)` - Unique ordering per paper

**Indexes:**
- `idx_paper_author_paper` on `paper_id`
- `idx_paper_author_author` on `author_id`

### Affiliation Model

**Links authors to institutions with role information**

```python
class Affiliation(Base):
    __tablename__ = 'affiliations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    
    # Role and position information
    position = Column(String(200))  # "PhD student", "Professor", etc.
    department = Column(String(200))  # Department within institution
    email_domain = Column(String(200))  # Specific email domain
    
    # Temporal validity (if known)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_primary = Column(Boolean, default=False)  # Primary affiliation flag
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- `author`: Many-to-one with Author
- `institution`: Many-to-one with Institution

**Indexes:**
- `idx_affiliation_author` on `author_id`
- `idx_affiliation_institution` on `institution_id`
- `idx_affiliation_position` on `position`

## Content Models

### Keyword and PaperKeyword Models

**Manages paper keywords and topics**

```python
class Keyword(Base):
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, unique=True)
    normalized_keyword = Column(String(200))  # Lowercase, trimmed version
```

```python
class PaperKeyword(Base):
    __tablename__ = 'paper_keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
```

**Relationships:**
- `Keyword.papers`: One-to-many with PaperKeyword
- `PaperKeyword.paper`: Many-to-one with Paper
- `PaperKeyword.keyword`: Many-to-one with Keyword

**Constraints:**
- `UNIQUE(paper_id, keyword_id)` in PaperKeyword

## Review and Citation Models

### Review Model

**Individual paper reviews and scores**

```python
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False)
    reviewer_id = Column(String(100))  # Anonymous reviewer identifier
    
    # Core review scores (1-5 scale)
    recommendation = Column(Integer)  # Accept/reject recommendation
    rating = Column(Integer)  # Overall rating
    confidence = Column(Integer)  # Reviewer confidence
    
    # Position paper specific metrics
    support = Column(Integer)
    significance = Column(Integer)
    discussion_potential = Column(Integer)
    argument_clarity = Column(Integer)
    related_work = Column(Integer)
    
    # Review content metrics
    word_count_summary = Column(Integer)
    word_count_strengths_weaknesses = Column(Integer)
    word_count_questions = Column(Integer)
    word_count_total = Column(Integer)
    
    # Interaction metrics
    reviewer_replies = Column(Integer, default=0)
    author_replies = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Relationships:**
- `paper`: Many-to-one with Paper

**Constraints:**
- `CHECK(recommendation >= 1 AND recommendation <= 5)`
- `CHECK(rating >= 1 AND rating <= 5)`

**Indexes:**
- `idx_review_paper` on `paper_id`
- `idx_review_rating` on `rating`
- `idx_review_recommendation` on `recommendation`

### ReviewStatistics Model

**Aggregated review metrics per paper**

```python
class ReviewStatistics(Base):
    __tablename__ = 'review_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False, unique=True)
    
    # Score statistics (mean and standard deviation)
    rating_mean = Column(Float)
    rating_std = Column(Float)
    confidence_mean = Column(Float)
    confidence_std = Column(Float)
    support_mean = Column(Float)
    support_std = Column(Float)
    significance_mean = Column(Float)
    significance_std = Column(Float)
    
    # Word count statistics
    word_count_summary_mean = Column(Float)
    word_count_summary_std = Column(Float)
    word_count_review_mean = Column(Float)
    word_count_review_std = Column(Float)
    
    # Correlation metrics
    rating_confidence_correlation = Column(Float)
    
    # Count metrics
    total_reviews = Column(Integer)
    total_reviewers = Column(Integer)
    
    last_calculated = Column(DateTime, default=datetime.utcnow)
```

**Relationships:**
- `paper`: One-to-one with Paper

**Indexes:**
- `idx_review_stats_rating_mean` on `rating_mean`

### Citation Model

**Citation metrics and external links**

```python
class Citation(Base):
    __tablename__ = 'citations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey('papers.id'), nullable=False, unique=True)
    
    # Google Scholar metrics
    google_scholar_citations = Column(Integer, default=0)
    google_scholar_url = Column(String(500))
    google_scholar_versions = Column(Integer, default=0)
    
    # Other citation sources (extensible)
    semantic_scholar_citations = Column(Integer)
    semantic_scholar_url = Column(String(500))
    
    last_updated = Column(DateTime, default=datetime.utcnow)
```

**Relationships:**
- `paper`: One-to-one with Paper

**Indexes:**
- `idx_citation_gs_count` on `google_scholar_citations`

## Conference and Track Models

### Conference Model

**Conference/venue information**

```python
class Conference(Base):
    __tablename__ = 'conferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # "ICML", "NeurIPS", etc.
    full_name = Column(String(500))  # Full conference name
    year = Column(Integer, nullable=False)
    
    # Event details
    location = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    website_url = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Relationships:**
- `tracks`: One-to-many with Track (cascade delete)

**Constraints:**
- `UNIQUE(name, year)` - One conference per year

**Indexes:**
- `idx_conference_year` on `year`
- `idx_conference_name` on `name`

### Track Model

**Conference tracks (main, workshops, tutorials, etc.)**

```python
class Track(Base):
    __tablename__ = 'tracks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conference_id = Column(Integer, ForeignKey('conferences.id'), nullable=False)
    
    # Track identification
    name = Column(String(300), nullable=False)  # Full track name
    short_name = Column(String(100))  # Short identifier
    track_type = Column(String(50))  # "main", "workshop", "tutorial", etc.
    
    # Track metadata
    description = Column(Text)
    organizers = Column(Text)  # Could be JSON for complex cases
    website_url = Column(String(500))
    submission_url = Column(String(500))
    
    # Important dates
    submission_deadline = Column(DateTime)
    notification_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- `conference`: Many-to-one with Conference
- `papers`: One-to-many with Paper

**Constraints:**
- `UNIQUE(conference_id, short_name)` - Unique track names per conference

**Indexes:**
- `idx_track_conference` on `conference_id`
- `idx_track_type` on `track_type`
- `idx_track_name` on `name`

## Extension Models

### ExternalProfile Model

**Flexible storage for additional author profiles**

```python
class ExternalProfile(Base):
    __tablename__ = 'external_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(String(100), ForeignKey('authors.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # "twitter", "researchgate", etc.
    profile_url = Column(String(500), nullable=False)
    profile_id = Column(String(200))  # Platform-specific ID
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- `author`: Many-to-one with Author (backref)

**Constraints:**
- `UNIQUE(author_id, platform)` - One profile per platform per author

**Indexes:**
- `idx_external_profile_author` on `author_id`
- `idx_external_profile_platform` on `platform`

## Model Usage Examples

### Creating Entities

```python
from models.models import Paper, Author, Institution, Country

# Create a country
country = Country(name="United States", code="US")

# Create an institution
institution = Institution(
    name="Massachusetts Institute of Technology",
    normalized_name="MIT",
    country=country,
    domain="mit.edu",
    institution_type="University"
)

# Create an author
author = Author(
    id="john_doe_mit",
    name="John Doe",
    orcid="0000-0000-0000-0001",
    homepage_url="https://johndoe.mit.edu"
)

# Create a paper
paper = Paper(
    id="abc123",
    title="A Novel Approach to Machine Learning",
    status="Oral",
    abstract="This paper presents...",
    author_count=3
)
```

### Querying with Relationships

```python
# Find all papers by an author
author_papers = session.query(Paper).join(PaperAuthor).filter(
    PaperAuthor.author_id == "john_doe_mit"
).all()

# Find all authors from an institution
mit_authors = session.query(Author).join(Affiliation).join(Institution).filter(
    Institution.normalized_name == "MIT"
).all()

# Get papers with high citation counts
highly_cited = session.query(Paper).join(Citation).filter(
    Citation.google_scholar_citations > 100
).order_by(Citation.google_scholar_citations.desc()).all()
```

### Complex Queries with Statistics

```python
# Papers with high review scores
top_papers = session.query(Paper, ReviewStatistics).join(ReviewStatistics).filter(
    ReviewStatistics.rating_mean > 4.0,
    ReviewStatistics.total_reviews >= 3
).order_by(ReviewStatistics.rating_mean.desc()).all()

# Institution collaboration analysis
collaborations = session.query(
    Institution.normalized_name.label('inst1'),
    Institution.normalized_name.label('inst2'),
    func.count(Paper.id).label('paper_count')
).select_from(Paper)\
.join(PaperAuthor, Paper.id == PaperAuthor.paper_id)\
.join(Author, PaperAuthor.author_id == Author.id)\
.join(Affiliation, Author.id == Affiliation.author_id)\
.join(Institution, Affiliation.institution_id == Institution.id)\
.group_by(Institution.id)\
.having(func.count(Paper.id) > 5).all()
```

## Performance Considerations

### Indexing Strategy
- **Primary keys**: Automatic indexes for fast lookups
- **Foreign keys**: Indexes on all foreign key columns
- **Search fields**: Indexes on commonly searched fields (name, orcid, etc.)
- **Compound indexes**: Multi-column indexes for complex queries

### Relationship Loading
- **Lazy loading**: Default for most relationships to avoid N+1 queries
- **Eager loading**: Use `joinedload()` for frequently accessed relationships
- **Batch loading**: Use `selectinload()` for one-to-many relationships

### Query Optimization
- **Select specific columns**: Avoid loading unnecessary data
- **Use joins**: Prefer joins over separate queries
- **Limit results**: Use `LIMIT` for large datasets
- **Index usage**: Ensure queries use appropriate indexes

## Data Integrity

### Constraints
- **Primary keys**: Ensure entity uniqueness
- **Foreign keys**: Maintain referential integrity
- **Unique constraints**: Prevent duplicate data
- **Check constraints**: Validate data ranges and formats

### Cascading Operations
- **Cascade delete**: Remove dependent records when parent is deleted
- **Cascade update**: Update foreign keys when parent key changes
- **Restrict**: Prevent deletion if dependent records exist

### Validation
- **Model validation**: Use SQLAlchemy validators for data validation
- **Business logic**: Implement validation in application layer
- **Database constraints**: Enforce constraints at database level
