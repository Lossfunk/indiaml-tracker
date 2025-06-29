Entity Relationship Diagram - Paperlists Database Schema
Core Entities and Relationships

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│      Paper      │──────│   PaperAuthor   │──────│     Author      │
│                 │ 1:N  │                 │ N:1  │                 │
│ • id (PK)       │      │ • paper_id (FK) │      │ • id (PK)       │
│ • title         │      │ • author_id(FK) │      │ • name          │
│ • status        │      │ • author_order  │      │ • gender        │
│ • track_id (FK) │      │ • affiliation   │      │ • orcid         │
│ • abstract      │      │   _at_time      │      │ • homepage_url  │
│ • primary_area  │      └─────────────────┘      │ • google_scholar│
│ • openreview_url│                               │ • linkedin_url  │
│ • pdf_url       │                               │ • twitter_url   │
│ • github_url    │                               └─────────────────┘
└─────────────────┘                                        │
         │                                                  │ 1:N
         │ N:1                                              ▼
         ▼                                        ┌─────────────────┐
┌─────────────────┐                               │   Affiliation   │
│      Track      │                               │                 │
│                 │                               │ • id (PK)       │
│ • id (PK)       │                               │ • author_id(FK) │
│ • conference_   │                               │ • institution   │
│   _id (FK)      │                               │   _id (FK)      │
│ • name          │                               │ • position      │
│ • short_name    │                               │ • department    │
│ • track_type    │                               │ • is_primary    │
│ • description   │                               └─────────────────┘
│ • organizers    │                                        │
│ • website_url   │                                        │ N:1
└─────────────────┘                                        ▼
         │                                        ┌─────────────────┐
         │ N:1                                    │   Institution   │
         ▼                                        │                 │
┌─────────────────┐                               │ • id (PK)       │
│   Conference    │                               │ • name          │
│                 │                               │ • normalized_   │
│ • id (PK)       │                               │   _name         │
│ • name          │                               │ • abbreviation  │
│ • full_name     │                               │ • domain        │
│ • year          │                               │ • website_url   │
│ • location      │                               │ • country_id(FK)│
│ • start_date    │                               │ • campus        │
│ • end_date      │                               └─────────────────┘
│ • website_url   │                                        │
└─────────────────┘                                        │ N:1
                                                           ▼
┌─────────────────┐                               ┌─────────────────┐
│     Review      │                               │     Country     │
│                 │                               │                 │
│ • id (PK)       │                               │ • id (PK)       │
│ • paper_id (FK) │──────┐                        │ • name          │
│ • reviewer_id   │      │ N:1                    │ • code          │
│ • rating        │      ▼                        └─────────────────┘
│ • confidence    │  Paper (above)
│ • word_counts   │
└─────────────────┘
         │
         │ 1:1
         ▼
┌─────────────────┐
│ ReviewStatistics│
│                 │
│ • paper_id (FK) │
│ • rating_mean   │
│ • rating_std    │
│ • confidence_   │
│   _mean/_std    │
└─────────────────┘

┌─────────────────┐
│     Citation    │
│                 │
│ • paper_id (FK) │──────┐
│ • gs_citations  │      │ 1:1
│ • gs_url        │      ▼
│ • last_updated  │  Paper (above)
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Keyword      │──────│  PaperKeyword   │──────│      Paper      │
│                 │ 1:N  │                 │ N:1  │   (above)       │
│ • id (PK)       │      │ • paper_id (FK) │      └─────────────────┘
│ • keyword       │      │ • keyword_id(FK)│
│ • normalized    │      └─────────────────┘
└─────────────────┘

┌─────────────────┐
│ ExternalProfile │
│                 │
│ • id (PK)       │
│ • author_id(FK) │──────┐
│ • platform      │      │ N:1
│ • profile_url   │      ▼
│ • is_verified   │  Author (above)
└─────────────────┘

Key Design Decisions
1. Conference and Track Modeling

    Problem: Papers belong to different tracks within conferences (workshops, main conference, etc.)
    Solution: Separate Conference and Track tables with proper relationships
    Benefits: Can model complex conference structures, track organizers, different deadlines

2. Track Types

Support for various conference components:

    main: Main conference track
    workshop: Workshop sessions
    tutorial: Tutorial sessions
    demo: Demonstration track
    poster_session: Poster sessions
    position: Position papers
    other: Custom track types

3. Multi-Affiliation Handling

    Problem: Original schema uses complex "+" syntax (e.g., "0+1;2;3+0")
    Solution: Separate Affiliation table with foreign keys to Author and Institution
    Benefits: Clean many-to-many relationship, easy querying, no parsing needed

2. Normalized Institution Data

    Problem: Raw institution names are inconsistent
    Solution: Institution table with normalized_name field
    Benefits: Enables proper aggregation, deduplication, and canonical representation

3. Flexible External Profiles

    Design: Generic ExternalProfile table for any platform
    Benefits: Extensible for Twitter, ResearchGate, Academia.edu, etc.

4. Review Data Structure

    Split: Individual reviews vs. aggregated statistics
    Benefits: Maintains raw data while providing pre-computed metrics

Query Examples
Find all papers in workshops for a specific conference:

sql

SELECT p.title, t.name as track_name, c.name as conference
FROM papers p
JOIN tracks t ON p.track_id = t.id
JOIN conferences c ON t.conference_id = c.id
WHERE c.name = 'ICML' 
  AND c.year = 2025 
  AND t.track_type = 'workshop';

Find collaboration patterns within a conference track:

sql

SELECT t.name as track, i1.normalized_name as inst1, i2.normalized_name as inst2, COUNT(*) as collaborations
FROM papers p
JOIN tracks t ON p.track_id = t.id
JOIN conferences c ON t.conference_id = c.id
JOIN paper_authors pa1 ON p.id = pa1.paper_id
JOIN paper_authors pa2 ON p.id = pa2.paper_id AND pa1.author_id != pa2.author_id
JOIN authors a1 ON pa1.author_id = a1.id
JOIN authors a2 ON pa2.author_id = a2.id
JOIN affiliations af1 ON a1.id = af1.author_id
JOIN affiliations af2 ON a2.id = af2.author_id
JOIN institutions i1 ON af1.institution_id = i1.id
JOIN institutions i2 ON af2.institution_id = i2.id
WHERE c.name = 'ICML' AND c.year = 2025
  AND i1.id < i2.id
GROUP BY t.name, i1.normalized_name, i2.normalized_name
ORDER BY collaborations DESC;

Find highly cited papers from specific research areas:

sql

SELECT p.title, c.google_scholar_citations, p.primary_area
FROM papers p
JOIN citations c ON p.id = c.paper_id
WHERE p.primary_area LIKE '%reinforcement_learning%'
  AND c.google_scholar_citations > 10
ORDER BY c.google_scholar_citations DESC;

Migration Strategy

    Extract and normalize institution names
    Parse author affiliations and create proper relationships
    Handle multi-affiliations by creating multiple Affiliation records
    Populate external profiles from existing URL fields
    Create review records from aggregated data
    Normalize keywords into separate entities

