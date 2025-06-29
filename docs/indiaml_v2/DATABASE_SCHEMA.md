# IndiaML v2 Database Schema Documentation

This document provides comprehensive documentation for the IndiaML v2 database schema, which is designed to store and analyze academic paper data from major ML/AI conferences.

## Overview

The database schema is designed around academic papers and their associated metadata, including authors, institutions, reviews, citations, and conference information. The schema supports complex queries for research analytics and author tracking.

## Core Tables

### Papers Table
**Primary entity representing academic papers**

```sql
CREATE TABLE papers (
    id VARCHAR(50) PRIMARY KEY,           -- Unique paper identifier (e.g., "3vjsUgCsZ4")
    title TEXT NOT NULL,                  -- Paper title
    status VARCHAR(20),                   -- "Poster", "Oral", "Spotlight"
    track_id INTEGER,                     -- Foreign key to tracks table
    primary_area VARCHAR(100),            -- Research area/topic
    abstract TEXT,                        -- Paper abstract
    tldr TEXT,                           -- Too Long; Didn't Read summary
    supplementary_material TEXT,          -- Additional materials
    bibtex TEXT,                         -- BibTeX citation
    site_url VARCHAR(500),               -- Conference presentation URL
    openreview_url VARCHAR(500),         -- OpenReview URL
    pdf_url VARCHAR(500),                -- PDF download URL
    github_url VARCHAR(500),             -- GitHub repository URL
    project_url VARCHAR(500),            -- Project page URL
    author_count INTEGER,                -- Number of authors
    pdf_size INTEGER DEFAULT 0,          -- PDF file size in bytes
    created_at DATETIME,                 -- Record creation timestamp
    updated_at DATETIME                  -- Last update timestamp
);
```

**Indexes:**
- `idx_paper_status` on `status`
- `idx_paper_primary_area` on `primary_area`
- `idx_paper_track` on `track_id`

### Authors Table
**Represents individual researchers and their profiles**

```sql
CREATE TABLE authors (
    id VARCHAR(100) PRIMARY KEY,         -- Unique author identifier
    name VARCHAR(200) NOT NULL,          -- Author's full name
    name_site VARCHAR(200),              -- Name as displayed on conference site
    openreview_id VARCHAR(100),          -- OpenReview profile ID
    gender VARCHAR(20),                  -- Gender information
    homepage_url VARCHAR(500),           -- Personal homepage
    dblp_id VARCHAR(200),               -- DBLP profile ID
    google_scholar_url VARCHAR(500),     -- Google Scholar profile
    orcid VARCHAR(50),                   -- ORCID identifier
    linkedin_url VARCHAR(500),           -- LinkedIn profile
    twitter_url VARCHAR(500),            -- Twitter profile
    primary_email VARCHAR(200),          -- Primary email address
    created_at DATETIME,                 -- Record creation timestamp
    updated_at DATETIME                  -- Last update timestamp
);
```

**Constraints:**
- `UNIQUE(orcid)` - ORCID must be unique when provided

**Indexes:**
- `idx_author_name` on `name`
- `idx_author_orcid` on `orcid`

### Institutions Table
**Represents academic and research institutions**

```sql
CREATE TABLE institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(300) NOT NULL,          -- Institution full name
    normalized_name VARCHAR(300) NOT NULL, -- Canonical/cleaned name
    abbreviation VARCHAR(50),            -- Common abbreviation
    country_id INTEGER NOT NULL,         -- Foreign key to countries
    campus VARCHAR(200),                 -- Campus location (e.g., "San Diego")
    domain VARCHAR(200),                 -- Primary email domain
    website_url VARCHAR(500),            -- Institution website
    institution_type VARCHAR(50),        -- "University", "Company", "Research Institute"
    created_at DATETIME,
    updated_at DATETIME
);
```

**Constraints:**
- `UNIQUE(normalized_name, country_id, campus)` - Prevents duplicate institutions

**Indexes:**
- `idx_institution_normalized_name` on `normalized_name`
- `idx_institution_normalized_name_country` on `(normalized_name, country_id)`
- `idx_institution_domain` on `domain`
- `idx_institution_country` on `country_id`

### Countries Table
**Represents countries for institution locations**

```sql
CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,   -- Country name
    code VARCHAR(3)                      -- ISO country code
);
```

## Relationship Tables

### Paper-Author Relationships
**Links papers to their authors with ordering information**

```sql
CREATE TABLE paper_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id VARCHAR(50) NOT NULL,       -- Foreign key to papers
    author_id VARCHAR(100) NOT NULL,     -- Foreign key to authors
    author_order INTEGER NOT NULL,       -- Author position (1st, 2nd, etc.)
    affiliation_at_time TEXT,           -- Raw affiliation string from paper
    created_at DATETIME
);
```

**Constraints:**
- `UNIQUE(paper_id, author_id)` - One relationship per paper-author pair
- `UNIQUE(paper_id, author_order)` - Unique ordering per paper

### Affiliations
**Links authors to institutions with role information**

```sql
CREATE TABLE affiliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id VARCHAR(100) NOT NULL,     -- Foreign key to authors
    institution_id INTEGER NOT NULL,     -- Foreign key to institutions
    position VARCHAR(200),               -- "PhD student", "Professor", etc.
    department VARCHAR(200),             -- Department within institution
    email_domain VARCHAR(200),           -- Specific email domain
    start_date DATETIME,                 -- Affiliation start date
    end_date DATETIME,                   -- Affiliation end date
    is_primary BOOLEAN DEFAULT FALSE,    -- Primary affiliation flag
    created_at DATETIME,
    updated_at DATETIME
);
```

### Keywords
**Paper keywords and topics**

```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword VARCHAR(200) NOT NULL UNIQUE, -- Original keyword
    normalized_keyword VARCHAR(200)       -- Lowercase, cleaned version
);

CREATE TABLE paper_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id VARCHAR(50) NOT NULL,       -- Foreign key to papers
    keyword_id INTEGER NOT NULL          -- Foreign key to keywords
);
```

## Review and Citation Data

### Reviews
**Individual paper reviews and scores**

```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id VARCHAR(50) NOT NULL,       -- Foreign key to papers
    reviewer_id VARCHAR(100),            -- Anonymous reviewer ID
    recommendation INTEGER,              -- 1-5 scale recommendation
    rating INTEGER,                      -- 1-5 scale rating
    confidence INTEGER,                  -- 1-5 scale confidence
    support INTEGER,                     -- Position paper support score
    significance INTEGER,                -- Significance score
    discussion_potential INTEGER,        -- Discussion potential score
    argument_clarity INTEGER,            -- Argument clarity score
    related_work INTEGER,               -- Related work score
    word_count_summary INTEGER,          -- Summary word count
    word_count_strengths_weaknesses INTEGER, -- Strengths/weaknesses word count
    word_count_questions INTEGER,        -- Questions word count
    word_count_total INTEGER,           -- Total review word count
    reviewer_replies INTEGER DEFAULT 0,  -- Number of reviewer replies
    author_replies INTEGER DEFAULT 0,    -- Number of author replies
    created_at DATETIME
);
```

**Constraints:**
- `CHECK(recommendation >= 1 AND recommendation <= 5)`
- `CHECK(rating >= 1 AND rating <= 5)`

### Review Statistics
**Aggregated review metrics per paper**

```sql
CREATE TABLE review_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id VARCHAR(50) NOT NULL UNIQUE, -- Foreign key to papers
    rating_mean REAL,                    -- Average rating
    rating_std REAL,                     -- Rating standard deviation
    confidence_mean REAL,               -- Average confidence
    confidence_std REAL,                -- Confidence standard deviation
    support_mean REAL,                  -- Average support score
    support_std REAL,                   -- Support standard deviation
    significance_mean REAL,             -- Average significance
    significance_std REAL,              -- Significance standard deviation
    word_count_summary_mean REAL,       -- Average summary word count
    word_count_summary_std REAL,        -- Summary word count std dev
    word_count_review_mean REAL,        -- Average review word count
    word_count_review_std REAL,         -- Review word count std dev
    rating_confidence_correlation REAL, -- Rating-confidence correlation
    total_reviews INTEGER,              -- Total number of reviews
    total_reviewers INTEGER,            -- Total number of reviewers
    last_calculated DATETIME            -- Last calculation timestamp
);
```

### Citations
**Citation metrics and external links**

```sql
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id VARCHAR(50) NOT NULL UNIQUE, -- Foreign key to papers
    google_scholar_citations INTEGER DEFAULT 0, -- Google Scholar citation count
    google_scholar_url VARCHAR(500),     -- Google Scholar page URL
    google_scholar_versions INTEGER DEFAULT 0, -- Number of versions
    semantic_scholar_citations INTEGER,  -- Semantic Scholar citations
    semantic_scholar_url VARCHAR(500),   -- Semantic Scholar URL
    last_updated DATETIME               -- Last update timestamp
);
```

## Conference and Track Information

### Conferences
**Conference/venue information**

```sql
CREATE TABLE conferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,          -- Conference acronym (e.g., "ICML")
    full_name VARCHAR(500),              -- Full conference name
    year INTEGER NOT NULL,               -- Conference year
    location VARCHAR(200),               -- Conference location
    start_date DATETIME,                 -- Conference start date
    end_date DATETIME,                   -- Conference end date
    website_url VARCHAR(500),            -- Conference website
    created_at DATETIME
);
```

**Constraints:**
- `UNIQUE(name, year)` - One conference per year

### Tracks
**Conference tracks (main, workshops, tutorials, etc.)**

```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conference_id INTEGER NOT NULL,      -- Foreign key to conferences
    name VARCHAR(300) NOT NULL,          -- Track full name
    short_name VARCHAR(100),             -- Track short name/identifier
    track_type VARCHAR(50),              -- "main", "workshop", "tutorial", etc.
    description TEXT,                    -- Track description
    organizers TEXT,                     -- Track organizers
    website_url VARCHAR(500),            -- Track website
    submission_url VARCHAR(500),         -- Submission portal
    submission_deadline DATETIME,        -- Submission deadline
    notification_date DATETIME,          -- Notification date
    is_active BOOLEAN DEFAULT TRUE,      -- Track status
    created_at DATETIME,
    updated_at DATETIME
);
```

**Constraints:**
- `UNIQUE(conference_id, short_name)` - Unique track names per conference

## External Profiles
**Flexible storage for additional author profiles**

```sql
CREATE TABLE external_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id VARCHAR(100) NOT NULL,     -- Foreign key to authors
    platform VARCHAR(50) NOT NULL,       -- Platform name (e.g., "twitter")
    profile_url VARCHAR(500) NOT NULL,   -- Profile URL
    profile_id VARCHAR(200),             -- Platform-specific ID
    is_verified BOOLEAN DEFAULT FALSE,   -- Verification status
    verified_at DATETIME,               -- Verification timestamp
    created_at DATETIME,
    updated_at DATETIME
);
```

**Constraints:**
- `UNIQUE(author_id, platform)` - One profile per platform per author

## Key Relationships

### Entity Relationship Diagram

```
Papers ──┬── PaperAuthors ── Authors ──┬── Affiliations ── Institutions ── Countries
         │                             └── ExternalProfiles
         ├── PaperKeywords ── Keywords
         ├── Reviews
         ├── ReviewStatistics
         ├── Citations
         └── Tracks ── Conferences
```

### Foreign Key Relationships

1. **Papers → Tracks**: Each paper belongs to a conference track
2. **PaperAuthors**: Many-to-many relationship between Papers and Authors
3. **Affiliations**: Many-to-many relationship between Authors and Institutions
4. **Institutions → Countries**: Each institution belongs to a country
5. **Reviews → Papers**: Each review is for a specific paper
6. **Citations → Papers**: Each citation record is for a specific paper
7. **Tracks → Conferences**: Each track belongs to a conference

## Data Integrity Features

### Constraints
- **Unique Constraints**: Prevent duplicate records
- **Check Constraints**: Ensure valid score ranges (1-5)
- **Foreign Key Constraints**: Maintain referential integrity

### Indexes
- **Primary Lookups**: Fast access by ID fields
- **Search Optimization**: Indexes on commonly queried fields
- **Compound Indexes**: Optimized for complex queries

### Cascading Deletes
- **Papers**: Deleting a paper removes all associated reviews, citations, etc.
- **Authors**: Deleting an author removes all affiliations and external profiles
- **Institutions**: Protected by foreign key constraints

## Performance Considerations

### Optimized Queries
The schema is optimized for common query patterns:
- Author paper counts and collaboration networks
- Institution rankings and statistics
- Conference and track analytics
- Citation and review analysis

### Indexing Strategy
- **Single-column indexes** for primary lookups
- **Compound indexes** for complex filtering
- **Covering indexes** for frequently accessed data combinations

### Normalization
- **3NF compliance** for data consistency
- **Denormalization** in statistics tables for performance
- **Flexible JSON fields** for extensible metadata
